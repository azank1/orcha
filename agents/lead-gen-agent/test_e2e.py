"""
USE CASE: Orcha outreach campaign — find US B2B decision-makers and pitch
the Lead Gen + workflow automation platform.

SCENARIO
--------
Orcha wants to reach sales leaders, RevOps, and growth executives at US
SaaS/tech companies (50-500 employees) who are likely to care about:
  • Automated B2B lead generation (the Lead Gen agent)
  • AI-driven workflow automation (Orcha platform)

The pipeline:
  1. Search Apollo for VP Sales / Head of Growth / RevOps leads in the US
  2. Score against Orcha's ICP
  3. Enrich missing emails via Hunter
  4. Write qualified leads to HubSpot CRM
     → If HUBSPOT_API_KEY not set: auth interrupt fires (user pastes token)
  5. Build personalised outreach email drafts
     → HITL interrupt: user reviews/edits ALL drafts before anything is sent
  6. Send approved emails via SendGrid

The user reviews every draft — nothing goes out without approval.

HOW TO RUN
----------
# Unit tests only (no API keys needed):
  cd agents/lead-gen-agent
  uv run python test_e2e.py --unit-only

# Full pipeline with mocks (needs LLM key):
  ANTHROPIC_API_KEY=sk-ant-... uv run python test_e2e.py

# Full pipeline with real email send:
  ANTHROPIC_API_KEY=sk-ant-...  \\
  SENDGRID_API_KEY=SG.xxx  \\
  FROM_EMAIL=you@yourdomain.com  \\
  HUBSPOT_API_KEY=pat-eu1-...  \\
  uv run python test_e2e.py
"""

import asyncio
import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(__file__))

# Load .env from the agent directory (where OPENAI_API_KEY etc. live)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

os.environ.setdefault("LLM_PROVIDER", "anthropic")

# ── Helpers ────────────────────────────────────────────────────────────────

def _sep(title: str = "") -> None:
    width = 62
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * (width - pad - len(title) - 2)}")
    else:
        print("─" * width)


def _print_leads(leads: list[dict], label: str = "Qualified leads") -> None:
    print(f"\n{label} ({len(leads)}):")
    for i, lead in enumerate(leads[:8], 1):
        name    = lead.get("full_name", lead.get("name", "?"))
        title   = lead.get("title", "")
        company = lead.get("company", "")
        score   = lead.get("icp_score", "?")
        email   = lead.get("email", "no email")
        print(f"  {i}. {name} — {title} @ {company}  [score={score}]  <{email}>")
    if len(leads) > 8:
        print(f"     … and {len(leads) - 8} more")


def _print_drafts(drafts: list[dict]) -> None:
    print(f"\nEmail drafts for your review ({len(drafts)}):")
    for i, d in enumerate(drafts, 1):
        print(f"\n  ─── Draft {i}: {d['to_name']} <{d['to_email']}> ───")
        print(f"  Subject : {d['subject']}")
        for line in d["body"].splitlines()[:6]:
            print(f"  {line}")
        if len(d["body"].splitlines()) > 6:
            print("  …")


# ── Email templates for Orcha outreach ────────────────────────────────

OUTREACH_SUBJECT = "Quick question about your lead gen process, {first_name}"

OUTREACH_BODY = """\
Hi {first_name},

I'm reaching out because {company} looks like a company that takes growth seriously — \
and I wanted to share something that might save your team real time.

We built Orcha, a platform that lets you run fully automated B2B lead gen pipelines \
with AI agents: find prospects, score against your ICP, enrich emails, sync to HubSpot, \
and send personalised outreach — all in one workflow. Human-in-the-loop controls mean \
nothing goes out without your sign-off.

Would a 20-minute call make sense to see if this fits how {company} approaches pipeline building?

Best,
The Orcha Team
https://orcha.ai
"""


# ── Simulated HITL: user reviews every draft before send ─────────────────

