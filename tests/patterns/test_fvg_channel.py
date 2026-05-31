from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.patterns.fvg_channel import (
    ChannelEntrySide,
    ChannelRetestEntry,
    ChannelBoundary,
    ChannelTrendDirection,
    FvgChannelConfig,
    channel_id,
    detect_fvg_parallel_channel,
    simulate_channel_boundary_exit,
    simulate_channel_retest_entry,
)
from quant_bitcoin.risk.exit_simulation import PatternExitReason


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": index,
                "open": row.get("open", row.get("close", 100.0)),
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
            }
            for index, row in enumerate(rows)
        ]
    )


def test_detects_parallel_channel_with_upper_touch_between_low_anchors() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
        ]
    )

    channel = detect_fvg_parallel_channel(candles, FvgChannelConfig(enabled=True, window=3))

    assert channel is not None
    assert channel.lower_anchor_1_index == 0
    assert channel.lower_anchor_2_index == 2
    assert channel.upper_touch_index == 1
    assert channel.trend_direction is ChannelTrendDirection.UPTREND
    assert channel.lower_line.slope == pytest.approx(1.0)
    assert channel.lower_at(3) == pytest.approx(103.0)
    assert channel.upper_at(3) == pytest.approx(113.0)
    metadata = channel.to_metadata()
    assert metadata["schema_version"] == "fvg_parallel_channel_v1"
    assert metadata["channel_trend_direction"] == "UPTREND"
    assert metadata["channel_boundary_direction_rule"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert metadata["all_candles_fit_inside_channel"] is True
    assert metadata["atr_used_for_stop_or_target"] is False
    assert metadata["channel_id"] == channel_id(channel)
    assert metadata["channel_identity"]["lower_anchor_1_index"] == 0
    assert metadata["channel_identity"]["lower_anchor_2_index"] == 2


def test_detects_downtrend_parallel_channel_with_lower_touch_between_high_anchors() -> None:
    candles = _frame(
        [
            {"high": 110.0, "low": 103.0, "close": 104.0},
            {"high": 105.0, "low": 100.0, "close": 101.0},
            {"high": 108.0, "low": 102.0, "close": 103.0},
        ]
    )

    channel = detect_fvg_parallel_channel(candles, FvgChannelConfig(enabled=True, window=3))

    assert channel is not None
    assert channel.trend_direction is ChannelTrendDirection.DOWNTREND
    assert channel.upper_anchor_1_index == 0
    assert channel.upper_anchor_2_index == 2
    assert channel.lower_touch_index == 1
    assert channel.upper_line.slope == pytest.approx(-1.0)
    assert channel.upper_at(3) == pytest.approx(107.0)
    assert channel.lower_at(3) == pytest.approx(98.0)
    metadata = channel.to_metadata()
    assert metadata["channel_trend_direction"] == "DOWNTREND"
    assert metadata["upper_anchor_1_index"] == 0
    assert metadata["upper_anchor_2_index"] == 2
    assert metadata["lower_touch_index"] == 1


def test_channel_identity_is_stable_for_same_geometry_across_calls() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)

    first = detect_fvg_parallel_channel(candles, config)
    second = detect_fvg_parallel_channel(candles.copy(), config)

    assert first is not None
    assert second is not None
    assert channel_id(first) == channel_id(second)
    assert first.to_metadata()["channel_identity"] == second.to_metadata()["channel_identity"]


def test_rejects_channel_without_intervening_upper_touch() -> None:
    candles = _frame(
        [
            {"high": 104.0, "low": 100.0, "close": 103.0},
            {"high": 105.0, "low": 101.0, "close": 104.0},
            {"high": 106.0, "low": 102.0, "close": 105.0},
            {"high": 120.0, "low": 103.0, "close": 119.0},
        ]
    )

    assert detect_fvg_parallel_channel(candles, FvgChannelConfig(enabled=True, window=4)) is None


def test_rejects_channel_when_low_breaks_lower_line_or_slope_is_not_upward() -> None:
    low_break = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 107.0, "low": 99.0, "close": 100.0},
        ]
    )
    non_upward = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 99.0, "close": 110.0},
            {"high": 107.0, "low": 98.0, "close": 106.0},
        ]
    )

    assert detect_fvg_parallel_channel(low_break, FvgChannelConfig(enabled=True, window=4)) is None
    assert detect_fvg_parallel_channel(non_upward, FvgChannelConfig(enabled=True, window=3)) is None


