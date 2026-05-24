from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    PivotConfig,
    PivotType,
    detect_pivots,
    pivot_strength_diagnostics,
    pivot_timing_metadata,
    remove_close_duplicate_pivots,
)


def _candles(highs: list[float], lows: list[float], **extra_columns: list[float]) -> pd.DataFrame:
    rows = len(highs)
    data = {
        "symbol": ["BTCUSDT"] * rows,
        "timestamp": pd.date_range("2026-05-16", periods=rows, freq="5min"),
        "open": [(high + low) / 2 for high, low in zip(highs, lows)],
        "high": highs,
        "low": lows,
        "close": [(high + low) / 2 for high, low in zip(highs, lows)],
        "volume": [1.0] * rows,
    }
    data.update(extra_columns)
    return pd.DataFrame(data)


def test_detects_pivot_high_in_simple_five_candle_sequence() -> None:
    candles = _candles([10, 11, 15, 12, 11], [7, 8, 9, 8, 7])

    pivots = detect_pivots(candles, PivotConfig(left_window=2, right_window=2))

    assert len(pivots) == 1
    pivot = pivots.iloc[0]
    assert pivot["pivot_type"] == PivotType.PIVOT_HIGH.value
    assert pivot["pivot_index"] == 2
    assert pivot["confirmed_index"] == 4
    assert pivot["price"] == 15.0
    assert pivot["strength"] == 3.0
    assert pivot["pivot_timestamp"] == candles.loc[2, "timestamp"]
    assert pivot["confirmed_timestamp"] == candles.loc[4, "timestamp"]
    assert pivot["is_confirmed"] == True


def test_pivot_timing_metadata_confirmation_delay_matches_right_window() -> None:
    metadata = pivot_timing_metadata(PivotConfig(left_window=2, right_window=3))

    assert metadata["current_candle_included"] is False
    assert metadata["requires_closed_candle"] is True
    assert metadata["warmup_period"] == 6
    assert metadata["confirmation_delay"] == 3
    assert metadata["baseline_mode"] == "CONFIRMED_AFTER_RIGHT_WINDOW"
    assert metadata["use_atr_filter"] is False
    assert metadata["minimum_pivot_strength_atr"] == pytest.approx(0.5)


def test_detects_pivot_low_in_simple_five_candle_sequence() -> None:
    candles = _candles([15, 14, 13, 14, 15], [10, 9, 5, 8, 9])

    pivots = detect_pivots(candles, PivotConfig(left_window=2, right_window=2))

    assert len(pivots) == 1
    pivot = pivots.iloc[0]
    assert pivot["pivot_type"] == PivotType.PIVOT_LOW.value
    assert pivot["pivot_index"] == 2
    assert pivot["confirmed_index"] == 4
    assert pivot["price"] == 5.0
    assert pivot["strength"] == 3.0


def test_does_not_mark_non_pivot_middle_candles() -> None:
    candles = _candles([10, 11, 12, 13, 14], [5, 6, 7, 8, 9])

    pivots = detect_pivots(candles, PivotConfig(left_window=2, right_window=2))

    assert pivots.empty
    assert list(pivots.columns) == [
        "symbol",
        "pivot_timestamp",
        "confirmed_timestamp",
        "pivot_index",
        "confirmed_index",
        "pivot_type",
        "price",
        "high_price",
        "low_price",
        "strength",
        "high_strength",
        "low_strength",
        "left_window",
        "right_window",
        "is_confirmed",
    ]


def test_requires_full_left_and_right_window_by_default() -> None:
    candles = _candles([15, 10, 9, 8], [5, 4, 3, 2])

    pivots = detect_pivots(candles, PivotConfig(left_window=2, right_window=2))

    assert pivots.empty


def test_can_emit_unconfirmed_rows_when_full_window_is_not_required() -> None:
    candles = _candles([10, 11, 12, 13], [9, 8, 7, 6])

    pivots = detect_pivots(
        candles,
        PivotConfig(left_window=2, right_window=2, require_full_window=False),
    )

    assert list(pivots["pivot_type"]) == [
        PivotType.UNCONFIRMED.value,
        PivotType.UNCONFIRMED.value,
    ]
    assert list(pivots["is_confirmed"]) == [False, False]