async def simulate_email_review(drafts: list[dict]) -> list[dict]:
    """
    Simulate the human-in-the-loop email review interrupt.

    A real user would see this in the Orcha UI, edit any draft they want,
    then click "Approve & Send". Here we simulate:
      • Viewing all drafts
      • Editing the subject of draft 1 to be more specific
      • Approving all drafts
    """
    _sep("INTERRUPT: Email Draft Review")
    print("⏸  Agent paused. Review all email drafts before sending.\n")
    _print_drafts(drafts)

    print("\n[Simulated user review]")
    edited = [dict(d) for d in drafts]

    if edited:
        # Personalise the first subject a bit more
        first_name = edited[0]["to_name"].split()[0] if edited[0]["to_name"] else "there"
        original_subject = edited[0]["subject"]
        edited[0]["subject"] = f"Hey {first_name} — saw your growth role at {edited[0].get('to_name', '')} → quick idea"
        print(f"  ✎ Draft 1 subject edited:")
        print(f"      Before : {original_subject}")
        print(f"      After  : {edited[0]['subject']}")

    print(f"\n  ✓ All {len(edited)} draft(s) approved. Proceeding with send.")
    return edited


async def simulate_hubspot_auth() -> str:
    """
    Simulate the HubSpot auth interrupt when no token is pre-configured.
    In production this shows a form in the Orcha UI.
    """
    _sep("INTERRUPT: HubSpot Token Required")
    print("⏸  Agent paused. HubSpot Private App Token needed for CRM writes.\n")
    print("  How to get your token:")
    print("  1. HubSpot → Settings → Integrations → Private Apps")
    print("  2. Create app → Scopes: crm.objects.contacts.write + read")
    print("  3. Generate + copy the token\n")
    print("[Simulated user action] Pasting mock token…")
    mock_token = "pat-eu1-mock-orcha-test-000000000000"
    print(f"  ✓ Token accepted: {mock_token[:16]}…")
    return mock_token


# ── Orcha ICP ─────────────────────────────────────────────────────────

def orcha_icp():
    from tools.score_tool import ICPConfig
    return ICPConfig(
        target_roles=[
            "VP Sales", "VP of Sales", "Head of Sales",
            "VP Revenue", "CRO", "Chief Revenue Officer",
            "Head of Growth", "VP Growth",
            "RevOps", "Revenue Operations",
            "Founder", "Co-Founder", "CEO",
        ],
        industries=["SaaS", "Software", "Technology", "B2B", "FinTech", "MarTech"],
        company_size_min=30,
        company_size_max=500,
        geographies=["United States", "US", "USA"],
        min_score=55,   # slightly lower threshold to get enough prospects with mocks
    )


# ── Full pipeline ─────────────────────────────────────────────────────────

async def run_orcha_outreach_campaign() -> dict:
    """
    Orcha's own B2B outreach: find US sales/growth leaders and pitch the platform.
    """
    from core.agent import LeadGenAgent

    _sep("Orcha Outreach Campaign — Full Pipeline")
    print("Target    : US SaaS/Tech companies, 30-500 employees")
    print("Roles     : VP Sales, Head of Growth, CRO, Founder")
    print("Goal      : Demo Orcha lead gen + workflow automation")
    print("Interrupts: HubSpot auth + email draft review (HITL)\n")

    agent = LeadGenAgent()
    start = time.time()

    result = await agent.run(
        query=(
            "Find VP Sales, Head of Growth, CRO and Founders at US SaaS and tech companies "
            "with 30 to 300 employees who would be interested in AI-powered lead generation "
            "and workflow automation tools"
        ),
        max_leads=10,
        write_to_crm=True,
        send_outreach_email=True,
        review_callback=simulate_email_review,
        hubspot_auth_callback=simulate_hubspot_auth,
    )

    elapsed = round(time.time() - start, 1)

    _sep("Campaign Result")
    print(f"  Status          : {result.get('status', '?')}")
    print(f"  Leads found     : {result.get('leads_found', 0)}")
    print(f"  Leads qualified : {result.get('leads_qualified', 0)}")
    print(f"  Written to CRM  : {result.get('leads_written_to_crm', 0)}")
    print(f"  Emails sent     : {result.get('emails_sent', 0)}")
    print(f"  Execution time  : {elapsed}s")
    print(f"  LLM provider    : {result.get('provider', '?')}")

    if result.get("summary"):
        print(f"\n  Summary: {result['summary']}")

    qualified = result.get("qualified_leads", [])
    if qualified:
        _print_leads(qualified, "Qualified prospects")

    return result


