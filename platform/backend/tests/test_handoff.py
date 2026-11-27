"""Provider hand-off: a resting provider's work goes to the other model; a usage-limit failure is retried elsewhere."""
import time

import pytest

from app.llm import registry as R
from app.llm.base import LLMError, LLMResult


class Fake:
    def __init__(self, name, fail=None, rate_limit=None):
        self.name, self.model, self.fail, self.rate_limit, self.calls = name, name + "-model", fail, rate_limit, 0

    def complete_json(self, **_):
        self.calls += 1
        if self.fail:
            raise LLMError(self.fail)
        return LLMResult(data={"ok": self.name}, provider=self.name, model=self.model,
                         meta={"rate_limit": self.rate_limit} if self.rate_limit else {})


@pytest.fixture
def two(monkeypatch, tmp_path):
    monkeypatch.setattr(R, "_health_path", lambda: tmp_path / "health.json")
    monkeypatch.setattr(R, "available_providers", lambda: ["claude_code", "codex"])
    fakes = {"claude_code": Fake("claude_code"), "codex": Fake("codex")}
    monkeypatch.setattr(R, "get_provider", lambda name=None: fakes[name or "claude_code"])
    return fakes


def call(provider="claude_code"):
    return R.tracked_json_call(purpose="research:test", system="s", prompt="p", schema={}, provider=provider)


def test_healthy_provider_is_used(two):
    assert call().data == {"ok": "claude_code"}


def test_claude_over_threshold_hands_off_to_codex(two):
    now = time.time()
    two["claude_code"].rate_limit = {"status": "allowed", "unifiedWindows": {
        "five_hour": {"utilization": 0.93, "resetsAt": now + 3600}, "seven_day": {"utilization": 0.2, "resetsAt": now + 86400}}}
    assert call().data == {"ok": "claude_code"}  # this call reports 93% ...
    assert R.resting("claude_code")[0]
    assert call().data == {"ok": "codex"}  # ... so the next one goes to Codex
    assert R.next_available_at() is None


def test_usage_limit_failure_retries_on_other_provider(two):
    two["claude_code"].fail = "Claude Code call failed: You've hit your usage limit · resets 8pm (UTC)"
    assert call().data == {"ok": "codex"}
    assert R.resting("claude_code")[0]
    assert two["claude_code"].calls == 1


def test_codex_limit_hands_back_to_claude(two):
    two["codex"].fail = "Codex call failed: You've hit your usage limit. Try again in 2 hours 5 minutes."
    assert call("codex").data == {"ok": "claude_code"}
    r, until, _ = R.resting("codex")
    assert r and until - time.time() > 2 * 3600


def test_both_resting_raises_usage_limit(two):
    two["claude_code"].fail = "429 usage limit"
    two["codex"].fail = "hit your usage limit"
    with pytest.raises(LLMError, match="usage limit"):
        call()
    assert R.next_available_at() is not None


def test_non_limit_errors_are_not_retried(two):
    two["claude_code"].fail = "Model output was not valid JSON"
    with pytest.raises(LLMError, match="valid JSON"):
        call()
    assert two["codex"].calls == 0 and not R.resting("claude_code")[0]
