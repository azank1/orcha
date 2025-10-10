"""
Orcha-2 Proxy (minimal)
FastAPI server exposing a simple health endpoint. Intended as a placeholder to validate
terminal runs from the proxy directory (python main.py).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn


def _load_env() -> None:
    """Load env from repo root and local proxy/.env if present."""
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # d:/dev/orcha-1
    # Load shared repo .env then local overrides
    load_dotenv(repo_root / ".env")
    load_dotenv(here.parent / ".env")


_load_env()

app = FastAPI(title="Orcha-2 Proxy", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])  # Simple health endpoint
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "orcha2-proxy",
        "version": app.version,
    }


if __name__ == "__main__":
    host = os.getenv("PROXY_HOST", "127.0.0.1")
    port = int(os.getenv("PROXY_PORT", "8081"))
    uvicorn.run("main:app", host=host, port=port, reload=os.getenv("DEBUG", "false").lower() == "true")
