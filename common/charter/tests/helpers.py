"""Shared charter fixtures for signing/attenuation tests."""

from __future__ import annotations

import base64
from typing import Any

from charter.signing import sign_charter
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from emerge_node.envelope import generate_keypair

ISSUER = {
    "legal_name": "Example Finserv Pvt Ltd",
    "identifier_type": "CIN",
    "identifier_value": "U72900MH2020PTC000000",
}

AGENT_IDENTITY = {"agent_id": "did:orcha:agent:fixture-payments-agent"}

ROOT_SCOPE = {
    "dpi_rails": ["UPI", "AccountAggregator"],
    "permitted_actions": ["initiate_payment", "query_balance"],
    "prohibited_actions": ["cash_withdrawal"],
    "max_transaction_value": "5000.00",
    "human_approval_required_above": "1000.00",
}

ROOT_DELEGATION = {"allowed": True, "max_depth": 2}

ROOT_VALIDITY = {
    "not_before": "2026-08-01T00:00:00Z",
    "not_after": "2027-08-01T00:00:00Z",
}


def make_keypair() -> tuple[str, str]:
    """Return (private_key_b64 seed, public_key_b64)."""
    private_key, public_key_b64 = generate_keypair()
    seed = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return base64.b64encode(seed).decode("ascii"), public_key_b64


def make_charter(
    charter_id: str,
    *,
    scope: dict[str, Any] | None = None,
    delegation: dict[str, Any] | None = None,
    validity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    charter: dict[str, Any] = {
        "charter_id": charter_id,
        "version": "1.0",
        "issued_by": dict(ISSUER),
        "agent_identity": dict(AGENT_IDENTITY),
        "authorized_scope": dict(ROOT_SCOPE if scope is None else scope),
        "delegation": dict(ROOT_DELEGATION if delegation is None else delegation),
        "validity": dict(ROOT_VALIDITY if validity is None else validity),
    }
    return charter


def sign_pair(
    child_overrides: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Sign a root charter and a child linked to it; return (root, child, pubkey)."""
    private_key_b64, public_key_b64 = make_keypair()
    root = sign_charter(make_charter("charter:root"), private_key_b64)
    child_unsigned = make_charter("charter:child", **child_overrides)
    child_unsigned["parent_charter_hash"] = root["charter_hash"]
    child = sign_charter(child_unsigned, private_key_b64)
    return root, child, public_key_b64
