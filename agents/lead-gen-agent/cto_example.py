"""
cto_example.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full end-to-end example:

  User types → "Find me 10 fintech CTOs to contact this week"
       ↓
  orcha orchestrator classifies intent → lead_generation
       ↓
  Calls lead gen A2A agent with platform keys + user's HubSpot token
       ↓
  Agent: searches Apollo → scores leads → finds emails → writes CRM
       ↓
  Returns structured result + prints a clean summary

Run this file directly to see the full flow:
  uv run python cto_example.py

Works without real API keys — uses mock data for Apollo/Hunter/HubSpot.
Only needs ANTHROPIC_API_KEY for the LLM reasoning step.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import asyncio
import json
import os
import time
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

# Your platform-level keys (never shown to users)
PLATFORM_KEYS = {
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "apollo_api_key":    os.getenv("APOLLO_API_KEY", ""),       # mock if missing
    "hunter_api_key":    os.getenv("HUNTER_API_KEY", ""),       # mock if missing
}

# Simulated user context (in real orcha this comes from your auth/session)
SIMULATED_USER = {
    "id": "user_sulleman_001",
    "name": "Sulleman",
    "hubspot_token": os.getenv("HUBSPOT_API_KEY", ""),          # mock if missing
    "plan": "pro",
}

# Lead gen agent location
LEAD_GEN_URL    = os.getenv("LEAD_GEN_AGENT_URL", "http://localhost:8001")
LEAD_GEN_APIKEY = os.getenv("AGENT_API_KEY", "")


# ── Simulated token store (replace with Redis/Postgres in production) ─────────

class InMemoryTokenStore:
    """
    Simulates what your orcha platform stores after a user
    completes HubSpot OAuth. In production this is Redis or Postgres.
    """
    def __init__(self):
        self._store = {}

    async def set(self, key: str, value):
        self._store[key] = value

    async def get(self, key: str):
        return self._store.get(key)


token_store = InMemoryTokenStore()


# ── Platform credential resolver ──────────────────────────────────────────────

async def resolve_credentials_for_user(user_id: str) -> dict:
    """
    Builds the credentials dict to pass to the lead gen agent.
    - Platform keys (Anthropic, Apollo, Hunter) come from your vault/env
    - HubSpot token comes from the user's stored OAuth token
    
    This is what makes it zero-friction for users — they never see a key.
    """
    hubspot_token = await token_store.get(f"hubspot:{user_id}")

    return {
        # Platform pays for these — user never sees them
        "anthropic_api_key": PLATFORM_KEYS["anthropic_api_key"],
        "apollo_api_key":    PLATFORM_KEYS["apollo_api_key"] or None,
        "hunter_api_key":    PLATFORM_KEYS["hunter_api_key"] or None,
        # User's own CRM token from OAuth — or None if not connected
        "hubspot_api_key":   hubspot_token or None,
    }


# ── Lead gen agent caller ─────────────────────────────────────────────────────

async def call_lead_gen_agent(
    query: str,
    user_id: str,
    icp_override: dict | None = None,
    max_leads: int = 10,
    write_to_crm: bool = True,
) -> dict:
    """
    Calls the A2A lead gen agent on behalf of a user.
    Automatically resolves and injects all credentials.
    """
    credentials = await resolve_credentials_for_user(user_id)

    payload = {
        "query": query,
        "max_leads": max_leads,
        "write_to_crm": write_to_crm,
        "credentials": credentials,
    }

    if icp_override:
        payload["icp"] = icp_override

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{LEAD_GEN_URL}/run",
            headers={
                "X-API-Key": LEAD_GEN_APIKEY,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


# ── orcha orchestrator (simplified) ───────────────────────────────────────

async def orcha_handle_message(user_message: str, user: dict) -> str:
    """
    Simulates what orcha does when it receives a user message.
    In your real orchestrator this is your LLM routing + tool dispatch loop.
    Here we hardcode intent detection for clarity.
    """
    print(f"\n{'━'*60}")
    print(f"  User ({user['name']}): {user_message}")
    print(f"{'━'*60}")

    # In real orcha your LLM classifies this — we simulate it
    intent = classify_intent(user_message)
    print(f"  → Intent detected: {intent}")

    if intent == "lead_generation":
        # Extract ICP hints from the message (LLM does this in real system)
        icp = extract_icp_from_message(user_message)
        print(f"  → ICP extracted: {json.dumps(icp, indent=4)}")
        print(f"  → Calling lead gen agent at {LEAD_GEN_URL}...\n")

        start = time.time()
        result = await call_lead_gen_agent(
            query=user_message,
            user_id=user["id"],
            icp_override=icp,
            max_leads=10,
            write_to_crm=True,
        )
        elapsed = round(time.time() - start, 1)

        return format_response(result, elapsed, user)

    else:
        return f"I can help with that! (intent: {intent} — not lead gen, handled by other agents)"


def classify_intent(message: str) -> str:
    """
    Simulates LLM intent classification.
    In real orcha, Claude reads the message and picks the right tool.
    """
    lead_gen_keywords = [
        "find", "leads", "prospects", "contacts", "cto", "ceo", "vp",
        "outreach", "contact", "list", "fintech", "saas", "b2b"
    ]
    message_lower = message.lower()
    if any(kw in message_lower for kw in lead_gen_keywords):
        return "lead_generation"
    return "general_chat"


def extract_icp_from_message(message: str) -> dict:
    """
    Simulates LLM extracting ICP filters from the user message.
    In real orcha, Claude does this via structured output.

    "Find me 10 fintech CTOs to contact this week"
     → roles: [CTO], industries: [FinTech], geo: [United States]
    """
    msg = message.lower()

    roles = []
    if "cto" in msg:               roles.append("CTO")
    if "ceo" in msg:               roles.append("CEO")
    if "vp engineering" in msg:    roles.append("VP Engineering")
    if "vp sales" in msg:          roles.append("VP Sales")
    if "head of" in msg:           roles.append("Head of Engineering")
    if not roles:
        roles = ["CTO", "VP Engineering", "Head of Engineering"]

    industries = []
    if "fintech" in msg:           industries.append("FinTech")
    if "saas" in msg:              industries.append("SaaS")
    if "ecommerce" in msg:         industries.append("E-commerce")
    if "healthcare" in msg:        industries.append("HealthTech")
    if not industries:
        industries = ["SaaS", "Technology"]

    geographies = []
    if "london" in msg or "uk" in msg:     geographies.append("United Kingdom")
    if "us" in msg or "america" in msg:    geographies.append("United States")
    if "europe" in msg:                    geographies.append("Europe")
    if not geographies:
        geographies = ["United States"]

    return {
        "target_roles": roles,
        "industries": industries,
        "geographies": geographies,
        "company_size_min": 50,
        "company_size_max": 500,
        "min_score": 70,
    }


def format_response(result: dict, elapsed: float, user: dict) -> str:
    """Format the agent result into a clean user-facing response."""
    lines = []
    lines.append(f"\n{'━'*60}")
    lines.append(f"  Lead Gen Complete  ({elapsed}s)")
    lines.append(f"{'━'*60}")
    lines.append(f"  Searched:    {result.get('leads_found', 0)} prospects")
    lines.append(f"  Qualified:   {result.get('leads_qualified', 0)} matched your ICP")
    lines.append(f"  CRM:         {result.get('leads_written_to_crm', 0)} written to HubSpot")
    lines.append(f"{'━'*60}")

    leads = result.get("leads", [])
    if leads:
        lines.append(f"\n  Top {min(len(leads), 5)} qualified leads:\n")
        for i, lead in enumerate(leads[:5], 1):
            score = lead.get("icp_score", 0)
            score_bar = "█" * (score // 10) + "░" * (10 - score // 10)
            lines.append(f"  {i}. {lead.get('full_name', 'Unknown')}")
            lines.append(f"     {lead.get('title', '')} @ {lead.get('company', '')}")
            lines.append(f"     {lead.get('email') or 'email not found'}")
            lines.append(f"     {lead.get('location', '')}")
            lines.append(f"     ICP score: {score}/100  [{score_bar}]")
            if lead.get("crm_result", {}).get("url"):
                lines.append(f"     HubSpot: {lead['crm_result']['url']}")
            lines.append("")

    lines.append(f"  Summary: {result.get('summary', '')}")
    lines.append(f"{'━'*60}\n")

    return "\n".join(lines)


# ── Main — simulates the full user journey ────────────────────────────────────

async def main():
    print("\n" + "═"*60)
    print("  orcha — Lead Gen Demo")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═"*60)

    # Simulate: user has already connected HubSpot via OAuth
    # In production this happens during onboarding — user clicks "Connect HubSpot"
    await token_store.set(
        f"hubspot:{SIMULATED_USER['id']}",
        SIMULATED_USER["hubspot_token"] or "mock_hubspot_token"
    )
    print(f"\n  User '{SIMULATED_USER['name']}' logged in")
    print(f"  HubSpot: connected")
    print(f"  Apollo/Hunter: platform keys (user never sees these)")

    # Check lead gen agent is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health = await client.get(f"{LEAD_GEN_URL}/health")
            apis = health.json().get("apis_configured", {})
            print(f"\n  Lead gen agent: online at {LEAD_GEN_URL}")
            print(f"  APIs configured: {apis}")
    except httpx.ConnectError:
        print(f"\n  ⚠  Lead gen agent not running at {LEAD_GEN_URL}")
        print(f"  Start it with: uv run uvicorn main:app --port 8001")
        print(f"\n  Running in OFFLINE MODE — showing what the flow would look like\n")
        demo_offline()
        return

    # ── THE ACTUAL USER QUERY ──────────────────────────────────────────────────
    user_message = "Find me 10 fintech CTOs to contact this week"

    response = await orcha_handle_message(user_message, SIMULATED_USER)
    print(response)

    # ── BONUS: try a second query with different ICP ───────────────────────────
    user_message_2 = "I need VP Engineering leads at SaaS companies in London, under 200 employees"
    response2 = await orcha_handle_message(user_message_2, SIMULATED_USER)
    print(response2)


def demo_offline():
    """Shows what the output looks like when agent isn't running."""
    mock_result = {
        "leads_found": 25,
        "leads_qualified": 8,
        "leads_written_to_crm": 8,
        "leads": [
            {
                "full_name": "Sarah Chen",
                "title": "CTO",
                "company": "PayStream",
                "email": "sarah.chen@paystream.io",
                "location": "San Francisco, US",
                "icp_score": 100,
                "crm_result": {"url": "https://app.hubspot.com/contacts/123"},
            },
            {
                "full_name": "James Okafor",
                "title": "CTO",
                "company": "LendFlow",
                "email": "j.okafor@lendflow.com",
                "location": "New York, US",
                "icp_score": 95,
                "crm_result": {"url": "https://app.hubspot.com/contacts/124"},
            },
            {
                "full_name": "Priya Nair",
                "title": "CTO",
                "company": "ClearPay",
                "email": "priya@clearpay.io",
                "location": "Austin, US",
                "icp_score": 90,
                "crm_result": {"url": "https://app.hubspot.com/contacts/125"},
            },
        ],
        "summary": "Found 8 fintech CTOs matching your ICP. All written to HubSpot.",
    }

    user = SIMULATED_USER
    print(f"\n  User ({user['name']}): Find me 10 fintech CTOs to contact this week")
    print(f"  → Intent detected: lead_generation")
    print(f"  → ICP extracted: roles=[CTO], industries=[FinTech], geo=[US]")
    print(f"  → Calling lead gen agent...\n")
    print(format_response(mock_result, elapsed=4.2, user=user))


if __name__ == "__main__":
    asyncio.run(main())
