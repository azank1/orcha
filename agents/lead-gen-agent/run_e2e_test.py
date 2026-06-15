"""
E2E test runner — tests the lead-gen agent against real APIs.
Run this AFTER starting the server: python main.py

Usage:
  python run_e2e_test.py                  # full flow (search + HITL email review)
  python run_e2e_test.py --no-email       # search + CRM only, skip email HITL
  python run_e2e_test.py --no-crm         # search only, no CRM write
  python run_e2e_test.py --local          # test Google Maps path (local businesses)
"""
import asyncio
import json
import sys
import time
import httpx

BASE_URL = "http://localhost:4567"
POLL_INTERVAL = 3   # seconds between polls
MAX_POLLS     = 40  # give up after ~2 minutes


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"

def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m"

def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"

def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m"

def _cyan(text: str) -> str:
    return f"\033[96m{text}\033[0m"


# ── Step 0: health check ──────────────────────────────────────────────────────

async def check_health(client: httpx.AsyncClient) -> dict:
    print(_bold("\n[1] Health check..."))
    r = await client.get(f"{BASE_URL}/health")
    r.raise_for_status()
    data = r.json()

    configured = data.get("apis_configured", {})
    provider   = data.get("llm_provider", "?")

    print(f"    Server:       {_green('OK')}")
    print(f"    LLM provider: {_cyan(provider)}")
    print(f"    APIs configured:")
    for api, ok in configured.items():
        status = _green("yes") if ok else _yellow("no (mock)")
        print(f"      {api:<12} {status}")

    return data


# ── Step 1: simple /run smoke test ───────────────────────────────────────────

async def test_simple_search(client: httpx.AsyncClient, query: str) -> dict:
    print(_bold(f"\n[2] Simple search via /run (no CRM, no email)"))
    print(f"    Query: {_cyan(query)}")

    payload = {
        "query": query,
        "credentials": {},        # env vars are used automatically
        "max_leads": 5,
        "write_to_crm": False,
        "send_outreach_email": False,
    }

    t0 = time.time()
    r = await client.post(f"{BASE_URL}/run", json=payload, timeout=120)
    elapsed = int((time.time() - t0) * 1000)

    if r.status_code != 200:
        print(_red(f"    FAILED: HTTP {r.status_code}"))
        print(f"    Body: {r.text[:500]}")
        return {}

    data = r.json()
    leads = data.get("leads", [])

    print(f"    Status:           {_green(data.get('status', '?'))}")
    print(f"    Leads found:      {data.get('leads_found', 0)}")
    print(f"    Leads qualified:  {data.get('leads_qualified', 0)}")
    print(f"    Time:             {elapsed}ms")

    if leads:
        print(f"\n    Top {min(3, len(leads))} qualified leads:")
        for lead in leads[:3]:
            score  = lead.get("icp_score", "?")
            name   = lead.get("full_name", "Unknown")
            title  = lead.get("title", "")
            co     = lead.get("company", "")
            email  = lead.get("email") or _yellow("no email")
            source = lead.get("source", "")
            tag    = _yellow("[mock]") if "mock" in source else _green("[real]")
            print(f"    {tag} {name} — {title} at {co}")
            print(f"         Score: {score}  |  Email: {email}")
    else:
        print(_yellow("    No qualified leads returned."))

    return data


# ── Step 2: full A2A flow with HITL ──────────────────────────────────────────

async def _rpc(client: httpx.AsyncClient, method: str, params: dict, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "method": method, "id": req_id, "params": params}
    r = await client.post(BASE_URL + "/", json=payload, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"RPC error: {body['error']}")
    return body.get("result", {})


