"""Composite LLM provider that routes completions and embeddings to different backends."""

from __future__ import annotations

from typing import Any

from .provider import LLMProvider


class SplitLLMProvider(LLMProvider):
    """
    Composite provider that routes complete() → one backend and embed() → another.

    Allows using OpenRouter (Gemini Flash) for text completions and
    Ollama (nomic-embed-text) for embeddings in the same pipeline without
    changing any downstream component.
    """

    def __init__(self, completion: LLMProvider, embedding: LLMProvider) -> None:
        self._completion = completion
        self._embedding = embedding

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        return await self._completion.complete(
            model, messages, response_format, temperature
        )

    async def embed(self, text: str, model: str) -> list[float]:
        return await self._embedding.embed(text, model)
