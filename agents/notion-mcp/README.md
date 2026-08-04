# Notion Agent MCP Server

An MCP (Model Context Protocol) server that provides tools, resources, and prompts for interacting with Notion workspaces. Built on the official `@modelcontextprotocol/sdk` and `@notionhq/client`.

## Features

### Tools (5)
| Tool | Description |
|------|-------------|
| `search_notion` | Search pages and databases in the workspace |
| `get_page` | Retrieve a page by ID with properties and optional content blocks |
| `create_page` | Create a new page under a parent page or database |
| `update_page` | Update properties of an existing page |
| `query_database` | Query a database with filters and sorts |

### Resources (2)
| Resource | URI Pattern | Description |
|----------|-------------|-------------|
| Page | `notion://pages/{pageId}` | Read page data by ID |
| Database | `notion://databases/{databaseId}` | Read database schema by ID |

### Prompts (2)
| Prompt | Description |
|--------|-------------|
| `research_topic` | Generate a research plan and create a structured Notion page |
| `meeting_notes` | Create structured meeting notes in Notion |

## Quick Start

### 1. Install
```bash
cd mvp/notion-agent-mcp
npm install
```

### 2. Configure
Set the `NOTION_API_KEY` environment variable:
```bash
export NOTION_API_KEY="ntn_your_integration_token"
```

Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations) and share target pages/databases with it.

### 3. Run
```bash
# Development (with tsx)
npm run dev

# Production (build first)
npm run build
npm start
```

The server runs over **stdio** transport — it reads JSON-RPC messages from stdin and writes to stdout, with logs going to stderr.

## Project Structure

```
notion-agent-mcp/
├── src/
│   ├── index.ts              ← Entry point (stdio transport)
│   ├── server.ts             ← MCP server setup (tools, resources, prompts)
│   ├── config.ts             ← Environment configuration
│   ├── types.ts              ← Shared type definitions
│   ├── notion/
│   │   └── client.ts         ← Notion API wrapper (@notionhq/client)
│   └── tools/
│       ├── search.ts         ← search_notion tool
│       ├── get-page.ts       ← get_page tool
│       ├── create-page.ts    ← create_page tool
│       ├── update-page.ts    ← update_page tool
│       └── query-database.ts ← query_database tool
├── tests/
│   └── unit/
│       ├── notion-client.test.ts  ← NotionClient tests (7 tests)
│       ├── tools.test.ts          ← Tool function tests (9 tests)
│       └── server.test.ts         ← Server creation tests (2 tests)
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

## Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Type check
npm run lint
```

**18 unit tests** covering:
- NotionClient: search, getPage, createPage, queryDatabase, getDatabase
- Tools: all 5 tools with mock client
- Server: creation and initialization

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_API_KEY` | Yes | Notion integration token |
| `NOTION_DATABASE_ID` | No | Default database ID |
| `LOG_LEVEL` | No | `debug`, `info`, `warn`, `error` (default: `info`) |

## MCP Client Configuration

To use with an MCP client (e.g., Claude Desktop), add to your config:

```json
{
  "mcpServers": {
    "notion": {
      "command": "node",
      "args": ["path/to/notion-agent-mcp/dist/index.js"],
      "env": {
        "NOTION_API_KEY": "ntn_your_token"
      }
    }
  }
}
```

## Tech Stack

- TypeScript 5.5
- `@modelcontextprotocol/sdk` — MCP protocol implementation
- `@notionhq/client` — Official Notion SDK
- `zod` — Schema validation for tool parameters
- `vitest` — Test framework
