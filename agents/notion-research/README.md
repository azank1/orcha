# Notion Research Agent

FastMCP-based research agent with Notion, TradingView and web search integration.

## Tools (7)

| Tool | Description |
|------|-------------|
| `create_note` | Create structured research note in Notion |
| `search` | Web search via Tavily + LLM summarization |
| `market_data` | Fetch price/volume/indicators (mock for MVP) |
| `tradingview_chart` | Embed TradingView chart in Notion page |
| `orchestrate` | Full workflow: search → note → charts |
| `authorize_oauth` | Generate Google OAuth URL |
| `oauth_exchange` | Exchange OAuth code for tokens |

## Run

```bash
# SSE transport (default in Docker)
python -m src.server

# stdio transport (for local MCP clients)
fastmcp run src.server:mcp
```

## Config

All env vars optional — server starts in mock/dev mode without them.

| Var | Purpose |
|-----|---------|
| `NOTION_API_KEY` | Notion integration token |
| `OPENROUTER_API_KEY` | LLM for search summarization |
| `TAVILY_API_KEY` | Web search API |
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth for TradingView |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth secret |
| `ENCRYPTION_KEY` | Token encryption (base64) |

## Stack

- **FastMCP** 2.x — MCP protocol + SSE transport
- **notion-client** — Notion API
- **openai** — OpenRouter LLM client
- **aiohttp** — Tavily web search
- **google-auth-oauthlib** — OAuth flow