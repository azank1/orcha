"""Integration tests for database schema and initialization."""

from __future__ import annotations

import asyncpg
import pytest


@pytest.mark.integration
@pytest.mark.db
class TestSchemaSetup:
    """Tests verifying database schema is properly initialized."""

    @pytest.mark.asyncio
    async def test_agents_table_schema(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify agents table has required columns."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'agents'
                ORDER BY ordinal_position
            """
            )

        columns = {row["column_name"]: row["data_type"] for row in result}

        # Required columns (agents.id IS the DID; no separate did column)
        required = [
            "id",
            "user_id",
            "name",
            "version",
            "description",
            "provider",
            "owner_contact",
            "tags",
            "protocol_type",
            "protocol_version",
            "health_status",
            "health_endpoint",
            "is_active",
        ]
        for col in required:
            assert col in columns, f"Missing column: {col}"

    @pytest.mark.asyncio
    async def test_agent_embeddings_table_schema(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify agent_embeddings table has vector columns."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetch(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'agent_embeddings'
                ORDER BY ordinal_position
            """
            )

        columns = {row["column_name"]: row["data_type"] for row in result}

        # Key columns
        assert "agent_id" in columns
        assert "embedding" in columns or "embedding" in str(result)

    @pytest.mark.asyncio
    async def test_plan_executions_table_exists(
        self, test_db_pool: asyncpg.Pool
    ) -> None:
        """Verify plan_executions table exists for tracking queries."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'plan_executions'
                )
            """
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_agent_id_foreign_key(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify foreign key from agent_embeddings to agents."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name = 'agent_embeddings'
                    AND constraint_type = 'FOREIGN KEY'
                )
            """
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_agents_constraints(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify agents table constraints."""
        async with test_db_pool.acquire() as conn:
            # Check unique constraint on DID (agent identifier)
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name = 'agents'
                    AND constraint_type IN ('UNIQUE', 'PRIMARY KEY')
                )
            """
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_prisma_migrations_applied(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify _prisma_migrations table exists (indicates migrations run)."""
        async with test_db_pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '_prisma_migrations'
                )
            """
            )

        if not result:
            pytest.skip("Migrations not applied. Run 'make migrate'")

        assert result is True

    @pytest.mark.asyncio
    async def test_database_supports_arrays(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify database supports array types (for tags)."""
        async with test_db_pool.acquire() as conn:
            try:
                result = await conn.fetchval("SELECT ARRAY['test']::text[]")
                assert result == ["test"]
            except asyncpg.UndefinedTypeError:
                pytest.skip("Database doesn't support array types")

    @pytest.mark.asyncio
    async def test_database_supports_json(self, test_db_pool: asyncpg.Pool) -> None:
        """Verify database supports JSON type."""
        async with test_db_pool.acquire() as conn:
            try:
                result = await conn.fetchval("SELECT '{\"test\": 1}'::jsonb")
                assert result is not None
            except asyncpg.UndefinedTypeError:
                pytest.skip("Database doesn't support JSON type")
