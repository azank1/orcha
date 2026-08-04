"""Tests for the KY-A supervisor allowlist guardrails (WS10 / FR-10.1)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage
from superagent import kya_policy
from superagent.config import settings
from superagent.kya_policy import (
    KYA_ALLOWED_SYSTEM_TOOLS,
    agent_allowed,
    filter_pnd_candidates,
    filter_system_tool_schemas,
    kya_allowed_agent_ids,
    system_tool_allowed,
)
from superagent.nodes.execute_agent_calls import execute_agent_calls_node
from superagent.system_tools import enforcement
from superagent.system_tools.registry import (
    SYSTEM_TOOL_REGISTRY,
    register_all_system_tools,
)

KYA_DID = "did:orcha:agent:kya-verification"
ROGUE_DID = "did:orcha:agent:rogue-agent"


@pytest.fixture
def kya_on(monkeypatch):
    monkeypatch.setattr(settings, "kya_mode_enabled", True)
    return settings


def _candidate(agent_id: str, capability_id: str) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "agent_name": agent_id.rsplit(":", 1)[-1],
        "protocol_type": "MCP",
        "capabilities": [
            {
                "capability_id": capability_id,
                "capability_type": "TOOL",
                "description": "cap",
                "input_schema": {"type": "object", "properties": {}},
            }
        ],
    }


def _tool_name(agent_id: str, capability_id: str) -> str:
    safe_id = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in agent_id)
    return f"{safe_id}__{capability_id}"


def _state_with_tool_call(
    tool_name: str, args: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "session_id": "sess-kya",
        "user_id": "officer-1",
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool_name,
                        "args": args or {},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            )
        ],
        "pnd_candidates": [
            _candidate(KYA_DID, "verify_agent_identity"),
            _candidate(ROGUE_DID, "exfiltrate"),
        ],
    }


# ---------------------------------------------------------------------------
# Policy helpers
# ---------------------------------------------------------------------------


class TestPolicyHelpers:
    def test_default_allowed_agents(self):
        assert kya_allowed_agent_ids() == {
            "did:orcha:agent:kya-verification",
            "did:orcha:agent:rulebook-rag",
            "did:orcha:agent:payment-anomaly",
        }

    def test_allowed_agents_parses_comma_list(self, monkeypatch):
        monkeypatch.setattr(settings, "kya_allowed_agents", " did:a , did:b ,")
        assert kya_allowed_agent_ids() == {"did:a", "did:b"}

    def test_disabled_mode_is_permissive(self):
        assert system_tool_allowed("save_artifact") is True
        assert agent_allowed(ROGUE_DID) is True

    def test_enabled_mode_restricts(self, kya_on):
        assert system_tool_allowed("propose_enforcement") is True
        assert system_tool_allowed("sign_case_attestation") is True
        assert system_tool_allowed("create_checklist") is True
        assert system_tool_allowed("save_artifact") is False
        assert agent_allowed(KYA_DID) is True
        assert agent_allowed(ROGUE_DID) is False

    def test_filter_pnd_candidates(self, kya_on):
        cands = [
            _candidate(KYA_DID, "verify_agent_identity"),
            _candidate(ROGUE_DID, "x"),
        ]
        kept = filter_pnd_candidates(cands)
        assert [c["agent_id"] for c in kept] == [KYA_DID]

    def test_filter_pnd_candidates_disabled_is_noop(self):
        cands = [_candidate(ROGUE_DID, "x")]
        assert filter_pnd_candidates(cands) == cands


class TestPinAllowedAgents:
    @pytest.mark.asyncio
    async def test_missing_allowlisted_agents_are_pinned(self, kya_on, monkeypatch):
        """An allowlisted agent absent from PnD results is injected (no unknown-tool)."""
        manifest = {
            "agent_id": "did:orcha:agent:rulebook-rag",
            "name": "Rulebook RAG",
            "description": "rulebook",
            "transport": {"type": "sse"},
            "capabilities": [
                {
                    "id": "query_rulebook",
                    "type": "tool",
                    "name": "Query Rulebook",
                    "description": "q",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ],
        }
        monkeypatch.setattr(
            "superagent.middleware.manifest_cache.MANIFEST_CACHE.get_manifest",
            AsyncMock(return_value=manifest),
        )
        monkeypatch.setattr(
            settings,
            "kya_allowed_agents",
            "did:orcha:agent:kya-verification,did:orcha:agent:rulebook-rag",
        )

        out = await kya_policy.pin_allowed_agent_candidates(
            [_candidate(KYA_DID, "verify_agent_identity")]
        )

        assert {c["agent_id"] for c in out} == {
            KYA_DID,
            "did:orcha:agent:rulebook-rag",
        }
        pinned = next(c for c in out if c["agent_id"] == "did:orcha:agent:rulebook-rag")
        assert pinned["protocol_type"] == "MCP"
        assert pinned["capabilities"][0]["capability_id"] == "query_rulebook"
        assert pinned["capabilities"][0]["capability_type"] == "TOOL"

    @pytest.mark.asyncio
    async def test_pin_is_noop_when_disabled(self):
        cands = [_candidate(ROGUE_DID, "x")]
        out = await kya_policy.pin_allowed_agent_candidates(cands)
        assert out == cands

    @pytest.mark.asyncio
    async def test_pin_skips_agents_without_capabilities(self, kya_on, monkeypatch):
        monkeypatch.setattr(
            "superagent.middleware.manifest_cache.MANIFEST_CACHE.get_manifest",
            AsyncMock(return_value={"agent_id": KYA_DID, "capabilities": []}),
        )
        monkeypatch.setattr(settings, "kya_allowed_agents", KYA_DID)
        out = await kya_policy.pin_allowed_agent_candidates([])
        assert out == []

    def test_filter_system_tool_schemas(self, kya_on):
        schemas = [
            {"type": "function", "function": {"name": n}}
            for n in ("propose_enforcement", "save_artifact", "get_datetime")
        ]
        kept = filter_system_tool_schemas(schemas)
        names = {s["function"]["name"] for s in kept}
        assert names == {"propose_enforcement", "get_datetime"}
        assert names <= KYA_ALLOWED_SYSTEM_TOOLS


# ---------------------------------------------------------------------------
# Node-level enforcement (execute_agent_calls seam)
# ---------------------------------------------------------------------------


@pytest.fixture
def all_tools_registered():
    register_all_system_tools()
    return SYSTEM_TOOL_REGISTRY


class TestExecuteAgentCallsKyaMode:
    @pytest.mark.asyncio
    async def test_disallowed_system_tool_rejected_not_executed(
        self, kya_on, all_tools_registered, monkeypatch
    ):
        handler = AsyncMock(return_value={"ok": True})
        monkeypatch.setattr(
            SYSTEM_TOOL_REGISTRY._tools["save_artifact"], "handler", handler
        )

        updates = await execute_agent_calls_node(
            _state_with_tool_call("save_artifact", {"local_path": "/tmp/x"}), {}
        )

        handler.assert_not_called()
        msg = updates["messages"][0]
        assert msg.content.startswith("Error:")
        assert "allowlist" in msg.content

    @pytest.mark.asyncio
    async def test_allowed_system_tool_executes(self, kya_on, all_tools_registered):
        updates = await execute_agent_calls_node(
            _state_with_tool_call("get_datetime"), {}
        )
        assert not updates["messages"][0].content.startswith("Error:")

    @pytest.mark.asyncio
    async def test_disallowed_agent_rejected_not_executed(self, kya_on):
        updates = await execute_agent_calls_node(
            _state_with_tool_call(_tool_name(ROGUE_DID, "exfiltrate")), {}
        )
        msg = updates["messages"][0]
        assert msg.content.startswith("Error:")
        assert ROGUE_DID in msg.content

    @pytest.mark.asyncio
    async def test_allowed_agent_dispatched(self, kya_on, monkeypatch):
        executed: list[str] = []

        async def fake_execute(self, **kwargs: Any) -> dict[str, Any]:
            executed.append(kwargs["agent_id"])
            return {"content": "findings ok", "base_fee": "0"}

        monkeypatch.setattr(
            "superagent.middleware.pipeline.ExecutionMiddleware.execute", fake_execute
        )
        updates = await execute_agent_calls_node(
            _state_with_tool_call(_tool_name(KYA_DID, "verify_agent_identity")), {}
        )
        assert executed == [KYA_DID]
        assert updates["messages"][0].content == "findings ok"

    @pytest.mark.asyncio
    async def test_disabled_mode_dispatches_any_agent(self, monkeypatch):
        executed: list[str] = []

        async def fake_execute(self, **kwargs: Any) -> dict[str, Any]:
            executed.append(kwargs["agent_id"])
            return {"content": "ok", "base_fee": "0"}

        monkeypatch.setattr(
            "superagent.middleware.pipeline.ExecutionMiddleware.execute", fake_execute
        )
        updates = await execute_agent_calls_node(
            _state_with_tool_call(_tool_name(ROGUE_DID, "exfiltrate")), {}
        )
        assert executed == [ROGUE_DID]
        assert not updates["messages"][0].content.startswith("Error:")

    @pytest.mark.asyncio
    async def test_propose_enforcement_still_always_interrupts(
        self, kya_on, all_tools_registered, monkeypatch
    ):
        """KY-A mode must not bypass the HITL gate (FR-6.4 / FR-10.1)."""
        seen: list[dict[str, Any]] = []
        monkeypatch.setattr(
            enforcement,
            "interrupt",
            lambda event: seen.append(event) or {"status": "denied"},
        )
        updates = await execute_agent_calls_node(
            _state_with_tool_call(
                "propose_enforcement",
                {
                    "enforcement_action": "suspend_agent",
                    "target_agent_id": ROGUE_DID,
                    "justification": "scope violation",
                },
            ),
            {},
        )
        assert len(seen) == 1
        assert seen[0]["interrupt_type"] == "HITL_APPROVAL"
        assert "DENIED" in updates["messages"][0].content


def test_kya_policy_module_is_single_source():
    """Call sites import the policy module rather than redefining allowed sets."""
    import superagent.nodes.execute_agent_calls as eac

    assert eac.agent_allowed is kya_policy.agent_allowed
    assert eac.system_tool_allowed is kya_policy.system_tool_allowed