def test_strict_mode_rejects_equal_high_and_equal_low_ties() -> None:
    candles = _candles([10, 15, 15, 12, 11], [8, 5, 5, 7, 8])

    pivots = detect_pivots(candles, PivotConfig(left_window=2, right_window=2))

    assert pivots.empty


def test_equal_mode_allows_tied_high_and_low_as_both_pivot() -> None:
    candles = _candles([10, 15, 15, 12, 11], [8, 5, 5, 7, 8])

    pivots = detect_pivots(
        candles,
        PivotConfig(left_window=2, right_window=2, allow_equal_high_low=True),
    )

    assert len(pivots) == 1
    pivot = pivots.iloc[0]
    assert pivot["pivot_type"] == PivotType.BOTH.value
    assert pivot["high_price"] == 15.0
    assert pivot["low_price"] == 5.0
    assert pivot["high_strength"] == 0.0
    assert pivot["low_strength"] == 0.0


def test_atr_filter_rejects_weak_pivots() -> None:
    candles = _candles([10, 11, 15, 12, 11], [7, 8, 9, 8, 7], atr=[1, 1, 10, 1, 1])

    pivots = detect_pivots(
        candles,
        PivotConfig(
            left_window=2,
            right_window=2,
            use_atr_filter=True,
            minimum_pivot_strength_atr=0.5,
        ),
    )

    assert pivots.empty


def test_atr_filter_accepts_strong_pivot_and_reports_density() -> None:
    candles = _candles([10, 11, 15, 12, 11], [7, 8, 9, 8, 7], atr=[1, 1, 1, 1, 1])
    config = PivotConfig(
        left_window=2,
        right_window=2,
        use_atr_filter=True,
        minimum_pivot_strength_atr=0.5,
    )

    pivots = detect_pivots(candles, config)
    diagnostics = pivot_strength_diagnostics(
        pivots,
        config,
        current_index=4,
        candle_count=len(candles),
    )

    assert len(pivots) == 1
    assert pivots.iloc[0]["strength"] == pytest.approx(3.0)
    assert diagnostics["schema_version"] == "pivot_strength_diagnostics_v1"
    assert diagnostics["use_atr_filter"] is True
    assert diagnostics["pivot_count"] == 1
    assert diagnostics["confirmed_pivot_count"] == 1
    assert diagnostics["pivot_density_per_100_candles"] == pytest.approx(20.0)
    assert diagnostics["no_lookahead_confirmed"] is True


def test_filters_same_type_close_duplicate_pivots_by_stronger_price() -> None:
    pivots = [
        {"pivot_type": PivotType.PIVOT_HIGH.value, "pivot_index": 10, "price": 20.0},
        {"pivot_type": PivotType.PIVOT_HIGH.value, "pivot_index": 12, "price": 22.0},
    ]

    filtered = remove_close_duplicate_pivots(
        pivots,
        PivotConfig(
            left_window=1,
            right_window=1,
            minimum_distance_between_pivots=3,
        ),
    )

    assert filtered == [pivots[1]]


def test_rejects_missing_required_candle_columns() -> None:
    candles = _candles([10, 11, 12], [7, 8, 9]).drop(columns=["symbol"])

    with pytest.raises(ValueError, match="missing required columns: symbol"):
        detect_pivots(candles, PivotConfig(left_window=1, right_window=1))


def test_rejects_missing_high_or_low_values() -> None:
    candles = _candles([10, 11, 12], [7, 8, 9])
    candles.loc[1, "high"] = None

    with pytest.raises(ValueError, match="missing high or low"):
        detect_pivots(candles, PivotConfig(left_window=1, right_window=1))


@pytest.mark.parametrize(
    "config_kwargs, error",
    [
        ({"left_window": 0}, "left_window must be at least 1"),
        ({"right_window": 0}, "right_window must be at least 1"),
        (
            {"minimum_distance_between_pivots": 0},
            "minimum_distance_between_pivots must be at least 1",
        ),
        ({"minimum_pivot_strength_atr": -0.1}, "must be non-negative"),
    ],
)
def test_rejects_invalid_config_parameters(
    config_kwargs: dict[str, float], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        PivotConfig(**config_kwargs)


def test_rejects_missing_atr_when_atr_filter_is_enabled() -> None:
    candles = _candles([10, 11, 15, 12, 11], [7, 8, 9, 8, 7])

    with pytest.raises(ValueError, match="missing required ATR column"):
        detect_pivots(candles, PivotConfig(use_atr_filter=True))
