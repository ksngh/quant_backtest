from __future__ import annotations

import inspect

import pandas as pd
import pytest

from quant_bitcoin.backtesting import multitimeframe_candles
from quant_bitcoin.backtesting.multitimeframe_candles import (
    ALIGNMENT_CONTRACT_VERSION,
    align_completed_higher_timeframe_candles,
)


def _minute_candles(rows: int = 20) -> pd.DataFrame:
    timestamps = pd.date_range("2026-05-27T00:00:00Z", periods=rows, freq="min")
    data = []
    for index, timestamp in enumerate(timestamps):
        open_price = 100 + index
        data.append(
            {
                "timestamp": timestamp,
                "open": open_price,
                "high": open_price + 2,
                "low": open_price - 1,
                "close": open_price + 1,
                "volume": 10 + index,
            }
        )
    return pd.DataFrame(data)


def test_aligns_completed_1m_to_5m_candles_without_lookahead() -> None:
    result = align_completed_higher_timeframe_candles(
        _minute_candles(7),
        source_interval="1m",
        target_intervals=("5m",),
    )

    aligned = result.candles
    before_close = aligned.loc[4]
    first_visible = aligned.loc[5]

    assert before_close["timestamp"] == pd.Timestamp("2026-05-27T00:04:00Z")
    assert not bool(before_close["mtf_5m_available"])
    assert pd.isna(before_close["mtf_5m_open_time"])

    assert first_visible["timestamp"] == pd.Timestamp("2026-05-27T00:05:00Z")
    assert bool(first_visible["mtf_5m_available"])
    assert first_visible["mtf_5m_open_time"] == pd.Timestamp("2026-05-27T00:00:00Z")
    assert first_visible["mtf_5m_close_time"] == pd.Timestamp("2026-05-27T00:05:00Z")
    assert first_visible["mtf_5m_open"] == 100
    assert first_visible["mtf_5m_high"] == 106
    assert first_visible["mtf_5m_low"] == 99
    assert first_visible["mtf_5m_close"] == 105
    assert first_visible["mtf_5m_volume"] == sum(range(10, 15))


def test_aligns_1m_to_15m_and_preserves_base_row_count() -> None:
    result = align_completed_higher_timeframe_candles(
        _minute_candles(17),
        source_interval="1m",
        target_intervals=("15m",),
    )

    aligned = result.candles

    assert len(aligned) == 17
    assert not bool(aligned.loc[14, "mtf_15m_available"])
    assert bool(aligned.loc[15, "mtf_15m_available"])
    assert aligned.loc[15, "mtf_15m_open_time"] == pd.Timestamp("2026-05-27T00:00:00Z")
    assert aligned.loc[15, "mtf_15m_close_time"] == pd.Timestamp("2026-05-27T00:15:00Z")


def test_partial_final_higher_timeframe_window_is_not_exposed() -> None:
    result = align_completed_higher_timeframe_candles(
        _minute_candles(9),
        source_interval="1m",
        target_intervals=("5m",),
    )

    aligned = result.candles

    assert len(result.higher_timeframe_candles["5m"]) == 1
    assert aligned.loc[8, "mtf_5m_open_time"] == pd.Timestamp("2026-05-27T00:00:00Z")
    assert aligned.loc[8, "mtf_5m_close_time"] == pd.Timestamp("2026-05-27T00:05:00Z")
    assert pd.Timestamp("2026-05-27T00:05:00Z") not in set(
        result.higher_timeframe_candles["5m"]["open_time"]
    )


def test_missing_source_rows_leave_higher_timeframe_unavailable() -> None:
    candles = _minute_candles(10).drop(index=2).reset_index(drop=True)

    result = align_completed_higher_timeframe_candles(
        candles,
        source_interval="1m",
        target_intervals=("5m",),
    )

    aligned = result.candles

    assert aligned.loc[5, "timestamp"] == pd.Timestamp("2026-05-27T00:06:00Z")
    assert not bool(aligned.loc[5, "mtf_5m_available"])
    assert len(result.higher_timeframe_candles["5m"]) == 1
    assert result.higher_timeframe_candles["5m"].loc[0, "open_time"] == pd.Timestamp("2026-05-27T00:05:00Z")


def test_alignment_metadata_documents_contract_and_availability() -> None:
    result = align_completed_higher_timeframe_candles(
        _minute_candles(16),
        source_interval="1m",
        target_intervals=("5m", "15m"),
    )

    assert result.metadata["contract_version"] == ALIGNMENT_CONTRACT_VERSION
    assert result.metadata["source_interval"] == "1m"
    assert result.metadata["target_intervals"] == ["5m", "15m"]
    assert result.metadata["no_lookahead_guarantee"] is True
    assert result.metadata["targets"]["5m"]["availability_column"] == "mtf_5m_available"
    assert result.metadata["targets"]["15m"]["close_availability_semantics"] == (
        "visible when close_time <= base timestamp"
    )


def test_validation_rejects_unsorted_missing_columns_and_bad_intervals() -> None:
    unsorted = _minute_candles(3).iloc[[0, 2, 1]].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted ascending by timestamp"):
        align_completed_higher_timeframe_candles(unsorted, source_interval="1m", target_intervals=("5m",))

    missing = _minute_candles(3).drop(columns=["volume"])
    with pytest.raises(ValueError, match="missing required columns: volume"):
        align_completed_higher_timeframe_candles(missing, source_interval="1m", target_intervals=("5m",))

    with pytest.raises(ValueError, match="unsupported target_interval"):
        align_completed_higher_timeframe_candles(_minute_candles(3), source_interval="1m", target_intervals=("2m",))

    with pytest.raises(ValueError, match="must be divisible"):
        align_completed_higher_timeframe_candles(_minute_candles(20), source_interval="3m", target_intervals=("5m",))


def test_aligned_rows_can_be_joined_to_synthetic_fvg_like_data_without_raw_count_change() -> None:
    candles = _minute_candles(8)
    candles.loc[0, "high"] = 101
    candles.loc[2, "open"] = 106
    candles.loc[2, "low"] = 105
    candles.loc[2, "high"] = 108
    candles.loc[2, "close"] = 107

    result = align_completed_higher_timeframe_candles(candles, target_intervals=("5m",))

    assert len(result.candles) == len(candles)
    assert list(result.candles["timestamp"]) == list(pd.to_datetime(candles["timestamp"], utc=True))
    assert "mtf_5m_close" in result.candles.columns


def test_multitimeframe_helper_has_no_exchange_or_network_coupling() -> None:
    source = inspect.getsource(multitimeframe_candles)

    assert "binance" not in source.lower()
    assert "requests" not in source
    assert "urllib" not in source
    assert "exchange" not in source.lower()
    assert "signed" not in source.lower()
