from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.trendline_forensics import build_trendline_false_breakout_forensics
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _action(side: str = "LONG", timestamp: str = "2026-05-24T00:00:00Z") -> StrategyAction:
    return StrategyAction(
        StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT,
        timestamp,
        quantity=1.0,
        reason="PATTERN_CONFIRMED",
        requested_price=100.0,
        metadata={
            "pattern_type": "TRENDLINE_BREAK",
            "event_id": "tl1",
            "position_side": side,
            "trendline_value": 99.0 if side == "LONG" else 101.0,
            "fill_price": 100.0,
            "risk_per_unit": 2.0,
            "touch_count": 3,
            "trendline_slope": -0.5,
            "break_distance_atr": 1.2,
            "volume_ratio": 1.4,
            "displacement_confirmed": True,
            "pivot_metadata": {"confirmation_delay": 2},
        },
    )


def test_bullish_close_back_below_trendline_classified_failed_breakout() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2026-05-24T00:00:00Z", "open": 100, "high": 100.5, "low": 98, "close": 98.5},
            {"timestamp": "2026-05-24T00:01:00Z", "open": 98.5, "high": 99, "low": 97, "close": 97.5},
        ]
    )

    report = build_trendline_false_breakout_forensics([_action("LONG")], candles)

    record = report["records"][0]
    assert record["outcome"] == "failed_breakout"
    assert record["bars_to_reentry"] == 1
    assert report["outcomes"]["failed_breakout"] == 1


def test_bearish_close_back_above_trendline_is_symmetric() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2026-05-24T00:00:00Z", "open": 100, "high": 102, "low": 99.5, "close": 102},
            {"timestamp": "2026-05-24T00:01:00Z", "open": 102, "high": 103, "low": 101, "close": 102.5},
        ]
    )

    report = build_trendline_false_breakout_forensics([_action("SHORT")], candles)

    assert report["records"][0]["outcome"] == "failed_breakout"
    assert report["records"][0]["bars_to_reentry"] == 1


def test_strong_follow_through_classified_immediate_continuation() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2026-05-24T00:00:00Z", "open": 100, "high": 103, "low": 99.5, "close": 102},
            {"timestamp": "2026-05-24T00:01:00Z", "open": 102, "high": 105, "low": 101, "close": 104},
        ]
    )

    report = build_trendline_false_breakout_forensics([_action("LONG")], candles)

    assert report["records"][0]["outcome"] == "immediate_follow_through"
    assert report["records"][0]["max_favorable_r_before_reentry"] == 2.5
    assert report["groups"]["touch_count"]["3"]["event_count"] == 1


def test_trendline_forensics_schema_present_for_empty_run() -> None:
    report = build_trendline_false_breakout_forensics([], pd.DataFrame())

    assert report["schema_version"] == "trendline_false_breakout_forensics_v1"
    assert report["event_count"] == 0
