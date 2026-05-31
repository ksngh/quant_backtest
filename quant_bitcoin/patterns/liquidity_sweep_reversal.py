"""Liquidity sweep reversal pattern detection.

This module consumes already-provided completed OHLCV candles and emits
deterministic liquidity sweep reversal events. It is offline-only research
code: it does not fetch market data, read secrets, call exchange APIs, place
orders, persist records, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, atr_timing_metadata, calculate_atr
from quant_bitcoin.indicators.displacement_candle import (
    DisplacementCandleConfig,
    detect_displacement_candles,
)
from quant_bitcoin.indicators.volume_ratio import (
    VolumeRatioBaselineMode,
    VolumeRatioConfig,
    calculate_volume_ratio,
)

REQUIRED_LIQUIDITY_SWEEP_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class LiquiditySweepDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class LiquiditySweepStatus(Enum):
    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"


class LiquiditySweepEntryMode(Enum):
    MARKET_ON_RECLAIM_CLOSE = "MARKET_ON_RECLAIM_CLOSE"
    MARKET_ON_DISPLACEMENT_CLOSE = "MARKET_ON_DISPLACEMENT_CLOSE"
    LIMIT_AT_FVG_MIDPOINT = "LIMIT_AT_FVG_MIDPOINT"
    LIMIT_AT_OB_618 = "LIMIT_AT_OB_618"
    BEST_NET_RR_BETWEEN_FVG_MIDPOINT_AND_OB_618 = (
        "BEST_NET_RR_BETWEEN_FVG_MIDPOINT_AND_OB_618"
    )


@dataclass(frozen=True)
class LiquiditySweepReversalConfig:
    liquidity_pool_lookback_bars: int = 80
    min_liquidity_pool_age_bars: int = 5
    min_sweep_atr_multiplier: float = 0.05
    min_sweep_bps: float = 2.0
    reclaim_max_bars: int = 2
    displacement_max_bars_after_sweep: int = 3
    minimum_displacement_body_ratio: float = 0.55
    minimum_displacement_atr_multiplier: float = 0.8
    minimum_volume_ratio: float = 1.5
    minimum_pattern_score: float = 0.70
    require_fvg_confluence: bool = False
    require_order_block_confluence: bool = False
    require_both_fvg_and_ob: bool = False
    entry_mode: LiquiditySweepEntryMode | str = (
        LiquiditySweepEntryMode.BEST_NET_RR_BETWEEN_FVG_MIDPOINT_AND_OB_618
    )
    target_r_multiple: float = 2.0
    min_gross_rr: float = 1.2
    min_net_rr: float = 1.0
    min_net_reward_bps: float = 8.0
    enable_tradability_gates: bool = False
    enable_mtf_confirmation: bool = False
    mtf_timeframes: tuple[str, ...] = ("15m",)
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None
    displacement_config: DisplacementCandleConfig | None = None

    def __post_init__(self) -> None:
        if self.liquidity_pool_lookback_bars < 2:
            raise ValueError("liquidity_pool_lookback_bars must be at least 2")
        if self.min_liquidity_pool_age_bars < 1:
            raise ValueError("min_liquidity_pool_age_bars must be at least 1")
        if self.min_sweep_atr_multiplier < 0:
            raise ValueError("min_sweep_atr_multiplier must be non-negative")
        if self.min_sweep_bps < 0:
            raise ValueError("min_sweep_bps must be non-negative")
        if self.reclaim_max_bars < 0:
            raise ValueError("reclaim_max_bars must be non-negative")
        if self.displacement_max_bars_after_sweep < 0:
            raise ValueError("displacement_max_bars_after_sweep must be non-negative")
        if not 0 <= self.minimum_displacement_body_ratio <= 1:
            raise ValueError("minimum_displacement_body_ratio must be between 0 and 1")
        if self.minimum_displacement_atr_multiplier < 0:
            raise ValueError("minimum_displacement_atr_multiplier must be non-negative")
        if self.minimum_volume_ratio < 0:
            raise ValueError("minimum_volume_ratio must be non-negative")
        if not 0 <= self.minimum_pattern_score <= 1:
            raise ValueError("minimum_pattern_score must be between 0 and 1")
        if self.target_r_multiple <= 0:
            raise ValueError("target_r_multiple must be positive")
        if self.min_gross_rr < 0:
            raise ValueError("min_gross_rr must be non-negative")
        if self.min_net_rr < 0:
            raise ValueError("min_net_rr must be non-negative")
        if self.min_net_reward_bps < 0:
            raise ValueError("min_net_reward_bps must be non-negative")
        _coerce_entry_mode(self.entry_mode)
        if self.atr_config is None:
            object.__setattr__(self, "atr_config", AtrConfig())
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
        if self.displacement_config is None:
            object.__setattr__(
                self,
                "displacement_config",
                DisplacementCandleConfig(
                    minimum_body_ratio=self.minimum_displacement_body_ratio,
                    minimum_range_atr_multiplier=self.minimum_displacement_atr_multiplier,
                    minimum_volume_ratio=self.minimum_volume_ratio,
                    minimum_close_position_ratio=0.65,
                ),
            )
        object.__setattr__(
            self,
            "mtf_timeframes",
            tuple(str(value).strip() for value in self.mtf_timeframes if str(value).strip()),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity_sweep_reversal_config_v1",
            "liquidity_pool_lookback_bars": int(self.liquidity_pool_lookback_bars),
            "min_liquidity_pool_age_bars": int(self.min_liquidity_pool_age_bars),
            "min_sweep_atr_multiplier": float(self.min_sweep_atr_multiplier),
            "min_sweep_bps": float(self.min_sweep_bps),
            "reclaim_max_bars": int(self.reclaim_max_bars),
            "displacement_max_bars_after_sweep": int(
                self.displacement_max_bars_after_sweep
            ),
            "minimum_displacement_body_ratio": float(
                self.minimum_displacement_body_ratio
            ),
            "minimum_displacement_atr_multiplier": float(
                self.minimum_displacement_atr_multiplier
            ),
            "minimum_volume_ratio": float(self.minimum_volume_ratio),
            "minimum_pattern_score": float(self.minimum_pattern_score),
            "require_fvg_confluence": bool(self.require_fvg_confluence),
            "require_order_block_confluence": bool(self.require_order_block_confluence),
            "require_both_fvg_and_ob": bool(self.require_both_fvg_and_ob),
            "entry_mode": _coerce_entry_mode(self.entry_mode).value,
            "target_r_multiple": float(self.target_r_multiple),
            "min_gross_rr": float(self.min_gross_rr),
            "min_net_rr": float(self.min_net_rr),
            "min_net_reward_bps": float(self.min_net_reward_bps),
            "enable_tradability_gates": bool(self.enable_tradability_gates),
            "enable_mtf_confirmation": bool(self.enable_mtf_confirmation),
            "mtf_timeframes": tuple(self.mtf_timeframes),
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class LiquiditySweepReversalEvent:
    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    liquidity_pool_index: int
    liquidity_pool_timestamp: Any
    liquidity_pool_price: float
    liquidity_pool_source: str
    sweep_candle_index: int
    sweep_candle_timestamp: Any
    sweep_extreme_price: float
    sweep_distance: float
    sweep_distance_atr: float | None
    sweep_distance_bps: float
    reclaim_candle_index: int
    reclaim_candle_timestamp: Any
    reclaim_close: float
    reclaim_lag_bars: int
    displacement_candle_index: int
    displacement_direction: str
    displacement_range_atr: float | None
    displacement_body_ratio: float | None
    volume_ratio: float | None
    fvg_confluence_pass: bool
    fvg_event_id: str | None
    fvg_zone_low: float | None
    fvg_zone_high: float | None
    order_block_confluence_pass: bool
    order_block_event_id: str | None
    order_block_zone_low: float | None
    order_block_zone_high: float | None
    entry_reference: float
    stop_reference: float
    target_reference: float
    risk_reward: float | None
    pattern_score: float
    score_components: dict[str, Any] = field(default_factory=dict)
    score_component_sources: dict[str, str] = field(default_factory=dict)
    score_limitations: tuple[str, ...] = ()
    score_calibration: dict[str, Any] = field(default_factory=dict)
    atr_metadata: dict[str, Any] = field(default_factory=dict)
    regime_metadata: dict[str, Any] = field(default_factory=dict)
    mtf_metadata: dict[str, Any] = field(default_factory=dict)
    reason: str = "LIQUIDITY_SWEEP_RECLAIM_DISPLACEMENT_CONFLUENCE"
    zone_low: float | None = None
    zone_high: float | None = None
    zone_mid: float | None = None
    target_source: str = "FIXED_R_MULTIPLE"
    entry_source: str = "ENTRY_REFERENCE"
    executable_pattern_score: float | None = None
    diagnostic_pattern_score: float | None = None


def detect_liquidity_sweep_reversals(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: LiquiditySweepReversalConfig | None = None,
) -> list[LiquiditySweepReversalEvent]:
    cfg = config or LiquiditySweepReversalConfig()
    frame = _normalize_candles(candles, symbol)
    if frame.empty:
        return []
    enriched, displacement_rows = _indicator_frames(frame, cfg)
    events: list[LiquiditySweepReversalEvent] = []
    resolved_symbol = symbol or str(enriched.iloc[0]["symbol"])
    for current_index in range(len(enriched)):
        events.extend(
            evaluate_liquidity_sweep_reversal_at_index(
                enriched,
                displacement_rows,
                current_index,
                symbol=resolved_symbol,
                timeframe=timeframe,
                config=cfg,
            )
        )
    return events


def detect_liquidity_sweep_reversals_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: LiquiditySweepReversalConfig | None = None,
) -> list[LiquiditySweepReversalEvent]:
    cfg = config or LiquiditySweepReversalConfig()
    frame = _normalize_candles(candles, symbol)
    if current_index < 0 or current_index >= len(frame):
        return []
    enriched, displacement_rows = _indicator_frames(frame.iloc[: current_index + 1], cfg)
    return evaluate_liquidity_sweep_reversal_at_index(
        enriched,
        displacement_rows,
        current_index,
        symbol=symbol or (str(enriched.iloc[0]["symbol"]) if not enriched.empty else None),
        timeframe=timeframe,
        config=cfg,
    )


def evaluate_liquidity_sweep_reversal_at_index(
    enriched_candles: pd.DataFrame,
    displacement_rows: pd.DataFrame,
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: LiquiditySweepReversalConfig | None = None,
) -> list[LiquiditySweepReversalEvent]:
    cfg = config or LiquiditySweepReversalConfig()
    if current_index < 1 or current_index >= len(enriched_candles):
        return []
    row = enriched_candles.iloc[current_index]
    displacement = displacement_rows.iloc[current_index]
    if not bool(displacement.get("is_displacement")):
        return []
    displacement_direction = str(displacement.get("displacement_direction", "")).upper()
    if displacement_direction not in {"BULLISH", "BEARISH"}:
        return []

    direction = (
        LiquiditySweepDirection.BULLISH
        if displacement_direction == "BULLISH"
        else LiquiditySweepDirection.BEARISH
    )
    sweep_candidates = _candidate_sweep_indices(current_index, cfg)
    events: list[LiquiditySweepReversalEvent] = []
    for sweep_index in sweep_candidates:
        pool = _liquidity_pool(enriched_candles, sweep_index, direction, cfg)
        if pool is None:
            continue
        if not _sweep_passes(enriched_candles, sweep_index, pool, direction, cfg):
            continue
        reclaim = _reclaim_index(enriched_candles, sweep_index, current_index, pool, direction, cfg)
        if reclaim is None:
            continue
        if current_index - sweep_index > cfg.displacement_max_bars_after_sweep:
            continue
        confluence = _confluence(enriched_candles, current_index, direction)
        if not _confluence_passes(confluence, cfg):
            continue
        event = _build_event(
            enriched_candles,
            displacement,
            current_index,
            sweep_index,
            reclaim,
            pool,
            confluence,
            direction,
            symbol=symbol,
            timeframe=timeframe,
            config=cfg,
        )
        if event is not None:
            events.append(event)
    return events[:1]


def _indicator_frames(
    frame: pd.DataFrame,
    config: LiquiditySweepReversalConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    atr_rows = calculate_atr(
        frame[["symbol", "timestamp", "high", "low", "close"]],
        config.atr_config,
    )
    volume_rows = calculate_volume_ratio(
        frame[["symbol", "timestamp", "volume"]],
        config.volume_ratio_config,
    )
    enriched = frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]
    displacement_rows = detect_displacement_candles(
        enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
        config.displacement_config,
    )
    return enriched, displacement_rows


def _build_event(
    frame: pd.DataFrame,
    displacement: pd.Series,
    current_index: int,
    sweep_index: int,
    reclaim_index: int,
    pool: dict[str, Any],
    confluence: dict[str, Any],
    direction: LiquiditySweepDirection,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: LiquiditySweepReversalConfig,
) -> LiquiditySweepReversalEvent | None:
    current = frame.iloc[current_index]
    sweep = frame.iloc[sweep_index]
    atr = _optional_float(current.get("atr")) or _optional_float(sweep.get("atr"))
    volume_ratio = _optional_float(current.get("volume_ratio"))
    if volume_ratio is None or volume_ratio < config.minimum_volume_ratio:
        return None

    pool_price = float(pool["price"])
    sweep_extreme = float(sweep["low"] if direction is LiquiditySweepDirection.BULLISH else sweep["high"])
    sweep_distance = (
        pool_price - sweep_extreme
        if direction is LiquiditySweepDirection.BULLISH
        else sweep_extreme - pool_price
    )
    if sweep_distance <= 0:
        return None
    sweep_distance_atr = None if atr is None or atr <= 0 else sweep_distance / atr
    sweep_distance_bps = sweep_distance / pool_price * 10_000.0

    entry_reference, entry_source, zone = _entry_reference(confluence, direction, config)
    stop_reference = sweep_extreme
    target_reference, target_source = _target_reference(
        frame,
        current_index,
        entry_reference,
        stop_reference,
        direction,
        config,
    )
    risk_reward = _risk_reward(entry_reference, stop_reference, target_reference, direction)
    if risk_reward is None or risk_reward < config.min_gross_rr:
        return None

    score, components, sources = _score_components(
        sweep_distance_atr=sweep_distance_atr,
        sweep_distance_bps=sweep_distance_bps,
        reclaim_lag=current_index - reclaim_index,
        displacement=displacement,
        volume_ratio=volume_ratio,
        confluence=confluence,
    )
    status = (
        LiquiditySweepStatus.VALID
        if score >= config.minimum_pattern_score
        else LiquiditySweepStatus.WEAK
    )
    confluence_key = "FVG_OB" if confluence["fvg_pass"] and confluence["ob_pass"] else ("FVG" if confluence["fvg_pass"] else "OB")
    event_id = _event_id(
        symbol=symbol,
        timeframe=timeframe,
        direction=direction.value,
        pool_timestamp=pool["timestamp"],
        pool_price=pool_price,
        sweep_timestamp=sweep["timestamp"],
        sweep_extreme=sweep_extreme,
        confirmation_timestamp=current["timestamp"],
        confluence_key=confluence_key,
    )
    return LiquiditySweepReversalEvent(
        event_id=event_id,
        pattern_type="LIQUIDITY_SWEEP_REVERSAL",
        direction=direction.value,
        pattern_status=status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=current["timestamp"],
        start_index=int(pool["index"]),
        end_index=current_index,
        liquidity_pool_index=int(pool["index"]),
        liquidity_pool_timestamp=pool["timestamp"],
        liquidity_pool_price=pool_price,
        liquidity_pool_source="CONFIRMED_PRIOR_LOWEST_LOW"
        if direction is LiquiditySweepDirection.BULLISH
        else "CONFIRMED_PRIOR_HIGHEST_HIGH",
        sweep_candle_index=sweep_index,
        sweep_candle_timestamp=sweep["timestamp"],
        sweep_extreme_price=sweep_extreme,
        sweep_distance=sweep_distance,
        sweep_distance_atr=sweep_distance_atr,
        sweep_distance_bps=sweep_distance_bps,
        reclaim_candle_index=reclaim_index,
        reclaim_candle_timestamp=frame.iloc[reclaim_index]["timestamp"],
        reclaim_close=float(frame.iloc[reclaim_index]["close"]),
        reclaim_lag_bars=reclaim_index - sweep_index,
        displacement_candle_index=current_index,
        displacement_direction=direction.value,
        displacement_range_atr=_optional_float(displacement.get("candle_range")) / atr if atr and atr > 0 else None,
        displacement_body_ratio=_optional_float(displacement.get("body_ratio")),
        volume_ratio=volume_ratio,
        fvg_confluence_pass=bool(confluence["fvg_pass"]),
        fvg_event_id=confluence.get("fvg_event_id"),
        fvg_zone_low=confluence.get("fvg_zone_low"),
        fvg_zone_high=confluence.get("fvg_zone_high"),
        order_block_confluence_pass=bool(confluence["ob_pass"]),
        order_block_event_id=confluence.get("ob_event_id"),
        order_block_zone_low=confluence.get("ob_zone_low"),
        order_block_zone_high=confluence.get("ob_zone_high"),
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        pattern_score=score,
        score_components=components,
        score_component_sources=sources,
        score_limitations=(
            "heuristic_score_not_calibrated_probability",
            "ohlcv_liquidity_sweep_proxy_not_order_book_liquidity",
            "no_live_trading_authorization",
        ),
        score_calibration={
            "score_type": "heuristic_quality_score",
            "is_calibrated_probability": False,
            "promotion_blocked_without_oos_validation": True,
        },
        atr_metadata={
            **atr_timing_metadata(config.atr_config or AtrConfig()),
            "atr": atr,
        },
        regime_metadata={
            "tradability_context_missing": True,
            "enable_tradability_gates": bool(config.enable_tradability_gates),
        },
        mtf_metadata={
            "enabled": bool(config.enable_mtf_confirmation),
            "timeframes": tuple(config.mtf_timeframes),
            "context_source": "resampled_completed_base_candles",
            "native_higher_timeframe_context_required_task": "TASK_265",
        },
        zone_low=zone["zone_low"],
        zone_high=zone["zone_high"],
        zone_mid=zone["zone_mid"],
        target_source=target_source,
        entry_source=entry_source,
        executable_pattern_score=score,
        diagnostic_pattern_score=score,
    )


def _candidate_sweep_indices(
    current_index: int,
    config: LiquiditySweepReversalConfig,
) -> range:
    earliest = max(0, current_index - config.displacement_max_bars_after_sweep)
    return range(earliest, current_index + 1)


def _liquidity_pool(
    frame: pd.DataFrame,
    sweep_index: int,
    direction: LiquiditySweepDirection,
    config: LiquiditySweepReversalConfig,
) -> dict[str, Any] | None:
    end = sweep_index - config.min_liquidity_pool_age_bars
    if end < 0:
        return None
    start = max(0, end - config.liquidity_pool_lookback_bars + 1)
    window = frame.iloc[start : end + 1]
    if window.empty:
        return None
    if direction is LiquiditySweepDirection.BULLISH:
        relative = pd.to_numeric(window["low"], errors="coerce").idxmin()
        price = float(frame.loc[relative, "low"])
    else:
        relative = pd.to_numeric(window["high"], errors="coerce").idxmax()
        price = float(frame.loc[relative, "high"])
    return {
        "index": int(relative),
        "timestamp": frame.loc[relative, "timestamp"],
        "price": price,
    }


def _sweep_passes(
    frame: pd.DataFrame,
    sweep_index: int,
    pool: dict[str, Any],
    direction: LiquiditySweepDirection,
    config: LiquiditySweepReversalConfig,
) -> bool:
    sweep = frame.iloc[sweep_index]
    pool_price = float(pool["price"])
    atr = _optional_float(sweep.get("atr"))
    threshold = pool_price * config.min_sweep_bps / 10_000.0
    if atr is not None:
        threshold = max(threshold, atr * config.min_sweep_atr_multiplier)
    if direction is LiquiditySweepDirection.BULLISH:
        return float(sweep["low"]) <= pool_price - threshold
    return float(sweep["high"]) >= pool_price + threshold


def _reclaim_index(
    frame: pd.DataFrame,
    sweep_index: int,
    current_index: int,
    pool: dict[str, Any],
    direction: LiquiditySweepDirection,
    config: LiquiditySweepReversalConfig,
) -> int | None:
    max_reclaim = min(current_index, sweep_index + config.reclaim_max_bars)
    pool_price = float(pool["price"])
    for index in range(sweep_index, max_reclaim + 1):
        close = float(frame.iloc[index]["close"])
        if direction is LiquiditySweepDirection.BULLISH and close > pool_price:
            return index
        if direction is LiquiditySweepDirection.BEARISH and close < pool_price:
            return index
    return None


def _confluence(
    frame: pd.DataFrame,
    current_index: int,
    direction: LiquiditySweepDirection,
) -> dict[str, Any]:
    fvg = _fvg_confluence(frame, current_index, direction)
    ob = _local_ob_confluence(frame, current_index, direction)
    return {
        "fvg_pass": fvg is not None,
        "ob_pass": ob is not None,
        **(fvg or {}),
        **(ob or {}),
    }


def _fvg_confluence(
    frame: pd.DataFrame,
    current_index: int,
    direction: LiquiditySweepDirection,
) -> dict[str, Any] | None:
    if current_index < 2:
        return None
    c1 = frame.iloc[current_index - 2]
    c3 = frame.iloc[current_index]
    if direction is LiquiditySweepDirection.BULLISH and float(c1["high"]) < float(c3["low"]):
        zone_low = float(c1["high"])
        zone_high = float(c3["low"])
    elif direction is LiquiditySweepDirection.BEARISH and float(c1["low"]) > float(c3["high"]):
        zone_low = float(c3["high"])
        zone_high = float(c1["low"])
    else:
        return None
    event_id = sha256(
        f"fvg:{direction.value}:{c1['timestamp']}:{c3['timestamp']}:{zone_low}:{zone_high}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "fvg_event_id": event_id,
        "fvg_zone_low": zone_low,
        "fvg_zone_high": zone_high,
    }


def _local_ob_confluence(
    frame: pd.DataFrame,
    current_index: int,
    direction: LiquiditySweepDirection,
) -> dict[str, Any] | None:
    if current_index < 1:
        return None
    previous = frame.iloc[current_index - 1]
    current = frame.iloc[current_index]
    prev_open = float(previous["open"])
    prev_close = float(previous["close"])
    if direction is LiquiditySweepDirection.BULLISH:
        if not (prev_close < prev_open and float(current["close"]) > float(previous["high"])):
            return None
    else:
        if not (prev_close > prev_open and float(current["close"]) < float(previous["low"])):
            return None
    zone_low = float(previous["low"])
    zone_high = float(previous["high"])
    event_id = sha256(
        f"ob:{direction.value}:{previous['timestamp']}:{current['timestamp']}:{zone_low}:{zone_high}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "ob_event_id": event_id,
        "ob_zone_low": zone_low,
        "ob_zone_high": zone_high,
    }


def _confluence_passes(
    confluence: dict[str, Any],
    config: LiquiditySweepReversalConfig,
) -> bool:
    fvg_pass = bool(confluence.get("fvg_pass"))
    ob_pass = bool(confluence.get("ob_pass"))
    if config.require_both_fvg_and_ob:
        return fvg_pass and ob_pass
    if config.require_fvg_confluence and not fvg_pass:
        return False
    if config.require_order_block_confluence and not ob_pass:
        return False
    return fvg_pass or ob_pass


def _entry_reference(
    confluence: dict[str, Any],
    direction: LiquiditySweepDirection,
    config: LiquiditySweepReversalConfig,
) -> tuple[float, str, dict[str, float]]:
    mode = _coerce_entry_mode(config.entry_mode)
    candidates: list[tuple[float, str, dict[str, float]]] = []
    if confluence.get("fvg_pass"):
        low = float(confluence["fvg_zone_low"])
        high = float(confluence["fvg_zone_high"])
        candidates.append(((low + high) / 2.0, "FVG_MIDPOINT", _zone(low, high)))
    if confluence.get("ob_pass"):
        low = float(confluence["ob_zone_low"])
        high = float(confluence["ob_zone_high"])
        zone_size = high - low
        ob_618 = high - zone_size * 0.618 if direction is LiquiditySweepDirection.BULLISH else low + zone_size * 0.618
        candidates.append((ob_618, "ORDER_BLOCK_618", _zone(low, high)))
    if not candidates:
        raise ValueError("confluence candidates required")
    if mode is LiquiditySweepEntryMode.LIMIT_AT_FVG_MIDPOINT:
        for candidate in candidates:
            if candidate[1] == "FVG_MIDPOINT":
                return candidate
    if mode is LiquiditySweepEntryMode.LIMIT_AT_OB_618:
        for candidate in candidates:
            if candidate[1] == "ORDER_BLOCK_618":
                return candidate
    if mode in {
        LiquiditySweepEntryMode.MARKET_ON_RECLAIM_CLOSE,
        LiquiditySweepEntryMode.MARKET_ON_DISPLACEMENT_CLOSE,
    }:
        return candidates[0]
    return candidates[0] if len(candidates) == 1 else candidates[1]


def _target_reference(
    frame: pd.DataFrame,
    current_index: int,
    entry: float,
    stop: float,
    direction: LiquiditySweepDirection,
    config: LiquiditySweepReversalConfig,
) -> tuple[float, str]:
    window = frame.iloc[max(0, current_index - config.liquidity_pool_lookback_bars) : current_index + 1]
    if direction is LiquiditySweepDirection.BULLISH:
        highs = [float(value) for value in window["high"] if float(value) > entry]
        if highs:
            return min(highs), "OPPOSITE_LIQUIDITY_POOL"
        return entry + abs(entry - stop) * config.target_r_multiple, "FIXED_R_MULTIPLE"
    lows = [float(value) for value in window["low"] if float(value) < entry]
    if lows:
        return max(lows), "OPPOSITE_LIQUIDITY_POOL"
    return entry - abs(stop - entry) * config.target_r_multiple, "FIXED_R_MULTIPLE"


def _risk_reward(
    entry: float,
    stop: float,
    target: float,
    direction: LiquiditySweepDirection,
) -> float | None:
    if direction is LiquiditySweepDirection.BULLISH:
        risk = entry - stop
        reward = target - entry
    else:
        risk = stop - entry
        reward = entry - target
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def _score_components(
    *,
    sweep_distance_atr: float | None,
    sweep_distance_bps: float,
    reclaim_lag: int,
    displacement: pd.Series,
    volume_ratio: float,
    confluence: dict[str, Any],
) -> tuple[float, dict[str, Any], dict[str, str]]:
    sweep_raw = min(1.0, max(0.0, (sweep_distance_atr or sweep_distance_bps / 10.0) / 0.5))
    reclaim_raw = 1.0 if reclaim_lag <= 0 else max(0.0, 1.0 - reclaim_lag * 0.25)
    body = _optional_float(displacement.get("body_ratio")) or 0.0
    range_atr = _optional_float(displacement.get("candle_range")) or 0.0
    displacement_raw = min(1.0, max(body, range_atr / 3.0))
    volume_raw = min(1.0, volume_ratio / 3.0)
    confluence_raw = 1.0 if confluence.get("fvg_pass") and confluence.get("ob_pass") else 0.75
    tradability_raw = 0.7
    weighted = {
        "sweep_quality": (sweep_raw, 0.20, "observed_sweep_distance"),
        "reclaim_quality": (reclaim_raw, 0.20, "observed_reclaim_speed"),
        "displacement_quality": (displacement_raw, 0.20, "observed_displacement_candle"),
        "volume_quality": (volume_raw, 0.15, "observed_prior_only_volume_ratio"),
        "confluence_quality": (confluence_raw, 0.15, "observed_fvg_or_order_block"),
        "tradability_quality": (tradability_raw, 0.10, "missing_or_neutral_proxy_context"),
    }
    components = {
        key: {
            "raw_score": raw,
            "weight": weight,
            "weighted_score": raw * weight,
            "source": source,
        }
        for key, (raw, weight, source) in weighted.items()
    }
    sources = {key: source for key, (_, _, source) in weighted.items()}
    return sum(value["weighted_score"] for value in components.values()), components, sources


def _zone(low: float, high: float) -> dict[str, float]:
    return {"zone_low": low, "zone_high": high, "zone_mid": (low + high) / 2.0}


def _event_id(**payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    symbol: str | None,
) -> pd.DataFrame:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    missing = [column for column in REQUIRED_LIQUIDITY_SWEEP_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required candle columns: {missing}")
    if frame.empty:
        return frame
    normalized = frame.reset_index(drop=True).copy()
    if "symbol" not in normalized.columns:
        normalized.insert(0, "symbol", symbol or "UNKNOWN")
    for column in ("open", "high", "low", "close", "volume"):
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if not normalized["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")
    for row in normalized.itertuples(index=False):
        if float(row.high) < float(row.low):
            raise ValueError("candle high must be greater than or equal to low")
    return normalized


def _coerce_entry_mode(
    mode: LiquiditySweepEntryMode | str,
) -> LiquiditySweepEntryMode:
    if isinstance(mode, LiquiditySweepEntryMode):
        return mode
    normalized = str(mode).strip().upper()
    try:
        return LiquiditySweepEntryMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in LiquiditySweepEntryMode)
        raise ValueError(f"entry_mode must be one of: {allowed}") from exc


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None
