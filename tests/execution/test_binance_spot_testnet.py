from __future__ import annotations

from urllib.parse import parse_qs

import pytest

from quant_bitcoin.execution import (
    BINANCE_SPOT_TESTNET_BASE_URL,
    BinanceSpotTestnetExecutionClient,
    BinanceTestnetExecutionError,
    SHORT_NOT_SUPPORTED_FOR_SPOT,
    order_intent_from_strategy_action,
    sign_query_string,
)
from quant_bitcoin.execution.binance_spot_testnet import BINANCE_LIVE_BASE_URL, _validate_allowed_path
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _intent(action_type=StrategyActionType.ENTER_LONG):
    return order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(action_type, timestamp=1, quantity=0.5, requested_price=100),
    )


def test_hmac_signature_generation_with_fake_values() -> None:
    query = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"

    assert sign_query_string(query, "fake-secret") == (
        "e7d6781000a9e2b1d006f56c74fba4e993e11507d1f58644d7f6a6e3e5b9259f"
    )


def test_missing_testnet_credentials_fail_closed(monkeypatch) -> None:
    monkeypatch.delenv("BINANCE_TESTNET_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_TESTNET_API_SECRET", raising=False)

    with pytest.raises(BinanceTestnetExecutionError, match="BINANCE_TESTNET_API_KEY"):
        BinanceSpotTestnetExecutionClient.from_env()


def test_missing_testnet_secret_fails_closed() -> None:
    with pytest.raises(BinanceTestnetExecutionError, match="BINANCE_TESTNET_API_SECRET"):
        BinanceSpotTestnetExecutionClient(api_key="key", api_secret="")


def test_live_url_is_rejected() -> None:
    with pytest.raises(BinanceTestnetExecutionError, match="live Binance base URL"):
        BinanceSpotTestnetExecutionClient(
            api_key="key",
            api_secret="secret",
            base_url=BINANCE_LIVE_BASE_URL,
        )


def test_endpoint_allowlist_rejects_unknown_path() -> None:
    with pytest.raises(BinanceTestnetExecutionError, match="allowlisted"):
        _validate_allowed_path("/api/v3/account")


def test_enter_long_maps_to_signed_spot_buy_request() -> None:
    captured = {}

    def fake_http(method, url, headers, body, timeout):
        captured.update(method=method, url=url, headers=headers, body=body, timeout=timeout)
        return {
            "symbol": "BTCUSDT",
            "clientOrderId": "client-1",
            "status": "FILLED",
            "executedQty": "0.5",
            "fills": [{"price": "100", "qty": "0.5", "commission": "0.01", "commissionAsset": "USDT"}],
        }

    client = BinanceSpotTestnetExecutionClient(
        api_key="key",
        api_secret="secret",
        http_client=fake_http,
        time_provider_ms=lambda: 1234567890,
    )

    report = client.execute_order_intent(_intent())

    assert captured["method"] == "POST"
    assert captured["url"] == f"{BINANCE_SPOT_TESTNET_BASE_URL}/api/v3/order"
    assert captured["headers"]["X-MBX-APIKEY"] == "key"
    params = parse_qs(captured["body"])
    assert params["symbol"] == ["BTCUSDT"]
    assert params["side"] == ["BUY"]
    assert params["type"] == ["MARKET"]
    assert params["timestamp"] == ["1234567890"]
    assert params["recvWindow"] == ["5000"]
    assert "signature" in params
    assert report.status == "FILLED"
    assert report.average_price == 100
    assert report.fills[0].commission_asset == "USDT"


def test_exit_long_maps_to_spot_sell_request() -> None:
    captured = {}

    def fake_http(method, url, headers, body, timeout):
        captured["body"] = body
        return {"symbol": "BTCUSDT", "status": "NEW", "executedQty": "0"}

    client = BinanceSpotTestnetExecutionClient(
        api_key="key",
        api_secret="secret",
        http_client=fake_http,
        time_provider_ms=lambda: 1,
    )

    report = client.execute_order_intent(_intent(StrategyActionType.EXIT_LONG))

    assert parse_qs(captured["body"])["side"] == ["SELL"]
    assert report.status == "ACCEPTED"


def test_enter_short_is_blocked_before_request_creation() -> None:
    def unexpected_http(*args, **kwargs):
        raise AssertionError("blocked spot short must not make HTTP request")

    client = BinanceSpotTestnetExecutionClient(
        api_key="key",
        api_secret="secret",
        http_client=unexpected_http,
    )

    report = client.execute_order_intent(_intent(StrategyActionType.ENTER_SHORT))

    assert report.status == "REJECTED"
    assert report.reason == SHORT_NOT_SUPPORTED_FOR_SPOT


def test_testnet_client_dry_run_does_not_call_http() -> None:
    def unexpected_http(*args, **kwargs):
        raise AssertionError("dry-run should not send a network request")

    client = BinanceSpotTestnetExecutionClient(
        api_key="key",
        api_secret="secret",
        http_client=unexpected_http,
    )

    report = client.execute_order_intent(_intent(), dry_run=True)

    assert report.status == "DRY_RUN"
    assert report.metadata["product_mode"] == "SPOT_TESTNET"
