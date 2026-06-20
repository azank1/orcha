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
| Per-IP rate limit | nginx | 10 req/min `/api/`, 5 `/auth/` |

Guest sessions: `GET /auth/guest` when `SANDBOX_MODE=true` (frontend `VITE_SANDBOX_MODE=true`).

## Services

Registry · PnD · SuperAgent · Gateway · Frontend · PostgreSQL · Redis · Kafka · Ollama · 8 agents (7 fleet + finance-dashboard).
