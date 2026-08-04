"""Test configuration and shared fixtures for Planning & Discovery service."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import asyncpg
import pytest
import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load test environment
_env_file = Path(__file__).parent.parent / ".env.test"
if _env_file.exists():
    load_dotenv(_env_file)

# Fallback to main .env if test-specific doesn't exist
if not os.getenv("DATABASE_URL"):
    _main_env = Path(__file__).parent.parent.parent.parent / ".env"
    if _main_env.exists():
        load_dotenv(_main_env)

# Stable test user used by all DB fixtures
_TEST_USER_ID = "test-user-fixture-001"
_TEST_USER_EMAIL = "fixture@orcha.test"


async def _ensure_test_user(conn: asyncpg.Connection) -> None:
    """Insert the shared test user if it doesn't already exist."""
    await conn.execute(
        """
        INSERT INTO users (id, email, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (id) DO NOTHING
        """,
        _TEST_USER_ID,
        _TEST_USER_EMAIL,
    )


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get test database URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture
async def test_db_pool(test_db_url: str) -> AsyncGenerator[asyncpg.Pool, None]:
    """Create database connection pool for tests."""
    pool = await asyncpg.create_pool(
        dsn=test_db_url, min_size=2, max_size=5, command_timeout=10
    )
    try:
        yield pool
    finally:
        await pool.close()


@pytest.fixture
async def clean_db(test_db_pool: asyncpg.Pool) -> AsyncGenerator[None, None]:
    """Clean agent-related tables and ensure the test user exists."""
    async with test_db_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE plan_executions, agent_embeddings, agents RESTART IDENTITY CASCADE"
        )
        await _ensure_test_user(conn)
    yield
    async with test_db_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE plan_executions, agent_embeddings, agents RESTART IDENTITY CASCADE"
        )


@pytest.fixture
async def db_conn(
    test_db_pool: asyncpg.Pool,
) -> AsyncGenerator[asyncpg.Connection, None]:
    """Get single database connection for a test."""
    async with test_db_pool.acquire() as conn:
        yield conn


@pytest.fixture
def mock_db_pool() -> AsyncMock:
    """Mock asyncpg pool for unit tests."""
    return AsyncMock(spec=asyncpg.Pool)


