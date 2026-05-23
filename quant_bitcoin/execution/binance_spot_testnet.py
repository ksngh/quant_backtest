from __future__ import annotations

import hmac
import hashlib
import json
import os
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from quant_bitcoin.execution.order_intent import ExecutionFill, ExecutionReport, OrderIntent
from quant_bitcoin.execution.product_policy import ProductMode, evaluate_product_policy

BINANCE_SPOT_TESTNET_BASE_URL = "https://testnet.binance.vision"
BINANCE_LIVE_BASE_URL = "https://api.binance.com"
ORDER_PATH = "/api/v3/order"
ALLOWED_TESTNET_PATHS = frozenset({ORDER_PATH})
DEFAULT_RECV_WINDOW_MS = 5000

HttpClient = Callable[[str, str, dict[str, str], str, float], dict[str, Any]]
TimeProviderMs = Callable[[], int]


class BinanceTestnetExecutionError(RuntimeError):
    pass


class BinanceSpotTestnetExecutionClient:
    """Canonical execution client for Binance Spot testnet orders only."""

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        base_url: str = BINANCE_SPOT_TESTNET_BASE_URL,
        http_client: HttpClient | None = None,
        time_provider_ms: TimeProviderMs | None = None,
        recv_window_ms: int = DEFAULT_RECV_WINDOW_MS,
        timeout: float = 10.0,
    ) -> None:
        if not api_key:
            raise BinanceTestnetExecutionError("BINANCE_TESTNET_API_KEY is required")
        if not api_secret:
            raise BinanceTestnetExecutionError("BINANCE_TESTNET_API_SECRET is required")
        normalized_base_url = base_url.rstrip("/")
        if normalized_base_url == BINANCE_LIVE_BASE_URL:
            raise BinanceTestnetExecutionError("live Binance base URL is not allowed in testnet client")
        if "testnet.binance.vision" not in normalized_base_url:
            raise BinanceTestnetExecutionError("testnet client requires Binance Spot testnet base URL")
        if recv_window_ms <= 0:
            raise ValueError("recv_window_ms must be positive")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = normalized_base_url
        self._http_client = http_client or _urllib_http_client
        self._time_provider_ms = time_provider_ms or (lambda: int(time.time() * 1000))
        self.recv_window_ms = recv_window_ms
        self.timeout = timeout

    @classmethod
    def from_env(cls, **kwargs):
        return cls(
            api_key=os.environ.get("BINANCE_TESTNET_API_KEY", ""),
            api_secret=os.environ.get("BINANCE_TESTNET_API_SECRET", ""),
            **kwargs,
        )

    def execute_order_intent(
        self,
        intent: OrderIntent,
        *,
        dry_run: bool = False,
    ) -> ExecutionReport:
        decision = evaluate_product_policy(intent, product_mode=ProductMode.SPOT_TESTNET)
        if not decision.allowed:
            return _rejected_report(intent, decision.reason, decision.metadata)
        if dry_run:
            return _dry_run_report(intent, decision.metadata)

        params = self._build_order_params(intent)
        response = self._signed_request("POST", ORDER_PATH, params)
        return _execution_report_from_binance_response(
            intent,
            response,
            policy_metadata=decision.metadata,
        )

    def _build_order_params(self, intent: OrderIntent) -> dict[str, str | int]:
        if intent.order_type not in {"MARKET", "LIMIT"}:
            raise BinanceTestnetExecutionError(f"unsupported order type: {intent.order_type}")
        params: dict[str, str | int] = {
            "symbol": intent.symbol,
            "side": intent.execution_side,
            "type": intent.order_type,
            "quantity": _format_decimal(intent.quantity),
            "newClientOrderId": intent.client_order_id or intent.intent_id[:32],
            "recvWindow": self.recv_window_ms,
            "timestamp": self._time_provider_ms(),
        }
        if intent.order_type == "LIMIT":
            if intent.reference_price is None:
                raise BinanceTestnetExecutionError("LIMIT orders require reference_price")
            params["price"] = _format_decimal(intent.reference_price)
            params["timeInForce"] = "GTC"
        return params

    def _signed_request(
        self,
        method: str,
        path: str,
        params: dict[str, str | int],
    ) -> dict[str, Any]:
        _validate_allowed_path(path)
        query = urlencode(params)
        signature = sign_query_string(query, self.api_secret)
        body = f"{query}&signature={signature}"
        url = f"{self.base_url}{path}"
        response = self._http_client(
            method,
            url,
            {"X-MBX-APIKEY": self.api_key, "Content-Type": "application/x-www-form-urlencoded"},
            body,
            self.timeout,
        )
        if not isinstance(response, dict):
            raise BinanceTestnetExecutionError("Binance testnet response must be a JSON object")
        return response


