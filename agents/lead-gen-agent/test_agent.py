"""
Tests for the Lead Gen Agent.
Run with: python -m pytest test_agent.py -v
Or run individual tests: python test_agent.py
"""
import asyncio
import json
import os
import sys
import unittest

# Make sure we can import from parent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.score_tool import score_lead, score_and_filter, deduplicate, ICPConfig


# ── Scoring tests (no API calls needed) ──────────────────────────────────────

class TestScoring(unittest.TestCase):

    def setUp(self):
        self.icp = ICPConfig(
            target_roles=["CTO", "VP Engineering"],
            industries=["SaaS", "FinTech"],
            company_size_min=50,
            company_size_max=500,
            geographies=["United States"],
            min_score=70,
        )

    def test_perfect_lead_scores_100(self):
        lead = {
            "full_name": "Jane Smith",
            "title": "CTO",
            "company": "CloudCo",
            "industry": "SaaS",
            "company_size": 150,
            "email": "jane@cloudco.com",
            "email_status": "verified",
            "location": "San Francisco, US",
        }
        result = score_lead(lead, self.icp)
        self.assertEqual(result["icp_score"], 100)
        self.assertTrue(result["qualified"])

    def test_wrong_role_reduces_score(self):
        lead = {
            "full_name": "Bob Jones",
            "title": "Marketing Manager",
            "company": "CloudCo",
            "industry": "SaaS",
            "company_size": 150,
            "email": "bob@cloudco.com",
            "email_status": "verified",
        }
        result = score_lead(lead, self.icp)
        self.assertEqual(result["score_breakdown"]["role"], 0)
        self.assertFalse(result["qualified"])

    def test_partial_role_match(self):
        lead = {
            "full_name": "Alice Kim",
            "title": "Senior VP Engineering",  # contains "VP Engineering"
            "company": "CloudCo",
            "industry": "SaaS",
            "company_size": 150,
            "email": "alice@cloudco.com",
            "email_status": "verified",
        }
        result = score_lead(lead, self.icp)
        self.assertGreaterEqual(result["score_breakdown"]["role"], 20)

    def test_filter_returns_qualified_and_disqualified(self):
        leads = [
            {"full_name": "A", "title": "CTO", "industry": "SaaS", "company_size": 100, "email": "a@x.com", "email_status": "verified"},
            {"full_name": "B", "title": "Sales Rep", "industry": "Retail", "company_size": 5000, "email": None},
        ]
        qualified, disqualified = score_and_filter(leads, self.icp)
        self.assertEqual(len(qualified), 1)
        self.assertEqual(len(disqualified), 1)
        self.assertEqual(qualified[0]["full_name"], "A")

    def test_dedup_removes_duplicate_emails(self):
        leads = [
            {"full_name": "A", "email": "same@x.com"},
            {"full_name": "B", "email": "same@x.com"},
            {"full_name": "C", "email": "other@x.com"},
        ]
        result = deduplicate(leads)
        self.assertEqual(len(result), 2)
        emails = [l["email"] for l in result]
        self.assertIn("same@x.com", emails)
        self.assertIn("other@x.com", emails)

    def test_dedup_against_existing_crm(self):
        leads = [
            {"full_name": "A", "email": "existing@x.com"},
            {"full_name": "B", "email": "new@x.com"},
        ]
        result = deduplicate(leads, existing_emails={"existing@x.com"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["email"], "new@x.com")



# ── LLM Provider tests ───────────────────────────────────────────────────────

class TestLLMProvider(unittest.TestCase):

    def test_default_provider_is_anthropic(self):
        os.environ.pop("LLM_PROVIDER", None)
        from core.llm_provider import get_provider, AnthropicProvider
        provider = get_provider()
        self.assertIsInstance(provider, AnthropicProvider)

    def test_openai_tool_schema_format(self):
        from core.llm_provider import OpenAIProvider
        from core.tool_schemas import TOOL_SCHEMAS
        provider = OpenAIProvider()
        formatted = provider.format_tools(TOOL_SCHEMAS)
        self.assertEqual(formatted[0]["type"], "function")
        self.assertIn("name", formatted[0]["function"])
        self.assertIn("parameters", formatted[0]["function"])

    def test_anthropic_tool_schema_passthrough(self):
        from core.llm_provider import AnthropicProvider
        from core.tool_schemas import TOOL_SCHEMAS
        provider = AnthropicProvider()
        formatted = provider.format_tools(TOOL_SCHEMAS)
        self.assertEqual(formatted, TOOL_SCHEMAS)

    def test_grok_uses_openai_sdk_with_xai_url(self):
        from core.llm_provider import GrokProvider, OpenAIProvider
        grok = GrokProvider()
        self.assertIsInstance(grok, OpenAIProvider)
        self.assertEqual(grok.BASE_URL, "https://api.x.ai/v1")
        self.assertEqual(grok.MODEL, "grok-3")

    def test_get_api_key_name_per_provider(self):
        from core.llm_provider import get_api_key_name
        for provider, expected in [
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("openai",    "OPENAI_API_KEY"),
            ("grok",      "GROK_API_KEY"),
        ]:
            os.environ["LLM_PROVIDER"] = provider
            self.assertEqual(get_api_key_name(), expected)
        os.environ.pop("LLM_PROVIDER", None)


# ── Mock tool tests ───────────────────────────────────────────────────────────

class TestApolloMock(unittest.TestCase):
    def test_mock_returns_prospects_when_no_key(self):
        """When APOLLO_API_KEY is not set, mock data should be returned."""
        os.environ.pop("APOLLO_API_KEY", None)
        from tools.apollo_tool import search_prospects
        results = asyncio.run(search_prospects(["CTO"], geographies=["United States"]))
        self.assertGreater(len(results), 0)
        self.assertIn("full_name", results[0])
        self.assertIn("email", results[0])
        self.assertIn("title", results[0])
        print(f"  Mock Apollo returned {len(results)} prospects")


class TestHunterMock(unittest.TestCase):
    def test_mock_returns_email_when_no_key(self):
        os.environ.pop("HUNTER_API_KEY", None)
        from tools.hunter_tool import find_email
        result = asyncio.run(find_email("John", "Smith", "acme.com"))
        self.assertIsNotNone(result["email"])
        self.assertIn("acme.com", result["email"])
        print(f"  Mock Hunter returned: {result['email']}")


class TestHubSpotMock(unittest.TestCase):
    def test_mock_upsert_when_no_key(self):
        os.environ.pop("HUBSPOT_API_KEY", None)
        from tools.hubspot_tool import upsert_contact
        lead = {
            "full_name": "Jane Doe",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "title": "CTO",
            "company": "Acme",
        }
        result = asyncio.run(upsert_contact(lead))
        self.assertIn("hubspot_id", result)
        self.assertTrue(result["created"])
        print(f"  Mock HubSpot created: {result['hubspot_id']}")


# ── Context var tests ─────────────────────────────────────────────────────────

class TestContext(unittest.TestCase):

    def test_set_and_get_key(self):
        """Credentials injected via set_credentials are visible via get_key."""
        from core.context import set_credentials, get_key, api_keys
        token = set_credentials({"ANTHROPIC_API_KEY": "test-key-123"})
        try:
            self.assertEqual(get_key("ANTHROPIC_API_KEY"), "test-key-123")
        finally:
            api_keys.reset(token)

    def test_context_resets_after_request(self):
        """After reset, get_key no longer returns the injected value."""
        from core.context import set_credentials, get_key, api_keys
        os.environ.pop("ANTHROPIC_API_KEY", None)
        token = set_credentials({"ANTHROPIC_API_KEY": "ephemeral-key"})
        self.assertEqual(get_key("ANTHROPIC_API_KEY"), "ephemeral-key")
        api_keys.reset(token)
        self.assertIsNone(get_key("ANTHROPIC_API_KEY"))

    def test_none_values_stripped(self):
        """None values don't overwrite os.environ fallback."""
        from core.context import set_credentials, get_key, api_keys
        os.environ["HUNTER_API_KEY"] = "env-hunter-key"
        token = set_credentials({"ANTHROPIC_API_KEY": "test", "HUNTER_API_KEY": None})
        try:
            self.assertEqual(get_key("HUNTER_API_KEY"), "env-hunter-key")
        finally:
            api_keys.reset(token)
            os.environ.pop("HUNTER_API_KEY", None)

    def test_concurrent_contexts_isolated(self):
        """Two concurrent async tasks each see only their own credentials."""
        from core.context import set_credentials, get_key, api_keys

        async def task(key_value, results):
            token = set_credentials({"ANTHROPIC_API_KEY": key_value})
            try:
                await asyncio.sleep(0.01)
                results.append(get_key("ANTHROPIC_API_KEY"))
            finally:
                api_keys.reset(token)

        async def run():
            results = []
            await asyncio.gather(
                task("key-for-task-A", results),
                task("key-for-task-B", results),
            )
            return results

        results = asyncio.run(run())
        self.assertIn("key-for-task-A", results)
        self.assertIn("key-for-task-B", results)
        print(f"  Concurrent isolation: {results}")


# ── Integration test (full agent, no real APIs) ───────────────────────────────

class TestAgentIntegration(unittest.TestCase):
    def test_full_run_with_mock_apis(self):
        """Full agent run — credentials passed via context, not env vars."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            self.skipTest("ANTHROPIC_API_KEY not set — skipping LLM test")

        from core.agent import LeadGenAgent
        from core.context import set_credentials, api_keys

        # Pass creds via context exactly as the orchestrator would
        token = set_credentials({
            "ANTHROPIC_API_KEY": anthropic_key,
            # No Apollo/Hunter/HubSpot keys → tools use mock data
        })
        try:
            agent = LeadGenAgent()
            result = asyncio.run(agent.run(
                query="Find CTO leads at SaaS companies in the US",
                max_leads=5,
                write_to_crm=True,
            ))
        finally:
            api_keys.reset(token)

        print(f"\n  Agent result: {json.dumps(result, indent=2)}")
        self.assertEqual(result["status"], "success")
        self.assertIn("summary", result)
        self.assertIn("execution_time_ms", result)
        print(f"  Execution time: {result['execution_time_ms']}ms")


if __name__ == "__main__":
    print("Running Lead Gen Agent tests...\n")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Always run these (no API keys needed)
    suite.addTests(loader.loadTestsFromTestCase(TestScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestContext))
    suite.addTests(loader.loadTestsFromTestCase(TestApolloMock))
    suite.addTests(loader.loadTestsFromTestCase(TestHunterMock))
    suite.addTests(loader.loadTestsFromTestCase(TestHubSpotMock))

    # Only runs if ANTHROPIC_API_KEY is set
    suite.addTests(loader.loadTestsFromTestCase(TestAgentIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
