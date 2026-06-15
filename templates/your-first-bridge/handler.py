"""your-first-bridge — a skeleton protocol handler for the Orcha runtime.

A *bridge* teaches the runtime to orchestrate agents that speak a protocol it
doesn't support yet (n8n webhooks, a LangGraph server, a plain OpenAPI service,
…). You implement one class that knows how to (a) call the remote agent and
(b) return its result as text. The runtime handles planning, routing, auth,
payments, and human-in-the-loop around you.

This file is a heavily-commented starting point. Copy it into
`services/superagent/src/superagent/handlers/`, rename it, fill in the TODOs,
and register it in the pipeline dispatch (see docs/bridges.md, "Wiring it in").
"""

from __future__ import annotations

import logging
from typing import Any

import httpx  # the runtime already depends on httpx
from langchain_core.runnables import RunnableConfig

from .base import AgentHandler  # ABC: gives you emit_event() + auth headers

logger = logging.getLogger(__name__)

# The protocol string your manifests declare (protocol.type in emerge.yaml).
# Keep it short and uppercase, e.g. "N8N", "LANGGRAPH", "OPENAPI".
PROTOCOL = "MYPROTO"


class MyProtoHandler(AgentHandler):
    """Bridge handler for ``protocol.type: myproto`` agents.

    The pipeline constructs this with resolved ``auth_headers`` (from the vault
    + auth cascade) and calls ``send_task``. Return a plain string — the
    OutputNormalizer turns it into the user-facing artifact.
    """

    async def send_task(
        self,
        agent_id: str,
        task: str,
        transport: dict[str, Any],
        state: dict[str, Any],
        config: RunnableConfig | None,
        call_id: str,
    ) -> str:
        """Call the remote agent and return its result as text.

        Args:
            agent_id:  the agent's DID (did:orcha:agent:*).
            task:      the natural-language instruction the planner routed here.
            transport: the manifest's ``protocol.transport`` block — your
                       endpoint/command/headers live here.
            state:     execution state (user_id, session_id, …) — read-only here.
            config:    LangChain config; pass to ``emit_event`` for streaming.
            call_id:   correlation id for logs/tracing.
        """
        endpoint = transport.get("endpoint")
        if not endpoint:
            return "Error: bridge transport has no endpoint"

        # Optional: stream a progress event to the UI.
        await self.emit_event(config, {"type": "progress", "content": f"Calling {agent_id}"})

        # TODO: shape the request the way YOUR protocol expects.
        payload = {"input": task}
        headers = {"Content-Type": "application/json", **self._auth_headers}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.exception("Bridge call failed | agent=%s call_id=%s", agent_id, call_id)
            return f"Error: bridge call failed: {exc}"

        # TODO: extract the human-readable result from YOUR protocol's response.
        return str(data.get("output", data))
