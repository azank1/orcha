"""
super_agent_example.py
Shows how to register the Lead Gen Agent as a tool in a super-agent.
Uses OpenRouter with Z.ai GLM (OpenAI-compatible API); delegates to the lead gen agent when appropriate.
"""
import asyncio
import json
import os

import certifi
import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

LEAD_GEN_AGENT_URL = os.getenv("LEAD_GEN_AGENT_URL", "http://localhost:8000")
LEAD_GEN_API_KEY = os.getenv("LEAD_GEN_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
SUPER_AGENT_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")


# ── A2A Tool definition for the super-agent (OpenAI / OpenRouter shape) ───────

_LEAD_FN = {
    "name": "lead_generation",
    "description": (
        "Use this when the user wants to find new sales leads, build prospect lists, "
        "discover potential customers, enrich contacts, or populate the CRM with new leads. "
        "Handles the full pipeline: search → score → enrich → CRM write."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language description of leads to find",
            },
            "max_leads": {
                "type": "integer",
                "description": "Maximum leads to find (default 10)",
                "default": 10,
            },
            "write_to_crm": {
                "type": "boolean",
                "description": "Whether to write results to HubSpot (default true)",
                "default": True,
            },
        },
        "required": ["query"],
    },
}

OPENAI_TOOLS = [{"type": "function", "function": _LEAD_FN}]


async def call_lead_gen_agent(query: str, max_leads: int = 10, write_to_crm: bool = True) -> dict:
    """Call the A2A lead gen agent server — credentials passed per-request."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{LEAD_GEN_AGENT_URL}/run",
            headers={"X-API-Key": LEAD_GEN_API_KEY, "Content-Type": "application/json"},
            json={
                "query": query,
                "max_leads": max_leads,
                "write_to_crm": write_to_crm,
                "credentials": {
                    "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
                    "LLM_PROVIDER": "openrouter",
                    "apollo_api_key": os.getenv("APOLLO_API_KEY"),
                    "hunter_api_key": os.getenv("HUNTER_API_KEY"),
                    "hubspot_api_key": os.getenv("HUBSPOT_API_KEY"),
                },
            },
        )
        resp.raise_for_status()
        return resp.json()


class SuperAgent:
    """
    Orchestrating super-agent that routes lead generation tasks
    to the A2A lead gen agent, and handles everything else itself.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=OPENROUTER_BASE_URL,
            http_client=httpx.AsyncClient(
                verify=certifi.where(), timeout=httpx.Timeout(120.0)
            ),
        )

    async def run(self, user_message: str) -> str:
        print(f"\nSuper-agent processing: '{user_message}'")
        system = (
            "You are a sales automation super-agent. "
            "When the user wants to find leads, prospect, or build contact lists, "
            "call the lead_generation function tool. "
            "For anything else, answer directly."
        )
        messages: list[dict] = [{"role": "user", "content": user_message}]

        for _ in range(5):
            resp = await self.client.chat.completions.create(
                model=SUPER_AGENT_MODEL,
                max_tokens=2048,
                temperature=0,
                messages=[{"role": "system", "content": system}, *messages],
                tools=OPENAI_TOOLS,
                tool_choice="auto",
            )
            choice = resp.choices[0]
            msg = choice.message

            assistant_msg: dict = {
                "role": "assistant",
                "content": msg.content,
            }
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_msg)

            if choice.finish_reason != "tool_calls" or not msg.tool_calls:
                return (msg.content or "").strip()

            tool_messages: list[dict] = []
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                print(f"  → Delegating to tool: {name}")

                if name == "lead_generation":
                    result = await call_lead_gen_agent(**args)
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })
                    print(
                        f"  ← Lead gen returned: {result.get('leads_qualified', 0)} qualified leads"
                    )
                else:
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": f"Unknown tool: {name}"}),
                    })

            messages.extend(tool_messages)

        return "Super-agent reached iteration limit."


# ── CLI demo ──────────────────────────────────────────────────────────────────

async def main():
    super_agent = SuperAgent()

    # Discover the lead gen agent (optional — just for logging)
    async with httpx.AsyncClient() as client:
        try:
            card = await client.get(f"{LEAD_GEN_AGENT_URL}/.well-known/agent-card")
            print(f"Discovered agent: {card.json().get('name')} v{card.json().get('version')}")
        except Exception:
            print(
                f"Note: Lead gen agent not reachable at {LEAD_GEN_AGENT_URL} "
                "— start it with: uvicorn main:app"
            )
            return

    queries = [
        "Find me 5 VP Engineering leads at SaaS companies in the US with under 200 employees",
        "I need fintech CTOs in London to contact this week, max 10 leads",
    ]

    for query in queries:
        result = await super_agent.run(query)
        print(f"\nResult:\n{result}\n{'─'*60}")


if __name__ == "__main__":
    asyncio.run(main())
