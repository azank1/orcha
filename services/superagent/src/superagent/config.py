"""SuperAgent settings — fail-early at module import if env vars are missing."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    # LLM / OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Orchestration LLM (OpenRouter id). Override with ORCHESTRATOR_MODEL — prefer a small/cheap
    # model here (e.g. Haiku, Gemini Flash); keep sonnet only if you need heavier reasoning.
    orchestrator_model: str = "anthropic/claude-3.5-haiku"
    # PnD gate Tier-3 classifier — cheap model is fine (same env pattern as orchestrator).
    small_model: str = "anthropic/claude-3.5-haiku"

    # Infrastructure
    redis_url: str
    database_url: str
    vault_key: str  # base64-encoded 32-byte key for AES-256-GCM

    # Dependent services
    pnd_service_url: str
    registry_service_url: str = "http://localhost:8000"
    registry_internal_key: str = "dev-internal-secret"

    # Platform MCP secrets (optional — read from .env; copied to os.environ at boot for
    # PlatformToolSeeder checks and stdio MCP subprocess env)
    tavily_api_key: str | None = None
    firecrawl_api_key: str | None = None

    # Platform tool manifests (common/emerge-tools — manifests + servers/Chomper)
    # Overridable via EMERGE_TOOLS_DIR — container default matches Dockerfile COPY
    emerge_tools_dir: str = "/app/common/emerge-tools"

    # S3 / Artifact storage (boto3 — LocalStack in dev, real AWS in prod)
    artifact_s3_bucket: str = "emerge-artifacts-local"
    s3_endpoint_url: str | None = (
        None  # None = real AWS; set to http://localstack:4566 for dev
    )
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region: str = "us-east-1"

    # Server
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8002
    log_level: str = "info"

    # Context window
    token_budget: int = 140_000
    compression_threshold: float = 0.85  # compress when usage > 85% of budget
    keep_last_messages: int = 15

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")


# Raises pydantic.ValidationError at import time if required vars are missing
settings = Settings()
