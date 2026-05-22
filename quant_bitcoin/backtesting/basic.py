"""Deprecated basic historical backtest engine.

Deprecated: use ``quant_bitcoin.backtesting.strategy_engine`` for active
backtest execution paths.

This module is intentionally limited to backtest responsibilities: it iterates
through standard candle data, calls a strategy, simulates in-memory trades, and
returns a small result object. It does not fetch market data, place orders, or
call exchange APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quant_bitcoin.strategies import Signal

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


@dataclass(frozen=True)
class BacktestTrade:
    """A simulated trade generated during a backtest."""

    timestamp: pd.Timestamp
    signal: Signal
    price: float
    quantity: float
    cash_after: float
    position_after: float


@dataclass(frozen=True)
class BacktestSummary:
    """Deterministic summary values for a completed backtest."""

    starting_cash: float
    ending_cash: float
    ending_position: float
    final_price: float | None
    final_equity: float
    total_return: float
    trade_count: int
    buy_count: int
    sell_count: int


def _empty_summary() -> BacktestSummary:
    return BacktestSummary(
        starting_cash=0.0,
        ending_cash=0.0,
        ending_position=0.0,
        final_price=None,
        final_equity=0.0,
        total_return=0.0,
        trade_count=0,
        buy_count=0,
        sell_count=0,
    )


@dataclass(frozen=True)
class BacktestResult:
    """Basic result returned by a historical backtest."""

    starting_cash: float
    ending_cash: float
    ending_position: float
    final_price: float | None
    final_equity: float
    trades: tuple[BacktestTrade, ...]
    summary: BacktestSummary = field(default_factory=_empty_summary)


@dataclass(frozen=True)
class BasicBacktester:
    """Run a simple long-only backtest with a fixed trade quantity."""

    starting_cash: float = 10_000.0
    trade_quantity: float = 1.0

    def __post_init__(self) -> None:
        if self.starting_cash < 0:
            raise ValueError("starting cash must be non-negative")
        if self.trade_quantity <= 0:
            raise ValueError("trade quantity must be positive")

    def run(self, candles: pd.DataFrame, strategy: Any) -> BacktestResult:
        """Run a backtest by calling ``strategy.generate_signal`` per candle.

        The simulation is intentionally small and long-only:
        - BUY opens one fixed-size position when no position is open and cash is
          sufficient.
        - SELL closes the full position when one is open.
        - HOLD, duplicate BUY while in position, SELL while flat, and BUY with
          insufficient cash do not create simulated trades.
        """

        _validate_standard_candle_data(candles)
        _validate_strategy(strategy)

        normalized = candles.loc[:, STANDARD_CANDLE_COLUMNS].copy()
        normalized["timestamp"] = _parse_timestamps(normalized["timestamp"])
        for column in NUMERIC_CANDLE_COLUMNS:
            normalized[column] = _parse_numeric_values(normalized[column], column)

        cash = float(self.starting_cash)
        position = 0.0
        trades: list[BacktestTrade] = []

        for row_index in range(len(normalized)):
            candles_so_far = normalized.iloc[: row_index + 1]
            signal = strategy.generate_signal(candles_so_far)
            timestamp = normalized.iloc[row_index]["timestamp"]
            price = float(normalized.iloc[row_index]["close"])

            if signal is Signal.BUY and position == 0:
                trade_cost = price * self.trade_quantity
                if cash >= trade_cost:
                    cash -= trade_cost
                    position += self.trade_quantity
                    trades.append(
                        BacktestTrade(
                            timestamp=timestamp,
                            signal=Signal.BUY,
                            price=price,
                            quantity=self.trade_quantity,
                            cash_after=cash,
                            position_after=position,
                        )
                    )
            elif signal is Signal.SELL and position > 0:
                quantity = position
                cash += price * quantity
                position = 0.0
                trades.append(
                    BacktestTrade(
                        timestamp=timestamp,
                        signal=Signal.SELL,
                        price=price,
                        quantity=quantity,
                        cash_after=cash,
                        position_after=position,
                    )
                )

        final_price = (
            float(normalized.iloc[-1]["close"]) if not normalized.empty else None
        )
        final_equity = cash + (
            position * final_price if final_price is not None else 0.0
        )

        completed_trades = tuple(trades)
        starting_cash = float(self.starting_cash)
        summary = _build_summary(
            starting_cash=starting_cash,
            ending_cash=cash,
            ending_position=position,
            final_price=final_price,
            final_equity=final_equity,
            trades=completed_trades,
        )

        return BacktestResult(
            starting_cash=starting_cash,
            ending_cash=cash,
            ending_position=position,
            final_price=final_price,
            final_equity=final_equity,
            trades=completed_trades,
            summary=summary,
        )


def _build_summary(
    *,
    starting_cash: float,
    ending_cash: float,
    ending_position: float,
    final_price: float | None,
    final_equity: float,
    trades: tuple[BacktestTrade, ...],
) -> BacktestSummary:
    buy_count = sum(1 for trade in trades if trade.signal is Signal.BUY)
    sell_count = sum(1 for trade in trades if trade.signal is Signal.SELL)
    total_return = (
        (final_equity - starting_cash) / starting_cash if starting_cash != 0 else 0.0
    )

    return BacktestSummary(
        starting_cash=starting_cash,
        ending_cash=ending_cash,
        ending_position=ending_position,
        final_price=final_price,
        final_equity=final_equity,
        total_return=total_return,
        trade_count=len(trades),
        buy_count=buy_count,
        sell_count=sell_count,
    )


def _validate_strategy(strategy: Any) -> None:
    if not callable(getattr(strategy, "generate_signal", None)):
        raise ValueError("strategy must provide a callable generate_signal method")


def _validate_standard_candle_data(candles: pd.DataFrame) -> None:
    missing_columns = [
        column for column in STANDARD_CANDLE_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Candle data is missing required columns: {missing}")


def _parse_timestamps(timestamp: pd.Series) -> pd.Series:
    try:
        parsed = pd.to_datetime(timestamp, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Candle data contains invalid timestamp values") from error

    if not parsed.is_monotonic_increasing:
        raise ValueError("Candle data must be sorted ascending by timestamp")
    return parsed


def _parse_numeric_values(values: pd.Series, column: str) -> pd.Series:
    try:
        return pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Candle data contains non-numeric values in column: {column}"
        ) from error
