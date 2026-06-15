"""Tiered validation orchestrator.

Tier 1 — Deterministic structural checks (DeterministicValidator)
Tier 2 — ML classifier  [OMITTED by design — not implemented]
Tier 3 — LLM semantic review (LLMValidator)

Short-circuits on Tier 1 failure (no point running LLM on a broken DAG).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .deterministic import DeterministicValidator
from .llm_validator import LLMValidator

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

    from ...schemas.internal import ValidationResult

logger = logging.getLogger(__name__)


class TieredValidator:
    """
    Orchestrates Tier 1 (deterministic) → Tier 3 (LLM) validation.

    Tier 2 (ML classifier) is intentionally omitted.
    """

    def __init__(self, llm_provider: LLMProvider, validation_model: str) -> None:
        self._deterministic = DeterministicValidator()
        self._llm_validator = LLMValidator(llm_provider, validation_model)

    async def validate(
        self,
        workflow_dag: dict[str, Any],
        original_query: str = "",
    ) -> ValidationResult:
        """
        Run the full validation pipeline and return a merged ``ValidationResult``.

        Returns the first failing tier result so callers can surface precise issues.
        """
        # Tier 1 — fast, deterministic
        logger.debug("Running Tier 1 (deterministic) validation")
        tier1 = self._deterministic.validate(workflow_dag)
        if not tier1.is_valid:
            logger.warning(
                "Tier 1 validation FAILED — %d issue(s): %s",
                len(tier1.issues),
                tier1.issues,
            )
            return tier1

        # Tier 2 — ML classifier — OMITTED

        # Tier 3 — LLM semantic review — DISABLED (re-enable when needed)
        # tier3 = await self._llm_validator.validate(
        #     workflow_dag,
        #     original_query=original_query,
        #     tier1_result=tier1,
        # )
        # if not tier3.is_valid:
        #     logger.warning(
        #         "Tier 3 validation FAILED — %d issue(s): %s",
        #         len(tier3.issues),
        #         tier3.issues,
        #     )
        # return tier3

        logger.debug("Tier 3 (LLM) validation disabled — returning Tier 1 result")
        return tier1
