"""LLM provider that runs the Claude Code CLI (`claude -p`) under the user's own subscription login.

No API key and no per-call billing: usage counts against the user's Claude plan limits. The call
runs with every built-in tool and MCP server disabled, in an empty temporary directory, with
ANTHROPIC_API_KEY removed from its environment so it can never silently fall back to API billing.
The CLI's `total_cost_usd` is a list-price *equivalent*, stored in `meta` only; the billed cost
recorded in `llm_usage` is 0.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile

from app.llm.base import LLMError, LLMResult

_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


class ClaudeCodeProvider:
    name = "claude_code"

    def __init__(self, path: str, model: str, timeout_s: int):
        self.path = path
        self.model = model
        self.timeout_s = timeout_s

    def complete_json(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult:
        # stream-json (with --verbose) adds a rate_limit_event carrying plan utilization per window, which the
        # registry uses to hand work to another provider before the limit is actually hit.
        cmd = [self.path, "-p", "--output-format", "stream-json", "--verbose", "--json-schema", json.dumps(schema),
               "--system-prompt", system, "--model", self.model, "--tools", "", "--strict-mcp-config",
               "--no-session-persistence"]
        if effort in _EFFORTS:
            cmd += ["--effort", effort]
        env = {k: v for k, v in os.environ.items()
               if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY", "DATABASE_URL")}
        with tempfile.TemporaryDirectory(prefix="mrl-cc-") as cwd:
            try:
                proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd, env=env,
                                      timeout=self.timeout_s)
            except subprocess.TimeoutExpired as e:
                raise LLMError(f"Claude Code call timed out after {self.timeout_s}s") from e
            except OSError as e:
                raise LLMError(f"Could not start Claude Code CLI: {e}") from e
        out, rate_limit = None, None
        for line in proc.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                out = ev
            elif ev.get("type") == "rate_limit_event":
                rate_limit = ev.get("rate_limit_info") or rate_limit
        if out is None:
            tail = (proc.stderr or proc.stdout or "")[-500:].strip()
            err = LLMError(f"Claude Code returned no result (exit {proc.returncode}): {tail}")
            if rate_limit:
                err.result = LLMResult(data={}, provider=self.name, model=self.model, meta={"rate_limit": rate_limit})
            raise err

        mu = out.get("modelUsage") or {}
        served = next(iter(mu), self.model)
        u = out.get("usage") or {}
        in_tok = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        result = LLMResult(
            data={}, provider=self.name, model=served, input_tokens=in_tok,
            output_tokens=u.get("output_tokens") or 0, cache_read_tokens=u.get("cache_read_input_tokens") or 0,
            cost_usd=0.0, stop_reason=out.get("subtype"), raw_text=out.get("result") or "",
            meta={"billing": "claude subscription", "list_price_equivalent_usd": out.get("total_cost_usd"),
                  "session_id": out.get("session_id"), "num_turns": out.get("num_turns"), "rate_limit": rate_limit},
        )
        if out.get("is_error") or out.get("subtype") != "success":
            msg = out.get("result") or out.get("subtype") or "unknown error"
            if out.get("api_error_status"):
                msg = f"API error {out['api_error_status']}: {msg}"
            raise LLMError(f"Claude Code call failed: {str(msg)[:500]}", result)
        data = out.get("structured_output")
        if not isinstance(data, dict):
            try:
                data = json.loads(result.raw_text)
            except (json.JSONDecodeError, TypeError) as e:
                raise LLMError("Claude Code did not return structured JSON output", result) from e
        result.data = data
        return result
