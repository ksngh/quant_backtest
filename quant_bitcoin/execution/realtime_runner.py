from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Protocol

import pandas as pd

from quant_bitcoin.execution.order_intent import ExecutionClient, ExecutionReport, OrderIntent, order_intent_from_strategy_action
from quant_bitcoin.execution.reconciliation import ExecutionQualityMetrics, reconcile_execution_report
from quant_bitcoin.market_data.binance_websocket import parse_binance_kline_message
from quant_bitcoin.persistence import SOURCE_BINANCE_SPOT, PersistedCandle
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


class RealtimeCandleRepository(Protocol):
    def upsert_candles(self, candles): ...

    def load_standard_candles(
        self,
        *,
        source: str,
        symbol: str,
        interval: str,
        start_time=None,
        end_time=None,
    ) -> list[dict[str, Any]]: ...


StrategyCallable = Callable[[pd.DataFrame], list[StrategyAction]]


@dataclass(frozen=True)
class RealtimeRunnerOutput:
    candle_identity: dict[str, Any] | None
    strategy_key: str
    triggered: bool
    actions: tuple[StrategyAction, ...] = ()
    order_intents: tuple[OrderIntent, ...] = ()
    execution_reports: tuple[ExecutionReport, ...] = ()
    execution_quality: tuple[ExecutionQualityMetrics, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass
class RealtimeCandleCloseRunner:
    """Run one strategy after a finalized candle has been persisted."""

    repository: RealtimeCandleRepository
    strategy_key: str
    strategy: StrategyCallable
    execution_client: ExecutionClient
    source: str = SOURCE_BINANCE_SPOT
    symbol: str = "BTCUSDT"
    interval: str = "1m"
    candle_window: int = 200
    dry_run: bool = True
    _processed_keys: set[tuple[str, str, str, Any, str]] = field(default_factory=set)

    def process_kline_message(self, message: Any) -> RealtimeRunnerOutput:
        candle = parse_binance_kline_message(
            message,
            expected_symbol=self.symbol,
            expected_interval=self.interval,
        )
        if candle is None:
            return RealtimeRunnerOutput(
                candle_identity=None,
                strategy_key=self.strategy_key,
                triggered=False,
                warnings=("open or non-matching kline ignored",),
            )
        return self.process_closed_candle(candle)

    def process_closed_candle(self, candle: PersistedCandle) -> RealtimeRunnerOutput:
        identity = {
            "source": candle.source,
            "symbol": candle.symbol,
            "interval": candle.interval,
            "open_time": candle.open_time,
        }
        idempotency_key = (
            candle.source,
            candle.symbol,
            candle.interval,
            candle.open_time,
            self.strategy_key,
        )
        if idempotency_key in self._processed_keys:
            return RealtimeRunnerOutput(
                candle_identity=identity,
                strategy_key=self.strategy_key,
                triggered=False,
                warnings=("duplicate candle strategy trigger ignored",),
            )

        self.repository.upsert_candles([candle])
        candles = self.repository.load_standard_candles(
            source=candle.source,
            symbol=candle.symbol,
            interval=candle.interval,
            end_time=candle.open_time,
        )
        if self.candle_window > 0:
            candles = candles[-self.candle_window :]
        frame = pd.DataFrame(candles)
        if frame.empty:
            return RealtimeRunnerOutput(
                candle_identity=identity,
                strategy_key=self.strategy_key,
                triggered=False,
                warnings=("no stored candles available for strategy input",),
            )

        actions = tuple(action for action in self.strategy(frame) if action.action_type != StrategyActionType.SKIP)
        close_price = float(frame.iloc[-1]["close"])
        intents: list[OrderIntent] = []
        reports: list[ExecutionReport] = []
        quality: list[ExecutionQualityMetrics] = []
        errors: list[str] = []
        for action in actions:
            priced_action = action if action.requested_price is not None else replace(action, requested_price=close_price)
            try:
                intent = order_intent_from_strategy_action(
                    symbol=candle.symbol,
                    action=priced_action,
                )
                report = self.execution_client.execute_order_intent(
                    intent,
                    dry_run=self.dry_run,
                )
                quality.append(
                    reconcile_execution_report(
                        report,
                        reference_price=intent.reference_price,
                    )
                )
            except Exception as error:
                errors.append(str(error))
                continue
            intents.append(intent)
            reports.append(report)

        self._processed_keys.add(idempotency_key)
        return RealtimeRunnerOutput(
            candle_identity=identity,
            strategy_key=self.strategy_key,
            triggered=True,
            actions=actions,
            order_intents=tuple(intents),
            execution_reports=tuple(reports),
            execution_quality=tuple(quality),
            errors=tuple(errors),
        )
