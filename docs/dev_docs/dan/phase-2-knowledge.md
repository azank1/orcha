# Phase 2 — Knowledge

**Gate:** Autonomous tasks completing end-to-end with <5% failure rate

Once autonomous agents are reliably completing tasks, Phase 2 starts: agents that share what they've learned. The network gets smarter over time without any central training run.

---

## The shift

Phases 0 and 1 give agents the ability to find each other and act. Phase 2 gives the **network** memory.

An agent that successfully researches "Q3 earnings for AAPL" today should benefit the next agent that gets a related query tomorrow — without that second agent re-doing the work from scratch.

Human civilization's most powerful property is that each generation starts where the previous one left off. Every agent today is permanently, irrecoverably, on the first day of school. Phase 2 ends that.

---

## Why IPFS is the wrong answer

IPFS is a content-addressed file system. It is excellent for serving static files. It is wrong for the DAN knowledge layer:

- **Content routing is slow.** Finding who has content requires DHT traversal — multiple hops, high latency. A knowledge system queried hundreds of times per second cannot afford this.
- **No native semantic search.** IPFS gives you content by CID. It has no concept of "find me knowledge about B2B lead generation." You would need to build an entire index layer on top.
- **No streaming updates.** Knowledge is not static. Agents are constantly learning. IPFS is not designed for high-frequency, small-update streams.
- **Garbage collection complexity.** Who pins what? Who pays for storage? Hard unsolved problems.

We need something purpose-built for the DAN use case.

---

## The right model: local-first, gossip-propagated

How does human knowledge actually propagate? Not through a central server. Through people. Each person holds knowledge in their own mind, shares it through communication, and when enough people have shared a piece of knowledge, it becomes common knowledge.

Apply this to agents:

**Each agent maintains its own local knowledge store.** Three components:

```
agent_knowledge/
├── experiences/        # Task logs, outcomes, learnings
│   └── {task_id}.json
├── fragments/          # Discrete knowledge units (indexed by embedding)
│   └── {fragment_id}.json
├── agent_profiles/     # Cached profiles of known agents
│   └── {agent_did}.json
└── embeddings.db       # sqlite-vec or LanceDB for semantic search
```

**Knowledge fragment schema:**

```json
{
  "id": "local-uuid",
  "content": "The knowledge itself",
  "summary": "One-line for broadcast",
  "domain": "sales",
  "source": "experience | received | synthesized",
  "source_did": "did:orcha:agent:research-agent",
  "timestamp": 1750000000000,
  "embedding": [0.12, -0.34, ...],
  "anchor_hash": "QmXxx",
  "visibility": "public | domain | private",
  "expires_at": 1757776000000
}
```

---

## Storage technology

For the local embedded store:

| Option | Strengths | Use for |
|--------|-----------|---------|
| **LanceDB** | Native vector + scalar, embedded, fast | Primary knowledge store — vectors + metadata |
| **sqlite-vec** | Ultra-lightweight, no deps, SQLite-native | Lightweight deployments, edge agents |
| **DuckDB** | Analytical queries over knowledge fragments | Agents doing research/synthesis heavy work |

For knowledge propagation and streaming:

| Option | Strengths | Use for |
|--------|-----------|---------|
| **Hypercore/Hyperbee** | Append-only P2P log, very fast | Agent experience streams, chronological logs |
| **libp2p Streams** | Already in the stack, encrypted | On-demand full fragment delivery |

No IPFS. No centralized object storage. Fully embedded, fully P2P.

---

## Knowledge propagation

When an agent learns something worth sharing, it:

1. Stores it locally with full fidelity
2. Broadcasts a `KNOWLEDGE_BROADCAST` on `orcha/knowledge/{domain}` with: summary, domain tags, compressed embedding hint, reference to fetch full content
3. Peers that find the embedding relevant request the full content via a direct libp2p stream
4. High-value knowledge gets anchored — when a fragment receives many fetch requests, the agent creates a content hash. This hash can be anchored on-chain (Phase 3) to prove the knowledge existed and hasn't been altered.

The full content is never broadcast — only the hint. Receivers pull on demand.

---

## Privacy model

Agents declare their sharing policy in `emerge.yaml`:

```yaml
network:
  knowledge:
    store_path: "./knowledge"
    auto_share_threshold: 0.8    # Confidence threshold to auto-broadcast
    visibility_default: "domain" # public | domain | private
    exclude_subjects: ["/internal/", "/credentials/"]
    ttl_days: 90
```

**Privacy enforcement for `domain` visibility:** Domain-private knowledge is encrypted with a domain key. Only registered domain participants have the domain key. The domain key is rotated when agents leave the domain.

The default is `visibility_default: "domain"`. Agents never expose knowledge they haven't explicitly opted to share.

---

## Why this beats a global knowledge graph

A centralized global knowledge graph has three fatal flaws:

1. **It doesn't fit in any agent's context.** An agent querying a graph with millions of fragments cannot load the entire graph. You need semantic search regardless — so make the distributed store the index and local search the query engine.
2. **It creates a write bottleneck.** Thousands of agents writing simultaneously requires either a centralized coordinator (defeats decentralization) or complex distributed transactions (extreme engineering complexity).
3. **It doesn't mimic biology.** The human brain doesn't query a central server. Each brain is a self-contained, constantly-synced node in a vast network. The richness of human knowledge comes from the diversity of what different brains hold, not a master database.

The local-first model gives you: zero-latency local queries, eventual-consistency distributed queries, privacy by default, and resilience (no single point of failure).

---

## Knowledge contribution scoring

An agent's knowledge contribution is measured and fed into Phase 3 reputation scoring:

- **Fragments broadcast:** How many knowledge fragments shared
- **Fetch count:** How many times your fragments were fetched by peers
- **Quality signal:** Whether agents that consumed your knowledge performed better (tracked via `FULFILLMENT_SIGNAL`)

High contribution score → higher reputation → more tasks offered → more knowledge acquired. This is the positive feedback loop that makes the network smarter over time.

---

## Open questions → RFC issues

- [ ] **Storage backend:** LanceDB requires more setup than sqlite-vec. What's the default for new agents? Should `emerge-node` ship with sqlite-vec and let heavy users upgrade to LanceDB?
- [ ] **Conflict resolution:** Two agents share conflicting factual fragments. How does a receiver choose? Timestamp? Source reputation? Requester-side judgment?
- [ ] **Fragment versioning:** How do agents update or retract knowledge they previously shared?
- [ ] **Sensitive knowledge:** What prevents an agent from accidentally sharing PII embedded in a task result? Does Orcha provide a scrubber, or is it purely agent-responsibility?
- [ ] **Hypercore vs libp2p Streams:** Should experience streams be Hypercore-native or just chunked libp2p stream responses? Hypercore adds a dependency but gives append-only semantics.
