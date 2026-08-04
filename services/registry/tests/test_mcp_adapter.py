"""Tests for MCP adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.registry.src.adapters.mcp import MCPAdapter


class TestMCPAdapter:
    """Test suite for MCPAdapter."""

    @pytest.mark.asyncio
    async def test_harvest_successful(
        self,
        mock_mcp_tools_response,
        mock_mcp_resources_response,
        mock_mcp_prompts_response,
    ):
        """Test successful harvesting of MCP capabilities."""
        adapter = MCPAdapter(
            endpoint="https://api.example.com/mcp/sse", timeout=10, max_retries=3
        )

        # Mock the HTTP client
        with patch(
            "services.registry.src.adapters.mcp.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Mock responses for each endpoint
            responses = [
                mock_mcp_tools_response,
                mock_mcp_resources_response,
                mock_mcp_prompts_response,
            ]
            mock_response = MagicMock()
            mock_response.json = MagicMock(side_effect=responses)
            mock_response.raise_for_status = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)

            # Perform harvest
            result = await adapter.harvest()

        # Assertions
        assert len(result.capabilities) == 4  # 2 tools + 1 resource + 1 prompt
        assert len(result.errors) == 0

        # Check tools
        tools = [cap for cap in result.capabilities if cap.type == "tool"]
        assert len(tools) == 2
        assert tools[0].id == "get_stock_price"
        assert tools[0].name == "get_stock_price"
        assert tools[0].input_schema is not None

        # Check tool with x402 metadata
        analyze_tool = next((t for t in tools if t.id == "analyze_market"), None)
        assert analyze_tool is not None
        assert analyze_tool.x402_price == "25"
        assert analyze_tool.x402_asset == "USDC"

        # Check resources
        resources = [cap for cap in result.capabilities if cap.type == "resource"]
        assert len(resources) == 1
        assert resources[0].uri_template == "file:///data/stocks/AAPL.json"
        assert resources[0].mime_type == "application/json"

        # Check prompts
        prompts = [cap for cap in result.capabilities if cap.type == "prompt"]
        assert len(prompts) == 1
        assert prompts[0].id == "market_analysis"
        assert prompts[0].arguments is not None

    @pytest.mark.asyncio
    async def test_harvest_with_connection_error(self):
        """Test harvesting handles connection errors gracefully."""
        adapter = MCPAdapter(
            endpoint="https://api.example.com/mcp/sse", timeout=10, max_retries=3
        )

        with (
            patch(
                "services.registry.src.adapters.mcp.httpx.AsyncClient"
            ) as mock_client,
            patch("asyncio.sleep", new=AsyncMock()),
        ):  # Speed up retries
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Simulate connection error
            mock_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            # Should handle gracefully and return errors
            result = await adapter.harvest()

            assert len(result.capabilities) == 0
            assert len(result.errors) == 3  # One error per harvest method

    @pytest.mark.asyncio
    async def test_harvest_with_partial_failure(
        self, mock_mcp_tools_response, mock_mcp_prompts_response
    ):
        """Test harvesting continues when one endpoint fails."""
        adapter = MCPAdapter(
            endpoint="https://api.example.com/mcp/sse",
            timeout=10,
            max_retries=1,  # Reduce retries for faster test
        )

        with (
            patch(
                "services.registry.src.adapters.mcp.httpx.AsyncClient"
            ) as mock_client,
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Create response mocks
            tools_response = MagicMock()
            tools_response.json = MagicMock(return_value=mock_mcp_tools_response)
            tools_response.raise_for_status = MagicMock()

            prompts_response = MagicMock()
            prompts_response.json = MagicMock(return_value=mock_mcp_prompts_response)
            prompts_response.raise_for_status = MagicMock()

            # Mock post by checking the request method
            async def mock_post(*_, **kwargs):
                json_payload = kwargs.get("json")
                method = json_payload.get("method") if json_payload else None
                if method == "tools/list":
                    return tools_response
                if method == "resources/list":
                    raise httpx.HTTPError("Internal server error")
                if method == "prompts/list":
                    return prompts_response
                raise ValueError(f"Unknown method: {method}")

            mock_instance.post = AsyncMock(side_effect=mock_post)

            result = await adapter.harvest()

        # Should have tools and prompts but error for resources
        assert len(result.capabilities) == 3  # 2 tools + 1 prompt
        assert len(result.errors) == 1  # One error from resources/list

    @pytest.mark.asyncio
    async def test_harvest_with_retry_logic(self, mock_mcp_tools_response):
        """Test retry logic with exponential backoff."""
        adapter = MCPAdapter(
            endpoint="https://api.example.com/mcp/sse", timeout=10, max_retries=3
        )

        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("asyncio.sleep", new=AsyncMock()),
        ):  # Mock sleep to speed up test
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # First 2 attempts fail, 3rd succeeds
            attempt_count = 0

            async def mock_post(*args, **kwargs):
                nonlocal attempt_count
                attempt_count += 1

                if attempt_count < 3:
                    raise httpx.HTTPError("Temporary error")

                mock_resp = MagicMock()
                mock_resp.json = MagicMock(return_value=mock_mcp_tools_response)
                mock_resp.raise_for_status = MagicMock()
                return mock_resp

            mock_instance.post = mock_post

            # Should eventually succeed after retries
            result = await adapter._harvest_tools()

            assert len(result) == 2  # 2 tools from mock response

    @pytest.mark.asyncio
    async def test_health_check_successful(self):
        """Test successful health check."""
        adapter = MCPAdapter(endpoint="https://api.example.com/mcp/sse", timeout=5)

        with patch(
            "services.registry.src.adapters.mcp.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_instance.post = AsyncMock(return_value=mock_response)

            is_healthy = await adapter.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False on failure."""
        adapter = MCPAdapter(endpoint="https://api.example.com/mcp/sse", timeout=5)

        with patch(
            "services.registry.src.adapters.mcp.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            is_healthy = await adapter.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_extract_x402_from_metadata(self):
        """Test extracting x402 payment info from tool metadata."""
        adapter = MCPAdapter(endpoint="https://api.example.com/mcp/sse")

        metadata = {"x402": {"price": "100", "asset": "ETH"}}

        price, asset = await adapter._extract_x402("test_tool", metadata)

        assert price == "100"
        assert asset == "ETH"

    @pytest.mark.asyncio
    async def test_extract_x402_from_header(self):
        """Test extracting x402 payment info from HTTP header during dry-run."""
        adapter = MCPAdapter(endpoint="https://api.example.com/mcp/sse")

        with patch(
            "services.registry.src.adapters.mcp.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.headers = {
                "X-Microtransaction": "price=50;asset=USDC;recipient=0x123"
            }
            mock_instance.post = AsyncMock(return_value=mock_response)

            price, asset = await adapter._extract_x402("test_tool", {})

        assert price == "50"
        assert asset == "USDC"

    @pytest.mark.asyncio
    async def test_extract_x402_not_found(self):
        """Test x402 extraction returns None when not found."""
        adapter = MCPAdapter(endpoint="https://api.example.com/mcp/sse")

        with patch(
            "services.registry.src.adapters.mcp.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.headers = {}  # No x402 header
            mock_instance.post = AsyncMock(return_value=mock_response)

            price, asset = await adapter._extract_x402("test_tool", {})

        assert price is None
        assert asset is None
