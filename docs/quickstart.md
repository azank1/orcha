# Quickstart — clone to a registered agent in ~5 minutes

This is the 5-minute path: from `git clone` to your own agent registered and
callable. It runs fully in **mock payment mode** — no wallet, no chain, no keys
beyond a single LLM API key.

## Prerequisites

- **Docker** (for Postgres, Kafka, Redis, registry)
- **Python 3.12+** and [**uv**](https://docs.astral.sh/uv/) (`pip install uv`)
- An **OpenRouter API key** ([openrouter.ai](https://openrouter.ai)) — used for
  completions and (optionally) embeddings.

> Embeddings run on Ollama locally **or** OpenRouter. The default compose file
> includes Ollama (`nomic-embed-text`); set `EMBEDDING_PROVIDER=openrouter` to
> skip the Ollama download entirely.

## 1. Clone and install

```bash
git clone git@github.com:azank1/orcha.git
cd orcha
cp services/registry/.env.example services/registry/.env      # placeholders are fine
echo "OPENROUTER_API_KEY=sk-or-..." >> services/superagent/.env

make install            # uv sync — Python deps + the `emerge` CLI
make prisma-generate    # database client
make grpc-generate       # registry gRPC stubs
```

## 2. Bring the stack up

```bash
./scripts/run-all.sh
```

This starts the infrastructure and the core services:

| Service | URL |
|---|---|
| Registry | http://localhost:8000 |
| Planning & Discovery | http://localhost:8001 |
| SuperAgent | http://localhost:8002 |
| Gateway (mock payments) | http://localhost:8080 |
| Frontend | http://localhost:3000 |

Wait until the registry health check passes:

```bash
curl -s localhost:8000/ | head
```

## 3. Create and register your first agent

In a second terminal:

```bash
emerge init "My Agent"
cd my-agent
emerge run
```

You should see:

```
✓ Serving My Agent on http://localhost:8900  (did:orcha:agent:my-agent)
  ✓ Registered with http://localhost:8000
```

That's it — your agent is registered and discoverable. Confirm it:

```bash
curl -s localhost:8000/api/v1/agents | python -m json.tool
curl -s localhost:8900/.well-known/agent.json | python -m json.tool
```

## 4. Use it

Open the frontend at http://localhost:3000, or drive the SuperAgent directly,
and give it a goal your agent can handle. The planner discovers your agent in
the registry and routes the matching step to it.

## Next steps

- [`join.md`](join.md) — pick a role, phased journey diagram
- [`VISION.md`](../VISION.md) — why Orcha → DAN
- [`ROADMAP.md`](../ROADMAP.md) — milestones
- Edit `agent.py` — see [`emerge-yaml.md`](emerge-yaml.md)
- Contributor setup: [`setup.md`](setup.md)
- Connect a protocol: [`bridges.md`](bridges.md)

## Troubleshooting

- **`emerge: command not found`** — run inside the uv env: `uv run emerge ...`,
  or `pip install -e sdk`.
- **Registration skipped / connection refused** — the registry isn't up yet;
  re-run after `curl localhost:8000/` succeeds. Use `emerge run --no-register`
  to serve without registering.
- **Embedding/Ollama errors** — set `EMBEDDING_PROVIDER=openrouter` to avoid the
  local model download.
