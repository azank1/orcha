"""Configuration for the Planning & Discovery Service.

Follows the same runtime configuration pattern as the Registry Service:
- pydantic-settings BaseSettings reads from environment / .env file
- Required fields (no default) cause a ValidationError at import time if absent
- An explicit model_validator enforces cross-field constraints (e.g. api_key
  required when using OpenRouter) so the service fails early rather than at
  the first LLM call.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the environment-specific .env file (same pattern as registry)
_environment = os.getenv("ENVIRONMENT", "development")
_env_file = Path(__file__).parent.parent.parent / f".env.{_environment}"
if not _env_file.exists():
    _env_file = Path(__file__).parent.parent.parent / ".env"

load_dotenv(_env_file)


class Settings(BaseSettings):
    """Planning & Discovery Service configuration."""

    model_config = SettingsConfigDict(
        env_file=str(_env_file),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service identity ──────────────────────────────────────────────────────
    service_name: str = "planning-discovery-service"
    service_version: str = "0.1.0"
    environment: str = "development"

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8001
    reload: bool = True

    # ── Required config vars (no default → fail early if absent) ─────────────
    database_url: str
    kafka_bootstrap_servers: str

    # ── LLM ──────────────────────────────────────────────────────────────────
    # Legacy single-provider field — kept for backwards compatibility.
    # When llm_completion_provider / llm_embedding_provider are set the split
    # provider is used instead and this field is ignored.
    llm_provider: str = "openrouter"  # "openrouter" | "ollama"

    # Split-provider configuration (new).
    # llm_completion_provider → text completions (OpenRouter / Ollama)
    # llm_embedding_provider  → embedding generation (Ollama / OpenRouter)
    llm_completion_provider: str = "openrouter"
    llm_embedding_provider: str = "ollama"

    openrouter_api_key: str | None = None
    # Override to point at any OpenAI-compatible endpoint (e.g. Gemini's
    # https://generativelanguage.googleapis.com/v1beta/openai).
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"

    llm_decomposition_model: str = "meta-llama/llama-3.1-8b-instruct"
    llm_fallback_model: str = "openai/gpt-4o"
    llm_embedding_model: str = "openai/text-embedding-3-small"
    # Optional embedding vector size override (e.g. 768 for gemini/openai models
    # that support configurable output dimensions through OpenRouter).
    llm_embedding_dimension: int | None = None
    llm_validation_model: str = "openai/gpt-4o-mini"
    llm_confidence_threshold: float = 0.75
    llm_timeout: int = 60
    llm_max_retries: int = 3

    # ── asyncpg connection pool ───────────────────────────────────────────────
    db_pool_min_size: int = 10
    db_pool_max_size: int = 20

    # ── Kafka consumer groups ─────────────────────────────────────────────────
    kafka_manifest_group_id: str = "planning-manifest-processors"
    kafka_query_group_id: str = "planning-query-handlers"

    # ── Hybrid search ─────────────────────────────────────────────────────────
    similarity_threshold: float = 0.75
    top_k_candidates: int = 5

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _validate_llm_config(self) -> Settings:
        """Fail early if OpenRouter is selected but no API key is provided."""
        needs_openrouter_key = (
            self.llm_provider == "openrouter"
            or self.llm_completion_provider == "openrouter"
            or self.llm_embedding_provider == "openrouter"
        )
        if needs_openrouter_key and not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY must be set when using OpenRouter. "
                "Add it to your .env file or environment."
            )
        if (
            self.llm_embedding_dimension is not None
            and self.llm_embedding_dimension <= 0
        ):
            raise ValueError("LLM_EMBEDDING_DIMENSION must be a positive integer")
        return self


# Module-level singleton — raises ValidationError at import time if config is invalid
settings = Settings()
