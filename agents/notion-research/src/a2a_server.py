"""
Notion Research Agent — A2A-compatible server.

Exposes:
- GET  /.well-known/agent.json → Agent Card
- POST /a2a/tasks/send → receives NL tasks, returns research results
- GET  /health → health check

Skills:
- research_topic:       Search web for a topic and return summarised findings.
- create_research_note: Create a structured Notion page from research data.
- market_data:          Fetch real-time market data for a symbol.

Converted from MCP/SSE to A2A/HTTP for the MetaOrcha MVP — the SuperAgent
orchestrator calls this agent via the A2AHandler using standard A2A task
lifecycle (send → completed/failed).
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .tools.note_creator import create_research_note
from .tools.research import fetch_market_data, search_web

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

app = FastAPI(title="Notion Research Agent (A2A)", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Agent Card ────────────────────────────────────────────────────────────────

AGENT_CARD = {
    "name": "Notion Research",
    "description": (
        "Research agent that searches the web, analyses market data, and "
        "creates structured research notes in Notion. Send a natural language "
        "task describing what to research."
    ),
    "url": f"http://localhost:{os.getenv('PORT', '3006')}",
    "version": "0.2.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "skills": [
        {
            "id": "research_topic",
            "name": "Topic Research",
            "description": (
                "Search the web for a topic, summarise findings via LLM, "
                "and return structured research results."
            ),
            "tags": ["research", "web-search", "summarization", "analysis"],
            "examples": [
                "Research the latest developments in AI agent orchestration",
                "Find information about x402 payment protocol for agents",
                "Research Bitcoin Lightning Network adoption in 2026",
            ],
        },
        {
            "id": "create_research_note",
            "name": "Create Research Note",
            "description": (
                "Create a structured research note in Notion with sections, "
                "tags, and formatted content."
            ),
            "tags": ["notion", "notes", "documentation", "writing"],
            "examples": [
                "Create a Notion page titled 'AI Agent Market Analysis' with research findings",
                "Write a research note about Web3 payment protocols in Notion",
            ],
        },
        {
            "id": "market_data",
            "name": "Market Data",
            "description": "Fetch real-time or historical market data (price, volume, indicators) for a symbol.",
            "tags": ["market", "finance", "data", "crypto", "stocks"],
            "examples": [
                "Get the current price of BTC",
                "Fetch ETH market data for the last 24 hours",
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
        task_id = params.get("taskId") or message.get("taskId") or str(uuid.uuid4())

        parts = message.get("parts", [])
        text_parts = [
            p.get("text", "")
            for p in parts
            if p.get("kind") == "text" or p.get("type") == "text"
        ]
        query = " ".join(text_parts).strip()

        if not query:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": _task_failed(task_id, "No text message provided")}

        logger.info("jsonrpc_task_received", task_id=task_id, method=method, query=query[:200])

        # Route to the appropriate skill
        skill = _detect_skill(query)
        try:
            if skill == "create_research_note":
                result = await _handle_create_note(query)
            elif skill == "market_data":
                result = await _handle_market_data(query)
            else:
                result = await _handle_research(query)

            answer = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            task_result = {
                "id": task_id,
                "status": {
                    "state": "completed",
                    "message": {"role": "agent", "parts": [{"type": "text", "text": answer}]},
                },
                "artifacts": [{"parts": [{"type": "text", "text": answer}]}],
            }
        except Exception as e:
            logger.error("task_failed", task_id=task_id, error=str(e))
            task_result = _task_failed(task_id, str(e))

        return {"jsonrpc": "2.0", "id": rpc_id, "result": task_result}

    elif method == "tasks/get":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32602, "message": "Stateless agent — use message/send"},
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
        }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "notion-research",
        "version": "0.2.0",
        "notion_configured": settings.notion_api_key is not None,
        "tavily_configured": settings.tavily_api_key is not None,
    }


# ── A2A tasks/send ────────────────────────────────────────────────────────────


@app.post("/a2a/tasks/send")
async def send_task(body: dict[str, Any]):
    """Handle A2A tasks/send — receive NL task, dispatch to appropriate skill."""
    task_id = body.get("id", f"task_{uuid.uuid4().hex[:12]}")

    # Extract text message from A2A envelope
    message = body.get("message", {})
    parts = message.get("parts", [])
    text_parts = [p["text"] for p in parts if p.get("type") == "text"]
    query = " ".join(text_parts).strip()

    if not query:
        return _task_failed(task_id, "No text message provided")

    logger.info("task_received", task_id=task_id, query=query[:200])

    # Route to the appropriate skill based on intent detection
    skill = _detect_skill(query)

    try:
        if skill == "create_research_note":
            result = await _handle_create_note(query)
        elif skill == "market_data":
            result = await _handle_market_data(query)
        else:
            # Default: research_topic
            result = await _handle_research(query)

        answer = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)

        return {
            "id": task_id,
            "status": {
                "state": "completed",
                "message": {
                    "role": "agent",
                    "parts": [{"type": "text", "text": answer}],
                },
            },
            "artifacts": [{"parts": [{"type": "text", "text": answer}]}],
        }

    except Exception as e:
        logger.error("task_failed", task_id=task_id, error=str(e))
        return _task_failed(task_id, str(e))


# ── Skill handlers ────────────────────────────────────────────────────────────


async def _handle_research(query: str) -> dict[str, Any]:
    """Execute the research_topic skill."""
    results = await search_web(query=query, max_results=5, summarize=True)
    return {
        "skill": "research_topic",
        "query": query,
        "sources": len(results.get("results", [])),
        "results": results.get("results", []),
        "summary": results.get("summary"),
    }


async def _handle_create_note(query: str) -> dict[str, Any]:
    """Execute the create_research_note skill.

    Extracts title/topic from the query and creates a Notion page.
    If no workspace_id is provided, uses a default or returns instructions.
    """
    # Parse the query for structured data
    title, topic, workspace_id, sections, tags = _parse_note_params(query)

    if not settings.notion_api_key:
        return {
            "skill": "create_research_note",
            "status": "mock",
            "message": (
                f"Would create Notion page titled '{title}' about '{topic}'. "
                "Configure NOTION_API_KEY to create real pages."
            ),
            "title": title,
            "topic": topic,
        }

    if not workspace_id:
        return {
            "skill": "create_research_note",
            "status": "needs_input",
            "message": (
                "Please provide a Notion workspace/database ID to create the page in. "
                "Example: 'Create a note in workspace abc123def456...'"
            ),
        }

    result = await create_research_note(
        title=title,
        topic=topic,
        workspace_id=workspace_id,
        sections=sections,
        tags=tags,
    )
    return {"skill": "create_research_note", **result}


async def _handle_market_data(query: str) -> dict[str, Any]:
    """Execute the market_data skill."""
    symbol = _extract_symbol(query)
    data_type = "price"
    if any(w in query.lower() for w in ["volume", "vol"]):
        data_type = "volume"
    elif any(w in query.lower() for w in ["indicator", "rsi", "macd"]):
        data_type = "indicators"
    elif any(w in query.lower() for w in ["news", "headline"]):
        data_type = "news"

    result = await fetch_market_data(
        symbol=symbol, data_type=data_type, timeframe="24h"
    )
    return {"skill": "market_data", "symbol": symbol, **result}


# ── Intent detection & parsing helpers ────────────────────────────────────────


def _detect_skill(query: str) -> str:
    """Simple keyword-based skill routing."""
    q = query.lower()

    # Create note signals
    note_signals = [
        "create a note",
        "create a page",
        "create a notion",
        "write a note",
        "write a research note",
        "create notion",
        "make a page",
        "write to notion",
        "save to notion",
        "make a notion",
    ]
    if any(sig in q for sig in note_signals):
        return "create_research_note"

    # Market data signals
    market_signals = [
        "price of",
        "market data",
        "stock price",
        "crypto price",
        "btc price",
        "eth price",
        "bitcoin",
        "ethereum",
        "trading",
        "ticker",
    ]
    if any(sig in q for sig in market_signals):
        return "market_data"

    # Default to research
    return "research_topic"


def _parse_note_params(
    query: str,
) -> tuple[str, str, str | None, list[dict] | None, list[str] | None]:
    """Extract note parameters from natural language query."""
    import re

    # Try to extract title (text in quotes)
    title_match = re.search(r"['\"](.+?)['\"]", query)
    title = title_match.group(1) if title_match else query[:60]

    # Topic is the core subject
    topic = query

    # Try to extract workspace ID (32-char hex string)
    ws_match = re.search(r"\b([a-f0-9]{32})\b", query)
    workspace_id = ws_match.group(1) if ws_match else None

    # Tags from hashtags or "tagged with" patterns
    tags = re.findall(r"#(\w+)", query)

    return title, topic, workspace_id, None, tags or None


def _extract_symbol(query: str) -> str:
    """Extract a financial symbol from the query."""
    import re

    # Common patterns: BTC, BTCUSD, ETH/USD, $AAPL
    match = re.search(
        r"\b(BTC|ETH|SOL|AAPL|GOOGL|MSFT|TSLA|AMZN|XRP|ADA|DOT|LINK)\b",
        query.upper(),
    )
    if match:
        return match.group(1)

    # Try $SYMBOL pattern
    dollar_match = re.search(r"\$([A-Z]{1,5})", query.upper())
    if dollar_match:
        return dollar_match.group(1)

    return "BTC"  # default


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
