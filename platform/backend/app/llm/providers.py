"""Anthropic and OpenAI implementations of `LLMProvider`, using the official SDKs."""
from __future__ import annotations

import json
import logging

from app.llm.base import LLMError, LLMResult, price

log = logging.getLogger(__name__)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=3, timeout=600)
        self.model = model

    def complete_json(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult:
        a = self._anthropic
        kwargs: dict = dict(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            thinking={"type": "adaptive"},
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        )
        try:
            # Server-side refusal fallback (beta) keeps a classifier false-positive from killing a job.
            if self.model.startswith(("claude-opus-5", "claude-sonnet-5-5", "claude-fable-5")):
                with self.client.beta.messages.stream(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
                ) as stream:
                    resp = stream.get_final_message()
            else:
                with self.client.messages.stream(**kwargs) as stream:
                    resp = stream.get_final_message()
        except a.AuthenticationError as e:
            raise LLMError(f"Anthropic authentication failed: {e.message}") from e
        except a.RateLimitError as e:
            raise LLMError(f"Anthropic rate limit: {e.message}") from e
        except a.BadRequestError as e:
            raise LLMError(f"Anthropic rejected the request: {e.message}") from e
        except a.APIStatusError as e:
            raise LLMError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except a.APIConnectionError as e:
            raise LLMError(f"Could not reach Anthropic API: {e}") from e

        served_model = getattr(resp, "model", self.model) or self.model
        u = resp.usage
        in_tok = (u.input_tokens or 0) + (getattr(u, "cache_creation_input_tokens", 0) or 0)
        cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
        cost, known = price(served_model, in_tok, u.output_tokens or 0, cache_read)
        result = LLMResult(data={}, provider=self.name, model=served_model, input_tokens=in_tok,
                           output_tokens=u.output_tokens or 0, cache_read_tokens=cache_read, cost_usd=cost,
                           stop_reason=resp.stop_reason, meta={"price_known": known})
        if resp.stop_reason == "refusal":
            raise LLMError("Model declined the request (stop_reason=refusal)", result)
        if resp.stop_reason == "max_tokens":
            raise LLMError(f"Response truncated at max_tokens={max_tokens}", result)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        result.raw_text = text
        try:
            result.data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"Model output was not valid JSON: {e}", result) from e
        return result


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str):
        import openai

        self._openai = openai
        self.client = openai.OpenAI(api_key=api_key, max_retries=3, timeout=600)
        self.model = model

    def complete_json(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 16000,
                      effort: str = "high") -> LLMResult:
        o = self._openai
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                response_format={"type": "json_schema",
                                 "json_schema": {"name": "result", "schema": schema, "strict": False}},
                max_completion_tokens=max_tokens,
            )
        except o.AuthenticationError as e:
            raise LLMError(f"OpenAI authentication failed: {e}") from e
        except o.RateLimitError as e:
            raise LLMError(f"OpenAI rate limit: {e}") from e
        except o.APIStatusError as e:
            raise LLMError(f"OpenAI API error {e.status_code}: {e}") from e
        except o.APIConnectionError as e:
            raise LLMError(f"Could not reach OpenAI API: {e}") from e
        choice = resp.choices[0]
        u = resp.usage
        cost, known = price(resp.model, u.prompt_tokens if u else 0, u.completion_tokens if u else 0)
        text = choice.message.content or ""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"Model output was not valid JSON: {e}") from e
        return LLMResult(data=data, provider=self.name, model=resp.model,
                         input_tokens=u.prompt_tokens if u else 0, output_tokens=u.completion_tokens if u else 0,
                         cost_usd=cost, stop_reason=choice.finish_reason, raw_text=text,
                         meta={"price_known": known})
