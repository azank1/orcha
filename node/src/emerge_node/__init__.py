"""emerge-node — DAN gossip sidecar (Phase D0 spike)."""

from .envelope import SignedManifestEnvelope, generate_keypair, sign_manifest, verify_envelope
from .gossip import GossipHub, publish_envelope, subscribe_once

__all__ = [
    "SignedManifestEnvelope",
    "generate_keypair",
    "sign_manifest",
    "verify_envelope",
    "GossipHub",
    "publish_envelope",
    "subscribe_once",
]
