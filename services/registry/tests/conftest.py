"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from common.database.src.generated_client import Prisma
from dotenv import load_dotenv

# Load test environment variables
TEST_ENV_FILE = Path(__file__).parent.parent / ".env.test"
load_dotenv(TEST_ENV_FILE)

# Test data directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db() -> AsyncGenerator[Prisma, None]:
    """
    Provide a mocked database client.

    In real integration tests, this would connect to a test database.
    For unit tests, we mock the database operations.
    """
    db = MagicMock(spec=Prisma)

    # Mock common database operations
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.agent = MagicMock()
    db.user = MagicMock()
    db.transport = MagicMock()
    db.security = MagicMock()
    db.authstrategy = MagicMock()
    db.payment = MagicMock()
    db.capability = MagicMock()
    db.agentversion = MagicMock()

    yield db


@pytest.fixture
def mcp_emerge_yaml() -> str:
    """Load MCP emerge.yaml fixture."""
    return (FIXTURES_DIR / "mcp_emerge.yaml").read_text()


@pytest.fixture
def a2a_emerge_yaml() -> str:
    """Load A2A emerge.yaml fixture."""
    return (FIXTURES_DIR / "a2a_emerge.yaml").read_text()


@pytest.fixture
def invalid_emerge_yaml() -> str:
    """Load invalid emerge.yaml fixture."""
    return (FIXTURES_DIR / "invalid_emerge.yaml").read_text()


@pytest.fixture
def test_user_id() -> str:
    """Test user ID."""
    return "test_user_123"


@pytest.fixture
def mock_mcp_tools_response():
    """Mock MCP tools/list response."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {
                    "name": "get_stock_price",
                    "description": "Get current stock price",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"symbol": {"type": "string"}},
                        "required": ["symbol"],
                    },
                },
                {
                    "name": "analyze_market",
                    "description": "Analyze market trends",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"sector": {"type": "string"}},
                    },
                    "metadata": {"x402": {"price": "25", "asset": "USDC"}},
                },
            ]
        },
    }


@pytest.fixture
def mock_mcp_resources_response():
    """Mock MCP resources/list response."""
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "resources": [
                {
                    "uri": "file:///data/stocks/AAPL.json",
                    "name": "Apple Stock Data",
                    "description": "Real-time Apple stock data",
                    "mimeType": "application/json",
                }
            ]
        },
    }


@pytest.fixture
def mock_mcp_prompts_response():
    """Mock MCP prompts/list response."""
    return {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "prompts": [
                {
                    "name": "market_analysis",
                    "description": "Generate market analysis report",
                    "arguments": [
                        {
                            "name": "sector",
                            "description": "Market sector to analyze",
                            "required": True,
                        }
                    ],
                }
            ]
        },
    }


@pytest.fixture
def mock_a2a_agent_card():
    """Mock A2A Agent Card."""
    return {
        "schemaVersion": "1.0",
        "name": "TestA2AAgent",
        "description": "A test A2A agent",
        "url": "https://api.example.com/a2a",
        "provider": "TestProvider",
        "tags": ["test", "finance"],
        "authSchemes": [
            {
                "scheme": "apiKey",
                "service_identifier": "test-service",
                "description": "API Key authentication",
            },
            {
                "scheme": "oauth2",
                "tokenUrl": "https://auth.example.com/token",
                "scopes": ["read", "write"],
            },
        ],
        "skills": [
            {
                "id": "calculate_portfolio",
                "name": "Calculate Portfolio Value",
                "description": "Calculate total portfolio value",
                "input_schema": {
                    "type": "object",
                    "properties": {"holdings": {"type": "array"}},
                },
                "output_schema": {
                    "type": "object",
                    "properties": {"total_value": {"type": "number"}},
                },
            },
            {
                "id": "get_market_data",
                "name": "Get Market Data",
                "description": "Retrieve market data",
                "input_schema": {
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                },
            },
        ],
    }


@pytest.fixture
def mock_agent_record():
    """Mock agent database record."""
    from datetime import datetime

    agent = MagicMock()
    agent.id = "did:orcha:agent:test-agent"
    agent.user_id = "test_user_123"
    agent.name = "TestAgent"
    agent.version = "1.0.0"
    agent.description = "A test agent"
    agent.provider = "TestProvider"
    agent.owner_contact = "test@example.com"
    agent.tags = ["test"]
    agent.protocol_type = "MCP"
    agent.protocol_version = "2025-11-25"
    agent.health_status = "UNKNOWN"
    agent.health_endpoint = "https://api.example.com/health"
    agent.health_failures = 0
    agent.last_health_check = None
    agent.indexed_at = datetime.now(UTC)
    agent.updated_at = datetime.now(UTC)
    agent.is_active = True

    return agent
