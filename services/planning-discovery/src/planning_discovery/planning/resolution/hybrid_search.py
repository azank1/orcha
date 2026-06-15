"""Stage 2a — Hybrid search pipeline.

Combines GIN inverted index filtering, full-text search, HNSW vector search,
Reciprocal Rank Fusion, and cross-encoder reranking to return the top-K
most relevant agents for a task.
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import numpy as np

from .keyword_extractor import extract_keywords

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

    from ...db.pool import AsyncpgPool

logger = logging.getLogger(__name__)

_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Process-level embedding cache: (query, model) → vector.
# Avoids repeat remote API calls when the same query arrives on consecutive
# orchestrator turns (which is the common case during multi-step agent runs).
_EMBED_CACHE_MAX = 128
_embed_cache: dict[tuple[str, str], list[float]] = {}


def _embed_cache_get(query: str, model: str) -> list[float] | None:
    return _embed_cache.get((query, model))


def _embed_cache_set(query: str, model: str, vec: list[float]) -> None:
    if len(_embed_cache) >= _EMBED_CACHE_MAX:
        _embed_cache.pop(next(iter(_embed_cache)))
    _embed_cache[(query, model)] = vec

# ms-marco-MiniLM-L-6-v2 outputs raw logits (not probabilities).
# Empirical ranges: highly relevant ~5–12, relevant ~0–5, irrelevant < 0.
_CE_HIGH_THRESHOLD   =  5.0
_CE_MEDIUM_THRESHOLD =  0.0


class HybridSearchPipeline:
    """
    Five-step hybrid search::

        1. GIN inverted index filter  (~8ms)   → 2K candidates
        2. Full-text search (parallel)  (~100ms)  → 100 scored
        3. HNSW vector search (parallel) (~100ms) → 100 scored
        4. Reciprocal Rank Fusion        (~1ms)   → 50 fused
        5. Cross-encoder reranking       (~100ms) → top_k final
    """

    def __init__(
        self,
        pool: AsyncpgPool,
        llm_provider: LLMProvider,
        embedding_model: str,
        top_k: int = 5,
    ) -> None:
        self._pool = pool
        self._llm = llm_provider
        self._embedding_model = embedding_model
        self._top_k = top_k
        self._cross_encoder: Any = None  # loaded on first search; call warm_up() at startup

    async def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute the full hybrid search pipeline for *query*.

        Args:
            query:   Natural-language task description.
            filters: Optional filters, e.g. ``{"protocol_type": "MCP"}``.

        Returns:
            List of up to ``top_k`` agent dicts, sorted by relevance.
        """
        filters = filters or {}
        logger.debug("[search] query=%r filters=%s", query, filters)

        keywords = extract_keywords(query)
        logger.debug("[Step 1] extracted keywords: %s", keywords)

        # Step 1: GIN inverted index — fast pre-filter (tag overlap)
        candidate_ids = await self._inverted_index_filter(keywords, filters)
        logger.debug(
            "[Step 1] tag-filtered candidates: %d ids=%s",
            len(candidate_ids),
            candidate_ids,
        )

        # Fallback: tag overlap is too strict (agent tags rarely match query words
        # verbatim).  If Step 1 yields nothing, widen to all HEALTHY active agents.
        if not candidate_ids:
            logger.info(
                "[Step 1] tag filter returned 0 results — widening to all HEALTHY agents"
                " (query=%r, keywords=%s)",
                query,
                keywords,
            )
            candidate_ids = await self._all_active_agents(filters)
            logger.debug(
                "[Step 1 fallback] widened candidate pool: %d ids=%s",
                len(candidate_ids),
                candidate_ids,
            )

        if not candidate_ids:
            logger.warning("[search] No agents in DB matching filters=%s", filters)
            return []

        # Steps 2 & 3: Run full-text and vector search in parallel
        fulltext_scores, vector_scores = await asyncio.gather(
            self._fulltext_search(query, candidate_ids),
            self._vector_search(query, candidate_ids),
        )
        logger.debug(
            "[Step 2] fulltext hits: %d — top scores: %s",
            len(fulltext_scores),
            fulltext_scores[:5],
        )
        logger.debug(
            "[Step 3] vector hits: %d — top scores: %s",
            len(vector_scores),
            vector_scores[:5],
        )

        # Step 4: RRF fusion → top 50
        fused = self._reciprocal_rank_fusion(fulltext_scores, vector_scores, top_k=50)
        logger.debug("[Step 4] RRF fused ranking (%d): %s", len(fused), fused)

        # Fetch full agent manifests for top 50
        agents = await self._fetch_agents(fused)
        logger.debug("[fetch_agents] fetched %d agents", len(agents))

        # Step 5: Cross-encoder reranking → top_k
        result = await self._cross_encoder_rerank(query, agents, self._top_k)
        logger.debug(
            "[Step 5] cross-encoder reranked to %d — scores: %s",
            len(result),
            [(a.get("name"), a.get("cross_encoder_score")) for a in result],
        )
        return result

    # ── Step 1: GIN inverted index filter ─────────────────────────────────────

    async def _inverted_index_filter(
        self, keywords: list[str], filters: dict[str, Any]
    ) -> list[str]:
        protocol = filters.get("protocol_type")
        # Join keywords into a plain-text string for plainto_tsquery — this uses
        # the GIN index on search_vector (name + description + tags) rather than
        # the tags array column, which doesn't contain extracted NLTK keywords.
        kw_string = " ".join(keywords) if keywords else None
        sql = """
            SELECT id FROM agents
            WHERE health_status::text = 'HEALTHY'
              AND is_active = true
              AND uptime_score >= 0.80
              AND ($1::text IS NULL OR protocol_type::text = $1::text)
              AND ($2::text IS NULL OR search_vector @@ plainto_tsquery('english', $2))
        """
        logger.debug(
            "[Step 1/_inverted_index_filter] protocol=%r kw_string=%r",
            protocol,
            kw_string,
        )
        results = await self._pool.fetch(sql, protocol, kw_string)
        return [r["id"] for r in results]

    # todo remove this; we can't fetch all agents into memory for large DBs, so we need to improve the tag filtering rather than widen to everything
    async def _all_active_agents(self, filters: dict[str, Any]) -> list[str]:
        """Return all HEALTHY active agents, optionally filtered by protocol_type."""
        protocol = filters.get("protocol_type")
        sql = """
            SELECT id FROM agents
            WHERE health_status::text = 'HEALTHY'
              AND is_active = true
              AND uptime_score >= 0.80
              AND ($1::text IS NULL OR protocol_type::text = $1::text)
        """
        logger.debug("[Step 1/_all_active_agents] protocol=%r", protocol)
        results = await self._pool.fetch(sql, protocol)
        return [r["id"] for r in results]

    # ── Step 2: Full-text search ───────────────────────────────────────────────

    async def _fulltext_search(
        self, query: str, candidate_ids: list[str]
    ) -> list[tuple[str, float]]:
        # plainto_tsquery is used instead of to_tsquery because:
        # - It handles stop words, stemming, and punctuation automatically
        # - to_tsquery with '&' requires ALL tokens to match, which fails when
        #   the query contains domain-specific nouns (e.g. "Shibuya") not in any
        #   agent's description.  plainto_tsquery uses AND internally but strips
        #   stop words and unknown lexemes gracefully.
        logger.debug(
            "[Step 2/_fulltext_search] query=%r candidates=%d",
            query,
            len(candidate_ids),
        )
        sql = """
            SELECT id,
                   ts_rank_cd(search_vector, plainto_tsquery('english', $1), 32) AS score
            FROM agents
            WHERE id = ANY($2::text[])
              AND search_vector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT 100
        """
        results = await self._pool.fetch(sql, query, candidate_ids)
        logger.debug("[Step 2/_fulltext_search] hits=%d", len(results))
        return [(r["id"], float(r["score"])) for r in results]

    # ── Step 3: HNSW vector search ─────────────────────────────────────────────

    async def _vector_search(
        self, query: str, candidate_ids: list[str]
    ) -> list[tuple[str, float]]:
        query_emb = await self._embed_cached(query)
        logger.debug(
            "[Step 3/_vector_search] embedding dim=%d candidates=%d",
            len(query_emb),
            len(candidate_ids),
        )
        vec_str = "[" + ",".join(str(v) for v in query_emb) + "]"

        sql = """
            SELECT agent_id,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM agent_embeddings
            WHERE agent_id = ANY($2::text[])
            ORDER BY embedding <=> $1::vector
            LIMIT 100
        """
        results = await self._pool.fetch(sql, vec_str, candidate_ids)
        logger.debug("[Step 3/_vector_search] hits=%d", len(results))
        return [(r["agent_id"], float(r["similarity"])) for r in results]

    # ── Step 4: Reciprocal Rank Fusion ────────────────────────────────────────

    def _reciprocal_rank_fusion(
        self,
        fulltext: list[tuple[str, float]],
        vector: list[tuple[str, float]],
        k: int = 60,
        top_k: int = 50,
    ) -> list[str]:
        scores: dict[str, float] = defaultdict(float)

        for rank, (agent_id, _) in enumerate(fulltext, start=1):
            scores[agent_id] += 1.0 / (k + rank)
        for rank, (agent_id, _) in enumerate(vector, start=1):
            scores[agent_id] += 1.0 / (k + rank)

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, _ in sorted_results[:top_k]]

    # ── Step 5: Cross-encoder reranking ───────────────────────────────────────

    async def _cross_encoder_rerank(
        self,
        query: str,
        agents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not agents:
            return []

        cross_encoder = self._get_cross_encoder()
        pairs = [
            [query, f"{a.get('name', '')}: {a.get('description', '')}"] for a in agents
        ]

        # Run blocking cross-encoder inference in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None, lambda: cross_encoder.predict(pairs, batch_size=32)
        )

        for agent, score in zip(agents, scores, strict=False):
            agent["cross_encoder_score"] = float(score)
            agent["confidence"] = (
                "high" if score > _CE_HIGH_THRESHOLD
                else "medium" if score > _CE_MEDIUM_THRESHOLD
                else "low"
            )

        agents.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
        return agents[:top_k]

    async def _fetch_agents(self, agent_ids: list[str]) -> list[dict[str, Any]]:
        if not agent_ids:
            return []
        sql = """
            SELECT a.id, a.name, a.description, a.tags, a.protocol_type::text,
                   a.health_status::text, a.version, a.provider,
                   a.success_rate, a.uptime_score, a.p95_latency_ms, a.execution_count,
                   p.enabled AS payment_enabled, p.base_fee,
                   json_agg(json_build_object(
                       'name', c.name,
                       'type', c.type::text,
                       'description', c.description,
                       'capability_id', c.capability_id,
                       'input_schema', c.input_schema,
                       'output_schema', c.output_schema
                   )) AS capabilities
            FROM agents a
            LEFT JOIN capabilities c ON c.agent_id = a.id
            LEFT JOIN payment_configs p ON p.agent_id = a.id
            WHERE a.id = ANY($1::text[])
            GROUP BY a.id, p.enabled, p.base_fee
        """
        rows = await self._pool.fetch(sql, agent_ids)
        result = []
        for r in rows:
            d = dict(r)
            caps = d.get("capabilities")
            if isinstance(caps, str):
                caps = _json.loads(caps)
            # Filter out LEFT JOIN null-placeholder rows (no matching capability)
            d["capabilities"] = [c for c in (caps or []) if c.get("name") is not None]
            result.append(d)
        return result

    async def _embed_cached(self, query: str) -> list[float]:
        """Embed *query*, returning a cached vector if the same query was seen recently."""
        cached = _embed_cache_get(query, self._embedding_model)
        if cached is not None:
            logger.debug("[embed_cached] cache hit for query=%.60r", query)
            return cached
        result = await self._llm.embed(query, self._embedding_model)
        _embed_cache_set(query, self._embedding_model, result)
        return result

    def warm_up(self) -> None:
        """Pre-load the cross-encoder at startup so the first request isn't slow."""
        self._get_cross_encoder()
        logger.info("Cross-encoder warmed up: %s", _CROSS_ENCODER_MODEL)

    def _get_cross_encoder(self) -> Any:
        if self._cross_encoder is None:
            import logging as _logging
            import warnings
            from sentence_transformers import CrossEncoder

            # Suppress the harmless `position_ids` UNEXPECTED key warning that
            # fires when sentence-transformers loads this BERT checkpoint with a
            # newer transformers version that registers position_ids as a buffer.
            _ts_logger = _logging.getLogger("transformers.modeling_utils")
            _prev_level = _ts_logger.level
            _ts_logger.setLevel(_logging.ERROR)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._cross_encoder = CrossEncoder(
                    _CROSS_ENCODER_MODEL,
                    automodel_args={"ignore_mismatched_sizes": True},
                )
            _ts_logger.setLevel(_prev_level)
            logger.info("Cross-encoder loaded: %s", _CROSS_ENCODER_MODEL)
        return self._cross_encoder

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        a = np.array(vec1)
        b = np.array(vec2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
