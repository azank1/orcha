"""Health check endpoint for the Planning & Discovery service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from ...config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=dict[str, Any])
async def health_check() -> dict[str, Any]:
    """
    Service liveness/readiness probe.

    Returns 200 when the service is healthy and ready to accept planning
    requests.  No auth required — designed for load-balancer / k8s probes.
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }
