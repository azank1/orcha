"""D0 spike — two peers exchange one signed manifest envelope."""

from __future__ import annotations

import asyncio

import pytest

from emerge_node.envelope import sign_manifest, verify_envelope, generate_keypair
from emerge_node.gossip import GossipHub, publish_envelope, subscribe_once


@pytest.fixture
def sample_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "identity": {
            "id": "did:orcha:agent:gossip-test",
            "name": "Gossip Test",
            "version": "0.1.0",
        },
        "protocol": {"type": "a2a", "transport": {"type": "http", "endpoint": "http://localhost:8900"}},
    }


@pytest.mark.asyncio
async def test_signed_envelope_roundtrip(sample_manifest: dict) -> None:
    private_key, pub_b64 = generate_keypair()
    envelope = sign_manifest(
        manifest=sample_manifest,
        publisher_did="did:orcha:agent:gossip-test",
        private_key=private_key,
        public_key_b64=pub_b64,
    )
    assert verify_envelope(envelope)

    tampered = sign_manifest(
        manifest={**sample_manifest, "identity": {**sample_manifest["identity"], "name": "Evil"}},
        publisher_did="did:orcha:agent:gossip-test",
        private_key=private_key,
        public_key_b64=pub_b64,
    )
    # Re-use signature from original — must fail verify
    bad = envelope.__class__(
        schema_version=envelope.schema_version,
        manifest=tampered.manifest,
        publisher_did=envelope.publisher_did,
        public_key_b64=envelope.public_key_b64,
        signature_b64=envelope.signature_b64,
        published_at=envelope.published_at,
    )
    assert not verify_envelope(bad)


@pytest.mark.asyncio
async def test_gossip_hub_exchanges_envelope(sample_manifest: dict) -> None:
    hub = GossipHub(host="127.0.0.1", port=0)
    # bind ephemeral — start_server with port 0
    server = await asyncio.start_server(hub._handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    private_key, pub_b64 = generate_keypair()
    envelope = sign_manifest(
        manifest=sample_manifest,
        publisher_did="did:orcha:agent:gossip-test",
        private_key=private_key,
        public_key_b64=pub_b64,
    )

    async def subscriber() -> None:
        received = await subscribe_once("127.0.0.1", port, timeout=3.0)
        assert received.publisher_did == envelope.publisher_did
        assert verify_envelope(received)

    sub_task = asyncio.create_task(subscriber())
    await asyncio.sleep(0.1)
    await publish_envelope("127.0.0.1", port, envelope)
    await sub_task

    server.close()
    await server.wait_closed()
