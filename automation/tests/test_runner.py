import pytest
import asyncio
from orchestrator.runner import Runner
from unittest.mock import patch, MagicMock

class TestRunner:
    @pytest.fixture
    def mock_mcp_client(self):
        with patch('clients.mcp_client.MCPClient') as mock:
            client_instance = MagicMock()
            mock.return_value = client_instance
            yield client_instance
            
    @pytest.fixture
    def mock_planner(self):
        with patch('orchestrator.planner.Planner') as mock:
            planner_instance = MagicMock()
            mock.return_value = planner_instance
            yield planner_instance
    
    @pytest.mark.asyncio
    async def test_run_export_menu(self, mock_planner, mock_mcp_client):
        # Setup mocks
        mock_planner.plan.return_value = "foodtec.export_menu"
        mock_mcp_client.call.return_value = asyncio.Future()
        mock_mcp_client.call.return_value.set_result({"result": {"categories": []}})
        
        # Run test
        runner = Runner()
        result = await runner.run("show me the menu")
        
        # Verify
        mock_planner.plan.assert_called_once_with("show me the menu")
        mock_mcp_client.call.assert_called_once_with(
            "foodtec.export_menu", 
            {"orderType": "Pickup"}
        )
        assert "result" in result

    @pytest.mark.asyncio
    async def test_run_validate_order(self, mock_planner, mock_mcp_client):
        # Setup mocks
        mock_planner.plan.return_value = "foodtec.validate_order"
        mock_mcp_client.call.return_value = asyncio.Future()
        mock_mcp_client.call.return_value.set_result({"result": {"valid": True}})
        
        # Run test
        runner = Runner()
        result = await runner.run("validate my order")
        
        # Verify
        mock_planner.plan.assert_called_once_with("validate my order")
        mock_mcp_client.call.assert_called_once()
        assert "result" in result