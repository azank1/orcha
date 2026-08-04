"""
asyncpg connection pool for raw SQL operations (pgvector queries).

Prisma does not support pgvector operations natively, so vector inserts,
upserts, and HNSW similarity searches use the asyncpg pool directly.
"""

from __future__ import annotations

import logging

import asyncpg

logger = logging.getLogger(__name__)


class AsyncpgPool:
    """
    Wrapper around an asyncpg connection pool.

    Usage::

        pool = AsyncpgPool(dsn="postgresql://...", min_size=10, max_size=20)
        await pool.connect()

        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM agents")

        await pool.disconnect()
    """

    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 20) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create the connection pool."""
        self._pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            command_timeout=30,
            server_settings={
                "jit": "off",  # Disable JIT — improves vector op stability
                "work_mem": "256MB",  # Larger working memory for complex queries
            },
        )
        logger.info(
            "asyncpg pool connected (min=%d, max=%d)", self._min_size, self._max_size
        )

    async def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("asyncpg pool disconnected")

    def acquire(self) -> asyncpg.pool.PoolConnectionProxy:  # type: ignore[type-arg]
        """Acquire a connection from the pool (async context manager)."""
        if self._pool is None:
            raise RuntimeError("AsyncpgPool is not connected — call connect() first")
        return self._pool.acquire()  # type: ignore[return-value]

    async def fetch(self, query: str, *args: object) -> list[asyncpg.Record]:
        """Execute a query and return all rows."""
        if self._pool is None:
            raise RuntimeError("AsyncpgPool is not connected")
        return await self._pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args: object) -> asyncpg.Record | None:
        """Execute a query and return a single row."""
        if self._pool is None:
            raise RuntimeError("AsyncpgPool is not connected")
        return await self._pool.fetchrow(query, *args)

    async def execute(self, query: str, *args: object) -> str:
        """Execute a query and return the status string."""
        if self._pool is None:
            raise RuntimeError("AsyncpgPool is not connected")
        return await self._pool.execute(query, *args)
