# Hosted sandbox (M1)

Public demo stack for Orcha. Canonical spec: [SCOPE-MAP.md](../../docs/dev_docs/SCOPE-MAP.md) § M1.

## Quick start

```bash
cp .env.sandbox.example .env.sandbox   # fill secrets — never commit
make -f deploy/sandbox/Makefile up
make -f deploy/sandbox/Makefile seed   # register agents
```

URL (local): http://localhost

## Owner checklist before public URL

1. Set `SANDBOX_MAX_DAILY_MESSAGES` in `.env.sandbox` (default 500 ≈ $50/day at $0.10/msg).
2. Set `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` for LLM routing.
3. Set `JWT_SECRET` to a strong random value.
4. Set `CORS_ORIGINS` to your public domain (not `*` in production).
5. Terminate TLS in front of nginx (see below).

## TLS (public URL)

The bundled `nginx.conf` listens on **:80** inside the compose network. For HTTPS:

- **Cloudflare** (recommended): orange-cloud proxy → origin :80; no cert in container.
- **Caddy / Traefik** on the host: reverse-proxy to `sandbox-nginx:80` with automatic Let's Encrypt.
- **nginx TLS**: add a `listen 443 ssl` server block + mount certs; keep rate limits identical.

## Spend protection

| Control | Env var | Default |
|---------|---------|---------|
| Global daily messages | `SANDBOX_MAX_DAILY_MESSAGES` | 500 |
| Guest messages per account | `SANDBOX_GUEST_MAX_MESSAGES` | 1 |
| Per-IP rate limit | nginx | 60 req/min `/api/`, 5 `/auth/` |

Guest sessions: `GET /auth/guest` when `SANDBOX_MODE=true` (frontend `VITE_SANDBOX_MODE=true`).

**Guest limit:** each guest account gets `SANDBOX_GUEST_MAX_MESSAGES` (default **1**) message. Refresh the page to obtain a new guest session for another try. For launch day, consider temporarily raising `SANDBOX_GUEST_MAX_MESSAGES` in `.env.sandbox`.

## OpenRouter credits

The planner and orchestrator route through OpenRouter. If runs fail with `Internal graph error`, check superagent logs for **402** (insufficient credits). Top up at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits). Orchestrator `max_tokens` is capped at 1024 to reduce credit burn.

## Public URL (Show HN)

Quick tunnel for testing:

```bash
cloudflared tunnel --url http://localhost:80
```

For a stable HN link, use Cloudflare orange-cloud proxy or a named tunnel — pin the URL in [SHOW-HN.md](../../docs/dev_docs/SHOW-HN.md) before posting.

## Vercel frontend + local backend (recommended for Show HN)

Deploy the static React SPA to Vercel while the backend runs locally behind a Cloudflare tunnel. The browser talks directly to the tunnel URL — Vercel only serves HTML/JS/CSS.

**Step 1 — Deploy frontend to Vercel**

Connect the repo in [vercel.com/new](https://vercel.com/new). The `vercel.json` at the repo root configures the build automatically. In Vercel → Settings → Environment Variables, add:

```
VITE_GATEWAY_URL = https://<your-tunnel>.trycloudflare.com/api
VITE_SANDBOX_MODE = true
```

Redeploy after setting env vars (Vercel bakes them in at build time).

**Step 2 — Start the backend and expose via tunnel**

```bash
make -f deploy/sandbox/Makefile up
make -f deploy/sandbox/Makefile seed
cloudflared tunnel --url http://localhost:80
# → prints https://<random>.trycloudflare.com (update VITE_GATEWAY_URL on Vercel)
```

**Step 3 — Allow the Vercel domain in CORS**

Add your Vercel URL to `CORS_ORIGINS` in `.env.sandbox`, then rebuild the gateway:

```bash
# In .env.sandbox:
CORS_ORIGINS=http://localhost:3000,https://app.metaorcha.ai,https://orcha.vercel.app

docker compose -f deploy/sandbox/docker-compose.sandbox.yml up -d --build gateway
```

**Stable tunnel (named, requires Cloudflare account + domain)**

```bash
cloudflared tunnel create orcha-sandbox
cloudflared tunnel route dns orcha-sandbox sandbox.yourdomain.com
cloudflared tunnel run --url http://localhost:80 orcha-sandbox
# → stable https://sandbox.yourdomain.com — no URL change on restart
```

With a stable URL, set `VITE_GATEWAY_URL` once in Vercel and leave it.

## Demo validation

```bash
# M1 portfolio gate (Gates 3–5)
GATEWAY_URL=http://localhost/api ./scripts/m0-gates-live.sh

# M2 3-protocol gate (run 5×, pass ≥4)
GATEWAY_URL=http://localhost/api M2_RUNS=5 M2_PASS=4 ./scripts/m2-gates-live.sh
```

See [M2-DEMO.md](../../docs/dev_docs/M2-DEMO.md) and [docs/assets/README.md](../../docs/assets/README.md) for hero clip recording.

## Services

Registry · PnD · SuperAgent · Gateway · Frontend · PostgreSQL · Redis · Kafka · Ollama · 8 agents (7 fleet + finance-dashboard).
