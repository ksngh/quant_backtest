from __future__ import annotations

import socket
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest

from quant_bitcoin.backtesting.basic import BasicBacktester
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.market_data.postgres_provider import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.strategies import Signal


class FakeRepository:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, Any]] = []

    def load_standard_candles(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        return self.rows


class SequenceStrategy:
    def __init__(self, signals: list[Signal]) -> None:
        self.signals = signals
        self.calls: list[pd.DataFrame] = []

    def generate_signal(self, candles: pd.DataFrame) -> Signal:
        self.calls.append(candles)
        return self.signals[len(self.calls) - 1]


def standard_row(timestamp: datetime, close: str) -> dict[str, Any]:
    close_decimal = Decimal(close)
    return {
        "timestamp": timestamp,
        "open": close_decimal - Decimal("1"),
        "high": close_decimal + Decimal("2"),
        "low": close_decimal - Decimal("2"),
        "close": close_decimal,
        "volume": Decimal("3.5"),
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "close_time": datetime(2024, 1, 1, 0, 0, 59, tzinfo=timezone.utc),
        "raw_payload": ["provider-specific"],
    }


def test_postgres_provider_returns_standard_candles_sorted_by_timestamp():
    repository = FakeRepository(
        [
            standard_row(datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc), "120"),
            standard_row(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), "100"),
            standard_row(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), "110"),
        ]
    )

    candles = PostgresCandleDataProvider(repository).load()

    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)
    assert candles["timestamp"].tolist() == [
        pd.Timestamp("2024-01-01 00:00:00+00:00"),
        pd.Timestamp("2024-01-01 00:01:00+00:00"),
        pd.Timestamp("2024-01-01 00:02:00+00:00"),
    ]
    assert candles["close"].tolist() == [100, 110, 120]
    assert "source" not in candles.columns
    assert "close_time" not in candles.columns
    assert "raw_payload" not in candles.columns


def test_postgres_provider_passes_stream_and_open_time_filters_to_repository():
    repository = FakeRepository([])
    start_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc)

    candles = PostgresCandleDataProvider(
        repository,
        source="binance_spot",
        symbol="ETHUSDT",
        interval="5m",
        start_time=start_time,
        end_time=end_time,
    ).load()

    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)
    assert candles.empty
    assert repository.calls == [
        {
            "source": "binance_spot",
            "symbol": "ETHUSDT",
            "interval": "5m",
            "start_time": start_time,
            "end_time": end_time,
        }
    ]


def test_postgres_provider_loaded_candles_can_run_basic_backtest_without_csv():
    repository = FakeRepository(
        [
            standard_row(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), "100"),
            standard_row(datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), "110"),
            standard_row(datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc), "120"),
        ]
    )
    candles = PostgresCandleDataProvider(repository).load()
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.SELL])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert result.final_equity == 1_020
    assert len(result.trades) == 2
    assert all(
        list(call.columns) == list(STANDARD_CANDLE_COLUMNS) for call in strategy.calls
    )


def test_postgres_provider_rejects_invalid_numeric_values():
    repository = FakeRepository(
        [
            {
                "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "open": Decimal("100"),
                "high": Decimal("101"),
                "low": Decimal("99"),
                "close": "not-a-number",
                "volume": Decimal("1"),
            }
        ]
    )

    with pytest.raises(ValueError, match="non-numeric values in column: close"):
        PostgresCandleDataProvider(repository).load()


def test_postgres_provider_does_not_open_network_connections(monkeypatch):
    repository = FakeRepository(
        [standard_row(datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), "100")]
    )

    def fail_socket_creation(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("PostgreSQL provider must not create network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket_creation)

    candles = PostgresCandleDataProvider(repository).load()

    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)
