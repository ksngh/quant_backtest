from __future__ import annotations

from quant_bitcoin.backtesting.multitimeframe_candles import align_completed_higher_timeframe_candles
from quant_bitcoin.indicators.pivots import PivotConfig, detect_pivots
from quant_bitcoin.indicators import AtrConfig, VolumeRatioConfig
from quant_bitcoin.patterns import FairValueGapConfig, detect_fair_value_gaps
from quant_bitcoin.patterns.entry_simulation import (
    PatternEntryConfig,
    PatternEntryMode,
    PatternEntryTrigger,
    create_entry_plan_from_event,
    simulate_pattern_entry,
)
from tests.fixtures.synthetic_fvg_v2 import (
    bearish_retest_v2_scenario,
    bullish_retest_v2_scenario,
    expected_diagnostic_keys,
)


def test_fvg_v2_fixture_shapes_and_scenario_labels() -> None:
    bullish = bullish_retest_v2_scenario()
    bearish = bearish_retest_v2_scenario()

    assert bullish.name == "bullish_retest_v2_aligned_confluent"
    assert bearish.name == "bearish_retest_v2_aligned_confluent"
    assert len(bullish.candles) == 46
    assert len(bearish.candles) == 46
    assert set(("timestamp", "open", "high", "low", "close", "volume")).issubset(bullish.candles.columns)


def test_fvg_v2_fixture_detects_bullish_and_bearish_events_without_default_change() -> None:
    config = _fvg_test_config()

    bullish_events = detect_fair_value_gaps(bullish_retest_v2_scenario().candles.iloc[:11], config=config)
    bearish_events = detect_fair_value_gaps(bearish_retest_v2_scenario().candles.iloc[:11], config=config)

    assert any(event.direction == "BULLISH" and event.end_index == 10 for event in bullish_events)
    assert any(event.direction == "BEARISH" and event.end_index == 10 for event in bearish_events)


def test_fvg_v2_multitimeframe_visibility_helper_has_no_lookahead() -> None:
    scenario = bullish_retest_v2_scenario()
    result = align_completed_higher_timeframe_candles(
        scenario.candles,
        source_interval="1m",
        target_intervals=("5m", "15m"),
    )

    assert not bool(result.candles.loc[4, "mtf_5m_available"])
    assert bool(result.candles.loc[5, "mtf_5m_available"])
    assert not bool(result.candles.loc[14, "mtf_15m_available"])
    assert bool(result.candles.loc[15, "mtf_15m_available"])


def test_fvg_v2_pivot_confirmation_delay_fixture() -> None:
    scenario = bullish_retest_v2_scenario()
    pivots = detect_pivots(
        scenario.candles[["symbol", "timestamp", "open", "high", "low", "close"]],
        PivotConfig(left_window=1, right_window=1, minimum_distance_between_pivots=1),
    )

    assert not pivots.empty
    assert (pivots["confirmed_index"] > pivots["pivot_index"]).all()
    assert pivots["confirmed_index"].max() <= len(scenario.candles) - 1


def test_fvg_v2_reaction_entry_fixture_distinguishes_touch_without_reaction() -> None:
    scenario = bullish_retest_v2_scenario()
    event = [event for event in detect_fair_value_gaps(scenario.candles.iloc[:11], config=_fvg_test_config()) if event.end_index == 10][0]
    plan = create_entry_plan_from_event(event, PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT, "LONG")
    reaction_plan = plan.__class__(
        mode=plan.mode,
        direction=plan.direction,
        limit_price=plan.limit_price,
        config=PatternEntryConfig(max_wait_bars=2, entry_trigger=PatternEntryTrigger.TOUCH_AND_REACTION_CLOSE),
        event_id=plan.event_id,
        pattern_type=plan.pattern_type,
        metadata=plan.metadata,
    )

    result = simulate_pattern_entry(reaction_plan, scenario.candles.iloc[10], scenario.candles.iloc[11:13])

    assert result.status.value == "NOT_FILLED"
    assert result.touch_candle_index is not None
    assert result.reaction_candle_index is None


def test_fvg_v2_expected_diagnostic_snapshot_keys() -> None:
    assert {"fvg_retest_v2", "fvg_entry_mode"}.issubset(expected_diagnostic_keys())


def _fvg_test_config() -> FairValueGapConfig:
    return FairValueGapConfig(
        require_displacement_candle=False,
        minimum_volume_ratio=0.0,
        minimum_pattern_score=0.0,
        atr_config=AtrConfig(period=1),
        volume_ratio_config=VolumeRatioConfig(window=1, require_full_window=False),
    )
