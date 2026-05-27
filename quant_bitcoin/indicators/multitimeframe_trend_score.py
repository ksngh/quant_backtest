"""Composite EMA trend score across completed candle timeframes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd

from quant_bitcoin.indicators.ema import EmaTrendConfig, calculate_ema_trend_features, ema_timing_metadata


TREND_SCORE_SCHEMA_VERSION = "multitimeframe_trend_score_v1"
DEFAULT_TREND_SCORE_WEIGHTS: dict[str, float] = {"1m": 0.20, "5m": 0.30, "15m": 0.50}


@dataclass(frozen=True)
class MultiTimeframeTrendScoreConfig:
    """Configuration for bounded EMA trend agreement scoring."""

    timeframes: tuple[str, ...] = ("1m", "5m", "15m")
    source_timeframe: str = "1m"
    weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_TREND_SCORE_WEIGHTS))
    ema_config: EmaTrendConfig = field(default_factory=EmaTrendConfig)
    neutral_threshold: float = 0.05

    def __post_init__(self) -> None:
        if not self.timeframes:
            raise ValueError("timeframes must include at least one timeframe")
        if self.source_timeframe not in self.timeframes:
            raise ValueError("source_timeframe must be included in timeframes")
        if self.neutral_threshold < 0:
            raise ValueError("neutral_threshold must be non-negative")
        total = 0.0
        for timeframe in self.timeframes:
            weight = float(self.weights.get(timeframe, 0.0))
            if weight < 0:
                raise ValueError("timeframe weights must be non-negative")
            total += weight
        if total <= 0:
            raise ValueError("at least one configured timeframe weight must be positive")


def calculate_multitimeframe_trend_score(
    candles: pd.DataFrame,
    *,
    higher_timeframe_candles: Mapping[str, pd.DataFrame] | None = None,
    config: MultiTimeframeTrendScoreConfig | None = None,
) -> pd.DataFrame:
    """Return one trend-score row per base candle.

    ``candles`` is the base timeframe frame. Higher timeframe rows must be
    completed candles, usually from Task 226 aggregation. Missing higher
    timeframe context is recorded per row instead of being treated as neutral
    agreement.
    """

    cfg = config or MultiTimeframeTrendScoreConfig()
    _validate_base_candles(candles)
    base = candles.copy().reset_index(drop=True)
    base["timestamp"] = pd.to_datetime(base["timestamp"], errors="raise", utc=True, format="mixed")
    higher = higher_timeframe_candles or {}

    features_by_timeframe = {
        cfg.source_timeframe: _base_timeframe_features(base, cfg),
    }
    for timeframe in cfg.timeframes:
        if timeframe == cfg.source_timeframe:
            continue
        frame = _higher_timeframe_source(base, higher, timeframe)
        features_by_timeframe[timeframe] = _higher_timeframe_features(frame, cfg)

    rows: list[dict[str, Any]] = []
    for _, candle in base.iterrows():
        timestamp = candle["timestamp"]
        components: dict[str, dict[str, Any]] = {}
        weighted_sum = 0.0
        available_weight = 0.0
        configured_weight = 0.0
        missing_timeframes: list[str] = []

        for timeframe in cfg.timeframes:
            weight = float(cfg.weights.get(timeframe, 0.0))
            configured_weight += weight
            component = _component_for_timestamp(
                features_by_timeframe[timeframe],
                timestamp,
                timeframe,
                weight,
                cfg,
            )
            components[timeframe] = component
            if component["is_available"] and component["score"] is not None and weight > 0:
                weighted_sum += float(component["score"]) * weight
                available_weight += weight
            elif not component["is_available"]:
                missing_timeframes.append(timeframe)

        trend_score = None
        trend_direction = "UNAVAILABLE"
        if available_weight > 0:
            trend_score = max(-1.0, min(1.0, weighted_sum / available_weight))
            trend_direction = _direction(trend_score, cfg.neutral_threshold)

        metadata = {
            "schema_version": TREND_SCORE_SCHEMA_VERSION,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "source_timeframe": cfg.source_timeframe,
            "timeframes": list(cfg.timeframes),
            "configured_weight": configured_weight,
            "available_weight": available_weight,
            "missing_timeframes": missing_timeframes,
            "components": components,
            "timing": multitimeframe_trend_score_timing_metadata(cfg),
            "diagnostic_only": True,
        }
        rows.append(
            {
                "timestamp": timestamp,
                "trend_score": trend_score,
                "trend_direction": trend_direction,
                "available_weight": available_weight,
                "configured_weight": configured_weight,
                "missing_timeframes": tuple(missing_timeframes),
                "trend_score_metadata": metadata,
            }
        )

    return pd.DataFrame(rows)


def multitimeframe_trend_score_timing_metadata(
    config: MultiTimeframeTrendScoreConfig | None = None,
) -> dict[str, Any]:
    """Return timing metadata for composite trend scoring."""

    cfg = config or MultiTimeframeTrendScoreConfig()
    return {
        "schema_version": "indicator_timing_metadata_v1",
        "indicator": "multitimeframe_trend_score",
        "current_candle_included": True,
        "requires_closed_candle": True,
        "warmup_period": cfg.ema_config.warmup_period,
        "confirmation_delay": 0,
        "baseline_mode": "uses completed base candle and latest completed higher-timeframe candles",
        "safe_usage": "diagnostic-only after candle close; not an auto-trading signal",
        "higher_timeframe_availability_caveat": (
            "higher-timeframe components are unavailable until each derived candle close_time "
            "is less than or equal to the base timestamp"
        ),
        "ema_timing": ema_timing_metadata(cfg.ema_config),
    }


def _base_timeframe_features(base: pd.DataFrame, cfg: MultiTimeframeTrendScoreConfig) -> pd.DataFrame:
    columns = ["timestamp", "close"]
    if "symbol" in base.columns:
        columns.insert(0, "symbol")
    features = calculate_ema_trend_features(base.loc[:, columns], cfg.ema_config)
    features["available_from"] = features["timestamp"]
    return features


def _higher_timeframe_features(frame: pd.DataFrame, cfg: MultiTimeframeTrendScoreConfig) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    source = frame.rename(columns={"close_time": "timestamp"}).copy()
    if "symbol" not in source.columns:
        source["symbol"] = None
    features = calculate_ema_trend_features(source.loc[:, ["symbol", "timestamp", "close"]], cfg.ema_config)
    features["available_from"] = pd.to_datetime(frame["close_time"], errors="raise", utc=True, format="mixed").reset_index(drop=True)
    return features


def _higher_timeframe_source(
    base: pd.DataFrame,
    higher: Mapping[str, pd.DataFrame],
    timeframe: str,
) -> pd.DataFrame:
    if timeframe in higher:
        return _normalize_higher_frame(higher[timeframe])

    prefix = f"mtf_{timeframe}_"
    required = [f"{prefix}available", f"{prefix}open_time", f"{prefix}close_time", f"{prefix}close"]
    if not all(column in base.columns for column in required):
        return pd.DataFrame()
    available = base[base[f"{prefix}available"]].loc[:, required].drop_duplicates(
        subset=[f"{prefix}open_time"]
    )
    if available.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        {
            "open_time": available[f"{prefix}open_time"],
            "close_time": available[f"{prefix}close_time"],
            "close": available[f"{prefix}close"],
        }
    ).reset_index(drop=True)


def _normalize_higher_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("higher timeframe candles must be pandas DataFrames")
    if frame.empty:
        return pd.DataFrame()
    missing = [column for column in ("open_time", "close_time", "close") if column not in frame.columns]
    if missing:
        raise ValueError(f"higher timeframe candles missing required columns: {', '.join(missing)}")
    normalized = frame.loc[:, [column for column in ("symbol", "open_time", "close_time", "close") if column in frame.columns]].copy()
    normalized["open_time"] = pd.to_datetime(normalized["open_time"], errors="raise", utc=True, format="mixed")
    normalized["close_time"] = pd.to_datetime(normalized["close_time"], errors="raise", utc=True, format="mixed")
    normalized["close"] = pd.to_numeric(normalized["close"], errors="raise")
    if not normalized["close_time"].is_monotonic_increasing:
        raise ValueError("higher timeframe candles must be sorted ascending by close_time")
    return normalized.reset_index(drop=True)


def _component_for_timestamp(
    features: pd.DataFrame,
    timestamp: pd.Timestamp,
    timeframe: str,
    weight: float,
    cfg: MultiTimeframeTrendScoreConfig,
) -> dict[str, Any]:
    if features.empty:
        return _missing_component(timeframe, weight, "MISSING_TIMEFRAME_CONTEXT")
    visible = features[features["available_from"] <= timestamp]
    if visible.empty:
        return _missing_component(timeframe, weight, "NO_COMPLETED_TIMEFRAME_CANDLE")
    row = visible.iloc[-1]
    if not bool(row["is_valid"]):
        return _missing_component(timeframe, weight, str(row["reason"] or "WARMUP"))

    sub_scores = {
        "close_vs_ema": _sign(row["close_vs_ema_slow"]),
        "fast_vs_slow": _sign(row["fast_vs_slow"]),
        "fast_ema_slope": _sign(row["ema_fast_slope"]),
    }
    if cfg.ema_config.include_slow_slope:
        sub_scores["slow_ema_slope"] = _sign(row["ema_slow_slope"])
    score = sum(sub_scores.values()) / len(sub_scores)
    return {
        "timeframe": timeframe,
        "weight": weight,
        "score": max(-1.0, min(1.0, score)),
        "direction": _direction(score, cfg.neutral_threshold),
        "is_available": True,
        "missing_reason": None,
        "feature_timestamp": row["timestamp"].isoformat().replace("+00:00", "Z"),
        "components": sub_scores,
        "ema_fast": float(row["ema_fast"]),
        "ema_slow": float(row["ema_slow"]),
        "close": float(row["close"]),
    }


def _missing_component(timeframe: str, weight: float, reason: str) -> dict[str, Any]:
    return {
        "timeframe": timeframe,
        "weight": weight,
        "score": None,
        "direction": "UNAVAILABLE",
        "is_available": False,
        "missing_reason": reason,
        "feature_timestamp": None,
        "components": {},
    }


def _direction(score: float, threshold: float) -> str:
    if score > threshold:
        return "BULLISH"
    if score < -threshold:
        return "BEARISH"
    return "NEUTRAL"


def _sign(value: Any) -> int:
    if value is None or pd.isna(value):
        return 0
    numeric = float(value)
    if numeric > 0:
        return 1
    if numeric < 0:
        return -1
    return 0


def _validate_base_candles(candles: pd.DataFrame) -> None:
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("trend-score candles must be a pandas DataFrame")
    missing = [column for column in ("timestamp", "close") if column not in candles.columns]
    if missing:
        raise ValueError(f"trend-score candles missing required columns: {', '.join(missing)}")
    if candles.empty:
        return
    timestamps = pd.to_datetime(candles["timestamp"], errors="raise", utc=True, format="mixed")
    if timestamps.duplicated().any():
        raise ValueError("trend-score candles contain duplicate timestamp")
    if not pd.Series(timestamps).is_monotonic_increasing:
        raise ValueError("trend-score candles must be sorted ascending by timestamp")
    pd.to_numeric(candles["close"], errors="raise")
