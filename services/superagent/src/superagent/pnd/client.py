"""PnDClient — HTTP client for /api/v1/candidates on the PnD service."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import settings
from .models import PlanResponse, PnDCandidateRequest, PnDCandidateResponse

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


class PlanUnavailableError(Exception):
    """Raised when the PnD /plan endpoint cannot produce a usable plan.

    Callers fall back to the ReAct path — this is never user-facing as-is.
    """

    def __init__(self, reason: str, status_code: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


class PnDClient:
    """Async HTTP client for the Planning & Discovery /v1/candidates endpoint."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.pnd_service_url).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self._base_url, timeout=_TIMEOUT, http2=True
        )
        logger.info("PnDClient started — base_url=%s", self._base_url)

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("PnDClient stopped")

    async def get_candidates(
        self,
        query: str,
        conversation_context: list[str],
        user_id: str,
        top_k: int = 8,
        protocol_filter: str | None = None,
        exclude_agent_ids: list[str] | None = None,
    ) -> PnDCandidateResponse:
        """Call POST /api/v1/candidates and return parsed response."""
        assert self._client is not None, "PnDClient not started — call start() first"

        payload = PnDCandidateRequest(
            query=query,
            conversation_context=conversation_context[-3:],
            user_id=user_id,
            top_k=top_k,
            protocol_filter=protocol_filter,
            exclude_agent_ids=exclude_agent_ids or [],
        )

        logger.info(
            "PnD → POST /api/v1/candidates | user=%s top_k=%d protocol_filter=%s "
            "exclude=%s query='%.80s'",
            user_id,
            top_k,
            protocol_filter,
            exclude_agent_ids or [],
            query,
        )

        resp = await self._client.post(
            "/api/v1/candidates",
            content=payload.model_dump_json(),
            headers={"Content-Type": "application/json"},
        )

        logger.info(
            "PnD ← %d %s | url=%s",
            resp.status_code,
            resp.reason_phrase,
            resp.url,
        )

        resp.raise_for_status()
        data = resp.json()
        result = PnDCandidateResponse(**data)

        logger.info(
            "PnD candidates: %d returned (of %d requested) latency=%dms",
            len(result.candidates),
            top_k,
            result.retrieval_latency_ms,
        )
        for i, c in enumerate(result.candidates):
            logger.debug(
                "  [%d] agent_id=%s name=%r protocol=%s score=%.4f capabilities=%d",
                i,
                c.agent_id,
                c.agent_name,
                c.protocol_type,
                c.relevance_score,
                len(c.capabilities),
            )

        return result

    async def get_plan(
        self, query: str, context: dict[str, Any] | None = None
    ) -> PlanResponse:
        """Call POST /api/v1/plan and return the parsed workflow plan.

        Raises PlanUnavailableError on HTTP errors, success=False, or
        unparseable payloads — callers fall back to the ReAct path.
        """
        assert self._client is not None, "PnDClient not started — call start() first"

        logger.info("PnD → POST /api/v1/plan | query='%.80s'", query)
        try:
            resp = await self._client.post(
                "/api/v1/plan",
                json={"query": query, "context": context},
            )
        except httpx.HTTPError as exc:
            raise PlanUnavailableError(f"plan request failed: {exc}") from exc

        logger.info(
            "PnD ← %d %s | url=%s", resp.status_code, resp.reason_phrase, resp.url
        )
        if resp.status_code != 200:
            raise PlanUnavailableError(
                f"plan endpoint returned {resp.status_code}",
                status_code=resp.status_code,
            )

        try:
            result = PlanResponse.model_validate(resp.json())
        except Exception as exc:
            raise PlanUnavailableError(f"plan payload unparseable: {exc}") from exc
        if not result.success:
            raise PlanUnavailableError(result.message or "planner reported failure")
        logger.info(
            "PnD plan ok plan_id=%s nodes=%d edges=%d",
            result.workflow.id,
            len(result.workflow.nodes),
            len(result.workflow.edges),
        )
        return result
