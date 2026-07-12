"""Configuration for E-commerce Automation Agent."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent configuration from environment variables.

    All API keys are optional — the server starts in mock mode without them.
    """

    # Shopify Admin API
    shopify_store_url: Optional[str] = None       # e.g. "https://mystore.myshopify.com"
    shopify_access_token: Optional[str] = None    # Admin API access token
    shopify_oauth_client_id: Optional[str] = None
    shopify_oauth_client_secret: Optional[str] = None
    shopify_oauth_redirect_uri: str = "http://localhost:3009/auth/callback"
    shopify_oauth_authorization_url: str = "http://localhost:3009/auth/start"
    shopify_oauth_scopes: str = "read_products,write_products"
    gateway_base_url: str = "http://localhost:8080"

    # Meta Graph API — Facebook
    fb_access_token: Optional[str] = None         # Page access token
    fb_page_id: Optional[str] = None              # Facebook Page ID

    # Meta Graph API — Instagram
    ig_access_token: Optional[str] = None         # Instagram Business token (usually same as FB)
    ig_user_id: Optional[str] = None              # Instagram Business Account ID

    # Production mode — see src/tools/_production_guard.py.
    # false (default): unconfigured integrations return clearly-labeled mock
    #   data — the right default for demos and the public sandbox.
    # true: unconfigured integrations raise instead of returning mock data —
    #   use this in a real deployment so misconfiguration fails loudly.
    require_live_credentials: bool = False

    # Server
    port: int = 3009
    host: str = "0.0.0.0"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
