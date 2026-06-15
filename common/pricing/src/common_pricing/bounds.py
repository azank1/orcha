"""Market bounds for agent base_fee validation — pure functions.

Agents must register a base_fee within [floor, ceiling] relative to the
category median computed nightly by the metrics_refresh job.
If no category median exists (bootstrap), all fees are allowed.
"""

from __future__ import annotations

from decimal import Decimal

from .constants import (
    BASE_FEE_CEILING_MULTIPLIER,
    BASE_FEE_FLOOR_MULTIPLIER,
    UPTIME_FLOOR,
)


def market_floor(category_median: Decimal) -> Decimal:
    """Minimum allowed base_fee = category_median × 0.10."""
    return category_median * BASE_FEE_FLOOR_MULTIPLIER


def market_ceiling(category_median: Decimal) -> Decimal:
    """Maximum allowed base_fee = category_median × 5.00."""
    return category_median * BASE_FEE_CEILING_MULTIPLIER


def is_within_bounds(
    base_fee: Decimal,
    category_median: Decimal | None,
) -> tuple[bool, str]:
    """
    Check whether base_fee is within the allowed market range.

    Args:
        base_fee: the agent's proposed base_fee in USD
        category_median: median base_fee for the agent's task_category;
                         None means bootstrap (no stats yet) — all fees pass

    Returns:
        (is_valid, reason) — reason is "" on success, description on failure
    """
    if base_fee < Decimal("0"):
        return False, "base_fee must be non-negative"

    if category_median is None or category_median == Decimal("0"):
        # Bootstrap mode — no category stats yet, all fees are allowed
        return True, ""

    floor = market_floor(category_median)
    ceiling = market_ceiling(category_median)

    if base_fee < floor:
        return (
            False,
            f"base_fee ${base_fee} is below market floor ${floor} "
            f"(10% of category median ${category_median})",
        )
    if base_fee > ceiling:
        return (
            False,
            f"base_fee ${base_fee} exceeds market ceiling ${ceiling} "
            f"(5× category median ${category_median})",
        )

    return True, ""


def uptime_gate(uptime_score: float, floor: float = UPTIME_FLOOR) -> bool:
    """Return True if the agent passes the uptime hard gate."""
    return uptime_score >= floor