def sign_query_string(query_string: str, api_secret: str) -> str:
    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _validate_allowed_path(path: str) -> None:
    if path not in ALLOWED_TESTNET_PATHS:
        raise BinanceTestnetExecutionError(f"endpoint is not allowlisted: {path}")


def _execution_report_from_binance_response(
    intent: OrderIntent,
    response: dict[str, Any],
    *,
    policy_metadata: dict[str, object] | None = None,
) -> ExecutionReport:
    fills = tuple(_fill_from_response(fill) for fill in response.get("fills", []) or [])
    executed_quantity = float(response.get("executedQty", 0) or 0)
    average_price = _average_price(fills)
    metadata = {"raw_response": response}
    if policy_metadata:
        metadata.update(policy_metadata)
    return ExecutionReport(
        intent_id=intent.intent_id,
        client_order_id=str(response.get("clientOrderId") or intent.client_order_id or intent.intent_id[:32]),
        symbol=str(response.get("symbol") or intent.symbol),
        status="FILLED" if str(response.get("status", "")).upper() == "FILLED" else "ACCEPTED",
        action_type=intent.action_type,
        position_side=intent.position_side,
        execution_side=intent.execution_side,
        requested_quantity=intent.quantity,
        executed_quantity=executed_quantity,
        average_price=average_price,
        fills=fills,
        metadata=metadata,
    )


def _fill_from_response(raw_fill: dict[str, Any]) -> ExecutionFill:
    return ExecutionFill(
        price=float(raw_fill.get("price", 0) or 0),
        quantity=float(raw_fill.get("qty", raw_fill.get("quantity", 0)) or 0),
        commission=(
            float(raw_fill["commission"])
            if raw_fill.get("commission") is not None
            else None
        ),
        commission_asset=raw_fill.get("commissionAsset"),
        liquidity=("MAKER" if raw_fill.get("isMaker") is True else "TAKER" if raw_fill.get("isMaker") is False else None),
        raw_payload=dict(raw_fill),
    )


def _average_price(fills: tuple[ExecutionFill, ...]) -> float | None:
    total_quantity = sum(fill.quantity for fill in fills)
    if total_quantity <= 0:
        return None
    return sum(fill.price * fill.quantity for fill in fills) / total_quantity


def _dry_run_report(
    intent: OrderIntent,
    policy_metadata: dict[str, object] | None,
) -> ExecutionReport:
    metadata = {"mode": "testnet_dry_run"}
    if policy_metadata:
        metadata.update(policy_metadata)
    return ExecutionReport(
        intent_id=intent.intent_id,
        client_order_id=intent.client_order_id or intent.intent_id[:32],
        symbol=intent.symbol,
        status="DRY_RUN",
        action_type=intent.action_type,
        position_side=intent.position_side,
        execution_side=intent.execution_side,
        requested_quantity=intent.quantity,
        executed_quantity=0.0,
        metadata=metadata,
    )


def _rejected_report(
    intent: OrderIntent,
    reason: str | None,
    policy_metadata: dict[str, object] | None,
) -> ExecutionReport:
    metadata = {}
    if policy_metadata:
        metadata.update(policy_metadata)
    return ExecutionReport(
        intent_id=intent.intent_id,
        client_order_id=intent.client_order_id or intent.intent_id[:32],
        symbol=intent.symbol,
        status="REJECTED",
        action_type=intent.action_type,
        position_side=intent.position_side,
        execution_side=intent.execution_side,
        requested_quantity=intent.quantity,
        executed_quantity=0.0,
        reason=reason,
        metadata=metadata,
    )


def _format_decimal(value: float) -> str:
    return f"{float(value):.12g}"


def _urllib_http_client(
    method: str,
    url: str,
    headers: dict[str, str],
    body: str,
    timeout: float,
) -> dict[str, Any]:
    request = Request(
        url,
        data=body.encode("utf-8"),
        headers=headers,
        method=method,
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit execution client
        return json.loads(response.read().decode("utf-8"))
