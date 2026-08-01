# Orcha Roadmap

This is the public trajectory for Orcha. It describes direction, not dated commitments. Each phase is gated on the phase before it being validated by real adoption — we build the next layer only when the current one is earned.

---

## ✅ v1 — OSS Runtime (now)

The multi-protocol orchestration runtime, fully usable locally in mock payment mode.

- Core services: Registry, Planning & Discovery, SuperAgent, Gateway
- Three protocols orchestrated in one run: **MCP**, **A2A**, **ACP**
- Execution pipeline: input validation, credential vault + auth cascade (OAuth), output normalization, human-in-the-loop interrupts, per-call payments (mock mode by default)
- 7 example agents + agent/bridge templates
- `emerge` CLI (`init` / `run` / `publish`) and the `@emerge.agent` SDK decorator
- Versioned `emerge.yaml` spec with JSON Schema + RFC governance
- `ExecutionObserver` seam — a no-op hook today; the extension point for post-execution observers
- Experimental spikes: signed-envelope gossip (`node/`) and a `FulfillmentRecorder` observer (`services/validator/`) — early seams toward a network layer, not a live network

---

## 🔧 v1.2 — Harness (gated on v1 validation)

Reliability work for production-grade orchestration. Does not block launch.

- DAG executor for parallel and dependent step execution
- Output verification and semantic judging
- Retry and fallback policies
- Context manager for long-running multi-step tasks

---

Have an opinion on direction? Open a discussion issue or join the community.
