# your-first-bridge

A skeleton for adding a **protocol bridge** to the Orcha runtime so it can
orchestrate agents that speak something we don't support out of the box.

This is the contribution we most want — read
[`docs/bridges.md`](../../docs/bridges.md) for the full walkthrough.

## Files

- `handler.py` — a heavily-commented `AgentHandler` subclass. Implement
  `send_task()`: call the remote agent, return its result as text.

## The 4 steps

1. Copy `handler.py` into
   `services/superagent/src/superagent/handlers/<yourproto>_handler.py`.
2. Implement the request/response mapping for your protocol.
3. Register it in the pipeline dispatch
   (`services/superagent/src/superagent/middleware/pipeline.py`, `_dispatch`).
4. Add a registry adapter so manifests with `protocol.type: <yourproto>` can be
   registered, and ship an example agent + `emerge.yaml`.

Open a **Bridge request** issue first if you want feedback on the design.
