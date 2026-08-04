"""Typed dataclasses for pricing domain objects.

No Pydantic, no ORM — pure Python dataclasses so this package stays dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class InvocationRecord:
    """Represents one completed agent invocation, ready for billing settlement."""

    call_id: str
    session_id: str
    agent_id: str
    user_id: str
    base_fee: Decimal
    latency_ms: int
    execution_success: bool
    timestamp: datetime


@dataclass
class CostBreakdown:
    """Full cost decomposition for a single turn."""

    base_fees_total: Decimal  # sum of base_fee across all agent calls in the turn
    platform_token_cost: Decimal  # PLATFORM_TOKEN_RATE × output_tokens
    turn_cost: Decimal  # base_fees_total + platform_token_cost
    developer_payout: Decimal  # turn_cost × (1 - PLATFORM_SPREAD)  [per-agent]
    platform_cut: Decimal  # turn_cost × PLATFORM_SPREAD         [per-agent]


@dataclass
class RoutingCandidate:
    """Agent candidate enriched with metrics for routing score computation."""

    agent_id: str
    base_fee_usd: Decimal
    success_rate: float
    uptime_score: float
    p95_latency_ms: int
    execution_count: int
    routing_score: float = field(default=0.0)
