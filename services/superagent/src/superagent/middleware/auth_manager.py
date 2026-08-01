"""AuthManager — resolves credentials for agent calls using 5 strategies."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# OAuth token cache: (agent_id, user_id) → (access_token, expiry_ts)
_oauth_cache: dict[tuple[str, str], tuple[str, float]] = {}


class AuthResolutionError(Exception):
    """Raised when no auth strategy succeeds and HITL is required."""


class AuthManager:
    """
    Resolves auth credentials for an agent.

    Strategy order (first success wins):
    1. NONE — agent requires no auth
    2. X_API_KEY / HTTP_BEARER — from VaultClient (user secret or global)
    3. OAUTH2 — cached token or refresh
    4. OAUTH2_DCR — Dynamic Client Registration
    5. HITL — raise AuthResolutionError to trigger interrupt
    """

    def __init__(self, vault: Any) -> None:
        self._vault = vault

    async def resolve(
        self,
        agent_id: str,
        user_id: str,
        auth_strategies: list[dict[str, Any]],
    ) -> dict[str, str]:
        """
        Return HTTP headers dict with resolved credentials.

        Raises AuthResolutionError if all strategies fail (triggers HITL).
        """
        if not auth_strategies:
            return {}

        for strategy in auth_strategies:
            strategy_type = strategy.get("type", "")
            config = strategy.get("config", {})
            try:
                headers = await self._try_strategy(
                    strategy_type, config, agent_id, user_id
                )
                if headers is not None:
                    return headers
            except Exception:
                logger.debug("Auth strategy %r failed for %s", strategy_type, agent_id)
                continue

        raise AuthResolutionError(f"All auth strategies exhausted for agent {agent_id}")

    async def _try_strategy(
        self,
        strategy_type: str,
        config: dict[str, Any],
        agent_id: str,
        user_id: str,
    ) -> dict[str, str] | None:
        if strategy_type == "X_API_KEY":
            key_ref = config.get("key_vault_ref") or config.get("header_value")
            if key_ref:
                secret = await self._vault.get_user_secret(user_id, key_ref)
                if secret:
                    header_name = config.get("header_name", "X-Api-Key")
                    return {header_name: secret}

        elif strategy_type == "HTTP_BEARER":
            key_ref = config.get("token_vault_ref") or config.get("key_vault_ref")
            if key_ref:
                token = await self._vault.get_user_secret(user_id, key_ref)
                if token:
                    return {"Authorization": f"Bearer {token}"}

        elif strategy_type == "OAUTH2":
            return await self._oauth2(config, agent_id, user_id)

        elif strategy_type == "OAUTH2_DCR":
            return await self._oauth2_dcr(config, agent_id, user_id)

        elif strategy_type in ("PLATFORM_ENV", "platform_env"):
            # Credentials are already in SuperAgent os.environ.
            # MCPHandler passes {**os.environ} to the subprocess — no headers needed.
            return {}

        return None

    async def _oauth2(
        self,
        config: dict[str, Any],
        agent_id: str,
        user_id: str,
    ) -> dict[str, str] | None:
        """Return bearer token from cache or refresh."""
        cache_key = (agent_id, user_id)
        cached = _oauth_cache.get(cache_key)
        if cached:
            token, expiry = cached
            if time.monotonic() < expiry - 60:  # 60s buffer
                return {"Authorization": f"Bearer {token}"}

        # Refresh using stored refresh token
        import httpx

        refresh_token = await self._vault.get_user_secret(
            user_id, config.get("refresh_token_key", f"{agent_id}_refresh_token")
        )
        if not refresh_token:
            return None

        token_url = config.get("token_url", "")
        client_id = config.get("client_id", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        _oauth_cache[cache_key] = (access_token, time.monotonic() + expires_in)
        return {"Authorization": f"Bearer {access_token}"}

    async def _oauth2_dcr(
        self,
        config: dict[str, Any],
        agent_id: str,
        user_id: str,
    ) -> dict[str, str] | None:
        """Dynamic Client Registration flow."""
        import httpx

        reg = await self._vault.get_agent_registration(agent_id, user_id)
        if not reg:
            return None

        client_id = reg.get("client_id")
        client_secret = reg.get("client_secret")
        token_url = config.get("token_url", "")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return {"Authorization": f"Bearer {data['access_token']}"}
