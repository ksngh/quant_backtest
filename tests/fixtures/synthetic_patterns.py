from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from quant_bitcoin.indicators import (
    AtrConfig,
    DisplacementCandleConfig,
    PivotConfig,
    VolumeRatioConfig,
)
from quant_bitcoin.patterns import (
    AdamAndEveConfig,
    CupAndHandleConfig,
    DiamondConfig,
    FairValueGapConfig,
    OrderBlockConfig,
    TrendlineBreakConfig,
    detect_adam_and_eve_patterns,
    detect_adam_and_eve_patterns_at_index,
    detect_cup_and_handle_patterns,
    detect_cup_and_handle_patterns_at_index,
    detect_diamond_patterns,
    detect_diamond_patterns_at_index,
    detect_fair_value_gaps,
    detect_fair_value_gaps_at_index,
    detect_order_blocks,
    detect_order_blocks_at_index,
    detect_trendline_breaks,
    detect_trendline_breaks_at_index,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryMode


Detector = Callable[..., list[Any]]


@dataclass(frozen=True)
class SyntheticEntryCase:
    name: str
    mode: PatternEntryMode
    should_fill: bool
    max_wait_bars: int | None = None


@dataclass(frozen=True)
class SyntheticExitCase:
    name: str
    description: str


@dataclass(frozen=True)
class SyntheticPatternFixture:
    pattern_type: str
    direction: str
    position_side: str
    valid_candles: pd.DataFrame
    invalid_candles: pd.DataFrame
    config: Any
    current_index: int
    detect_all: Detector
    detect_at_index: Detector
    entry_cases: tuple[SyntheticEntryCase, ...]
    exit_cases: tuple[SyntheticExitCase, ...]
    unsupported_inverse_direction: str | None = None
    unsupported_inverse_candles: pd.DataFrame | None = None


STANDARD_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def all_pattern_fixtures() -> tuple[SyntheticPatternFixture, ...]:
    return (
        fair_value_gap_bullish_fixture(),
        fair_value_gap_bearish_fixture(),
        order_block_bullish_fixture(),
        order_block_bearish_fixture(),
        trendline_bullish_fixture(),
        trendline_bearish_fixture(),
        cup_and_handle_bullish_fixture(),
        diamond_bullish_fixture(),
        diamond_bearish_fixture(),
        adam_and_eve_bullish_fixture(),
    )


def fair_value_gap_bullish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="FAIR_VALUE_GAP",
        direction="BULLISH",
        position_side="LONG",
        valid_candles=_rows(
            [
                {"open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0},
                {"open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
                {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
            ]
        ),
        invalid_candles=_flat_candles(3),
        config=_fvg_config(),
        current_index=2,
        detect_all=detect_fair_value_gaps,
        detect_at_index=detect_fair_value_gaps_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def fair_value_gap_bearish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="FAIR_VALUE_GAP",
        direction="BEARISH",
        position_side="SHORT",
        valid_candles=_rows(
            [
                {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
                {"open": 107.0, "high": 108.0, "low": 94.0, "close": 95.0, "volume": 500.0},
                {"open": 99.0, "high": 100.0, "low": 96.0, "close": 98.0},
            ]
        ),
        invalid_candles=_flat_candles(3),
        config=_fvg_config(),
        current_index=2,
        detect_all=detect_fair_value_gaps,
        detect_at_index=detect_fair_value_gaps_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def order_block_bullish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="ORDER_BLOCK",
        direction="BULLISH",
        position_side="LONG",
        valid_candles=_rows(
            [
                {"open": 100.0, "high": 100.0, "low": 99.0, "close": 99.2},
                {"open": 99.2, "high": 110.0, "low": 98.0, "close": 109.5, "volume": 500.0},
            ]
        ),
        invalid_candles=_flat_candles(3),
        config=_ob_config(),
        current_index=1,
        detect_all=detect_order_blocks,
        detect_at_index=detect_order_blocks_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def order_block_bearish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="ORDER_BLOCK",
        direction="BEARISH",
        position_side="SHORT",
        valid_candles=_rows(
            [
                {"open": 99.0, "high": 100.0, "low": 99.0, "close": 99.8},
                {"open": 99.8, "high": 101.0, "low": 89.0, "close": 89.5, "volume": 500.0},
            ]
        ),
        invalid_candles=_flat_candles(3),
        config=_ob_config(),
        current_index=1,
        detect_all=detect_order_blocks,
        detect_at_index=detect_order_blocks_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def trendline_bullish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="TRENDLINE_BREAK",
        direction="BULLISH",
        position_side="LONG",
        valid_candles=_rows(
            [
                {"open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0},
                {"open": 14.0, "high": 15.0, "low": 9.0, "close": 14.0},
                {"open": 11.0, "high": 12.0, "low": 8.0, "close": 11.0},
                {"open": 12.0, "high": 13.0, "low": 9.0, "close": 12.0},
                {"open": 13.0, "high": 14.0, "low": 9.0, "close": 13.0},
                {"open": 11.0, "high": 12.0, "low": 8.0, "close": 12.0},
                {"open": 11.0, "high": 14.5, "low": 11.0, "close": 14.2, "volume": 500.0},
            ],
            base_price=10.0,
        ),
        invalid_candles=_flat_candles(4, base_price=10.0),
        config=_trendline_config(),
        current_index=6,
        detect_all=detect_trendline_breaks,
        detect_at_index=detect_trendline_breaks_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def trendline_bearish_fixture() -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="TRENDLINE_BREAK",
        direction="BEARISH",
        position_side="SHORT",
        valid_candles=_rows(
            [
                {"open": 10.0, "high": 12.0, "low": 8.0, "close": 10.0},
                {"open": 6.0, "high": 11.0, "low": 5.0, "close": 6.0},
                {"open": 9.0, "high": 12.0, "low": 7.0, "close": 9.0},
                {"open": 8.0, "high": 11.0, "low": 7.0, "close": 8.0},
                {"open": 7.0, "high": 10.0, "low": 6.0, "close": 7.0},
                {"open": 8.0, "high": 11.0, "low": 7.0, "close": 8.0},
                {"open": 8.5, "high": 8.5, "low": 5.3, "close": 5.8, "volume": 500.0},
            ],
            base_price=10.0,
        ),
        invalid_candles=_flat_candles(4, base_price=10.0),
        config=_trendline_config(),
        current_index=6,
        detect_all=detect_trendline_breaks,
        detect_at_index=detect_trendline_breaks_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def cup_and_handle_bullish_fixture() -> SyntheticPatternFixture:
    valid = _rows(
        [
            {"open": 90.0, "high": 92.0, "low": 89.0, "close": 91.0},
            {"open": 96.0, "high": 100.0, "low": 95.0, "close": 99.0},
            {"open": 92.0, "high": 93.0, "low": 88.0, "close": 89.0},
            {"open": 82.0, "high": 83.0, "low": 80.0, "close": 81.0},
            {"open": 81.0, "high": 82.0, "low": 79.0, "close": 81.0},
            {"open": 81.0, "high": 82.0, "low": 80.0, "close": 81.0},
            {"open": 88.0, "high": 90.0, "low": 86.0, "close": 89.0},
            {"open": 96.0, "high": 99.0, "low": 95.0, "close": 98.0},
            {"open": 95.0, "high": 98.0, "low": 95.0, "close": 97.0},
            {"open": 96.0, "high": 97.0, "low": 94.0, "close": 95.0},
            {"open": 96.0, "high": 99.0, "low": 95.0, "close": 98.0},
            {"open": 99.0, "high": 104.0, "low": 98.0, "close": 103.0, "volume": 500.0},
        ]
    )
    return SyntheticPatternFixture(
        pattern_type="CUP_AND_HANDLE",
        direction="BULLISH",
        position_side="LONG",
        valid_candles=valid,
        invalid_candles=_flat_candles(8),
        config=_cup_config(),
        current_index=11,
        detect_all=detect_cup_and_handle_patterns,
        detect_at_index=detect_cup_and_handle_patterns_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
        unsupported_inverse_direction="BEARISH",
        unsupported_inverse_candles=_mirror_prices(valid),
    )


def diamond_bullish_fixture() -> SyntheticPatternFixture:
    return _diamond_fixture("BULLISH", "LONG", breakout_close=112.0)


def diamond_bearish_fixture() -> SyntheticPatternFixture:
    return _diamond_fixture("BEARISH", "SHORT", breakout_close=85.0)


def adam_and_eve_bullish_fixture() -> SyntheticPatternFixture:
    valid = _rows(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 90.0, "high": 92.0, "low": 88.0, "close": 89.0},
            {"open": 82.0, "high": 90.0, "low": 80.0, "close": 83.0},
            {"open": 88.0, "high": 92.0, "low": 86.0, "close": 90.0},
            {"open": 96.0, "high": 100.0, "low": 95.0, "close": 99.0},
            {"open": 90.0, "high": 93.0, "low": 86.0, "close": 88.0},
            {"open": 84.0, "high": 88.0, "low": 82.0, "close": 85.0},
            {"open": 83.0, "high": 87.0, "low": 81.0, "close": 84.0},
            {"open": 84.0, "high": 86.0, "low": 82.0, "close": 84.0},
            {"open": 84.0, "high": 87.0, "low": 83.0, "close": 85.0},
            {"open": 86.0, "high": 90.0, "low": 84.0, "close": 88.0},
            {"open": 90.0, "high": 95.0, "low": 89.0, "close": 94.0},
            {"open": 101.0, "high": 106.0, "low": 100.0, "close": 104.0, "volume": 500.0},
        ]
    )
    return SyntheticPatternFixture(
        pattern_type="ADAM_AND_EVE",
        direction="BULLISH",
        position_side="LONG",
        valid_candles=valid,
        invalid_candles=_flat_candles(8),
        config=_adam_config(),
        current_index=12,
        detect_all=detect_adam_and_eve_patterns,
        detect_at_index=detect_adam_and_eve_patterns_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
        unsupported_inverse_direction="BEARISH",
        unsupported_inverse_candles=_mirror_prices(valid),
    )


def _diamond_fixture(direction: str, position_side: str, *, breakout_close: float) -> SyntheticPatternFixture:
    return SyntheticPatternFixture(
        pattern_type="DIAMOND_PATTERN",
        direction=direction,
        position_side=position_side,
        valid_candles=_rows(
            [
                {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
                {"open": 104.0, "high": 105.0, "low": 103.0, "close": 104.0},
                {"open": 96.0, "high": 97.0, "low": 95.0, "close": 96.0},
                {"open": 114.0, "high": 115.0, "low": 113.0, "close": 114.0},
                {"open": 86.0, "high": 87.0, "low": 85.0, "close": 86.0},
                {"open": 109.0, "high": 110.0, "low": 108.0, "close": 109.0},
                {"open": 91.0, "high": 92.0, "low": 90.0, "close": 91.0},
                {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
                {"open": 97.0, "high": 98.0, "low": 96.0, "close": 97.0},
                {"open": 98.0, "high": 100.0, "low": 97.0, "close": 98.0},
                {"open": 111.0, "high": 113.0, "low": 84.0, "close": breakout_close, "volume": 500.0},
            ]
        ),
        invalid_candles=_flat_candles(6),
        config=_diamond_config(),
        current_index=10,
        detect_all=detect_diamond_patterns,
        detect_at_index=detect_diamond_patterns_at_index,
        entry_cases=_entry_cases(),
        exit_cases=_exit_cases(),
    )


def _rows(rows: list[dict[str, Any]], *, base_price: float = 100.0) -> pd.DataFrame:
    normalized = []
    for index, row in enumerate(rows):
        candle = {
            "timestamp": f"2026-05-16T00:{index:02d}:00Z",
            "open": base_price,
            "high": base_price + 1,
            "low": base_price - 1,
            "close": base_price,
            "volume": 100.0,
        }
        candle.update(row)
        normalized.append(candle)
    return pd.DataFrame(normalized, columns=STANDARD_COLUMNS)


def _flat_candles(count: int, *, base_price: float = 100.0) -> pd.DataFrame:
    return _rows([{} for _ in range(count)], base_price=base_price)


def _mirror_prices(candles: pd.DataFrame, *, anchor: float = 100.0) -> pd.DataFrame:
    mirrored = candles.copy(deep=True)
    old_high = candles["high"].copy()
    old_low = candles["low"].copy()
    mirrored["open"] = anchor - (candles["open"] - anchor)
    mirrored["close"] = anchor - (candles["close"] - anchor)
    mirrored["high"] = anchor - (old_low - anchor)
    mirrored["low"] = anchor - (old_high - anchor)
    return mirrored


def _volume_config(minimum: float = 1.3) -> VolumeRatioConfig:
    return VolumeRatioConfig(
        window=2,
        minimum_volume_ratio_for_confirmation=minimum,
        high_volume_ratio_threshold=2.0,
        require_full_window=False,
    )


def _pivot_config() -> PivotConfig:
    return PivotConfig(left_window=1, right_window=1, minimum_distance_between_pivots=1)


def _fvg_config() -> FairValueGapConfig:
    return FairValueGapConfig(
        atr_config=AtrConfig(period=1),
        volume_ratio_config=_volume_config(),
        displacement_config=DisplacementCandleConfig(
            minimum_range_atr_multiplier=1.0,
            minimum_volume_ratio=1.3,
        ),
    )


def _ob_config() -> OrderBlockConfig:
    return OrderBlockConfig(atr_config=AtrConfig(period=2), volume_ratio_config=_volume_config())


def _trendline_config() -> TrendlineBreakConfig:
    return TrendlineBreakConfig(
        minimum_trendline_length=1,
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=1),
        volume_ratio_config=_volume_config(),
        displacement_config=DisplacementCandleConfig(
            minimum_range_atr_multiplier=0.1,
            minimum_volume_ratio=1.3,
        ),
    )


def _cup_config() -> CupAndHandleConfig:
    return CupAndHandleConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_cup_duration=4,
        maximum_cup_duration=12,
        minimum_handle_duration=2,
        maximum_handle_duration=5,
        minimum_bottom_zone_duration=2,
        bottom_zone_atr_multiplier=1.0,
        require_prior_uptrend=False,
    )


def _diamond_config() -> DiamondConfig:
    return DiamondConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_pattern_duration=7,
        maximum_pattern_duration=20,
        minimum_expansion_range_change_atr=0.5,
        minimum_pattern_height_atr=1.0,
        maximum_pattern_height_atr=10.0,
    )


def _adam_config() -> AdamAndEveConfig:
    return AdamAndEveConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_pattern_duration=6,
        maximum_pattern_duration=20,
        adam_left_window=1,
        adam_right_window=1,
        maximum_adam_bottom_duration=3,
        minimum_eve_bottom_duration=5,
        minimum_eve_bottom_zone_duration=3,
        bottom_zone_atr_multiplier=1.0,
        minimum_adam_range_atr=0.5,
        minimum_eve_to_adam_duration_ratio=1.5,
        minimum_pattern_height_atr=1.0,
        maximum_pattern_height_atr=10.0,
        require_prior_downtrend=False,
    )


def _entry_cases() -> tuple[SyntheticEntryCase, ...]:
    return (
        SyntheticEntryCase("market_fill", PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, True),
        SyntheticEntryCase("limit_fill", PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE, True, max_wait_bars=1),
        SyntheticEntryCase("limit_no_fill", PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE, False, max_wait_bars=1),
    )


def _exit_cases() -> tuple[SyntheticExitCase, ...]:
    return (
        SyntheticExitCase("stop_first", "Future candle reaches stop before target."),
        SyntheticExitCase("target_first", "Future candle reaches target before stop."),
        SyntheticExitCase("ambiguous", "Future candle can reach stop and target in the same candle."),
        SyntheticExitCase("soft_invalidation", "Future close invalidates the pattern thesis before hard stop."),
        SyntheticExitCase("time_stop", "Future candles do not resolve before max holding bars."),
    )
