# Phase 0 — Gossip

**Gate:** ≥1 external agent registered in the wild (Day-30 adoption signal)

Once an agent that Orcha's team didn't write registers with the runtime, Phase 0 engineering begins. The gate is simple by design — one real external registration signals that the ecosystem is alive.

---

## What changes

The central Registry becomes **optional**. Agents can announce themselves to the mesh directly via gossip, and other agents can discover them without hitting a central endpoint.

The Registry doesn't go away — it's still the fastest path for discovery. But it's no longer the *only* path.

---

## emerge-node

The new artifact is `emerge-node` — a lightweight sidecar daemon that runs alongside any agent.

```
your-agent (A2A/MCP) ─► emerge-node ─► GossipSub mesh
                              │
                              └─► local peer table
                              └─► signed announcement broadcast
```

`emerge-node` responsibilities:
- Broadcast a signed agent announcement on startup
- Subscribe to peer announcements from the mesh
- Maintain a local peer table (agent DID → endpoint → last-seen)
- Expose a local HTTP API for the agent to query discovered peers

It is **not** a proxy, not a new protocol, and not required for v1 agents. It's opt-in.

---

## Transport: libp2p + GossipSub

**Why libp2p:** Battle-tested in IPFS and Ethereum. Has browser support, hole-punching, and multiple transport options. GossipSub gives efficient message propagation with flood control.

**GossipSub topic:** `orcha/agents/v1`

**Message type:** Signed agent announcement envelope (see below)

---

## Signed announcement envelope

Every announcement is a signed JSON envelope using the agent's existing DID:

```json
{
  "schema": "orcha/gossip/v1",
  "did": "did:orcha:agent:my-agent",
  "endpoint": "http://192.168.1.10:8900",
  "capabilities": ["web-search", "data-extraction"],
  "protocol": "a2a",
  "timestamp": "2026-06-16T00:00:00Z",
  "ttl": 300,
  "signature": "<base64-encoded DID signature>"
}
```

Receivers MUST:
1. Verify the signature against the DID's public key
2. Reject envelopes where `timestamp` is >5 minutes old
3. Reject envelopes where the DID doesn't match `did:orcha:agent:*` namespace

Receivers SHOULD:
- Re-broadcast valid envelopes they haven't seen (GossipSub handles this)
- Expire peers that haven't re-announced within `ttl` seconds

---

## Bootstrap nodes

Cold-start problem: how does a new `emerge-node` find its first peer?

Strategy: a small set of well-known bootstrap nodes (similar to IPFS bootstrappers). The `emerge-node` config ships with a default list. Operators can override this.

Bootstrap nodes run `emerge-node` with `--bootstrap` mode — they don't announce any agent, just maintain connectivity and relay gossip.

Open question for RFC: should bootstrap nodes be run by the Orcha team, by community volunteers, or via a DHT-based approach? → File an RFC issue.

---

## "Registry becomes optional" — what that means technically

Today:
```
emerge run → POST /api/v1/agents/register → Registry → Planning & Discovery embeddings
```

Phase 0 with emerge-node:
```
emerge run → emerge-node broadcast → GossipSub mesh → peers update local tables
           → (optional) POST /api/v1/agents/register → Registry
```

The Planning & Discovery service can be extended to also consume from the local peer table of an `emerge-node` running alongside it. This is the bridge between gossip and the existing vector search.

---

## Open questions → RFC issues

- [ ] Key management: where does the agent's signing keypair live? In `emerge.yaml`? Generated on first `emerge run`?
- [ ] Bootstrap node operations: who runs them? How are they funded?
- [ ] Peer table persistence: local SQLite? In-memory only?
- [ ] Rate limiting: max announcement frequency per DID?
- [ ] Privacy: should endpoint be in the announcement or resolved separately?
