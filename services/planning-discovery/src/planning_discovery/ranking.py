"""Routing score computation for agent candidates — Stage 2a post-processing.

Called after cross-encoder reranking, before Semantic Coverage analysis.
Hard-gates agents below SUCCESS_RATE_FLOOR or UPTIME_FLOOR.
Enriches each candidate dict with a `routing_score` field so the
coverage analyzer and LLM selection can factor in historical performance.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from common_pricing.bounds import uptime_gate
from common_pricing.constants import (
    BOOTSTRAP_EXECUTION_COUNT,
    BOOTSTRAP_LATENCY_MS,
    BOOTSTRAP_SUCCESS_RATE,
    SUCCESS_RATE_FLOOR,
    UPTIME_FLOOR,
)
from common_pricing.formulae import routing_score

logger = logging.getLogger(__name__)


def score_candidates(
    candidates: list[dict[str, Any]],
    registry_median_latency_ms: float | None,
    registry_median_base_fee: Decimal | None,
) -> list[dict[str, Any]]:
    """
    Apply routing scores to a list of agent candidate dicts.

    Called after cross-encoder reranking (Step 5 of HybridSearchPipeline).
    Mutates `routing_score` key on each passing dict in-place.
    Returns the filtered + sorted list.

    Hard-gates remove agents that are statistically unreliable:
      - success_rate < SUCCESS_RATE_FLOOR (0.50) → excluded
      - uptime_score < UPTIME_FLOOR (0.80)        → excluded

    Bootstrap mode (execution_count < 50): uses conservative default metrics
    instead of real ones so new agents aren't penalised unfairly.

    Args:
        candidates:               Cross-encoder reranked candidates (each a dict
                                  with keys: agent_id, success_rate, uptime_score,
                                  p95_latency_ms, execution_count, base_fee).
        registry_median_latency_ms: Nightly-computed category median; None in bootstrap.
        registry_median_base_fee:   Nightly-computed category median; None in bootstrap.

    Returns:
        Subset of candidates that pass gates, sorted by routing_score desc.
        The original cross_encoder_score is preserved — callers can blend both.
    """
    passed: list[dict[str, Any]] = []

    for c in candidates:
        success_rate: float = float(c.get("success_rate", BOOTSTRAP_SUCCESS_RATE))
        uptime: float = float(c.get("uptime_score", 1.0))
        p95_ms: int = int(c.get("p95_latency_ms", BOOTSTRAP_LATENCY_MS))
        exec_count: int = int(c.get("execution_count", 0))
        raw_fee = c.get("base_fee") or "0"
        base_fee = Decimal(str(raw_fee))

        # ── Hard gates (pre-bootstrap agents always pass) ─────────────────────
        in_bootstrap = exec_count < BOOTSTRAP_EXECUTION_COUNT
        if not in_bootstrap:
            if success_rate < SUCCESS_RATE_FLOOR:
                logger.debug(
                    "score_candidates: gated out agent=%s success_rate=%.2f < %.2f",
                    c.get("id", c.get("agent_id")),
                    success_rate,
                    SUCCESS_RATE_FLOOR,
                )
                continue
            if not uptime_gate(uptime, UPTIME_FLOOR):
                logger.debug(
                    "score_candidates: gated out agent=%s uptime=%.2f < %.2f",
                    c.get("id", c.get("agent_id")),
                    uptime,
                    UPTIME_FLOOR,
                )
                continue

        # ── Use bootstrap defaults for new agents ─────────────────────────────
        eff_success = BOOTSTRAP_SUCCESS_RATE if in_bootstrap else success_rate
        eff_latency = BOOTSTRAP_LATENCY_MS if in_bootstrap else p95_ms

        # ── Normalise latency and base_fee against registry medians ───────────
        norm_latency = (
            (eff_latency / registry_median_latency_ms)
            if registry_median_latency_ms and registry_median_latency_ms > 0
            else 1.0
        )
        norm_base_fee = (
            (float(base_fee) / float(registry_median_base_fee))
            if registry_median_base_fee and registry_median_base_fee > 0
            else 1.0
        )

        score = routing_score(
            success_rate=eff_success,
            uptime_score=uptime,
            p95_latency_ms=eff_latency,
            base_fee_usd=base_fee,
            norm_latency=norm_latency,
            norm_base_fee=norm_base_fee,
        )

        c["routing_score"] = score
        passed.append(c)

    # Sort by routing_score descending; preserve cross_encoder_score for tiebreaking
    passed.sort(key=lambda x: x.get("routing_score", 0.0), reverse=True)
    return passed
