"""Charter signing and offline verification (aac-srs.md FR-2).

Canonical JSON (the ``emerge_node.envelope`` scheme) → sha256 → Ed25519.
The signature is over the hex ``charter_hash``, matching the validator's
attestation signer, so one crypto implementation covers envelopes,
attestations, and charters.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from emerge_node.envelope import canonical_json_bytes, verify_bytes

# Fields excluded from the signed payload (attached by signing itself).
_SIGNATURE_FIELDS = ("operator_signature", "charter_hash", "regulator_attestation")


def _unsigned_payload(charter: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in charter.items() if k not in _SIGNATURE_FIELDS}


def compute_charter_hash(charter: dict[str, Any]) -> str:
    """sha256 hex digest of the canonical charter, excluding signature fields."""
    return hashlib.sha256(canonical_json_bytes(_unsigned_payload(charter))).hexdigest()


def sign_charter(charter_dict: dict[str, Any], private_key_b64: str) -> dict:
    """Sign a charter dict and return a new dict with the signature attached.

    ``private_key_b64`` is a base64 32-byte Ed25519 seed (same convention as
    the validator's ``ATTESTATION_PRIVATE_KEY_B64``). Adds ``charter_hash``
    and ``operator_signature`` (algorithm, public_key, signature).
    """
    seed = base64.b64decode(private_key_b64)
    if len(seed) != 32:
        raise ValueError(
            f"private_key_b64 must be a base64 32-byte Ed25519 seed (got {len(seed)} bytes)"
        )
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    public_key_b64 = base64.b64encode(
        private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ).decode("ascii")

    charter_hash = compute_charter_hash(charter_dict)
    signature_b64 = base64.b64encode(
        private_key.sign(charter_hash.encode("utf-8"))
    ).decode("ascii")

    signed = dict(charter_dict)
    signed["charter_hash"] = charter_hash
    signed["operator_signature"] = {
        "algorithm": "Ed25519",
        "public_key": public_key_b64,
        "signature": signature_b64,
    }
    return signed


def verify_charter(signed_charter: dict[str, Any], public_key_b64: str) -> bool:
    """Offline verification: recompute the hash and verify the signature."""
    operator_signature = signed_charter.get("operator_signature")
    if not operator_signature:
        return False
    charter_hash = compute_charter_hash(signed_charter)
    if signed_charter.get("charter_hash") not in (None, charter_hash):
        return False
    return verify_bytes(
        charter_hash.encode("utf-8"),
        operator_signature["signature"],
        public_key_b64,
    )
