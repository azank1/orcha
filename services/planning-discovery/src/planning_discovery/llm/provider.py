"""LLM Provider utilities for the Planning & Discovery service.

The shared base ``LLMProvider`` ABC lives in ``common.llm.src.provider``.
This module provides:
- ``MockLLMProvider``: Deterministic provider for testing
- ``create_llm_provider``: Factory that creates a real or mock provider
- Re-exports of ``LLMUsage`` / ``TrackedLLMProvider`` for convenience
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import structlog

from common.llm.src.provider import LLMProvider

from .tracked_provider import CumulativeStats, LLMUsage, TrackedLLMProvider

logger = structlog.get_logger()

# Re-export for backward compatibility
__all__ = [
    "CumulativeStats",
    "LLMProvider",
    "LLMUsage",
    "MockLLMProvider",
    "TrackedLLMProvider",
    "create_llm_provider",
]


# ── Mock Provider ────────────────────────────────────────────────────────────


class MockLLMProvider(LLMProvider):
    """Deterministic provider for testing.

    Configure canned responses via ``add_response()``.  Calls are tracked
    for assertion in tests.  Implements the ``common.llm`` interface
    (``complete()`` returns ``str``).
    """

    def __init__(self) -> None:
        self.responses: list[str] = []
        self.embeddings: list[list[float]] = []
        self.call_log: list[dict[str, Any]] = []
        self._response_idx = 0
        self._embedding_idx = 0

    def add_response(self, content: str) -> MockLLMProvider:
        """Queue a response for the next ``complete()`` call."""
        self.responses.append(content)
        return self

    def add_json_response(self, data: dict[str, Any]) -> MockLLMProvider:
        """Queue a JSON response."""
        self.responses.append(json.dumps(data))
        return self

    def add_embedding(self, embedding: list[float]) -> MockLLMProvider:
        """Queue an embedding for the next ``embed()`` call."""
        self.embeddings.append(embedding)
        return self

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.call_log.append(
            {
                "type": "complete",
                "model": model,
                "messages": messages,
                "response_format": response_format,
            }
        )
        if self._response_idx < len(self.responses):
            content = self.responses[self._response_idx]
            self._response_idx += 1
        else:
            content = '{"error": "no mock response configured"}'

        return content

    async def embed(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> list[float]:
        self.call_log.append({"type": "embed", "model": model, "text_len": len(text)})
        if self._embedding_idx < len(self.embeddings):
            emb = self.embeddings[self._embedding_idx]
            self._embedding_idx += 1
            return emb
        # Return a deterministic fake embedding
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h] * 48  # 1536 dims


# ── Factory ──────────────────────────────────────────────────────────────────


def create_llm_provider(
    provider_type: str = "mock",
    api_key: str | None = None,
    base_url: str | None = None,
    embedding_dimension: int | None = None,
) -> LLMProvider:
    """Factory function to create the appropriate LLM provider.

    For ``"openrouter"`` and ``"ollama"``, delegates to ``common.llm``
    and wraps the result in ``TrackedLLMProvider`` for cost tracking.
    For ``"mock"``, returns a bare ``MockLLMProvider``.
    """
    if provider_type == "mock":
        return MockLLMProvider()

    from common.llm.src import LLMConfig, LLMProviderType
    from common.llm.src import create_llm_provider as _create

    if provider_type == "openrouter":
        if not api_key:
            raise ValueError("OpenRouter provider requires an API key")
        config = LLMConfig(
            provider=LLMProviderType.OPENROUTER,
            api_key=api_key,
            base_url=base_url or "https://openrouter.ai/api/v1",
            embedding_dimension=embedding_dimension,
        )
        return TrackedLLMProvider(_create(config))

    if provider_type == "ollama":
        config = LLMConfig(
            provider=LLMProviderType.OLLAMA,
            ollama_base_url=base_url or "http://localhost:11434",
            embedding_dimension=embedding_dimension,
        )
        return TrackedLLMProvider(_create(config))

    raise ValueError(f"Unknown LLM provider type: {provider_type}")
