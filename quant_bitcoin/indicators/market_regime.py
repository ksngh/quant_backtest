"""Market-regime feature tagging from supplied OHLCV candles.

This module is a pure offline indicator helper. It consumes already-provided
candle rows and does not fetch market data, read secrets, call exchange APIs,
place orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean, pstdev
from typing import Any

import pandas as pd

REQUIRED_MARKET_REGIME_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

MARKET_REGIME_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "close",
    "return_rate",
    "realized_volatility",
    "volatility_regime",
    "trading_value",
    "average_trading_value",
    "trading_value_percentile",
    "liquidity_zscore",
    "liquidity_regime",
    "spread_proxy",
    "range_spread_proxy_percentile",
    "spread_regime",
    "wick_dominance_proxy",
    "session_tag",
    "weekday_tag",
    "trend_strength",
    "trend_regime",
    "mean_reversion_zscore",
    "mean_reversion_regime",
    "market_regime",
    "is_valid",
    "reason",
)


class RegimeVolatility(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class LiquidityRegime(Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    UNTRADABLE = "UNTRADABLE"
    UNKNOWN = "UNKNOWN"


class SpreadRegime(Enum):
    TIGHT = "TIGHT"
    NORMAL = "NORMAL"
    WIDE = "WIDE"
    UNKNOWN = "UNKNOWN"


class TrendRegime(Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGE = "RANGE"
    UNKNOWN = "UNKNOWN"


class MeanReversionRegime(Enum):
    OVERBOUGHT = "OVERBOUGHT"
    OVERSOLD = "OVERSOLD"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MarketRegimeConfig:
    """Configuration for deterministic OHLCV-derived regime labels."""

    volatility_window: int = 20
    trend_window: int = 20
    liquidity_window: int = 20
    mean_reversion_window: int = 20
    low_volatility_threshold: float = 0.005
    high_volatility_threshold: float = 0.02
    minimum_average_trading_value: float = 1_000_000.0
    low_spread_threshold: float = 0.002
    high_spread_threshold: float = 0.01
    trend_strength_threshold: float = 0.02
    mean_reversion_zscore_threshold: float = 1.0
    use_quote_volume_if_available: bool = True
    require_full_window: bool = True

    def __post_init__(self) -> None:
        for name in (
            "volatility_window",
            "trend_window",
            "liquidity_window",
            "mean_reversion_window",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")
        for name in (
            "low_volatility_threshold",
            "high_volatility_threshold",
            "minimum_average_trading_value",
            "low_spread_threshold",
            "high_spread_threshold",
            "trend_strength_threshold",
            "mean_reversion_zscore_threshold",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.low_volatility_threshold > self.high_volatility_threshold:
            raise ValueError("low_volatility_threshold must be less than or equal to high_volatility_threshold")
        if self.low_spread_threshold > self.high_spread_threshold:
            raise ValueError("low_spread_threshold must be less than or equal to high_spread_threshold")


def calculate_market_regime(
    candles: pd.DataFrame,
    config: MarketRegimeConfig | None = None,
) -> pd.DataFrame:
    """Return OHLCV-derived regime rows for every supplied candle."""

    regime_config = config or MarketRegimeConfig()
    _validate_candles(candles)

    if candles.empty:
        return pd.DataFrame(columns=MARKET_REGIME_OUTPUT_COLUMNS)

    open_values = pd.to_numeric(candles["open"], errors="raise")
    high_values = pd.to_numeric(candles["high"], errors="raise")
    low_values = pd.to_numeric(candles["low"], errors="raise")
    close_values = pd.to_numeric(candles["close"], errors="raise")
    volume_values = pd.to_numeric(candles["volume"], errors="raise")
    quote_volume_values = (
        pd.to_numeric(candles["quote_volume"], errors="raise")
        if regime_config.use_quote_volume_if_available and "quote_volume" in candles.columns
        else None
    )

    returns = _return_rates(close_values)
    trading_values = _trading_values(close_values, volume_values, quote_volume_values)
    rows: list[dict[str, Any]] = []

    for position, (_, candle) in enumerate(candles.iterrows()):
        close = _optional_float(close_values.iloc[position])
        high = _optional_float(high_values.iloc[position])
        low = _optional_float(low_values.iloc[position])
        open_price = _optional_float(open_values.iloc[position])
        volume = _optional_float(volume_values.iloc[position])

        base = {
            "symbol": candle["symbol"],
            "timestamp": candle["timestamp"],
            "close": close,
            "return_rate": returns[position],
        }

        invalid_reason = _invalid_reason(open_price, high, low, close, volume)
        if invalid_reason is not None:
            rows.append(_invalid_row(base, trading_values[position], invalid_reason))
            continue

        volatility = _rolling_population_std(returns, position, regime_config.volatility_window, regime_config.require_full_window)
        trading_value = trading_values[position]
        average_trading_value = _rolling_mean(trading_values, position, regime_config.liquidity_window, regime_config.require_full_window)
        spread_proxy = ((high or 0.0) - (low or 0.0)) / close if close and close > 0 else None
        spread_values = _spread_proxy_values(high_values, low_values, close_values)
        trading_value_percentile = _rolling_percentile_rank(trading_values, position, regime_config.liquidity_window, regime_config.require_full_window)
        liquidity_zscore = _rolling_zscore(trading_values, position, regime_config.liquidity_window, regime_config.require_full_window)
        range_spread_proxy_percentile = _rolling_percentile_rank(spread_values, position, regime_config.liquidity_window, regime_config.require_full_window)
        wick_dominance_proxy = _wick_dominance_proxy(open_price, high, low, close)
        session_tag = classify_utc_session(candle["timestamp"])
        weekday_tag = classify_weekday_tag(candle["timestamp"])
        trend_strength = _trend_strength(close_values, position, regime_config)
        zscore = _mean_reversion_zscore(close_values, position, regime_config)
        values_ready = all(
            value is not None
            for value in (
                volatility,
                trading_value,
                average_trading_value,
                spread_proxy,
                trend_strength,
                zscore,
            )
        )

        volatility_regime = classify_regime_volatility(volatility, regime_config)
        liquidity_regime = classify_liquidity_regime(average_trading_value, regime_config)
        spread_regime = classify_spread_regime(spread_proxy, regime_config)
        trend_regime = classify_trend_regime(trend_strength, regime_config)
        mean_reversion_regime = classify_mean_reversion_regime(zscore, regime_config)
        market_regime = combine_market_regime(volatility_regime, trend_regime, mean_reversion_regime)

        rows.append(
            {
                **base,
                "realized_volatility": volatility,
                "volatility_regime": volatility_regime,
                "trading_value": trading_value,
                "average_trading_value": average_trading_value,
                "trading_value_percentile": trading_value_percentile,
                "liquidity_zscore": liquidity_zscore,
                "liquidity_regime": liquidity_regime,
                "spread_proxy": spread_proxy,
                "range_spread_proxy_percentile": range_spread_proxy_percentile,
                "spread_regime": spread_regime,
                "wick_dominance_proxy": wick_dominance_proxy,
                "session_tag": session_tag,
                "weekday_tag": weekday_tag,
                "trend_strength": trend_strength,
                "trend_regime": trend_regime,
                "mean_reversion_zscore": zscore,
                "mean_reversion_regime": mean_reversion_regime,
                "market_regime": market_regime if values_ready else "UNKNOWN",
                "is_valid": bool(values_ready),
                "reason": None if values_ready else "warmup",
            }
        )

    return pd.DataFrame(rows, columns=MARKET_REGIME_OUTPUT_COLUMNS)


def calculate_market_regime_snapshot(
    candles: pd.DataFrame,
    config: MarketRegimeConfig | None = None,
) -> dict[str, Any]:
    rows = calculate_market_regime(candles, config)
    if rows.empty:
        return {column: None for column in MARKET_REGIME_OUTPUT_COLUMNS}
    return rows.iloc[-1].to_dict()


def classify_regime_volatility(
    realized_volatility: float | None,
    config: MarketRegimeConfig | None = None,
) -> str:
    regime_config = config or MarketRegimeConfig()
    if realized_volatility is None:
        return RegimeVolatility.UNKNOWN.value
    if realized_volatility >= regime_config.high_volatility_threshold:
        return RegimeVolatility.HIGH.value
    if realized_volatility <= regime_config.low_volatility_threshold:
        return RegimeVolatility.LOW.value
    return RegimeVolatility.NORMAL.value


def classify_liquidity_regime(
    average_trading_value: float | None,
    config: MarketRegimeConfig | None = None,
) -> str:
    regime_config = config or MarketRegimeConfig()
    if average_trading_value is None:
        return LiquidityRegime.UNKNOWN.value
    if average_trading_value >= regime_config.minimum_average_trading_value * 5:
        return LiquidityRegime.HIGH.value
    if average_trading_value >= regime_config.minimum_average_trading_value:
        return LiquidityRegime.NORMAL.value
    if average_trading_value > 0:
        return LiquidityRegime.LOW.value
    return LiquidityRegime.UNTRADABLE.value


def classify_spread_regime(
    spread_proxy: float | None,
    config: MarketRegimeConfig | None = None,
) -> str:
    regime_config = config or MarketRegimeConfig()
    if spread_proxy is None:
        return SpreadRegime.UNKNOWN.value
    if spread_proxy <= regime_config.low_spread_threshold:
        return SpreadRegime.TIGHT.value
    if spread_proxy >= regime_config.high_spread_threshold:
        return SpreadRegime.WIDE.value
    return SpreadRegime.NORMAL.value


def classify_trend_regime(
    trend_strength: float | None,
    config: MarketRegimeConfig | None = None,
) -> str:
    regime_config = config or MarketRegimeConfig()
    if trend_strength is None:
        return TrendRegime.UNKNOWN.value
    if trend_strength >= regime_config.trend_strength_threshold:
        return TrendRegime.UPTREND.value
    if trend_strength <= -regime_config.trend_strength_threshold:
        return TrendRegime.DOWNTREND.value
    return TrendRegime.RANGE.value


def classify_mean_reversion_regime(
    zscore: float | None,
    config: MarketRegimeConfig | None = None,
) -> str:
    regime_config = config or MarketRegimeConfig()
    if zscore is None:
        return MeanReversionRegime.UNKNOWN.value
    if zscore >= regime_config.mean_reversion_zscore_threshold:
        return MeanReversionRegime.OVERBOUGHT.value
    if zscore <= -regime_config.mean_reversion_zscore_threshold:
        return MeanReversionRegime.OVERSOLD.value
    return MeanReversionRegime.NEUTRAL.value


def combine_market_regime(
    volatility_regime: str,
    trend_regime: str,
    mean_reversion_regime: str,
) -> str:
    if TrendRegime.UNKNOWN.value in (trend_regime,) or RegimeVolatility.UNKNOWN.value in (volatility_regime,):
        return "UNKNOWN"
    if trend_regime in (TrendRegime.UPTREND.value, TrendRegime.DOWNTREND.value):
        if volatility_regime == RegimeVolatility.HIGH.value:
            return f"HIGH_VOL_{trend_regime}"
        if volatility_regime == RegimeVolatility.LOW.value:
            return f"LOW_VOL_{trend_regime}"
        return trend_regime
    if mean_reversion_regime in (MeanReversionRegime.OVERBOUGHT.value, MeanReversionRegime.OVERSOLD.value):
        return "MEAN_REVERSION_EXTREME"
    if volatility_regime == RegimeVolatility.LOW.value:
        return "LOW_VOL_RANGE"
    if volatility_regime == RegimeVolatility.HIGH.value:
        return "HIGH_VOL_RANGE"
    return TrendRegime.RANGE.value


def classify_utc_session(timestamp: Any) -> str:
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    hour = ts.hour
    if 12 <= hour < 16:
        return "EU_US_OVERLAP"
    if 0 <= hour < 8:
        return "ASIA"
    if 8 <= hour < 12:
        return "EU"
    if 16 <= hour < 21:
        return "US"
    return "OFF_HOURS"


def classify_weekday_tag(timestamp: Any) -> str:
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return "WEEKEND" if ts.weekday() >= 5 else "WEEKDAY"


def _validate_candles(candles: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REQUIRED_MARKET_REGIME_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(f"missing required Market Regime columns: {joined}")


def _return_rates(close_values: pd.Series) -> list[float | None]:
    returns: list[float | None] = []
    for position, close in enumerate(close_values):
        current = _optional_float(close)
        previous = _optional_float(close_values.iloc[position - 1]) if position > 0 else None
        if current is None or previous is None or previous == 0:
            returns.append(None)
        else:
            returns.append((current - previous) / previous)
    return returns


def _trading_values(
    close_values: pd.Series,
    volume_values: pd.Series,
    quote_volume_values: pd.Series | None,
) -> list[float | None]:
    values: list[float | None] = []
    for position in range(len(close_values)):
        quote_volume = _optional_float(quote_volume_values.iloc[position]) if quote_volume_values is not None else None
        close = _optional_float(close_values.iloc[position])
        volume = _optional_float(volume_values.iloc[position])
        if quote_volume is not None:
            values.append(quote_volume)
        elif close is not None and volume is not None:
            values.append(close * volume)
        else:
            values.append(None)
    return values


def _rolling_population_std(
    values: list[float | None],
    position: int,
    window: int,
    require_full_window: bool,
) -> float | None:
    window_values = _window(values, position, window, require_full_window)
    if window_values is None:
        return None
    return pstdev(window_values)


def _rolling_mean(
    values: list[float | None],
    position: int,
    window: int,
    require_full_window: bool,
) -> float | None:
    window_values = _window(values, position, window, require_full_window)
    if window_values is None:
        return None
    return mean(window_values)


def _rolling_percentile_rank(
    values: list[float | None],
    position: int,
    window: int,
    require_full_window: bool,
) -> float | None:
    window_values = _window(values, position, window, require_full_window)
    current = values[position]
    if window_values is None or current is None:
        return None
    less_or_equal = len([value for value in window_values if value <= float(current)])
    return less_or_equal / len(window_values)


def _rolling_zscore(
    values: list[float | None],
    position: int,
    window: int,
    require_full_window: bool,
) -> float | None:
    window_values = _window(values, position, window, require_full_window)
    current = values[position]
    if window_values is None or current is None:
        return None
    baseline = mean(window_values)
    deviation = pstdev(window_values)
    if deviation == 0:
        return 0.0
    return (float(current) - baseline) / deviation


def _spread_proxy_values(high_values: pd.Series, low_values: pd.Series, close_values: pd.Series) -> list[float | None]:
    values: list[float | None] = []
    for position in range(len(close_values)):
        high = _optional_float(high_values.iloc[position])
        low = _optional_float(low_values.iloc[position])
        close = _optional_float(close_values.iloc[position])
        values.append(((high or 0.0) - (low or 0.0)) / close if high is not None and low is not None and close and close > 0 else None)
    return values


def _wick_dominance_proxy(open_price: float | None, high: float | None, low: float | None, close: float | None) -> float | None:
    if None in (open_price, high, low, close):
        return None
    assert open_price is not None and high is not None and low is not None and close is not None
    candle_range = high - low
    if candle_range <= 0:
        return 0.0
    body_high = max(open_price, close)
    body_low = min(open_price, close)
    wick_total = max(0.0, high - body_high) + max(0.0, body_low - low)
    return wick_total / candle_range


def _trend_strength(
    close_values: pd.Series,
    position: int,
    config: MarketRegimeConfig,
) -> float | None:
    start_position = max(0, position + 1 - config.trend_window)
    if config.require_full_window and position + 1 - start_position < config.trend_window:
        return None
    start = _optional_float(close_values.iloc[start_position])
    current = _optional_float(close_values.iloc[position])
    if start is None or current is None or start == 0:
        return None
    return (current - start) / start


def _mean_reversion_zscore(
    close_values: pd.Series,
    position: int,
    config: MarketRegimeConfig,
) -> float | None:
    raw_values = [_optional_float(value) for value in close_values.iloc[max(0, position + 1 - config.mean_reversion_window) : position + 1]]
    if config.require_full_window and len(raw_values) < config.mean_reversion_window:
        return None
    if any(value is None for value in raw_values):
        return None
    values = [value for value in raw_values if value is not None]
    if not values:
        return None
    baseline = mean(values)
    deviation = pstdev(values)
    if deviation == 0:
        return 0.0
    return (values[-1] - baseline) / deviation


def _window(
    values: list[float | None],
    position: int,
    window: int,
    require_full_window: bool,
) -> list[float] | None:
    raw_values = values[max(0, position + 1 - window) : position + 1]
    if require_full_window and len(raw_values) < window:
        return None
    if any(value is None for value in raw_values):
        return None
    return [float(value) for value in raw_values if value is not None]


def _invalid_reason(
    open_price: float | None,
    high: float | None,
    low: float | None,
    close: float | None,
    volume: float | None,
) -> str | None:
    if None in (open_price, high, low, close, volume):
        return "missing_ohlcv"
    if high is not None and low is not None and high < low:
        return "invalid_high_low"
    if close is not None and close <= 0:
        return "invalid_close"
    if volume is not None and volume < 0:
        return "invalid_volume"
    return None


def _invalid_row(base: dict[str, Any], trading_value: float | None, reason: str) -> dict[str, Any]:
    return {
        **base,
        "realized_volatility": None,
        "volatility_regime": RegimeVolatility.UNKNOWN.value,
        "trading_value": trading_value,
        "average_trading_value": None,
        "trading_value_percentile": None,
        "liquidity_zscore": None,
        "liquidity_regime": LiquidityRegime.UNKNOWN.value,
        "spread_proxy": None,
        "range_spread_proxy_percentile": None,
        "spread_regime": SpreadRegime.UNKNOWN.value,
        "wick_dominance_proxy": None,
        "session_tag": classify_utc_session(base["timestamp"]),
        "weekday_tag": classify_weekday_tag(base["timestamp"]),
        "trend_strength": None,
        "trend_regime": TrendRegime.UNKNOWN.value,
        "mean_reversion_zscore": None,
        "mean_reversion_regime": MeanReversionRegime.UNKNOWN.value,
        "market_regime": "UNKNOWN",
        "is_valid": False,
        "reason": reason,
    }


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric or numeric in (float("inf"), float("-inf")):
        return None
    return numeric