# ============================================================================
# LLM PROVIDER MOCKS
# ============================================================================


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Mock LLM provider with deterministic responses."""
    mock = MagicMock()
    mock.embed = AsyncMock(return_value=[0.1] * 1536)
    mock.complete = AsyncMock(
        return_value='{"tasks": [], "edges": [], "metadata": {"confidence": 0.85}}'
    )
    return mock


# ============================================================================
# AGENT MANIFEST FIXTURES
# ============================================================================


@pytest.fixture
def minimal_agent_manifest() -> dict:
    """Minimal valid agent manifest."""
    return {
        "identity": {
            "id": "did:orcha:agent:test-minimal",
            "name": "MinimalAgent",
            "version": "1.0.0",
            "description": "A minimal test agent",
            "tags": ["test"],
        },
        "protocol": {"type": "mcp", "version": "2025-11-25"},
        "capabilities": [],
    }


@pytest.fixture
def crypto_oracle_manifest() -> dict:
    """Realistic crypto oracle agent manifest."""
    return {
        "identity": {
            "id": "did:orcha:agent:crypto-oracle",
            "name": "CryptoOracle",
            "version": "1.0.0",
            "description": "Real-time cryptocurrency price oracle",
            "tags": ["crypto", "defi", "price-feed", "oracle"],
        },
        "protocol": {"type": "mcp", "version": "2025-11-25"},
        "capabilities": [
            {
                "type": "TOOL",
                "capability_id": "get_crypto_price",
                "name": "Get Crypto Price",
                "description": "Fetches current market price for a cryptocurrency",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Crypto symbol (e.g., ETH)",
                        },
                        "network": {
                            "type": "string",
                            "enum": ["ETHEREUM", "BASE"],
                            "description": "Blockchain network",
                        },
                    },
                    "required": ["symbol"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "price": {"type": "number"},
                        "timestamp": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
            }
        ],
    }


@pytest.fixture
def payment_agent_manifest() -> dict:
    """Payment processor agent manifest."""
    return {
        "identity": {
            "id": "did:orcha:agent:payment-processor",
            "name": "PaymentProcessor",
            "version": "1.0.0",
            "description": "Processes payments across blockchains",
            "tags": ["payment", "x402", "defi"],
        },
        "protocol": {"type": "mcp", "version": "2025-11-25"},
        "capabilities": [
            {
                "type": "TOOL",
                "capability_id": "send_payment",
                "name": "Send Payment",
                "description": "Send payment to a recipient",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string"},
                        "amount": {"type": "number"},
                        "chain": {"type": "string", "enum": ["ETHEREUM", "POLYGON"]},
                    },
                    "required": ["recipient", "amount", "chain"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "tx_hash": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
            }
        ],
    }


@pytest.fixture
def load_registry_fixture(tmp_path: Path) -> dict:
    """Load agent manifest from registry fixtures."""
    fixture_path = (
        Path(__file__).parent.parent.parent / "registry/tests/fixtures/mcp_emerge.yaml"
    )
    if fixture_path.exists():
        with fixture_path.open() as f:
            return yaml.safe_load(f)
    return {
        "identity": {
            "name": "TestMCPAgent",
            "description": "A test MCP agent",
            "tags": ["test", "mcp"],
        },
        "protocol": {"type": "mcp", "version": "2025-11-25"},
        "capabilities": [],
    }


# ============================================================================
# DATABASE SEED FIXTURES
# ============================================================================


@pytest.fixture
async def seed_agents(
    test_db_pool: asyncpg.Pool,
    crypto_oracle_manifest: dict,
    payment_agent_manifest: dict,
) -> AsyncGenerator[None, None]:
    """Seed database with test agents (truncates first for isolation)."""
    async with test_db_pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE plan_executions, agent_embeddings, agents RESTART IDENTITY CASCADE"
        )
        await _ensure_test_user(conn)

        for manifest in [crypto_oracle_manifest, payment_agent_manifest]:
            identity = manifest["identity"]
            await conn.execute(
                """
                INSERT INTO agents (
                    id, user_id, name, version, description, provider, owner_contact,
                    tags, protocol_type, protocol_version, health_endpoint, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                ON CONFLICT (id) DO NOTHING
                """,
                identity["id"],
                _TEST_USER_ID,
                identity["name"],
                identity["version"],
                identity["description"],
                "test-provider",
                "test@example.com",
                identity["tags"],
                "MCP",
                manifest["protocol"]["version"],
                "http://localhost:9999/health",
            )
    yield


@pytest.fixture
async def seed_embeddings(
    test_db_pool: asyncpg.Pool, seed_agents: None
) -> AsyncGenerator[None, None]:
    """Seed database with agent embeddings."""
    import numpy as np

    async with test_db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name FROM agents ORDER BY id")

        for row in rows:
            agent_id = row["id"]
            embedding = np.random.RandomState(42).normal(0, 1, 768).tolist()
            vec = str(embedding)

            await conn.execute(
                """
                INSERT INTO agent_embeddings (
                    id, agent_id, templated_string,
                    embedding, name_embedding, description_embedding, capabilities_embedding,
                    updated_at
                )
                VALUES ($1, $2, $3, $4::vector, $5::vector, $6::vector, $7::vector, NOW())
                ON CONFLICT (agent_id) DO NOTHING
                """,
                str(uuid.uuid4()),
                agent_id,
                f"Agent: {row['name']}",
                vec,
                vec,
                vec,
                vec,
            )
    yield


# ============================================================================
# MOCKS & HELPERS
# ============================================================================


@pytest.fixture
def mock_kafka_producer() -> AsyncMock:
    """Mock Kafka producer."""
    return AsyncMock()


@pytest.fixture
def mock_kafka_consumer() -> AsyncMock:
    """Mock Kafka consumer."""
    mock = AsyncMock()
    mock.__aiter__.return_value = iter([])
    return mock


# ============================================================================
# PYTEST MARKERS & CONFIGURATION
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, mocked)")
    config.addinivalue_line("markers", "integration: Integration tests (may need DB)")
    config.addinivalue_line("markers", "db: Tests requiring real database")
    config.addinivalue_line("markers", "slow: Slow tests (>1s)")
