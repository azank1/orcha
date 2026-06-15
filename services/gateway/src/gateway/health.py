"""Health aggregation endpoint."""

from __future__ import annotations

import logging
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
