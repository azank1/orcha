"""Payment settlement — Step 6.5 of the ExecutionMiddleware pipeline.

Fires after checklist auto-update.  Runs as asyncio.create_task so it never
blocks the caller's response.

On success: deducts credits_usd, writes Transaction(PENDING) and AgentInvocation(SUCCESS).
On error/timeout: releases reserve, writes AgentInvocation(ERROR/TIMEOUT).

MCP agents are free — settlement is never called for protocol == "MCP".
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal

logger = logging.getLogger(__name__)


def compute_revenue_split(base_fee: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Return (developer_payout, platform_cut, validator_cut) for settlement.

    Uses DAN three-way split when COORDINATOR_SHARE_BPS or VALIDATOR_SHARE_BPS
    are set; otherwise falls back to the legacy two-way platform split.
    """
    coordinator_bps = int(os.getenv("COORDINATOR_SHARE_BPS", "0"))
    validator_bps = int(os.getenv("VALIDATOR_SHARE_BPS", "0"))

    if coordinator_bps > 0 or validator_bps > 0:
        from common_pricing.formulae import split_revenue_dan

        developer_payout, validator_cut, coordinator_cut = split_revenue_dan(
            base_fee,
            coordinator_share_bps=coordinator_bps,
            validator_share_bps=validator_bps,
        )
        return developer_payout, coordinator_cut, validator_cut

    from common_pricing.formulae import split_revenue

    developer_payout, platform_cut = split_revenue(base_fee)
    return developer_payout, platform_cut, Decimal("0")


async def settle_invocation(
    *,
    user_id: str,
    agent_id: str,
    session_id: str,
    call_id: str,
    base_fee: Decimal,
    latency_ms: int,
    execution_success: bool,
    platform_tokens: int = 0,
) -> None:
    """
    Step 6.5 — Release reserve, deduct credits, write Transaction(PENDING).

    Called via asyncio.create_task — exceptions are logged but never re-raised.
    """
    # ── Release Redis reserve (always — success or failure) ───────────────────
    try:
        import redis.asyncio as aioredis

        from ..config import settings

        redis_client = aioredis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )
        async with redis_client as r:
            await r.delete(f"reserve:{session_id}:{call_id}")
    except Exception:
        logger.warning(
            "settle_invocation: Redis unavailable — reserve not released call_id=%s",
            call_id,
        )

    # ── Invocation record (ERROR path — no billing) ───────────────────────────
    if not execution_success:
        await _write_invocation_record(
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            call_id=call_id,
            status="ERROR",
            latency_ms=latency_ms,
            base_fee=None,
            platform_tokens=platform_tokens,
        )
        return

    # ── Revenue split ─────────────────────────────────────────────────────────
    try:
        developer_payout, platform_cut, validator_cut = compute_revenue_split(base_fee)
        validator_did = os.getenv("VALIDATOR_DID", "").strip()
        if validator_did and validator_cut > 0:
            logger.info(
                "settle_invocation: mock validator payout validator_did=%s "
                "amount=%s call_id=%s",
                validator_did,
                validator_cut,
                call_id,
            )
    except Exception:
        logger.exception("settle_invocation: revenue split failed call_id=%s", call_id)
        return

    # ── DB operations ─────────────────────────────────────────────────────────
    try:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        try:
            # Deduct credits atomically — floor at 0, detect shortfall
            await db.execute_raw(
                "UPDATE users SET credits_usd = GREATEST(credits_usd - $1::numeric, 0) WHERE id = $2",
                float(base_fee),
                user_id,
            )

            # Check for shortfall → set arrears
            user = await db.user.find_unique(where={"id": user_id})
            if user is not None and float(user.credits_usd) == 0 and base_fee > 0:
                shortfall = base_fee - Decimal(str(user.credits_usd))
                if shortfall > 0:
                    await db.user.update(
                        where={"id": user_id},
                        data={
                            "arrears_usd": float(shortfall),
                            "arrears_flag": True,
                            "credits_usd": 0.0,
                        },
                    )

            # Write Transaction(PENDING) — Gateway settlement cron settles on-chain
            await db.transaction.create(
                data={
                    "session_id": session_id,
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "call_id": call_id,
                    "base_fee": float(base_fee),
                    "platform_cut": float(platform_cut),
                    "developer_payout": float(developer_payout),
                    "latency_ms": latency_ms,
                    "status": "PENDING",
                }
            )

            # Write AgentInvocation(SUCCESS) for metrics_refresh
            await db.agentinvocation.create(
                data={
                    "session_id": session_id,
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "call_id": call_id,
                    "status": "SUCCESS",
                    "latency_ms": latency_ms,
                    "base_fee": float(base_fee),
                    "platform_tokens": platform_tokens,
                }
            )

            # Increment agent execution_count + rolling success_rate
            await _update_agent_metrics(agent_id, success=True, db=db)

        finally:
            await db.disconnect()

    except Exception:
        logger.exception(
            "settle_invocation: DB write failed call_id=%s agent=%s user=%s",
            call_id,
            agent_id,
            user_id,
        )


async def _write_invocation_record(
    *,
    user_id: str,
    agent_id: str,
    session_id: str,
    call_id: str,
    status: str,
    latency_ms: int,
    base_fee: Decimal | None,
    platform_tokens: int,
) -> None:
    try:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        try:
            await db.agentinvocation.create(
                data={
                    "session_id": session_id,
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "call_id": call_id,
                    "status": status,
                    "latency_ms": latency_ms,
                    "base_fee": float(base_fee) if base_fee is not None else None,
                    "platform_tokens": platform_tokens,
                }
            )
            await _update_agent_metrics(agent_id, success=(status == "SUCCESS"), db=db)
        finally:
            await db.disconnect()
    except Exception:
        logger.exception(
            "settle_invocation: invocation record write failed call_id=%s", call_id
        )


async def _update_agent_metrics(agent_id: str, success: bool, db: object) -> None:
    """Increment execution_count and update rolling success_rate on Agent row."""
    try:
        agent = await db.agent.find_unique(where={"id": agent_id})  # type: ignore[attr-defined]
        if agent is None:
            return
        total = agent.execution_count + 1
        current_rate = getattr(agent, "success_rate", 0.70)
        # Exponential moving average: weight recent calls more
        new_rate = (current_rate * (total - 1) + (1.0 if success else 0.0)) / total
        await db.agent.update(  # type: ignore[attr-defined]
            where={"id": agent_id},
            data={"execution_count": total, "success_rate": new_rate},
        )
    except Exception:
        logger.debug("_update_agent_metrics: failed for agent=%s", agent_id)
