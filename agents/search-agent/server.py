"""Docs Search MCP Agent — SSE transport.

Generic web search via Google Serper — the caller constructs the full query
(including any site: operators or keywords). Returns structured search results
(organic + topStories) with title, snippet, link, and date.
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

load_dotenv()

_PORT = int(os.getenv("PORT", "3007"))

mcp = FastMCP("docs-search", host="0.0.0.0", port=_PORT)

SERPER_URL = "https://google.serper.dev/search"


def _mock_search_results(query: str) -> dict:
    """Zero-dependency mock — used when SERPER_API_KEY is unset.

    Keeps the OSS stack runnable end-to-end with no closed-service dependency
    (see orcha-always.mdc rule 1). Real search resumes automatically once a
    key is set in .env / .env.sandbox.
    """
    return {
        "organic": [
            {
                "title": f"[mock] Search result for: {query}",
                "link": "https://example.com/mock-search-result",
                "snippet": (
                    "This is a mock search result — SERPER_API_KEY is not set. "
                    "Set SERPER_API_KEY to enable real web search."
                ),
                "position": 1,
            }
        ]
    }


async def _search_web(query: str) -> dict:
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        logger.info("search_web: SERPER_API_KEY unset — returning mock results")
        return _mock_search_results(query)

    payload = json.dumps({"q": query, "num": 8})
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}
        except httpx.HTTPStatusError:
            logger.warning(
                "search_web: Serper API error — falling back to mock", exc_info=True
            )
            return _mock_search_results(query)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "agent": "docs-search", "version": "1.1.0"})


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web using Google and return structured results (organic + top stories).

    The caller is responsible for constructing the full query, including any
    site: operators (e.g. "site:python.langchain.com memory management") or
    other search modifiers.

    Args:
        query: Full search query string

    Returns:
        JSON string with organic results and top stories, each containing
        title, link, snippet, and date.
    """
    query = " ".join(query.split())  # collapse newlines/tabs/extra spaces
    logger.info("search_web: query=%r", query)

    raw = await _search_web(query)

    organic = []
    for r in raw.get("organic", []):
        entry: dict = {
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "position": r.get("position"),
        }
        if r.get("date"):
            entry["date"] = r["date"]
        if r.get("sitelinks"):
            entry["sitelinks"] = [
                {"title": s.get("title", ""), "link": s.get("link", "")}
                for s in r["sitelinks"]
            ]
        organic.append(entry)

    if not organic:
        return json.dumps({"query": query, "organic": [], "error": "No results found"})

    return json.dumps({"query": query, "organic": organic}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="sse")
