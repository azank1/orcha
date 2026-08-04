# Lead Gen Agent — Production A2A Server

A fully autonomous B2B lead generation agent exposed as an A2A-compatible JSON-RPC server. Targets early-stage startup founders (CTO/CEO/Founder, < 10 employees) using Hunter.io for real contact discovery, with Gmail OAuth for outreach and human-in-the-loop email review before anything is sent.

## What it does

Given a natural language query like *"find 5 automation companies and send outreach"*, it autonomously:

1. Searches Hunter.io domain-search across a curated pool of early-stage automation startups
2. Filters to CTO / CEO / Founder titles only (word-boundary matched, no false positives)
3. Scores each lead against your ICP (0–100)
4. Pauses for human review of all email drafts before sending (**HITL interrupt**)
5. Authenticates Gmail via OAuth if not already connected (**OAuth interrupt**, auto-resumes)
6. Sends approved emails via Gmail API and returns a structured summary

---

## Architecture

```
lead-gen-agent/
├── main.py                        # FastAPI A2A JSON-RPC server (port 4567)
├── agent_card.json                # A2A discovery manifest
├── core/
│   ├── agent.py                   # LLM agentic loop + HITL callbacks
│   ├── llm_provider.py            # OpenRouter / OpenAI / Anthropic adapter
│   └── context.py                 # Per-request API key context (contextvars)
├── tools/
│   ├── hunter_tool.py             # PRIMARY: prospect search + email finder
│   ├── apollo_tool.py             # FALLBACK: mock data when Hunter unavailable
│   ├── search_router.py           # Routes global → Hunter, local → Google Maps
│   ├── google_maps_tool.py        # Local business search
│   ├── hubspot_tool.py            # CRM writer (HubSpot)
│   ├── score_tool.py              # ICP scoring (no external calls)
│   ├── sendgrid_tool.py           # Email via SendGrid (alternative to Gmail)
│   └── email_preview_tool.py      # Build draft previews before send
├── integrations/
│   ├── gmail_oauth.py             # Gmail OAuth2 flow + token store + send API
│   └── hubspot_oauth.py           # HubSpot OAuth flow
└── .env.example                   # Copy to .env and fill in keys
```

---

## Quick start

### 1. Install

```bash
cd agents/lead-gen-agent
uv sync          # or: pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Key variables (set these — everything else is optional):

| Variable | Where to get it |
|----------|----------------|
| `HUNTER_API_KEY` | hunter.io → Dashboard → API |
| `OPENROUTER_API_KEY` | openrouter.ai |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → OAuth 2.0 Credentials |
| `GOOGLE_CLIENT_SECRET` | same as above |
| `GMAIL_REDIRECT_URI` | set to `http://localhost:4567/oauth/gmail/callback` |

> **Note:** Do not put inline comments on the same line as API key values in `.env` — they will be included in the key string and cause 401 errors.

### 3. Run

```bash
uv run python main.py
# Server starts at http://localhost:4567
```

### 4. Pre-auth Gmail (recommended — do this once before running tasks)

```bash
# Get auth URL
curl "http://localhost:4567/oauth/gmail/connect?tenant_id=mycompany"
# Open the returned auth_url in your browser and approve
# Server logs: "Gmail OAuth complete: tenant=mycompany"
```

---

## Running the agent

### Full pipeline — find leads + send outreach

```bash
curl -X POST http://localhost:4567/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "method": "message/send", "id": "1",
    "params": {"message": {"parts": [
      {"kind": "text", "text": "find 5 automation companies and send outreach"},
      {"kind": "data", "data": {
        "max_leads": 5,
        "write_to_crm": true,
        "send_outreach_email": true,
        "tenant_id": "mycompany"
      }}
    ]}}
  }'
# Returns: {"result": {"id": "<task_id>", "status": {"state": "submitted"}}}
```

### Poll task status

```bash
curl -X POST http://localhost:4567/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tasks/get", "id": "2", "params": {"id": "<task_id>"}}'
```

States: `submitted` → `working` → `input-required` → `completed` / `failed`

### Resume after HITL interrupt (email approval)

When state is `input-required` with `interrupt_type: approval`, the `metadata.drafts` array contains all email drafts for review. Resume with:

```bash
# Approve all drafts as-is
curl -X POST http://localhost:4567/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "method": "message/send", "id": "3",
    "params": {"message": {
      "taskId": "<task_id>",
      "parts": [
        {"kind": "text", "text": "approved"},
        {"kind": "data", "data": {"approved": true, "edits": {}}}
      ]
    }}
  }'
```

> **Important:** `taskId` must be inside the `message` object, not at the `params` level.

### Gmail OAuth interrupt (mid-task)

When state is `input-required` with `interrupt_type: oauth_required`, open `metadata.auth_url` in your browser. The callback URL (`/oauth/gmail/callback`) embeds the task ID in the OAuth `state` param — the agent **auto-resumes** once you approve. No manual resume message needed.

---

