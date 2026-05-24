from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.indicators.volume_ratio import (
    VOLUME_RATIO_OUTPUT_COLUMNS,
    VolumeAverageMethod,
    VolumeInputMode,
    VolumeRatioBaselineMode,
    VolumeRatioConfig,
    VolumeStatus,
    calculate_volume_ratio,
    calculate_volume_ratio_snapshot,
    classify_volume_status,
    volume_ratio_timing_metadata,
)


def _candles(volumes: list[object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "BTCUSDT",
                "timestamp": f"2026-05-16T{index:02d}:00:00Z",
                "volume": volume,
            }
            for index, volume in enumerate(volumes)
        ]
    )


def test_calculates_volume_ratio_with_default_inclusive_mean_window() -> None:
    candles = _candles([100.0] * 19 + [300.0])

    volume_ratio = calculate_volume_ratio(candles)
    latest = volume_ratio.iloc[-1]

    assert list(volume_ratio.columns) == list(VOLUME_RATIO_OUTPUT_COLUMNS)
    assert latest["symbol"] == "BTCUSDT"
    assert latest["timestamp"] == "2026-05-16T19:00:00Z"
    assert latest["volume"] == pytest.approx(300.0)
    assert latest["average_volume"] == pytest.approx(110.0)
    assert latest["volume_ratio"] == pytest.approx(300.0 / 110.0)
    assert latest["minimum_volume_ratio_for_confirmation"] == pytest.approx(1.5)
    assert latest["volume_confirmation"] == True
    assert latest["volume_status"] == VolumeStatus.HIGH.value
    assert latest["is_valid"] == True


def test_prior_only_volume_ratio_excludes_spike_from_baseline() -> None:
    candles = _candles([100.0, 100.0, 100.0, 1000.0])
    inclusive = calculate_volume_ratio(candles, VolumeRatioConfig(window=3)).iloc[-1]
    prior_only = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(window=3, baseline_includes_current=False),
    ).iloc[-1]

    assert inclusive["average_volume"] == pytest.approx(400.0)
    assert inclusive["volume_ratio"] == pytest.approx(2.5)
    assert prior_only["average_volume"] == pytest.approx(100.0)
    assert prior_only["volume_ratio"] == pytest.approx(10.0)


def test_prior_only_baseline_mode_matches_compatibility_flag() -> None:
    candles = _candles([100.0, 100.0, 100.0, 1000.0])

    mode_rows = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(
            window=3,
            baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
        ),
    )
    flag_rows = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(window=3, baseline_includes_current=False),
    )

    assert mode_rows.iloc[-1]["volume_ratio"] == pytest.approx(10.0)
    assert flag_rows.iloc[-1]["volume_ratio"] == mode_rows.iloc[-1]["volume_ratio"]
    assert mode_rows.attrs["volume_ratio_metadata"]["baseline_mode"] == "PRIOR_ONLY"


def test_quote_volume_input_uses_quote_volume_when_available() -> None:
    candles = _candles([10.0, 20.0])
    candles["quote_volume"] = [1_000.0, 4_000.0]

    volume_ratio = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(
            window=2,
            volume_input_mode=VolumeInputMode.QUOTE_VOLUME_IF_AVAILABLE,
        ),
    )
    latest = volume_ratio.iloc[-1]

    assert latest["volume"] == pytest.approx(4_000.0)
    assert latest["average_volume"] == pytest.approx(2_500.0)
    assert latest["volume_ratio"] == pytest.approx(4_000.0 / 2_500.0)
    assert volume_ratio.attrs["volume_ratio_metadata"] == {
        "schema_version": "volume_ratio_config_metadata_v1",
        "baseline_mode": "CURRENT_INCLUSIVE",
        "volume_input_mode": "QUOTE_VOLUME_IF_AVAILABLE",
        "selected_volume_column": "quote_volume",
        "window": 2,
        "average_method": "MEAN",
        "minimum_volume_ratio_for_confirmation": 1.5,
    }


def test_quote_volume_input_falls_back_to_base_volume_when_quote_missing() -> None:
    candles = _candles([10.0, 20.0])

    volume_ratio = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(
            window=2,
            volume_input_mode=VolumeInputMode.QUOTE_VOLUME_IF_AVAILABLE,
        ),
    )

    assert volume_ratio.iloc[-1]["average_volume"] == pytest.approx(15.0)
    assert volume_ratio.iloc[-1]["volume_ratio"] == pytest.approx(20.0 / 15.0)
    assert (
        volume_ratio.attrs["volume_ratio_metadata"]["selected_volume_column"]
        == "volume"
    )


