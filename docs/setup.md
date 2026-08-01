# Manual setup — for contributors

Most users should use the **[5-minute quickstart](quickstart.md)** (`./scripts/run-all.sh`). This guide is for working on individual services, debugging infra, or running without the all-in-one script.

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node.js 20+** and **npm** (frontend)
- **Docker** (Postgres, Redis, Kafka)
- **Ollama** with `nomic-embed-text` (or OpenRouter embeddings)
- **OpenRouter API key**

---

## Step 1 — Infrastructure

```bash
make docker-up
make kafka-topics
make redis-up
```

Postgres defaults (`docker-compose.local.yml`):

| Setting | Value |
|---|---|
| User / password | `postgres` / `postgres` |
| Database | `orcha` |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/orcha` |

<details>
<summary>Standalone Postgres container</summary>

```bash
docker run --name orcha \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=orcha \
  -p 5432:5432 \
  -d pgvector/pgvector:pg15
```

</details>

---

## Step 2 — Install & database

```bash
make install
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/orcha" make migrate
make prisma-generate
make grpc-generate
```

---

## Step 3 — Configure services

Copy each `.env.example` and set secrets. Minimum for local dev:

**Registry** — `services/registry/.env`: `DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`, `KAFKA_ENABLED=true`, `DISABLE_AUTH=true`

**Planning & Discovery** — `services/planning-discovery/.env.development`: `DATABASE_URL`, `OPENROUTER_API_KEY`, `LLM_EMBEDDING_MODEL=nomic-embed-text`

**SuperAgent** — `services/superagent/.env`: `OPENROUTER_API_KEY`, `VAULT_KEY=$(openssl rand -base64 32)`, `DATABASE_URL`

**Gateway** — `services/gateway/.env`: for `make gw-dev` use `SUPERAGENT_URL=http://127.0.0.1:8002` and `REGISTRY_URL=http://127.0.0.1:8000`

Gateway defaults to `PAYMENT_MODE=mock` — no wallet needed.

---

## Step 4 — Start services

From repo root, separate terminals:

```bash
make pnd-dev              # :8001
make dev s=registry       # :8000
make sa-dev               # :8002
make gw-dev               # :8080
```

| Service | URL | Docs |
|---|---|---|
| Registry | http://localhost:8000 | /docs |
| Planning & Discovery | http://localhost:8001 | /docs |
| SuperAgent | http://localhost:8002 | /docs |
| Gateway | http://localhost:8080 | /docs |

---

## Step 5 — Register agents

```bash
make agents-dev           # start example HTTP agents
make seed-live            # register agents/*/emerge.yaml + embeddings
# or: make seed           # registry test fixtures only
```

SDK path: `emerge init my-agent && cd my-agent && emerge run`

---

## Step 6 — Chat / UI

**CLI:** `make chat`

**Web:** `cd frontend && npm install && npm run dev` → http://localhost:3000 (requires Gateway)

---

## Make targets (reference)

| Target | Description |
|---|---|
| `make install` | Workspace deps |
| `make migrate` | DB migrations |
| `make prisma-generate` | Prisma client |
| `make pnd-dev` / `make sa-dev` / `make gw-dev` | Core services |
| `make agents-dev` | Example agents |
| `make seed` / `make seed-live` | Register fixtures / fleet |
| `make kafka-up` / `make kafka-topics` | Kafka |
| `make test-all` / `make check` | Tests + lint |

Full list: run `make help`.

---

## PR checklist

```bash
make check
```
