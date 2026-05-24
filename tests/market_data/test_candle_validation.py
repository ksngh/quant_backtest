from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.market_data.candle_validation import (
    CandleValidationConfig,
    validate_standard_candles,
)


def _valid_candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1},
            {"timestamp": "2024-01-01T00:01:00Z", "open": 101, "high": 102, "low": 100, "close": 101.5, "volume": 2},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 102, "high": 103, "low": 101, "close": 102.5, "volume": 3},
        ]
    )


def test_validate_standard_candles_accepts_valid_schema() -> None:
    validate_standard_candles(_valid_candles())


def test_validate_standard_candles_rejects_duplicate_timestamps() -> None:
    candles = _valid_candles()
    candles.loc[1, "timestamp"] = candles.loc[0, "timestamp"]

    with pytest.raises(ValueError, match="duplicate timestamp.*2024-01-01 00:00:00\\+00:00"):
        validate_standard_candles(candles)


def test_validate_standard_candles_rejects_missing_interval_gap_when_enforced() -> None:
    candles = _valid_candles()
    candles.loc[2, "timestamp"] = "2024-01-01T00:03:00Z"

    with pytest.raises(ValueError, match="interval gap for 1m"):
        validate_standard_candles(
            candles,
            CandleValidationConfig(interval="1m", enforce_continuity=True),
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("open", 0, "non-positive price in column: open"),
        ("high", 100, "high below open/close"),
        ("low", 102, "high < low"),
        ("close", 500, "high below open/close"),
        ("volume", -1, "negative volume"),
    ],
)
def test_validate_standard_candles_rejects_invalid_ohlcv(column: str, value: float, message: str) -> None:
    candles = _valid_candles()
    candles.loc[0, column] = value

    with pytest.raises(ValueError, match=message):
        validate_standard_candles(candles)


def test_validate_standard_candles_rejects_non_numeric_and_non_finite_values() -> None:
    non_numeric = _valid_candles().astype({"close": "object"})
    non_numeric.loc[0, "close"] = "bad"
    with pytest.raises(ValueError, match="non-numeric values in column: close"):
        validate_standard_candles(non_numeric)

    non_finite = _valid_candles()
    non_finite.loc[0, "close"] = float("inf")
    with pytest.raises(ValueError, match="non-finite values in column: close"):
        validate_standard_candles(non_finite)


def test_validate_standard_candles_normalizes_timezone_for_checks() -> None:
    candles = _valid_candles()
    candles.loc[0, "timestamp"] = "2024-01-01 00:00:00"
    candles.loc[1, "timestamp"] = "2024-01-01 00:01:00+00:00"
    candles.loc[2, "timestamp"] = "2024-01-01 00:02:00Z"

    validate_standard_candles(
        candles,
        CandleValidationConfig(interval="1m", enforce_continuity=True),
    )


def test_validate_standard_candles_does_not_mutate_input() -> None:
    candles = _valid_candles()
    original = candles.copy(deep=True)

    validate_standard_candles(candles)

    pd.testing.assert_frame_equal(candles, original)
