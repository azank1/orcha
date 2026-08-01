"""Tracked LLM provider — wraps common.llm.LLMProvider with cost & latency tracking.

The common.llm.LLMProvider ABC returns plain ``str`` from ``complete()``.
This wrapper adds per-call ``LLMUsage`` recording and cumulative statistics,
which are used by the P&D pipeline for telemetry and cost budgeting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from common.llm.src.provider import LLMProvider as BaseLLMProvider

logger = structlog.get_logger()


@dataclass
class LLMUsage:
    """Token usage and cost tracking for a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    latency_ms: float = 0.0


# Approximate per-token pricing (USD) for common models
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "anthropic/claude-3.5-sonnet": (3e-6, 15e-6),
    "anthropic/claude-3-haiku": (0.25e-6, 1.25e-6),
    "google/gemini-1.5-flash": (0.075e-6, 0.3e-6),
    "openai/gpt-4o": (2.5e-6, 10e-6),
    "openai/gpt-4o-mini": (0.15e-6, 0.6e-6),
    "meta-llama/llama-3.1-8b-instruct": (0.055e-6, 0.055e-6),
}


@dataclass
class CumulativeStats:
    """Cumulative usage stats across all calls."""

    total_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    calls: list[LLMUsage] = field(default_factory=list)

    def record(self, usage: LLMUsage) -> None:
        self.total_calls += 1
        self.total_tokens += usage.total_tokens
        self.total_cost_usd += usage.cost_usd
        self.total_latency_ms += usage.latency_ms
        self.calls.append(usage)


class TrackedLLMProvider(BaseLLMProvider):
    """Decorator around a ``common.llm.LLMProvider`` that records usage stats.

    Implements the same ``complete()`` / ``embed()`` interface so it can be
    used anywhere a ``BaseLLMProvider`` is expected.  Additionally exposes
    ``tracked_complete()`` which returns the raw content *plus* an ``LLMUsage``
    record.

    Usage::

        from common.llm.src import create_llm_provider, LLMConfig
        inner = create_llm_provider(config)
        tracked = TrackedLLMProvider(inner)
        content = await tracked.complete(model, messages)
        print(tracked.stats.total_cost_usd)
    """

    def __init__(self, inner: BaseLLMProvider) -> None:
        self._inner = inner
        self.stats = CumulativeStats()

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        content, _ = await self.tracked_complete(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )
        return content

    async def tracked_complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> tuple[str, LLMUsage]:
        """Like ``complete()`` but also returns an ``LLMUsage`` record."""
        t0 = time.monotonic()
        content = await self._inner.complete(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )
        latency_ms = (time.monotonic() - t0) * 1000

        # Estimate tokens from content length (rough, but works without API info)
        prompt_tok = sum(len(m.get("content", "")) for m in messages) // 4
        comp_tok = len(content) // 4

        pricing = MODEL_PRICING.get(model, (3e-6, 15e-6))
        cost = prompt_tok * pricing[0] + comp_tok * pricing[1]

        usage = LLMUsage(
            prompt_tokens=prompt_tok,
            completion_tokens=comp_tok,
            total_tokens=prompt_tok + comp_tok,
            cost_usd=cost,
            model=model,
            latency_ms=latency_ms,
        )
        self.stats.record(usage)

        logger.debug(
            "llm_tracked_complete",
            model=model,
            tokens=usage.total_tokens,
            cost_usd=round(usage.cost_usd, 6),
            latency_ms=round(latency_ms, 1),
        )
        return content, usage

    async def embed(self, text: str, model: str) -> list[float]:
        t0 = time.monotonic()
        result = await self._inner.embed(text, model)
        latency_ms = (time.monotonic() - t0) * 1000
        logger.debug(
            "llm_tracked_embed",
            model=model,
            dims=len(result),
            latency_ms=round(latency_ms, 1),
        )
        return result
