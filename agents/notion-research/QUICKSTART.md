# Notion Research Agent - Quick Start Guide

> **Note:** This guide is for the standalone Notion Research agent. For the full Orcha platform, see the [5-minute quickstart](../../docs/quickstart.md) and [agents/CONTRIBUTING.md](../CONTRIBUTING.md).

## Get Started in 5 Minutes

### Prerequisites
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- OpenRouter API key (from https://openrouter.ai/keys)
- Notion integration (optional, for production use)

### Step 1: Configure Environment

From the monorepo root:

```bash
cp agents/notion-research/.env.example agents/notion-research/.env
# Edit and add at minimum:
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
# Optional: NOTION_API_KEY, GOOGLE_OAUTH_*, TAVILY_API_KEY
```

### Step 2: Start the Agent

With the Orcha stack running (see root [README.md](../../README.md) or `./scripts/run-all.sh`):

```bash
# From repo root — starts all HTTP agents including notion-research on :3006
make agents-dev
```

Or run this agent alone:

```bash
cd agents/notion-research
uv run uvicorn src.server:app --host 0.0.0.0 --port 3006 --reload
```

### Step 3: Register with Registry

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -F "emerge_yaml=@agents/notion-research/emerge.yaml"
```

Health check:

```bash
curl http://localhost:3006/health
```

### Step 4: OAuth (optional)

Use the `authorize_oauth` and `oauth_exchange` MCP tools to complete the Google OAuth flow. See [README.md](README.md) for endpoint details.
