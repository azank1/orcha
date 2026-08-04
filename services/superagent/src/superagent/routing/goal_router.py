"""Hybrid goal router: ReAct loop vs DAG planner.

Channel A is a deterministic heuristic score — obvious cases route without an
LLM call. Borderline goals defer to Channel B, a small-model YES/NO arbiter.
Fusion is conservative (CDV dual-verify style): the cheap channel vetoes
wasted planning, the expensive channel vetoes over-planning, and any Channel B
error falls back to the ReAct fast path.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

_STEP_MARKERS = (
    " and then ",
    " then ",
    "first ",
    "after that",
    "step 1",
    "1.",
    "2.",
)

_CHANNEL_B_PROMPT = (
    "You are routing a user goal inside an agent orchestration runtime.\n"
    "Answer YES if the goal requires coordinated multi-step execution across "
    "multiple agents with data flowing between steps (a planned workflow).\n"
    "Answer NO if a single agent or a simple reactive loop suffices.\n"
    "Reply with exactly YES or NO.\n\nGoal: {goal}"
)


def _cand_get(candidate: Any, key: str, default: Any = None) -> Any:
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return getattr(candidate, key, default)


def score_channel_a_heuristic(goal: str, candidates: list[Any]) -> float:
    """Deterministic complexity score in [0, 1] for DAG routing."""
    score = 0.0
    n = len(candidates)
    if n >= 4:
        score += 0.35
    elif n >= 2:
        score += 0.15

    protocols = {_cand_get(c, "protocol_type", "") for c in candidates} - {""}
    if len(protocols) >= 2:
        score += 0.2

    text = f" {goal.lower()} "
    markers = sum(1 for m in _STEP_MARKERS if m in text)
    if markers >= 2:
        score += 0.3
    elif markers == 1:
        score += 0.15

    if len(goal.split()) >= 30:
        score += 0.15

    return min(score, 1.0)


async def classify_channel_b(goal: str, small_llm: Any) -> bool:
    """Semantic arbiter: small-model YES/NO on whether the goal needs a DAG.

    Uses the raw AsyncOpenAI surface, mirroring pnd_gate's tier-3 classifier.
    """
    resp = await small_llm.chat.completions.create(
        model=settings.dag_route_model or settings.small_model,
        messages=[{"role": "user", "content": _CHANNEL_B_PROMPT.format(goal=goal)}],
        max_tokens=5,
        temperature=0,
    )
    content = (resp.choices[0].message.content or "").strip().upper()
    return content.startswith("YES")


async def route_goal(
    goal: str,
    candidates: list[Any],
    small_llm: Any,
    has_checklist: bool = False,
) -> str:
    """Route a fresh goal to the DAG planner or the ReAct loop.

    Returns "dag" | "react". Flag-gated; conservative on every failure mode.
    """
    if not settings.dag_planner_enabled:
        return "react"
    if has_checklist:
        return "react"
    if not goal.strip():
        return "react"

    score = score_channel_a_heuristic(goal, candidates)
    logger.debug(
        "goal_router: channel_a=%.2f high=%.2f low=%.2f goal=%.60s",
        score,
        settings.dag_route_high,
        settings.dag_route_low,
        goal,
    )
    if score >= settings.dag_route_high:
        return "dag"
    if score <= settings.dag_route_low:
        return "react"

    try:
        verdict = await classify_channel_b(goal, small_llm)
    except Exception:
        logger.exception("goal_router: Channel B failed — falling back to ReAct")
        return "react"
    logger.info("goal_router: borderline score=%.2f channel_b=%s", score, verdict)
    return "dag" if verdict else "react"
