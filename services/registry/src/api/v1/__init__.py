"""API v1 endpoints."""

from fastapi import APIRouter

from . import agents, health

# Create v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(agents.router)
router.include_router(health.router)

__all__ = ["router"]