def test_trading_value_input_uses_close_times_base_volume() -> None:
    candles = _candles([10.0, 20.0])
    candles["close"] = [100.0, 200.0]

    volume_ratio = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(window=2, volume_input_mode=VolumeInputMode.TRADING_VALUE),
    )

    assert volume_ratio.iloc[-1]["volume"] == pytest.approx(4_000.0)
    assert volume_ratio.iloc[-1]["average_volume"] == pytest.approx(2_500.0)
    assert volume_ratio.iloc[-1]["volume_ratio"] == pytest.approx(4_000.0 / 2_500.0)
    assert (
        volume_ratio.attrs["volume_ratio_metadata"]["selected_volume_column"]
        == "trading_value"
    )


def test_volume_ratio_timing_metadata_tracks_baseline_mode() -> None:
    inclusive = volume_ratio_timing_metadata(VolumeRatioConfig(window=3))
    prior_only = volume_ratio_timing_metadata(
        VolumeRatioConfig(
            window=3,
            baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
            volume_input_mode=VolumeInputMode.TRADING_VALUE,
        )
    )

    assert inclusive["current_candle_included"] is True
    assert inclusive["warmup_period"] == 3
    assert inclusive["baseline_mode"] == "CURRENT_INCLUSIVE"
    assert prior_only["current_candle_included"] is False
    assert prior_only["requires_closed_candle"] is False
    assert prior_only["warmup_period"] == 4
    assert prior_only["baseline_mode"] == "PRIOR_ONLY"
    assert prior_only["volume_input_mode"] == "TRADING_VALUE"


def test_classifies_increased_normal_low_and_high_volume_statuses() -> None:
    config = VolumeRatioConfig(window=2)

    assert classify_volume_status(2.0, config) == VolumeStatus.HIGH.value
    assert classify_volume_status(1.5, config) == VolumeStatus.INCREASED.value
    assert classify_volume_status(1.0, config) == VolumeStatus.NORMAL.value
    assert classify_volume_status(0.5, config) == VolumeStatus.LOW.value
    assert classify_volume_status(None, config) == VolumeStatus.INVALID.value


def test_returns_increased_volume_confirmation_before_high_threshold() -> None:
    candles = _candles([100.0, 200.0])

    latest = calculate_volume_ratio(candles, VolumeRatioConfig(window=2)).iloc[-1]

    assert latest["average_volume"] == pytest.approx(150.0)
    assert latest["volume_ratio"] == pytest.approx(200.0 / 150.0)
    assert latest["volume_confirmation"] == False
    assert latest["volume_status"] == VolumeStatus.NORMAL.value

    increased = calculate_volume_ratio(
        _candles([100.0, 350.0]),
        VolumeRatioConfig(window=2),
    ).iloc[-1]
    assert increased["volume_ratio"] == pytest.approx(350.0 / 225.0)
    assert increased["volume_confirmation"] == True
    assert increased["volume_status"] == VolumeStatus.INCREASED.value


def test_zero_current_volume_is_low_when_average_volume_is_non_zero() -> None:
    candles = _candles([100.0, 0.0])

    latest = calculate_volume_ratio(candles, VolumeRatioConfig(window=2)).iloc[-1]

    assert latest["average_volume"] == pytest.approx(50.0)
    assert latest["volume_ratio"] == pytest.approx(0.0)
    assert latest["volume_confirmation"] == False
    assert latest["volume_status"] == VolumeStatus.LOW.value
    assert latest["is_valid"] == True


def test_marks_rows_invalid_until_full_window_is_available() -> None:
    candles = _candles([100.0, 150.0])

    volume_ratio = calculate_volume_ratio(candles, VolumeRatioConfig(window=3))

    assert volume_ratio.iloc[0]["is_valid"] == False
    assert volume_ratio.iloc[1]["is_valid"] == False
    assert volume_ratio.iloc[1]["average_volume"] is None
    assert volume_ratio.iloc[1]["volume_status"] == VolumeStatus.INVALID.value
    assert volume_ratio.iloc[1]["volume_confirmation"] == False


def test_can_calculate_partial_windows_when_full_window_is_not_required() -> None:
    candles = _candles([100.0, 200.0])

    volume_ratio = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(window=3, require_full_window=False),
    )

    assert volume_ratio.iloc[0]["average_volume"] == pytest.approx(100.0)
    assert volume_ratio.iloc[0]["volume_ratio"] == pytest.approx(1.0)
    assert volume_ratio.iloc[0]["is_valid"] == True
    assert volume_ratio.iloc[1]["average_volume"] == pytest.approx(150.0)
    assert volume_ratio.iloc[1]["is_valid"] == True


