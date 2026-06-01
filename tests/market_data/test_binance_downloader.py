from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from quant_bitcoin.market_data import BinanceCandleDownloader, normalize_binance_klines
from quant_bitcoin.market_data.binance_downloader import STANDARD_CANDLE_COLUMNS


def sample_klines() -> list[list[object]]:
    return [
        [
            1_704_067_260_000,
            "43000.5",
            "43100",
            "42950",
            "43050",
            "12.5",
            1_704_067_319_999,
            "0",
            1,
            "0",
            "0",
            "0",
        ],
        [
            1_704_067_200_000,
            "42000",
            "42500",
            "41900",
            "42400",
            "10",
            1_704_067_259_999,
            "0",
            1,
            "0",
            "0",
            "0",
        ],
    ]


def test_normalize_binance_klines_returns_standard_candle_schema_sorted():
    candles = normalize_binance_klines(sample_klines())

    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)
    assert candles["timestamp"].tolist() == [
        pd.Timestamp("2024-01-01 00:00:00"),
        pd.Timestamp("2024-01-01 00:01:00"),
    ]
    assert candles["open"].tolist() == [42000.0, 43000.5]
    assert candles["high"].tolist() == [42500, 43100]
    assert candles["low"].tolist() == [41900, 42950]
    assert candles["close"].tolist() == [42400, 43050]
    assert candles["volume"].tolist() == [10.0, 12.5]


def test_fetch_historical_candles_builds_public_kline_request_and_normalizes():
    requested: dict[str, object] = {}

    def fake_http_get(url: str, timeout: float) -> object:
        requested["url"] = url
        requested["timeout"] = timeout
        assert "/api/v3/klines" in url
        assert "order" not in url.lower()
        return sample_klines()

    downloader = BinanceCandleDownloader(timeout=3.5, http_get=fake_http_get)

    candles = downloader.fetch_historical_candles(
        " btcusdt ",
        "1m",
        start_time="2024-01-01 00:00:00",
        end_time="2024-01-01 00:01:00",
        limit=2,
    )

    parsed_url = urlparse(str(requested["url"]))
    query = parse_qs(parsed_url.query)
    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "data-api.binance.vision"
    assert parsed_url.path == "/api/v3/klines"
    assert query == {
        "symbol": ["BTCUSDT"],
        "interval": ["1m"],
        "limit": ["2"],
        "startTime": ["1704067200000"],
        "endTime": ["1704067260000"],
    }
    assert requested["timeout"] == 3.5
    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)


@pytest.mark.parametrize("interval", ["1m", "3m", "5m", "15m", "30m", "1h", "1d"])
def test_downloader_supports_configured_kline_intervals(interval):
    requested_urls: list[str] = []

    def fake_http_get(url: str, timeout: float) -> object:
        requested_urls.append(url)
        return []

    downloader = BinanceCandleDownloader(http_get=fake_http_get)

    candles = downloader.fetch_historical_candles("BTCUSDT", interval)

    assert candles.empty
    assert f"interval={interval}" in requested_urls[0]


def test_downloader_uses_configurable_base_url_for_mocked_http_integration():
    requested_urls: list[str] = []

    def fake_http_get(url: str, timeout: float) -> object:
        requested_urls.append(url)
        return []

    downloader = BinanceCandleDownloader(
        base_url="https://example.test/binance", http_get=fake_http_get
    )

    downloader.fetch_historical_candles("BTCUSDT", "1m", limit=1)

    assert requested_urls == [
        "https://example.test/binance/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1"
    ]


def test_normalize_binance_klines_rejects_non_sequence_response():
    with pytest.raises(ValueError, match="response must be a sequence of rows"):
        normalize_binance_klines({"unexpected": "payload"})


def test_normalize_binance_klines_rejects_short_rows():
    with pytest.raises(ValueError, match="row 0 has fewer than 6 fields"):
        normalize_binance_klines([[1_704_067_200_000, "42000"]])


def test_normalize_binance_klines_rejects_invalid_open_times():
    rows = sample_klines()
    rows[0][0] = "not-a-timestamp"

    with pytest.raises(ValueError, match="invalid open times"):
        normalize_binance_klines(rows)


def test_normalize_binance_klines_rejects_non_numeric_values():
    rows = sample_klines()
    rows[0][4] = "not-a-number"

    with pytest.raises(ValueError, match="non-numeric values in column: close"):
        normalize_binance_klines(rows)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"symbol": "   "}, "symbol must not be blank"),
        ({"interval": "2h"}, "supported Binance kline interval"),
        ({"limit": True}, "limit must be an integer"),
        ({"limit": 0}, "limit must be between 1 and 1000"),
        ({"limit": 1001}, "limit must be between 1 and 1000"),
        ({"start_time": -1}, "start_time must be non-negative"),
        (
            {"start_time": "2024-01-02", "end_time": "2024-01-01"},
            "start_time must be before or equal to end_time",
        ),
    ],
)
def test_downloader_rejects_invalid_request_parameters(kwargs, message):
    downloader = BinanceCandleDownloader(http_get=lambda url, timeout: [])
    params = {"symbol": "BTCUSDT", "interval": "1m", "limit": 1}
    params.update(kwargs)

    with pytest.raises(ValueError, match=message):
        downloader.fetch_historical_candles(**params)


def test_downloader_does_not_send_api_keys_or_call_order_endpoints():
    def fake_http_get(url: str, timeout: float) -> object:
        assert "apiKey" not in url
        assert "signature" not in url
        assert "X-MBX-APIKEY" not in url
        assert "/order" not in url.lower()
        return []

    downloader = BinanceCandleDownloader(http_get=fake_http_get)

    candles = downloader.fetch_historical_candles("BTCUSDT", "1m")

    assert candles.empty
