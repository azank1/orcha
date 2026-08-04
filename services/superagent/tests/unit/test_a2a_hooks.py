"""Unit tests for the A2A capability hook seam (lead-gen CRM behavior)."""

from __future__ import annotations

import json

from internal_commons.interrupts.types import InterruptType
from superagent.handlers.a2a_hooks import (
    LeadGenOptionsHook,
    get_a2a_hook,
    infer_crm_choice_from_task,
    register_a2a_hook,
)


class TestInferCrmChoice:
    def test_excel_keywords(self):
        assert infer_crm_choice_from_task("export leads to Excel please") == "excel"
        assert infer_crm_choice_from_task("give me an xlsx export") == "excel"

    def test_gsheets_keywords(self):
        assert infer_crm_choice_from_task("write to google sheets") == "gsheets"
        assert infer_crm_choice_from_task("put it in a spreadsheet") == "gsheets"

    def test_notion_and_hubspot(self):
        assert infer_crm_choice_from_task("sync to Notion") == "notion"
        assert infer_crm_choice_from_task("push to HubSpot") == "hubspot"

    def test_no_match_returns_none(self):
        assert infer_crm_choice_from_task("find me coffee shops") is None
        assert infer_crm_choice_from_task("") is None


class TestEnrichRequestParts:
    def test_text_part_always_first(self):
        hook = LeadGenOptionsHook()
        parts = hook.enrich_request_parts("find leads", {})
        assert parts[0] == {"kind": "text", "text": "find leads"}
        assert len(parts) == 1

    def test_allowlisted_opts_become_data_part(self):
        hook = LeadGenOptionsHook()
        state = {
            "lead_gen_options": {"crm_type": "notion", "max_leads": 5, "evil_key": 1}
        }
        parts = hook.enrich_request_parts("find leads", state)
        assert parts[1] == {
            "kind": "data",
            "data": {"crm_type": "notion", "max_leads": 5},
        }

    def test_inferred_crm_fills_missing_crm_type(self):
        hook = LeadGenOptionsHook()
        parts = hook.enrich_request_parts("export to excel", {"lead_gen_options": {}})
        assert parts[1] == {"kind": "data", "data": {"crm_type": "excel"}}

    def test_explicit_crm_type_beats_inference(self):
        hook = LeadGenOptionsHook()
        state = {"lead_gen_options": {"crm_type": "hubspot"}}
        parts = hook.enrich_request_parts("export to excel", state)
        assert parts[1] == {"kind": "data", "data": {"crm_type": "hubspot"}}


class TestAutoAnswerInterrupt:
    def test_crm_setup_with_named_crm_auto_answers(self):
        hook = LeadGenOptionsHook()
        answer = hook.auto_answer_interrupt(
            InterruptType.CRM_SETUP, "write to google sheets", {}
        )
        assert json.loads(answer) == {"crm_type": "gsheets"}

    def test_crm_setup_without_named_crm_returns_none(self):
        hook = LeadGenOptionsHook()
        assert (
            hook.auto_answer_interrupt(InterruptType.CRM_SETUP, "find leads", {})
            is None
        )

    def test_other_interrupt_types_return_none(self):
        hook = LeadGenOptionsHook()
        assert (
            hook.auto_answer_interrupt(
                InterruptType.HITL_APPROVAL, "export to excel", {}
            )
            is None
        )


class TestRegistry:
    def test_default_hook_is_lead_gen(self):
        assert isinstance(get_a2a_hook(), LeadGenOptionsHook)

    def test_register_replaces_and_restores(self):
        class DummyHook:
            def enrich_request_parts(self, task, state):
                return [{"kind": "text", "text": task}]

            def auto_answer_interrupt(self, interrupt_type, task, state):
                return None

        original = get_a2a_hook()
        register_a2a_hook(DummyHook())
        assert not isinstance(get_a2a_hook(), LeadGenOptionsHook)
        register_a2a_hook(original)
        assert get_a2a_hook() is original
