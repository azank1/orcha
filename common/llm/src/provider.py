"""Abstract LLM provider and factory function."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import LLMConfig


class LLMProvider(ABC):
    """
    Abstract base class for LLM provider backends (strategy pattern).

    All Metaorcha services that need LLM access should depend on this interface
    rather than a concrete implementation, making it easy to swap providers.
    """

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
    ) -> str:
        """
        Request a chat completion.

        Args:
            model:           Provider-specific model identifier.
            messages:        List of ``{"role": ..., "content": ...}`` dicts.
            response_format: Optional structured output spec, e.g.
                             ``{"type": "json_schema", "json_schema": ...}``.
            temperature:     Sampling temperature (0 = deterministic).

        Returns:
            The assistant's reply as a plain string.
        """

    @abstractmethod
    async def embed(self, text: str, model: str) -> list[float]:
        """
        Generate a text embedding vector.

        Args:
            text:  The input text to embed.
            model: Provider-specific embedding model identifier.

        Returns:
            Embedding as a list of floats.
        """


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function — returns the appropriate concrete LLMProvider.

    Args:
        config: Validated ``LLMConfig`` instance.

    Returns:
        A concrete provider (OpenRouterProvider or OllamaProvider).

    Raises:
        ValueError: If the provider type is unknown.
    """
    from .config import LLMProviderType
    from .ollama import OllamaProvider
    from .openrouter import OpenRouterProvider

    if config.provider == LLMProviderType.OPENROUTER:
        return OpenRouterProvider(config)
    if config.provider == LLMProviderType.OLLAMA:
        return OllamaProvider(config)

    raise ValueError(f"Unknown LLM provider: {config.provider!r}")
