"""Nightly metrics refresh job.

Runs on METRICS_REFRESH_SCHEDULE (daily 01:00 UTC).
Computes rolling 7-day agent metrics from agent_invocations and writes
them back to the Agent table.  Also aggregates per-category medians
into RegistryStats (used by PnD routing score).
"""

from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

_7_DAYS_AGO_DELTA = timedelta(days=7)


async def run_metrics_refresh(db: object) -> None:
    """
    Nightly job — called by APScheduler.

    For each agent:
      - 7-day rolling success_rate from agent_invocations
      - 7-day p95_latency_ms from agent_invocations
      - execution_count total from agent_invocations
      - uptime_score derived from health check pass rate (stub — full impl needs health log table)

    Then aggregates median_base_fee_usd + median_latency_ms per task_category → RegistryStats.
    """
    since = datetime.now(UTC) - _7_DAYS_AGO_DELTA

    # ── Per-agent metrics ─────────────────────────────────────────────────────
    try:
        agents = await db.agent.find_many()  # type: ignore[attr-defined]
    except Exception:
        logger.warning("MetricsRefresh: Agent table not available — skipping")
        return

    for agent in agents:
        try:
            await _refresh_agent_metrics(db, agent, since)
        except Exception:
            logger.exception(
                "MetricsRefresh: error refreshing metrics for agent=%s", agent.id
            )

    # ── Registry stats (per task_category medians) ────────────────────────────
    try:
        await _refresh_registry_stats(db)
    except Exception:
        logger.exception("MetricsRefresh: error refreshing registry stats")

    logger.info("MetricsRefresh: complete for %d agents", len(agents))


async def _refresh_agent_metrics(db: object, agent: object, since: datetime) -> None:
    """Compute and write 7-day metrics for a single agent."""
    try:
        invocations = await db.agentinvocation.find_many(  # type: ignore[attr-defined]
            where={
                "agent_id": agent.id,
                "created_at": {"gte": since},
            }
        )
    except Exception:
        # AgentInvocation table not yet migrated
        return

    total = len(invocations)
    if total == 0:
        return

    successes = sum(1 for i in invocations if i.status == "SUCCESS")
    success_rate = successes / total

    latencies = sorted(i.latency_ms for i in invocations if i.latency_ms is not None)
    p95_latency_ms = latencies[int(len(latencies) * 0.95)] if latencies else 5000

    # uptime_score: placeholder — full implementation requires a health_check_log table.
    # Default to 1.0 until health ping logging is implemented.
    uptime_score = 1.0

    all_time_count = await db.agentinvocation.count(  # type: ignore[attr-defined]
        where={"agent_id": agent.id}
    )

    await db.agent.update(  # type: ignore[attr-defined]
        where={"id": agent.id},
        data={
            "success_rate": success_rate,
            "p95_latency_ms": p95_latency_ms,
            "uptime_score": uptime_score,
            "execution_count": all_time_count,
        },
    )


async def _refresh_registry_stats(db: object) -> None:
    """Aggregate median_base_fee_usd and median_latency_ms per task_category."""
    try:
        # Fetch all agents with a payment base_fee set
        agents = await db.agent.find_many(  # type: ignore[attr-defined]
            where={"payment": {"is": {"enabled": True}}},
            include={"payment": True},
        )
    except Exception:
        return

    # Group by task_category
    categories: dict[str, list] = {}
    for agent in agents:
        category = getattr(agent, "task_category", None) or "general"
        categories.setdefault(category, []).append(agent)

    computed_at = datetime.now(UTC)

    for category, cat_agents in categories.items():
        base_fees = []
        latencies = []

        for agent in cat_agents:
            payment = getattr(agent, "payment", None)
            if payment and getattr(payment, "base_fee", None):
                with contextlib.suppress(TypeError, ValueError):
                    base_fees.append(float(payment.base_fee))
            if getattr(agent, "p95_latency_ms", None):
                latencies.append(agent.p95_latency_ms)

        median_base_fee = _median(base_fees) if base_fees else None
        median_latency = _median(latencies) if latencies else None

        with contextlib.suppress(Exception):
            await db.registrystats.upsert(  # type: ignore[attr-defined]
                where={"task_category": category},
                data={
                    "create": {
                        "task_category": category,
                        "median_base_fee_usd": median_base_fee,
                        "median_latency_ms": median_latency,
                        "agent_count": len(cat_agents),
                        "computed_at": computed_at,
                    },
                    "update": {
                        "median_base_fee_usd": median_base_fee,
                        "median_latency_ms": median_latency,
                        "agent_count": len(cat_agents),
                        "computed_at": computed_at,
                    },
                },
            )


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2
    return s[mid]
