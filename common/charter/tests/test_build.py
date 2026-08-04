"""build_charter: emerge.yaml manifest → AAC charter dict."""

from __future__ import annotations

from charter.build import build_charter
from charter.model import AACCharter
from helpers import AGENT_IDENTITY, ISSUER

# RFC-0001-era (emerge/1.1) manifest: no AAC fields at all.
LEGACY_MANIFEST = {
    "schema_version": "1.1",
    "identity": {
        "id": "did:orcha:agent:fixture-payments-agent",
        "name": "Fixture Payments Agent",
        "version": "1.0.0",
        "description": "Synthetic fixture agent.",
    },
    "authorized_scope": {
        "allowed_capabilities": ["initiate_payment", "query_balance"],
        "spend_cap_usd": "5000.00",
        "allowed_counterparties": ["did:orcha:agent:acme-billing"],
        "jurisdictions": ["GB", "EU"],
    },
}

# emerge/1.2 manifest with the AAC sub-fields (RFC 0002).
AAC_MANIFEST = {
    **LEGACY_MANIFEST,
    "schema_version": "1.2",
    "authorized_scope": {
        **LEGACY_MANIFEST["authorized_scope"],
        "rails": ["UPI", "AccountAggregator"],
        "delegation": {"allowed": True, "max_depth": 2},
        "human_approval_required_above": "1000.00",
        "validity": {"not_after": "2027-08-01T00:00:00Z"},
    },
}


class TestBuildCharter:
    def test_legacy_manifest_builds_with_absent_optional_blocks(self):
        charter = build_charter(
            LEGACY_MANIFEST, issuer=ISSUER, agent_identity=AGENT_IDENTITY
        )

        assert charter["issued_by"]["legal_name"] == "Example Finserv Pvt Ltd"
        assert charter["agent_identity"]["agent_id"] == AGENT_IDENTITY["agent_id"]
        scope = charter["authorized_scope"]
        assert scope["permitted_actions"] == ["initiate_payment", "query_balance"]
        assert scope["max_transaction_value"] == "5000.00"
        assert scope["allowed_counterparties"] == ["did:orcha:agent:acme-billing"]
        assert scope["jurisdictions"] == ["GB", "EU"]
        assert scope["dpi_rails"] == []
        # Absent optional blocks stay absent — "unspecified", not "unrestricted".
        assert "delegation" not in charter
        assert "validity" not in charter
        assert "operator_signature" not in charter
        AACCharter(**charter)

    def test_aac_manifest_maps_new_fields(self):
        charter = build_charter(
            AAC_MANIFEST,
            issuer=ISSUER,
            agent_identity=AGENT_IDENTITY,
            now="2026-08-01T00:00:00Z",
        )

        scope = charter["authorized_scope"]
        assert scope["dpi_rails"] == ["UPI", "AccountAggregator"]
        assert scope["human_approval_required_above"] == "1000.00"
        assert charter["delegation"] == {"allowed": True, "max_depth": 2}
        # `now` fills the missing not_before of a declared validity block.
        assert charter["validity"] == {
            "not_before": "2026-08-01T00:00:00Z",
            "not_after": "2027-08-01T00:00:00Z",
        }
        AACCharter(**charter)

    def test_agent_id_defaults_from_manifest_identity(self):
        charter = build_charter(LEGACY_MANIFEST, issuer=ISSUER, agent_identity={})
        assert (
            charter["agent_identity"]["agent_id"]
            == "did:orcha:agent:fixture-payments-agent"
        )

    def test_agent_public_key_is_additive_and_optional(self):
        # Absent on old charters — "unspecified", never a validation error.
        charter = build_charter(
            LEGACY_MANIFEST, issuer=ISSUER, agent_identity=AGENT_IDENTITY
        )
        assert AACCharter(**charter).agent_identity.agent_public_key is None

        # Present when the issuer binds a holder key (FR-4 holder binding).
        bound = build_charter(
            LEGACY_MANIFEST,
            issuer=ISSUER,
            agent_identity={**AGENT_IDENTITY, "agent_public_key": "b64pub"},
        )
        assert AACCharter(**bound).agent_identity.agent_public_key == "b64pub"
