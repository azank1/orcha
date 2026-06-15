"""Configuration for Web Scraper Agent."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent configuration from environment variables."""

    # Server
    port: int = 3004
    host: str = "0.0.0.0"

    # LLM (optional — summarize skill)
    openrouter_api_key: str | None = None
    llm_model: str = "anthropic/claude-3.5-sonnet"

    # OAuth providers (optional — authenticated scraping)
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Auth redirect base URL — the external URL this agent is reachable at
    auth_redirect_base: str = "http://localhost:3004"

    # Encryption key for token storage (base64-encoded 32-byte key).
    # If unset, tokens are stored in memory only (cleared on restart).
    token_encryption_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
