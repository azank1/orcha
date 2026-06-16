# Phase 2 — Knowledge

**Gate:** Autonomous tasks completing end-to-end with <5% failure rate

Once autonomous agents are reliably completing tasks, Phase 2 starts: agents that share what they've learned across the mesh. The network gets smarter over time without any central training run.

---

## The shift

Phases 0 and 1 give agents the ability to find each other and act. Phase 2 gives the *network* memory.

An agent that successfully researches "Q3 earnings for AAPL" today should benefit the next agent that gets a related query tomorrow — without that second agent re-doing the work from scratch.

This is not a shared model. It's a shared **knowledge index** — structured, attributable, and locally controlled.

---

## Local-first vector store

Each agent (or each `emerge-node`) maintains a local vector store of knowledge it has acquired through task completions.

This extends the existing pgvector setup in Planning & Discovery — the same embedding model (`nomic-embed-text` via Ollama), the same schema patterns, running locally per agent rather than centrally.

```
Agent completes task
        │
        ▼
  Extract knowledge fragments
  (structured output from task result)
        │
        ▼
  Embed + store locally
  (local pgvector or sqlite-vec)
        │
        ▼
  (optionally) Propagate to mesh
```

---

## Knowledge propagation

Agents **opt-in** to sharing specific knowledge fragments via GossipSub. They never share raw task content — only structured, typed knowledge fragments:

```json
{
  "schema": "orcha/knowledge/v1",
  "source_did": "did:orcha:agent:research-agent",
  "fragment_type": "factual",
  "subject": "AAPL Q3 2026 earnings",
  "summary": "Revenue $94.3B, EPS $1.45, beat estimates by 3%",
  "confidence": 0.92,
  "created_at": "2026-06-16T00:00:00Z",
  "expires_at": "2026-09-16T00:00:00Z",
  "embedding": "<vector omitted for gossip — fetched on demand>",
  "signature": "<source_did signature>"
}
```

Key properties:
- `fragment_type`: `factual`, `procedural`, `relational` — receivers filter by type
- `confidence`: agent-reported confidence (0–1), not runtime-enforced
- `expires_at`: knowledge has a TTL — agents don't store stale fragments forever
- `signature`: signed by the producing agent's DID — attributable, auditable
- Embedding is **not** broadcast — only the metadata. Receivers fetch the full vector on demand from the source agent.

---

## Privacy model

Agents declare their sharing policy in `emerge.yaml`:

```yaml
knowledge:
  sharing:
    enabled: true
    fragment_types: [factual]      # only share factual knowledge
    exclude_subjects: [/internal/] # subject patterns to never share
    ttl_days: 90
```

The default is `enabled: false`. Agents that don't opt in never propagate knowledge fragments. The runtime cannot override this — it's enforced at the `emerge-node` layer.

---

## Query-time knowledge retrieval

When an agent receives a task, it can query the mesh for relevant prior knowledge before starting:

```python
@emerge.agent(name="Research Agent", ...)
async def handle(task: str, context: emerge.Context) -> str:
    # Query local store first
    local_hits = await context.knowledge.search(task, limit=5)
    
    # If confidence is low, query the mesh
    if not local_hits or max(h.confidence for h in local_hits) < 0.7:
        mesh_hits = await context.knowledge.search_mesh(task, limit=10, timeout_ms=500)
    
    # Proceed with research, seeded by prior knowledge
    ...
```

`context.knowledge.search_mesh()` queries peers via `emerge-node` — it's a best-effort, timeout-bounded call. Tasks never block on mesh availability.

---

## Relation to Planning & Discovery

The existing Planning & Discovery service uses pgvector for agent capability embeddings — finding the *right agent* for a task. Phase 2 knowledge is different: it's finding the *right prior result* to seed a task.

They use the same embedding infrastructure but serve different purposes:
- **Planning & Discovery:** "Which agent should handle this?"
- **Phase 2 knowledge:** "What do we already know about this topic?"

In practice, the Planning & Discovery service may eventually consume Phase 2 knowledge to improve routing decisions — but that's a Phase 3 concern.

---

## Open questions → RFC issues

- [ ] Storage backend: local pgvector (requires Postgres per agent) vs sqlite-vec (zero-dependency)? The latter is much easier for lightweight agents.
- [ ] Conflict resolution: two agents share conflicting factual fragments. How does a receiver choose?
- [ ] Fragment versioning: how do agents update or retract knowledge they previously shared?
- [ ] Incentives: should agents that share high-quality knowledge receive preferential routing in Phase 3?
- [ ] Sensitive knowledge: what prevents an agent from accidentally sharing PII embedded in a task result?
