"""Tests for the sign_case_attestation system tool (WS8 / FR-8)."""

from __future__ import annotations

import json
import sys
from typing import Any

import pytest
from superagent.system_tools.attestation import (
    _sign_case_attestation,
    register_attestation_tools,
)
from superagent.system_tools.registry import (
    SYSTEM_TOOL_REGISTRY,
    SystemToolRegistry,
    register_all_system_tools,
)


@pytest.fixture
def fake_validator(monkeypatch):
    """Install a fake ``validator`` module exposing finalize_case."""
    calls: list[dict[str, Any]] = []

    async def finalize_case(
        session_id: str, case_payload: dict, db: Any = None
    ) -> dict:
        calls.append({"session_id": session_id, "case_payload": case_payload})
        return {
            "attestation_id": "att-1",
            "case_hash": "ab" * 32,
            "signature": "sig",
            "public_key": "pk",
            "status": "pending",
        }

    module = type(sys)("validator")
    module.finalize_case = finalize_case  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "validator", module)
    return calls


class TestSignCaseAttestation:
    def test_tool_registered(self):
        registry = SystemToolRegistry()
        register_attestation_tools(registry)
        assert registry.has("sign_case_attestation")
        schema = registry.get_all_schemas()[0]["function"]
        assert schema["parameters"]["required"] == ["case_payload"]

    def test_registered_by_register_all_system_tools(self):
        register_all_system_tools()
        assert SYSTEM_TOOL_REGISTRY.has("sign_case_attestation")

    @pytest.mark.asyncio
    async def test_handler_calls_finalize_case_and_returns_json(self, fake_validator):
        case_payload = {"verification": {"overall": "fail"}}
        result = await _sign_case_attestation(
            {"case_payload": case_payload, "summary": "one-liner"},
            {"session_id": "sess-1"},
        )
        parsed = json.loads(result)
        assert parsed == {
            "attestation_id": "att-1",
            "case_hash": "ab" * 32,
            "signature": "sig",
            "public_key": "pk",
            "status": "pending",
        }
        call = fake_validator[0]
        assert call["session_id"] == "sess-1"
        # Optional summary is folded into the signed payload.
        assert call["case_payload"]["verification"] == {"overall": "fail"}
        assert call["case_payload"]["summary"] == "one-liner"

    @pytest.mark.asyncio
    async def test_import_error_returns_error_string_without_raising(self, monkeypatch):
        # Importing a None entry in sys.modules raises ImportError regardless
        # of whether the validator package is actually installed.
        monkeypatch.setitem(sys.modules, "validator", None)
        result = await _sign_case_attestation(
            {"case_payload": {"x": 1}}, {"session_id": "sess-1"}
        )
        assert result.startswith("Error:")
        assert "validator" in result

    @pytest.mark.asyncio
    async def test_missing_case_payload_returns_error(self, fake_validator):
        result = await _sign_case_attestation({}, {"session_id": "sess-1"})
        assert result.startswith("Error:")
        assert fake_validator == []

    @pytest.mark.asyncio
    async def test_missing_session_id_returns_error(self, fake_validator):
        result = await _sign_case_attestation({"case_payload": {"x": 1}}, {})
        assert result.startswith("Error:")
        assert fake_validator == []


class TestEnforcementOrderingGuard:
    """KY-A mode: flagged cases can't be sealed before a human decision."""

    @pytest.mark.asyncio
    async def test_flagged_case_without_decision_is_refused(
        self, fake_validator, monkeypatch
    ):
        monkeypatch.setattr("superagent.kya_policy.settings.kya_mode_enabled", True)

        async def _false(session_id: str, db: Any = None) -> bool:
            return False

        monkeypatch.setattr(
            "superagent.middleware.audit_ledger.has_approved_hitl_decision", _false
        )

        result = await _sign_case_attestation(
            {"case_payload": {"payment_flags": [{"rule_id": "X"}]}},
            {"session_id": "sess-1"},
        )
        assert result.startswith("Error:")
        assert "propose_enforcement" in result
        assert fake_validator == []

    @pytest.mark.asyncio
    async def test_flagged_case_with_approved_decision_proceeds(
        self, fake_validator, monkeypatch
    ):
        monkeypatch.setattr("superagent.kya_policy.settings.kya_mode_enabled", True)

        async def _true(session_id: str, db: Any = None) -> bool:
            return True

        monkeypatch.setattr(
            "superagent.middleware.audit_ledger.has_approved_hitl_decision", _true
        )

        result = await _sign_case_attestation(
            {"case_payload": {"payment_flags": [{"rule_id": "X"}]}},
            {"session_id": "sess-1"},
        )
        assert json.loads(result)["attestation_id"] == "att-1"
        assert len(fake_validator) == 1

    @pytest.mark.asyncio
    async def test_clean_case_needs_no_decision(self, fake_validator, monkeypatch):
        monkeypatch.setattr("superagent.kya_policy.settings.kya_mode_enabled", True)
        result = await _sign_case_attestation(
            {
                "case_payload": {
                    "verification": {"overall": "pass"},
                    "payment_flags": [],
                }
            },
            {"session_id": "sess-1"},
        )
        assert json.loads(result)["attestation_id"] == "att-1"
