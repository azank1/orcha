"""Manifest processing endpoint — POST /api/v1/manifests/process.

Provides a direct HTTP interface to the same pipeline that the Kafka consumer
runs.  Accepts only an ``agent_id``; all manifest data is fetched from the
database, so the caller does not need to supply the manifest JSON.
"""

from __future__ import annotations

import json as _json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...manifest_processing.embedding_generator import (
    TDWAEmbeddingGenerator,  # noqa: TC001
)
from ...manifest_processing.storage import EmbeddingStorage  # noqa: TC001
from ...manifest_processing.template_generator import SemanticTemplateGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manifests", tags=["manifests"])

_template_gen = SemanticTemplateGenerator()


# ── Request / Response models ──────────────────────────────────────────────────


class ProcessManifestRequest(BaseModel):
    """Direct manifest processing request — only agent_id is required."""

    agent_id: str = Field(
        ..., min_length=1, description="Unique agent DID / identifier"
    )


class ProcessManifestResponse(BaseModel):
    """Result of the manifest processing pipeline."""

    success: bool
    agent_id: str
    templated_string: str
    embedding_dimensions: dict[str, int]
    message: str = "Manifest processed and embeddings stored"


# ── Dependencies ───────────────────────────────────────────────────────────────


def get_embedding_gen(request: Request) -> TDWAEmbeddingGenerator:
    gen: TDWAEmbeddingGenerator | None = getattr(
        request.app.state, "embedding_gen", None
    )
    if gen is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding generator not initialised",
        )
    return gen


def get_embedding_storage(request: Request) -> EmbeddingStorage:
    storage: EmbeddingStorage | None = getattr(
        request.app.state, "embedding_storage", None
    )
    if storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding storage not initialised",
        )
    return storage


def get_pool(request: Request):  # noqa: ANN201
    pool = getattr(request.app.state, "pool", None)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database pool not initialised",
        )
    return pool


# ── DB helper ──────────────────────────────────────────────────────────────────

_FETCH_AGENT_SQL = """
    SELECT
        a.id,
        a.name,
        a.description,
        a.tags,
        a.protocol_type::text  AS protocol_type,
        a.health_status::text  AS health_status,
        a.version,
        a.provider,
        json_agg(json_build_object(
            'name',        c.name,
            'type',        c.type::text,
            'description', c.description
        )) FILTER (WHERE c.name IS NOT NULL) AS capabilities
    FROM agents a
    LEFT JOIN capabilities c ON c.agent_id = a.id
    WHERE a.id = $1
    GROUP BY a.id
"""


async def _fetch_agent_manifest(pool, agent_id: str) -> dict:
    """Fetch agent + capabilities from DB and return a normaliser-compatible dict."""
    rows = await pool.fetch(_FETCH_AGENT_SQL, agent_id)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in database",
        )
    r = dict(rows[0])

    # asyncpg may return json_agg as a raw JSON string
    caps = r.get("capabilities")
    if isinstance(caps, str):
        caps = _json.loads(caps)
    caps = caps or []

    # Build a flat manifest dict compatible with normalize_manifest()
    return {
        "name": r["name"],
        "description": r["description"],
        "tags": list(r["tags"] or []),
        "protocol_type": r["protocol_type"],
        "capabilities": caps,
    }


# ── Route ──────────────────────────────────────────────────────────────────────


@router.post(
    "/process",
    response_model=ProcessManifestResponse,
    status_code=status.HTTP_200_OK,
    summary="Process an agent's manifest from DB and store embeddings",
)
async def process_manifest(
    body: ProcessManifestRequest,
    embedding_gen: Annotated[TDWAEmbeddingGenerator, Depends(get_embedding_gen)],
    storage: Annotated[EmbeddingStorage, Depends(get_embedding_storage)],
    pool: Annotated[object, Depends(get_pool)],
) -> ProcessManifestResponse:
    """
    Run the manifest processing pipeline directly over HTTP.

    Fetches the agent's data from the ``agents`` + ``capabilities`` tables,
    then executes the same steps as the Kafka consumer:

    1. Fetch agent manifest from DB (no body manifest required)
    2. Generate a TDWA semantic template string
    3. Compute TDWA embeddings (combined + per-field) via the configured LLM
    4. Upsert the embeddings into ``agent_embeddings``

    The ``agent_id`` must already exist in the ``agents`` table.
    Register the agent via the Registry service first.
    """
    logger.info("Direct manifest processing request for agent %s", body.agent_id)

    try:
        # Step 1 — fetch manifest from DB
        manifest = await _fetch_agent_manifest(pool, body.agent_id)

        # Step 2 — semantic template
        templated_string = _template_gen.generate(manifest)

        # Step 3 — TDWA embeddings
        embeddings: dict[str, list[float]] = await embedding_gen.generate(manifest)

        # Step 4 — persist
        await storage.upsert(body.agent_id, templated_string, embeddings)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Manifest processing failed for agent %s", body.agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manifest processing failed: {exc}",
        ) from exc

    logger.info("Manifest processed successfully for agent %s", body.agent_id)

    return ProcessManifestResponse(
        success=True,
        agent_id=body.agent_id,
        templated_string=templated_string,
        embedding_dimensions={field: len(vec) for field, vec in embeddings.items()},
    )
