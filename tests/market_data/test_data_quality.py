from __future__ import annotations

import pandas as pd

from quant_bitcoin.market_data.data_quality import (
    CandleDataQualityConfig,
    CandleDataQualitySeverity,
    audit_standard_candles,
)


def _valid_candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:01:00Z",
                "2024-01-01T00:02:00Z",
            ],
            "open": [100.0, 101.0, 102.0],
            "high": [101.0, 102.0, 103.0],
            "low": [99.0, 100.0, 101.0],
            "close": [100.5, 101.5, 102.5],
            "volume": [1.0, 2.0, 3.0],
        }
    )


def test_audit_valid_data_returns_clean_report() -> None:
    candles = _valid_candles()

    report = audit_standard_candles(candles)

    assert report.candle_count == 3
    assert report.issue_count == 0
    assert report.has_errors is False
    assert report.has_warnings is False
    assert report.duplicate_timestamp_count == 0
    assert report.missing_interval_count == 0
    assert report.zero_volume_count == 0


def test_audit_missing_required_columns_is_error() -> None:
    candles = _valid_candles().drop(columns=["volume"])

    report = audit_standard_candles(candles)

    assert report.has_errors is True
    assert any(issue.code == "MISSING_REQUIRED_COLUMNS" for issue in report.issues)


def test_audit_unsorted_timestamps_is_error() -> None:
    candles = _valid_candles().iloc[[1, 0, 2]]

    report = audit_standard_candles(candles)

    assert any(issue.code == "NON_ASCENDING_TIMESTAMPS" for issue in report.issues)


def test_audit_duplicate_timestamps_detected() -> None:
    candles = _valid_candles()
    candles.loc[1, "timestamp"] = candles.loc[0, "timestamp"]

    report = audit_standard_candles(candles)

    assert report.duplicate_timestamp_count == 2
    assert any(issue.code == "DUPLICATE_TIMESTAMPS" for issue in report.issues)


def test_audit_missing_interval_gap_detected() -> None:
    candles = _valid_candles().iloc[[0, 2]].reset_index(drop=True)

    report = audit_standard_candles(candles)

    assert report.missing_interval_count == 1
    assert any(issue.code == "MISSING_INTERVAL_GAPS" for issue in report.issues)


def test_audit_invalid_ohlc_relationships_detected() -> None:
    candles = _valid_candles()
    candles.loc[0, "high"] = 98.0
    candles.loc[1, "open"] = 500.0

    report = audit_standard_candles(candles)

    assert any(issue.code == "HIGH_BELOW_LOW" for issue in report.issues)
    assert any(issue.code == "OPEN_CLOSE_OUTSIDE_RANGE" for issue in report.issues)


def test_audit_negative_and_zero_volume_detected() -> None:
    candles = _valid_candles()
    candles.loc[0, "volume"] = -1.0
    candles.loc[1, "volume"] = 0.0

    report = audit_standard_candles(candles)

    assert any(issue.code == "NEGATIVE_VOLUME" for issue in report.issues)
    assert report.zero_volume_count == 1
    assert report.zero_volume_ratio == 1 / 3
    assert any(issue.code == "ZERO_VOLUME" for issue in report.issues)


def test_audit_zero_volume_can_be_error() -> None:
    candles = _valid_candles()
    candles.loc[0, "volume"] = 0.0

    report = audit_standard_candles(
        candles,
        CandleDataQualityConfig(treat_zero_volume_as_error=True),
    )

    zero_issue = next(issue for issue in report.issues if issue.code == "ZERO_VOLUME")
    assert zero_issue.severity == CandleDataQualitySeverity.ERROR


def test_audit_empty_input_handling() -> None:
    report_error = audit_standard_candles([])
    assert report_error.has_errors is True

    report_info = audit_standard_candles([], CandleDataQualityConfig(allow_empty=True))
    assert any(issue.code == "EMPTY_INPUT" for issue in report_info.issues)
    assert any(issue.severity == CandleDataQualitySeverity.INFO for issue in report_info.issues)


def test_audit_does_not_mutate_input() -> None:
    candles = _valid_candles()
    original = candles.copy(deep=True)

    _ = audit_standard_candles(candles)

    pd.testing.assert_frame_equal(candles, original)
