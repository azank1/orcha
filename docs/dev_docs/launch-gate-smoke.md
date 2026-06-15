# Launch gate — manual smoke checklist

Run this on a **fresh machine** (or VM) before tagging a public release.
Automated portions are in [`scripts/launch-gate-ci.sh`](../scripts/launch-gate-ci.sh) and the CI `launch-gate` job.

## Prerequisites (clean host)

- [ ] Docker installed and running
- [ ] Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- [ ] Node.js 20+ and npm (for frontend check)
- [ ] OpenRouter API key (for chat smoke)
- [ ] No pre-existing Orcha `.env` files copied by hand

## Automated gate (CI parity)

```bash
git clone git@github.com:azank1/orcha.git
cd orcha
make install
docker compose -f docker-compose.local.yml up -d postgres redis
./scripts/launch-gate-ci.sh
```

Expected: script exits 0 with `launch-gate PASS`.

## Full stack (recommended local proof)

```bash
cp services/registry/.env.example services/registry/.env
cp services/planning-discovery/.env.example services/planning-discovery/.env.development
cp services/superagent/.env.example services/superagent/.env
cp services/gateway/.env.example services/gateway/.env
# Fill OPENROUTER_API_KEY, VAULT_KEY, and gateway local URLs:
#   SUPERAGENT_URL=http://127.0.0.1:8002
#   REGISTRY_URL=http://127.0.0.1:8000

make setup
./scripts/run-all.sh
```

## Manual checks

- [ ] `./scripts/run-all.sh` completes without manual intervention
- [ ] Frontend loads at http://localhost:3000
- [ ] Login works with `PAYMENT_MODE=mock` (5000 credits seeded)
- [ ] `curl http://localhost:8000/api/v1/agents` lists fleet agents
- [ ] PnD search returns at least one agent (requires Ollama + embeddings)
- [ ] SuperAgent single-turn chat invokes a registered agent (CLI or UI)
- [ ] SDK path: `emerge init my-agent && cd my-agent && emerge run --register` registers in Registry

## Sign-off

| Check | Owner | Date | Notes |
|---|---|---|---|
| Automated launch-gate | | | |
| Full run-all stack | | | |
| SDK quickstart | | | |
| Frontend chat | | | |
