# Master plan index — M0–M7

**Canonical execution spec:** [SCOPE-MAP.md](SCOPE-MAP.md) — all milestones, gates, and technical requirements live there. This file is the navigation index only.

---

## Milestone map (single numbering system)

| ID | Name | Gate | Doc |
|----|------|------|-----|
| **M0** | OSS Launch Gate | CanvasKit e2e verified, merged to `main` | [SCOPE-MAP § M0](SCOPE-MAP.md#m0--oss-launch-gate) · [verification log](M0-VERIFICATION.md) |
| **M1** | Hosted Sandbox | Public URL + spend cap | [SCOPE-MAP § M1](SCOPE-MAP.md#m1--hosted-sandbox) · [deploy/sandbox/README.md](../../deploy/sandbox/README.md) |
| **M2** | Demo + Launch | Hero clip + Show HN | [SCOPE-MAP § M2](SCOPE-MAP.md#m2--demo--launch-assets) · [M2-DEMO.md](M2-DEMO.md) |
| **M3** | Traction Window | YC W2027 metrics | [SCOPE-MAP § M3](SCOPE-MAP.md#m3--traction-window-nov-2026) |
| **M4** | DAN Phase 0 — Gossip | ≥1 external agent (Day-30) | [SCOPE-MAP § M4](SCOPE-MAP.md#m4--dan-phase-0-gossip) · [dan/phase-0-gossip.md](dan/phase-0-gossip.md) |
| **M5** | DAN Phase 1 — Autonomy | ≥10 mesh agents | [SCOPE-MAP § M5](SCOPE-MAP.md#m5--dan-phase-1-autonomous-loop) · [dan/phase-1-autonomy.md](dan/phase-1-autonomy.md) |
| **M6** | DAN Phase 2 — Knowledge | &lt;5% autonomous failure | [SCOPE-MAP § M6](SCOPE-MAP.md#m6--dan-phase-2-knowledge) · [dan/phase-2-knowledge.md](dan/phase-2-knowledge.md) |
| **M7** | DAN Phase 3 — Trust | Network demands trustlessness | [SCOPE-MAP § M7](SCOPE-MAP.md#m7--dan-phase-3-trust-layer) · [dan/phase-3-trust.md](dan/phase-3-trust.md) |

**Parallel (non-blocking):** v1.2 Harness — DAG executor, retry/fallback, semantic judging ([ROADMAP.md](../../ROADMAP.md)).

---

## Legacy naming crosswalk

Older docs used overlapping IDs. **M0–M7 in SCOPE-MAP is canonical going forward.**

| Legacy | Maps to |
|--------|---------|
| sprint-plan **F0–F3** (was M0–M3) | Pre-M0 foundation work (seam, SDK, CI) — done before current M0 |
| **I0** discover + run | M0 verification gate |
| **I1** first external PR | M3 traction signal |
| **I2** hosted sandbox | **M1** |
| **P0–P8** deliverables | M4 engineering tasks — see [dan/milestones.md](dan/milestones.md) |
| **D0–D3** engineering sprints | M4–M7 implementation waves — see [CONTRIBUTOR-JOURNEY.md](dan/CONTRIBUTOR-JOURNEY.md) |
| ROADMAP **v1** | M0–M2 |
| ROADMAP **v2 DAN Alpha** | M4–M5 |
| ROADMAP **v3 DAN** | M6–M7 |
| ROADMAP **Phase 4 Open Network** | Post-M7 — [ROADMAP.md](../../ROADMAP.md) |
| **DAPN** four planes | Surface layer; CanvasKit ships in M0, rest spec-only until post-M3 |

---

## Stack layers

```
DAPN (CanvasKit, ManifestKit, …)  →  M0 surface, M4+ network
DAN (gossip, autonomy, knowledge, trust)  →  M4–M7
OSS (SuperAgent, SDK, protocols)  →  M0 substrate
```

Injection seam: `ExecutionObserver` in SuperAgent — `NoOpObserver` today, `FulfillmentRecorder` at M5 spike.

---

## Reading order

1. [SCOPE-MAP.md](SCOPE-MAP.md) — what to build and when
2. [README.md](../../README.md) + [ROADMAP.md](../../ROADMAP.md) — public narrative
3. [INCEPTION.md](../../INCEPTION.md) — DAN thesis
4. [dan/gap-analysis.md](dan/gap-analysis.md) — built vs missing per phase
5. [primitives/README.md](primitives/README.md) — DAPN specs
