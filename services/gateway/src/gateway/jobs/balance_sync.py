"""Smart-wallet USDC balance sync cron job.

Privy webhooks (`wallet.funds_deposited`) only fire for EOA wallet activity.
Because user deposits land on the Kernel AA smart wallet (`user.wallet_address`),
not the EOA, Privy never notifies us and `credits_usd` is never incremented.

This job polls each provisioned smart wallet's on-chain USDC balance directly
via JSON-RPC and credits the delta since the last poll — reproducing the same
logic that `webhook.py` would have applied had the webhook fired.

Redis key: ``wallet:last_balance:{user_id}`` — last seen on-chain balance (USDC,
6-decimal normalised to a human Decimal string, e.g. "10.500000").

The job runs only in testnet/mainnet mode (APScheduler is skipped in mock mode).
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)

# USDC contract on Base Sepolia (ERC-20, 6 decimals)
USDC_ADDRESS_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

BALANCE_KEY_PREFIX = "wallet:last_balance:"
BALANCE_SYNC_LOCK_KEY = "balance_sync:lock"
BALANCE_SYNC_LOCK_TTL = 55  # slightly less than poll interval


# ── Public entry point ─────────────────────────────────────────────────────────


async def run_wallet_balance_sync(
    db: object,
    redis: object,
    chain: str,
    rpc_url: str,
) -> None:
    """Top-level cron entry — called by APScheduler."""
    logger.debug("Balance sync fired (chain=%s)", chain)

    lock_acquired = await redis.set(  # type: ignore[attr-defined]
        BALANCE_SYNC_LOCK_KEY,
        "1",
        nx=True,
        ex=BALANCE_SYNC_LOCK_TTL,
    )
    if not lock_acquired:
        logger.debug("Balance sync: lock held by another instance, skipping")
        return

    try:
        await _do_balance_sync(db, redis, chain, rpc_url)
    except Exception:
        logger.exception("Balance sync: unhandled error")
    finally:
        await redis.delete(BALANCE_SYNC_LOCK_KEY)  # type: ignore[attr-defined]


# ── Internal ──────────────────────────────────────────────────────────────────


async def _do_balance_sync(db: object, redis: object, chain: str, rpc_url: str) -> None:
    if chain not in ("base_sepolia", "base"):
        logger.debug("Balance sync: chain=%s not EVM — skipping", chain)
        return

    try:
        users = await db.user.find_many(  # type: ignore[attr-defined]
            where={
                "wallet_address": {"not": None},
                "privy_wallet_id": {"not": None},
            }
        )
    except Exception:
        logger.warning("Balance sync: could not query users — User table not ready?")
        return

    if not users:
        logger.debug("Balance sync: no users with smart wallets")
        return

    logger.info("Balance sync: checking %d users", len(users))
    credited_count = 0

    for user in users:
        try:
            credited = await _sync_user_balance(user, db, redis, rpc_url)
            if credited:
                credited_count += 1
        except Exception:
            logger.exception(
                "Balance sync: error syncing user=%s", getattr(user, "id", "?")
            )

    if credited_count:
        logger.info("Balance sync: credited %d users", credited_count)


async def _sync_user_balance(
    user: object,
    db: object,
    redis: object,
    rpc_url: str,
) -> bool:
    """Sync one user. Returns True if credits were updated."""
    user_id: str = user.id  # type: ignore[attr-defined]
    smart_wallet: str = user.wallet_address  # type: ignore[attr-defined]
    eoa_wallet: str | None = getattr(user, "eoa_wallet_address", None)

    # Skip Solana users: on Solana the smart_wallet_address == eoa_wallet_address.
    if smart_wallet and eoa_wallet and smart_wallet.lower() == eoa_wallet.lower():
        return False

    on_chain = await _read_usdc_balance(smart_wallet, rpc_url)

    redis_key = f"{BALANCE_KEY_PREFIX}{user_id}"
    last_str: str | None = await redis.get(redis_key)  # type: ignore[attr-defined]
    last = Decimal(last_str) if last_str else Decimal("0")

    # Always persist the current balance so we don't re-credit after settlement drains the wallet.
    await redis.set(redis_key, str(on_chain))  # type: ignore[attr-defined]

    delta = on_chain - last
    if delta <= Decimal("0"):
        return False

    # New USDC arrived — apply the same arrears-then-credits logic as webhook.py.
    arrears_flag = bool(getattr(user, "arrears_flag", False))
    arrears_usd = Decimal(str(getattr(user, "arrears_usd", 0.0)))
    credited = delta

    if arrears_flag and arrears_usd > 0:
        deduction = min(arrears_usd, delta)
        credited = delta - deduction
        remaining_arrears = arrears_usd - deduction
        clear_arrears = remaining_arrears <= 0

        await db.user.update(  # type: ignore[attr-defined]
            where={"id": user_id},
            data={
                "credits_usd": float(Decimal(str(user.credits_usd)) + credited),  # type: ignore[attr-defined]
                "arrears_usd": float(remaining_arrears),
                "arrears_flag": not clear_arrears,
            },
        )
        logger.info(
            "Balance sync: user=%s on_chain=%s delta=%s credited=%s arrears_cleared=%s",
            user_id,
            on_chain,
            delta,
            credited,
            clear_arrears,
        )
    else:
        await db.user.update(  # type: ignore[attr-defined]
            where={"id": user_id},
            data={
                "credits_usd": float(Decimal(str(user.credits_usd)) + credited),  # type: ignore[attr-defined]
            },
        )
        logger.info(
            "Balance sync: user=%s on_chain=%s delta=%s credited=%s",
            user_id,
            on_chain,
            delta,
            credited,
        )

    return True


async def _read_usdc_balance(wallet_address: str, rpc_url: str) -> Decimal:
    """Return the USDC balance of ``wallet_address`` in human units (6-decimal normalised)."""
    # ERC-20 balanceOf(address) selector: keccak256("balanceOf(address)")[:4]
    selector = "70a08231"
    padded_addr = wallet_address.removeprefix("0x").lower().zfill(64)
    call_data = f"0x{selector}{padded_addr}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [
            {"to": USDC_ADDRESS_BASE_SEPOLIA, "data": call_data},
            "latest",
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(rpc_url, json=payload, timeout=10.0)
        resp.raise_for_status()
        result_hex: str = resp.json().get("result") or "0x0"

    raw = int(result_hex, 16)
    return Decimal(raw) / Decimal("1_000_000")
