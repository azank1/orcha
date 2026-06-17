# Technical scope map — OSS, DAN, DAPN

Internal index: maps **existing** scope and spec documents to the three product layers. Use this when reconciling an external SRS or technical scope document against what is already planned in-repo.

**Canonical plan index:** [`MASTER-PLAN.md`](MASTER-PLAN.md)

---

## Layer definitions

| Layer | What it is | Primary outcome |
|-------|-----------|-----------------|
| **OSS v1** | Multi-protocol orchestration runtime + `emerge` SDK/CLI | A contributor runs the stack locally in an afternoon |
| **DAN** | Decentralized agent network (gossip, autonomy, knowledge, trust) | Agents discover and coordinate without a central coordinator |
| **DAPN** | Decentralized Agentic App Network — apps as agent compositions | Users get persistent applications (CanvasKit UI), not chat transcripts |

Stack order: **OSS substrate → DAN network → DAPN surface**. See [`MASTER-PLAN.md`](MASTER-PLAN.md) for milestone crosswalk.

---

## Document → layer mapping

### OSS v1 (substrate)

| Document | Path | Scope covered |
|----------|------|---------------|
| Public entry | [`README.md`](../../README.md) | v1 runtime, quickstart, DAN/DAPN pointers |
| Product trajectory | [`ROADMAP.md`](../../ROADMAP.md) | v1 → v1.2 → v2 → v3 gates |
| Launch execution | [`oss-launch/sprint-plan.md`](oss-launch/sprint-plan.md) | M0–M3 engineering and launch ops |
| Launch quality | [`launch-gate-smoke.md`](../launch-gate-smoke.md) | Fresh-machine smoke checklist |
| Spec governance | [`spec/governance.md`](../spec/governance.md), [`spec/emerge-yaml.schema.json`](../spec/emerge-yaml.schema.json) | `emerge.yaml` RFC process |
| SDK | [`sdk/README.md`](../../sdk/README.md) | `@emerge.agent`, CLI, A2A server |
| Contributor funnel | [`join.md`](../join.md), [`quickstart.md`](../quickstart.md) | Onboarding |

**OSS injection seam (DAN hook):** [`services/superagent/src/superagent/middleware/observers.py`](../../services/superagent/src/superagent/middleware/observers.py) — `ExecutionObserver` / `NoOpObserver`.

### DAN (network)

| Document | Path | Scope covered |
|----------|------|---------------|
| Civilization thesis | [`INCEPTION.md`](../../INCEPTION.md) | Five deficiencies, three layers, adoption gates |
| Phase specs | [`dan/phase-0-gossip.md`](dan/phase-0-gossip.md) … [`phase-3-trust.md`](dan/phase-3-trust.md) | Gossip, autonomy, knowledge, trust |
| Engineering tracker | [`dan/milestones.md`](dan/milestones.md) | P0–P4 deliverables |
| Gap matrix | [`dan/gap-analysis.md`](dan/gap-analysis.md) | v1 substrate vs phase gaps |
| Community + engineering journey | [`dan/CONTRIBUTOR-JOURNEY.md`](dan/CONTRIBUTOR-JOURNEY.md) | I0–I2, D0–D3 sprints |
| Code spikes | [`node/`](../../node/), [`services/validator/`](../../services/validator/) | D0 gossip, D1 attestations (experimental) |

### DAPN (surface)

| Document | Path | Scope covered |
|----------|------|---------------|
| Primitives index | [`primitives/README.md`](primitives/README.md) | Five primitives, composition flow |
| CanvasKit | [`primitives/canvaskit.md`](primitives/canvaskit.md) | UIManifest schema, SSE `canvas_manifest`, v0.1 components |
| ManifestKit | [`primitives/manifestkit.md`](primitives/manifestkit.md) | App/Automation/UIManifest schemas |
| OrchFlow | [`primitives/orchflow.md`](primitives/orchflow.md) | Plane 3 automation substrate |
| ConnectKit | [`primitives/connectkit.md`](primitives/connectkit.md) | Typed API connectors |
| AgentKey | [`primitives/agentkey.md`](primitives/agentkey.md) | Per-action capability tokens |
| ROADMAP DAPN section | [`ROADMAP.md`](../../ROADMAP.md#-dapn--decentralized-agentic-app-network) | Four planes, five primitives |
| Demo agent | [`agents/finance-dashboard-agent/`](../../agents/finance-dashboard-agent/) | Canvas envelope reference implementation |

---

## External scope documents (not yet in repo)

The OSS launch sprint plan was derived from sources that are **not checked in**. When the SRS / technical scope arrives, add rows here and link the file:

| External doc | Expected layer | In-repo status |
|--------------|----------------|----------------|
| `MetaOrcha_OSS_Launch_Plan.md` | OSS M0–M3 | Referenced in [`oss-launch/sprint-plan.md`](oss-launch/sprint-plan.md) — **pending check-in** |
| `OSS-Technical-Scope.md` | OSS v1 boundaries | **Pending** — map sections to M0–M3 and v1.2 Harness |
| `launch-runbook.md` | OSS M3 ops | **Pending** — map to M3 checklist in sprint-plan |
| **SRS (user-provided)** | TBD | **Pending** — use table below to slot sections |

### SRS section template (fill when document arrives)

| SRS section | Maps to layer | Existing doc / milestone | Gap / action |
|-------------|---------------|--------------------------|--------------|
| *(example) Runtime orchestration* | OSS v1 | sprint-plan M0–M2, ROADMAP v1 | — |
| *(example) Federated discovery* | DAN Phase 0 | phase-0-gossip, D0 in CONTRIBUTOR-JOURNEY | libp2p post Day-30 |
| *(example) Declarative agent UI* | DAPN / CanvasKit | primitives/canvaskit.md, Plane 4 | ConnectKit for live data |
| | | | |

---

## Naming crosswalk (avoid confusion)

| Name in docs | Meaning | See also |
|--------------|---------|----------|
| **M0–M3** | OSS launch engineering milestones | [`oss-launch/sprint-plan.md`](oss-launch/sprint-plan.md) |
| **I0–I2** | Community inception gates | [`dan/CONTRIBUTOR-JOURNEY.md`](dan/CONTRIBUTOR-JOURNEY.md) |
| **Phase 0–4** | Public DAN product phases | [`ROADMAP.md`](../../ROADMAP.md), [`dan/phase-*.md`](dan/) |
| **D0–D3** | Internal DAN engineering sprints | [`dan/CONTRIBUTOR-JOURNEY.md`](dan/CONTRIBUTOR-JOURNEY.md) |
| **P0–P4** | DAN deliverable IDs | [`dan/milestones.md`](dan/milestones.md) |
| **Planes 1–4** | DAPN architecture layers | [`ROADMAP.md`](../../ROADMAP.md), [`primitives/README.md`](primitives/README.md) |

**Important:** **D1** (validator attestations spike) is **not** the same as **Phase 1** (full `@autonomous` cognitive loop). See [`dan/gap-analysis.md`](dan/gap-analysis.md).

---

## Branch reconciliation status (2026-06-18)

| Source | Status on `main` |
|--------|------------------|
| `origin/az/beta/v1-playable` CanvasKit + DAPN docs + beta wiring | **Merged** via cherry-pick (`0f912d4`, `2c34e79`, `3ca6dd0`) |
| `origin/dan/inception` incremental phase doc rewrites | **Superseded** by `main` phase specs + INCEPTION reconcile (`4a0e6bc`); no unique code beyond beta merge |
| `origin/az/great-brahmagupta-yik22c` | Duplicate of beta — **delete remote** |