def test_channel_retest_long_enters_on_upper_line_and_exits_at_projected_width_target() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 109.0, "close": 113.2},
            {"high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])
    assert entry is not None
    assert entry.side is ChannelEntrySide.LONG
    assert entry.entry_boundary is ChannelBoundary.UPPER
    assert entry.fill_price == pytest.approx(113.2)
    assert entry.stop_price == pytest.approx(102.0)
    assert entry.target_price == pytest.approx(123.2)
    assert entry.stop_source == "PRE_RETEST_CANDLE_LOW"
    assert entry.retest_structure_low == pytest.approx(109.0)
    assert entry.metadata["stop_source"] == "PRE_RETEST_CANDLE_LOW"
    assert entry.metadata["retest_structure_low"] == pytest.approx(109.0)
    assert entry.metadata["pre_retest_stop_valid"] is True
    assert entry.metadata["pre_retest_candle_index"] == 2
    assert entry.metadata["pre_retest_candle_low"] == pytest.approx(102.0)
    assert entry.metadata["pre_retest_candle_high"] == pytest.approx(107.0)
    assert entry.metadata["channel_lower_line_price_at_entry"] == pytest.approx(103.0)
    assert entry.metadata["line_stop_price_diagnostic"] == pytest.approx(103.0)
    assert entry.metadata["channel_width_at_entry"] == pytest.approx(10.0)
    assert entry.metadata["retest_confirmation_basis"] == "CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1"
    assert entry.metadata["retest_confirmation_price_source"] == "close"
    assert entry.metadata["retest_close_rule"] == "close >= upper_channel_line"
    assert entry.metadata["entry_trigger"] == "UPPER_CLOSE_BASED_RETEST"
    assert entry.metadata["target_price_source"] == "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE"
    assert entry.metadata["projected_channel_width_target"] == pytest.approx(123.2)
    assert entry.metadata["opposite_boundary_target_price"] == pytest.approx(113.0)
    assert entry.metadata["channel_boundary_direction_mode"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert entry.metadata["original_channel_entry_side"] == "SHORT"
    assert entry.metadata["effective_channel_entry_side"] == "LONG"
    assert entry.metadata["atr_used_for_stop_or_target"] is False

    exit_event = simulate_channel_boundary_exit(channel, entry, candles.iloc[3:])
    assert exit_event is not None
    assert exit_event.reason is PatternExitReason.TAKE_PROFIT
    assert exit_event.price == pytest.approx(123.2)
    assert exit_event.metadata["target_boundary"] == "CHANNEL_WIDTH_TARGET"
    assert exit_event.metadata["line_target_price"] == pytest.approx(123.2)
    assert exit_event.metadata["target_source"] == "FVG_V2_CHANNEL_WIDTH_PROJECTION"
    assert exit_event.metadata["atr_used_for_stop_or_target"] is False


def test_channel_retest_rejects_upper_wick_without_close_confirmation() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 109.0, "close": 112.5},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    assert simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3]) is None


def test_channel_retest_marks_missing_pre_retest_candle_stop_invalid() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 109.0, "close": 113.2},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config)

    assert entry is not None
    assert entry.metadata["pre_retest_stop_valid"] is False
    assert entry.metadata["pre_retest_stop_invalid_reason"] == "PRE_RETEST_CANDLE_MISSING"


def test_channel_retest_marks_invalid_pre_retest_stop_relation() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 109.0, "close": 113.2},
        ]
    )
    invalid_context = pd.DataFrame(
        [{"timestamp": 2, "open": 120.0, "high": 121.0, "low": 120.0, "close": 120.0}],
        index=[2],
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=invalid_context)

    assert entry is not None
    assert entry.stop_price == pytest.approx(120.0)
    assert entry.metadata["pre_retest_stop_valid"] is False
    assert entry.metadata["pre_retest_stop_invalid_reason"] == "LONG_PRE_RETEST_LOW_NOT_BELOW_ENTRY"


def test_channel_long_stop_uses_pre_retest_candle_low() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 109.0, "close": 113.2},
            {"high": 110.0, "low": 101.9, "close": 104.1},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None
    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])
    assert entry is not None

    exit_event = simulate_channel_boundary_exit(channel, entry, candles.iloc[3:])

    assert exit_event is not None
    assert exit_event.reason is PatternExitReason.HARD_STOP
    assert exit_event.price == pytest.approx(102.0)
    assert exit_event.metadata["stop_boundary"] == "LOWER"
    assert exit_event.metadata["stop_source"] == "PRE_RETEST_CANDLE_LOW"
    assert exit_event.metadata["retest_structure_low"] == pytest.approx(109.0)


def test_channel_long_entry_allows_missing_diagnostic_structure_low() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 113.4, "low": 0.0, "close": 113.2},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])

    assert entry is not None
    assert entry.side is ChannelEntrySide.LONG
    assert entry.stop_source == "PRE_RETEST_CANDLE_LOW"
    assert entry.retest_structure_low is None
    assert entry.metadata["stop_source"] == "PRE_RETEST_CANDLE_LOW"
    assert entry.metadata["retest_structure_low"] is None
    assert entry.metadata["pre_retest_candle_low"] == pytest.approx(102.0)


