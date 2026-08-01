"""Finance Dashboard Agent — MCP SSE transport.

Returns a CanvasKit UIManifest as a canvas envelope. The Orcha SuperAgent
detects the __canvas__ marker in the output and emits a canvas_manifest SSE
event, which the frontend renders as a live dashboard.

For demo purposes this uses realistic but static mock data. A production version
would pull live data via ConnectKit connectors (Alpaca, Coinbase, Plaid).
"""

from __future__ import annotations

import json
import logging
import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_PORT = int(os.getenv("PORT", "3010"))

mcp = FastMCP("finance-dashboard", host="0.0.0.0", port=_PORT)


# ---------------------------------------------------------------------------
# Mock data generators
# ---------------------------------------------------------------------------


def _performance_series(days: int) -> list[dict]:
    """Generate a realistic-looking 90-day portfolio performance series."""
    import math
    import random

    random.seed(42)
    base = 118_000
    points = []
    value = base
    for i in range(days):
        # Mild upward drift with daily noise
        drift = 0.0004
        noise = random.gauss(0, 0.008)
        value = value * (1 + drift + noise)
        date_offset = days - i
        # Simple date arithmetic without dateutil
        from datetime import date, timedelta

        d = date.today() - timedelta(days=date_offset)
        points.append({"date": d.strftime("%b %d"), "value": round(value)})
    return points


def _positions_table() -> tuple[list[dict], list[dict]]:
    columns = [
        {"key": "symbol", "label": "Symbol", "type": "text"},
        {"key": "shares", "label": "Shares", "type": "number"},
        {"key": "price", "label": "Price", "type": "currency"},
        {"key": "value", "label": "Market Value", "type": "currency"},
        {"key": "pnl_pct", "label": "P&L %", "type": "percent"},
    ]
    rows = [
        {"symbol": "AAPL", "shares": 42, "price": 213.45, "value": 8964.90, "pnl_pct": 0.127},
        {"symbol": "NVDA", "shares": 15, "price": 875.20, "value": 13128.00, "pnl_pct": 0.341},
        {"symbol": "MSFT", "shares": 28, "price": 415.80, "value": 11642.40, "pnl_pct": 0.089},
        {"symbol": "BTC",  "shares": 0.48, "price": 67400.00, "value": 32352.00, "pnl_pct": 0.512},
        {"symbol": "ETH",  "shares": 3.2, "price": 3580.00, "value": 11456.00, "pnl_pct": 0.218},
        {"symbol": "GOOGL", "shares": 22, "price": 172.60, "value": 3797.20, "pnl_pct": -0.031},
        {"symbol": "TSLA",  "shares": 18, "price": 248.90, "value": 4480.20, "pnl_pct": -0.142},
    ]
    return columns, rows


def _alerts() -> list[dict]:
    return [
        {
            "id": "a1",
            "severity": "warning",
            "title": "TSLA down 14.2% MTD",
            "body": "Position below cost basis. Consider reviewing stop-loss.",
            "timestamp": "2h ago",
        },
        {
            "id": "a2",
            "severity": "success",
            "title": "BTC +51.2% since entry",
            "body": "Bitcoin position significantly outperforming. Take-profit threshold reached.",
            "timestamp": "4h ago",
        },
        {
            "id": "a3",
            "severity": "info",
            "title": "NVDA earnings in 3 days",
            "body": "Q3 earnings call scheduled. Implied volatility elevated.",
            "timestamp": "1d ago",
        },
    ]


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {"status": "healthy", "agent": "finance-dashboard", "version": "1.0.0"}
    )


@mcp.tool()
async def get_portfolio_dashboard(
    user_id: str = "",
    date_range_days: int = 90,
) -> str:
    """Build a portfolio dashboard UIManifest for the given user.

    Returns a CanvasKit canvas envelope. The Orcha runtime detects the
    __canvas__ marker and renders the manifest as a visual dashboard instead
    of a text reply.

    Args:
        user_id: Optional user identifier. Defaults to demo portfolio.
        date_range_days: Number of days in the performance chart (default 90).

    Returns:
        JSON canvas envelope with a UIManifest dashboard.
    """
    logger.info("get_portfolio_dashboard: user=%r days=%d", user_id or "demo", date_range_days)

    days = max(7, min(date_range_days, 365))
    perf_series = _performance_series(days)
    columns, rows = _positions_table()
    alerts = _alerts()

    total_value = sum(r["value"] for r in rows)
    day_pnl = total_value * 0.0148
    day_pnl_pct = 0.0148
    total_pnl_pct = (total_value - 118_000) / 118_000

    manifest = {
        "version": "1.0",
        "title": f"Portfolio — {user_id or 'Demo Account'} (sample data)",
        "layout": "dashboard",
        "components": [
            {
                "type": "metric_card",
                "id": "total_value",
                "label": "Total Value",
                "value": f"${total_value:,.0f}",
                "delta": round(total_pnl_pct * 100, 1),
                "trend": "up",
                "unit": "USD",
            },
            {
                "type": "metric_card",
                "id": "day_pnl",
                "label": "Day P&L",
                "value": f"+${day_pnl:,.0f}",
                "delta": round(day_pnl_pct * 100, 2),
                "trend": "up",
                "unit": "USD",
            },
            {
                "type": "metric_card",
                "id": "open_positions",
                "label": "Open Positions",
                "value": str(len(rows)),
            },
            {
                "type": "metric_card",
                "id": "active_alerts",
                "label": "Active Alerts",
                "value": str(len(alerts)),
                "sub_label": "1 new",
            },
            {
                "type": "line_chart",
                "id": "performance_chart",
                "title": f"{days}-Day Performance",
                "x_key": "date",
                "y_keys": ["value"],
                "colors": ["#6366f1"],
                "data": perf_series,
            },
            {
                "type": "data_table",
                "id": "positions_table",
                "title": "Open Positions",
                "columns": columns,
                "rows": rows,
            },
            {
                "type": "alert_feed",
                "id": "alerts_feed",
                "title": "Alerts",
                "alerts": alerts,
            },
        ],
    }

    return json.dumps(
        {
            "__canvas__": True,
            "summary": f"Portfolio dashboard: ${total_value:,.0f} total value across {len(rows)} positions.",
            "manifest": manifest,
        }
    )


if __name__ == "__main__":
    mcp.run(transport="sse")
