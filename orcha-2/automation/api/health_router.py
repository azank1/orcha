from __future__ import annotations

from fastapi import APIRouter, Request
import httpx

router = APIRouter(prefix="/automation", tags=["health"]) 


@router.get("/health/llm")
async def llm_health(request: Request):
    # Minimal health – detect Ollama reachability and OpenAI key presence
    settings = None
    status = {"ollama": "disabled", "openai": "disabled"}
    try:
        # Access LLM client if available
        app_state = getattr(request.app.state, "app", None)
        llm = getattr(app_state, "llm", None)
        if llm is not None:
            # Pull settings from environment via client (best-effort)
            from automation.core.llm_client import OLLAMA_HOST, USE_OLLAMA, USE_OPENAI, OPENAI_API_KEY
            if USE_OLLAMA:
                try:
                    async with httpx.AsyncClient(timeout=2) as c:
                        r = await c.get(f"{OLLAMA_HOST}/api/tags")
                        status["ollama"] = "ok" if r.status_code == 200 else f"http {r.status_code}"
                except Exception as e:
                    status["ollama"] = f"error: {e}"
            if USE_OPENAI:
                status["openai"] = "ok" if OPENAI_API_KEY else "missing_api_key"
    except Exception as e:
        status["error"] = str(e)
    return status
