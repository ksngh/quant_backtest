from __future__ import annotations

import inspect

import pytest

from quant_bitcoin.indicators import fibonacci_retracement
from quant_bitcoin.indicators.fibonacci_retracement import (
    FibonacciOverlapMode,
    FibonacciRetracementConfig,
    evaluate_fibonacci_retracement_confluence,
)


def test_bullish_retracement_midpoint_confluence_passes() -> None:
    result = evaluate_fibonacci_retracement_confluence(
        direction="BULLISH",
        anchor_low=94,
        anchor_high=108,
        zone_low=100,
        zone_high=102,
    )

    assert result["confluence_pass"] is True
    assert result["retracement_level_at_zone_mid"] == pytest.approx(0.5)
    assert result["band_low"] == pytest.approx(99.348)
    assert result["band_high"] == pytest.approx(102.652)


def test_bearish_retracement_midpoint_confluence_passes() -> None:
    result = evaluate_fibonacci_retracement_confluence(
        direction="BEARISH",
        anchor_low=92,
        anchor_high=108,
        zone_low=100,
        zone_high=102,
    )

    assert result["confluence_pass"] is True
    assert result["retracement_level_at_zone_mid"] == pytest.approx(0.5625)


def test_zone_overlap_modes_are_direction_aware() -> None:
    midpoint_fail = evaluate_fibonacci_retracement_confluence(
        direction="BULLISH",
        anchor_low=90,
        anchor_high=110,
        zone_low=96,
        zone_high=99,
        config=FibonacciRetracementConfig(overlap_mode=FibonacciOverlapMode.MIDPOINT),
    )
    any_overlap = evaluate_fibonacci_retracement_confluence(
        direction="BULLISH",
        anchor_low=90,
        anchor_high=110,
        zone_low=96,
        zone_high=99,
        config=FibonacciRetracementConfig(overlap_mode=FibonacciOverlapMode.ANY_ZONE_OVERLAP),
    )

    assert midpoint_fail["confluence_pass"] is False
    assert any_overlap["confluence_pass"] is True


def test_fibonacci_tolerance_expands_band_by_atr() -> None:
    result = evaluate_fibonacci_retracement_confluence(
        direction="BULLISH",
        anchor_low=90,
        anchor_high=110,
        zone_low=95.5,
        zone_high=96,
        atr=10,
        config=FibonacciRetracementConfig(tolerance_atr_multiplier=0.2),
    )

    assert result["tolerance"] == pytest.approx(2.0)
    assert result["confluence_pass"] is True


def test_invalid_anchor_returns_explicit_unavailable_metadata() -> None:
    result = evaluate_fibonacci_retracement_confluence(
        direction="BULLISH",
        anchor_low=100,
        anchor_high=100,
        zone_low=99,
        zone_high=101,
    )

    assert result["feature_available"] is False
    assert result["confluence_pass"] is False
    assert result["reason"] == "INVALID_ANCHOR_RANGE"


def test_fibonacci_config_validation() -> None:
    with pytest.raises(ValueError, match="min_level must be between 0 and 1"):
        FibonacciRetracementConfig(min_level=-0.1)
    with pytest.raises(ValueError, match="min_level must be less than or equal"):
        FibonacciRetracementConfig(min_level=0.7, max_level=0.6)
    with pytest.raises(ValueError, match="tolerance_atr_multiplier must be non-negative"):
        FibonacciRetracementConfig(tolerance_atr_multiplier=-0.1)


def test_fibonacci_module_has_no_exchange_or_network_coupling() -> None:
    source = inspect.getsource(fibonacci_retracement)

    assert "binance" not in source.lower()
    assert "requests" not in source
    assert "urllib" not in source
    assert "signed" not in source.lower()
