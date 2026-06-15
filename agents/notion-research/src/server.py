"""
Notion Research Agent — FastMCP Server
MCP 2025-03-26 · SSE transport · 7 tools
"""
import json
from typing import Optional

import structlog
from fastmcp import FastMCP

from .config import settings
from .tools.note_creator import create_research_note
from .tools.research import fetch_market_data, search_web
from .tools.tradingview import add_tradingview_chart
from .tools.oauth import get_oauth_url, exchange_oauth_code

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

mcp = FastMCP(
    "notion-research",
    description="Research agent w/ Notion integration, TradingView charts & web search",
)


# ── Core tools ───────────────────────────────────────────────────────────────


@mcp.tool()
async def create_note(
    title: str,
    topic: str,
    workspace_id: str,
    sections: Optional[list[dict]] = None,
    tags: Optional[list[str]] = None,
) -> dict:
    """Create a research note in Notion with structured sections, tags and formatting."""
    return await create_research_note(
        title=title,
        topic=topic,
        workspace_id=workspace_id,
        sections=sections,
        tags=tags,
    )


@mcp.tool()
async def search(
    query: str,
    max_results: int = 5,
    summarize: bool = True,
) -> dict:
    """Search the web for research content and optionally summarize via LLM."""
    return await search_web(
        query=query,
        max_results=max_results,
        summarize=summarize,
    )


@mcp.tool()
async def market_data(
    symbol: str,
    data_type: str,
    timeframe: str = "24h",
) -> dict:
    """Fetch real-time or historical market data (price, volume, indicators, news)."""
    return await fetch_market_data(
        symbol=symbol,
        data_type=data_type,
        timeframe=timeframe,
    )


@mcp.tool()
async def tradingview_chart(
    page_id: str,
    symbol: str,
    oauth_token: str,
    interval: str = "1D",
    chart_type: str = "candlestick",
    indicators: Optional[list[str]] = None,
    theme: str = "light",
) -> dict:
    """Add TradingView chart embedding to a Notion page (requires OAuth)."""
    return await add_tradingview_chart(
        page_id=page_id,
        symbol=symbol,
        oauth_token=oauth_token,
        interval=interval,
        chart_type=chart_type,
        indicators=indicators,
        theme=theme,
    )


@mcp.tool()
async def orchestrate(
    topic: str,
    workspace_id: str,
    assets: Optional[list[str]] = None,
    include_charts: bool = True,
    oauth_token: Optional[str] = None,
) -> dict:
    """Execute complete research workflow: search web → create note → add charts."""
    return await _orchestrate(
        topic=topic,
        workspace_id=workspace_id,
        assets=assets,
        include_charts=include_charts,
        oauth_token=oauth_token,
    )


# ── OAuth tools ──────────────────────────────────────────────────────────────


@mcp.tool()
def authorize_oauth() -> str:
    """Generate Google OAuth authorization URL for TradingView access."""
    return get_oauth_url()


@mcp.tool()
async def oauth_exchange(code: str) -> dict:
    """Exchange OAuth authorization code for access/refresh tokens."""
    return await exchange_oauth_code(code)


# ── Internal orchestration (unchanged business logic) ────────────────────────


async def _orchestrate(
    topic: str,
    workspace_id: str,
    assets: Optional[list[str]] = None,
    include_charts: bool = True,
    oauth_token: Optional[str] = None,
) -> dict:
    """Execute complete research workflow."""
    logger.info("orchestrate_start", topic=topic, assets=assets)

    results: dict = {
        "topic": topic,
        "steps": [],
        "note_id": None,
        "charts_added": 0,
    }

    # 1 — web research
    search_results = await search_web(query=topic, max_results=5, summarize=True)
    results["steps"].append(
        {"step": "web_research", "status": "completed", "sources": len(search_results.get("results", []))}
    )

    # 2 — market data
    market: dict = {}
    if assets:
        for asset in assets:
            market[asset] = await fetch_market_data(symbol=asset, data_type="price")
        results["steps"].append(
            {"step": "market_data", "status": "completed", "assets": len(assets)}
        )

    # 3 — create Notion note
    sections = [{"heading": "Research Summary", "content": search_results.get("summary", "")}]
    if market:
        body = "\n".join(
            f"**{sym}**: ${d.get('price', 'N/A')}" for sym, d in market.items()
        )
        sections.append({"heading": "Market Data", "content": body})

    note = await create_research_note(
        title=f"{topic} - Research",
        topic=topic,
        sections=sections,
        tags=["research", "automated"],
        workspace_id=workspace_id,
    )
    results["note_id"] = note["page_id"]
    results["steps"].append(
        {"step": "create_note", "status": "completed", "page_id": note["page_id"]}
    )

    # 4 — charts
    if include_charts and oauth_token and assets:
        for asset in assets:
            try:
                await add_tradingview_chart(
                    page_id=note["page_id"],
                    symbol=asset,
                    interval="1D",
                    chart_type="candlestick",
                    indicators=["RSI", "MACD"],
                    oauth_token=oauth_token,
                )
                results["charts_added"] += 1
            except Exception as e:
                logger.warning("chart_embed_failed", asset=asset, error=str(e))

        results["steps"].append(
            {"step": "add_charts", "status": "completed", "count": results["charts_added"]}
        )

    logger.info("orchestrate_complete", note_id=results["note_id"])
    return results


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="sse", host=settings.host, port=settings.port)
