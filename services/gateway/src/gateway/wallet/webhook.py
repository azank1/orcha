"""Privy deposit webhook handler.

Privy fires a POST to this endpoint when a USDC deposit is confirmed on-chain.
Configure the webhook URL in Privy Dashboard → Webhooks:
    https://<your-gateway>/wallet/webhook/privy

Privy uses Svix for webhook delivery. Set PRIVY_WEBHOOK_SECRET to the signing
secret from the Privy Dashboard to enable signature verification.
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request, status
from svix.webhooks import Webhook, WebhookVerificationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["wallet-webhook"])


def _verify_privy_signature(request_headers: dict, raw_body: bytes) -> dict:
    """
    Validate the Privy webhook using Svix (handles signature, timestamp replay protection).
    Returns the parsed payload dict on success.
    """
    webhook_secret = os.environ.get("PRIVY_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning(
            "PRIVY_WEBHOOK_SECRET not set — webhook signature verification skipped"
        )
        import json

        return json.loads(raw_body)

    try:
        wh = Webhook(webhook_secret)
        return wh.verify(raw_body, request_headers)
    except WebhookVerificationError as e:
        logger.error("Webhook verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Privy webhook signature mismatch or expired payload",
        ) from e


@router.post("/wallet/webhook/privy")
async def handle_privy_deposit(request: Request) -> dict:
    """
    Handle confirmed USDC deposit events from Privy.

    On receipt:
    1. Verify Svix signature.
    2. Look up user by privy_wallet_id.
    3. Credit credits_usd.
    4. If user has arrears, subtract owed amount (+ interest) first, then clear flag.
    """
    raw_body = await request.body()
    payload = _verify_privy_signature(dict(request.headers), raw_body)
    event_type = payload.get("type", "")

    # Only handle incoming transfer events
    if event_type != "wallet.funds_deposited":
        return {"ignored": True, "event_type": event_type}

    wallet_id: str = payload.get("wallet_id", "")
    # Privy sends amount as USDC base units (6 decimals), e.g. "20000000" = 20.0 USDC
    amount_str: str = str(payload.get("amount", "0"))
    amount = Decimal(amount_str) / Decimal("1000000")

    if amount <= 0:
        return {"credited": "0", "reason": "zero_amount"}

    db = request.app.state.db

    user = await db.user.find_first(where={"privy_wallet_id": wallet_id})
    if user is None:
        logger.warning(
            "Privy deposit webhook: no user found for wallet_id=%s", wallet_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not associated with any user",
        )

    arrears_flag = bool(getattr(user, "arrears_flag", False))
    arrears_usd = Decimal(str(getattr(user, "arrears_usd", 0.0)))

    credited = amount

    if arrears_flag and arrears_usd > 0:
        # Deduct owed amount first (spec §10: interest accrues but we clear principal here)
        deduction = min(arrears_usd, amount)
        credited = amount - deduction
        remaining_arrears = arrears_usd - deduction
        clear_arrears = remaining_arrears <= 0

        await db.user.update(
            where={"id": user.id},
            data={
                "credits_usd": float(Decimal(str(user.credits_usd)) + credited),
                "arrears_usd": float(remaining_arrears),
                "arrears_flag": not clear_arrears,
            },
        )
        logger.info(
            "Deposit credited: user=%s credited=%s arrears_cleared=%s",
            user.id,
            credited,
            clear_arrears,
        )
    else:
        await db.user.update(
            where={"id": user.id},
            data={
                "credits_usd": float(Decimal(str(user.credits_usd)) + credited),
            },
        )
        logger.info("Deposit credited: user=%s amount=%s", user.id, credited)

    return {
        "credited": str(credited),
        "user_id": user.id,
        "tx_hash": payload.get("transaction_hash"),
    }
