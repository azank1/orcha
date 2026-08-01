"""PnDClient — HTTP client for /api/v1/candidates on the PnD service."""

from __future__ import annotations

import logging

import httpx

from ..config import settings
from .models import PnDCandidateRequest, PnDCandidateResponse

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


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
