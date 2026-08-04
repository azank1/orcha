"""Shared fail-closed guard for the mock-fallback pattern used across
shopify.py / facebook.py / instagram.py.

By default this agent runs mock-safe: any tool called without the relevant
credentials configured returns a clearly-labeled `{"status": "mock", ...}`
payload instead of erroring. That's the right default for demos and the
public sandbox. It's the wrong default for a real production deployment,
where silently returning fake data for a misconfigured integration can be
mistaken for a real write (e.g. "created" a product that was never actually
created on Shopify).

Set REQUIRE_LIVE_CREDENTIALS=true to flip that: unconfigured integrations
raise instead of returning mock data, so misconfiguration fails loudly at
call time rather than silently at the data layer.
"""

from __future__ import annotations


def is_production_mode() -> bool:
    # Read from the Settings object (pydantic-settings), not os.environ
    # directly — Settings loads `.env` regardless of whether the process was
    # started via a shell that sourced it (local `uv run`) or via Docker
    # (which populates os.environ only if the compose file says so).
    from ..config import settings

    return bool(settings.require_live_credentials)


def require_configured(configured: bool, service: str, missing_env: str) -> bool:
    """Return `configured` unchanged, unless production mode demands otherwise.

    Call this in place of a bare `_is_configured()` check. If
    REQUIRE_LIVE_CREDENTIALS=true and the integration isn't configured, raises
    instead of letting the caller silently fall through to a mock branch.
    """
    if not configured and is_production_mode():
        raise RuntimeError(
            f"{service} is not configured (missing {missing_env}) and "
            "REQUIRE_LIVE_CREDENTIALS=true — refusing to return mock data. "
            "Set the required credentials, or unset REQUIRE_LIVE_CREDENTIALS "
            "for demo/mock mode."
        )
    return configured
