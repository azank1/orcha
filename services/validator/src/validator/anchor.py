"""Thin async testnet anchor adapter (KY-A supervisory harness, WS9 / FR-9.2–9.4).

Swappable "H-layer" adapter: the validator never talks to a chain directly and
there is deliberately NO web3/eth dependency in this repo. When anchoring is
enabled, the case_hash is POSTed to an external anchor service
(``ATTESTATION_ANCHOR_URL``) which performs the actual testnet write; chain
specifics stay behind this adapter boundary.

Behaviour contract:

- ``ATTESTATION_ANCHOR_ENABLED`` != "true" → row marked ``skipped`` (FR-9.3:
  the demo always completes without a chain, no credentials needed).
- Enabled → POST {case_hash, attestation_id}; on 2xx with chain_id/tx_hash in
  the JSON body → persist them, status ``anchored``, anchored_at set.
- Any error/timeout (10s) → row left ``pending`` (retryable), return "pending".
- Never raises. Always invoked as an asyncio background task by callers
  (``signer.finalize_case``), never inline in a user-facing path.
- Does NOT touch the payment ``Transaction`` table (FR-9.2).
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from .signer import _ensure_db

logger = logging.getLogger(__name__)

ENABLED_ENV = "ATTESTATION_ANCHOR_ENABLED"
URL_ENV = "ATTESTATION_ANCHOR_URL"
_TIMEOUT_SECONDS = 10.0


async def _update_row(db: Any, attestation_id: str, data: dict[str, Any]) -> None:
    await db.attestation.update(where={"id": attestation_id}, data=data)


async def anchor_attestation(attestation_id: str, db: Any = None) -> str:
    """Anchor one attestation; returns "anchored" | "skipped" | "pending".

    Never raises — anchoring must not break the supervisory flow.
    """
    if os.environ.get(ENABLED_ENV, "").strip().lower() != "true":
        try:
            client, owns_db = await _ensure_db(db)
            try:
                await _update_row(client, attestation_id, {"status": "skipped"})
            finally:
                if owns_db:
                    await client.disconnect()
        except Exception:
            logger.exception(
                "Anchor disabled but failed to mark attestation %s skipped",
                attestation_id,
            )
        logger.info("Attestation %s anchor skipped (anchor disabled)", attestation_id)
        return "skipped"

    url = os.environ.get(URL_ENV, "").strip()
    if not url:
        logger.warning(
            "%s=true but %s is unset — attestation %s stays pending",
            ENABLED_ENV,
            URL_ENV,
            attestation_id,
        )
        return "pending"

    try:
        client, owns_db = await _ensure_db(db)
        try:
            row = await client.attestation.find_unique(where={"id": attestation_id})
            if row is None:
                logger.warning(
                    "Attestation %s not found; cannot anchor", attestation_id
                )
                return "pending"

            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as http:
                resp = await http.post(
                    url,
                    json={"case_hash": row.case_hash, "attestation_id": attestation_id},
                )
            if resp.status_code // 100 != 2:
                logger.warning(
                    "Anchor service returned %s for attestation %s; stays pending",
                    resp.status_code,
                    attestation_id,
                )
                return "pending"

            body = resp.json()
            chain_id = body.get("chain_id")
            tx_hash = body.get("tx_hash")
            await _update_row(
                client,
                attestation_id,
                {
                    "status": "anchored",
                    "chain_id": chain_id,
                    "tx_hash": tx_hash,
                    "anchored_at": datetime.now(UTC),
                },
            )
            logger.info(
                "Attestation %s anchored on %s (tx=%s)",
                attestation_id,
                chain_id,
                tx_hash,
            )
            return "anchored"
        finally:
            if owns_db:
                await client.disconnect()
    except Exception:
        logger.exception(
            "Anchor failed for attestation %s; left pending (retryable)",
            attestation_id,
        )
        return "pending"
