"""Binance historical candle downloader.

This module is intentionally limited to market-data responsibilities: requesting
public historical kline/candlestick data, normalizing the response to the
standard candle schema, and returning rows sorted by candle open timestamp. It
never sends signed requests, API keys, or order endpoint requests.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

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

SUPPORTED_KLINE_INTERVALS: tuple[str, ...] = (
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "1d",
)
MINUTE_INTERVALS: frozenset[str] = frozenset({"1m", "3m", "5m", "15m", "30m"})
BINANCE_KLINES_PATH = "/api/v3/klines"
DEFAULT_MARKET_DATA_BASE_URL = "https://data-api.binance.vision"

HttpGet = Callable[[str, float], object]


class BinanceCandleDownloader:
    """Fetch and normalize public Binance spot historical candles."""

    def __init__(
        self,
        base_url: str = DEFAULT_MARKET_DATA_BASE_URL,
        timeout: float = 10.0,
        http_get: HttpGet | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http_get = http_get or _get_json

    def fetch_historical_candles(
        self,
        symbol: str,
        interval: str = "1m",
        *,
        start_time: int | str | datetime | pd.Timestamp | None = None,
        end_time: int | str | datetime | pd.Timestamp | None = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch historical candles and return the standard candle schema.

        Args:
            symbol: Binance spot symbol, for example ``BTCUSDT``.
            interval: Supported Binance kline interval, such as ``1m``, ``1h``,
                or ``1d``.
            start_time: Optional candle open start time in milliseconds or a
                datetime-like value.
            end_time: Optional candle open end time in milliseconds or a
                datetime-like value.
            limit: Maximum candles to request. Binance spot klines support up to
                1000 rows per request.
        """

        params = _build_kline_params(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        url = f"{self.base_url}{BINANCE_KLINES_PATH}?{urlencode(params)}"
        _reject_order_endpoint(url)

        raw_klines = self._http_get(url, self.timeout)
        return normalize_binance_klines(raw_klines)


def normalize_binance_klines(raw_klines: object) -> pd.DataFrame:
    """Normalize raw Binance kline rows to the standard candle schema."""

    if not isinstance(raw_klines, Sequence) or isinstance(raw_klines, (str, bytes)):
        raise ValueError("Binance kline response must be a sequence of rows")

    rows: list[dict[str, object]] = []
    for index, raw_row in enumerate(raw_klines):
        if not isinstance(raw_row, Sequence) or isinstance(raw_row, (str, bytes)):
            raise ValueError(f"Binance kline row {index} must be a sequence")
        if len(raw_row) < 6:
            raise ValueError(f"Binance kline row {index} has fewer than 6 fields")

        rows.append(
            {
                "timestamp": raw_row[0],
                "open": raw_row[1],
                "high": raw_row[2],
                "low": raw_row[3],
                "close": raw_row[4],
                "volume": raw_row[5],
            }
        )

    normalized = pd.DataFrame(rows, columns=STANDARD_CANDLE_COLUMNS)
    if normalized.empty:
        return normalized

    normalized["timestamp"] = _parse_binance_open_times(normalized["timestamp"])
    for column in NUMERIC_CANDLE_COLUMNS:
        normalized[column] = _parse_numeric(normalized[column], column)

    return normalized.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _build_kline_params(
    *,
    symbol: str,
    interval: str,
    start_time: int | str | datetime | pd.Timestamp | None,
    end_time: int | str | datetime | pd.Timestamp | None,
    limit: int,
) -> dict[str, int | str]:
    normalized_symbol = _normalize_symbol(symbol)
    _validate_kline_interval(interval)
    _validate_limit(limit)

    params: dict[str, int | str] = {
        "symbol": normalized_symbol,
        "interval": interval,
        "limit": limit,
    }

    start_time_ms = _to_milliseconds(start_time, "start_time")
    end_time_ms = _to_milliseconds(end_time, "end_time")
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms
    if (
        start_time_ms is not None
        and end_time_ms is not None
        and start_time_ms > end_time_ms
    ):
        raise ValueError("start_time must be before or equal to end_time")

    return params


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError("symbol must not be blank")
    return normalized_symbol


def _validate_kline_interval(interval: str) -> None:
    if interval not in SUPPORTED_KLINE_INTERVALS:
        supported = ", ".join(SUPPORTED_KLINE_INTERVALS)
        raise ValueError(
            f"interval must be a supported Binance kline interval: {supported}"
        )


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")


def _to_milliseconds(
    value: int | str | datetime | pd.Timestamp | None, field_name: str
) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value

    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be a valid timestamp") from error
    if pd.isna(timestamp):
        raise ValueError(f"{field_name} must be a valid timestamp")
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)

    return int(timestamp.value // 1_000_000)


def _parse_binance_open_times(open_times: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(open_times, unit="ms", errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Binance kline response contains invalid open times") from error


def _parse_numeric(values: pd.Series, column: str) -> pd.Series:
    try:
        return pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Binance kline response contains non-numeric values in column: {column}"
        ) from error


def _reject_order_endpoint(url: str) -> None:
    normalized_url = url.lower()
    if "/order" in normalized_url or "order" in normalized_url.split("?", 1)[0]:
        raise ValueError("Binance candle downloader must not call order endpoints")


def _get_json(url: str, timeout: float) -> object:
    _reject_order_endpoint(url)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - public market data URL
        return json.loads(response.read().decode("utf-8"))
