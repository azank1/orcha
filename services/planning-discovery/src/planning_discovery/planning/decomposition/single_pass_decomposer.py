"""Stage 1 — Single-pass query decomposition.

Decomposes natural-language queries into complete task DAGs using a single
LLM call. Falls back to a stronger model when confidence is low.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .dag_validator import DAGValidator
from .prompts import DECOMPOSITION_SYSTEM_PROMPT
from .schemas import DecompositionResult

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

logger = logging.getLogger(__name__)

# _SIMPLE_PATTERNS = [
#     r"^(get|fetch|find|show|calculate|convert)\s+",
#     r"^what (is|are) the\s+",
#     r"^how much (is|are)\s+",
# ]
# _COMPLEX_INDICATORS = [
#     r"\b(if|when|unless|after|then)\b",
#     r"\b(every|repeatedly|until|while)\b",
#     r"\band\s+(then|after)\b",
#     r"\bor\b.*\belse\b",
# ]


class SinglePassDecomposer:
    """
    Decomposes a user query into a task DAG in one LLM call.

    Flow::

        query → pre-flight check (simple?) → single LLM call
             → DAG validation → confidence routing → result
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        primary_model: str,
        fallback_model: str,
        confidence_threshold: float = 0.75,
    ) -> None:
        self._llm = llm_provider
        self._primary_model = primary_model
        self._fallback_model = fallback_model
        self._confidence_threshold = confidence_threshold
        self._validator = DAGValidator()

    async def decompose(
        self,
        user_query: str,
        context: dict[str, Any] | None = None,
    ) -> DecompositionResult:
        """Decompose *user_query* into a task DAG."""
        context = context or {}

        # # Pre-flight: skip decomposition for simple single-action queries
        # if self._is_simple_query(user_query):
        #     return self._skip_decomposition(user_query)

        # Single-pass decomposition with small model
        decomposition = await self._single_pass_decompose(user_query, context)

        # Validate structure
        validation = self._validator.validate(decomposition)
        decomposition.confidence = validation.confidence

        # Fall back to stronger model if confidence is low
        if (
            not validation.is_valid
            or validation.confidence < self._confidence_threshold
        ):
            logger.warning(
                "Low confidence (%.2f) — falling back to %s",
                validation.confidence,
                self._fallback_model,
            )
            decomposition = await self._fallback_decompose(user_query, context)
            decomposition.method = "fallback_gpt4"

        return decomposition

    # def _is_simple_query(self, query: str) -> bool:
    #     has_simple = any(re.search(p, query, re.I) for p in _SIMPLE_PATTERNS)
    #     has_complex = any(re.search(p, query, re.I) for p in _COMPLEX_INDICATORS)
    #     return has_simple and not has_complex

    def _skip_decomposition(self, query: str) -> DecompositionResult:
        single_task = {
            "id": "task_1",
            "type": "agent_task",
            "description": query,
            "required_capabilities": self._infer_capabilities(query),
            "inputs": {},
            "depends_on": [],
            "expected_output_schema": {},
        }
        return DecompositionResult(
            success=True,
            tasks=[single_task],
            edges=[],
            metadata={"complexity": "simple", "estimated_steps": 1},
            confidence=0.95,
            method="skip",
            llm_calls=0,
        )

    async def _single_pass_decompose(
        self, query: str, context: dict[str, Any]
    ) -> DecompositionResult:
        user_prompt = self._build_user_prompt(query, context)

        response = await self._llm.complete(
            model=self._primary_model,
            messages=[
                {"role": "system", "content": DECOMPOSITION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,  # deterministic DAG extraction — reduces planner flakiness
        )

        logger.debug("LLM response: %s", response)
        dag = json.loads(response)
        return DecompositionResult(
            success=True,
            tasks=dag.get("tasks", []),
            edges=dag.get("edges", []),
            metadata=dag.get("metadata", {}),
            confidence=dag.get("metadata", {}).get("confidence", 0.8),
            method="single_pass_7b",
            llm_calls=1,
        )

    async def _fallback_decompose(
        self, query: str, context: dict[str, Any]
    ) -> DecompositionResult:
        user_prompt = self._build_user_prompt(query, context)

        response = await self._llm.complete(
            model=self._fallback_model,
            messages=[
                {"role": "system", "content": DECOMPOSITION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,  # deterministic DAG extraction — reduces planner flakiness
        )

        dag = json.loads(response)
        return DecompositionResult(
            success=True,
            tasks=dag.get("tasks", []),
            edges=dag.get("edges", []),
            metadata=dag.get("metadata", {}),
            confidence=dag.get("metadata", {}).get("confidence", 0.9),
            method="fallback_gpt4",
            llm_calls=1,
        )

    def _build_user_prompt(self, query: str, context: dict[str, Any]) -> str:
        ctx_str = f"\nContext: {json.dumps(context)}" if context else ""
        return (
            f"User query: {query}{ctx_str}\n\nDecompose this into a complete task DAG."
        )

    def _infer_capabilities(self, query: str) -> dict[str, Any]:
        return {
            "capability_type": "TOOL",
            "domains": [],
            "functions": [],
        }
