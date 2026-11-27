"""LLM provider that runs the OpenAI Codex CLI (`codex exec`) under the user's own ChatGPT login.

No API key and no per-call billing: usage counts against the user's ChatGPT plan limits. The call runs in an
empty temporary directory with a read-only sandbox, no user config, no saved session, and with OPENAI_API_KEY
removed from its environment so it can never silently fall back to API billing. Billed cost recorded is 0.

Codex enforces OpenAI strict structured output, so schemas are converted: every object gets
additionalProperties=false and lists all properties as required; originally-optional properties become nullable,
and nulls are stripped from the output again so callers see the shape they asked for.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile

from app.llm.base import LLMError, LLMResult

_EFFORTS = {"low", "medium", "high", "xhigh"}
_EFFORT_MAP = {"max": "xhigh"}


def _nullable(s: dict) -> dict:
    t = s.get("type")
    if isinstance(t, str):
        return {**s, "type": [t, "null"]} if t != "null" else s
    if isinstance(t, list):
        return s if "null" in t else {**s, "type": [*t, "null"]}
    return {"anyOf": [s, {"type": "null"}]}


def strictify(schema: dict) -> dict:
    s = copy.deepcopy(schema)

    def walk(n):
        if isinstance(n, list):
            return [walk(x) for x in n]
        if not isinstance(n, dict):
            return n
        n = {k: walk(v) for k, v in n.items()}
        if n.get("type") == "object" or (isinstance(n.get("type"), list) and "object" in n["type"]) or "properties" in n:
            props = n.get("properties") or {}
            req = set(n.get("required") or [])
            n["properties"] = {k: (v if k in req else _nullable(v)) for k, v in props.items()}
            n["required"] = list(props)
            n["additionalProperties"] = False
        return n

    return walk(s)


def strip_nulls(v):
    if isinstance(v, dict):
        return {k: strip_nulls(x) for k, x in v.items() if x is not None}
    if isinstance(v, list):
        return [strip_nulls(x) for x in v]
    return v


class CodexProvider:
    name = "codex"

    def __init__(self, path: str, model: str, timeout_s: int):
        self.path = path
        self.model = model
        self.timeout_s = timeout_s

    def complete_json(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult:
        effort = _EFFORT_MAP.get(effort, effort)
        env = {k: v for k, v in os.environ.items()
               if k not in ("OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                            "DATABASE_URL")}
        full = (f"<instructions>\n{system}\n</instructions>\n\n{prompt}\n\n"
                "Answer directly from your own reasoning; do not run commands or read files. "
                "Respond only with JSON matching the required output schema.")
        with tempfile.TemporaryDirectory(prefix="mrl-cx-") as cwd:
            sp, lp = os.path.join(cwd, "schema.json"), os.path.join(cwd, "last.txt")
            with open(sp, "w") as f:
                json.dump(strictify(schema), f)
            cmd = [self.path, "exec", "-m", self.model, "-s", "read-only", "--skip-git-repo-check", "--ephemeral",
                   "--ignore-user-config", "--json", "--output-schema", sp, "-o", lp]
            if effort in _EFFORTS:
                cmd += ["-c", f'model_reasoning_effort="{effort}"']
            cmd.append("-")
            try:
                proc = subprocess.run(cmd, input=full, capture_output=True, text=True, cwd=cwd, env=env,
                                      timeout=self.timeout_s)
            except subprocess.TimeoutExpired as e:
                raise LLMError(f"Codex call timed out after {self.timeout_s}s") from e
            except OSError as e:
                raise LLMError(f"Could not start Codex CLI: {e}") from e
            try:
                text = open(lp).read().strip()
            except OSError:
                text = ""

        usage, error = {}, None
        for line in proc.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "turn.completed":
                usage = ev.get("usage") or {}
            elif ev.get("type") in ("error", "turn.failed"):
                error = (ev.get("error") or {}).get("message") or ev.get("message") or error
        cached = usage.get("cached_input_tokens") or 0
        result = LLMResult(
            data={}, provider=self.name, model=self.model,
            input_tokens=max(0, (usage.get("input_tokens") or 0) - cached),
            output_tokens=(usage.get("output_tokens") or 0) + (usage.get("reasoning_output_tokens") or 0),
            cache_read_tokens=cached, cost_usd=0.0, raw_text=text,
            meta={"billing": "chatgpt subscription"},
        )
        if error or proc.returncode != 0:
            msg = error or (proc.stderr or proc.stdout or "")[-500:].strip() or f"exit {proc.returncode}"
            raise LLMError(f"Codex call failed: {str(msg)[:500]}", result)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"Codex did not return JSON: {text[:200]}", result) from e
        if not isinstance(data, dict):
            raise LLMError("Codex did not return a JSON object", result)
        result.data = strip_nulls(data)
        return result
