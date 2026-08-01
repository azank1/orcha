# Writing a bridge

A **bridge** teaches the Orcha runtime to orchestrate agents that speak a
protocol it doesn't support yet — an n8n webhook, a LangGraph server, a plain
OpenAPI service. This is the highest-leverage contribution to the project: one
good bridge unlocks a whole ecosystem of existing agents.

The runtime already handles planning, routing, credential vault + auth cascade,
output normalization, human-in-the-loop interrupts, and payments. A bridge only
has to answer one question: **given a task and a transport, how do I call the
remote agent and get text back?**

## The contract

Every protocol handler subclasses `AgentHandler`
(`services/superagent/src/superagent/handlers/base.py`) and is invoked by the
execution pipeline. The minimal shape:

```python
from .base import AgentHandler

class MyProtoHandler(AgentHandler):
    async def send_task(self, agent_id, task, transport, state, config, call_id) -> str:
        # call the remote agent using `transport` (endpoint/auth) + self._auth_headers
        # return the result as a plain string
        ...
```

- `self._auth_headers` is already resolved from the vault + auth cascade.
- `transport` is the manifest's `protocol.transport` block.
- Return a **string**; the OutputNormalizer turns it into the user-facing
  artifact. Prefix hard errors with `Error:` so the pipeline marks the step
  failed.
- Use `await self.emit_event(config, {...})` to stream progress to the UI.

Start from [`templates/your-first-bridge/handler.py`](../templates/your-first-bridge/handler.py).

## Wiring it in

The pipeline dispatches on the manifest's `protocol.type`. Add your handler to
`_dispatch` in
`services/superagent/src/superagent/middleware/pipeline.py`:

```python
if protocol == "MYPROTO":
    from ..handlers.myproto_handler import MyProtoHandler
    handler = MyProtoHandler(auth_headers=auth_headers)
    return await handler.send_task(
        agent_id=agent_id, task=args.get("task", str(args)),
        transport=transport, state=self._state, config=config, call_id=call_id,
    )
```

Then make the registry accept manifests with `protocol.type: myproto` (add an
adapter that harvests capabilities the way your protocol advertises them), and
ship an example agent with its `emerge.yaml`.

## Human-in-the-loop, auth, and payments come for free

- **Clarifications:** raise/return the runtime's input-required signal and the
  pipeline surfaces a clarification modal — see how `A2AHandler` handles
  `input-required`.
- **Auth:** declare `auth_strategies` in the manifest; the cascade resolves
  credentials into `self._auth_headers` before your handler runs.
- **Payments:** set `payment.base_fee` in the manifest; mock mode meters it with
  no wallet.

## Checklist for a bridge PR

- [ ] Handler subclasses `AgentHandler`, returns text, fails with `Error:`.
- [ ] Registered in pipeline `_dispatch`.
- [ ] Registry adapter for `protocol.type: <yourproto>`.
- [ ] Example agent + `emerge.yaml` + a test.
- [ ] A short note in [`protocols.md`](protocols.md).

Open a **Bridge request** issue first to align on the design.

---

## Wanted bridges

These are confirmed gaps — implement any of them and the PR is very likely to merge. Each row links to a tracking issue with the `good first issue` and `bridge` labels.

| Protocol | Difficulty | Why it matters |
|----------|-----------|----------------|
| **Computer-use** | ⭐ Easy (backend adapter) | Reference bridge — already ships as open interface. Swap `MockComputerUseBackend` for a real screenshot/action provider via `COMPUTER_USE_BACKEND` env var. See `handlers/computer_use_handler.py`. |
| **OpenAPI / Swagger** | ⭐ Easy | Turns any documented REST API into an Orcha agent — the largest surface area of any bridge |
| **n8n webhooks** | ⭐ Easy | Connects the no-code automation ecosystem; n8n users can expose their workflows as agents |
| **LangChain** | ⭐⭐ Medium | Largest agent framework by adoption; a bridge makes Orcha the orchestration layer for LangChain agents |
| **Slack events** | ⭐⭐ Medium | Human-in-the-loop via Slack; surfaces clarification modals as Slack messages |
| **gRPC** | ⭐⭐⭐ Hard | Covers internal service mesh agents; protobuf schema drives capability extraction |
| **WebSocket (streaming)** | ⭐⭐⭐ Hard | Real-time agent outputs; streaming protocol through the existing output normalizer |

**Branch naming:** `feat/bridge-<protocol-slug>` (e.g., `feat/bridge-openapi`, `feat/bridge-n8n`, `feat/bridge-langchain`)