def test_channel_retest_short_enters_on_lower_line_and_exits_at_projected_width_target() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 108.0, "low": 102.8, "close": 102.8},
            {"high": 106.5, "low": 92.0, "close": 93.0},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])
    assert entry is not None
    assert entry.side is ChannelEntrySide.SHORT
    assert entry.entry_boundary is ChannelBoundary.LOWER
    assert entry.fill_price == pytest.approx(102.8)
    assert entry.stop_price == pytest.approx(107.0)
    assert entry.target_price == pytest.approx(92.8)
    assert entry.stop_source == "PRE_RETEST_CANDLE_HIGH"
    assert entry.metadata["stop_source"] == "PRE_RETEST_CANDLE_HIGH"
    assert entry.metadata["pre_retest_stop_valid"] is True
    assert entry.metadata["pre_retest_candle_index"] == 2
    assert entry.metadata["pre_retest_candle_low"] == pytest.approx(102.0)
    assert entry.metadata["pre_retest_candle_high"] == pytest.approx(107.0)
    assert entry.metadata["line_stop_price_diagnostic"] == pytest.approx(113.0)
    assert entry.metadata["channel_width_at_entry"] == pytest.approx(10.0)
    assert entry.metadata["retest_confirmation_basis"] == "CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1"
    assert entry.metadata["retest_confirmation_price_source"] == "close"
    assert entry.metadata["retest_close_rule"] == "close <= lower_channel_line"
    assert entry.metadata["entry_trigger"] == "LOWER_CLOSE_BASED_RETEST"
    assert entry.metadata["target_price_source"] == "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE"
    assert entry.metadata["projected_channel_width_target"] == pytest.approx(92.8)
    assert entry.metadata["opposite_boundary_target_price"] == pytest.approx(103.0)
    assert entry.metadata["original_channel_entry_side"] == "LONG"
    assert entry.metadata["effective_channel_entry_side"] == "SHORT"

    exit_event = simulate_channel_boundary_exit(channel, entry, candles.iloc[3:])
    assert exit_event is not None
    assert exit_event.reason is PatternExitReason.TAKE_PROFIT
    assert exit_event.price == pytest.approx(92.8)
    assert exit_event.metadata["target_boundary"] == "CHANNEL_WIDTH_TARGET"
    assert exit_event.metadata["target_source"] == "FVG_V2_CHANNEL_WIDTH_PROJECTION"


def test_channel_retest_rejects_lower_wick_without_close_confirmation() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 108.0, "low": 102.8, "close": 104.0},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    assert simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3]) is None


def test_channel_short_stop_and_same_candle_ambiguity_are_explicit() -> None:
    candles = _frame(
        [
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 111.0, "low": 101.0, "close": 110.0},
            {"high": 107.0, "low": 102.0, "close": 106.0},
            {"high": 108.0, "low": 102.8, "close": 102.8},
            {"high": 114.2, "low": 103.9, "close": 113.8},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None
    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])
    assert entry is not None

    stop_exit = simulate_channel_boundary_exit(channel, entry, candles.iloc[3:])
    assert stop_exit is not None
    assert stop_exit.reason is PatternExitReason.HARD_STOP
    assert stop_exit.price == pytest.approx(107.0)
    assert stop_exit.metadata["stop_boundary"] == "UPPER"

    ambiguous_entry = ChannelRetestEntry(
        side=ChannelEntrySide.LONG,
        timestamp=candles.iloc[4]["timestamp"],
        fill_price=110.0,
        candle_index=4,
        touch_index=4,
        confirmation_index=4,
        entry_boundary=ChannelBoundary.UPPER,
        stop_price=104.0,
        target_price=114.0,
        metadata={},
    )
    ambiguous_exit = simulate_channel_boundary_exit(
        channel,
        ambiguous_entry,
        candles.iloc[4:],
        allow_same_candle_exit=True,
    )
    assert ambiguous_exit is not None
    assert ambiguous_exit.reason is PatternExitReason.HARD_STOP
    assert ambiguous_exit.metadata["same_candle_entry_exit_ambiguity"] is True
    assert ambiguous_exit.metadata["ambiguous_stop_target"] is True


def test_downtrend_upper_boundary_retest_enters_long() -> None:
    candles = _frame(
        [
            {"high": 110.0, "low": 103.0, "close": 104.0},
            {"high": 105.0, "low": 100.0, "close": 101.0},
            {"high": 108.0, "low": 102.0, "close": 103.0},
            {"high": 107.2, "low": 103.0, "close": 107.1},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])

    assert entry is not None
    assert entry.side is ChannelEntrySide.LONG
    assert entry.entry_boundary is ChannelBoundary.UPPER
    assert entry.metadata["channel_trend_direction"] == "DOWNTREND"


def test_downtrend_lower_boundary_retest_enters_short() -> None:
    candles = _frame(
        [
            {"high": 110.0, "low": 103.0, "close": 104.0},
            {"high": 105.0, "low": 100.0, "close": 101.0},
            {"high": 108.0, "low": 102.0, "close": 103.0},
            {"high": 102.0, "low": 97.8, "close": 97.9},
        ]
    )
    config = FvgChannelConfig(enabled=True, window=3)
    channel = detect_fvg_parallel_channel(candles.iloc[:3], config)
    assert channel is not None

    entry = simulate_channel_retest_entry(channel, candles.iloc[3:], config, context_candles=candles.iloc[:3])

    assert entry is not None
    assert entry.side is ChannelEntrySide.SHORT
    assert entry.entry_boundary is ChannelBoundary.LOWER
    assert entry.metadata["channel_trend_direction"] == "DOWNTREND"
