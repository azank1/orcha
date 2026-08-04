"""Tier 3 — LLM-based semantic validation of workflow DAGs.

Uses an LLM to assess whether the generated workflow plan is semantically
coherent: correct agent assignments, logical data flow, and alignment with
the original user intent.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ...schemas.internal import ValidationResult

if TYPE_CHECKING:
    from common.llm.src import LLMProvider

logger = logging.getLogger(__name__)

_VALIDATION_SYSTEM_PROMPT = """\
You are a workflow validation expert for a multi-agent orchestration system.

Your job is to assess whether a generated workflow DAG is semantically sound.

Evaluate the following:
1. **Agent alignment**: Are the assigned agents appropriate for each task?
2. **Data flow coherence**: Does the output of each step logically feed into the next?
3. **Goal completion**: Does the overall workflow address the user's original intent?
4. **Efficiency**: Are there obvious redundancies or missing steps?

Respond ONLY with a valid JSON object matching this schema:
{
  "is_valid": boolean,
  "confidence": "high" | "medium" | "low",
  "issues": [<list of specific issue strings, empty if none>],
  "suggestions": [<list of optional improvement suggestions, empty if none>],
  "reasoning": "<brief overall assessment>"
}
"""


class LLMValidator:
    """
    Tier 3: semantic validation using an LLM.

    Only called after Tier 1 (deterministic) passes — by that point the
    DAG is structurally sound, so the LLM focuses purely on semantics.
    """

    def __init__(self, llm_provider: LLMProvider, model: str) -> None:
        self._llm = llm_provider
        self._model = model

    async def validate(
        self,
        workflow_dag: dict[str, Any],
        original_query: str = "",
        tier1_result: ValidationResult | None = None,
    ) -> ValidationResult:
        """
        Run LLM semantic validation and return a merged ``ValidationResult``.

        If the LLM call fails, returns a *medium-confidence* pass so that a
        transient LLM error does not block every workflow.
        """
        prompt = self._build_prompt(workflow_dag, original_query, tier1_result)
        try:
            raw = await self._llm.complete(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(raw)
        except Exception:
            logger.exception(
                "LLM validation call failed — treating as conditionally valid"
            )
            return ValidationResult(
                is_valid=True,
                issues=["LLM validation unavailable — structural validation only"],
                confidence=0.5,
                tier="llm",
            )

        issues: list[str] = result.get("issues") or []
        suggestions: list[str] = result.get("suggestions") or []
        reasoning: str = result.get("reasoning", "")
        confidence_label: str = result.get("confidence", "medium")
        confidence_score = {"high": 0.9, "medium": 0.65, "low": 0.35}.get(
            confidence_label, 0.65
        )

        logger.debug(
            "LLM validation: valid=%s confidence=%s issues=%d",
            result.get("is_valid"),
            confidence_label,
            len(issues),
        )

        return ValidationResult(
            is_valid=bool(result.get("is_valid", True)),
            issues=issues,
            suggestions=suggestions,
            reasoning=reasoning,
            confidence=confidence_score,
            tier="llm",
        )

    def _build_prompt(
        self,
        workflow_dag: dict[str, Any],
        original_query: str,
        tier1_result: ValidationResult | None,
    ) -> str:
        parts = [_VALIDATION_SYSTEM_PROMPT, "\n\n"]

        if original_query:
            parts.append(f"**Original user query**: {original_query}\n\n")

        parts.append(
            f"**Workflow DAG**:\n```json\n{json.dumps(workflow_dag, indent=2)}\n```\n"
        )

        if tier1_result and tier1_result.issues:
            parts.append(
                "\n**Note from structural validation** (already passed):\n"
                + "\n".join(f"- {i}" for i in tier1_result.issues)
                + "\n"
            )

        parts.append(
            "\nPlease validate this workflow and return your assessment as JSON."
        )
        return "".join(parts)
