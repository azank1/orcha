"""Initialise PnD vector indices in PostgreSQL.

Usage::

    python -m services.planning-discovery.scripts.db.initialize_database

Or via Make::

    make pnd-db-init

Reads DATABASE_URL from the environment (or .env file if python-dotenv is
available).  Runs ``001_create_vector_indices.sql`` against the database.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)

_SQL_FILE = Path(__file__).parent / "001_create_vector_indices.sql"


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try loading from service .env files (best-effort, not a hard dependency)
        # parents[2] = services/planning-discovery/
        service_root = Path(__file__).parents[2]
        env_environment = os.getenv("ENVIRONMENT", "development")
        for candidate in (
            service_root / f".env.{env_environment}",
            service_root / ".env",
        ):
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        database_url = (
                            line.split("=", 1)[1].strip().strip('"').strip("'")
                        )
                        break
            if database_url:
                break

    if not database_url:
        logger.error(
            "DATABASE_URL is not set. Export it or create a .env file in the service root."
        )
        sys.exit(1)

    sql = _SQL_FILE.read_text()

    logger.info("Connecting to database…")
    conn: asyncpg.Connection = await asyncpg.connect(dsn=database_url)

    try:
        logger.info("Executing %s…", _SQL_FILE.name)
        await conn.execute(sql)
        logger.info("Vector indices created / verified successfully")
    finally:
        await conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(main())
