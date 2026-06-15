# Google Workspace Orchestrator (A2A)

Multi-step Google Workspace agent for MetaOrcha: **A2A JSON-RPC** on `POST /`, **workspace-mcp** over HTTP (`/mcp`), **Google ADK `LlmAgent` + `LiteLlm`** targeting **OpenRouter**, and **DAG** planning across **all** [workspace-mcp](https://github.com/taylorwilsdon/google_workspace_mcp) tool groups.

## Covered MCP services (12)

Each service maps to a **skill** / planner **domain** id used for tool filtering:

| Skill id | workspace-mcp area |
|----------|-------------------|
| `workspace_drive` | Drive |
| `workspace_gmail` | Gmail |
| `workspace_calendar` | Calendar |
| `workspace_docs` | Docs |
| `workspace_sheets` | Sheets |
| `workspace_slides` | Slides |
| `workspace_forms` | Forms |
| `workspace_tasks` | Tasks |
| `workspace_contacts` | Contacts (People API) |
| `workspace_chat` | Chat |
| `workspace_search` | Programmable Search (`search_custom`, …) |
| `workspace_apps_script` | Apps Script |
| `workspace_orchestrator` | Full DAG (all tools) |

Tool **names** are enumerated in [`src/agent_registry.py`](src/agent_registry.py) from the upstream README; if the MCP adds tools, **keyword fallback** narrows by name substring before falling back to the full tool list.

## Requirements

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) recommended
- `uvx` on `PATH` if `MCP_SPAWN_ENABLED=1` (to spawn `workspace-mcp`)
- Root or local `.env` with at least **`OPENROUTER_API_KEY`**

## Quick start

```bash
cd agents/google-workspace-orchestrator
cp .env.example .env
# edit .env — set OPENROUTER_API_KEY and Google vars as needed

uv sync
uv run uvicorn src.server:app --host 0.0.0.0 --port 3011
```

Default **`WORKSPACE_MCP_TOOL_TIER=complete`** so the subprocess loads the full tool surface (override with `core` / `extended` to reduce quota or exposure).

Smoke checks:

```bash
curl -s http://localhost:3011/health | jq .
curl -s http://localhost:3011/.well-known/agent.json | jq .schemaVersion
```

## OAuth (SuperAgent + gateway)

1. SuperAgent preflight reads `emerge.yaml` **oauth2** strategy for the invoked skill.
2. The chat UI runs the OAuth popup; Google redirects to the **gateway** at **`http://localhost:5500/auth/callback`** (configure the same URL under *Authorized redirect URIs* for the OAuth client in Google Cloud).
3. The gateway forwards the **authorization `code`** to this agent’s **`GET /auth/callback`**. Pass the same opaque **`state`** key used for vault/session correlation.
4. Prefer **`Authorization: Bearer …`** from SuperAgent when the platform already holds Google tokens.

Optional `params.metadata.oauth_state` (or `session_id`) selects the in-memory token bucket when no bearer header is sent.

## MCP subprocess

`uvx workspace-mcp --transport streamable-http --tool-tier <WORKSPACE_MCP_TOOL_TIER>`

The agent’s MCP client sends **`Accept: application/json, text/event-stream`** (required by streamable HTTP MCP); without it, `workspace-mcp` returns **406 Not Acceptable**.

Set `MCP_SPAWN_ENABLED=0` and `WORKSPACE_MCP_URL` to use an external server.

**Custom Search:** configure `GOOGLE_PSE_API_KEY` and `GOOGLE_PSE_ENGINE_ID` on the MCP process per upstream docs.

## emerge.yaml

Register with the MetaOrcha registry using [`emerge.yaml`](./emerge.yaml). Skill IDs must match `/.well-known/agent.json` and **`security.auth_strategies[0].capability_ids`**.

## Destructive actions (HITL)

Tools whose names match destructive substrings (e.g. send, delete, trash) return **`input-required`** until the user replies **approve** on a follow-up `message/send` with the same `taskId` (SuperAgent clarify flow).
