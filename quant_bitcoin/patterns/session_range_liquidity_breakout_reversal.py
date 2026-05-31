"""Session-range liquidity breakout reversal pattern detection.

The detector consumes completed OHLCV candles that were supplied by the caller.
It does not fetch market data, read secrets, call exchange APIs, place orders,
or persist records. Events are deterministic and use only candles up to the
current confirmation candle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, calculate_atr
from quant_bitcoin.indicators.volume_ratio import (
    VolumeRatioBaselineMode,
    VolumeRatioConfig,
    calculate_volume_ratio,
)
from quant_bitcoin.patterns.score_metadata import build_score_metadata
from quant_bitcoin.risk.exit_plan import (
    BreakEvenSettings,
    RiskExitConfig,
    RiskExitPlan,
    TimeStopSettings,
    TrailingStopSettings,
    create_risk_exit_plan,
)

REQUIRED_SESSION_RANGE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

PATTERN_TYPE = "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL"


@dataclass(frozen=True)
class SessionRangeLiquidityBreakoutReversalConfig:
    range_lookback_bars: int = 120
    breakout_buffer_bps: float = 0.0
    minimum_range_bps: float = 10.0
    minimum_volume_ratio: float = 0.8
    minimum_body_ratio: float = 0.25
    signal_mode: str = "FAILED_BREAKOUT_REVERSAL"
    direction_mode: str = "BOTH"
    minimum_pattern_score: float = 0.40
    target_r_multiple: float = 4.0
    stop_atr_buffer_multiplier: float = 0.20
    max_bars_in_trade: int = 240
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None

    def __post_init__(self) -> None:
        if self.range_lookback_bars < 2:
            raise ValueError("range_lookback_bars must be at least 2")
        if self.breakout_buffer_bps < 0:
            raise ValueError("breakout_buffer_bps must be non-negative")
        if self.minimum_range_bps < 0:
            raise ValueError("minimum_range_bps must be non-negative")
        if self.minimum_volume_ratio < 0:
            raise ValueError("minimum_volume_ratio must be non-negative")
        if not 0 <= self.minimum_body_ratio <= 1:
            raise ValueError("minimum_body_ratio must be between 0 and 1")
        if not 0 <= self.minimum_pattern_score <= 1:
            raise ValueError("minimum_pattern_score must be between 0 and 1")
        if self.target_r_multiple <= 0:
            raise ValueError("target_r_multiple must be positive")
        if self.stop_atr_buffer_multiplier < 0:
            raise ValueError("stop_atr_buffer_multiplier must be non-negative")
        if self.max_bars_in_trade < 1:
            raise ValueError("max_bars_in_trade must be at least 1")
        _coerce_signal_mode(self.signal_mode)
        _coerce_direction_mode(self.direction_mode)
        if self.atr_config is None:
            object.__setattr__(self, "atr_config", AtrConfig(period=14, require_full_window=True))
        if self.volume_ratio_config is None:
            object.__setattr__(
                self,
                "volume_ratio_config",
                VolumeRatioConfig(
                    window=20,
                    minimum_volume_ratio_for_confirmation=self.minimum_volume_ratio,
                    high_volume_ratio_threshold=max(2.0, self.minimum_volume_ratio),
                    require_full_window=True,
                    baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
                ),
            )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "session_range_liquidity_breakout_reversal_config_v1",
            "enabled": True,
            "range_lookback_bars": int(self.range_lookback_bars),
            "breakout_buffer_bps": float(self.breakout_buffer_bps),
            "minimum_range_bps": float(self.minimum_range_bps),
            "minimum_volume_ratio": float(self.minimum_volume_ratio),
            "minimum_body_ratio": float(self.minimum_body_ratio),
            "signal_mode": _coerce_signal_mode(self.signal_mode),
            "direction_mode": _coerce_direction_mode(self.direction_mode),
            "minimum_pattern_score": float(self.minimum_pattern_score),
            "target_r_multiple": float(self.target_r_multiple),
            "stop_atr_buffer_multiplier": float(self.stop_atr_buffer_multiplier),
            "max_bars_in_trade": int(self.max_bars_in_trade),
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class SessionRangeLiquidityBreakoutReversalEvent:
    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    range_start_index: int
    range_end_index: int
    range_high: float
    range_low: float
    range_mid: float
    range_size_bps: float
    breakout_side: str
    signal_mode: str
    volume_ratio: float
    body_ratio: float
    atr: float
    breakout_distance_bps: float
    entry_reference: float
    stop_reference: float
    target_reference: float
    risk_reward: float
    pattern_score: float
    executable_pattern_score: float
    diagnostic_pattern_score: float
    score_components: dict[str, Any] = field(default_factory=dict)
    score_component_sources: dict[str, str] = field(default_factory=dict)
    score_limitations: tuple[str, ...] = ()
    score_calibration: dict[str, Any] = field(default_factory=dict)
    atr_metadata: dict[str, Any] = field(default_factory=dict)
    reason: str = "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL_CONFIRMED"
    zone_low: float | None = None
    zone_high: float | None = None
    zone_mid: float | None = None
    target_source: str = "FIXED_R_MULTIPLE"
    entry_source: str = "CONFIRMATION_CLOSE"


def detect_session_range_liquidity_breakout_reversals(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
) -> list[SessionRangeLiquidityBreakoutReversalEvent]:
    cfg = config or SessionRangeLiquidityBreakoutReversalConfig()
    frame = _enriched_candles(_normalize_candles(candles, symbol), cfg)
    events: list[SessionRangeLiquidityBreakoutReversalEvent] = []
    for index in range(len(frame)):
        event = evaluate_session_range_liquidity_breakout_reversal_at_index(
            frame,
            index,
            symbol=symbol,
            timeframe=timeframe,
            config=cfg,
            already_enriched=True,
        )
        if event is not None:
            events.append(event)
    return events


def detect_session_range_liquidity_breakout_reversals_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
) -> list[SessionRangeLiquidityBreakoutReversalEvent]:
    event = evaluate_session_range_liquidity_breakout_reversal_at_index(
        candles,
        current_index,
        symbol=symbol,
        timeframe=timeframe,
        config=config,
    )
    return [] if event is None else [event]


def evaluate_session_range_liquidity_breakout_reversal_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
    already_enriched: bool = False,
) -> SessionRangeLiquidityBreakoutReversalEvent | None:
    cfg = config or SessionRangeLiquidityBreakoutReversalConfig()
    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    frame = frame.reset_index(drop=True)
    if not already_enriched:
        frame = _enriched_candles(_normalize_candles(frame, symbol), cfg)
    if current_index < cfg.range_lookback_bars or current_index >= len(frame):
        return None

    row = frame.iloc[current_index]
    prior = frame.iloc[current_index - cfg.range_lookback_bars : current_index]
    entry = _positive_float(row["close"])
    current_atr = _positive_float(row.get("atr"))
    volume_ratio = _positive_float(row.get("volume_ratio"))
    if entry is None or current_atr is None or volume_ratio is None:
        return None

    range_high = float(prior["high"].max())
    range_low = float(prior["low"].min())
    if range_high <= range_low:
        return None
    range_mid = (range_high + range_low) / 2.0
    range_size_bps = ((range_high - range_low) / entry) * 10_000.0
    if range_size_bps < cfg.minimum_range_bps:
        return None

    high = float(row["high"])
    low = float(row["low"])
    open_price = float(row["open"])
    close = float(row["close"])
    body_ratio = _body_ratio(row)
    if volume_ratio < cfg.minimum_volume_ratio or body_ratio < cfg.minimum_body_ratio:
        return None

    signal_mode = _coerce_signal_mode(cfg.signal_mode)
    direction_mode = _coerce_direction_mode(cfg.direction_mode)
    buffer = cfg.breakout_buffer_bps / 10_000.0
    signal = _select_signal(
        row=row,
        range_high=range_high,
        range_low=range_low,
        buffer=buffer,
        signal_mode=signal_mode,
        direction_mode=direction_mode,
    )
    if signal is None:
        return None

    direction, breakout_side = signal
    if direction == "BEARISH":
        stop_reference = max(high, range_high)
        risk = stop_reference - close
        target_reference = close - cfg.target_r_multiple * risk
        breakout_distance_bps = ((high - range_high) / close) * 10_000.0 if breakout_side == "UPSIDE_FAILURE" else ((range_low - close) / close) * 10_000.0
    else:
        stop_reference = min(low, range_low)
        risk = close - stop_reference
        target_reference = close + cfg.target_r_multiple * risk
        breakout_distance_bps = ((range_low - low) / close) * 10_000.0
    if risk <= 0 or target_reference <= 0:
        return None

    score = _score_metadata(
        volume_ratio=volume_ratio,
        body_ratio=body_ratio,
        range_size_bps=range_size_bps,
        breakout_distance_bps=breakout_distance_bps,
        config=cfg,
    )
    pattern_score = float(score["pattern_score"])
    if pattern_score < cfg.minimum_pattern_score:
        return None

    resolved_symbol = symbol or str(frame.iloc[0].get("symbol", "UNKNOWN"))
    event_id = _build_event_id(
        direction=direction,
        symbol=resolved_symbol,
        timeframe=timeframe,
        timestamp=row["timestamp"],
        range_start_timestamp=prior.iloc[0]["timestamp"],
        range_end_timestamp=prior.iloc[-1]["timestamp"],
        signal_mode=signal_mode,
    )
    return SessionRangeLiquidityBreakoutReversalEvent(
        event_id=event_id,
        pattern_type=PATTERN_TYPE,
        direction=direction,
        pattern_status="VALID",
        symbol=resolved_symbol,
        timeframe=timeframe,
        timestamp=row["timestamp"],
        start_index=current_index - cfg.range_lookback_bars,
        end_index=current_index,
        range_start_index=current_index - cfg.range_lookback_bars,
        range_end_index=current_index - 1,
        range_high=range_high,
        range_low=range_low,
        range_mid=range_mid,
        range_size_bps=range_size_bps,
        breakout_side=breakout_side,
        signal_mode=signal_mode,
        volume_ratio=volume_ratio,
        body_ratio=body_ratio,
        atr=current_atr,
        breakout_distance_bps=breakout_distance_bps,
        entry_reference=entry,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=float(cfg.target_r_multiple),
        pattern_score=pattern_score,
        executable_pattern_score=float(score["executable_pattern_score"]),
        diagnostic_pattern_score=float(score["diagnostic_pattern_score"]),
        score_components=score["score_components"],
        score_component_sources=score["score_component_sources"],
        score_limitations=tuple(score["score_limitations"]),
        score_calibration=score["score_calibration"],
        atr_metadata={
            "atr": current_atr,
            "atr_buffer_multiplier": float(cfg.stop_atr_buffer_multiplier),
            "target_r_multiple": float(cfg.target_r_multiple),
        },
        zone_low=range_low,
        zone_high=range_high,
        zone_mid=range_mid,
    )


def create_session_range_liquidity_breakout_reversal_risk_exit_plan(
    event: SessionRangeLiquidityBreakoutReversalEvent,
    *,
    config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
) -> RiskExitPlan:
    cfg = config or SessionRangeLiquidityBreakoutReversalConfig()
    risk_config = RiskExitConfig(
        atr_buffer_multiplier=float(cfg.stop_atr_buffer_multiplier),
        r_multiples=(float(cfg.target_r_multiple),),
        minimum_first_target_r=0.1,
        time_stop=TimeStopSettings(max_bars_in_trade=int(cfg.max_bars_in_trade)),
        break_even=BreakEvenSettings(enabled=False),
        trailing_stop=TrailingStopSettings(enabled=False),
        partial_exits=(),
    )
    return create_risk_exit_plan(
        direction="SHORT" if event.direction == "BEARISH" else "LONG",
        entry_price=event.entry_reference,
        structural_stop=event.stop_reference,
        atr=event.atr,
        config=risk_config,
        detector_target_reference=event.target_reference,
        atr_metadata=event.atr_metadata,
    )


def _select_signal(
    *,
    row: pd.Series,
    range_high: float,
    range_low: float,
    buffer: float,
    signal_mode: str,
    direction_mode: str,
) -> tuple[str, str] | None:
    open_price = float(row["open"])
    high = float(row["high"])
    low = float(row["low"])
    close = float(row["close"])
    allow_short = direction_mode in {"BOTH", "SHORT_ONLY"}
    allow_long = direction_mode in {"BOTH", "LONG_ONLY"}
    upside_failed = high > range_high * (1.0 + buffer) and close < range_high and close < open_price
    downside_failed = low < range_low * (1.0 - buffer) and close > range_low and close > open_price
    downside_breakdown = close < range_low * (1.0 - buffer) and close < open_price

    if signal_mode in {"FAILED_BREAKOUT_REVERSAL", "SHORT_MIX"} and allow_short and upside_failed:
        return "BEARISH", "UPSIDE_FAILURE"
    if signal_mode == "FAILED_BREAKOUT_REVERSAL" and allow_long and downside_failed:
        return "BULLISH", "DOWNSIDE_FAILURE"
    if signal_mode in {"BREAKDOWN_CONTINUATION", "SHORT_MIX"} and allow_short and downside_breakdown:
        return "BEARISH", "DOWNSIDE_BREAKDOWN"
    return None


def _enriched_candles(
    frame: pd.DataFrame,
    config: SessionRangeLiquidityBreakoutReversalConfig,
) -> pd.DataFrame:
    enriched = frame.copy(deep=True)
    if "atr" not in enriched.columns:
        atr = calculate_atr(
            enriched[["symbol", "timestamp", "high", "low", "close"]],
            config.atr_config,
        )
        enriched["atr"] = atr["atr"]
    if "volume_ratio" not in enriched.columns:
        ratios = calculate_volume_ratio(
            enriched[["symbol", "timestamp", "volume"]],
            config.volume_ratio_config,
        )
        enriched["volume_ratio"] = ratios["volume_ratio"]
    return enriched


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    symbol: str | None,
) -> pd.DataFrame:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    missing = [column for column in REQUIRED_SESSION_RANGE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing candle columns: {missing}")
    frame = frame.copy(deep=True).reset_index(drop=True)
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")
    if "symbol" not in frame.columns:
        frame["symbol"] = symbol or "UNKNOWN"
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame


def _score_metadata(
    *,
    volume_ratio: float,
    body_ratio: float,
    range_size_bps: float,
    breakout_distance_bps: float,
    config: SessionRangeLiquidityBreakoutReversalConfig,
) -> dict[str, Any]:
    return build_score_metadata(
        PATTERN_TYPE,
        [
            {
                "name": "range_definition",
                "raw_score": min(range_size_bps / max(config.minimum_range_bps * 4.0, 1.0), 1.0),
                "weight": 0.25,
                "source": "prior_completed_range",
                "description": "Prior completed range is large enough to define actionable liquidity.",
            },
            {
                "name": "breakout_distance",
                "raw_score": min(max(breakout_distance_bps, 0.0) / 20.0, 1.0),
                "weight": 0.25,
                "source": "confirmation_candle_breakout_distance",
                "description": "Distance beyond the prior range before failure or continuation.",
            },
            {
                "name": "candle_body",
                "raw_score": body_ratio,
                "weight": 0.25,
                "source": "confirmation_candle_body_ratio",
                "description": "Directional close quality on the confirmation candle.",
            },
            {
                "name": "volume_confirmation",
                "raw_score": min(volume_ratio / max(config.minimum_volume_ratio * 2.0, 1.0), 1.0),
                "weight": 0.25,
                "source": "prior_only_volume_ratio",
                "description": "Relative volume on the confirmation candle.",
            },
        ],
    )


def _body_ratio(row: pd.Series) -> float:
    high = float(row["high"])
    low = float(row["low"])
    if high <= low:
        return 0.0
    return abs(float(row["close"]) - float(row["open"])) / (high - low)


def _positive_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(numeric) or numeric <= 0:
        return None
    return numeric


def _coerce_signal_mode(value: str) -> str:
    normalized = str(value).upper()
    if normalized not in {"FAILED_BREAKOUT_REVERSAL", "BREAKDOWN_CONTINUATION", "SHORT_MIX"}:
        raise ValueError("signal_mode must be FAILED_BREAKOUT_REVERSAL, BREAKDOWN_CONTINUATION, or SHORT_MIX")
    return normalized


def _coerce_direction_mode(value: str) -> str:
    normalized = str(value).upper()
    if normalized not in {"BOTH", "LONG_ONLY", "SHORT_ONLY"}:
        raise ValueError("direction_mode must be BOTH, LONG_ONLY, or SHORT_ONLY")
    return normalized


def _build_event_id(
    *,
    direction: str,
    symbol: str | None,
    timeframe: str | None,
    timestamp: Any,
    range_start_timestamp: Any,
    range_end_timestamp: Any,
    signal_mode: str,
) -> str:
    raw = "|".join(
        [
            PATTERN_TYPE,
            direction,
            str(symbol or ""),
            str(timeframe or ""),
            str(timestamp),
            str(range_start_timestamp),
            str(range_end_timestamp),
            signal_mode,
        ]
    )
    return "SRLBR-" + sha256(raw.encode("utf-8")).hexdigest()[:20]
