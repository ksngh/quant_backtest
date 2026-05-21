"""Pure portfolio equity-curve helpers for historical backtests.

This module converts standard candles plus simulated trades into an ordered,
mark-to-market equity series with drawdown values. It is intentionally pure and
side-effect free: no data fetching, no exchange calls, and no input mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.basic import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.strategies import Signal


@dataclass(frozen=True)
class EquityCurveConfig:
    """Configuration for equity-curve construction."""

    allow_empty_candles: bool = False


@dataclass(frozen=True)
class EquityCurvePoint:
    """One ordered portfolio valuation point."""

    timestamp: pd.Timestamp
    close_price: float
    cash: float
    position_quantity: float
    position_market_value: float
    equity: float
    drawdown: float = 0.0
    trade_marker: str | None = None


@dataclass(frozen=True)
class EquityCurveResult:
    """Built equity curve and metadata."""

    points: tuple[EquityCurvePoint, ...]
    trade_count: int
    starting_cash: float


def build_equity_curve_from_trades(
    candles: pd.DataFrame,
    trades: Any,
    starting_cash: float,
    mark_to_market: bool = True,
    config: EquityCurveConfig | None = None,
) -> EquityCurveResult:
    """Build an ordered equity curve from standard candles and trade-like rows.

    Trade compatibility:
    - Supports `BacktestTrade` directly.
    - Supports generic trade-like mappings/objects with timestamp, side/signal,
      price, quantity, and optional cost.
    - Pattern-strategy trade structures should be converted by callers into this
      generic trade-like shape before invoking this function.
    """

    curve_config = config or EquityCurveConfig()
    if float(starting_cash) < 0:
        raise ValueError("starting_cash must be non-negative")

    frame = _normalize_candles(candles, curve_config)
    normalized_trades = _normalize_trades(trades)

    cash = float(starting_cash)
    position_quantity = 0.0
    points: list[EquityCurvePoint] = []

    trades_by_timestamp: dict[pd.Timestamp, list[dict[str, Any]]] = {}
    for trade in normalized_trades:
        trades_by_timestamp.setdefault(trade["timestamp"], []).append(trade)

    for _, candle in frame.iterrows():
        timestamp = candle["timestamp"]
        close_price = float(candle["close"])
        marker: str | None = None

        for trade in trades_by_timestamp.get(timestamp, []):
            side = trade["side"]
            quantity = trade["quantity"]
            price = trade["price"]
            cost = trade.get("cost", 0.0)

            if side == "BUY":
                cash -= (price * quantity) + cost
                position_quantity += quantity
            elif side == "SELL":
                cash += (price * quantity) - cost
                position_quantity -= quantity

            marker = side

        position_market_value = position_quantity * close_price if mark_to_market else 0.0
        equity = cash + position_market_value

        points.append(
            EquityCurvePoint(
                timestamp=timestamp,
                close_price=close_price,
                cash=cash,
                position_quantity=position_quantity,
                position_market_value=position_market_value,
                equity=equity,
                trade_marker=marker,
            )
        )

    points_with_drawdown = calculate_drawdown_series(points)
    return EquityCurveResult(
        points=points_with_drawdown,
        trade_count=len(normalized_trades),
        starting_cash=float(starting_cash),
    )


def calculate_drawdown_series(
    equity_points: list[EquityCurvePoint] | tuple[EquityCurvePoint, ...],
) -> tuple[EquityCurvePoint, ...]:
    """Return a new tuple of equity points with deterministic drawdown values."""

    high_water_mark: float | None = None
    result: list[EquityCurvePoint] = []

    for point in equity_points:
        if high_water_mark is None:
            high_water_mark = point.equity
        else:
            high_water_mark = max(high_water_mark, point.equity)

        drawdown = 0.0
        if high_water_mark != 0:
            drawdown = (point.equity - high_water_mark) / high_water_mark

        result.append(
            EquityCurvePoint(
                timestamp=point.timestamp,
                close_price=point.close_price,
                cash=point.cash,
                position_quantity=point.position_quantity,
                position_market_value=point.position_market_value,
                equity=point.equity,
                drawdown=drawdown,
                trade_marker=point.trade_marker,
            )
        )

    return tuple(result)


def _normalize_candles(candles: pd.DataFrame, config: EquityCurveConfig) -> pd.DataFrame:
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("candles must be a pandas DataFrame")

    missing = [column for column in STANDARD_CANDLE_COLUMNS if column not in candles.columns]
    if missing:
        raise ValueError(f"candles missing required columns: {', '.join(missing)}")

    frame = candles.loc[:, STANDARD_CANDLE_COLUMNS].copy(deep=True)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise")

    if frame.empty:
        if config.allow_empty_candles:
            return frame
        raise ValueError("candles must not be empty unless allow_empty_candles=True")

    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    return frame


def _normalize_trades(trades: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for trade in list(trades or []):
        timestamp = _coerce_timestamp(_get_trade_value(trade, "timestamp"))
        side = _coerce_side(
            _get_trade_value(trade, "side", allow_missing=True)
            or _get_trade_value(trade, "signal", allow_missing=True)
        )
        price = float(_get_trade_value(trade, "price"))
        quantity = float(_get_trade_value(trade, "quantity"))
        cost_value = _get_trade_value(trade, "cost", allow_missing=True)

        normalized_trade = {
            "timestamp": timestamp,
            "side": side,
            "price": price,
            "quantity": quantity,
        }
        if cost_value is not None:
            normalized_trade["cost"] = float(cost_value)

        normalized.append(normalized_trade)

    return normalized


def _get_trade_value(trade: Any, name: str, allow_missing: bool = False) -> Any:
    if isinstance(trade, dict):
        if name in trade:
            return trade[name]
    elif hasattr(trade, name):
        return getattr(trade, name)

    if allow_missing:
        return None
    raise ValueError(f"trade is missing required field: {name}")


def _coerce_timestamp(value: Any) -> pd.Timestamp:
    return pd.Timestamp(pd.to_datetime(value, utc=True, errors="raise"))


def _coerce_side(value: Any) -> str:
    if isinstance(value, Signal):
        value = value.value
    normalized = str(value).upper()
    if normalized not in {"BUY", "SELL"}:
        raise ValueError("trade side/signal must be BUY or SELL")
    return normalized
