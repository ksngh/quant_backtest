"""PostgreSQL-backed standard candle data provider.

This module is intentionally limited to market-data responsibilities: reading
persisted candle rows through the PostgreSQL repository, normalizing them to the
standard candle schema, and returning rows sorted by candle open timestamp. It
does not fetch exchange data, place orders, or call exchange APIs.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from quant_bitcoin.market_data.candle_validation import (
    CandleValidationConfig,
    validate_standard_candles,
)
from quant_bitcoin.persistence import PostgresCandleRepository, SOURCE_BINANCE_SPOT

STANDARD_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

NUMERIC_CANDLE_COLUMNS: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class PostgresCandleDataProvider:
    """Load persisted PostgreSQL candles as standard backtest input data."""

    def __init__(
        self,
        repository: PostgresCandleRepository,
        *,
        source: str = SOURCE_BINANCE_SPOT,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        enforce_continuity: bool = False,
    ) -> None:
        self.repository = repository
        self.source = source
        self.symbol = symbol
        self.interval = interval
        self.start_time = start_time
        self.end_time = end_time
        self.enforce_continuity = enforce_continuity

    @classmethod
    def from_database_url(
        cls,
        database_url: str,
        *,
        source: str = SOURCE_BINANCE_SPOT,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        enforce_continuity: bool = False,
    ) -> "PostgresCandleDataProvider":
        """Build a provider from a PostgreSQL connection URL."""

        return cls(
            PostgresCandleRepository(database_url),
            source=source,
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            enforce_continuity=enforce_continuity,
        )

    def load(self) -> pd.DataFrame:
        """Return persisted candles using the standard candle data contract."""

        rows = self.repository.load_standard_candles(
            source=self.source,
            symbol=self.symbol,
            interval=self.interval,
            start_time=self.start_time,
            end_time=self.end_time,
        )
        candles = pd.DataFrame(rows, columns=STANDARD_CANDLE_COLUMNS)
        if candles.empty:
            return candles

        normalized = candles.loc[:, STANDARD_CANDLE_COLUMNS].copy()
        normalized["timestamp"] = self._parse_timestamps(normalized["timestamp"])
        for column in NUMERIC_CANDLE_COLUMNS:
            normalized[column] = self._parse_numeric(normalized[column], column)

        normalized = normalized.sort_values("timestamp", kind="mergesort").reset_index(
            drop=True
        )
        validate_standard_candles(
            normalized,
            CandleValidationConfig(
                interval=self.interval,
                enforce_continuity=self.enforce_continuity,
                allow_empty=True,
                context="PostgreSQL candle data",
            ),
        )
        return normalized

    @staticmethod
    def _parse_timestamps(timestamp: pd.Series) -> pd.Series:
        try:
            return pd.to_datetime(timestamp, errors="raise", utc=True)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "PostgreSQL candle data contains invalid timestamp values"
            ) from error

    @staticmethod
    def _parse_numeric(values: pd.Series, column: str) -> pd.Series:
        try:
            return pd.to_numeric(values, errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"PostgreSQL candle data contains non-numeric values in column: {column}"
            ) from error
