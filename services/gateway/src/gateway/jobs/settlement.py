"""Settlement cron job — user-pays model.

Each settlement cycle:
  For every user with PENDING transactions:
    Phase 1 — Platform cut:  user smart wallet → platform wallet  (sum of user's platform_cuts, one tx)
    Phase 2 — Dev payouts:   user smart wallet → each dev wallet  (developer_payout per tx)

All transfers are gas-sponsored via the wallet-service (AA on EVM, fee-payer delegation on Solana).
The wallet-service returns tx_hash synchronously once the UserOperation is bundled/confirmed.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SETTLEMENT_LOCK_KEY = "settlement:lock"
SETTLEMENT_LOCK_TTL = 15  # seconds — shorter than cron interval


async def run_settlement(
    db: object,
    redis: object,
    gateway_instance_id: str,
    chain: str = "base_sepolia",
) -> None:
    logger.info(
        "Settlement cron fired (chain=%s instance=%s)", chain, gateway_instance_id
    )

    lock_acquired = await redis.set(  # type: ignore[attr-defined]
        SETTLEMENT_LOCK_KEY,
        gateway_instance_id,
        nx=True,
        ex=SETTLEMENT_LOCK_TTL,
    )
    if not lock_acquired:
        logger.info("Settlement: lock held by another instance, skipping")
        return

    logger.info("Settlement: lock acquired (chain=%s)", chain)
    try:
        await _do_settlement(db, chain)
    except Exception:
        logger.exception("Settlement: unhandled error")
    finally:
        await redis.delete(SETTLEMENT_LOCK_KEY)  # type: ignore[attr-defined]


async def _do_settlement(db: object, chain: str) -> None:
    from ..config import settings

    platform_wallet_id = getattr(settings, "platform_wallet_id", None)
    if not platform_wallet_id:
        logger.error("Settlement: PLATFORM_WALLET_ID not configured — skipping")
        return

    # Resolve the platform wallet's on-chain address (where users send USDC).
    platform_address = await _resolve_wallet_address(platform_wallet_id, "platform")
    if not platform_address:
        return

    # Fetch all pending transactions.
    try:
        pending = await db.transaction.find_many(where={"status": "PENDING"})  # type: ignore[attr-defined]
    except Exception:
        logger.warning("Settlement: Transaction table not available yet")
        return

    if not pending:
        logger.debug("Settlement: no pending transactions")
        return

    logger.info("Settlement: %d pending transactions", len(pending))

    # Group transactions by user_id.
    by_user: dict[str, list[Any]] = defaultdict(list)
    for txn in pending:
        by_user[txn.user_id].append(txn)

    caip_chain_id = _caip_chain_id(chain)
    wallet_service_url = getattr(
        settings, "wallet_service_url", "http://localhost:3000/internal"
    )
    settled_at = datetime.now(UTC)
    total_settled = 0

    for user_id, user_txns in by_user.items():
        settled = await _settle_user(
            db=db,
            user_id=user_id,
            user_txns=user_txns,
            platform_address=platform_address,
            chain=chain,
            caip_chain_id=caip_chain_id,
            wallet_service_url=wallet_service_url,
            settled_at=settled_at,
        )
        total_settled += settled

    logger.info(
        "Settlement: complete — %d/%d transactions settled",
        total_settled,
        len(pending),
    )


async def _settle_user(
    db: object,
    user_id: str,
    user_txns: list[Any],
    platform_address: str,
    chain: str,
    caip_chain_id: str,
    wallet_service_url: str,
    settled_at: datetime,
) -> int:
    """Settle all pending transactions for a single user. Returns count of settled txns."""
    try:
        user = await db.user.find_unique(where={"id": user_id})  # type: ignore[attr-defined]
    except Exception:
        logger.exception("Settlement: failed to fetch user=%s", user_id)
        return 0

    if user is None:
        logger.warning(
            "Settlement: user=%s not found, skipping %d txns", user_id, len(user_txns)
        )
        return 0

    wallet_id = getattr(user, "privy_wallet_id", None)
    eoa_address = getattr(user, "eoa_wallet_address", None)

    if not wallet_id or not eoa_address:
        logger.warning(
            "Settlement: user=%s has no smart wallet (privy_wallet_id=%s eoa_wallet_address=%s) — skipping",
            user_id,
            wallet_id,
            eoa_address,
        )
        return 0

    # Phase 1 — aggregate platform cut across all user's pending txns and send one tx.
    total_platform_cut = sum(Decimal(str(t.platform_cut)) for t in user_txns)
    platform_tx_hash: str | None = None

    if total_platform_cut > 0:
        try:
            platform_tx_hash = await _call_transfer(
                wallet_service_url=wallet_service_url,
                chain=chain,
                wallet_id=wallet_id,
                sender_address=eoa_address,
                to_address=platform_address,
                amount_usdc=total_platform_cut,
            )
            logger.info(
                "Settlement phase1: user=%s platform_cut=%s → platform tx=%s",
                user_id,
                total_platform_cut,
                platform_tx_hash,
            )
        except Exception:
            logger.exception(
                "Settlement phase1: platform_cut transfer failed for user=%s — skipping user",
                user_id,
            )
            return 0  # don't proceed if platform collection fails

    # Phase 2 — per-tx developer payout from user's smart wallet.
    # txn_id → tx_hash (None = zero payout or failed)
    dev_tx_hashes: dict[str, str | None] = {}

    for txn in user_txns:
        dev_payout = Decimal(str(txn.developer_payout))
        if dev_payout <= 0:
            dev_tx_hashes[txn.id] = None
            continue

        dev_address = await _resolve_dev_wallet(db, txn.agent_id)
        if not dev_address:
            logger.warning(
                "Settlement phase2: skipping txn=%s — could not resolve dev wallet for agent=%s",
                txn.id,
                txn.agent_id,
            )
            continue

        try:
            tx_hash = await _call_transfer(
                wallet_service_url=wallet_service_url,
                chain=chain,
                wallet_id=wallet_id,
                sender_address=eoa_address,
                to_address=dev_address,
                amount_usdc=dev_payout,
            )
            dev_tx_hashes[txn.id] = tx_hash
            logger.info(
                "Settlement phase2: txn=%s agent=%s dev_payout=%s tx=%s",
                txn.id,
                txn.agent_id,
                dev_payout,
                tx_hash,
            )
        except Exception:
            logger.exception("Settlement phase2: transfer failed txn=%s", txn.id)

    # Mark transactions as SETTLED.
    settled_count = 0
    for txn in user_txns:
        if txn.id not in dev_tx_hashes:
            continue  # dev wallet was unresolvable — do not mark settled
        try:
            await db.transaction.update(  # type: ignore[attr-defined]
                where={"id": txn.id},
                data={
                    "status": "SETTLED",
                    "settled_at": settled_at,
                    "chain_id": caip_chain_id,
                    "tx_hash": dev_tx_hashes[txn.id],
                },
            )
            settled_count += 1
        except Exception:
            logger.exception("Settlement: failed to mark txn=%s SETTLED", txn.id)

    return settled_count


async def _call_transfer(
    wallet_service_url: str,
    chain: str,
    wallet_id: str,
    sender_address: str,
    to_address: str,
    amount_usdc: Decimal,
) -> str:
    """Call wallet-service transfer endpoint. Returns tx_hash. Raises on failure."""
    # wallet-service chain key uses "base" not "base_sepolia"
    chain_key = _wallet_service_chain_key(chain)
    amount_wei = int(amount_usdc * 1_000_000)  # USDC has 6 decimals

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{wallet_service_url}/wallet/transfer",
            json={
                "chain": chain_key,
                "wallet_id": wallet_id,
                "sender_address": sender_address,
                "to_address": to_address,
                "amount_usdc_base_units": str(amount_wei),
            },
            timeout=120.0,  # AA bundler submission can take up to ~60s
        )
        resp.raise_for_status()
        data = resp.json()

    tx_hash = data.get("tx_hash")
    if not tx_hash:
        raise ValueError(f"wallet-service returned no tx_hash: {data}")
    return tx_hash


async def _resolve_wallet_address(wallet_id: str, label: str) -> str | None:
    """Resolve on-chain address for a Privy wallet ID."""
    try:
        from ..wallet.privy_client import get_wallet_address

        addr = await get_wallet_address(wallet_id)
        logger.info("Settlement: resolved %s wallet address=%s", label, addr)
        return addr
    except Exception:
        logger.exception(
            "Settlement: failed to resolve %s wallet address (id=%s)", label, wallet_id
        )
        return None


async def _resolve_dev_wallet(db: object, agent_id: str) -> str | None:
    """Return the developer's on-chain wallet_address for the given agent."""
    try:
        agent = await db.agent.find_unique(where={"id": agent_id})  # type: ignore[attr-defined]
        if agent is None:
            return None
        dev = await db.user.find_unique(where={"id": agent.user_id})  # type: ignore[attr-defined]
        if dev is None:
            return None
        is_dev = getattr(dev, "role", None) == "DEV" or getattr(
            dev, "is_dev_mode", False
        )
        if not is_dev:
            logger.warning(
                "Settlement: agent %s owner %s is not a developer (role=%s is_dev_mode=%s)",
                agent_id,
                dev.id,
                getattr(dev, "role", "?"),
                getattr(dev, "is_dev_mode", False),
            )
            return None
        addr = getattr(dev, "wallet_address", None)
        if not addr:
            logger.warning("Settlement: developer %s has no wallet_address", dev.id)
        return addr
    except Exception:
        logger.exception("Settlement: _resolve_dev_wallet failed agent=%s", agent_id)
        return None


def _caip_chain_id(chain: str) -> str:
    """Return CAIP-2 chain identifier."""
    _map = {
        "base": "eip155:8453",
        "base_sepolia": "eip155:84532",
        "ethereum": "eip155:1",
        "ethereum_sepolia": "eip155:11155111",
        "arbitrum": "eip155:42161",
        "arbitrum_sepolia": "eip155:421614",
        "polygon": "eip155:137",
        "polygon_amoy": "eip155:80002",
        "solana": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
        "solana_devnet": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
    }
    return _map.get(chain, f"eip155:{chain}")


def _wallet_service_chain_key(chain: str) -> str:
    """Map internal chain name to wallet-service strategy key."""
    _map = {
        "base_sepolia": "base",
        "base": "base",
        "solana": "solana",
        "solana_devnet": "solana",
    }
    return _map.get(chain, "base")