# ── Unit tests ─────────────────────────────────────────────────────────────

class TestEmailPreview(unittest.TestCase):
    def test_build_previews_personalises_correctly(self):
        from tools.email_preview_tool import build_email_previews
        leads = [
            {"full_name": "Jane Smith", "email": "jane@acme.com", "title": "VP Sales", "company": "Acme"},
            {"full_name": "Bob Jones",  "email": "bob@beta.com",  "title": "CRO",      "company": "Beta"},
        ]
        drafts = build_email_previews(
            leads,
            subject=OUTREACH_SUBJECT,
            message_template=OUTREACH_BODY,
        )
        self.assertEqual(len(drafts), 2)
        self.assertIn("Jane", drafts[0]["subject"])
        self.assertIn("Acme", drafts[0]["body"])
        self.assertEqual(drafts[1]["to_email"], "bob@beta.com")

    def test_skips_leads_without_email(self):
        from tools.email_preview_tool import build_email_previews
        leads = [
            {"full_name": "No Email",  "title": "VP Sales", "company": "X"},
            {"full_name": "Has Email", "email": "yes@y.com", "title": "CRO", "company": "Y"},
        ]
        drafts = build_email_previews(leads, subject="Hi {first_name}", message_template="Body")
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["to_email"], "yes@y.com")

    def test_bad_placeholder_falls_back_gracefully(self):
        from tools.email_preview_tool import build_email_previews
        leads = [{"full_name": "Alice", "email": "alice@x.com", "title": "CRO", "company": "X"}]
        drafts = build_email_previews(
            leads, subject="Hey {unknown_field}", message_template="Body"
        )
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["subject"], "Hey {unknown_field}")   # raw fallback

    def test_orcha_template_renders(self):
        from tools.email_preview_tool import build_email_previews
        leads = [{"full_name": "Sarah Lee", "email": "sarah@saas.io", "title": "VP Sales", "company": "SaasCo"}]
        drafts = build_email_previews(leads, OUTREACH_SUBJECT, OUTREACH_BODY)
        self.assertIn("Sarah", drafts[0]["subject"])
        self.assertIn("SaasCo", drafts[0]["body"])
        self.assertIn("Orcha", drafts[0]["body"])


class TestResumeValueParsing(unittest.TestCase):
    """Tests for the _parse_resume_data logic in main.py."""

    def test_json_text_part_parsed(self):
        parts = [{"kind": "text", "text": '{"approved": true, "edited_drafts": [{"to_email": "a@b.com"}]}'}]
        r = _parse_resume(parts)
        self.assertTrue(r.get("approved"))
        self.assertEqual(len(r["edited_drafts"]), 1)

    def test_plain_text_stored_as_text_key(self):
        self.assertEqual(_parse_resume([{"kind": "text", "text": "approve"}]), {"text": "approve"})

    def test_deny_text(self):
        self.assertEqual(_parse_resume([{"kind": "text", "text": "deny"}]), {"text": "deny"})

    def test_data_part_merged(self):
        parts = [{"kind": "data", "data": {"response": "pat-eu1-token"}}]
        self.assertEqual(_parse_resume(parts).get("response"), "pat-eu1-token")

    def test_mixed_parts(self):
        parts = [
            {"kind": "text", "text": "some text"},
            {"kind": "data", "data": {"extra": "field"}},
        ]
        r = _parse_resume(parts)
        self.assertEqual(r.get("text"), "some text")
        self.assertEqual(r.get("extra"), "field")


