"""Tests for authorized_scope (emerge/1.1, RFC 0001)."""

import json
from pathlib import Path

import yaml
from jsonschema import validate

from services.registry.src.models.emerge_config import EmergeConfig
from services.registry.src.services.validation import ValidationService

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "spec" / "emerge-yaml.schema.json"
)

BASE_CONFIG = {
    "identity": {
        "id": "did:orcha:agent:scoped-agent",
        "name": "ScopedAgent",
        "version": "1.0.0",
        "description": "Agent with a declared authorised scope",
    },
    "protocol": {
        "type": "a2a",
        "version": "0.3",
        "transport": {"type": "http", "endpoint": "https://agent.example.com"},
    },
    "health_endpoint": "https://agent.example.com/health",
    "security": {"transport_layer": {"type": "tls"}, "auth_strategies": []},
}

SCOPE_BLOCK = {
    "allowed_capabilities": ["search_docs", "summarize"],
    "spend_cap_usd": "5000.00",
    "allowed_counterparties": ["did:orcha:agent:acme-billing"],
    "jurisdictions": ["GB", "EU"],
}


class TestAuthorizedScope:
    """Parsing, validation, and backward compatibility of authorized_scope."""

    def test_manifest_without_scope_remains_valid(self):
        """emerge/1.0 manifests (no authorized_scope) stay valid — backward compat."""
        config = EmergeConfig(**BASE_CONFIG)
        assert config.authorized_scope is None

        is_valid, error = ValidationService.validate_emerge_config(config)
        assert is_valid is True
        assert error is None

    def test_manifest_with_scope_parses(self):
        """The block parses into typed fields."""
        config = EmergeConfig(**{**BASE_CONFIG, "authorized_scope": SCOPE_BLOCK})

        scope = config.authorized_scope
        assert scope is not None
        assert scope.allowed_capabilities == ["search_docs", "summarize"]
        assert scope.spend_cap_usd == "5000.00"
        assert scope.allowed_counterparties == ["did:orcha:agent:acme-billing"]
        assert scope.jurisdictions == ["GB", "EU"]

    def test_scope_subfields_optional(self):
        """A partial block is valid; omitted sub-fields default sensibly."""
        config = EmergeConfig(
            **{**BASE_CONFIG, "authorized_scope": {"spend_cap_usd": "100.00"}}
        )
        scope = config.authorized_scope
        assert scope is not None
        assert scope.spend_cap_usd == "100.00"
        assert scope.allowed_capabilities == []
        assert scope.allowed_counterparties == []
        assert scope.jurisdictions == []

    def test_json_schema_validates_with_and_without_scope(self):
        """The canonical JSON Schema accepts both shapes (FR-2.3)."""
        schema = json.loads(SCHEMA_PATH.read_text())
        validate(yaml.safe_load(yaml.dump(BASE_CONFIG)), schema)
        validate(
            yaml.safe_load(yaml.dump({**BASE_CONFIG, "authorized_scope": SCOPE_BLOCK})),
            schema,
        )

    def test_fleet_manifests_unchanged_and_valid(self):
        """Existing fleet manifests have no authorized_scope and still validate."""
        schema = json.loads(SCHEMA_PATH.read_text())
        fleet_dir = Path(__file__).resolve().parents[3] / "agents"
        manifests = sorted(fleet_dir.glob("*/emerge.yaml"))
        assert manifests, "expected at least one fleet emerge.yaml"
        for manifest in manifests:
            data = yaml.safe_load(manifest.read_text())
            validate(data, schema)


AAC_SCOPE_BLOCK = {
    "principal": {
        "legal_name": "Example Finserv Pvt Ltd",
        "identifier_type": "CIN",
        "identifier_value": "U72900MH2020PTC000000",
        "regulator_license": "NBFC-2024-0000",
    },
    "rails": ["UPI", "AccountAggregator"],
    "delegation": {"allowed": True, "max_depth": 2},
    "human_approval_required_above": "1000.00",
    "validity": {
        "not_before": "2026-08-01T00:00:00Z",
        "not_after": "2027-08-01T00:00:00Z",
    },
}


class TestAACCharterFields:
    """AAC charter sub-fields on authorized_scope (emerge/1.2, RFC 0002)."""

    def test_aac_fields_parse(self):
        """The full 1.2 block parses into typed nested models."""
        config = EmergeConfig(
            **{**BASE_CONFIG, "authorized_scope": {**SCOPE_BLOCK, **AAC_SCOPE_BLOCK}}
        )
        scope = config.authorized_scope
        assert scope is not None
        assert scope.principal is not None
        assert scope.principal.legal_name == "Example Finserv Pvt Ltd"
        assert scope.principal.identifier_type == "CIN"
        assert scope.principal.regulator_license == "NBFC-2024-0000"
        assert scope.rails == ["UPI", "AccountAggregator"]
        assert scope.delegation is not None
        assert scope.delegation.allowed is True
        assert scope.delegation.max_depth == 2
        assert scope.human_approval_required_above == "1000.00"
        assert scope.validity is not None
        assert scope.validity.not_before == "2026-08-01T00:00:00Z"
        assert scope.validity.not_after == "2027-08-01T00:00:00Z"

    def test_partial_aac_blocks_validate(self):
        """Partial blocks default sensibly; regulator_license is optional."""
        config = EmergeConfig(
            **{
                **BASE_CONFIG,
                "authorized_scope": {
                    "principal": {
                        "legal_name": "Example Pte Ltd",
                        "identifier_type": "UEN",
                        "identifier_value": "202000000A",
                    },
                    "delegation": {"allowed": True},
                },
            }
        )
        scope = config.authorized_scope
        assert scope is not None
        assert scope.principal is not None
        assert scope.principal.regulator_license is None
        assert scope.delegation is not None
        assert scope.delegation.max_depth == 0
        assert scope.rails == []
        assert scope.validity is None

    def test_json_schema_validates_with_and_without_aac_fields(self):
        """The 1.2 JSON Schema accepts manifests with and without the new fields."""
        schema = json.loads(SCHEMA_PATH.read_text())
        validate(
            yaml.safe_load(yaml.dump({**BASE_CONFIG, "authorized_scope": SCOPE_BLOCK})),
            schema,
        )
        validate(
            yaml.safe_load(
                yaml.dump(
                    {
                        **BASE_CONFIG,
                        "schema_version": "1.2",
                        "authorized_scope": {**SCOPE_BLOCK, **AAC_SCOPE_BLOCK},
                    }
                )
            ),
            schema,
        )
