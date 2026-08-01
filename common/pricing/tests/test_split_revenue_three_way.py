"""Tests for the three-way revenue split."""

from decimal import Decimal

from common_pricing.formulae import split_revenue_three_way


def test_split_revenue_three_way_sums_to_base_fee() -> None:
    base = Decimal("1.00")
    agent, validator, coordinator = split_revenue_three_way(
        base, coordinator_share_bps=1000, validator_share_bps=500
    )
    assert agent + validator + coordinator == base
    assert validator == Decimal("0.05")
    assert coordinator == Decimal("0.10")
    assert agent == Decimal("0.85")
