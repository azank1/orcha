"""Signed manifest envelopes for agent-network gossip (Ed25519)."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


@dataclass(frozen=True)
class SignedManifestEnvelope:
    schema_version: str
    manifest: dict[str, Any]
    publisher_did: str
    public_key_b64: str
    signature_b64: str
    published_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest": self.manifest,
            "publisher_did": self.publisher_did,
            "public_key_b64": self.public_key_b64,
            "signature_b64": self.signature_b64,
            "published_at": self.published_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignedManifestEnvelope:
        return cls(
            schema_version=str(data["schema_version"]),
            manifest=dict(data["manifest"]),
            publisher_did=str(data["publisher_did"]),
            public_key_b64=str(data["public_key_b64"]),
            signature_b64=str(data["signature_b64"]),
            published_at=str(data["published_at"]),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> SignedManifestEnvelope:
        return cls.from_dict(json.loads(raw))


def generate_keypair() -> tuple[Ed25519PrivateKey, str]:
    """Return (private_key, public_key_b64)."""
    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    return private_key, base64.b64encode(public_bytes).decode("ascii")


def _canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()


def sign_manifest(
    *,
    manifest: dict[str, Any],
    publisher_did: str,
    private_key: Ed25519PrivateKey,
    public_key_b64: str,
) -> SignedManifestEnvelope:
    payload = _canonical_manifest_bytes(manifest)
    signature = private_key.sign(payload)
    return SignedManifestEnvelope(
        schema_version="1.0",
        manifest=manifest,
        publisher_did=publisher_did,
        public_key_b64=public_key_b64,
        signature_b64=base64.b64encode(signature).decode("ascii"),
        published_at=datetime.now(UTC).isoformat(),
    )


def verify_envelope(envelope: SignedManifestEnvelope) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(envelope.public_key_b64)
        )
        signature = base64.b64decode(envelope.signature_b64)
        public_key.verify(signature, _canonical_manifest_bytes(envelope.manifest))
        return True
    except (InvalidSignature, ValueError):
        return False
