"""Unit tests for keyword extraction."""

from __future__ import annotations

import pytest
from planning_discovery.planning.resolution.keyword_extractor import extract_keywords

pytestmark = pytest.mark.unit


class TestKeywordExtraction:
    """Tests for extracting search keywords from queries."""

    def test_simple_query_extraction(self) -> None:
        """Test keyword extraction from simple query."""
        keywords = extract_keywords("Get ETH price on Ethereum")

        assert len(keywords) > 0
        assert any(kw.lower() in ["eth", "ethereum", "price"] for kw in keywords)

    def test_complex_query_extraction(self) -> None:
        """Test extraction from query with conditionals."""
        keywords = extract_keywords(
            "Fetch ETH price. If below $2800, analyze RSI and volume."
        )

        assert len(keywords) > 0
        assert any(
            term in " ".join(keywords).lower()
            for term in ["eth", "price", "rsi", "volume"]
        )

    def test_empty_query(self) -> None:
        """Test with empty query."""
        keywords = extract_keywords("")
        assert isinstance(keywords, list)

    def test_special_characters_handling(self) -> None:
        """Test handling of special characters."""
        keywords = extract_keywords("Get $USDC price on @Ethereum")

        assert isinstance(keywords, list)
        # Non-alpha tokens are filtered — result may be empty, which is fine
        for kw in keywords:
            assert kw.isalpha()

    def test_stopwords_filtered(self) -> None:
        """Test that stopwords are removed."""
        keywords = extract_keywords("get the price of eth on the chain")

        # 'the', 'of', 'on' are stopwords and should be absent
        assert "the" not in keywords
        assert "of" not in keywords
        assert "on" not in keywords

    def test_returns_list(self) -> None:
        """Return type is always a list of strings."""
        keywords = extract_keywords("ETH price on Ethereum")
        assert isinstance(keywords, list)
        assert all(isinstance(kw, str) for kw in keywords)
