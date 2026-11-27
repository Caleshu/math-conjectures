"""Provider selection, budget enforcement, usage recording, and hand-off between providers.

Hand-off: each provider has a health record in DATA_DIR/provider_health.json. A provider is "resting" while it is
over its usage limit, or (Claude Code, which reports plan utilization) once any usage window reaches
CLAUDE_HANDOFF_UTILIZATION (default 90%), until that window resets. Calls to a resting provider go to the other
model family instead; a call that hits a usage limit marks the provider resting and is retried once elsewhere.
Work only stops when every provider is resting.
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.config import get_settings
from app.db import session_scope
from app.llm.base import LLMBudgetExceeded, LLMError, LLMProvider, LLMResult, LLMUnavailable
from app.models import LLMUsage


def available_providers() -> list[str]:
    s = get_settings()
    out = []
    if s.anthropic_api_key:
        out.append("anthropic")
    from app.config import _claude_code_path
    if _claude_code_path():
        out.append("claude_code")
    from app.config import _codex_path
    if _codex_path():
        out.append("codex")
    if s.openai_api_key:
        out.append("openai")
    return out


def default_provider() -> str | None:
    s = get_settings()
    if s.default_llm_provider != "auto":
        return s.default_llm_provider
    avail = available_providers()
    return avail[0] if avail else None


def get_provider(name: str | None = None) -> LLMProvider:
    s = get_settings()
    name = name or default_provider()
    if name is None:
        raise LLMUnavailable("No AI provider available: install/log in to Claude Code, or set ANTHROPIC_API_KEY")
    if name == "anthropic":
        if not s.anthropic_api_key:
            raise LLMUnavailable("Anthropic is not configured: set ANTHROPIC_API_KEY in .env")
        from app.llm.providers import AnthropicProvider
        return AnthropicProvider(s.anthropic_api_key, s.anthropic_model)
    if name == "claude_code":
        from app.config import _claude_code_path
        path = _claude_code_path()
        if not path:
            raise LLMUnavailable("Claude Code CLI not found (or CLAUDE_CODE_ENABLED=false)")
        from app.llm.claude_code import ClaudeCodeProvider
        return ClaudeCodeProvider(path, s.claude_code_model, s.claude_code_timeout_s)
    if name == "codex":
        from app.config import _codex_path
        path = _codex_path()
        if not path:
            raise LLMUnavailable("Codex CLI not found or not logged in (run `codex login`, or CODEX_ENABLED=false)")
        from app.llm.codex import CodexProvider
        return CodexProvider(path, s.codex_model, s.codex_timeout_s)
    if name == "openai":
        if not s.openai_api_key:
            raise LLMUnavailable("OpenAI is not configured: set OPENAI_API_KEY in .env")
        from app.llm.providers import OpenAIProvider
        return OpenAIProvider(s.openai_api_key, s.openai_model)
    raise LLMUnavailable(f"Unknown LLM provider '{name}'")


# ------------------------------------------------------------------------------------------
# Provider health and hand-off
# ------------------------------------------------------------------------------------------
CLAUDE_PROVIDERS = ("claude_code", "anthropic")
GPT_PROVIDERS = ("codex", "openai")
_LIMIT_RE = re.compile(r"429|rate.?limit|usage limit|hit your .*limit|quota|not logged in|please run /login", re.I)
_health_lock = threading.Lock()


def _health_path():
    return get_settings().data_dir / "provider_health.json"


def load_health() -> dict:
    try:
        return json.loads(_health_path().read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _update_health(provider: str, **fields) -> None:
    with _health_lock:
        h = load_health()
        h[provider] = {**h.get(provider, {}), **fields, "updated": time.time()}
        try:
            _health_path().write_text(json.dumps(h, indent=1))
        except OSError:
            pass


def record_rate_limit(provider: str, info: dict | None) -> None:
    """Store the plan utilization a provider reported (Claude Code's rate_limit_event)."""
    if not info:
        return
    windows = {name: {"utilization": w.get("utilization"), "resets_at": w.get("resetsAt")}
               for name, w in (info.get("unifiedWindows") or {}).items()}
    fields = {"windows": windows, "status": info.get("status")}
    if info.get("status") == "rejected" and info.get("resetsAt"):
        fields["limited_until"] = float(info["resetsAt"])
    _update_health(provider, **fields)


def mark_limited(provider: str, until: float, reason: str) -> None:
    _update_health(provider, limited_until=until, reason=reason[:300])


def resting(provider: str) -> tuple[bool, float | None, str]:
    """(is resting, until when (unix time), why)."""
    h = load_health().get(provider) or {}
    now = time.time()
    if (h.get("limited_until") or 0) > now:
        return True, h["limited_until"], f"usage limit ({h.get('reason') or 'limit reached'})"
    thr = get_settings().claude_handoff_utilization
    for name, w in (h.get("windows") or {}).items():
        u, r = w.get("utilization") or 0, w.get("resets_at") or 0
        if u >= thr and r > now:
            return True, float(r), f"{name.replace('_', '-')} usage at {u:.0%} (hand-off threshold {thr:.0%})"
    return False, None, ""


def provider_status() -> list[dict]:
    out = []
    for p in available_providers():
        r, until, why = resting(p)
        h = load_health().get(p) or {}
        out.append({"provider": p, "resting": r, "until": datetime.fromtimestamp(until, timezone.utc).isoformat() if until else None,
                    "reason": why or None, "windows": h.get("windows") or {}})
    return out


def next_available_at() -> datetime | None:
    """None when some provider can take work now; otherwise when the first one comes back."""
    times = []
    for p in available_providers():
        r, until, _ = resting(p)
        if not r:
            return None
        times.append(until or time.time() + 900)
    return datetime.fromtimestamp(min(times), timezone.utc) if times else None


def route(name: str) -> str:
    """The provider that should actually serve a call meant for `name`."""
    if not resting(name)[0]:
        return name
    same = CLAUDE_PROVIDERS if name in CLAUDE_PROVIDERS else GPT_PROVIDERS
    avail = available_providers()
    order = [p for p in avail if p not in same] + [p for p in avail if p in same and p != name]
    for p in order:
        if not resting(p)[0]:
            return p
    t = next_available_at()
    raise LLMError(f"usage limit: every AI provider is resting; first one back at {t.isoformat() if t else 'unknown'}")


def _limit_until(err: LLMError) -> float:
    """When a provider that just refused a call should be tried again."""
    info = ((err.result.meta if err.result else {}) or {}).get("rate_limit") or {}
    if info.get("resetsAt"):
        return float(info["resetsAt"]) + 60
    msg = str(err)
    if re.search(r"not logged in|please run /login", msg, re.I):
        return time.time() + 15 * 60
    m = re.search(r"try again in\s+((?:\d+\s*(?:days?|d|hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b[\s,and]*)+)", msg, re.I)
    if m:
        secs = 0
        for n, unit in re.findall(r"(\d+)\s*([a-z]+)", m.group(1), re.I):
            u = unit.lower()
            secs += int(n) * (86400 if u.startswith("d") else 3600 if u.startswith("h") else 60 if u.startswith("m") else 1)
        return time.time() + secs + 60
    from app.autopilot import reset_time  # "resets 8:50pm (America/New_York)"; falls back to 15 minutes
    return reset_time(msg).timestamp()


def total_spend_usd() -> float:
    with session_scope() as db:
        return float(db.scalar(select(func.coalesce(func.sum(LLMUsage.cost_usd), 0.0))) or 0.0)


def _record(provider: LLMProvider, purpose: str, res: LLMResult | None, job_id: str | None,
            subject_id: str | None, error: str | None) -> None:
    with session_scope() as db:
        db.add(LLMUsage(
            provider=provider.name, model=res.model if res else provider.model, purpose=purpose,
            input_tokens=res.input_tokens if res else 0, output_tokens=res.output_tokens if res else 0,
            cache_read_tokens=res.cache_read_tokens if res else 0, cost_usd=res.cost_usd if res else 0.0,
            job_id=job_id, subject_id=subject_id, success=error is None, error=error,
        ))


def tracked_json_call(*, purpose: str, system: str, prompt: str, schema: dict, provider: str | None = None,
                      job_id: str | None = None, subject_id: str | None = None, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult:
    """The only entry point agents should use. Enforces budget, records usage, and hands off to another provider
    when the requested one is resting or hits its usage limit."""
    budget = get_settings().llm_budget_usd
    spent = total_spend_usd()  # subscription calls are recorded at $0 billed, so they never consume this
    if spent >= budget:
        raise LLMBudgetExceeded(f"LLM budget exhausted: ${spent:.2f} spent of ${budget:.2f} (LLM_BUDGET_USD)")
    name = provider or _preferred(purpose)
    if name is None:
        get_provider(None)  # raises LLMUnavailable with the setup hint
    tried: set[str] = set()
    while True:
        actual = route(name) if name not in tried else next(
            (p for p in available_providers() if p not in tried and not resting(p)[0]), None)
        if actual is None or actual in tried:
            raise LLMError(f"usage limit: no other AI provider can take '{purpose}' right now")
        tried.add(actual)
        p = get_provider(actual)
        try:
            res = p.complete_json(system=system, prompt=prompt, schema=schema, max_tokens=max_tokens, effort=effort)
        except LLMError as e:
            _record(p, purpose, e.result, job_id, subject_id, str(e))
            if e.result:
                record_rate_limit(actual, (e.result.meta or {}).get("rate_limit"))
            if _LIMIT_RE.search(str(e)) and len(tried) < 3:
                mark_limited(actual, _limit_until(e), str(e))
                continue  # hand off to the next provider that is not resting
            raise
        except Exception as e:
            _record(p, purpose, None, job_id, subject_id, f"{type(e).__name__}: {e}")
            raise LLMError(f"{type(e).__name__}: {e}") from e
        _record(p, purpose, res, job_id, subject_id, None)
        record_rate_limit(actual, (res.meta or {}).get("rate_limit"))
        return res


def _preferred(purpose: str) -> str | None:
    """Research calls default to the configured provider; background work (novelty pre-checks, paper extraction)
    goes to BACKGROUND_LLM_PROVIDER (default codex) when available, which keeps Claude usage for research."""
    bg = get_settings().background_llm_provider
    if not purpose.startswith("research") and bg and bg in available_providers():
        return bg
    return default_provider()
