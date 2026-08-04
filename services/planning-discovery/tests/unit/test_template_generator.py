"""Unit tests for TDWA semantic template generator."""

from __future__ import annotations

import pytest
from planning_discovery.manifest_processing.normalizer import normalize_manifest
from planning_discovery.manifest_processing.template_generator import (
    SemanticTemplateGenerator,
)

pytestmark = pytest.mark.unit


class TestSemanticTemplateGenerator:
    """Tests for semantic template generation."""

    def test_generate_minimal_template(self, minimal_agent_manifest: dict) -> None:
        """Test template generation with minimal manifest."""
        generator = SemanticTemplateGenerator()
        result = generator.generate(minimal_agent_manifest)

        assert "Agent: MinimalAgent" in result
        assert "Role: A minimal test agent" in result
        assert "Protocol: MCP" in result
        assert "test" in result

    def test_generate_full_template(self, crypto_oracle_manifest: dict) -> None:
        """Test template generation with full manifest."""
        generator = SemanticTemplateGenerator()
        result = generator.generate(crypto_oracle_manifest)

        assert "Agent: CryptoOracle" in result
        assert "crypto" in result
        assert "defi" in result
        assert "Get Crypto Price" in result

    def test_format_capabilities(self, crypto_oracle_manifest: dict) -> None:
        """Test capability formatting."""
        generator = SemanticTemplateGenerator()
        manifest = normalize_manifest(crypto_oracle_manifest)
        result = generator._format_capabilities(manifest.capabilities)

        assert "TOOL named Get Crypto Price" in result
        assert "symbol" in result
        assert "network" in result

    def test_extract_networks(self, crypto_oracle_manifest: dict) -> None:
        """Test network extraction from capabilities."""
        generator = SemanticTemplateGenerator()
        manifest = normalize_manifest(crypto_oracle_manifest)
        networks = generator._extract_networks(manifest.capabilities)

        assert "ETHEREUM" in networks
        assert "BASE" in networks
        assert networks == sorted(networks)  # Verify sorting

    def test_extract_networks_with_chain(self, payment_agent_manifest: dict) -> None:
        """Test network extraction from 'chain' field."""
        generator = SemanticTemplateGenerator()
        manifest = normalize_manifest(payment_agent_manifest)
        networks = generator._extract_networks(manifest.capabilities)

        assert "ETHEREUM" in networks
        assert "POLYGON" in networks

    def test_extract_networks_none(self, minimal_agent_manifest: dict) -> None:
        """Test network extraction with no capabilities."""
        generator = SemanticTemplateGenerator()
        manifest = normalize_manifest(minimal_agent_manifest)
        networks = generator._extract_networks(manifest.capabilities)

        assert networks == []

    def test_calculate_reliability_none(self, minimal_agent_manifest: dict) -> None:
        """Test reliability calculation (currently None)."""
        generator = SemanticTemplateGenerator()
        reliability = generator._calculate_reliability(minimal_agent_manifest)

        assert reliability is None

    def test_empty_capability_list(self) -> None:
        """Test with manifest having empty capabilities."""
        manifest = {
            "identity": {"name": "Test", "description": "Test", "tags": []},
            "protocol": {"type": "mcp"},
            "capabilities": [],
        }
        generator = SemanticTemplateGenerator()
        result = generator.generate(manifest)

        assert "Agent: Test" in result
        assert "Integrated Skills: none" in result
