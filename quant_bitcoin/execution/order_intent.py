from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    execution_side_for_action,
    position_side_for_action,
)

ExecutionSide = Literal["BUY", "SELL"]
PositionSide = Literal["LONG", "SHORT"]
OrderType = Literal["MARKET", "LIMIT"]
ExecutionStatus = Literal["ACCEPTED", "FILLED", "REJECTED", "DRY_RUN"]


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    symbol: str
    action_type: str
    position_side: PositionSide
    execution_side: ExecutionSide
    quantity: float
    order_type: OrderType = "MARKET"
    reference_price: float | None = None
    client_order_id: str | None = None
    timestamp: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionFill:
    price: float
    quantity: float
    timestamp: Any | None = None
    commission: float | None = None
    commission_asset: str | None = None
    liquidity: Literal["MAKER", "TAKER"] | None = None
    raw_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionReport:
    intent_id: str
    client_order_id: str
    symbol: str
    status: ExecutionStatus
    action_type: str
    position_side: PositionSide
    execution_side: ExecutionSide
    requested_quantity: float
    executed_quantity: float
    average_price: float | None = None
    fills: tuple[ExecutionFill, ...] = ()
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ExecutionClient(Protocol):
    def execute_order_intent(self, intent: OrderIntent, *, dry_run: bool = False) -> ExecutionReport: ...


def order_intent_from_strategy_action(
    *,
    symbol: str,
    action: StrategyAction,
    default_quantity: float | None = None,
    order_type: OrderType = "MARKET",
    client_order_id: str | None = None,
) -> OrderIntent:
    if action.action_type == StrategyActionType.SKIP:
        raise ValueError("SKIP actions cannot be converted to order intents")
    position_side = position_side_for_action(action.action_type)
    execution_side = execution_side_for_action(action.action_type)
    if position_side not in {"LONG", "SHORT"} or execution_side not in {"BUY", "SELL"}:
        raise ValueError(f"unsupported action type for order intent: {action.action_type}")
    quantity = action.quantity if action.quantity is not None else default_quantity
    if quantity is None or float(quantity) <= 0:
        raise ValueError("order intent quantity must be positive")
    normalized_symbol = _normalize_symbol(symbol)
    intent_id = _stable_intent_id(
        {
            "symbol": normalized_symbol,
            "action_type": action.action_type.value,
            "timestamp": str(action.timestamp),
            "quantity": float(quantity),
            "reference_price": action.requested_price,
            "metadata": action.metadata,
        }
    )
    generated_client_order_id = client_order_id or f"qb-{intent_id[:24]}"
    return OrderIntent(
        intent_id=intent_id,
        symbol=normalized_symbol,
        action_type=action.action_type.value,
        position_side=position_side,  # type: ignore[arg-type]
        execution_side=execution_side,  # type: ignore[arg-type]
        quantity=float(quantity),
        order_type=order_type,
        reference_price=action.requested_price,
        client_order_id=generated_client_order_id,
        timestamp=action.timestamp,
        metadata=dict(action.metadata or {}),
    )


def _stable_intent_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be blank")
    return normalized
