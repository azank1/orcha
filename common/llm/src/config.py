"""LLM provider configuration models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, model_validator


class LLMProviderType(StrEnum):
    """Supported LLM provider backends."""

    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """
    Configuration for an LLM provider.

    Fails early if ``provider=openrouter`` and ``api_key`` is absent or empty,
    so misconfigured services crash at startup rather than at first LLM call.
    """

    provider: LLMProviderType = LLMProviderType.OPENROUTER

    # OpenRouter-specific
    api_key: str | None = None
    base_url: str = "https://openrouter.ai/api/v1"

    # Ollama-specific (also used as base_url override for openrouter-compatible APIs)
    ollama_base_url: str = "http://localhost:11434"

    # Shared
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    # Optional embedding size override for providers that support it
    # (e.g. OpenRouter/OpenAI-compatible embeddings APIs).
    embedding_dimension: int | None = None

    @model_validator(mode="after")
    def _validate_api_key(self) -> LLMConfig:
        if self.provider == LLMProviderType.OPENROUTER and not self.api_key:
            raise ValueError(
                "api_key is required when provider=openrouter. Set OPENROUTER_API_KEY in your environment."
            )
        if self.embedding_dimension is not None and self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be a positive integer")
        return self
