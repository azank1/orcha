# Phase 1 — Autonomous Loop

**Gate:** 10+ active agents in the gossip mesh

Once there are enough agents finding each other via gossip that a mesh is meaningfully alive, Phase 1 starts: agents that can act without a human trigger.

---

## The shift

Phase 0 gives agents **visibility** — they can find each other. Phase 1 gives them **agency** — they act on that visibility without waiting to be asked.

The human moves from operator to supervisor. Agents run their own Observe→Think→Act loops. Humans set goals and constraints; agents execute and report back.

A human professional does not wait for the phone to ring. They read the news, notice opportunities, reach out to contacts, improve their skills, and position themselves for future work — all without being explicitly instructed to. Phase 1 gives agents this.

---

## Tiered Cognitive Loop

The naive implementation — LLM call every N seconds per agent — doesn't scale.

**The math:** 10,000 agents × LLM call every 2 minutes = ~83 calls/second. At $0.001/call (Haiku-class), this is **$7,200/day** in pure think-loop costs before any real work is done.

The solution: **tiered activation**, modeled on the human nervous system.

```
Fast path (rule-based, always running, ~0 cost):
  Check: any relevant gossip messages? Any heartbeat anomalies? Any threshold crossed?
  If no signal: sleep until next cycle
  If signal: invoke LLM slow path

Slow path (LLM, invoked only on signal):
  Observe: gather context (gossip state, own metrics, knowledge store)
  Think: LLM reasoning over state
  Act: tool calls, gossip broadcasts, task delegations
  Record: ExecutionObserver.on_invocation()
```

Reflexes are fast and cheap. Full cognition is expensive and reserved. This is how biology solved the same problem.

---

## emerge.yaml — `cognitive_loop` section

```yaml
network:
  cognitive_loop:
    enabled: true
    cycle_seconds: 120          # Fast-path check interval
    max_self_tasks_per_hour: 5  # Rate limit on autonomous task initiation
    objectives:                 # Agent's standing goals (seeded into every think cycle)
      - "Maintain top-10 rank in sales domain"
      - "Monitor for new lead generation techniques"
      - "Respond to intents within my budget range"
```

---

## `@autonomous` decorator

Phase 1 extends the existing `@emerge.agent` SDK with a new decorator:

```python
from emerge import autonomous, AgentState, NetworkContext, Action

@autonomous
async def think(state: AgentState, network: NetworkContext) -> Action:
    """
    Called when the fast path detects a signal worth reasoning about.

    state:   agent's current metrics, domain rank, knowledge summary
    network: recent gossip, domain signals, nearby agents and their intents
    """
    if state.domain_rank > 20:
        return Action.REQUEST_SELF_IMPROVEMENT(
            capability_gap="Identify 3 lead enrichment capabilities I'm missing"
        )

    if network.has_relevant_intents():
        return Action.RESPOND_TO_BEST_INTENT(
            criteria="highest_budget_within_capabilities"
        )

    return Action.OBSERVE_AND_WAIT()
```

Key properties:
- `@autonomous` is additive — `@emerge.agent` agents don't need to change
- `think()` is called only when the fast path fires a signal
- `Action` is a typed return — structured, loggable, auditable
- The agent author controls the `Think` step — Orcha doesn't impose a specific LLM or strategy

---

## Observe→Think→Act loop

```
Trigger (fast path fires)
      │
      ▼
  Observe ──► gossip state, own metrics, knowledge store queries
      │
      ▼
   Think ──► LLM reasoning (or rule-based — agent's choice)
      │
      ▼
    Act ──► invoke peer agents / emit INTENT_BROADCAST / update knowledge
      │
      ▼
  Record ──► ExecutionObserver.on_invocation() ← the hook that's already there
      │
      ▼
  (loop or sleep until next fast-path signal)
```

---

## Knowledge messages (introduced in Phase 1)

`KNOWLEDGE_BROADCAST` and `KNOWLEDGE_REQUEST` are Phase 1 message types — they're introduced alongside the cognitive loop because agents need to share what they learn as they act autonomously.

```typescript
interface KnowledgeBroadcastPayload {
  fragment_summary:  string;    // One-line description of what was learned
  domain:            string;
  embeddings_hint:   number[];  // Compressed embedding for relevance routing
  full_content_ref:  string;    // How to fetch full content (local-first pull)
  visibility:        "public" | "domain" | "private";
}
```

Receivers that find `embeddings_hint` relevant can request the full content via a direct libp2p stream — the full content is never broadcast, only the hint.

---

## AgentHealthMetrics — heartbeat formalization

Agents publish a `HEARTBEAT` on `orcha/heartbeat` every N seconds:

```typescript
interface HeartbeatPayload {
  did:              string;
  domain:           string;
  tasks_completed:  number;    // Cumulative
  tasks_failed:     number;    // Cumulative
  avg_latency_ms:   number;    // Rolling 1h
  reputation_score: number;    // Current score (0–10,000)
  stake_balance:    number;    // Native token units staked
  cognitive_loop:   boolean;   // Whether autonomous loop is active
}
```

Peers use heartbeats to build their local view of the network without DHT traversal. An agent that stops heartbeating is treated as offline after 3× its declared cycle interval.

---

## ExecutionObserver — the hook that's already there

```python
# services/superagent/src/superagent/observers/execution_observer.py
class ExecutionObserver:
    async def on_invocation(self, event: InvocationEvent) -> None:
        pass  # no-op in v1
```

In Phase 1, `FulfillmentRecorder` implements this hook:

```python
class FulfillmentRecorder(ExecutionObserver):
    async def on_invocation(self, event: InvocationEvent) -> None:
        await self.recorder.record(
            agent_did=event.agent_did,
            task_type=event.task_type,
            outcome=event.outcome,
            latency_ms=event.latency_ms,
            autonomous=event.triggered_by == TriggerSource.AUTONOMOUS,
        )
```

`FulfillmentRecorder` is opt-in hosted infrastructure. Agents that register with it get aggregate analytics. The recorder never sees task content — only structured outcome metadata. This data feeds into Phase 3 reputation scoring.

---

## Open questions → RFC issues

- [ ] **Trigger types beyond time-based:** Event-driven (specific gossip message pattern)? Threshold-based (own reputation drops below X)? Webhook-triggered by external system?
- [ ] **Constraint enforcement:** Local (agent-side) or enforced by the runtime? Who verifies `max_self_tasks_per_hour`?
- [ ] **Multi-agent autonomous chains:** Agent A acts → triggers Agent B's autonomous loop. How deep can this recurse without infinite loops?
- [ ] **Human interrupt mechanism:** What's the override path for autonomous agents mid-loop? Emergency stop?
- [ ] **Fast-path signal types:** What exactly triggers the slow path? Define the signal taxonomy.
