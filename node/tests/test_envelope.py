"""Signed envelope roundtrip — sign, verify, tamper-reject."""

from __future__ import annotations

import base64

import pytest
from emerge_node.envelope import (
    SignedManifestEnvelope,
    canonical_json_bytes,
    generate_keypair,
    sign_manifest,
    verify_bytes,
    verify_envelope,
)


@pytest.fixture
def sample_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "identity": {
            "id": "did:orcha:agent:envelope-test",
            "name": "Envelope Test",
            "version": "0.1.0",
        },
        "protocol": {
            "type": "a2a",
            "transport": {"type": "http", "endpoint": "http://localhost:8900"},
        },
    }


def test_signed_envelope_roundtrip(sample_manifest: dict) -> None:
    private_key, pub_b64 = generate_keypair()
    envelope = sign_manifest(
        manifest=sample_manifest,
        publisher_did="did:orcha:agent:envelope-test",
        private_key=private_key,
        public_key_b64=pub_b64,
    )
    assert verify_envelope(envelope)

    tampered = SignedManifestEnvelope(
        schema_version=envelope.schema_version,
        manifest={
            **sample_manifest,
            "identity": {**sample_manifest["identity"], "name": "Evil"},
        },
        publisher_did=envelope.publisher_did,
        public_key_b64=envelope.public_key_b64,
        signature_b64=envelope.signature_b64,
        published_at=envelope.published_at,
    )
    assert not verify_envelope(tampered)


def test_verify_bytes_and_canonical_json(sample_manifest: dict) -> None:
    private_key, pub_b64 = generate_keypair()
    payload = canonical_json_bytes(sample_manifest)
    signature = private_key.sign(payload)

    assert verify_bytes(payload, base64.b64encode(signature).decode("ascii"), pub_b64)
    assert not verify_bytes(
        payload + b"x", base64.b64encode(signature).decode("ascii"), pub_b64
    )
