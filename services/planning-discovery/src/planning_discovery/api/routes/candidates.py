"""Candidates endpoint — POST /api/v1/candidates.

Returns a ranked list of agent candidates suitable for SuperAgent's per-turn
tool-schema injection.  The PnD internal pipeline (GIN → HNSW → cross-encoder)
is reused unchanged; this endpoint only adds a new response contract.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...planning.pipeline import OptimizedPlanningPipeline  # noqa: TC001

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])

# Characters not valid in an OpenAI function name
_INVALID_FUNC_CHAR_RE = re.compile(r"[^a-zA-Z0-9_-]")


# ── Request / Response models ──────────────────────────────────────────────────


class CandidatesRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    conversation_context: list[str] = Field(default_factory=list)
    user_id: str
    top_k: int = Field(default=8, ge=1, le=20)
    protocol_filter: str | None = Field(
        default=None, description="'MCP' | 'A2A' | null"
    )
    exclude_agent_ids: list[str] = Field(default_factory=list)


class CandidateCapability(BaseModel):
    capability_id: str
    capability_type: str  # "TOOL" | "RESOURCE" | "PROMPT"
    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class ToolCandidate(BaseModel):
    agent_id: str
    agent_name: str
    agent_description: str
    protocol_type: str  # "MCP" | "A2A"
    relevance_score: float
    capabilities: list[CandidateCapability]
    health_status: str = "HEALTHY"


class CandidatesResponse(BaseModel):
    candidates: list[ToolCandidate]
    retrieval_latency_ms: int

    def to_openai_tool_schemas(self) -> list[dict[str, Any]]:
        """Convert candidates to OpenAI function-calling tool schemas.

        MCP agents: each TOOL capability becomes a separate function named
        ``{sanitised_agent_id}__{capability_id}``.

        A2A/ACP agents: the whole agent becomes a single delegate function named
        ``delegate__{sanitised_agent_id}``.
        """
        tools: list[dict[str, Any]] = []
        for c in self.candidates:
            safe_id = _sanitise(c.agent_id)
            if c.protocol_type == "MCP":
                for cap in c.capabilities:
                    if cap.capability_type != "TOOL":
                        continue
                    func_name = f"{safe_id}__{cap.capability_id}"
                    tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "description": (f"[{c.agent_name}] {cap.description}"),
                                "parameters": cap.input_schema
                                or {"type": "object", "properties": {}},
                            },
                        }
                    )
            else:
                # A2A / ACP — delegate the whole task to this agent
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": f"delegate__{safe_id}",
                            "description": (
                                f"Delegate task to {c.agent_name}: "
                                f"{c.agent_description}"
                            ),
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "task": {
                                        "type": "string",
                                        "description": "Natural-language task description",
                                    }
                                },
                                "required": ["task"],
                            },
                        },
                    }
                )
        return tools


# ── Helpers ────────────────────────────────────────────────────────────────────


def _sanitise(agent_id: str) -> str:
    """Replace characters not allowed in OpenAI function names with underscores."""
    return _INVALID_FUNC_CHAR_RE.sub("_", agent_id)


def _build_query(request: CandidatesRequest) -> str:
    """Combine the latest query with the last 3 conversation turns."""
    if not request.conversation_context:
        return request.query
    context = request.conversation_context[-3:]
    return " ".join(context + [request.query])


def _row_to_candidate(row: dict[str, Any], score: float) -> ToolCandidate:
    caps = [
        CandidateCapability(
            capability_id=c.get("capability_id", ""),
            capability_type=c.get("type", "TOOL"),
            name=c.get("name", ""),
            description=c.get("description", ""),
            input_schema=c.get("input_schema"),
            output_schema=c.get("output_schema"),
        )
        for c in row.get("capabilities", [])
    ]
    return ToolCandidate(
        agent_id=row["id"],
        agent_name=row["name"],
        agent_description=row["description"],
        protocol_type=row.get("protocol_type", "MCP"),
        relevance_score=score,
        capabilities=caps,
        health_status=row.get("health_status", "HEALTHY"),
    )


# ── Dependency ─────────────────────────────────────────────────────────────────


def get_pipeline(request: Request) -> OptimizedPlanningPipeline:
    pipeline: OptimizedPlanningPipeline | None = getattr(
        request.app.state, "pipeline", None
    )
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Planning pipeline is not initialised",
        )
    return pipeline


# ── Route ──────────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=CandidatesResponse,
    status_code=status.HTTP_200_OK,
    summary="Return ranked agent candidates for SuperAgent tool-schema injection",
)
async def get_candidates(
    body: CandidatesRequest,
    pipeline: Annotated[OptimizedPlanningPipeline, Depends(get_pipeline)],
) -> CandidatesResponse:
    """
    Run the hybrid search pipeline and return up to ``top_k`` agent candidates
    formatted for OpenAI function-calling tool schemas.

    Called by SuperAgent's orchestrator node on every turn where the PnD gate
    fires.  Only ``HEALTHY`` agents are returned (guaranteed by the search
    pipeline's ``WHERE health_status = 'HEALTHY'`` filter).
    """
    logger.info(
        "Candidates request — query='%.80s' user=%s top_k=%d",
        body.query,
        body.user_id,
        body.top_k,
    )

    filters: dict[str, Any] = {}
    if body.protocol_filter:
        filters["protocol_type"] = body.protocol_filter

    combined_query = _build_query(body)

    # Temporarily override top_k for this request
    original_top_k = pipeline._search._top_k  # noqa: SLF001
    pipeline._search._top_k = body.top_k  # noqa: SLF001
    t0 = time.monotonic()
    try:
        rows = await pipeline._search.search(combined_query, filters)  # noqa: SLF001
    except Exception as exc:
        logger.exception("Hybrid search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search pipeline error",
        ) from exc
    finally:
        pipeline._search._top_k = original_top_k  # noqa: SLF001

    latency_ms = int((time.monotonic() - t0) * 1000)

    # Filter excluded agents
    exclude = set(body.exclude_agent_ids)
    rows = [r for r in rows if r.get("id") not in exclude]

    # Build candidates with scores (cross_encoder_score if available, else index-based)
    candidates: list[ToolCandidate] = []
    for i, row in enumerate(rows):
        score = row.get("cross_encoder_score", 1.0 - i * 0.05)
        candidates.append(_row_to_candidate(row, float(score)))

    logger.info(
        "Candidates response — %d agents, latency=%dms",
        len(candidates),
        latency_ms,
    )
    return CandidatesResponse(candidates=candidates, retrieval_latency_ms=latency_ms)