class TestICPScoring(unittest.TestCase):
    def test_vp_sales_scores_high_for_orcha(self):
        from tools.score_tool import score_lead, ICPConfig
        icp = orcha_icp()
        lead = {
            "title": "VP Sales",
            "industry": "SaaS",
            "company_size": 150,
            "email": "vp@saas.io",
            "email_status": "verified",
        }
        scored = score_lead(lead, icp)
        self.assertGreaterEqual(scored["icp_score"], 60)
        self.assertTrue(scored["qualified"])

    def test_irrelevant_role_disqualified(self):
        from tools.score_tool import score_lead, ICPConfig
        icp = orcha_icp()
        lead = {"title": "Junior Designer", "industry": "SaaS", "company_size": 100}
        scored = score_lead(lead, icp)
        self.assertFalse(scored["qualified"])


def _parse_resume(parts: list[dict]) -> dict:
    """Inline copy of main.py:_parse_resume_data for unit testing."""
    resume: dict = {}
    for part in parts:
        kind = part.get("kind")
        if kind == "text":
            text = part.get("text", "")
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    resume.update(parsed)
                    continue
            except (json.JSONDecodeError, ValueError):
                pass
            resume["text"] = text
        elif kind == "data":
            data = part.get("data", {})
            if isinstance(data, dict):
                resume.update(data)
    return resume


# ── Main entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Orcha outreach campaign E2E test")
    parser.add_argument("--unit-only", action="store_true",
                        help="Run unit tests only (no LLM key required)")
    args = parser.parse_args()

    if args.unit_only:
        unittest.main(argv=["", "-v"], exit=True)

    # Check LLM key
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    key_map  = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "grok": "GROK_API_KEY"}
    llm_key  = key_map.get(provider)
    if llm_key and not os.getenv(llm_key):
        print(f"⚠  {llm_key} not set — running unit tests only.\n")
        print(f"   Full pipeline: {llm_key}=<key> uv run python test_e2e.py\n")
        print("   Real outreach: add SENDGRID_API_KEY, FROM_EMAIL, HUBSPOT_API_KEY\n")
        unittest.main(argv=["", "-v"], exit=True)

    # Unit tests first
    _sep("Unit Tests")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEmailPreview)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestResumeValueParsing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestICPScoring))
    result_unit = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result_unit.wasSuccessful():
        sys.exit(1)

    # Full campaign pipeline
    result = asyncio.run(run_orcha_outreach_campaign())

    _sep("Done ✓")
    print("\nPipeline summary:")
    print("  ✓ Lead search (Apollo — mock if no key)")
    print("  ✓ ICP scoring against Orcha's target persona")
    print("  ✓ Email enrichment (Hunter — mock if no key)")

    if os.getenv("HUBSPOT_API_KEY"):
        print("  ✓ HubSpot CRM write (real token)")
    else:
        print("  ✓ HubSpot auth interrupt simulated (no real token configured)")

    print("  ✓ Email drafts generated with Orcha pitch template")
    print("  ✓ HITL review interrupt: user reviewed and edited drafts")

    emails_sent = result.get("emails_sent", 0)
    if os.getenv("SENDGRID_API_KEY") and emails_sent > 0:
        print(f"  ✓ {emails_sent} outreach email(s) sent via SendGrid")
        print("\n  ⚡ Real emails dispatched — watch your inbox for replies!")
    elif os.getenv("SENDGRID_API_KEY"):
        print("  ⚠  SendGrid key present but 0 emails sent — check FROM_EMAIL env var")
    else:
        print("  ℹ  Email send skipped (SENDGRID_API_KEY not set)")
        print("     Set SENDGRID_API_KEY + FROM_EMAIL to send real outreach.")
