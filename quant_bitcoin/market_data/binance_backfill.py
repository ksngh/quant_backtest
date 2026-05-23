"""Restartable Binance public candle backfill into persistence.

This module stays inside the market-data boundary. It requests public Binance spot
klines, maps them to the accepted persistence schema, and writes finalized
candles through a repository. It never signs requests, accepts API keys, or calls
exchange order endpoints.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from quant_bitcoin.market_data.binance_downloader import (
    BINANCE_KLINES_PATH,
    DEFAULT_MARKET_DATA_BASE_URL,
    MINUTE_INTERVALS,
)
from quant_bitcoin.persistence import (
    HISTORICAL_BACKFILL_MODE,
    SOURCE_BINANCE_SPOT,
    IngestionCheckpoint,
    PersistedCandle,
)

BINANCE_MAX_KLINE_LIMIT = 1000
ONE_MINUTE_MS = 60_000
RETRYABLE_HTTP_STATUS_CODES = frozenset({408, 418, 425, 429, 500, 502, 503, 504})

HttpGet = Callable[[str, float], object]
Sleep = Callable[[float], None]
TimeProvider = Callable[[], datetime]


class CandleRepository(Protocol):
    """Persistence behavior needed by the historical backfill."""

    def latest_open_time(
        self, source: str, symbol: str, interval: str
    ) -> datetime | None: ...

    def upsert_candles(self, candles: Sequence[PersistedCandle]) -> int: ...

    def save_checkpoint(self, checkpoint: IngestionCheckpoint) -> None: ...


@dataclass(frozen=True)
class BackfillResult:
    """Summary of one historical backfill run."""

    symbol: str
    interval: str
    requested_start_time: datetime | None
    requested_end_time: datetime
    stored_candles: int
    pages_fetched: int


@dataclass(frozen=True)
class MultiIntervalBackfillResult:
    """Summary of a multi-interval historical backfill run."""

    symbol: str
    intervals: tuple[str, ...]
    results: tuple[BackfillResult, ...]


class BinanceBackfillError(RuntimeError):
    """Base error for Binance historical backfill failures."""


class RetryableBinanceError(BinanceBackfillError):
    """A public market-data request failed in a retryable way."""


class MultiIntervalBackfillError(BinanceBackfillError):
    """A specific interval failed during multi-interval backfill."""

    def __init__(self, interval: str, error: Exception) -> None:
        super().__init__(f"backfill failed for interval {interval}: {error}")
        self.interval = interval
        self.error = error


def parse_interval_list(value: str) -> tuple[str, ...]:
    """Parse a comma-separated interval list, preserving order and de-duplicating."""

    if not isinstance(value, str):
        raise ValueError("intervals must be a string")
    intervals: list[str] = []
    seen: set[str] = set()
    for raw_interval in value.split(","):
        interval = raw_interval.strip()
        if not interval:
            continue
        _validate_interval(interval)
        if interval not in seen:
            intervals.append(interval)
            seen.add(interval)
    if not intervals:
        raise ValueError("intervals must include at least one supported interval")
    return tuple(intervals)


class MultiIntervalBinanceBackfillRunner:
    """Run the existing single-interval backfiller once per requested interval."""

    def __init__(self, backfiller: BinanceHistoricalBackfiller) -> None:
        self.backfiller = backfiller

    def run(
        self,
        *,
        symbol: str = "BTCUSDT",
        intervals: Sequence[str],
        start_time: datetime | int | None = None,
        end_time: datetime | int | None = None,
        limit: int = BINANCE_MAX_KLINE_LIMIT,
    ) -> MultiIntervalBackfillResult:
        normalized_symbol = _normalize_symbol(symbol)
        parsed_intervals = parse_interval_list(",".join(intervals))
        results: list[BackfillResult] = []
        for interval in parsed_intervals:
            try:
                results.append(
                    self.backfiller.run(
                        symbol=normalized_symbol,
                        interval=interval,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )
                )
            except Exception as error:
                raise MultiIntervalBackfillError(interval, error) from error
        return MultiIntervalBackfillResult(
            symbol=normalized_symbol,
            intervals=parsed_intervals,
            results=tuple(results),
        )


class BinanceHistoricalBackfiller:
    """Fetch public Binance spot klines and persist closed candles."""

    def __init__(
        self,
        repository: CandleRepository,
        *,
        base_url: str = DEFAULT_MARKET_DATA_BASE_URL,
        timeout: float = 10.0,
        http_get: HttpGet | None = None,
        sleep: Sleep = time.sleep,
        now: TimeProvider | None = None,
        max_retries: int = 3,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.repository = repository
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http_get = http_get or _get_json
        self._sleep = sleep
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.max_retries = max_retries

    def run(
        self,
        *,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_time: datetime | int | None = None,
        end_time: datetime | int | None = None,
        limit: int = BINANCE_MAX_KLINE_LIMIT,
    ) -> BackfillResult:
        """Backfill finalized candles from Binance into the repository."""

        normalized_symbol = _normalize_symbol(symbol)
        _validate_interval(interval)
        _validate_limit(limit)

        latest_closed_open_ms = _latest_closed_open_time_ms(self._now(), interval)
        requested_end_ms = (
            _to_milliseconds(end_time, "end_time")
            if end_time is not None
            else latest_closed_open_ms
        )
        requested_end_ms = min(requested_end_ms, latest_closed_open_ms)
        requested_start_ms = self._determine_start_ms(
            normalized_symbol, interval, start_time
        )
        if requested_start_ms is not None and requested_start_ms > requested_end_ms:
            self._save_checkpoint(
                symbol=normalized_symbol,
                interval=interval,
                status="completed",
                last_open_time=self.repository.latest_open_time(
                    SOURCE_BINANCE_SPOT, normalized_symbol, interval
                ),
                last_close_time=None,
                metadata={"stored_candles": 0, "pages_fetched": 0},
            )
            return BackfillResult(
                symbol=normalized_symbol,
                interval=interval,
                requested_start_time=_from_milliseconds(requested_start_ms),
                requested_end_time=_from_milliseconds(requested_end_ms),
                stored_candles=0,
                pages_fetched=0,
            )

        current_start_ms = requested_start_ms
        stored_candles = 0
        pages_fetched = 0
        last_open_time: datetime | None = None
        last_close_time: datetime | None = None

        self._save_checkpoint(
            symbol=normalized_symbol,
            interval=interval,
            status="running",
            last_open_time=None,
            last_close_time=None,
            metadata={"requested_end_time_ms": requested_end_ms},
        )

        while True:
            raw_klines = self._fetch_klines(
                symbol=normalized_symbol,
                interval=interval,
                start_time_ms=current_start_ms,
                end_time_ms=requested_end_ms,
                limit=limit,
            )
            pages_fetched += 1
            if not raw_klines:
                break

            page_candles = [
                map_binance_kline_to_persisted_candle(
                    raw_kline,
                    symbol=normalized_symbol,
                    interval=interval,
                    now=self._now(),
                )
                for raw_kline in raw_klines
            ]
            closed_candles = [candle for candle in page_candles if candle.is_closed]
            if closed_candles:
                stored_candles += self.repository.upsert_candles(closed_candles)
                last_open_time = closed_candles[-1].open_time
                last_close_time = closed_candles[-1].close_time
                self._save_checkpoint(
                    symbol=normalized_symbol,
                    interval=interval,
                    status="running",
                    last_open_time=last_open_time,
                    last_close_time=last_close_time,
                    metadata={
                        "stored_candles": stored_candles,
                        "pages_fetched": pages_fetched,
                    },
                )

            last_raw_open_ms = _extract_open_time_ms(raw_klines[-1], len(raw_klines) - 1)
            next_start_ms = last_raw_open_ms + _interval_milliseconds(interval)
            if next_start_ms > requested_end_ms or len(raw_klines) < limit:
                break
            current_start_ms = next_start_ms

        self._save_checkpoint(
            symbol=normalized_symbol,
            interval=interval,
            status="completed",
            last_open_time=last_open_time,
            last_close_time=last_close_time,
            metadata={"stored_candles": stored_candles, "pages_fetched": pages_fetched},
        )
        return BackfillResult(
            symbol=normalized_symbol,
            interval=interval,
            requested_start_time=(
                _from_milliseconds(requested_start_ms)
                if requested_start_ms is not None
                else None
            ),
            requested_end_time=_from_milliseconds(requested_end_ms),
            stored_candles=stored_candles,
            pages_fetched=pages_fetched,
        )

    def _determine_start_ms(
        self, symbol: str, interval: str, start_time: datetime | int | None
    ) -> int | None:
        if start_time is not None:
            return _to_milliseconds(start_time, "start_time")

        latest_open_time = self.repository.latest_open_time(
            SOURCE_BINANCE_SPOT, symbol, interval
        )
        if latest_open_time is None:
            return 0
        return _to_milliseconds(latest_open_time, "latest_open_time") + _interval_milliseconds(
            interval
        )

    def _fetch_klines(
        self,
        *,
        symbol: str,
        interval: str,
        start_time_ms: int | None,
        end_time_ms: int,
        limit: int,
    ) -> list[object]:
        params: dict[str, int | str] = {
            "symbol": symbol,
            "interval": interval,
            "endTime": end_time_ms,
            "limit": limit,
        }
        if start_time_ms is not None:
            params["startTime"] = start_time_ms
        url = f"{self.base_url}{BINANCE_KLINES_PATH}?{urlencode(params)}"
        _reject_order_endpoint(url)

        for attempt in range(self.max_retries + 1):
            try:
                payload = self._http_get(url, self.timeout)
                return _validate_kline_page(payload)
            except RetryableBinanceError:
                if attempt >= self.max_retries:
                    raise
                self._sleep(2**attempt)
        raise AssertionError("unreachable retry loop exit")

    def _save_checkpoint(
        self,
        *,
        symbol: str,
        interval: str,
        status: str,
        last_open_time: datetime | None,
        last_close_time: datetime | None,
        metadata: dict[str, object],
    ) -> None:
        self.repository.save_checkpoint(
            IngestionCheckpoint(
                source=SOURCE_BINANCE_SPOT,
                symbol=symbol,
                interval=interval,
                mode=HISTORICAL_BACKFILL_MODE,
                last_open_time=last_open_time,
                last_close_time=last_close_time,
                last_event_time=None,
                status=status,
                metadata=metadata,
            )
        )


def map_binance_kline_to_persisted_candle(
    raw_kline: object,
    *,
    symbol: str,
    interval: str,
    now: datetime,
) -> PersistedCandle:
    """Map one Binance kline row to the accepted persisted candle schema."""

    if not isinstance(raw_kline, Sequence) or isinstance(raw_kline, (str, bytes)):
        raise ValueError("Binance kline row must be a sequence")
    if len(raw_kline) < 11:
        raise ValueError("Binance kline row must contain at least 11 fields")

    open_time_ms = _extract_open_time_ms(raw_kline, 0)
    close_time_ms = _extract_integer_field(raw_kline, 6, "close_time")
    now_ms = _to_milliseconds(now, "now")

    return PersistedCandle(
        source=SOURCE_BINANCE_SPOT,
        symbol=_normalize_symbol(symbol),
        interval=interval,
        open_time=_from_milliseconds(open_time_ms),
        close_time=_from_milliseconds(close_time_ms),
        open=_decimal_field(raw_kline, 1, "open"),
        high=_decimal_field(raw_kline, 2, "high"),
        low=_decimal_field(raw_kline, 3, "low"),
        close=_decimal_field(raw_kline, 4, "close"),
        volume=_decimal_field(raw_kline, 5, "volume"),
        quote_asset_volume=_decimal_field(raw_kline, 7, "quote_asset_volume"),
        number_of_trades=_extract_integer_field(raw_kline, 8, "number_of_trades"),
        taker_buy_base_asset_volume=_decimal_field(
            raw_kline, 9, "taker_buy_base_asset_volume"
        ),
        taker_buy_quote_asset_volume=_decimal_field(
            raw_kline, 10, "taker_buy_quote_asset_volume"
        ),
        is_closed=close_time_ms < now_ms,
        raw_payload=list(raw_kline),
    )


def _get_json(url: str, timeout: float) -> object:
    _reject_order_endpoint(url)
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310 - public data URL
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in RETRYABLE_HTTP_STATUS_CODES:
            raise RetryableBinanceError(
                f"retryable Binance market-data response: {error.code}"
            ) from error
        raise BinanceBackfillError(
            f"non-retryable Binance market-data response: {error.code}"
        ) from error
    except URLError as error:
        raise RetryableBinanceError("retryable Binance market-data request failure") from error


def _validate_kline_page(payload: object) -> list[object]:
    if isinstance(payload, dict):
        retry_markers = {"418", "429"}
        code = str(payload.get("code"))
        status = str(payload.get("status"))
        if code in retry_markers or status in retry_markers:
            raise RetryableBinanceError("Binance market-data request was rate limited")
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise ValueError("Binance kline response must be a sequence of rows")
    return list(payload)


def _reject_order_endpoint(url: str) -> None:
    normalized_url = url.lower()
    if "/order" in normalized_url or "order" in normalized_url.split("?", 1)[0]:
        raise ValueError("Binance backfill must not call order endpoints")
    forbidden_query_parts = ("apikey", "signature", "x-mbx-apikey")
    if any(part in normalized_url for part in forbidden_query_parts):
        raise ValueError("Binance backfill must not include signed request data")


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be blank")
    return normalized


def _validate_interval(interval: str) -> None:
    if interval not in MINUTE_INTERVALS:
        supported = ", ".join(sorted(MINUTE_INTERVALS))
        raise ValueError(f"interval must be a supported minute interval: {supported}")


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= limit <= BINANCE_MAX_KLINE_LIMIT:
        raise ValueError("limit must be between 1 and 1000")


def _latest_closed_open_time_ms(now: datetime, interval: str) -> int:
    now_ms = _to_milliseconds(now, "now")
    interval_ms = _interval_milliseconds(interval)
    return (now_ms // interval_ms) * interval_ms - interval_ms


def _interval_milliseconds(interval: str) -> int:
    if not interval.endswith("m"):
        raise ValueError("only minute intervals are supported")
    minutes = int(interval[:-1])
    return minutes * ONE_MINUTE_MS


def _to_milliseconds(value: datetime | int, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or millisecond integer")
    timestamp = value
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return int(timestamp.timestamp() * 1000)


def _from_milliseconds(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def _extract_open_time_ms(raw_kline: object, row_index: int) -> int:
    if not isinstance(raw_kline, Sequence) or isinstance(raw_kline, (str, bytes)):
        raise ValueError(f"Binance kline row {row_index} must be a sequence")
    return _extract_integer_field(raw_kline, 0, "open_time")


def _extract_integer_field(raw_kline: Sequence[object], index: int, field_name: str) -> int:
    try:
        value = int(raw_kline[index])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Binance kline field {field_name} must be an integer") from error
    if value < 0:
        raise ValueError(f"Binance kline field {field_name} must be non-negative")
    return value


def _decimal_field(raw_kline: Sequence[object], index: int, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_kline[index]))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Binance kline field {field_name} must be numeric") from error
