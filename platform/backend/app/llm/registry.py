"""Provider selection, budget enforcement and usage recording."""
from __future__ import annotations

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
    if name == "openai":
        if not s.openai_api_key:
            raise LLMUnavailable("OpenAI is not configured: set OPENAI_API_KEY in .env")
        from app.llm.providers import OpenAIProvider
        return OpenAIProvider(s.openai_api_key, s.openai_model)
    raise LLMUnavailable(f"Unknown LLM provider '{name}'")


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
    """The only entry point agents should use. Enforces budget and records usage."""
    budget = get_settings().llm_budget_usd
    spent = total_spend_usd()  # subscription calls are recorded at $0 billed, so they never consume this
    if spent >= budget:
        raise LLMBudgetExceeded(f"LLM budget exhausted: ${spent:.2f} spent of ${budget:.2f} (LLM_BUDGET_USD)")
    p = get_provider(provider)
    try:
        res = p.complete_json(system=system, prompt=prompt, schema=schema, max_tokens=max_tokens, effort=effort)
    except LLMError as e:
        _record(p, purpose, e.result, job_id, subject_id, str(e))
        raise
    except Exception as e:
        _record(p, purpose, None, job_id, subject_id, f"{type(e).__name__}: {e}")
        raise LLMError(f"{type(e).__name__}: {e}") from e
    _record(p, purpose, res, job_id, subject_id, None)
    return res
