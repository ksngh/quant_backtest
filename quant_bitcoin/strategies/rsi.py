"""RSI-based strategy components.

This module is intentionally limited to strategy responsibilities: it consumes
standard candle data, calculates RSI from close prices, and returns a signal.
It does not fetch market data, choose quantities, or execute orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

STANDARD_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class Signal(Enum):
    """Trading signal returned by strategies."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RsiSmoothingMethod(str, Enum):
    """Supported RSI smoothing methods."""

    SIMPLE = "SIMPLE"
    WILDER = "WILDER"


class RsiSignalMode(str, Enum):
    """Supported RSI signal trigger modes."""

    LEVEL = "LEVEL"
    CROSSING = "CROSSING"


@dataclass(frozen=True)
class RsiStrategy:
    """Generate signals from the latest RSI value.

    The default contract is backward-compatible with the original strategy:
    simple rolling RSI and latest-level thresholds. ``CROSSING`` mode is
    opt-in and only emits a setup signal when RSI newly crosses a threshold.
    """

    window: int = 14
    buy_threshold: float = 30.0
    sell_threshold: float = 70.0
    smoothing_method: RsiSmoothingMethod | str = RsiSmoothingMethod.SIMPLE
    signal_mode: RsiSignalMode | str = RsiSignalMode.LEVEL

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError("RSI window must be at least 1")
        if not 0 <= self.buy_threshold <= 100:
            raise ValueError("RSI buy threshold must be between 0 and 100")
        if not 0 <= self.sell_threshold <= 100:
            raise ValueError("RSI sell threshold must be between 0 and 100")
        if self.buy_threshold >= self.sell_threshold:
            raise ValueError("RSI buy threshold must be below sell threshold")
        object.__setattr__(
            self,
            "smoothing_method",
            _coerce_smoothing_method(self.smoothing_method),
        )
        object.__setattr__(
            self,
            "signal_mode",
            _coerce_signal_mode(self.signal_mode),
        )

    def generate_signal(self, candles: pd.DataFrame) -> Signal:
        """Return BUY, SELL, or HOLD for standard candle data."""

        rsi = calculate_rsi(
            candles,
            window=self.window,
            smoothing_method=self.smoothing_method,
        )
        latest_rsi = rsi.iloc[-1] if not rsi.empty else pd.NA

        if pd.isna(latest_rsi):
            return Signal.HOLD
        if self.signal_mode is RsiSignalMode.CROSSING:
            previous_rsi = rsi.iloc[-2] if len(rsi) >= 2 else pd.NA
            if pd.isna(previous_rsi):
                return Signal.HOLD
            if previous_rsi > self.buy_threshold and latest_rsi <= self.buy_threshold:
                return Signal.BUY
            if previous_rsi < self.sell_threshold and latest_rsi >= self.sell_threshold:
                return Signal.SELL
            return Signal.HOLD
        if latest_rsi <= self.buy_threshold:
            return Signal.BUY
        if latest_rsi >= self.sell_threshold:
            return Signal.SELL
        return Signal.HOLD


def calculate_rsi(
    candles: pd.DataFrame,
    window: int = 14,
    smoothing_method: RsiSmoothingMethod | str = RsiSmoothingMethod.SIMPLE,
) -> pd.Series:
    """Calculate RSI from standard candle close prices.

    Args:
        candles: Standard candle data containing the required candle schema.
        window: Rolling lookback window for average gains and losses.
        smoothing_method: ``SIMPLE`` preserves the original simple rolling RSI.
            ``WILDER`` uses Wilder's recursive moving average (RMA).

    Raises:
        ValueError: If required candle columns are missing, the window is
            invalid, smoothing method is unknown, or close prices cannot be
            treated as numeric values.
    """

    if window < 1:
        raise ValueError("RSI window must be at least 1")
    _validate_standard_candle_schema(candles)
    method = _coerce_smoothing_method(smoothing_method)

    close = _numeric_close_prices(candles["close"])
    price_changes = close.diff()
    gains = price_changes.clip(lower=0)
    losses = -price_changes.clip(upper=0)

    if method is RsiSmoothingMethod.WILDER:
        return _calculate_wilder_rsi(gains, losses, window)
    return _calculate_simple_rsi(gains, losses, window)


def _calculate_simple_rsi(
    gains: pd.Series, losses: pd.Series, window: int
) -> pd.Series:
    average_gain = gains.rolling(window=window, min_periods=window).mean()
    average_loss = losses.rolling(window=window, min_periods=window).mean()

    return _rsi_from_average_gain_loss(average_gain, average_loss)


def _calculate_wilder_rsi(
    gains: pd.Series, losses: pd.Series, window: int
) -> pd.Series:
    average_gain = pd.Series(float("nan"), index=gains.index, dtype="float64")
    average_loss = pd.Series(float("nan"), index=losses.index, dtype="float64")
    if len(gains) <= window:
        return _rsi_from_average_gain_loss(average_gain, average_loss)

    previous_average_gain = float(gains.iloc[1 : window + 1].mean())
    previous_average_loss = float(losses.iloc[1 : window + 1].mean())
    average_gain.iloc[window] = previous_average_gain
    average_loss.iloc[window] = previous_average_loss

    for index in range(window + 1, len(gains)):
        current_gain = float(gains.iloc[index])
        current_loss = float(losses.iloc[index])
        previous_average_gain = (
            previous_average_gain * (window - 1) + current_gain
        ) / window
        previous_average_loss = (
            previous_average_loss * (window - 1) + current_loss
        ) / window
        average_gain.iloc[index] = previous_average_gain
        average_loss.iloc[index] = previous_average_loss

    return _rsi_from_average_gain_loss(average_gain, average_loss)


def _rsi_from_average_gain_loss(
    average_gain: pd.Series, average_loss: pd.Series
) -> pd.Series:
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
    rsi = rsi.mask((average_gain == 0) & (average_loss > 0), 0.0)
    rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50.0)

    return rsi


def _validate_standard_candle_schema(candles: pd.DataFrame) -> None:
    missing_columns = [
        column for column in STANDARD_CANDLE_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Candle data is missing required columns: {missing}")


def _numeric_close_prices(close_prices: pd.Series) -> pd.Series:
    try:
        return pd.to_numeric(close_prices, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Candle data contains non-numeric close values") from error


def _coerce_smoothing_method(
    smoothing_method: RsiSmoothingMethod | str,
) -> RsiSmoothingMethod:
    if isinstance(smoothing_method, RsiSmoothingMethod):
        return smoothing_method
    try:
        return RsiSmoothingMethod(str(smoothing_method).upper())
    except ValueError as error:
        raise ValueError(
            "RSI smoothing method must be SIMPLE or WILDER"
        ) from error


def _coerce_signal_mode(signal_mode: RsiSignalMode | str) -> RsiSignalMode:
    if isinstance(signal_mode, RsiSignalMode):
        return signal_mode
    try:
        return RsiSignalMode(str(signal_mode).upper())
    except ValueError as error:
        raise ValueError("RSI signal mode must be LEVEL or CROSSING") from error
