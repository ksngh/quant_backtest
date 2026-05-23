from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from quant_bitcoin.execution.order_intent import ExecutionFill, ExecutionReport, OrderIntent
from quant_bitcoin.execution.product_policy import (
    SHORT_NOT_SUPPORTED_FOR_SPOT,
    ProductMode,
    evaluate_product_policy,
)


@dataclass
class PaperExecutionClient:
    """Deterministic in-memory execution client for canonical order intents."""

    cash_balance: float = 0.0
    positions: dict[str, float] = field(default_factory=dict)
    allow_simulated_shorts: bool = False
    product_mode: ProductMode | None = None
    reports: list[ExecutionReport] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash_balance = _validate_number(self.cash_balance, "cash_balance", allow_zero=True)
        self.positions = {
            _normalize_symbol(symbol): float(quantity)
            for symbol, quantity in self.positions.items()
        }

    def execute_order_intent(
        self,
        intent: OrderIntent,
        *,
        dry_run: bool = False,
    ) -> ExecutionReport:
        product_mode = self.product_mode or (
            ProductMode.BACKTEST_SIMULATION
            if self.allow_simulated_shorts
            else ProductMode.SPOT_PAPER
        )
        decision = evaluate_product_policy(intent, product_mode=product_mode)
        if not decision.allowed:
            return self._record_report(
                intent,
                "REJECTED",
                0.0,
                None,
                (),
                decision.reason,
                policy_metadata=decision.metadata,
            )
        price = _validate_number(intent.reference_price, "reference_price")
        quantity = _validate_number(intent.quantity, "quantity")
        if dry_run:
            return self._record_report(intent, "DRY_RUN", 0.0, None, (), None, record=False)

        if intent.action_type == "ENTER_LONG":
            return self._enter_long(intent, quantity, price)
        if intent.action_type in {"EXIT_LONG", "PARTIAL_EXIT_LONG"}:
            return self._exit_long(intent, quantity, price)
        if intent.action_type == "ENTER_SHORT":
            return self._enter_short(intent, quantity, price)
        if intent.action_type in {"EXIT_SHORT", "PARTIAL_EXIT_SHORT"}:
            return self._exit_short(intent, quantity, price)
        return self._record_report(intent, "REJECTED", 0.0, None, (), "UNSUPPORTED_ACTION_TYPE")

    def _enter_long(self, intent: OrderIntent, quantity: float, price: float) -> ExecutionReport:
        notional = quantity * price
        if notional > self.cash_balance:
            return self._record_report(intent, "REJECTED", 0.0, None, (), "INSUFFICIENT_PAPER_CASH")
        self.cash_balance -= notional
        self.positions[intent.symbol] = self.positions.get(intent.symbol, 0.0) + quantity
        return self._filled_report(intent, quantity, price)

    def _exit_long(self, intent: OrderIntent, quantity: float, price: float) -> ExecutionReport:
        current_position = self.positions.get(intent.symbol, 0.0)
        if current_position <= 0 or quantity > current_position:
            return self._record_report(intent, "REJECTED", 0.0, None, (), "INSUFFICIENT_PAPER_POSITION")
        self.cash_balance += quantity * price
        position_after = current_position - quantity
        if position_after == 0:
            self.positions.pop(intent.symbol, None)
        else:
            self.positions[intent.symbol] = position_after
        return self._filled_report(intent, quantity, price)

    def _enter_short(self, intent: OrderIntent, quantity: float, price: float) -> ExecutionReport:
        self.cash_balance += quantity * price
        self.positions[intent.symbol] = self.positions.get(intent.symbol, 0.0) - quantity
        return self._filled_report(intent, quantity, price)

    def _exit_short(self, intent: OrderIntent, quantity: float, price: float) -> ExecutionReport:
        current_position = self.positions.get(intent.symbol, 0.0)
        if current_position >= 0 or quantity > abs(current_position):
            return self._record_report(intent, "REJECTED", 0.0, None, (), "INSUFFICIENT_PAPER_SHORT_POSITION")
        self.cash_balance -= quantity * price
        position_after = current_position + quantity
        if position_after == 0:
            self.positions.pop(intent.symbol, None)
        else:
            self.positions[intent.symbol] = position_after
        return self._filled_report(intent, quantity, price)

    def _filled_report(self, intent: OrderIntent, quantity: float, price: float) -> ExecutionReport:
        fill = ExecutionFill(
            price=price,
            quantity=quantity,
            timestamp=intent.timestamp,
            raw_payload={"source": "paper"},
        )
        return self._record_report(intent, "FILLED", quantity, price, (fill,), None)

    def _record_report(
        self,
        intent: OrderIntent,
        status,
        executed_quantity: float,
        average_price: float | None,
        fills: tuple[ExecutionFill, ...],
        reason: str | None,
        *,
        record: bool = True,
        policy_metadata: dict[str, object] | None = None,
    ) -> ExecutionReport:
        metadata = {
            "cash_after": self.cash_balance,
            "position_after": self.positions.get(intent.symbol, 0.0),
            "mode": "paper",
        }
        if policy_metadata:
            metadata.update(policy_metadata)
        report = ExecutionReport(
            intent_id=intent.intent_id,
            client_order_id=intent.client_order_id or intent.intent_id[:32],
            symbol=intent.symbol,
            status=status,
            action_type=intent.action_type,
            position_side=intent.position_side,
            execution_side=intent.execution_side,
            requested_quantity=intent.quantity,
            executed_quantity=executed_quantity,
            average_price=average_price,
            fills=fills,
            reason=reason,
            metadata=metadata,
        )
        if record:
            self.reports.append(report)
        return report


def _validate_number(value: float | None, field_name: str, *, allow_zero: bool = False) -> float:
    if not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    number = float(value)
    if not isfinite(number) or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{field_name} must be positive")
    return number


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("symbol must not be blank")
    return normalized