def test_missing_volume_in_active_window_marks_row_invalid() -> None:
    candles = _candles([100.0, None, 300.0])

    volume_ratio = calculate_volume_ratio(candles, VolumeRatioConfig(window=2))

    assert volume_ratio.iloc[1]["is_valid"] == False
    assert volume_ratio.iloc[2]["is_valid"] == False
    assert volume_ratio.iloc[2]["volume_status"] == VolumeStatus.INVALID.value
    assert volume_ratio.iloc[2]["volume_confirmation"] == False


def test_zero_average_volume_marks_row_invalid() -> None:
    candles = _candles([0.0, 0.0])

    latest = calculate_volume_ratio(candles, VolumeRatioConfig(window=2)).iloc[-1]

    assert latest["is_valid"] == False
    assert latest["average_volume"] is None
    assert latest["volume_ratio"] is None
    assert latest["volume_status"] == VolumeStatus.INVALID.value
    assert latest["volume_confirmation"] == False


def test_median_average_method_can_reduce_one_candle_spike_distortion() -> None:
    candles = _candles([100.0, 100.0, 1000.0, 100.0, 300.0])

    latest = calculate_volume_ratio(
        candles,
        VolumeRatioConfig(window=5, average_method=VolumeAverageMethod.MEDIAN),
    ).iloc[-1]

    assert latest["average_volume"] == pytest.approx(100.0)
    assert latest["volume_ratio"] == pytest.approx(3.0)
    assert latest["volume_status"] == VolumeStatus.HIGH.value


def test_rejects_missing_required_columns_and_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="missing required Volume Ratio columns: volume"):
        calculate_volume_ratio(_candles([100.0]).drop(columns=["volume"]))
    with pytest.raises(ValueError, match="window must be at least 1"):
        VolumeRatioConfig(window=0)
    with pytest.raises(ValueError, match="average_method must be one of"):
        VolumeRatioConfig(average_method="WILD")
    with pytest.raises(ValueError, match="baseline_mode must be one of"):
        VolumeRatioConfig(baseline_mode="FUTURE")
    with pytest.raises(ValueError, match="volume_input_mode must be one of"):
        VolumeRatioConfig(volume_input_mode="DOLLAR_VOLUME")
    with pytest.raises(ValueError, match="low_volume_ratio_threshold"):
        VolumeRatioConfig(low_volume_ratio_threshold=1.6)
    with pytest.raises(ValueError, match="minimum_volume_ratio_for_confirmation"):
        VolumeRatioConfig(minimum_volume_ratio_for_confirmation=2.1)
    with pytest.raises(ValueError, match="close column is required"):
        calculate_volume_ratio(
            _candles([100.0, 200.0]),
            VolumeRatioConfig(volume_input_mode=VolumeInputMode.TRADING_VALUE),
        )


def test_rejects_non_numeric_volume() -> None:
    with pytest.raises(ValueError):
        calculate_volume_ratio(_candles(["not-a-number"]))


def test_negative_volume_marks_row_invalid_without_fetching_external_data() -> None:
    candles = _candles([100.0, -1.0])

    latest = calculate_volume_ratio(candles, VolumeRatioConfig(window=2)).iloc[-1]

    assert latest["is_valid"] == False
    assert latest["volume_status"] == VolumeStatus.INVALID.value


def test_returns_latest_snapshot_for_output_schema_consumers() -> None:
    candles = _candles([100.0, 300.0])

    snapshot = calculate_volume_ratio_snapshot(candles, VolumeRatioConfig(window=2))

    assert snapshot["symbol"] == "BTCUSDT"
    assert snapshot["timestamp"] == "2026-05-16T01:00:00Z"
    assert snapshot["volume"] == pytest.approx(300.0)
    assert snapshot["average_volume"] == pytest.approx(200.0)
    assert snapshot["volume_ratio"] == pytest.approx(1.5)
    assert snapshot["volume_confirmation"] == True
    assert snapshot["volume_status"] == VolumeStatus.INCREASED.value
    assert snapshot["is_valid"] == True
    assert snapshot["metadata"]["baseline_mode"] == "CURRENT_INCLUSIVE"
    assert snapshot["metadata"]["volume_input_mode"] == "BASE_VOLUME"
