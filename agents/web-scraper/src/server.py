"""Web Scraper Agent — A2A-compatible agent for fetching structured data from URLs.

Exposes:
- GET  /.well-known/agent.json → Agent Card
- POST /                       → A2A JSON-RPC 2.0 endpoint (message/send, tasks/get)
- POST /a2a/tasks/send         → legacy REST endpoint (kept for direct testing)
- GET  /health → health check
- GET  /auth/start → begin OAuth flow (authenticated scraping)
- GET  /auth/callback → OAuth callback

The agent receives natural language tasks like "Fetch data from https://example.com
and summarize the key points" and uses BeautifulSoup to extract structured data,
optionally summarizing via LLM.  For pages requiring login, the agent returns an
A2A ``input-required`` state with an auth URL; the user authenticates in a popup
and the agent retries with stored credentials.
"""

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Any

import aiohttp
import structlog
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_auth_headers, has_any_token, router as auth_router
from .config import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

app = FastAPI(title="Web Scraper Agent", version="0.2.0")

# In-memory task store for A2A polling (tasks complete synchronously so this is tiny)
_task_store: dict[str, dict[str, Any]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount OAuth routes for authenticated scraping
app.include_router(auth_router)

# --- Agent Card ---

AGENT_CARD = {
    # Required by MetaOrcha registry A2AAdapter — missing → 0 capabilities harvested
    "schemaVersion": "1.0",
    "name": "Web Scraper",
    "description": (
        "Fetches and extracts structured data from web URLs. "
        "Supports authenticated scraping — the agent can open an OAuth popup "
        "for the user to sign in, then scrape pages that require login."
    ),
    "url": f"http://localhost:{os.getenv('PORT', '3004')}",
    "version": "0.2.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "skills": [
        {
            "id": "scrape",
            "name": "Web Scraping",
            "description": "Fetch a URL and extract structured data (title, headings, text, tables, links).",
            "tags": ["scraping", "web", "data-extraction"],
            "examples": [
                "Fetch https://example.com and extract the main content",
                "Scrape the pricing table from https://example.com/pricing",
            ],
        },
        {
            "id": "summarize",
            "name": "Page Summarization",
            "description": "Fetch a URL and provide an LLM-powered summary of the content.",
            "tags": ["summarization", "web", "ai"],
            "examples": [
                "Summarize the article at https://example.com/blog/post",
            ],
        },
        {
            "id": "authenticated_scrape",
            "name": "Authenticated Scraping",
            "description": (
                "Login to a site via OAuth (Google, etc.) and scrape pages that "
                "require authentication.  Returns an auth URL for the user to "
                "sign in, then fetches with stored credentials."
            ),
            "tags": ["scraping", "auth", "oauth", "login"],
            "examples": [
                "Login to my Google account and scrape my profile",
                "Sign in and fetch my dashboard at https://app.example.com/dashboard",
            ],
        },
    ],
}


@app.get("/.well-known/agent.json")
async def get_agent_card():
    return AGENT_CARD


# --- A2A JSON-RPC 2.0 root endpoint ---

@app.post("/")
async def jsonrpc_endpoint(body: dict[str, Any]):
    """A2A JSON-RPC 2.0 dispatcher — handles message/send and tasks/get."""
    rpc_id = body.get("id", "")
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "message/send":
        message = params.get("message", {})
        message_id = message.get("messageId", str(uuid.uuid4()))
        task_id = params.get("taskId") or message.get("taskId") or str(uuid.uuid4())

        # Extract text from parts (support both "kind" and "type" keys)
        parts = message.get("parts", [])
        text_parts = [
            p.get("text", "")
            for p in parts
            if p.get("kind") == "text" or p.get("type") == "text"
        ]
        query = " ".join(text_parts).strip()

        session_id = params.get("metadata", {}).get("session_id", "default")

        logger.info("jsonrpc_task_received", task_id=task_id, method=method, query=query[:200])

        # Execute task inline (synchronous)
        task_result = await _execute_task(task_id, query, session_id)
        _task_store[task_id] = task_result

        return {"jsonrpc": "2.0", "id": rpc_id, "result": task_result}

    elif method == "tasks/get":
        task_id = params.get("id", "")
        task = _task_store.get(task_id)
        if task is None:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32602, "message": f"Task {task_id!r} not found"},
            }
        return {"jsonrpc": "2.0", "id": rpc_id, "result": task}

    else:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
        }


