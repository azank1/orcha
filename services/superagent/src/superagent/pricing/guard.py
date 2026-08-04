"""Payment guard — Step 2.5 of the ExecutionMiddleware pipeline.

Checks user credits before any network call is made to an agent.
Raises PaymentInterrupt on insufficient credits or arrears — caught
at execute_agent_calls_node level, same pattern as AuthInterruptRequired.

MCP agents are free and bypass this guard entirely.
"""

from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaymentInterrupt(Exception):
    """
    Raised when a user cannot be charged before an agent invocation.

    reason: "arrears" | "insufficient_credits" | "user_not_found"
    amount: amount owed (for arrears) or 0 (for zero credits)
    """

    def __init__(self, reason: str, amount: Decimal) -> None:
        self.reason = reason
        self.amount = amount
        super().__init__(reason)


async def payment_guard(
    *,
    user_id: str,
    base_fee: Decimal,
    session_id: str,
    call_id: str,
) -> None:
    """
    Step 2.5 — Credit check + Redis soft reserve.

    Called before any A2A/ACP agent network call.
    Raises PaymentInterrupt if execution should be blocked.

    The Redis soft reserve (TTL 300s) prevents double-spending within a
    concurrent session.  Released by settle_invocation() after the call.

    Args:
        user_id:    authenticated user ID
        base_fee:   expected charge (from agent manifest payment.base_fee)
        session_id: current session ID (for reserve key namespace)
        call_id:    LangGraph tool call ID (for reserve key uniqueness)
    """
    # ── Fetch user ────────────────────────────────────────────────────────────
    try:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"id": user_id})
        finally:
            await db.disconnect()
    except Exception:
        logger.warning(
            "payment_guard: DB unavailable — skipping guard for call_id=%s", call_id
        )
        return

    if user is None:
        raise PaymentInterrupt("user_not_found", Decimal("0"))

    # ── Arrears block ─────────────────────────────────────────────────────────
    if getattr(user, "arrears_flag", False):
        raise PaymentInterrupt("arrears", Decimal(str(getattr(user, "arrears_usd", 0))))

    # ── Credit check ──────────────────────────────────────────────────────────
    user_credits = Decimal(str(user.credits_usd))
    if user_credits <= 0:
        raise PaymentInterrupt("insufficient_credits", Decimal("0"))

    # ── Soft reserve (Redis TTL = 300s, covers max agent timeout) ─────────────
    try:
        import redis.asyncio as aioredis

        from ..config import settings

        redis_client = aioredis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )
        async with redis_client as r:
            await r.setex(
                f"reserve:{session_id}:{call_id}",
                300,
                str(base_fee),
            )
    except Exception:
        # Non-fatal — proceed without reserve if Redis is unavailable
        logger.warning(
            "payment_guard: Redis unavailable — soft reserve skipped for call_id=%s",
            call_id,
        )
