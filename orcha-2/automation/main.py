from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from automation.api import search_router
from automation.api.orchestrator_ws import router as ws_router

app = FastAPI(title="Orcha-2 Automation Layer", version="0.1.0")
app.include_router(search_router.router)
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "orcha2-automation", "version": "0.1.0"}
from contextlib import asynccontextmanager
from automation.core.config import get_settings
from automation.core.llm_client import LLMClient
from automation.providers.menu import DemoMenuProvider
from automation.api.health_router import router as health_router


class AppState:
    llm: LLMClient
    menu: DemoMenuProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.app = AppState()
    # Initialize long-lived dependencies
    app.state.app.llm = LLMClient()
    app.state.app.menu = DemoMenuProvider()
    # Startup banner
    try:
        pid = os.getpid()
        print(f"🚀  Automation API starting on {settings.host}:{settings.port} (pid {pid})")
    except Exception:
        pass
    yield
    # Teardown: if we add persistent httpx clients, close here


app = FastAPI(title="Orcha-2 Automation", version="0.1.0", lifespan=lifespan)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Access log middleware (must be added before lifespan)
@app.middleware("http")
async def access_logger(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    try:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        access_log_path = os.path.join(log_dir, "automation_access.log")
        with open(access_log_path, "a", encoding="utf-8") as f:
            f.write(
                f"{start.isoformat()}Z pid={os.getpid()} method={request.method} path={request.url.path} status={response.status_code} dur_ms={duration_ms}\n"
            )
    except Exception:
        pass
    return response

app.include_router(search_router.router)
app.include_router(ws_router)
app.include_router(health_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "orcha2-automation", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    s = get_settings()
    uvicorn.run("automation.main:app", host=s.host, port=s.port, reload=True)
