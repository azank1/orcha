"""Monotonic delegation attenuation (FR-3): shrinking passes, widening fails."""

from __future__ import annotations

from charter.attenuation import scope_violations, verify_delegation_chain
from helpers import (
    ROOT_DELEGATION,
    ROOT_SCOPE,
    ROOT_VALIDITY,
    make_charter,
    sign_pair,
)

SHRUNK_SCOPE = {
    "dpi_rails": ["UPI"],
    "permitted_actions": ["query_balance"],
    "prohibited_actions": ["cash_withdrawal", "crypto_payout"],
    "max_transaction_value": "1000.00",
    "human_approval_required_above": "2000.00",
}


def _flat_scope(scope, delegation, validity):
    return {**scope, "delegation": delegation, "validity": validity}


class TestScopeViolations:
    def test_shrinking_scope_passes(self):
        child = _flat_scope(
            SHRUNK_SCOPE,
            {"allowed": True, "max_depth": 1},
            {"not_before": "2026-09-01T00:00:00Z", "not_after": "2027-01-01T00:00:00Z"},
        )
        parent = _flat_scope(ROOT_SCOPE, ROOT_DELEGATION, ROOT_VALIDITY)
        assert scope_violations(child, parent) == []

    def test_widening_names_every_dimension(self):
        child = _flat_scope(
            {
                "dpi_rails": ["UPI", "ULI"],  # extra rail
                "permitted_actions": [
                    "initiate_payment",
                    "query_balance",
                    "delete_records",
                ],
                "prohibited_actions": [],  # drops parent prohibition
                "max_transaction_value": "9000.00",  # bigger cap
                "human_approval_required_above": "500.00",  # lower HITL threshold
            },
            {"allowed": True, "max_depth": 2},  # must be <= parent max_depth - 1
            {"not_before": "2026-01-01T00:00:00Z", "not_after": "2028-01-01T00:00:00Z"},
        )
        parent = _flat_scope(ROOT_SCOPE, ROOT_DELEGATION, ROOT_VALIDITY)
        violations = scope_violations(child, parent)

        assert any(v.startswith("rails: child exceeds parent") for v in violations)
        assert any("permitted_actions: child exceeds parent" in v for v in violations)
        assert any("prohibited_actions: child drops" in v for v in violations)
        assert any(
            "max_transaction_value: child 9000.00 exceeds" in v for v in violations
        )
        assert any(
            "human_approval_required_above: child 500.00 below" in v for v in violations
        )
        assert any("delegation: child max_depth 2" in v for v in violations)
        assert any("validity: child window not within parent" in v for v in violations)

    def test_missing_dimension_is_unspecified_never_a_pass(self):
        parent = _flat_scope(ROOT_SCOPE, ROOT_DELEGATION, ROOT_VALIDITY)
        violations = scope_violations(_flat_scope({}, None, None), parent)
        assert violations
        assert all("unspecified" in v or "not allowed" in v for v in violations)
        # Mirror image: child fully specified, parent unspecified.
        child = _flat_scope(
            SHRUNK_SCOPE, {"allowed": True, "max_depth": 1}, ROOT_VALIDITY
        )
        assert scope_violations(child, _flat_scope({}, None, None))

    def test_delegation_disallowed_by_parent(self):
        child = _flat_scope(
            SHRUNK_SCOPE, {"allowed": True, "max_depth": 0}, ROOT_VALIDITY
        )
        parent = _flat_scope(
            ROOT_SCOPE, {"allowed": False, "max_depth": 0}, ROOT_VALIDITY
        )
        assert scope_violations(child, parent) == [
            "delegation: not allowed by parent charter"
        ]


class TestDelegationChain:
    def test_shrinking_chain_passes(self):
        root, child, _ = sign_pair(
            {
                "scope": SHRUNK_SCOPE,
                "delegation": {"allowed": True, "max_depth": 1},
                "validity": ROOT_VALIDITY,
            }
        )
        ok, violations = verify_delegation_chain([root, child])
        assert ok is True
        assert violations == []

    def test_widening_chain_fails_with_named_violations(self):
        root, child, _ = sign_pair(
            {
                "scope": {**ROOT_SCOPE, "max_transaction_value": "9000.00"},
                "delegation": ROOT_DELEGATION,
                "validity": ROOT_VALIDITY,
            }
        )
        ok, violations = verify_delegation_chain([root, child])
        assert ok is False
        assert any("hop 1: max_transaction_value" in v for v in violations)

    def test_broken_parent_hash_linkage_fails(self):
        root, child, _ = sign_pair({"scope": SHRUNK_SCOPE})
        child["parent_charter_hash"] = "0" * 64

        ok, violations = verify_delegation_chain([root, child])
        assert ok is False
        assert any("chain linkage" in v for v in violations)

    def test_missing_linkage_is_unspecified(self):
        root = make_charter("charter:root")
        child = make_charter("charter:child", scope=SHRUNK_SCOPE)
        ok, violations = verify_delegation_chain([root, child])
        assert ok is False
        assert any("chain linkage: unspecified" in v for v in violations)
