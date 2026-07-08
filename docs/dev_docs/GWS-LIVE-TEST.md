# Google Workspace Live Test — real OAuth, real APIs

> The PoC harness (`docs/dev_docs/POC.md`) proves the loop's *mechanics* with a
> deterministic fixture. This test proves the *content*: the AI decomposes a
> Workspace goal, authenticates against real Google OAuth, and reads/writes
> real Gmail/Drive/Sheets data — end to end, in the same verified loop.

## One-time setup (owner, ~1 hour)

### 1. Google Cloud Console

1. Create (or reuse) a project → **APIs & Services**.
2. Enable APIs: **Gmail, Drive, Calendar, Docs, Sheets** (add others per
   `agents/google-workspace-orchestrator/emerge.yaml` scopes as needed).
3. **OAuth consent screen** → External → **Testing** mode → add your own
   Google account as a **test user**. (Testing mode allows all the declared
   scopes for test users without app verification.)
4. **Credentials → Create credentials → OAuth client ID → Web application**:
   - Authorized redirect URI — exactly: `http://localhost:3011/auth/callback`
5. Copy the client ID + secret.

### 2. `.env.sandbox`

```bash
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<your-secret>
```

### 3. Rebuild + reseed

```bash
docker compose -f deploy/sandbox/docker-compose.sandbox.yml up -d --build gws-orchestrator
make -f deploy/sandbox/Makefile seed   # re-registers manifests (redirect_uri preserved)
curl -s http://localhost:3011/health   # agent reachable from the host (3011 → container 8080)
```

## The test

Open the UI (`http://localhost`) and type:

> **Check my Gmail inbox for unread emails and summarize the most recent one**

Expected sequence:

| Step | What you see | What it proves |
|------|--------------|----------------|
| 1 | Plan step routes to `google-workspace-orchestrator` | PnD discovery + LLM routing to a *real* agent |
| 2 | **Auth interrupt** with a Google consent link (SSE `interrupt`, type `AGENT_OAUTH_CALLBACK`) | preflight built the authorize URL from `emerge.yaml` (redirect `localhost:3011`) |
| 3 | Consent popup → approve → browser lands on the agent's `/auth/callback` → "Tokens stored and session resumed" | the agent exchanged the code itself (it holds the secret) and POSTed `resume-agent-oauth` to the gateway |
| 4 | Session resumes automatically; the agent's own LLM loop calls real Gmail via workspace-mcp | the re-sent task found the bearer via `metadata.session_id` in the durable token store |
| 5 | Real inbox summary in the result, with the **✓ Verified** badge | the verifier ran on genuine API output, not a fixture |

Then try a **write**: *"Create a Google Doc titled 'Orcha live test' with a one-line summary of my latest email"* — confirm the doc appears in your Drive.

## The durability test (the fix this shipped)

```bash
docker restart sandbox-gws-orchestrator
# wait ~10s, then in the SAME chat session:
#   "List my 3 most recent unread emails"
```

**Expected: no re-consent.** The token store is SQLite on the `gws-tokens`
volume (`GWS_TOKEN_DB=/app/data/tokens.db`) — before this fix the tokens
lived in process memory and a restart silently logged you out mid-session.

## Failure modes

| Symptom | Cause |
|---------|-------|
| `redirect_uri_mismatch` on consent | Google Cloud redirect URI is not exactly `http://localhost:3011/auth/callback`, or the registered manifest's `redirect_uri` was rewritten (the seed script only rewrites `endpoint:`/`health_endpoint:` lines to the docker-internal hostname — every OAuth URL field, including `authorization_url` and `oauth_connect_url` on other agents, is left untouched by construction; verify with `curl -s localhost:8000/api/v1/agents/did:orcha:agent:google-workspace-orchestrator | grep redirect_uri`) |
| Callback returns 503 | `GOOGLE_OAUTH_CLIENT_SECRET` not set in `.env.sandbox` / container not rebuilt |
| Consent OK but session never resumes | `GATEWAY_BASE_URL` wrong inside the container — compose must set `http://gateway:8080` (the config default `localhost:8080` is the agent itself) |
| Re-consent after agent restart | token volume missing — check `gws-tokens` volume is mounted at `/app/data` |
| `access_denied` on consent | your Google account is not added as a test user on the consent screen |

## Security notes

- The callback logs token *shape* only (`has_refresh`, `expires_in`, scope) —
  never token material.
- The resume POST to the gateway carries `{agent_id, status}` — the OAuth
  token never transits the gateway or SuperAgent.
- Tokens at rest: SQLite on a local docker volume, sandbox scope. For hosted
  deployments, encrypting this store (or migrating it to the platform vault
  via the dormant `AuthManager._oauth2` refresh-token path) is the D2-adjacent
  follow-up.
