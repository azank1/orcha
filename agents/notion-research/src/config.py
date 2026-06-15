"""Configuration for Notion Research Agent"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Agent configuration from environment variables.

    All API keys are optional so the server starts in dev/mock mode
    without a full .env file.
    """

    # Notion API
    notion_api_key: Optional[str] = None

    # Google OAuth (for TradingView access)
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None
    google_oauth_redirect_uri: str = "http://localhost:3003/oauth/callback"

    # OpenRouter for AI analysis
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "anthropic/claude-3.5-sonnet"

    # Web Research (Tavily)
    tavily_api_key: Optional[str] = None

    # Security
    encryption_key: Optional[str] = None

    # Server
    port: int = 3006
    host: str = "0.0.0.0"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
