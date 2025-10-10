from fastapi.testclient import TestClient
from automation.main import app

class FakeLLM:
    async def classify_intent(self, text: str):
        if "pizza" in text.lower():
            return {"type": "search", "source": "fake", "query": "pizza"}
        return {"type": "unknown", "source": "fake"}

def test_search_rest_offline():
    with TestClient(app) as client:
        # Inject fake LLM to avoid external calls
        app.state.app.llm = FakeLLM()
        r = client.get("/automation/search", params={"query": "pizza"})
        assert r.status_code == 200
        data = r.json()
        assert data["query"] == "pizza"
        assert isinstance(data["results"], list)
