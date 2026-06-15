"""Integration tests for database operations."""

from __future__ import annotations

import asyncpg
import pytest

from tests.conftest import _TEST_USER_ID

_AGENT_INSERT = """
    INSERT INTO agents (
        id, user_id, name, version, description, provider, owner_contact,
        tags, protocol_type, protocol_version, health_endpoint, updated_at
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
"""


@pytest.mark.integration
@pytest.mark.db
class TestDatabaseOperations:
    """Tests for database connectivity and operations."""

    async def test_db_connection(self, test_db_pool: asyncpg.Pool) -> None:
        """Test basic database connection."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
        assert result == 1

    async def test_agents_table_exists(self, test_db_pool: asyncpg.Pool) -> None:
        """Test that agents table exists."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agents')"
            )
        assert result is True

    async def test_agent_embeddings_table_exists(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Test that agent_embeddings table exists."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_embeddings')"
            )
        assert result is True

    async def test_insert_and_retrieve_agent(
        self, test_db_pool: asyncpg.Pool, clean_db: None
    ) -> None:
        """Test inserting and retrieving an agent."""
        async with test_db_pool.acquire() as conn:
            await conn.execute(
                _AGENT_INSERT,
                "did:emerge:agent:test-001",
                _TEST_USER_ID,
                "TestAgent",
                "1.0.0",
                "A test agent",
                "test-provider",
                "test@example.com",
                ["test"],
                "MCP",
                "2025-11-25",
                "http://localhost:9999/health",
            )
            result = await conn.fetchrow(
                "SELECT * FROM agents WHERE id = $1", "did:emerge:agent:test-001"
            )

        assert result is not None
        assert result["name"] == "TestAgent"
        assert result["is_active"] is True

    async def test_vector_extension_available(self, test_db_pool: asyncpg.Pool) -> None:
        """Test that pgvector extension is available."""
        async with test_db_pool.acquire() as conn:
            try:
                result = await conn.fetchval("SELECT '[1,2,3]'::vector")
                assert result is not None
            except asyncpg.UndefinedObjectError:
                pytest.skip("pgvector extension not installed")

    async def test_full_text_search_vector_column(
        self, test_db_pool: asyncpg.Pool, clean_db: None
    ) -> None:
        """Test full-text search vector column is auto-populated by trigger."""
        async with test_db_pool.acquire() as conn:
            await conn.execute(
                _AGENT_INSERT,
                "did:emerge:agent:fts-001",
                _TEST_USER_ID,
                "CryptoOracle",
                "1.0.0",
                "Provides cryptocurrency price data",
                "test-provider",
                "test@example.com",
                ["crypto", "price"],
                "MCP",
                "2025-11-25",
                "http://localhost:9999/health",
            )
            result = await conn.fetchval(
                "SELECT search_vector FROM agents WHERE id = $1",
                "did:emerge:agent:fts-001",
            )

        assert result is not None

    async def test_agent_filtering_by_tags(
        self, test_db_pool: asyncpg.Pool, seed_agents: None
    ) -> None:
        """Test filtering agents by tags."""
        async with test_db_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT id, name FROM agents WHERE $1 = ANY(tags) ORDER BY id",
                "crypto",
            )

        assert len(results) > 0
        assert any(r["name"] == "CryptoOracle" for r in results)

    async def test_agent_filtering_by_protocol(
        self, test_db_pool: asyncpg.Pool, seed_agents: None
    ) -> None:
        """Test filtering agents by protocol type."""
        async with test_db_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT id, name, protocol_type FROM agents WHERE protocol_type = $1 AND is_active = true ORDER BY id",
                "MCP",
            )

        assert len(results) > 0
        assert all(r["protocol_type"] == "MCP" for r in results)
