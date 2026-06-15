"""Redis-backed OAuth grant store with 24-hour TTL.

Grant keys are scoped to (user_id, agent_id, scope) so multiple sessions for
the same user share the same grant — re-authentication happens at most once
per user per 24 hours, not once per session.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_GRANT_TTL = 86400  # 24 hours
_KEY_PREFIX = "superagent:oauth"

_redis_client: Any = None


def _get_redis() -> Any:
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis

        from ..config import settings

        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def capability_grant_key(agent_id: str, capability_id: str) -> str:
    scope = capability_id or "*"
    return f"{agent_id}::{scope}"


def config_grant_key(agent_id: str, provider_name: str, scopes: list[str]) -> str:
    provider = (provider_name or "").strip().lower() or "unknown"
    scope_sig = " ".join(sorted(s.strip() for s in scopes if s.strip()))
    return f"{agent_id}::oauthcfg::{provider}::{scope_sig}"


def _redis_key(user_id: str, scope_key: str) -> str:
    return f"{_KEY_PREFIX}:{user_id}:{scope_key}"


async def has_grant(user_id: str, scope_keys: list[str]) -> bool:
    """Return True if ANY of the given scope keys has a live grant."""
    if not scope_keys:
        return False
    try:
        r = _get_redis()
        full_keys = [_redis_key(user_id, k) for k in scope_keys]
        results = await r.mget(*full_keys)
        return any(v is not None for v in results)
    except Exception:
        logger.warning(
            "oauth_grants: Redis unavailable for has_grant check", exc_info=True
        )
        return False


async def store_grants(user_id: str, scope_keys: list[str]) -> None:
    """Persist all scope_keys as granted for this user with 24-hour TTL."""
    if not scope_keys:
        return
    try:
        r = _get_redis()
        async with r.pipeline() as pipe:
            for k in scope_keys:
                pipe.set(_redis_key(user_id, k), "1", ex=_GRANT_TTL)
            await pipe.execute()
        logger.info(
            "oauth_grants_stored user=%s scope_keys=%s ttl=%ds",
            user_id,
            scope_keys,
            _GRANT_TTL,
        )
    except Exception:
        logger.warning(
            "oauth_grants: Redis unavailable for store_grants", exc_info=True
        )


async def store_grants_for_strategy(
    user_id: str,
    agent_id: str,
    provider_name: str,
    scopes: list[str],
    manifest: dict[str, Any],
) -> None:
    """
    Store OAuth grants for ALL capabilities that use the same auth strategy.

    Resolution: find every auth strategy in the manifest whose config matches
    provider_name + scopes fingerprint, collect all their capability_ids, then
    write a Redis grant for each capability plus the config-level key.
    """
    cfg_key = config_grant_key(agent_id, provider_name, scopes)
    keys: list[str] = [cfg_key]

    # Derive sorted scopes fingerprint to match strategies by config
    target_scopes = sorted(s.strip() for s in scopes if s.strip())

    security = manifest.get("security", {})
    for strategy in security.get("auth_strategies", []):
        cfg = strategy.get("config", {}) or {}
        s_provider = (cfg.get("provider_hint", "") or "").strip().lower()
        s_scopes = sorted(s.strip() for s in (cfg.get("scopes") or []) if s.strip())

        # Match by provider and scopes fingerprint (or either alone as fallback)
        if s_provider and s_provider != (provider_name or "").strip().lower():
            continue
        if s_scopes and s_scopes != target_scopes:
            continue

        for cap_id in strategy.get("capability_ids") or []:
            if cap_id:
                keys.append(capability_grant_key(agent_id, cap_id))

    await store_grants(user_id, keys)
    logger.info(
        "oauth_grants_strategy_fanout user=%s agent=%s provider=%s capabilities_covered=%d",
        user_id,
        agent_id,
        provider_name,
        len([k for k in keys if "::" in k and "oauthcfg" not in k]),
    )
