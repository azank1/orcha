# Orcha

**Orchestrate AI agents across MCP, A2A, and ACP in one runtime.**

Every agent framework assumes all your agents speak the same protocol. In
practice you end up with MCP servers here, A2A agents there, and a pile of glue
code. Orcha is an orchestration runtime where **one natural-language goal gets
planned, routed, and executed across agents speaking _different_ protocols in
the same run** — with input validation, a credential vault + auth cascade
(OAuth included), output normalization, human-in-the-loop approvals, and
per-call payments (mock mode by default — no wallet needed).

> 📺 **Demo:** _<60–90s demo video — coming at launch>_
> 💬 **Community:** [Discord](https://discord.gg/orcha) · 📖 [Quickstart](docs/quickstart.md) · 🧩 [Write a bridge](docs/bridges.md)

## Register an agent in 3 lines

```python
import emerge

@emerge.agent(name="My Agent", description="What I do")
def handle(task: str) -> str:
    return f"handled: {task}"
```

```bash
emerge run        # serve locally + register against the local registry
```

The manifest ([`emerge.yaml`](docs/emerge-yaml.md) — versioned, JSON-Schema'd)
gives every agent a DID, declared transport, auth, and pricing. See the
[**5-minute quickstart**](docs/quickstart.md) to go from `git clone` to a
registered, callable agent.

## How it works

Agents register via a **Registry**, are discovered by a **Planning & Discovery**
service, and are orchestrated by a **SuperAgent** that delegates each step to the
right agent at the right time. A **React + Vite** web app (`frontend/`) talks to
the **Gateway** (port 8080) for auth, sessions, and streaming orchestration.

Everything is open: the engine, the registry, the planner, the frontend, the
CLI/SDK, and the [bridge interface](docs/bridges.md) for adding new protocols —
that's the contribution we most want. See [`ROADMAP.md`](ROADMAP.md) for the
trajectory and [`CONTRIBUTING.md`](CONTRIBUTING.md) to get involved.

## Repository layout

```bash
git clone git@github.com:azank1/orcha.git
cd orcha
```

```
orcha/
├── agents/                    # Example agents (MCP, A2A)
│   ├── ecommerce-automation/
│   ├── google-workspace-orchestrator/
│   ├── lead-gen-agent/
│   ├── notion-mcp/
│   ├── notion-research/
│   ├── search-agent/
│   └── web-scraper/
├── common/                    # Shared libraries (database, proto, LLM)
├── frontend/                  # React web app (Vite dev server — port 3000)
├── sdk/                       # orcha-sdk — `emerge` CLI + @emerge.agent SDK
├── templates/                 # your-first-agent, your-first-bridge scaffolds
├── docs/                      # quickstart, emerge-yaml, protocols, bridges, spec
├── services/
│   ├── registry/              # Agent registration — REST + gRPC (port 8000)
│   ├── planning-discovery/    # Agent discovery + planning (port 8001)
│   ├── superagent/            # Orchestrator LLM backend (port 8002)
│   └── gateway/               # BFF — auth, sessions, proxies to SuperAgent (port 8080)
├── Makefile                   # All dev commands
└── pyproject.toml             # UV workspace root
```

---

## Quickstart vs. manual setup

Most people should follow the **[5-minute quickstart](docs/quickstart.md)**
(`docker-compose.local.yml` + `./scripts/run-all.sh` + `emerge run`). The steps
below are the **detailed manual setup** for working on the services themselves.

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** and **npm** (for the `frontend/` web app)
- **Docker** (for Postgres, Redis, Kafka)
- **Ollama** (for local embeddings — `nomic-embed-text` model)
- **OpenRouter API key** (for LLM completions)

---

## Step 1 — Start infrastructure

**Recommended:** use the compose stack (matches `./scripts/run-all.sh` and [docs/quickstart.md](docs/quickstart.md)):

```bash
make docker-up          # postgres, redis, kafka via docker-compose.local.yml
make kafka-topics       # create required Kafka topics
```

Postgres defaults from [`docker-compose.local.yml`](docker-compose.local.yml):

| Setting | Value |
|---|---|
| User / password | `postgres` / `postgres` |
| Database | `metaorcha` |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/metaorcha` |

<details>
<summary>Alternative: standalone Postgres container</summary>

```bash
docker run --name metaorcha \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=metaorcha \
  -p 5432:5432 \
  -d pgvector/pgvector:pg15
```

Use the same `DATABASE_URL` as above in all service `.env` files.

</details>

### Redis (SuperAgent session state)

```bash
make redis-up
```

### Kafka (agent registration events)

```bash
make kafka-up
make kafka-topics
```

---

## Step 2 — Install dependencies

```bash
make install
```

---

## Step 3 — Database setup

Run migrations and generate the Prisma client:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/metaorcha" make migrate
make prisma-generate
```

---

## Step 4 — Configure services

Each service reads its config from a `.env` file in the service root. Copy the example and fill in your secrets.

### Registry

```bash
cp services/registry/.env.example services/registry/.env
```

Edit `services/registry/.env` and set:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/metaorcha` |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` |
| `KAFKA_ENABLED` | `true` |
| `DISABLE_AUTH` | `true` (for local dev) |

### Planning & Discovery

```bash
cp services/planning-discovery/.env.example services/planning-discovery/.env.development
```

Edit `services/planning-discovery/.env.development` and set:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/metaorcha` |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `LLM_EMBEDDING_MODEL` | `nomic-embed-text` (requires Ollama) |

> Ollama must be running locally with `nomic-embed-text` pulled: `ollama pull nomic-embed-text`

### SuperAgent

```bash
cp services/superagent/.env.example services/superagent/.env
```

Edit `services/superagent/.env` and set:

| Variable | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `VAULT_KEY` | Run `openssl rand -base64 32` to generate |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/metaorcha` |

---

## Step 5 — Start services

Open terminals as needed (or use `tmux`). All commands run from the **monorepo root**.

```bash
# Terminal 1 — Planning & Discovery
make pnd-dev

# Terminal 2 — Registry
make dev s=registry

# Terminal 3 — SuperAgent
make sa-dev

# Terminal 4 — Gateway (required for the web app in Step 9)
make gw-dev
```

Copy and edit Gateway config once:

```bash
cp services/gateway/.env.example services/gateway/.env
```

> **Local dev ports:** Registry `:8000`, PnD `:8001`, SuperAgent `:8002`, Gateway `:8080`.
> The example `.env` lists supervisord/production port layout (`SUPERAGENT_URL=:8001`, `REGISTRY_URL=:8003`).
> For local `make gw-dev`, override to:
> `SUPERAGENT_URL=http://127.0.0.1:8002` and `REGISTRY_URL=http://127.0.0.1:8000`.

### Payment mode

The Gateway ships with `PAYMENT_MODE=mock` by default — new users are seeded with mock credits so the full orchestration flow works without external payment setup. **This is the recommended mode for local development.**

Service URLs:

| Service | URL | API Docs |
|---|---|---|
| Registry | http://localhost:8000 | http://localhost:8000/docs |
| Planning & Discovery | http://localhost:8001 | http://localhost:8001/docs |
| SuperAgent | http://localhost:8002 | http://localhost:8002/docs |
| Gateway | http://localhost:8080 | http://localhost:8080/docs |

---

## Step 6 — Register agents

### Option A — Full stack (recommended)

With services and agents running:

```bash
./scripts/run-all.sh          # registers all agents/*/emerge.yaml + embeddings
# or, if infra/services are already up:
make agents-dev               # start HTTP agents first
make seed-live                # register fleet manifests + trigger embeddings
```

### Option B — Test fixtures only (no live agent servers)

```bash
make seed
```

This registers **registry test fixtures** from `services/registry/tests/fixtures/` (via a local manifest server on port 9000). It does **not** register the example fleet in `agents/`.

### Option C — Register via Swagger UI

1. Open http://localhost:8000/docs
2. Use `POST /api/v1/agents/register`
3. Upload any `agents/<name>/emerge.yaml`

### Option D — SDK (after quickstart scaffold)

```bash
emerge init my-agent && cd my-agent && emerge run --register
```

See [docs/quickstart.md](docs/quickstart.md).

---

## Step 7 — Start example agents

```bash
make agents-dev
```

This starts all HTTP agents with multiplexed logs:

| Agent | Port | Protocol |
|---|---|---|
| web-scraper | 3004 | A2A HTTP |
| notion-research | 3006 | A2A HTTP |
| search-agent | 3007 | MCP SSE |
| ecommerce-automation | 3009 | A2A HTTP |
| google-workspace-orchestrator | 3011 | A2A HTTP |
| lead-gen-agent | 4567 | A2A HTTP |
| notion-mcp | stdio | MCP STDIO |

### Agent environment setup

Each agent has a `.env.example`. Copy and configure before running:

```bash
cp agents/web-scraper/.env.example      agents/web-scraper/.env
cp agents/notion-mcp/.env.example       agents/notion-mcp/.env
cp agents/notion-research/.env.example  agents/notion-research/.env
cp agents/search-agent/.env.example     agents/search-agent/.env
```

Agents that need secrets:

| Agent | Required secret |
|---|---|
| `search-agent` | `SERPER_API_KEY` |
| `notion-mcp` | `NOTION_API_KEY` |
| `notion-research` | `NOTION_API_KEY`, `OPENROUTER_API_KEY` |

---

## Step 8 — Register agent runtime secrets

For agents that need API keys at call-time (e.g. a Notion agent that needs `NOTION_API_KEY`), register the secret via SuperAgent so it can be injected at runtime:

1. Open http://localhost:8002/docs
2. Use `POST /secrets/agent-env`
3. Provide the `agent_id` and the key/value pair
userId should be (if using superagent cli interface) `dev_user`

---

## Step 9 — Chat with SuperAgent

You can use either the **web app** (Gateway + React) or the **CLI** — both talk to the same SuperAgent stack.

### Option A — Web app (`npm run dev`)

1. Ensure **Gateway** is running (`make gw-dev` from Step 5) and the other backend services are up.
2. Install and start the Vite dev server:

```bash
cd frontend
npm install          # first time only
npm run dev
```

3. Open **http://localhost:3000** (see `frontend/vite.config.ts` if the port differs).

The UI calls the Gateway at **`VITE_GATEWAY_URL`**, which defaults to **`http://localhost:8080`**. To point at another host, create `frontend/.env.local`:

```bash
echo 'VITE_GATEWAY_URL=http://localhost:8080' > frontend/.env.local
```

Production build (optional):

```bash
cd frontend
npm run build
npm run preview   # local preview of the production bundle
```

### Option B — CLI chat

```bash
# Another terminal from repo root
make chat
```

Or run directly:

```bash
uv run python services/superagent/cli/chat.py --port 8002
```

Type a message and SuperAgent will plan, discover, and delegate to the right agents.

---

## Make targets

All commands run from the **monorepo root**.

### Setup & dependencies

| Target | Description |
|---|---|
| `make install` | Install all workspace dependencies |
| `make prisma-generate` | Generate Prisma client + fetch engine binary |
| `make migrate` | Apply database migrations |
| `make migrate-dev` | Create and apply a new migration |
| `make db-indices` | Apply pgvector indices (run after `make migrate`) |

### Running services

| Target | Description |
|---|---|
| `make pnd-dev` | Start Planning & Discovery (port 8001) |
| `make dev s=registry` | Start Registry (port 8000) |
| `make sa-dev` | Start SuperAgent (port 8002) |
| `make gw-dev` | Start Gateway (port 8080) — use with `frontend` |
| `make gw-dev-watch` | Gateway with auto-reload |
| `make agents-dev` | Start all example agents |

### Infrastructure

| Target | Description |
|---|---|
| `make redis-up` | Start Redis |
| `make redis-down` | Stop Redis |
| `make kafka-up` | Start Kafka |
| `make kafka-down` | Stop Kafka |
| `make kafka-topics` | Create required Kafka topics |

### Testing

| Target | Description |
|---|---|
| `make test-all` | Run tests for all services |
| `make test s=registry` | Run tests for a specific service |
| `make sa-test` | Run SuperAgent tests only |
| `make pnd-test` | Run Planning & Discovery tests only |

### Code quality

| Target | Description |
|---|---|
| `make lint` | Run ruff linter (with auto-fix) |
| `make format` | Format code with ruff |
| `make format-check` | Check formatting without modifying files |
| `make check` | Run lint + format-check + test-all |

### Seeding & utilities

| Target | Description |
|---|---|
| `make seed` | Register registry test fixtures (not fleet agents in `agents/`) |
| `make seed-live` | Register fleet agents from `agents/*/emerge.yaml` |
| `make chat` | Open SuperAgent CLI chat |

---

## PR checklist

Before opening a PR, ensure all checks pass:

```bash
make check
```

This runs `make lint`, `make format-check`, and `make test-all`.
