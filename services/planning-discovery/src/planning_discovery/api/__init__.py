"""Planning & Discovery service API."""

from fastapi import APIRouter

from .routes.candidates import router as candidates_router
from .routes.health import router as health_router
from .routes.manifests import router as manifests_router
from .routes.planning import router as planning_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(planning_router)
v1_router.include_router(manifests_router)
v1_router.include_router(candidates_router)

__all__ = ["v1_router"]
