"""
cto_example_with_pat.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Same CTO example but now using KeyManager for credential handling.

Shows the full user journey:
  1. User signs up
  2. Pastes HubSpot PAT once in settings
  3. Types "Find me 10 fintech CTOs to contact this week"
  4. Everything runs automatically — user never touches a key again

Run:
  uv run python cto_example_with_pat.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import asyncio
import os
import time
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

from onboarding.key_manager import KeyManager

# ── Setup ─────────────────────────────────────────────────────────────────────

LEAD_GEN_URL    = os.getenv("LEAD_GEN_AGENT_URL", "http://localhost:8001")
LEAD_GEN_APIKEY = os.getenv("AGENT_API_KEY", "")

key_manager = KeyManager()  # uses InMemoryStore — swap for Redis/Postgres in prod


# ── Simulated orcha orchestrator ─────────────────────────────────────────

async def orcha_handle_message(user_message: str, user_id: str, user_name: str):
    print(f"\n{'━'*60}")
    print(f"  {user_name}: {user_message}")
    print(f"{'━'*60}")

    # Check user is ready before calling agent
    ready, missing = await key_manager.has_required_keys(user_id)
    if not ready:
        print(f"  ✗ Cannot run — missing: {missing}")
        print(f"    → Tell user to connect their integrations in Settings")
        return

    # Resolve credentials automatically — user does nothing
    credentials = await key_manager.resolve(user_id)

    connected = await key_manager.list_connected_services(user_id)
    print(f"  → User integrations: {connected}")
    print(f"  → Platform keys: apollo, hunter, anthropic (silent)")
    print(f"  → Calling lead gen agent...\n")

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{LEAD_GEN_URL}/run",
                headers={"X-API-Key": LEAD_GEN_APIKEY},
                json={
                    "query": user_message,
                    "max_leads": 10,
                    "write_to_crm": True,
                    "credentials": credentials,
                    "icp": {
                        "target_roles": ["CTO", "VP Engineering"],
                        "industries": ["FinTech"],
                        "geographies": ["United States"],
                        "company_size_min": 50,
                        "company_size_max": 500,
                        "min_score": 70,
                    },
                },
            )
            resp.raise_for_status()
            result = resp.json()
            elapsed = round(time.time() - start, 1)
            print_result(result, elapsed)

    except httpx.ConnectError:
        print(f"  ⚠  Agent not running — start with: uv run uvicorn main:app --port 8001")
        print_mock_result()


def print_result(result: dict, elapsed: float):
    print(f"  Lead Gen Complete ({elapsed}s)")
    print(f"  {'─'*50}")
    print(f"  Searched  : {result.get('leads_found', 0)} prospects")
    print(f"  Qualified : {result.get('leads_qualified', 0)} matched ICP")
    print(f"  CRM       : {result.get('leads_written_to_crm', 0)} → HubSpot")
    print(f"  {'─'*50}")

    for i, lead in enumerate(result.get("leads", [])[:5], 1):
        score = lead.get("icp_score", 0)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        print(f"  {i}. {lead.get('full_name')}  —  {lead.get('title')} @ {lead.get('company')}")
        print(f"     {lead.get('email') or 'no email'}")
        print(f"     Score: {score}/100  [{bar}]")
        if lead.get("crm_result", {}).get("url"):
            print(f"     HubSpot → {lead['crm_result']['url']}")
        print()

    print(f"  {result.get('summary', '')}")


def print_mock_result():
    print_result({
        "leads_found": 25,
        "leads_qualified": 8,
        "leads_written_to_crm": 8,
        "leads": [
            {"full_name": "Sarah Chen",  "title": "CTO", "company": "PayStream",
             "email": "sarah.chen@paystream.io", "icp_score": 100,
             "crm_result": {"url": "https://app.hubspot.com/contacts/123"}},
            {"full_name": "James Okafor","title": "CTO", "company": "LendFlow",
             "email": "j.okafor@lendflow.com",   "icp_score": 95,
             "crm_result": {"url": "https://app.hubspot.com/contacts/124"}},
            {"full_name": "Priya Nair",  "title": "CTO", "company": "ClearPay",
             "email": "priya@clearpay.io",         "icp_score": 90,
             "crm_result": {"url": "https://app.hubspot.com/contacts/125"}},
        ],
        "summary": "Found 8 fintech CTOs matching your ICP. All written to HubSpot.",
    }, elapsed=4.2)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n" + "═"*60)
    print("  orcha — PAT credential flow demo")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═"*60)

    user_id   = "user_sulleman_001"
    user_name = "Sulleman"

    # ── Step 1: User signs up — no keys asked ─────────────────────────────────
    print(f"\n  Step 1: {user_name} signs up to orcha")
    print(f"  No API keys asked at signup.")

    # ── Step 2: Settings page — paste HubSpot PAT once ───────────────────────
    print(f"\n  Step 2: Settings → Integrations")
    print(f"  User pastes HubSpot Private App token once...")

    hubspot_pat = os.getenv("HUBSPOT_API_KEY") or "pat-na1-mock-token-for-demo"
    await key_manager.store_user_key(user_id, "hubspot", hubspot_pat)

    connected = await key_manager.list_connected_services(user_id)
    print(f"  Connected: {connected}")
    print(f"  Platform (silent): apollo, hunter, anthropic")
    print(f"  ✓ Setup complete — user is ready")

    # ── Step 3: User just types naturally ────────────────────────────────────
    print(f"\n  Step 3: User sends a message in orcha chat")

    await orcha_handle_message(
        "Find me 10 fintech CTOs to contact this week",
        user_id,
        user_name,
    )

    # ── Step 4: Show what happens without HubSpot connected ──────────────────
    print(f"\n{'═'*60}")
    print(f"  What happens if user hasn't connected HubSpot yet:")
    print(f"{'═'*60}")

    new_user_id = "user_new_001"
    await orcha_handle_message(
        "Find me 10 fintech CTOs to contact this week",
        new_user_id,
        "NewUser",
    )


if __name__ == "__main__":
    asyncio.run(main())
