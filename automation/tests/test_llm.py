import pytest
from orchestrator.llm import LLMWrapper
import os

# Skip these tests if no OpenAI API key is present
pytestmark = pytest.mark.skipif(
    "OPENAI_API_KEY" not in os.environ,
    reason="OPENAI_API_KEY not set in environment"
)

class TestLLM:
    def test_llm_initialization(self):
        llm = LLMWrapper()
        assert llm.llm is not None
        
    def test_simple_query(self):
        llm = LLMWrapper()
        response = llm.ask("What is 2+2?")
        assert response is not None
        assert len(response) > 0
        
    def test_tool_selection(self):
        llm = LLMWrapper()
        response = llm.ask(
            "The user said: show me the menu. "
            "Which tool should I call? Options: "
            "foodtec.export_menu, foodtec.validate_order, foodtec.accept_order"
        )
        assert "export_menu" in response.lower()