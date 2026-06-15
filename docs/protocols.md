# Protocol support matrix

Orcha orchestrates agents that speak **different** protocols in the same run.
The planner routes each step to the right agent regardless of how that agent
talks; the execution pipeline speaks the protocol on your behalf.

## Supported today

| Protocol | Transport(s) | Shape | Good for |
|---|---|---|---|
| **MCP** (Model Context Protocol) | stdio, SSE | tool calls | stateless capabilities, tools, system primitives |
| **A2A** (Agent-to-Agent) | HTTP (JSON-RPC 2.0) | `message/send` → task | long-running tasks, clarification rounds, auth handoffs, payments |
| **ACP** | HTTP | task | agent-to-agent task delegation |

The `emerge` SDK serves **A2A** out of the box (`emerge run`), so the fastest
way to publish an agent is the [quickstart](quickstart.md).

## Why more than one protocol

MCP is a tool-call protocol — great for stateless capabilities, the wrong shape
for long-running tasks with clarification rounds, auth handoffs, or payment. A2A
covers that half. Real systems have both, so the runtime speaks both — and lets
you [bridge](bridges.md) the rest.

## Declaring your protocol

In `emerge.yaml`:

```yaml
protocol:
  type: "a2a"          # mcp | a2a | acp
  version: "1.0"
  transport:
    type: "http"        # sse | stdio | http
    endpoint: "http://localhost:8900"
```

See the [emerge.yaml reference](emerge-yaml.md) for the full manifest.

## Wanted: bridges

The protocols we'd most love contributed as bridges:

- **n8n** — webhook bridge (a great starter issue)
- **LangGraph** — orchestrate a LangGraph server as an agent
- **OpenAPI** — turn any OpenAPI service into an orchestratable agent

See [bridges.md](bridges.md) and open a **Bridge request** issue.
