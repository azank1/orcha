"""Pricing constants — exact values from spec §9.

All values are hard spec values that must not be configured per-deployment.
"""

from __future__ import annotations

from decimal import Decimal

# ── Revenue split ─────────────────────────────────────────────────────────────
PLATFORM_SPREAD = Decimal("0.20")  # 20% platform cut on base_fee
PLATFORM_TOKEN_RATE = Decimal("0.000002")  # $0.000002 per SuperAgent output token

# ── Arrears ───────────────────────────────────────────────────────────────────
ARREARS_INTEREST_RATE = Decimal("0.05")  # 5% interest on outstanding arrears

# ── Execution limits ──────────────────────────────────────────────────────────
MAX_RETRIES = 3

# ── Routing hard gates ────────────────────────────────────────────────────────
UPTIME_FLOOR = 0.80  # agents below this are excluded from routing
SUCCESS_RATE_FLOOR = 0.50  # agents below this are excluded from routing

# ── Bootstrap thresholds (agents with < BOOTSTRAP_EXECUTION_COUNT invocations) ─
BOOTSTRAP_SUCCESS_RATE = 0.70  # assumed success rate for new agents
BOOTSTRAP_LATENCY_MS = 5000  # assumed p95 latency for new agents
BOOTSTRAP_EXECUTION_COUNT = 50  # invocations before real metrics are trusted

# ── Base fee market bounds (applied as multiples of category median) ──────────
BASE_FEE_FLOOR_MULTIPLIER = Decimal("0.10")  # floor = 10% of category median
BASE_FEE_CEILING_MULTIPLIER = Decimal("5.00")  # ceiling = 5× category median

# ── Cron schedules (crontab syntax for APScheduler) ──────────────────────────
SETTLEMENT_CRON_SCHEDULE = "0 0 * * *"  # daily midnight UTC
METRICS_REFRESH_SCHEDULE = "0 1 * * *"  # nightly 01:00 UTC
