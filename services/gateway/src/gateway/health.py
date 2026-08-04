"""Health aggregation endpoint."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    services: dict[str, str] = {}

    # SuperAgent
    try:
        resp = await request.app.state.superagent.get("/health", timeout=3.0)
        services["superagent"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        services["superagent"] = "unreachable"

    # Registry
    try:
        resp = await request.app.state.registry.get("/api/v1/health", timeout=3.0)
        services["registry"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        services["registry"] = "unreachable"

    # Redis
    try:
        await request.app.state.redis.ping()
        services["redis"] = "ok"
    except Exception:
        services["redis"] = "unreachable"

    overall = "ok" if all(v == "ok" for v in services.values()) else "degraded"
    return {"status": overall, "services": services}


# ── Public sandbox status (landing page proof chip) ───────────────────────────

_STATUS_CACHE: dict[str, Any] = {"ts": 0.0, "payload": None}
_STATUS_TTL_S = 60.0


@router.get("/api/v1/sandbox/status")
async def sandbox_status(request: Request) -> dict[str, Any]:
    """Unauthenticated, cached (60s) proof-of-life for the public sandbox.

    Landing pages poll this to show 'live · N runs today' — every number is
    read from the database, never hardcoded.
    """
    now = time.monotonic()
    if _STATUS_CACHE["payload"] and now - _STATUS_CACHE["ts"] < _STATUS_TTL_S:
        return dict(_STATUS_CACHE["payload"])

    db = request.app.state.db
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    payload: dict[str, Any] = {"status": "live", "runs_today": 0, "agents_fleet": 0}
    try:
        payload["runs_today"] = await db.conversationsession.count(
            where={"created_at": {"gte": today}}
        )
        payload["agents_fleet"] = await db.agent.count(where={"is_active": True})
    except Exception:
        logger.exception("sandbox_status: db query failed")
        payload["status"] = "degraded"

    _STATUS_CACHE["ts"] = now
    _STATUS_CACHE["payload"] = payload
    return payload


# ── Public sandbox fleet (landing page agent grid) ────────────────────────────

_FLEET_CACHE: dict[str, Any] = {"ts": 0.0, "payload": None}
_FLEET_TTL_S = 300.0


@router.get("/api/v1/sandbox/fleet")
async def sandbox_fleet(request: Request) -> dict[str, Any]:
    """Unauthenticated, cached (5 min) agent fleet list for the public sandbox.

    Returns a minimal public-safe projection of registered agents: name, DID,
    protocol, health status, and last health check. No secrets, no endpoints.
    """
    now = time.monotonic()
    if _FLEET_CACHE["payload"] and now - _FLEET_CACHE["ts"] < _FLEET_TTL_S:
        return dict(_FLEET_CACHE["payload"])

    db = request.app.state.db
    payload: dict[str, Any] = {"status": "live", "agents": []}
    try:
        agents = await db.agent.find_many(
            where={"is_active": True},
            order={"name": "asc"},
            take=24,
        )
        payload["agents"] = [
            {
                "name": a.name,
                "did": a.id,
                "protocol": a.protocol_type,
                "health": a.health_status,
                "last_check": a.last_health_check.isoformat()
                if a.last_health_check
                else None,
            }
            for a in agents
        ]
    except Exception:
        logger.exception("sandbox_fleet: db query failed")
        payload["status"] = "degraded"

    _FLEET_CACHE["ts"] = now
    _FLEET_CACHE["payload"] = payload
    return payload