async def test_full_a2a_flow(
    client: httpx.AsyncClient,
    query: str,
    write_to_crm: bool,
    send_email: bool,
) -> dict:
    label_parts = []
    if write_to_crm:   label_parts.append("CRM write")
    if send_email:     label_parts.append("HITL email review")
    label = " + ".join(label_parts) if label_parts else "search only"

    print(_bold(f"\n[3] Full A2A flow — {label}"))
    print(f"    Query: {_cyan(query)}")

    # 3a. Submit task
    result = await _rpc(client, "message/send", {
        "message": {
            "role": "user",
            "parts": [
                {"kind": "text",  "text": query},
                {"kind": "data",  "data": {
                    "write_to_crm":         write_to_crm,
                    "send_outreach_email":  send_email,
                    "max_leads": 5,
                }},
            ],
        }
    })

    task_id = result.get("id")
    if not task_id:
        print(_red("    No task id returned — aborting"))
        return {}

    print(f"    Task created: {_cyan(task_id)}")

    # 3b. Poll until done or input-required
    final = {}
    for poll_n in range(MAX_POLLS):
        await asyncio.sleep(POLL_INTERVAL)

        status_result = await _rpc(client, "tasks/get", {"id": task_id}, req_id=2)
        state = status_result.get("status", {}).get("state", "unknown")

        print(f"    [{poll_n+1:02d}] status = {state}", end="", flush=True)

        if state == "completed":
            print()
            final = status_result
            break

        elif state == "failed":
            print()
            msg = status_result.get("status", {}).get("message", "no detail")
            print(_red(f"    Task failed: {msg}"))
            return {}

        elif state == "input-required":
            # HITL interrupt — read the draft emails and auto-approve
            print(_yellow("  ← paused for human review"))
            status_msg = status_result.get("status", {}).get("message", {})
            meta       = status_msg.get("metadata", {}) if isinstance(status_msg, dict) else {}
            interrupt  = meta.get("interrupt_type", "unknown")

            if interrupt == "approval":
                drafts = meta.get("drafts", [])
                print(f"\n    {_bold('Email drafts to review:')} ({len(drafts)} draft(s))")
                for i, d in enumerate(drafts, 1):
                    print(f"\n    --- Draft {i} ---")
                    print(f"    To:      {d.get('to', '?')}")
                    print(f"    Subject: {d.get('subject', '?')}")
                    body_preview = (d.get("body") or "")[:200]
                    print(f"    Body:    {body_preview}{'...' if len(d.get('body',''))>200 else ''}")

                print(_yellow("\n    Auto-approving drafts (simulating user review)..."))
                await _rpc(client, "message/send", {
                    "taskId": task_id,
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "approve"}],
                    },
                }, req_id=3)

            elif interrupt == "clarification":
                q = meta.get("question", "Input required")
                print(_yellow(f"\n    HubSpot auth needed: {q[:120]}..."))
                print(_red("    No HubSpot token in env — skipping CRM write in this task"))
                # Respond with empty so agent skips gracefully
                await _rpc(client, "message/send", {
                    "taskId": task_id,
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "skip"}],
                    },
                }, req_id=3)
        else:
            print()  # working / submitted — keep polling

    # 3c. Print results
    artifacts = final.get("artifacts", [])
    if not artifacts:
        print(_yellow("    No artifacts returned."))
        return final

    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                print(f"\n{_bold('    Result:')}")
                for line in part["text"].splitlines():
                    print(f"    {line}")
            elif part.get("kind") == "data":
                data = part["data"]
                leads = data.get("qualified_leads", [])
                if leads:
                    print(f"\n    {_bold('Qualified leads detail:')}")
                    for lead in leads:
                        src = lead.get("source","")
                        tag = _yellow("[mock]") if "mock" in src else _green("[real]")
                        print(f"    {tag} {lead.get('full_name','?')} — {lead.get('title','')} @ {lead.get('company','')}")
                        print(f"         Score: {lead.get('icp_score','?')}  |  Email: {lead.get('email') or 'n/a'}")

    return final


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    args         = sys.argv[1:]
    no_email     = "--no-email" in args
    no_crm       = "--no-crm"   in args
    local_search = "--local"    in args

    if local_search:
        query_simple = "Find coffee shops near downtown Chicago"
        query_full   = "Find restaurants near Manhattan New York and send them outreach emails"
    else:
        query_simple = "Find VP Engineering leads at SaaS companies in the US with 50-200 employees"
        query_full   = (
            "Find marketing directors at fintech startups in New York with 20-150 employees. "
            "Write qualified leads to CRM and send personalised outreach emails."
        )

    send_email = not no_email
    write_crm  = not no_crm

    print(_bold("=" * 60))
    print(_bold("  Lead Gen Agent — E2E Test with Real APIs"))
    print(_bold("=" * 60))

    async with httpx.AsyncClient() as client:
        # Step 0: health
        try:
            await check_health(client)
        except Exception as e:
            print(_red(f"\nServer not reachable: {e}"))
            print("Start the server first:  python main.py")
            sys.exit(1)

        # Step 1: simple /run (fast, no side effects)
        await test_simple_search(client, query_simple)

        # Step 2: full A2A with HITL
        await test_full_a2a_flow(
            client,
            query=query_full,
            write_to_crm=write_crm,
            send_email=send_email,
        )

    print(_bold("\n" + "=" * 60))
    print(_bold("  Test complete"))
    print(_bold("=" * 60))


if __name__ == "__main__":
    asyncio.run(main())
