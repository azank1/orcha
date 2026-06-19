"""Health check endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from common.database.src.generated_client import Prisma

from ...config import settings
from ...models.api_responses import HealthCheckResponse
from ..dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckResponse)
async def health_check(db: Annotated[Prisma, Depends(get_db)]):
    """
    Registry service health check.

    This endpoint is public (no authentication required).

    Returns:
        200 OK: Service is healthy
        503 Service Unavailable: Service is unhealthy
    """
    try:
        # Test database connection
        await db.query_raw("SELECT 1")
        db_status = "connected"
        is_healthy = True
    except Exception:
        db_status = "disconnected"
        is_healthy = False

    return HealthCheckResponse(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.now(UTC),
        database=db_status,
        version=settings.service_version,
    )
