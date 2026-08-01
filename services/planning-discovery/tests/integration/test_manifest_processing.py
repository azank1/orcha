"""Integration tests for manifest processing pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from planning_discovery.manifest_processing.embedding_generator import (
    TDWA_WEIGHTS,
    TDWAEmbeddingGenerator,
)
from planning_discovery.manifest_processing.template_generator import (
    SemanticTemplateGenerator,
)


@pytest.mark.integration
class TestManifestProcessingIntegration:
    """Integration tests for manifest processing components."""

    def test_template_and_embedding_flow(self, crypto_oracle_manifest: dict) -> None:
        """Test complete flow from template to embedding preparation."""
        template_gen = SemanticTemplateGenerator()
        semantic_string = template_gen.generate(crypto_oracle_manifest)

        assert "CryptoOracle" in semantic_string
        assert "crypto" in semantic_string
        assert "Get Crypto Price" in semantic_string
        assert len(semantic_string) > 50

        # TDWA weights must sum to 1.0
        assert abs(sum(TDWA_WEIGHTS.values()) - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_embedding_generation_with_mock_llm(
        self, mock_llm_provider: MagicMock, crypto_oracle_manifest: dict
    ) -> None:
        """Test embedding generation with mocked LLM."""
        mock_llm_provider.embed = AsyncMock(return_value=[0.1] * 1536)
        embedding_gen = TDWAEmbeddingGenerator(mock_llm_provider, "test-model")

        result = await embedding_gen.generate(crypto_oracle_manifest)

        assert isinstance(result, dict)
        assert "combined" in result
        assert len(result["combined"]) == 1536
        assert mock_llm_provider.embed.called

    def test_multiple_manifests_processing(
        self,
        minimal_agent_manifest: dict,
        crypto_oracle_manifest: dict,
        payment_agent_manifest: dict,
    ) -> None:
        """Test processing multiple different agent manifests."""
        generator = SemanticTemplateGenerator()

        templates = [
            generator.generate(minimal_agent_manifest),
            generator.generate(crypto_oracle_manifest),
            generator.generate(payment_agent_manifest),
        ]

        assert all(len(t) > 20 for t in templates)
        assert "MinimalAgent" in templates[0]
        assert "CryptoOracle" in templates[1]
        assert "PaymentProcessor" in templates[2]
        assert templates[0] != templates[1]
        assert templates[1] != templates[2]
