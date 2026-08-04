"""Stage 2b — Semantic coverage analysis.

Determines whether the top-K agents can fulfil a task's capability
requirements, and chooses an orchestration strategy:
  - single_agent:       One agent covers all requirements
  - sequential_chain:   ≤3 agents chained sequentially
  - recursive_subgraph: Complex multi-agent orchestration
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np

from ...schemas.internal import AgentSearchResult, CoverageResult

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

logger = logging.getLogger(__name__)


class SemanticCoverageAnalyzer:
    """
    Analyses whether retrieved agents satisfy a task's capability requirements
    using semantic similarity (cosine) rather than exact string matching.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        embedding_model: str,
        similarity_threshold: float = 0.75,
    ) -> None:
        self._llm = llm_provider
        self._embedding_model = embedding_model
        self._threshold = similarity_threshold

    async def analyze_coverage(
        self,
        task: dict[str, Any],
        top_candidates: list[dict[str, Any]],
    ) -> CoverageResult:
        """
        Determine the best orchestration strategy for *task* given *top_candidates*.

        Returns a ``CoverageResult`` with strategy, agent assignment, and reasoning.
        """
        required_functions: list[str] = task.get("required_capabilities", {}).get(
            "functions", []
        )

        if not required_functions:
            # No specific capabilities required — use the top candidate
            if not top_candidates:
                return CoverageResult(
                    strategy="single_agent",
                    confidence="low",
                    reasoning="No candidates found",
                )
            best = self._to_search_result(top_candidates[0])
            return CoverageResult(
                strategy="single_agent",
                agent=best,
                confidence="high",
                reasoning="No specific capability requirements",
            )

        # Embed required functions
        req_embeddings: dict[str, list[float]] = {}
        for func in required_functions:
            req_embeddings[func] = await self._llm.embed(func, self._embedding_model)

        # Check each candidate
        for candidate in top_candidates:
            coverage = await self._calculate_coverage(
                required_functions, req_embeddings, candidate
            )
            if coverage["coverage_score"] >= 1.0:
                return CoverageResult(
                    strategy="single_agent",
                    agent=self._to_search_result(candidate),
                    confidence="high",
                    coverage_details=coverage,
                    reasoning=f"Agent covers all {len(required_functions)} required functions",
                )

        # Try to build a sequential chain (≤3 agents)
        chain = await self._try_build_chain(
            required_functions, req_embeddings, top_candidates
        )
        if chain and len(chain) <= 3:  # noqa: PLR2004
            return CoverageResult(
                strategy="sequential_chain",
                chain=[self._to_search_result(a) for a in chain],
                confidence="high",
                reasoning=f"Can chain {len(chain)} agents sequentially",
            )

        return CoverageResult(
            strategy="recursive_subgraph",
            available_agents=[self._to_search_result(a) for a in top_candidates],
            confidence="medium",
            reasoning="Requires complex multi-agent orchestration",
        )

    async def _calculate_coverage(
        self,
        required_functions: list[str],
        required_embeddings: dict[str, list[float]],
        agent: dict[str, Any],
    ) -> dict[str, Any]:
        capabilities: list[dict[str, Any]] = agent.get("capabilities") or []
        agent_cap_embeddings: dict[str, list[float]] = {}

        for cap in capabilities:
            text = f"{cap.get('name', '')}: {cap.get('description', '')}"
            agent_cap_embeddings[cap.get("name", "")] = await self._llm.embed(
                text, self._embedding_model
            )

        matches: dict[str, Any] = {}
        covered = 0

        for req_func in required_functions:
            req_emb = required_embeddings[req_func]
            best_match: str | None = None
            best_similarity = 0.0

            for cap_name, cap_emb in agent_cap_embeddings.items():
                similarity = self._cosine_similarity(req_emb, cap_emb)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cap_name

            matched = best_similarity >= self._threshold
            matches[req_func] = {
                "agent_capability": best_match,
                "similarity": best_similarity,
                "matched": matched,
            }
            if matched:
                covered += 1

        return {
            "coverage_score": covered / len(required_functions)
            if required_functions
            else 1.0,
            "matches": matches,
            "covered_count": covered,
            "total_required": len(required_functions),
        }

    async def _try_build_chain(
        self,
        required_functions: list[str],
        req_embeddings: dict[str, list[float]],
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        uncovered = set(required_functions)
        chain: list[dict[str, Any]] = []

        for candidate in candidates:
            if not uncovered:
                break
            coverage = await self._calculate_coverage(
                list(uncovered), {f: req_embeddings[f] for f in uncovered}, candidate
            )
            covered_by_this = {
                func for func, match in coverage["matches"].items() if match["matched"]
            }
            if covered_by_this:
                chain.append(candidate)
                uncovered -= covered_by_this

        return chain if not uncovered else None

    def _to_search_result(self, agent: dict[str, Any]) -> AgentSearchResult:
        return AgentSearchResult(
            agent_id=agent.get("id", ""),
            similarity_score=agent.get("similarity_score", 0.0),
            cross_encoder_score=agent.get("cross_encoder_score", 0.0),
            confidence=agent.get("confidence", "low"),
            manifest=agent,
        )

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        a = np.array(vec1)
        b = np.array(vec2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