## Superagent integration

This agent is designed to run as a **sub-agent** inside the Orcha superagent. The superagent delegates lead generation tasks here via A2A JSON-RPC and handles the HITL interrupts transparently in the UI.

### How it fits

```
User (Chat UI)
      ↓  "find automation founders and send outreach"
Superagent (services/superagent)
      ↓  POST http://lead-gen-agent:4567/  (message/send)
Lead Gen Agent
      ↓  searches Hunter → scores → builds drafts
      ↑  state: input-required (interrupt_type: approval)
Superagent
      ↑  surfaces drafts to user in Chat UI
User approves / edits
      ↓  Superagent sends resume message (taskId inside message)
Lead Gen Agent
      ↓  sends emails via Gmail → state: completed
Superagent
      ↑  shows summary to user
```

### Registering in the registry

The agent self-describes via its A2A agent card at `GET /.well-known/agent.json`. The registry picks this up automatically when seeded:

```bash
# From repo root
python services/registry/scripts/seed_agents.py
```

Or add it manually in `services/registry/tests/fixtures/a2a_lead_gen.yaml`.

### Environment variable the superagent needs

```bash
LEAD_GEN_AGENT_URL=http://localhost:4567   # or deployed URL
```

### Interrupt handling in the superagent

The superagent polls `tasks/get` and checks `status.state`:

- `input-required` + `interrupt_type: approval` → render draft review UI, send resume with `approved: true` and optional `edited_drafts`
- `input-required` + `interrupt_type: oauth_required` → open `metadata.auth_url` in a modal; task auto-resumes after OAuth — no resume message needed
- `input-required` + `interrupt_type: hubspot_auth` → prompt user for HubSpot PAT, send resume with `hubspot_token`

See `services/superagent/src/superagent/handlers/a2a_handler.py` for the full interrupt dispatch logic.

---

## HITL interrupt flow

```
User sends task
      ↓
Agent searches Hunter → scores leads → builds email drafts
      ↓
Task pauses → state: input-required (interrupt_type: approval)
      ↓
User reviews drafts in metadata.drafts[]
      ↓
User sends resume message with approved: true (or edited_drafts)
      ↓
Agent sends emails via Gmail API → task: completed
```

---

## ICP scoring

| Signal | Points |
|--------|--------|
| Role match (CTO/CEO/Founder) | 40 |
| Industry match | 25 |
| Company size in range | 20 |
| Verified email | 15 |
| **Total** | **100** |

Default minimum score to qualify: **70/100**.

---

## Target persona

The agent is tuned to target early-stage founders:

- **Titles:** CTO, CEO, Founder, Co-Founder only
- **Company size:** < 10 employees (pre-seed / seed)
- **Why:** founders at tiny teams are the decision-maker, budget-holder, and technical evaluator in one person — highest conversion rate for automation tooling

Hunter's `domain-search` endpoint returns real crawled emails from a curated pool of automation startup domains. Company size is controlled by the domain curation list in `hunter_tool.py` (`_AUTOMATION_DOMAINS`), not a runtime filter (Hunter doesn't return headcount).

---

## Adding more target companies

Edit `_AUTOMATION_DOMAINS` in `tools/hunter_tool.py`:

```python
_AUTOMATION_DOMAINS = [
    "activepieces.com", "trigger.dev", "windmill.dev", ...
    "your-new-startup.com",   # add here
]
```

Hunter will crawl the domain and return any publicly-indexed professional emails.

---

## Gmail OAuth — how it works

Two flows are supported:

**Flow A — Pre-auth (recommended):**
```
GET /oauth/gmail/connect?tenant_id=<id>
→ returns auth_url
→ user opens in browser, approves
→ GET /oauth/gmail/callback stores token
```

**Flow B — Mid-task interrupt:**
```
Agent needs Gmail but token missing
→ task pauses with interrupt_type: oauth_required
→ auth_url in metadata embeds task_id in OAuth state param
→ user approves in browser
→ /oauth/gmail/callback stores token AND auto-resumes the paused task
→ super-agent only needs to keep polling tasks/get
```

Check connection status:
```bash
curl "http://localhost:4567/oauth/gmail/status?tenant_id=mycompany"
```

---

## Deployment

### Docker

```bash
docker build -t lead-gen-agent .
docker run -p 4567:4567 --env-file .env lead-gen-agent
```

### Railway

```bash
railway login && railway up
# Set env vars in Railway dashboard → Variables
```

---

## Health check

```bash
curl http://localhost:4567/health
```

Returns active task count, LLM provider, and which API keys are configured.

---

## Known limitations

- **Hunter free plan:** 25 domain searches/month — upgrade for production volume
- **Apollo fallback:** `people/search` requires a paid Apollo plan with API access; the agent falls back to mock data if the key lacks permissions
- **Company size filter:** Hunter does not return headcount — company size targeting is done via domain curation, not a runtime filter
- **Gmail scope:** only `gmail.send` is requested — the agent cannot read your inbox
