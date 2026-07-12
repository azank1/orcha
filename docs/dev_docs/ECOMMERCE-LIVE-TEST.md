# E-commerce Automation Live Test — real Shopify, real Meta APIs

> The PoC harness (`docs/dev_docs/POC.md`) proves the loop's *mechanics* with a
> deterministic fixture. This test proves the *content*: the AI decomposes a
> real store-management goal and calls real Shopify / Facebook / Instagram
> APIs — end to end, in the same verified loop.

Every integration below is independently optional. You don't need all three
to run a live test — Shopify alone (via a static access token) is the
fastest path.

## Fastest path: Shopify static token (~10 minutes)

No OAuth flow needed — a Shopify Admin API access token is enough.

1. Shopify Admin → **Settings → Apps and sales channels → Develop apps** →
   create a custom app → **Configure Admin API scopes**: enable
   `read_products` and `write_products` → **Install app** → copy the
   **Admin API access token**.
2. In `.env.sandbox` (or the agent's own `.env` for local dev):
   ```bash
   SHOPIFY_STORE_URL=https://your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=<your-admin-api-token>
   ```
3. Rebuild + reseed:
   ```bash
   docker compose -f deploy/sandbox/docker-compose.sandbox.yml up -d --build ecommerce
   make -f deploy/sandbox/Makefile seed
   curl -s http://localhost:3009/health   # agent reachable from the host (3009 → container 8080)
   ```

## OAuth path: Shopify Partner app (~30 minutes)

Use this if you want the agent-managed OAuth flow (`/auth/start` →
`/auth/callback`) instead of a static token — e.g. to test the same
consent-and-resume pattern `GWS-LIVE-TEST.md` documents for Google.

### 1. Shopify Partners

1. Create a Partner account at [partners.shopify.com](https://partners.shopify.com) → create an app.
2. **App setup → URLs**:
   - Allowed redirection URL(s) — exactly: `http://localhost:3009/auth/callback`
3. Copy the **Client ID** and **Client secret**.

### 2. `.env.sandbox`

```bash
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_OAUTH_CLIENT_ID=<your-client-id>
SHOPIFY_OAUTH_CLIENT_SECRET=<your-secret>
```

### 3. Rebuild + reseed

```bash
docker compose -f deploy/sandbox/docker-compose.sandbox.yml up -d --build ecommerce
make -f deploy/sandbox/Makefile seed   # re-registers manifests (redirect_uri preserved)
curl -s http://localhost:3009/health   # agent reachable from the host (3009 → container 8080)
```

## The test

Open the UI (`http://localhost`) and type:

> **List my active Shopify products**

Expected sequence (static-token path):

| Step | What you see | What it proves |
|------|--------------|-----------------|
| 1 | Plan step routes to `ecommerce-automation` | PnD discovery + LLM routing to a *real* agent |
| 2 | Real product list in the result, with the **✓ Verified** badge | the verifier ran on genuine Shopify Admin API output, not a mock |

Expected sequence (OAuth path) — same as `GWS-LIVE-TEST.md`'s Google flow:

| Step | What you see | What it proves |
|------|--------------|-----------------|
| 1 | Plan step routes to `ecommerce-automation` | PnD discovery + LLM routing to a *real* agent |
| 2 | **Auth interrupt** with a Shopify consent link (SSE `interrupt`, type `AGENT_OAUTH_CALLBACK`) | preflight built the authorize URL from `emerge.yaml` (redirect `localhost:3009`) |
| 3 | Consent popup → approve → browser lands on the agent's `/auth/callback` → session resumed | the agent exchanged the code itself (it holds the secret) and POSTed `resume-agent-oauth` to the gateway |
| 4 | Real product list in the result, with the **✓ Verified** badge | the verifier ran on genuine API output, not a fixture |

Then try a **write**: *"Create a Shopify product called Test Item priced at $9.99, SKU TEST-001"* — confirm it appears in your store's product list (as a draft, per Shopify's default).

If you also configured `FB_ACCESS_TOKEN`/`FB_PAGE_ID` or `IG_ACCESS_TOKEN`/`IG_USER_ID`, try: *"Post to my Facebook page: testing Orcha's ecommerce agent"* or *"Get Instagram insights for my last post"*.

## The real-work goal: research → list → publish, chained across two A2A agents

The compelling end-to-end scenario for this agent is a real content pipeline
a store owner would actually run, spanning **two different A2A agents in one
goal**:

> **Use your web scraper agent to summarize `<a product research URL>`, then
> create a Shopify product using that summary as the description, and post
> about the new product on Instagram.**

This chains `web-scraper` (research) → `ecommerce-automation` (Shopify
create) → `ecommerce-automation` (Instagram publish) — three real A2A calls
in one planned run.

**Known non-determinism (tested live during this doc's authoring, not
resolved):** the ReAct planner does not reliably route this chain today.
Two separate causes observed:

1. The orchestrator's tool list also contains an unconfigured system
   Firecrawl "web-scraper" tool (see `common/emerge-tools/manifests/web-scraper.yaml`)
   that shares a name with the real `web-scraper` A2A agent. For a short,
   single-purpose goal, naming the agent explicitly ("your web scraper
   agent") reliably steers the LLM to the correct `delegate__did_orcha_agent_web-scraper`
   tool. For this longer, 3-step chained goal, the LLM was observed retrying
   the broken system tool multiple times across turns even with the same
   explicit phrasing — a systemic tool-selection issue, not something fixed
   by wording alone.
2. Planning & Discovery's candidate search did not surface
   `ecommerce-automation` at all for several tested phrasings of "list/create
   a Shopify product" — a candidate-ranking gap in `services/planning-discovery`,
   separate from the tool-naming collision above.

**If you hit this:** split the goal into separate messages in the same
session (research first, confirm it used the real agent, then ask for the
Shopify + Instagram steps) — that keeps each step's tool list simpler and
avoids the multi-turn retry behavior. A durable fix requires either (a)
excluding unconfigured system MCP tools from PnD's own candidate results
(today they're filtered only at SuperAgent's boot-time baseline — see
`services/superagent/src/superagent/startup/platform_mcp_baseline.py` — not
at PnD's candidate-search layer), or (b) improving PnD's semantic ranking for
ecommerce/social-flavored goals. Both are follow-up work, not yet done.

## Confirming you're not looking at mock data

Every mock response includes `"status": "mock"` and Mock-prefixed IDs/titles (e.g. `mock_001`, `Mock Vendor`). A real response has `"status": "ok"` and real Shopify/Graph API IDs. If you want misconfiguration to fail loudly instead of silently serving mock data, set `REQUIRE_LIVE_CREDENTIALS=true` (see `agents/ecommerce-automation/README.md`) — this is recommended for any deployment beyond the public demo/sandbox.

## Failure modes

| Symptom | Cause |
|---------|-------|
| `redirect_uri_mismatch` on Shopify consent | The Partner app's Allowed redirection URL is not exactly `http://localhost:3009/auth/callback`, or the registered manifest's `redirect_uri` was rewritten — the seed script only rewrites `endpoint:`/`health_endpoint:` lines to the docker-internal hostname; verify with `curl -s localhost:8000/api/v1/agents/did:orcha:agent:ecommerce-automation \| grep redirect_uri` |
| Callback returns 503 `Shopify OAuth client is not configured` | `SHOPIFY_OAUTH_CLIENT_SECRET` not set, or container not rebuilt after setting it |
| Consent OK but session never resumes | `GATEWAY_BASE_URL` wrong inside the container — compose must set `http://gateway:8080` (the config default `localhost:8080` is the agent itself) |
| Tool calls return `"status": "mock"` despite setting credentials | Container wasn't rebuilt after editing `.env.sandbox` (`env_file` is read at container start, not live-reloaded) — rerun `docker compose ... up -d --build ecommerce` |
| Tool calls raise instead of falling back to mock | `REQUIRE_LIVE_CREDENTIALS=true` is set and the integration you're calling genuinely isn't configured — this is the intended fail-closed behavior, not a bug |
| Facebook/Instagram publish fails with an image URL error | The image must be a **publicly reachable HTTPS URL** — local file paths are not supported |

## Security notes

- The callback exchanges the OAuth code for a token itself (the agent holds `SHOPIFY_OAUTH_CLIENT_SECRET`) — the token never transits the gateway or SuperAgent.
- The resume POST to the gateway carries `{agent_id, status}` only.
- Facebook/Instagram tokens are static, env-var only, single-account — there is no per-tenant token store for those two integrations (unlike Shopify's OAuth flow). Treat `.env.sandbox` as the trust boundary for those tokens.
