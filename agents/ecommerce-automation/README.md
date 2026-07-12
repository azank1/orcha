# E-commerce Automation Agent

A2A agent for real e-commerce and social-media orchestration: Shopify store management, Facebook Page publishing, and Instagram Business publishing, all through one natural-language interface.

**Protocol:** A2A · **Port:** `3009` (local dev) / `8080` (Docker internal — matches the pattern used by all sandbox-deployed A2A agents; see `deploy/sandbox/docker-compose.sandbox.yml`).

## Skills

| Skill | What it does |
|---|---|
| `shopify_management` | Full CRUD for Shopify products — create, list, get, update, publish, unpublish, delete, bulk-delete |
| `social_publishing` | Publish posts/images to a Facebook Page and Instagram Business account |
| `store_analytics` | Read engagement metrics — likes, comments, Instagram media insights, post history |

See `emerge.yaml` for the full skill descriptions and example phrasings the orchestrator matches against.

## Modes: mock vs. live vs. production

This agent has three integrations (Shopify, Facebook, Instagram), each independently optional:

- **Unconfigured (default):** every tool call for that integration returns a clearly-labeled `{"status": "mock", ...}` payload instead of hitting a real API. This is intentional and safe — it's what makes the agent usable in the public sandbox and in local dev without any credentials.
- **Configured:** set the relevant credentials below and the tool calls hit the real Shopify Admin API / Meta Graph API.
- **`REQUIRE_LIVE_CREDENTIALS=true`:** for a real production deployment. Any integration that is *not* configured will **raise an error instead of silently returning mock data** — see `src/tools/_production_guard.py`. Use this so a misconfigured deployment fails loudly (at call time) rather than quietly serving fake data that could be mistaken for a real write.

## Configuration

Copy `.env.example` to `.env` and fill in what you need — every integration is independently optional.

### Shopify

| Var | Purpose |
|---|---|
| `SHOPIFY_STORE_URL` | e.g. `https://mystore.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | Admin API access token (static, simplest path) |
| `SHOPIFY_OAUTH_CLIENT_ID` / `SHOPIFY_OAUTH_CLIENT_SECRET` | Alternative: OAuth flow via `/auth/start` → `/auth/callback` (see `src/oauth_routes.py`) instead of a static token |

The `client_id` embedded in `emerge.yaml`'s `auth_strategies` is a Shopify Partner app identifier — public by OAuth design (unlike `client_secret`, it's not sensitive). If you deploy your own Shopify Partner app, replace it with your own app's `client_id`.

### Facebook / Instagram (Meta Graph API)

| Var | Purpose |
|---|---|
| `FB_ACCESS_TOKEN`, `FB_PAGE_ID` | Facebook Page publishing + analytics |
| `IG_ACCESS_TOKEN`, `IG_USER_ID` | Instagram Business publishing + insights (token is usually the same as `FB_ACCESS_TOKEN` for a linked account) |

Meta tokens are static — there's no OAuth flow wired up for Facebook/Instagram in this agent (only Shopify has one). Generate a long-lived Page/User access token via [Meta's Graph API Explorer](https://developers.facebook.com/tools/explorer/) or the Meta Business suite.

## Running it for real

1. Fill in `.env` with real credentials for whichever integrations you want live.
2. Start the agent: `uv run uvicorn src.a2a_server:app --host 0.0.0.0 --port 3009` (or via `./scripts/run-all.sh`, which starts the full fleet).
3. Optionally set `REQUIRE_LIVE_CREDENTIALS=true` if this is a real deployment and you want misconfiguration to fail loudly instead of silently mocking.
4. Send a goal through Orcha that names one of the skills above, e.g. *"List my active Shopify products"* or *"Post to my Facebook page: New arrivals just dropped"*.

## Known limitations

- Facebook/Instagram publishing requires a **publicly reachable HTTPS URL** for any image (`post_image` / `publish_media`) — local file paths won't work.
- Instagram publishing is a 3-step async process (create container → poll until ready → publish) and can take several seconds; see `src/tools/instagram.py`.
- There's no multi-tenant credential store for Facebook/Instagram (unlike Shopify's OAuth flow) — tokens are static, single-account, env-var only.
- **Chaining this agent with another A2A agent in one goal is not yet reliable** (e.g. "research a product, then list it on Shopify, then post to Instagram") — see the "Known non-determinism" section in `docs/dev_docs/ECOMMERCE-LIVE-TEST.md` for the two root causes (a tool-naming collision with an unconfigured system tool, and a PnD candidate-ranking gap). Single-skill goals against this agent work reliably; multi-step chains spanning two different A2A agents currently don't.
