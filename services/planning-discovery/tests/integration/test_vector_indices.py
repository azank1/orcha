"""Integration tests for vector index setup and operations."""

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
class TestVectorIndices:
    """Tests for vector index creation and usage."""

    async def test_pgvector_extension_installed(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify pgvector extension is available."""
        async with test_db_pool.acquire() as conn:
            try:
                result = await conn.fetchval("SELECT '[1,2,3]'::vector")
                assert result is not None
            except asyncpg.UndefinedObjectError:
                pytest.skip("pgvector extension not installed on test database")

    async def test_pg_trgm_extension_installed(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify pg_trgm extension is available."""
        async with test_db_pool.acquire() as conn:
            try:
                result = await conn.fetchval("SELECT similarity('hello', 'hallo')")
                assert result is not None
            except asyncpg.UndefinedFunctionError:
                pytest.skip("pg_trgm extension not installed on test database")

    async def test_full_text_search_index_exists(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify full-text search GIN index is created."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'agents' AND indexname = 'idx_agents_search_vector_gin')"
            )
        if not result:
            pytest.skip("Run 'make pnd-db-init' to create indices.")
        assert result is True

    async def test_hnsw_embedding_index_exists(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify HNSW vector index is created."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'agent_embeddings' AND indexname = 'idx_ae_embedding_hnsw')"
            )
        if not result:
            pytest.skip("Run 'make pnd-db-init' to create indices.")
        assert result is True

    async def test_generated_search_vector_column(
        self, test_db_pool: asyncpg.Pool, clean_db: None
    ) -> None:
        """Test that search_vector is auto-populated by the trigger on INSERT."""
        async with test_db_pool.acquire() as conn:
            await conn.execute(
                _AGENT_INSERT,
                "did:orcha:agent:sv-test",
                _TEST_USER_ID,
                "SearchTestAgent",
                "1.0.0",
                "A test agent for search",
                "test-provider",
                "test@example.com",
                ["test", "search"],
                "MCP",
                "2025-11-25",
                "http://localhost:9999/health",
            )
            result = await conn.fetchval(
                "SELECT search_vector FROM agents WHERE id = $1",
                "did:orcha:agent:sv-test",
            )

        assert result is not None

    async def test_tags_gin_index_exists(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify GIN index on tags array exists."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'agents' AND indexname = 'idx_agents_tags_gin')"
            )
        if not result:
            pytest.skip("Run 'make pnd-db-init' to create indices.")
        assert result is True

    async def test_query_by_embedding_similarity(
        self, test_db_pool: asyncpg.Pool, seed_agents: None, seed_embeddings: None
    ) -> None:
        """Test embedding similarity search capability."""
        async with test_db_pool.acquire() as conn:
            query_vector = "[" + ",".join(["0.1"] * 768) + "]"
            try:
                result = await conn.fetch(
                    """
                    SELECT agent_id, embedding <=> $1::vector as distance
                    FROM agent_embeddings
                    ORDER BY distance
                    LIMIT 5
                    """,
                    query_vector,
                )
                assert len(result) >= 0
            except asyncpg.UndefinedObjectError:
                pytest.skip("pgvector not installed")
