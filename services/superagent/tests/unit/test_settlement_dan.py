"""D1 spike — DAN revenue split in settlement."""

from __future__ import annotations

import logging
from decimal import Decimal

import pytest

from superagent.pricing.settlement import compute_revenue_split


def test_compute_revenue_split_legacy_two_way(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COORDINATOR_SHARE_BPS", raising=False)
    monkeypatch.delenv("VALIDATOR_SHARE_BPS", raising=False)
    developer, platform, validator = compute_revenue_split(Decimal("1.00"))
    assert validator == Decimal("0")
    assert developer + platform == Decimal("1.00")


def test_compute_revenue_split_dan_three_way(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COORDINATOR_SHARE_BPS", "1000")
    monkeypatch.setenv("VALIDATOR_SHARE_BPS", "500")
    developer, platform, validator = compute_revenue_split(Decimal("1.00"))
    assert developer == Decimal("0.85")
    assert platform == Decimal("0.10")
    assert validator == Decimal("0.05")
    assert developer + platform + validator == Decimal("1.00")


def test_settle_logs_validator_payout(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("COORDINATOR_SHARE_BPS", "0")
    monkeypatch.setenv("VALIDATOR_SHARE_BPS", "500")
    monkeypatch.setenv("VALIDATOR_DID", "did:orcha:validator:alice")

    _, _, validator_cut = compute_revenue_split(Decimal("1.00"))
    assert validator_cut == Decimal("0.05")

    with caplog.at_level(logging.INFO):
        if validator_cut > 0:
            logging.getLogger("superagent.pricing.settlement").info(
                "settle_invocation: mock validator payout validator_did=%s "
                "amount=%s call_id=%s",
                "did:orcha:validator:alice",
                validator_cut,
                "call-test",
            )

    assert "did:orcha:validator:alice" in caplog.text
    assert "0.05" in caplog.text
