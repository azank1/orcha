"""
Test for natural language workflow
"""
import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.natural_flow import NaturalFlow


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="No LLM API key configured"
)
def test_natural_flow_menu_query():
    """Test asking about menu items"""
    flow = NaturalFlow()
    
    # Ask about appetizers
    results = flow.process("Show me the appetizers")
    
    # Should have gotten LLM response
    assert results["llm_response"]
    assert isinstance(results["llm_response"], str)
    
    # Should have called export_menu
    assert len(results["actions"]) > 0
    assert any(action["tool"] == "foodtec.export_menu" for action in results["actions"])
    
    # Menu should be cached now
    assert flow.menu_cache is not None


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="No LLM API key configured"
)
def test_natural_flow_order():
    """Test placing an order through natural language"""
    flow = NaturalFlow()
    
    # Place an order
    results = flow.process("I want chicken strips for pickup, customer name is John Doe, phone 410-555-1234")
    
    # Should have LLM response
    assert results["llm_response"]
    
    # Should have multiple actions (export, validate, accept)
    assert len(results["actions"]) >= 2
    
    # Check that validation happened
    validation_actions = [a for a in results["actions"] if a["tool"] == "foodtec.validate_order"]
    if validation_actions:
        assert validation_actions[0].get("success")
        assert "canonical_price" in validation_actions[0]


def test_natural_flow_initialization():
    """Test that natural flow can be initialized"""
    try:
        flow = NaturalFlow()
        assert flow.mcp_client is not None
        assert flow.tools is not None
    except ValueError as e:
        # Expected if no API key configured
        if "API_KEY not found" in str(e):
            pytest.skip("No LLM API key configured")
        else:
            raise


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
