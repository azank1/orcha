# Orcha OSS Launch — Sprint / Milestone Plan

Internal execution plan derived from `MetaOrcha_OSS_Launch_Plan.md`,
`OSS-Technical-Scope.md`, and `launch-runbook.md`, reconciled against the actual
state of `azank1/orcha` (this checkout was the stale `main` snapshot @ `9c13c49`,
already partly carved — no ignitic/wallet-service/landing_page/deploy).

**This doc lives in `docs/dev_docs/` and is excluded from the public carve.**

**See also:** [MASTER-PLAN.md](../MASTER-PLAN.md) (unified milestone index) · [SCOPE-MAP.md](../SCOPE-MAP.md) (layer mapping + SRS slot)

## Milestones

| Milestone | Theme | Status |
|---|---|---|
| **M0** | Open/closed seam, DID lock, governance + spec | ✅ Done |
| **M1** | Developer experience: emerge CLI/SDK, templates, docs | ✅ Done |
| **M2** | Branding, CI expansion, credential hygiene, ungate dev surfaces | ✅ Core done |
| **M3** | Launch ops (non-code): 5-min test, demo, Discord, PyPI, publish | ⬜ Owner-driven |

### M0 — Foundation ✅
- `ExecutionObserver` hook (NoOp default) wired post-OutputNormalizer in the
  SuperAgent pipeline; fail-closed dispatch + tests. **(I-05)**
- DID namespace locked to **`did:orcha:agent:*` / `did:orcha:system:*`** across
  all 8 manifests, registry validation/model, fixtures, docs. **(I-01)**
- `schema_version` + optional `identity.public_key` on `EmergeConfig`. **(D-05, I-02 partial)**
- `docs/spec/emerge-yaml.schema.json` (JSON Schema) + `docs/spec/governance.md`
  (RFC process). **(D-05, I-04)**
- Community files: root `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `ROADMAP.md`, issue templates (bug/bridge/agent). **(L-01, L-02, L-03)**
- Phantom agents (`code-executor`, `data-analyzer`) removed from Makefile. **(C-04)**

### M1 — Developer Experience ✅
- `sdk/` package (`orcha-sdk`, import `emerge`), dependency-light (stdlib + pyyaml):
  - `@emerge.agent` decorator (≤3-line registration, sync/async handlers).
  - `emerge` CLI: `init` / `run` / `publish`. **(D-01)**
  - stdlib A2A server matching the runtime's JSON-RPC contract
    (`/health`, `/.well-known/agent.json`, `message/send`, `tasks/get`).
  - registry client + manifest generator; tests cover decorator→server→RPC.
- `templates/your-first-bridge` (commented `AgentHandler` skeleton). **(D-02)**
- Bundled `your-first-agent` template for `emerge init`. **(D-02)**
- Docs funnel: `quickstart.md`, `bridges.md`, `emerge-yaml.md`, `protocols.md`. **(D-03)**
- Wired `orcha-sdk` into the uv workspace; `uv.lock` regenerated.

### M2 — Hardening + branding ✅ (core)
- README launch hero; repo layout updated. **(B-01, B-02)**
- CI: SDK job + SuperAgent middleware/observer job, scoped to touched paths
  so green from day one. **(C-02)**
- `.gitignore` credential patterns. **(S-02)**
- Frontend display strings → Orcha; Agent Library + Register ungated into main
  nav (launch plan 3.3).

## Remaining backlog

### M2 follow-ups (before carve)
- [ ] **Infra/identifier rebrand** (`metaorcha` → `orcha`) in non-public-facing
  but carve-flagged spots: `docker-compose*.yml` (container/network/DB names),
  `scripts/*.sh`, kafka topic/group prefixes, env-var prefixes
  (`PAT_TOKEN_PREFIX=metaorcha_pat_`), `PAYMENT_FACILITATOR_URL`. **Risky —
  requires a live-stack run to verify (DB name, kafka, network refs are
  cross-referenced).** Do atomically + `./scripts/run-all.sh` smoke. **(B-01, S-01)**
  - Pre-existing DB-name drift: compose uses `metaorcha`, README/some env
    examples use `metaorcha-db` — unify during this pass.
- [ ] `frontend/.env.example` missing `VITE_GATEWAY_URL`; phantom-agent
  `.env.example`s. **(S-03)**
- [ ] Confirm `run-all.sh` has the `grpc-generate` step (commit `9c13c49`
  suggests added — verify Phase 2). **(R-01)**
- [ ] Backfill SuperAgent middleware test coverage (auth cascade + dispatch),
  then widen the CI lint scope beyond `middleware/` once pre-existing ruff debt
  (17 findings in `superagent/src`) is cleared. **(C-02)**

### M3 — Launch ops (owner-driven, mostly non-code)
- [ ] Placeholder swap: `discord.gg/orcha`, `security@orcha.ai`,
  `conduct@orcha.ai`, repo URL — per runbook §1. **(L-04, B-02)**
- [ ] `oss-carve.sh` + `oss-private-paths.txt` (not present here) → carved
  snapshot → update public `main`. **(G-01..G-02)**
- [ ] `make install && grpc-generate && prisma-generate && make check` on carved
  tree. **(G-03, C-03)**
- [ ] `./scripts/run-all.sh` smoke (services + 7 agents). **(G-04, R-02)**
- [ ] `emerge init && emerge run --no-register` smoke on carved tree. **(G-05)**
- [ ] CI green on `main` (GitHub Actions billing). **(C-01)**
- [ ] **5-minute outsider test** on a clean machine, quickstart only. **(O-01)**
- [ ] Demo video (60–90s), Discord server, PyPI `orcha-sdk` publish. **(O-02..O-04, D-04)**
- [ ] Public registry browse page (Etherscan surface) — launch plan T3 / deferred.

## Notes / decisions
- **DID namespace:** chose `did:orcha:` (owner decision) over both `did:metaorcha:`
  (launch plan) and `did:emerge:` (scope doc) — aligns identity with the product
  name, sidesteps the brand leak and toolchain coupling.
- **SDK location:** `sdk/` (MIT) rather than folding into `common/emerge-tools/`
  (which stays manifests-only and is loaded by SuperAgent via filesystem path).
- **SDK dependencies:** stdlib + pyyaml only — directly serves the "no heavy
  deps / 5-minute" bar and keeps `pip install orcha-sdk` light.
