"""
metaorcha_integration.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shows exactly how metaorcha integrates the lead gen A2A agent
at runtime — with credentials resolved per-request, per-user.

Drop this file into your metaorcha orchestrator and call
`register_lead_gen_agent(app, agent)` at startup.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import json
import logging
import os
import httpx
from typing import Any

logger = logging.getLogger("metaorcha.lead_gen")


# ── 1. Tool schema — tells your orchestrator LLM when to call this ─────────────

LEAD_GEN_TOOL_SCHEMA = {
    "name": "lead_generation",
    "description": (
        "Use when user wants to find leads, build prospect lists, discover "
        "potential customers, enrich contacts, or populate CRM with new leads. "
        "Handles full pipeline: search → score → enrich → CRM write."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language description of leads to find",
            },
            "max_leads": {
                "type": "integer",
                "default": 10,
                "description": "Max leads to return",
            },
            "write_to_crm": {
                "type": "boolean",
                "default": True,
                "description": "Write qualified leads to HubSpot",
            },
            "icp": {
                "type": "object",
                "description": "Optional ICP override",
                "properties": {
                    "target_roles":     {"type": "array", "items": {"type": "string"}},
                    "industries":       {"type": "array", "items": {"type": "string"}},
                    "geographies":      {"type": "array", "items": {"type": "string"}},
                    "company_size_min": {"type": "integer"},
                    "company_size_max": {"type": "integer"},
                    "min_score":        {"type": "integer"},
                },
            },
        },
        "required": ["query"],
    },
}


# ── 2. Runtime credential resolver ────────────────────────────────────────────

class LeadGenCredentialResolver:
    """
    Resolves credentials at runtime per-user per-request.

    Platform keys (Anthropic/OpenAI/Grok, Apollo, Hunter) come from
    your metaorcha environment — users never see them.

    User keys (HubSpot) come from your token store — set once by user
    in settings, reused automatically on every request.
    """

    def __init__(self, token_store):
        """
        token_store: anything with async get(key) / set(key, value)
        e.g. Redis, Postgres, or the InMemoryStore from key_manager.py
        """
        self.store = token_store

    async def resolve(self, user_id: str) -> dict:
        """
        Build full credentials dict for a lead gen request.
        Called automatically before every agent invocation.
        """
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

        # LLM key — only send the one that matches the active provider
        llm_keys = {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY") if provider == "anthropic" else None,
            "openai_api_key":    os.getenv("OPENAI_API_KEY")    if provider == "openai"    else None,
            "grok_api_key":      os.getenv("GROK_API_KEY")      if provider == "grok"      else None,
        }

        # User's HubSpot token (stored after they paste PAT in settings)
        hubspot_token = await self.store.get(f"hubspot:{user_id}")

        return {
            **llm_keys,
            "apollo_api_key":  os.getenv("APOLLO_API_KEY")  or None,
            "hunter_api_key":  os.getenv("HUNTER_API_KEY")  or None,
            "hubspot_api_key": hubspot_token or None,
        }

    async def is_ready(self, user_id: str) -> tuple[bool, list[str]]:
        """
        Check if user can run lead gen. Returns (ready, missing_list).
        Call this before invoking the agent to give user a clear error.
        """
        missing = []
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        key_map  = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai":    "OPENAI_API_KEY",
            "grok":      "GROK_API_KEY",
        }
        llm_key_name = key_map.get(provider, "ANTHROPIC_API_KEY")
        if not os.getenv(llm_key_name):
            missing.append(f"{llm_key_name} (platform — set in metaorcha env)")
        hubspot = await self.store.get(f"hubspot:{user_id}")
        if not hubspot:
            missing.append("HubSpot token (user → Settings → Integrations → paste PAT)")
        return len(missing) == 0, missing


# ── 3. A2A caller ─────────────────────────────────────────────────────────────

class LeadGenAgentCaller:
    """
    Calls the lead gen A2A server on behalf of a user.
    Handles credential injection, timeout, and error surfacing.
    """

    def __init__(self, resolver: LeadGenCredentialResolver):
        self.resolver   = resolver
        self.url        = os.getenv("LEAD_GEN_AGENT_URL", "http://localhost:8001")
        self.api_key    = os.getenv("LEAD_GEN_API_KEY", "")
        self.timeout    = 120.0

    async def run(self, user_id: str, tool_input: dict) -> dict:
        """
        Main entry point called by metaorcha tool dispatcher.

        user_id:    from your auth session
        tool_input: {query, max_leads, write_to_crm, icp} from LLM tool call
        """
        # Check user is ready
        ready, missing = await self.resolver.is_ready(user_id)
        if not ready:
            return {
                "status":  "error",
                "error":   "missing_credentials",
                "missing": missing,
                "message": f"Cannot run lead gen — missing: {', '.join(missing)}",
            }

        # Resolve credentials at runtime
        credentials = await self.resolver.resolve(user_id)

        payload = {
            "query":        tool_input["query"],
            "max_leads":    tool_input.get("max_leads", 10),
            "write_to_crm": tool_input.get("write_to_crm", True),
            "credentials":  credentials,
        }
        if "icp" in tool_input:
            payload["icp"] = tool_input["icp"]

        logger.info(
            f"Calling lead gen agent for user={user_id} "
            f"query='{tool_input['query']}' "
            f"provider={os.getenv('LLM_PROVIDER','anthropic')}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.url}/run",
                headers={
                    "X-API-Key":    self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()

        logger.info(
            f"Lead gen done for user={user_id}: "
            f"{result.get('leads_qualified',0)} qualified | "
            f"{result.get('leads_written_to_crm',0)} to CRM | "
            f"{result.get('execution_time_ms',0)}ms"
        )
        return result

    async def discover(self) -> dict:
        """Fetch the agent card — useful at startup to confirm agent is reachable."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.url}/.well-known/agent-card")
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> dict:
        """Check agent health."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.url}/health")
            resp.raise_for_status()
            return resp.json()


# ── 4. Registration — call this in your metaorcha startup ─────────────────────

def register_lead_gen_agent(app, orchestrator_agent, token_store):
    """
    Register the lead gen agent into metaorcha at startup.

    app:                your FastAPI app
    orchestrator_agent: your main metaorcha LLM agent object
    token_store:        your Redis/Postgres/memory store

    After calling this:
    - LEAD_GEN_TOOL_SCHEMA is added to orchestrator's tools
    - POST /tools/lead-gen/run is available for direct calls
    - GET  /tools/lead-gen/health shows agent status
    """
    resolver = LeadGenCredentialResolver(token_store)
    caller   = LeadGenAgentCaller(resolver)

    # Add tool schema to orchestrator so LLM knows when to call it
    orchestrator_agent.register_tool(
        schema   = LEAD_GEN_TOOL_SCHEMA,
        executor = lambda user_id, tool_input: caller.run(user_id, tool_input),
    )

    # Optional direct HTTP endpoints on metaorcha
    from fastapi import Request, HTTPException
    from pydantic import BaseModel

    class LeadGenRequest(BaseModel):
        query:        str
        max_leads:    int  = 10
        write_to_crm: bool = True
        icp:          dict | None = None

    @app.post("/tools/lead-gen/run")
    async def run_lead_gen(body: LeadGenRequest, request: Request):
        user_id = request.state.user_id  # from your auth middleware
        result  = await caller.run(user_id, body.model_dump())
        if result.get("status") == "error":
            raise HTTPException(400, detail=result)
        return result

    @app.get("/tools/lead-gen/health")
    async def lead_gen_health():
        try:
            return await caller.health()
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    @app.get("/tools/lead-gen/discover")
    async def lead_gen_discover():
        return await caller.discover()

    logger.info(f"Lead gen agent registered at {caller.url}")
    return caller


# ── 5. Tool dispatcher — add this case to your existing dispatcher ─────────────

async def dispatch_tool(tool_name: str, tool_input: dict, user_id: str, caller: LeadGenAgentCaller) -> Any:
    """
    Add this case to your existing metaorcha tool dispatcher.
    The rest of your tools stay exactly as they are.
    """
    if tool_name == "lead_generation":
        return await caller.run(user_id, tool_input)

    # ... your other tools unchanged below ...
    # elif tool_name == "calendar": ...
    # elif tool_name == "analytics": ...

    raise ValueError(f"Unknown tool: {tool_name}")


# ── 6. Minimal working example — paste into your metaorcha main.py ────────────

"""
# In your metaorcha main.py:

from metaorcha_integration import register_lead_gen_agent, LeadGenCredentialResolver
from your_token_store import token_store   # Redis, Postgres, etc.

# At startup — register once
@app.on_event("startup")
async def startup():
    register_lead_gen_agent(app, orchestrator, token_store)

# In your tool dispatcher — add one case
async def handle_tool_call(tool_name, tool_input, user_id):
    if tool_name == "lead_generation":
        resolver = LeadGenCredentialResolver(token_store)
        caller   = LeadGenAgentCaller(resolver)
        return await caller.run(user_id, tool_input)
    # ... rest of your tools

# In your settings route — store user's HubSpot PAT
@app.post("/settings/hubspot-token")
async def save_hubspot_token(token: str, request: Request):
    user_id = request.state.user_id
    await token_store.set(f"hubspot:{user_id}", token)
    return {"status": "connected"}

# Runtime credentials flow:
# 1. metaorcha env holds: ANTHROPIC_API_KEY, APOLLO_API_KEY, HUNTER_API_KEY
# 2. User pastes HubSpot PAT once → stored in token_store
# 3. Every request: resolver.resolve(user_id) assembles credentials
# 4. Credentials passed in POST /run body → context var inside agent
# 5. Agent executes → result back to metaorcha → back to user
"""
