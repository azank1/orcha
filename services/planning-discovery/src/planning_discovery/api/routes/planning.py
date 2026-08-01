"""Planning endpoint — POST /api/v1/plan.

Accepts a natural-language user query and returns a validated workflow
manifest ready for execution by the Orcha gateway.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...planning.pipeline import OptimizedPlanningPipeline  # noqa: TC001
from ...schemas.workflow_manifest import WorkflowManifest  # noqa: TC001
from ...utils.errors import (
    AmbiguousQueryError,
    NoAgentsFoundError,
    ValidationFailedError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plan", tags=["planning"])


# ── Request / Response models ──────────────────────────────────────────────────


class PlanRequest(BaseModel):
    """Input to the planning endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Natural-language task description",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional runtime context (user preferences, available tools, etc.)",
    )


class PlanResponse(BaseModel):
    """Envelope wrapping the generated workflow manifest."""

    success: bool = True
    workflow: WorkflowManifest
    message: str = "Workflow plan generated successfully"


# ── Dependency: resolve pipeline from app state ────────────────────────────────


def get_pipeline(request: Request) -> OptimizedPlanningPipeline:
    """Retrieve the shared pipeline instance from application state."""
    pipeline: OptimizedPlanningPipeline | None = getattr(
        request.app.state, "pipeline", None
    )
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Planning pipeline is not initialised — service may be starting up",
        )
    return pipeline


# ── Route ──────────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a workflow plan for a user query",
)
async def create_plan(
    body: PlanRequest,
    pipeline: Annotated[OptimizedPlanningPipeline, Depends(get_pipeline)],
) -> PlanResponse:
    """
    Run the 3-stage planning pipeline and return a ``WorkflowManifest``.

    **Stages**:
    1. **Decomposition** — breaks the query into a task DAG using an LLM
    2. **Resolution**    — finds the best agent(s) for each task via hybrid search
    3. **Validation**    — deterministic + LLM checks on the assembled DAG

    **Error responses**:
    - `400 Bad Request` — query is ambiguous or structurally invalid
    - `422 Unprocessable Entity` — validation failed on the generated DAG
    - `503 Service Unavailable` — no agents found or downstream LLM unavailable
    """
    logger.info("Plan request received — query='%.80s'", body.query)

    try:
        workflow = await pipeline.plan(body.query, body.context)
    except AmbiguousQueryError as exc:
        logger.warning("Ambiguous query: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except NoAgentsFoundError as exc:
        logger.warning("No agents found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValidationFailedError as exc:
        logger.warning("Validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected planning error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during planning",
        ) from exc

    return PlanResponse(workflow=workflow)
