import pytest
import asyncio
import os
from orchestrator.runner import Runner

# Skip these tests if MCP is not running
pytestmark = pytest.mark.skipif(
    "RUN_E2E_TESTS" not in os.environ,
    reason="RUN_E2E_TESTS not set in environment"
)

class TestE2E:
    @pytest.mark.asyncio
    async def test_menu_export(self):
        """Test that we can export the menu from MCP"""
        runner = Runner()
        
        # Override the planner to always return export_menu
        runner.planner.plan = lambda _: "foodtec.export_menu"
        
        result = await runner.run("show me the menu")
        assert "result" in result
        assert "error" not in result
        
    @pytest.mark.asyncio
    async def test_order_validation(self):
        """Test that we can validate an order with MCP"""
        runner = Runner()
        
        # Override the planner to always return validate_order
        runner.planner.plan = lambda _: "foodtec.validate_order"
        
        result = await runner.run("validate my order")
        assert "result" in result
        assert "error" not in result