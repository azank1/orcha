"""emerge-node — Ed25519 signed-envelope helpers (charter + attestation crypto)."""

from .envelope import (
    SignedManifestEnvelope,
    canonical_json_bytes,
    generate_keypair,
    sign_manifest,
    verify_bytes,
    verify_envelope,
)

__all__ = [
    "SignedManifestEnvelope",
    "canonical_json_bytes",
    "generate_keypair",
    "sign_manifest",
    "verify_bytes",
    "verify_envelope",
]
