from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    ATR_OUTPUT_COLUMNS,
    AtrConfig,
    AtrSmoothingMethod,
    VolatilityStatus,
    calculate_atr,
    calculate_atr_snapshot,
    calculate_true_range,
    atr_timing_metadata,
    classify_volatility,
)


def _candles(rows: list[dict[str, object]]) -> pd.DataFrame:
    base_rows = []
    for index, row in enumerate(rows):
        base = {
            "symbol": "BTCUSDT",
            "timestamp": f"2026-05-16T{index:02d}:00:00Z",
            "high": 10.0 + index,
            "low": 8.0 + index,
            "close": 9.0 + index,
        }
        base.update(row)
        base_rows.append(base)
    return pd.DataFrame(base_rows)


def test_calculates_true_range_with_first_candle_and_previous_close_gaps() -> None:
    assert calculate_true_range(10.0, 8.0, None) == pytest.approx(2.0)
    assert calculate_true_range(10.0, 8.0, 12.0) == pytest.approx(4.0)
    assert calculate_true_range(10.0, 8.0, 6.0) == pytest.approx(4.0)
    assert calculate_true_range(10.0, 8.0, 9.0) == pytest.approx(2.0)


def test_returns_rma_atr_with_default_config_and_warmup_rows() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": 12.0, "low": 9.0, "close": 11.0},
            {"high": 13.0, "low": 10.0, "close": 12.0},
            {"high": 16.0, "low": 11.0, "close": 15.0},
        ]
    )

    atr = calculate_atr(candles, AtrConfig(period=3))

    assert list(atr.columns) == list(ATR_OUTPUT_COLUMNS)
    assert list(atr["true_range"]) == pytest.approx([2.0, 3.0, 3.0, 5.0])
    assert atr.iloc[0]["is_valid"] == False
    assert atr.iloc[1]["is_valid"] == False
    assert atr.iloc[0]["volatility_status"] == VolatilityStatus.UNKNOWN.value
    assert atr.iloc[2]["atr"] == pytest.approx(8.0 / 3.0)
    assert atr.iloc[2]["is_valid"] == True
    assert atr.iloc[3]["atr"] == pytest.approx(((8.0 / 3.0) * 2 + 5.0) / 3.0)
    assert atr.iloc[3]["normalized_atr"] == pytest.approx(atr.iloc[3]["atr"] / 15.0)
    assert atr.iloc[3]["smoothing_method"] == AtrSmoothingMethod.RMA.value


def test_supports_sma_and_ema_smoothing_methods() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": 12.0, "low": 9.0, "close": 11.0},
            {"high": 13.0, "low": 10.0, "close": 12.0},
            {"high": 16.0, "low": 11.0, "close": 15.0},
        ]
    )

    sma = calculate_atr(candles, AtrConfig(period=3, smoothing_method="SMA"))
    ema = calculate_atr(
        candles,
        AtrConfig(period=3, smoothing_method=AtrSmoothingMethod.EMA),
    )

    assert sma.iloc[2]["atr"] == pytest.approx(8.0 / 3.0)
    assert sma.iloc[3]["atr"] == pytest.approx(11.0 / 3.0)
    assert ema.iloc[2]["atr"] == pytest.approx(8.0 / 3.0)
    assert ema.iloc[3]["atr"] == pytest.approx(5.0 * 0.5 + (8.0 / 3.0) * 0.5)
    assert sma.iloc[3]["smoothing_method"] == AtrSmoothingMethod.SMA.value
    assert ema.iloc[3]["smoothing_method"] == AtrSmoothingMethod.EMA.value


def test_classifies_volatility_from_normalized_atr_percent() -> None:
    config = AtrConfig(
        period=2,
        low_volatility_threshold_percent=1.0,
        high_volatility_threshold_percent=4.0,
    )

    assert classify_volatility(None, config) == VolatilityStatus.UNKNOWN.value
    assert classify_volatility(0.5, config) == VolatilityStatus.LOW.value
    assert classify_volatility(2.0, config) == VolatilityStatus.NORMAL.value
    assert classify_volatility(4.0, config) == VolatilityStatus.HIGH.value


def test_zero_or_negative_close_keeps_atr_but_omits_normalized_values() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": 12.0, "low": 9.0, "close": 0.0},
        ]
    )

    atr = calculate_atr(candles, AtrConfig(period=2))

    assert atr.iloc[-1]["is_valid"] == True
    assert atr.iloc[-1]["atr"] == pytest.approx(2.5)
    assert atr.iloc[-1]["normalized_atr"] is None
    assert atr.iloc[-1]["normalized_atr_percent"] is None
    assert atr.iloc[-1]["volatility_status"] == VolatilityStatus.UNKNOWN.value


def test_missing_price_marks_row_invalid_without_fetching_external_data() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": None, "low": 9.0, "close": 11.0},
        ]
    )

    atr = calculate_atr(candles, AtrConfig(period=2))

    assert atr.iloc[-1]["is_valid"] == False
    assert pd.isna(atr.iloc[-1]["true_range"])
    assert pd.isna(atr.iloc[-1]["atr"])
    assert atr.iloc[-1]["volatility_status"] == VolatilityStatus.UNKNOWN.value


def test_invalid_candle_marks_row_invalid() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": 7.0, "low": 9.0, "close": 8.0},
        ]
    )

    atr = calculate_atr(candles, AtrConfig(period=2))

    assert atr.iloc[-1]["is_valid"] == False
    assert pd.isna(atr.iloc[-1]["true_range"])
    assert pd.isna(atr.iloc[-1]["atr"])


def test_rejects_missing_required_columns_and_invalid_parameters() -> None:
    candles = _candles([{}]).drop(columns=["high"])

    with pytest.raises(ValueError, match="missing required ATR columns: high"):
        calculate_atr(candles)
    with pytest.raises(ValueError, match="period must be at least 1"):
        AtrConfig(period=0)
    with pytest.raises(ValueError, match="smoothing_method must be one of"):
        AtrConfig(smoothing_method="WILD")


def test_rejects_non_numeric_prices() -> None:
    candles = _candles([{"high": "not-a-number"}])

    with pytest.raises(ValueError):
        calculate_atr(candles)


def test_returns_latest_snapshot_for_output_schema_consumers() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0, "close": 9.0},
            {"high": 12.0, "low": 9.0, "close": 11.0},
        ]
    )

    snapshot = calculate_atr_snapshot(candles, AtrConfig(period=2))

    assert snapshot["symbol"] == "BTCUSDT"
    assert snapshot["timestamp"] == "2026-05-16T01:00:00Z"
    assert snapshot["period"] == 2
    assert snapshot["true_range"] == pytest.approx(3.0)
    assert snapshot["atr"] == pytest.approx(2.5)
    assert snapshot["is_valid"] == True


def test_atr_timing_metadata_reports_warmup_and_current_inclusion() -> None:
    metadata = atr_timing_metadata(AtrConfig(period=5))
    snapshot = calculate_atr_snapshot(
        _candles([{}, {}, {}, {}, {}]),
        AtrConfig(period=5),
        include_timing_metadata=True,
    )

    assert metadata["current_candle_included"] is True
    assert metadata["requires_closed_candle"] is True
    assert metadata["period"] == 5
    assert metadata["smoothing_method"] == AtrSmoothingMethod.RMA.value
    assert metadata["warmup_period"] == 5
    assert metadata["first_valid_index"] == 4
    assert metadata["confirmation_delay"] == 0
    assert snapshot["timing"] == metadata
