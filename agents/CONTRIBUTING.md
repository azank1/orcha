# Contributing an Agent

## Requirements

Every agent must:

1. Have an `emerge.yaml` at the root with a unique `did:metaorcha:agent:<name>` identity
2. Implement one of the supported protocols: **A2A** or **MCP**
3. Pass a basic smoke test (health check or tool invocation)
4. Include a `README.md` covering setup, environment variables, and usage

## Protocol Contracts

### A2A Agents

Minimum required endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | Agent card — name, skills, protocol version |
| `/tasks/send` | POST | Accept a task message, return result |
| `/health` | GET | Returns `{"status": "ok"}` |

Task payload:
```json
{
  "id": "task_abc123",
  "message": {
    "role": "user",
    "parts": [{ "type": "text", "text": "natural language task" }]
  }
}
```

Task response must include `status.state` — one of `completed`, `failed`, `input-required`.

### MCP Agents

Must implement `tools/list` and `tools/call` per the MCP spec (`2024-11-05` or later). Set `health_endpoint: null` in `emerge.yaml` for stdio transports.

## Directory Structure

```
agents/<your-agent>/
├── emerge.yaml          # Required — agent manifest
├── README.md            # Required — setup and usage
├── pyproject.toml       # Python agents
├── package.json         # Node.js agents
├── Dockerfile           # Required for production deployment
└── src/
    └── server.py / index.ts
```

## Adding a New Agent

1. Copy the closest existing agent as a template
2. Update `emerge.yaml` — set a unique `id`, bump version to `0.1.0`
3. Implement the protocol surface
4. Add a `Dockerfile` using the existing agents as reference
5. Add to `docker-compose.yml` in the repo root
6. Write a smoke test (curl or pytest)
7. Open a PR — include test output in the description

## Enhancing an Existing Agent

- Bump `version` in `emerge.yaml` on any capability change
- Add new skills to the `skills` list in `emerge.yaml` and in the agent card (`/.well-known/agent.json`)
- Do not break existing skill IDs — the registry and P&D index them
- Update the agent's `README.md` to reflect changes

## Standards

- No hardcoded secrets — use environment variables
- Log structured JSON with a `level` field (`info`, `warning`, `error`)
- A2A agents must return `status.state: "failed"` with a message on errors — not HTTP 500
- MCP agents must return a proper `content` array, even on errors
- Keep `emerge.yaml` in sync with what the agent actually exposes

## Testing

```bash
# A2A — health check
curl http://localhost:<port>/health

# A2A — agent card
curl http://localhost:<port>/.well-known/agent.json

# A2A — task invocation
curl -X POST http://localhost:<port>/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t1","message":{"role":"user","parts":[{"type":"text","text":"<task>"}]}}'
```

For MCP agents, use `mcp-inspector` or pipe JSON-RPC via stdin.
