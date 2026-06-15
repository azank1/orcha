# Notion Research Agent - Quick Start Guide

## Get Started in 5 Minutes

### Prerequisites
- Docker installed
- OpenRouter API key (get from https://openrouter.ai/keys)
- Notion integration created (optional, for production use)

### Step 1: Configure Environment

```bash
cd /workspaces/metaorcha-emerge/mvp

# Edit .env file and add your keys:
nano .env

# Minimum required:
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional (for full functionality):
NOTION_API_KEY=secret_your_notion_key
GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your_secret
TAVILY_API_KEY=tvly-your_key
```

### Step 2: Start Services

```bash
# Start all MVP services including Notion agent
docker-compose up -d

# Wait for services to be healthy (~30 seconds)
docker-compose ps
```

### Step 3: Test the Agent

```bash
# Run test workflow
cd /workspaces/metaorcha-emerge/mvp/scripts
python3 test_notion_workflow.py
```

### Step 4: Try Natural Language Queries

```bash
# Start interactive CLI
python3 interactive_orchestrator.py

# Try queries like:
> Research Bitcoin and create a Notion page with current price
> Create a comprehensive market analysis for Ethereum with charts
> Track my portfolio: BTC, ETH, SOL with 7-day charts
```

---

## What Gets Created

When you run a Notion workflow, the agent:

1. **Searches the web** for relevant research (Tavily API)
2. **Fetches market data** (mock for MVP, CoinGecko planned)
3. **Creates a Notion page** with structured content
4. **Embeds TradingView charts** (if OAuth configured)

---

## Architecture

```
Notion Research Agent (FastMCP · SSE transport · port 3003)
├── Tools (7):
│   ├── create_note          → Notion page creation
│   ├── search               → Tavily + OpenRouter summarization
│   ├── market_data          → price/volume/indicators
│   ├── tradingview_chart    → TradingView embed in Notion
│   ├── orchestrate          → meta-tool (calls all above)
│   ├── authorize_oauth      → Google OAuth URL
│   └── oauth_exchange       → code → token exchange
│
├── Config (pydantic-settings):
│   └── All keys optional — starts in mock/dev mode
│
└── Transport:
    ├── SSE (default in Docker, port 3003)
    └── stdio (for local MCP clients)
```

---

## Local Development (without Docker)

```bash
cd agents/notion-research

# Install deps
pip install -e ".[dev]"

# Run with SSE transport
python -m src.server

# Or stdio for MCP client testing
fastmcp run src.server:mcp
```

---

## OAuth Setup (Optional)

To enable TradingView chart embedding:

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:3003/oauth/callback`
4. Set `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` in `.env`

Use the `authorize_oauth` and `oauth_exchange` MCP tools to complete the flow.

---

## Monitoring

```bash
# View agent logs
docker-compose logs -f notion-agent

# Check container health
docker-compose ps
```

---

## Troubleshooting

**Agent not starting**: Check `docker-compose logs notion-agent` for missing deps.

**Notion API errors**: Create integration at https://www.notion.so/my-integrations, share database with it.

**OAuth errors**: Verify credentials in `.env` and redirect URI in Google Console.

---

## Docs

- [MVP Guide](../../mvp/README.md)
- [Contributing](../../CONTRIBUTING.md)
- [Agent Tools](src/tools/)
