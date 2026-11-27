"""Provider-neutral LLM interface.

Agents call `complete_json(...)` with a JSON schema and get back validated JSON plus usage.
Every call (success or failure) is written to `llm_usage` with its cost, and calls are refused
once the configured budget (LLM_BUDGET_USD) has been spent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class LLMUnavailable(Exception):
    """No provider configured (missing API key) or the requested provider is unknown."""


class LLMBudgetExceeded(Exception):
    pass


class LLMError(Exception):
    """A call failed. `result` carries token usage when the API did bill the call (e.g. refusals)."""

    def __init__(self, message: str, result: "LLMResult | None" = None):
        super().__init__(message)
        self.result = result


@dataclass
class LLMResult:
    data: dict
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    stop_reason: str | None = None
    raw_text: str = ""
    meta: dict = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str
    model: str

    def complete_json(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult: ...


# USD per million tokens: (input, output, cache read). Unknown models are recorded with cost 0
# and flagged, rather than guessed.
PRICING: dict[str, tuple[float, float, float]] = {
    "claude-fable-5-2": (8.0, 40.0, 0.20),
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-opus-5": (5.0, 25.0, 0.50),
    "claude-opus-4-8": (5.0, 25.0, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10),
    "claude-sonnet-5": (2.0, 10.0, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "gpt-6.2-astra": (8.0, 40.0, 0.40),
}


def price(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0) -> tuple[float, bool]:
    """Return (cost_usd, known_price)."""
    p = PRICING.get(model) or next((v for k, v in sorted(PRICING.items(), key=lambda kv: -len(kv[0]))
                                    if model.startswith(k + "-")), None)  # dated snapshots, e.g. gpt-6.2-astra-2026-11-17
    if not p:
        return 0.0, False
    return (input_tokens * p[0] + output_tokens * p[1] + cache_read * p[2]) / 1_000_000, True