async def _execute_task(task_id: str, query: str, session_id: str) -> dict[str, Any]:
    """Execute a scraping task and return the A2A task object."""
    if not query:
        return _task_failed(task_id, "No text message provided")

    try:
        urls = _extract_urls(query)

        if not urls:
            return _task_failed(task_id, "No URLs found in task message. Please include a URL to scrape.")

        wants_auth = _wants_authentication(query)

        if wants_auth and not has_any_token(session_id):
            provider = _detect_provider(query)
            auth_url = (
                f"{settings.auth_redirect_base}/auth/start"
                f"?provider={provider}&state={task_id}&session_id={session_id}"
            )
            logger.info("auth_required", task_id=task_id, provider=provider)
            return {
                "id": task_id,
                "status": {
                    "state": "input-required",
                    "message": {
                        "role": "agent",
                        "parts": [{"kind": "text", "text": (
                            "Authentication required. Please open the auth URL "
                            "to sign in, then resend this task."
                        )}],
                    },
                },
                "metadata": {"auth_url": auth_url, "provider": provider, "session_id": session_id},
            }

        extra_headers: dict[str, str] | None = None
        if has_any_token(session_id):
            provider = _detect_provider(query)
            extra_headers = get_auth_headers(session_id, provider)

        results = []
        for url in urls[:3]:
            data = await _fetch_and_extract(url, extra_headers=extra_headers)
            results.append(data)

        wants_summary = any(
            word in query.lower()
            for word in ["summarize", "summary", "key points", "overview", "tldr"]
        )

        if wants_summary and settings.openrouter_api_key:
            text_content = "\n\n".join(r.get("text", "")[:3000] for r in results)
            answer = await _summarize(query, text_content)
        else:
            answer = json.dumps(results, indent=2)

        return {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"kind": "text", "text": answer}]}],
        }

    except Exception as e:
        logger.error("task_failed", task_id=task_id, error=str(e))
        return _task_failed(task_id, str(e))


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "web-scraper",
        "version": "0.2.0",
        "auth_configured": settings.google_client_id is not None,
    }


# --- A2A tasks/send ---

@app.post("/a2a/tasks/send")
async def send_task(body: dict[str, Any]):
    """Legacy REST endpoint — delegates to _execute_task."""
    task_id = body.get("id", f"task_{uuid.uuid4().hex[:12]}")
    message = body.get("message", {})
    parts = message.get("parts", [])
    text_parts = [p.get("text", "") for p in parts if p.get("type") == "text" or p.get("kind") == "text"]
    query = " ".join(text_parts).strip()
    session_id = body.get("metadata", {}).get("session_id", "default")
    logger.info("legacy_task_received", task_id=task_id, query=query[:200])
    return await _execute_task(task_id, query, session_id)


# --- Core scraping ---

async def _fetch_and_extract(
    url: str,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch a URL and extract structured data.

    Args:
        url: The page to fetch.
        extra_headers: Optional headers (e.g. ``Authorization``) injected
            for authenticated scraping.
    """
    logger.info("fetching_url", url=url, authenticated=extra_headers is not None)

    headers = {"User-Agent": "MetaOrcha-WebScraper/0.2"}
    if extra_headers:
        headers.update(extra_headers)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            html = await resp.text()

    soup = BeautifulSoup(html, "lxml")

    # Remove script/style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract structured data
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:20]]

    # Main text content
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    text = "\n".join(paragraphs[:50])

    # Tables
    tables = []
    for table in soup.find_all("table")[:5]:
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)

    # Links
    links = []
    for a in soup.find_all("a", href=True)[:30]:
        href = a["href"]
        link_text = a.get_text(strip=True)
        if href.startswith("http") and link_text:
            links.append({"text": link_text, "url": href})

    return {
        "url": url,
        "title": title,
        "headings": headings,
        "text": text[:5000],
        "tables": tables,
        "links": links,
    }


async def _summarize(query: str, content: str) -> str:
    """LLM-powered summarization via OpenRouter."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    try:
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "Summarize web content concisely. Focus on key data and facts."},
                {"role": "user", "content": f"Task: {query}\n\nContent:\n{content[:4000]}"},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("summarization_failed", error=str(e))
        return content[:2000]


# --- Helpers ---

def _extract_urls(text: str) -> list[str]:
    """Extract HTTP(S) URLs from text."""
    import re
    return re.findall(r"https?://[^\s<>\"']+", text)


def _wants_authentication(query: str) -> bool:
    """Return True if the query signals that auth/login is needed."""
    q = query.lower()
    signals = [
        "login",
        "log in",
        "sign in",
        "signin",
        "authenticate",
        "my account",
        "my profile",
        "my dashboard",
        "logged in",
        "with my credentials",
    ]
    return any(sig in q for sig in signals)


def _detect_provider(query: str) -> str:
    """Guess the OAuth provider the user wants based on keywords."""
    q = query.lower()
    if any(w in q for w in ["google", "gmail", "gdrive"]):
        return "google"
    # Default to google for MVP; expand later (github, microsoft, etc.)
    return "google"


def _task_failed(task_id: str, error: str) -> dict:
    return {
        "id": task_id,
        "status": {
            "state": "failed",
            "message": {
                "role": "agent",
                "parts": [{"type": "text", "text": f"Error: {error}"}],
            },
        },
    }
