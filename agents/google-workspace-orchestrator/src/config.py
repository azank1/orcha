"""Environment-driven settings (shared project root .env)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_dotenv() -> Path | None:
    """Prefer repo-root .env: walk parents from this file (stops at root; max 8 levels)."""
    here = Path(__file__).resolve()
    for idx, parent in enumerate(here.parents):
        if idx >= 8:
            break
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_dotenv(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    port: int = Field(default=3011, alias="PORT")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_api_base: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_API_BASE",
    )
    openrouter_model: str = Field(
        default="openrouter/anthropic/claude-sonnet-4-5",
        alias="OPENROUTER_MODEL",
    )

    google_oauth_client_id: str | None = Field(
        default="154461586131-v3n1dt2ffiia1itobhvh4u1pp0mgf04n.apps.googleusercontent.com",
        alias="GOOGLE_OAUTH_CLIENT_ID",
    )
    google_oauth_client_secret: str | None = Field(
        default=None,
        alias="GOOGLE_OAUTH_CLIENT_SECRET",
    )
    google_oauth_redirect_uri: str | None = Field(
        default="http://localhost:3011/auth/callback",
        alias="GOOGLE_OAUTH_REDIRECT_URI",
        description="Must match Authorized redirect URIs in GCP and the redirect_uri used in both authorize and token exchange steps.",
    )
    fastmcp_server_auth_google_jwt_signing_key: str | None = Field(
        default=None,
        alias="FASTMCP_SERVER_AUTH_GOOGLE_JWT_SIGNING_KEY",
        description=(
            "Passed to workspace-mcp when GOOGLE_OAUTH_CLIENT_SECRET is unset (public PKCE client). "
            "If unset, the orchestrator generates an ephemeral key per subprocess (fine for dev)."
        ),
    )
    gateway_base_url: str = Field(
        default="http://localhost:8080",
        alias="GATEWAY_BASE_URL",
        description="Gateway base URL used by agent callback to resume OAuth interrupts.",
    )

    workspace_mcp_port: int = Field(default=8000, alias="WORKSPACE_MCP_PORT")
    workspace_mcp_url: str | None = Field(
        default=None,
        alias="WORKSPACE_MCP_URL",
        description=(
            "Optional override for the workspace-mcp HTTP URL. When unset and MCP_SPAWN_ENABLED=1, "
            "the agent spawns workspace-mcp as a subprocess and calls http://127.0.0.1 on WORKSPACE_MCP_PORT /mcp. "
            "Set this only when MCP runs outside the process (e.g. separate host or sidecar)."
        ),
    )
    workspace_mcp_tool_tier: str = Field(
        default="complete",
        alias="WORKSPACE_MCP_TOOL_TIER",
        description="workspace-mcp tier: core | extended | complete (complete exposes all tools per upstream).",
    )

    mcp_spawn_enabled: bool = Field(default=True, alias="MCP_SPAWN_ENABLED")
    mcp_readiness_timeout: float = Field(
        default=90.0,
        ge=0,
        alias="MCP_READINESS_TIMEOUT",
        description=(
            "Seconds to wait for workspace-mcp HTTP to answer the startup ping. "
            "0 disables the wait (non-blocking; MCP may still be starting). "
            "Readiness runs in the background so the API port stays available for load balancers."
        ),
    )


def mcp_http_url(s: Settings) -> str:
    if s.workspace_mcp_url:
        u = s.workspace_mcp_url.rstrip("/")
        return u if u.endswith("/mcp") else f"{u}/mcp"
    return f"http://127.0.0.1:{s.workspace_mcp_port}/mcp"


settings = Settings()
