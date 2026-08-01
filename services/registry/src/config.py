"""Configuration settings for Registry service."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine environment and load appropriate .env file
_environment = os.getenv("ENVIRONMENT", "development")
_env_file = Path(__file__).parent.parent / f".env.{_environment}"

# Fall back to .env if environment-specific file doesn't exist
if not _env_file.exists():
    _env_file = Path(__file__).parent.parent / ".env"

load_dotenv(_env_file)


class Settings(BaseSettings):
    """Registry service configuration."""

    model_config = SettingsConfigDict(
        env_file=str(_env_file),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service
    service_name: str = "registry-service"
    service_version: str = "1.0.0"
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    reload: bool = True

    # gRPC
    grpc_host: str = "[::]"
    grpc_port: int = 50051

    # Database
    database_url: str

    # Security
    pat_token_prefix: str = "orcha_pat_"  # noqa: S105
    pat_token_length: int = 40

    # Adapter Settings
    adapter_timeout: int = 10
    adapter_max_retries: int = 3
    adapter_base_delay: float = 1.0

    # Health Check
    health_check_interval: int = 300  # 5 minutes in seconds
    max_health_failures: int = 3

    # Payment
    payment_facilitator_url: str = "https://api.orcha.bot/verify"

    # MCP Protocol
    mcp_protocol_version: str = "2025-11-25"

    # Kafka (optional — service runs fine without Kafka, events are silently skipped)
    kafka_bootstrap_servers: str | None = None
    kafka_enabled: bool = False

    # Logging
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
