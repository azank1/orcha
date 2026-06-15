# Phase D0 — Gossip network surface

Thesis reference: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf) (gossip / discovery chapters).

## Goal

Machine B running a coordinator discovers and invokes an agent published on machine A **without** manually copying registry URLs or `emerge.yaml` files.

## Architecture

```mermaid
flowchart LR
  OpA[Agent operator A]
  NodeA[emerge-node A]
  Gossip[Gossip layer]
  NodeB[emerge-node B]
  CoordB[Coordinator B]
  OpA --> NodeA
  NodeA --> Gossip
  Gossip --> NodeB
  NodeB --> CoordB
```

## Components

### 1. `emerge-node` sidecar

Package: [`node/`](../../../node/) (`emerge-node` on PATH via uv workspace).

**Spike transport:** TCP pub/sub between peers (documented placeholder for libp2p GossipSub).

**Production target:** libp2p GossipSub with signed envelopes on topic `orcha/manifests/v1`.

CLI:

```bash
emerge-node --listen /ip4/0.0.0.0/tcp/9100 --bootstrap /ip4/127.0.0.1/tcp/9101
```

### 2. Signed manifest envelopes

Wire format (JSON):

```json
{
  "schema_version": "1.0",
  "manifest": { "...": "emerge.yaml parsed object" },
  "publisher_did": "did:orcha:agent:my-agent",
  "public_key_b64": "...",
  "signature_b64": "...",
  "published_at": "2026-06-16T00:00:00Z"
}
```

- Sign canonical JSON of `manifest` with publisher Ed25519 private key.
- Verify using `identity.public_key` from manifest or envelope.
- Implementation: [`node/src/emerge_node/envelope.py`](../../../node/src/emerge_node/envelope.py)

### 3. Bootstrap peers

Environment / CLI:

- `ORCHA_NETWORK_BOOTSTRAP=/ip4/bootstrap.orcha.dev/tcp/9100/p2p/...` (comma-separated)
- SDK: `emerge publish --network $ORCHA_NETWORK_BOOTSTRAP` (future)

Coordinators and nodes share bootstrap list; first peers are **trusted** (D0 honesty).

### 4. Federated registry read path

Coordinator B:

1. Ingests local registry registrations (existing).
2. Subscribes to gossip → validates signatures → upserts into **gossip index** (new PnD table or Redis cache).
3. PnD search merges local DB + gossip index for candidate retrieval.

**Not in D0:** cross-coordinator write replication; each coordinator owns its DB.

## Acceptance criteria

| # | Test |
|---|---|
| AC-D0-1 | Two `emerge-node` processes exchange one signed envelope on localhost |
| AC-D0-2 | Signature verification rejects tampered manifest |
| AC-D0-3 | Coordinator B lists agent DID after gossip ingest (integration — post D0-5/6) |
| AC-D0-4 | End-to-end: A publishes, B routes invocation to A's endpoint (integration) |

## Out of scope (D0)

- Chain, token, validator rewards
- Semantic judging / autonomous agents
- Permissionless coordinator entry

## Spike status

See [`node/tests/test_gossip_spike.py`](../../../node/tests/test_gossip_spike.py) for AC-D0-1/2.
