from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.retest_opportunity import build_fvg_ob_retest_opportunity_report
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2026-05-24T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100},
            {"timestamp": "2026-05-24T00:01:00Z", "open": 101, "high": 112, "low": 100, "close": 110},
            {"timestamp": "2026-05-24T00:02:00Z", "open": 110, "high": 113, "low": 108, "close": 111},
        ]
    )


def _metadata(*, side: str = "LONG", pattern: str = "FAIR_VALUE_GAP", entry_mode: str = "LIMIT_AT_ENTRY_REFERENCE"):
    return {
        "pattern_type": pattern,
        "pattern_direction": "BULLISH" if side == "LONG" else "BEARISH",
        "position_side": side,
        "confirmation_close": 100.0 if side == "LONG" else 110.0,
        "target_reference": 110.0 if side == "LONG" else 100.0,
        "bars_waited": 2,
        "volume_ratio": 1.5,
        "displacement_range_atr": 2.2,
        "pattern_entry_policy": {
            "schema_version": "pattern_entry_policy_v1",
            "entry_mode": entry_mode,
            "entry_style": "RETEST_LIMIT" if entry_mode.startswith("LIMIT") else "CHASE_OR_MOMENTUM",
        },
    }


def test_retest_not_filled_records_missed_move_and_market_target_hit() -> None:
    action = StrategyAction(
        StrategyActionType.SKIP,
        "2026-05-24T00:00:00Z",
        quantity=0.0,
        reason="ENTRY_NOT_FILLED",
        metadata=_metadata(),
    )

    report = build_fvg_ob_retest_opportunity_report([action], _candles())
    fvg = report["patterns"]["FAIR_VALUE_GAP"]

    assert fvg["not_filled_count"] == 1
    assert fvg["missed_trade_count"] == 1
    assert fvg["market_entry_target_hit_count"] == 1
    assert fvg["average_missed_mfe"] == 13.0


def test_retest_filled_after_n_bars_records_bars_waited_and_adverse_excursion() -> None:
    action = StrategyAction(
        StrategyActionType.ENTER_LONG,
        "2026-05-24T00:02:00Z",
        quantity=1.0,
        reason="PATTERN_CONFIRMED",
        metadata={**_metadata(), "fill_price": 109.0, "bars_waited": 2},
        requested_price=109.0,
    )

    report = build_fvg_ob_retest_opportunity_report([action], _candles())
    fvg = report["patterns"]["FAIR_VALUE_GAP"]

    assert fvg["filled_count"] == 1
    assert fvg["fill_rate"] == 1.0
    assert fvg["average_bars_waited"] == 2.0
    assert fvg["average_adverse_excursion_after_fill"] == 1.0


def test_long_short_opportunity_cost_symmetry() -> None:
    long_action = StrategyAction(
        StrategyActionType.SKIP,
        "2026-05-24T00:00:00Z",
        quantity=0.0,
        reason="ENTRY_NOT_FILLED",
        metadata=_metadata(side="LONG"),
    )
    short_candles = pd.DataFrame(
        [
            {"timestamp": "2026-05-24T00:00:00Z", "open": 110, "high": 111, "low": 109, "close": 110},
            {"timestamp": "2026-05-24T00:01:00Z", "open": 109, "high": 110, "low": 98, "close": 100},
        ]
    )
    short_action = StrategyAction(
        StrategyActionType.SKIP,
        "2026-05-24T00:00:00Z",
        quantity=0.0,
        reason="ENTRY_NOT_FILLED",
        metadata=_metadata(side="SHORT", pattern="ORDER_BLOCK"),
    )

    long_report = build_fvg_ob_retest_opportunity_report([long_action], _candles())
    short_report = build_fvg_ob_retest_opportunity_report([short_action], short_candles)

    assert long_report["patterns"]["FAIR_VALUE_GAP"]["market_entry_target_hit_count"] == 1
    assert short_report["patterns"]["ORDER_BLOCK"]["market_entry_target_hit_count"] == 1
    assert short_report["patterns"]["ORDER_BLOCK"]["average_missed_mfe"] == 12.0


def test_report_includes_fvg_and_order_block_sections() -> None:
    actions = [
        StrategyAction(
            StrategyActionType.SKIP,
            "2026-05-24T00:00:00Z",
            quantity=0.0,
            reason="ENTRY_NOT_FILLED",
            metadata=_metadata(pattern="FAIR_VALUE_GAP"),
        ),
        StrategyAction(
            StrategyActionType.SKIP,
            "2026-05-24T00:00:00Z",
            quantity=0.0,
            reason="ENTRY_NOT_FILLED",
            metadata=_metadata(pattern="ORDER_BLOCK"),
        ),
    ]

    report = build_fvg_ob_retest_opportunity_report(actions, _candles())

    assert report["schema_version"] == "fvg_ob_retest_opportunity_v1"
    assert set(report["patterns"]) == {"FAIR_VALUE_GAP", "ORDER_BLOCK"}
    assert report["overall"]["groups"]["entry_mode"]["LIMIT_AT_ENTRY_REFERENCE"]["signal_count"] == 2
