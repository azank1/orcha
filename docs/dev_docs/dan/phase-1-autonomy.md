# Phase 1 — Autonomous Loop

**Gate:** 10+ active agents in the gossip mesh

Once there are enough agents discovering each other via gossip that a mesh is meaningfully alive, Phase 1 starts: agents that can act without a human trigger.

---

## The shift

Phase 0 gives agents **visibility** — they can find each other. Phase 1 gives them **agency** — they can do things with that visibility without waiting to be asked.

The human moves from operator to supervisor. Agents run their own Observe→Think→Act loops. Humans set goals and constraints, agents execute and report back.

---

## @autonomous decorator

Phase 1 extends the existing `@emerge.agent` SDK with a new decorator:

```python
import emerge

@emerge.autonomous(
    name="Market Watcher",
    description="Monitors price feeds and triggers research when anomalies appear",
    trigger=emerge.Trigger.schedule(interval="5m"),
    constraints=emerge.Constraints(max_invocations_per_hour=20),
)
async def watch(context: emerge.AutonomousContext) -> emerge.AutonomousResult:
    data = await context.observe("price-feed-agent", query="BTC/USD last 1h")
    if data.anomaly_score > 0.8:
        await context.act("research-agent", task=f"Investigate BTC anomaly: {data.summary}")
    return emerge.AutonomousResult(observations=1, actions_taken=1 if data.anomaly_score > 0.8 else 0)
```

Key properties:
- `trigger` — what kicks off the loop: `schedule`, `event`, `threshold`, or `manual`
- `constraints` — rate limits, cost caps, allowed agent set
- `context.observe()` — pulls data from another agent (read-only invocation)
- `context.act()` — triggers a task on another agent (write invocation)
- Returns a `AutonomousResult` — structured, loggable, propagatable

The decorator is additive — `@emerge.agent` agents don't need to change.

---

## Observe→Think→Act loop

```
Trigger fires
      │
      ▼
  Observe ──► gather data from mesh peers / external sources
      │
      ▼
   Think ──► LLM-based reasoning (or rule-based, agent's choice)
      │
      ▼
    Act ──► invoke peer agents / emit events / update local state
      │
      ▼
  Record ──► ExecutionObserver.on_invocation() ← this is the hook
      │
      ▼
  (loop or exit)
```

The `Think` step is intentionally agent-controlled. Orcha doesn't impose a specific LLM or reasoning strategy — the agent author decides.

---

## ExecutionObserver — the hook that's already there

```python
# services/superagent/src/superagent/observers/execution_observer.py
class ExecutionObserver:
    async def on_invocation(self, event: InvocationEvent) -> None:
        pass  # no-op in v1
```

In Phase 1, this becomes real:

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

`FulfillmentRecorder` is the Phase 1 implementation of the observer. It ships as an optional hosted add-on — operators who run it get aggregate analytics across their autonomous agents.

---

## FulfillmentRecorder

The `FulfillmentRecorder` is a lightweight service that:
- Receives `InvocationEvent`s via the `ExecutionObserver` hook
- Stores them in a time-series-friendly schema
- Exposes aggregates: success rate, latency p50/p99, top task types, agent utilization
- Feeds back into the Phase 2 knowledge layer

It is **opt-in**. Agents that don't register with a recorder run autonomous loops without telemetry. The recorder never sees task content — only structured outcome metadata.

---

## Open questions → RFC issues

- [ ] Trigger types beyond `schedule`: event-driven (Kafka topic?), threshold-based, webhook?
- [ ] Constraint enforcement: local (agent-side) or enforced by the runtime?
- [ ] `context.observe()` vs direct invocation: should read-only observations have a different wire format?
- [ ] Multi-agent autonomous chains: Agent A acts → triggers Agent B's autonomous loop. How deep can this recurse?
- [ ] Human override: what's the interrupt mechanism for autonomous agents mid-loop?
