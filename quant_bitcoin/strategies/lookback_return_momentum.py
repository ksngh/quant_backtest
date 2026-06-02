"""Lookback return momentum research strategy.

This module is offline-only. It builds deterministic strategy actions from
completed OHLCV candles and never fetches data, persists records, or calls
exchange APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, calculate_atr, atr_timing_metadata
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


STRATEGY_KEY = "LOOKBACK_RETURN_MOMENTUM"
STRATEGY_NAME = "LOOKBACK_RETURN_MOMENTUM_RESEARCH_STRATEGY"
STRATEGY_VERSION = "v1"
DEFAULT_RISK_DISTANCE_PCT = 0.002
DEFAULT_RISK_DISTANCE_MODE = "atr"
DEFAULT_ATR_PERIOD = 14
DEFAULT_ATR_SMOOTHING = "RMA"
DEFAULT_STOP_LOSS_ATR_MULTIPLE = 1.0
DEFAULT_TAKE_PROFIT_ATR_MULTIPLE = 1.0
DEFAULT_MINIMUM_ATR_BPS = 0.0


TIMEFRAME_DEFAULTS: dict[str, dict[str, float | int]] = {
    "1m": {"lookback_bars": 20, "holding_bars": 5, "entry_threshold": 0.001},
    "5m": {"lookback_bars": 12, "holding_bars": 6, "entry_threshold": 0.0015},
    "15m": {"lookback_bars": 8, "holding_bars": 4, "entry_threshold": 0.002},
}


class LookbackReturnSignal(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


def _positive_float(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not isfinite(value) or value <= 0.0:
        return None
    return value


def _require_positive_finite(name: str, value: float) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive finite number") from exc
    if not isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be a positive finite number")


def _require_non_negative_finite(name: str, value: float) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a non-negative finite number") from exc
    if not isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number")


def _normalize_risk_distance_mode(raw: str) -> str:
    mode = str(raw).strip().lower()
    if mode not in {"atr", "fixed_pct"}:
        raise ValueError("risk_distance_mode must be atr or fixed_pct")
    return mode


@dataclass(frozen=True)
class LookbackReturnMomentumConfig:
    lookback_bars: int = 20
    entry_threshold: float = 0.001
    holding_bars: int = 5
    risk_distance_mode: str = DEFAULT_RISK_DISTANCE_MODE
    atr_period: int = DEFAULT_ATR_PERIOD
    atr_smoothing: str = DEFAULT_ATR_SMOOTHING
    stop_loss_atr_multiple: float = DEFAULT_STOP_LOSS_ATR_MULTIPLE
    take_profit_atr_multiple: float = DEFAULT_TAKE_PROFIT_ATR_MULTIPLE
    minimum_atr_bps: float = DEFAULT_MINIMUM_ATR_BPS
    risk_distance_pct: float = DEFAULT_RISK_DISTANCE_PCT
    stop_loss_r: float = 1.0
    take_profit_r: float = 1.5

    def __post_init__(self) -> None:
        if int(self.lookback_bars) < 1:
            raise ValueError("lookback_bars must be at least 1")
        if int(self.holding_bars) < 1:
            raise ValueError("holding_bars must be at least 1")
        mode = _normalize_risk_distance_mode(self.risk_distance_mode)
        if int(self.atr_period) < 1:
            raise ValueError("atr_period must be at least 1")
        AtrConfig(period=int(self.atr_period), smoothing_method=str(self.atr_smoothing).upper())
        _require_positive_finite("entry_threshold", self.entry_threshold)
        _require_positive_finite("stop_loss_atr_multiple", self.stop_loss_atr_multiple)
        _require_positive_finite("take_profit_atr_multiple", self.take_profit_atr_multiple)
        _require_non_negative_finite("minimum_atr_bps", self.minimum_atr_bps)
        _require_positive_finite("risk_distance_pct", self.risk_distance_pct)
        _require_positive_finite("stop_loss_r", self.stop_loss_r)
        _require_positive_finite("take_profit_r", self.take_profit_r)
        object.__setattr__(self, "lookback_bars", int(self.lookback_bars))
        object.__setattr__(self, "holding_bars", int(self.holding_bars))
        object.__setattr__(self, "entry_threshold", float(self.entry_threshold))
        object.__setattr__(self, "risk_distance_mode", mode)
        object.__setattr__(self, "atr_period", int(self.atr_period))
        object.__setattr__(self, "atr_smoothing", str(self.atr_smoothing).upper())
        object.__setattr__(self, "stop_loss_atr_multiple", float(self.stop_loss_atr_multiple))
        object.__setattr__(self, "take_profit_atr_multiple", float(self.take_profit_atr_multiple))
        object.__setattr__(self, "minimum_atr_bps", float(self.minimum_atr_bps))
        object.__setattr__(self, "risk_distance_pct", float(self.risk_distance_pct))
        object.__setattr__(self, "stop_loss_r", float(self.stop_loss_r))
        object.__setattr__(self, "take_profit_r", float(self.take_profit_r))

    def to_metadata(self) -> dict[str, object]:
        atr_timing = atr_timing_metadata(
            AtrConfig(period=self.atr_period, smoothing_method=self.atr_smoothing)
        )
        return {
            "schema_version": "lookback_return_momentum_config_v1",
            "enabled": True,
            "strategy_key": STRATEGY_KEY,
            "strategy_version": STRATEGY_VERSION,
            "lookback_bars": self.lookback_bars,
            "entry_threshold": self.entry_threshold,
            "holding_bars": self.holding_bars,
            "risk_distance_mode": self.risk_distance_mode,
            "atr_period": self.atr_period,
            "atr_smoothing": self.atr_smoothing,
            "atr_timing": atr_timing,
            "stop_loss_atr_multiple": self.stop_loss_atr_multiple,
            "take_profit_atr_multiple": self.take_profit_atr_multiple,
            "minimum_atr_bps": self.minimum_atr_bps,
            "risk_distance_pct": self.risk_distance_pct,
            "stop_loss_r": self.stop_loss_r,
            "take_profit_r": self.take_profit_r,
            "risk_distance_rule": (
                "R_distance = ATR_at_entry"
                if self.risk_distance_mode == "atr"
                else "R_distance = entry_price * risk_distance_pct"
            ),
            "entry_timing": "signal_candle_close",
            "exit_precedence": "stop_loss_then_take_profit_then_time_exit",
            "position_policy": "flat_only_no_reverse",
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class LookbackReturnMomentumCostAwareConfig:
    enabled: bool = False
    min_net_reward_bps: float = 20.0
    min_net_rr: float = 1.5
    fee_bps: float = 0.0
    spread_bps: float = 0.0
    slippage_bps: float = 0.0
    minimum_slippage_bps: float = 0.0
    volatility_slippage_multiplier: float = 0.0
    liquidity_role: str = "TAKER"
    cost_profile_name: str | None = None

    def __post_init__(self) -> None:
        _require_non_negative_finite("min_net_reward_bps", self.min_net_reward_bps)
        _require_positive_finite("min_net_rr", self.min_net_rr)
        _require_non_negative_finite("fee_bps", self.fee_bps)
        _require_non_negative_finite("spread_bps", self.spread_bps)
        _require_non_negative_finite("slippage_bps", self.slippage_bps)
        _require_non_negative_finite("minimum_slippage_bps", self.minimum_slippage_bps)
        _require_non_negative_finite("volatility_slippage_multiplier", self.volatility_slippage_multiplier)
        object.__setattr__(self, "enabled", bool(self.enabled))
        object.__setattr__(self, "min_net_reward_bps", float(self.min_net_reward_bps))
        object.__setattr__(self, "min_net_rr", float(self.min_net_rr))
        object.__setattr__(self, "fee_bps", float(self.fee_bps))
        object.__setattr__(self, "spread_bps", float(self.spread_bps))
        object.__setattr__(self, "slippage_bps", float(self.slippage_bps))
        object.__setattr__(self, "minimum_slippage_bps", float(self.minimum_slippage_bps))
        object.__setattr__(self, "volatility_slippage_multiplier", float(self.volatility_slippage_multiplier))
        object.__setattr__(self, "liquidity_role", str(self.liquidity_role).upper())

    def to_metadata(self) -> dict[str, object]:
        return {
            "schema_version": "lookback_return_momentum_cost_aware_entry_filter_config_v1",
            "enabled": self.enabled,
            "min_net_reward_bps": self.min_net_reward_bps,
            "min_net_rr": self.min_net_rr,
            "fee_bps": self.fee_bps,
            "spread_bps": self.spread_bps,
            "slippage_bps": self.slippage_bps,
            "minimum_slippage_bps": self.minimum_slippage_bps,
            "volatility_slippage_multiplier": self.volatility_slippage_multiplier,
            "cost_profile_name": self.cost_profile_name or "manual",
            "liquidity_role": self.liquidity_role,
            "gate_version": "cost_aware_entry_filter_v1",
        }


@dataclass(frozen=True)
class LookbackReturnMomentumSignal:
    signal: LookbackReturnSignal
    momentum_return: float | None
    reason: str


@dataclass(frozen=True)
class LookbackReturnMomentumRiskLevels:
    side: str
    entry_price: float
    r_distance: float
    stop_price: float
    take_profit_price: float
    risk_per_unit: float
    risk_distance_mode: str
    atr_value: float | None = None
    atr_period: int | None = None
    atr_smoothing: str | None = None
    stop_loss_atr_multiple: float | None = None
    take_profit_atr_multiple: float | None = None
    atr_bps: float | None = None
    minimum_atr_bps: float | None = None
    atr_metadata: dict[str, object] | None = None

    def to_metadata(self) -> dict[str, object]:
        return {
            "position_side": self.side,
            "entry_price": self.entry_price,
            "r_distance": self.r_distance,
            "risk_per_unit": self.risk_per_unit,
            "stop_price": self.stop_price,
            "take_profit_price": self.take_profit_price,
            "target_price": self.take_profit_price,
            "risk_distance_mode": self.risk_distance_mode,
            "atr_value": self.atr_value,
            "atr_period": self.atr_period,
            "atr_smoothing": self.atr_smoothing,
            "stop_loss_atr_multiple": self.stop_loss_atr_multiple,
            "take_profit_atr_multiple": self.take_profit_atr_multiple,
            "atr_bps": self.atr_bps,
            "minimum_atr_bps": self.minimum_atr_bps,
            "atr_metadata": self.atr_metadata or {},
        }


@dataclass(frozen=True)
class LookbackReturnMomentumStrategy:
    config: LookbackReturnMomentumConfig = LookbackReturnMomentumConfig()
    cost_aware_config: LookbackReturnMomentumCostAwareConfig | None = None
    strategy_key: str = STRATEGY_KEY
    strategy_name: str = STRATEGY_NAME
    strategy_version: str = STRATEGY_VERSION

    def evaluate(
        self,
        candles_so_far: pd.DataFrame | list[dict[str, Any]],
        portfolio_state: dict[str, Any] | None = None,
    ) -> list[StrategyAction]:
        frame = _frame(candles_so_far, required=("timestamp", "high", "low", "close"))
        if frame.empty:
            return []
        position = float((portfolio_state or {}).get("position", 0.0))
        if position != 0.0:
            return []
        signal = calculate_lookback_return_momentum_signal(frame, self.config)
        if signal.signal is LookbackReturnSignal.NONE:
            return []
        side = signal.signal.value
        latest = frame.iloc[-1]
        entry_price = _positive_float(latest["close"])
        if entry_price is None:
            return []
        atr_context = (
            calculate_atr_risk_context(frame, self.config)
            if self.config.risk_distance_mode == "atr"
            else {}
        )
        if self.config.risk_distance_mode == "atr" and not atr_context.get("atr_is_valid"):
            metadata = _invalid_risk_entry_metadata(
                self.config,
                side=side,
                momentum_return=signal.momentum_return,
                signal_reason=signal.reason,
                signal_index=len(frame) - 1,
                bars_since_signal=0,
                entry_price=entry_price,
                atr_metadata=atr_context,
            )
            return [
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=latest["timestamp"],
                    reason="INVALID_ATR_RISK_DISTANCE",
                    requested_price=entry_price,
                    metadata=metadata,
                )
            ]
        risk = calculate_risk_levels(
            entry_price,
            side,
            self.config,
            atr_value=atr_context.get("atr_value") if atr_context else None,
            atr_metadata=atr_context or None,
        )
        minimum_atr_decision = minimum_atr_bps_filter_decision(risk, self.config)
        if minimum_atr_decision.get("enabled") and minimum_atr_decision.get("blocked"):
            metadata = _entry_metadata(
                self.config,
                side=side,
                momentum_return=signal.momentum_return,
                risk=risk,
                signal_reason=signal.reason,
                signal_index=len(frame) - 1,
                bars_since_signal=0,
                minimum_atr_decision=minimum_atr_decision,
            )
            return [
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=latest["timestamp"],
                    reason="ATR_TOO_SMALL_FOR_COST",
                    requested_price=entry_price,
                    metadata=_skipped_entry_metadata(metadata, "ATR_TOO_SMALL_FOR_COST"),
                )
            ]
        cost_decision = cost_aware_entry_filter_decision(risk, latest, self.cost_aware_config)
        action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
        metadata = _entry_metadata(
            self.config,
            side=side,
            momentum_return=signal.momentum_return,
            risk=risk,
            signal_reason=signal.reason,
            signal_index=len(frame) - 1,
            bars_since_signal=0,
            minimum_atr_decision=minimum_atr_decision,
            cost_aware_decision=cost_decision,
        )
        if cost_decision.get("enabled") and cost_decision.get("blocked"):
            metadata = _blocked_entry_metadata(metadata, cost_decision)
            return [
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=latest["timestamp"],
                    reason=str(cost_decision.get("block_reason") or "COST_INFEASIBLE_NET_RR"),
                    requested_price=entry_price,
                    metadata=metadata,
                )
            ]
        return [
            StrategyAction(
                action_type,
                timestamp=latest["timestamp"],
                reason="LOOKBACK_RETURN_MOMENTUM_SIGNAL",
                requested_price=entry_price,
                metadata=metadata,
            )
        ]


def config_for_timeframe(
    interval: str,
    *,
    lookback_bars: int | None = None,
    entry_threshold: float | None = None,
    holding_bars: int | None = None,
    risk_distance_mode: str | None = None,
    atr_period: int | None = None,
    atr_smoothing: str | None = None,
    stop_loss_atr_multiple: float | None = None,
    take_profit_atr_multiple: float | None = None,
    minimum_atr_bps: float | None = None,
    risk_distance_pct: float | None = None,
    stop_loss_r: float | None = None,
    take_profit_r: float | None = None,
) -> LookbackReturnMomentumConfig:
    values = dict(TIMEFRAME_DEFAULTS.get(str(interval).lower(), TIMEFRAME_DEFAULTS["1m"]))
    overrides = {
        "lookback_bars": lookback_bars,
        "entry_threshold": entry_threshold,
        "holding_bars": holding_bars,
        "risk_distance_mode": risk_distance_mode,
        "atr_period": atr_period,
        "atr_smoothing": atr_smoothing,
        "stop_loss_atr_multiple": stop_loss_atr_multiple,
        "take_profit_atr_multiple": take_profit_atr_multiple,
        "minimum_atr_bps": minimum_atr_bps,
        "risk_distance_pct": risk_distance_pct,
        "stop_loss_r": stop_loss_r,
        "take_profit_r": take_profit_r,
    }
    values.update({key: value for key, value in overrides.items() if value is not None})
    return LookbackReturnMomentumConfig(**values)


def calculate_momentum_return(
    candles_so_far: pd.DataFrame | list[dict[str, Any]],
    *,
    lookback_bars: int,
) -> float | None:
    frame = _frame(candles_so_far, required=("close",))
    lookback = int(lookback_bars)
    if lookback < 1:
        raise ValueError("lookback_bars must be at least 1")
    if len(frame) <= lookback:
        return None
    current_close = _positive_float(frame.iloc[-1]["close"])
    lookback_close = _positive_float(frame.iloc[-1 - lookback]["close"])
    if current_close is None or lookback_close is None:
        return None
    return current_close / lookback_close - 1.0


def calculate_lookback_return_momentum_signal(
    candles_so_far: pd.DataFrame | list[dict[str, Any]],
    config: LookbackReturnMomentumConfig | None = None,
) -> LookbackReturnMomentumSignal:
    cfg = config or LookbackReturnMomentumConfig()
    frame = _frame(candles_so_far, required=("close",))
    if len(frame) <= cfg.lookback_bars:
        return LookbackReturnMomentumSignal(
            LookbackReturnSignal.NONE,
            None,
            "INSUFFICIENT_LOOKBACK",
        )
    momentum_return = calculate_momentum_return(frame, lookback_bars=cfg.lookback_bars)
    if momentum_return is None:
        return LookbackReturnMomentumSignal(
            LookbackReturnSignal.NONE,
            None,
            "INVALID_CLOSE",
        )
    if momentum_return >= cfg.entry_threshold:
        return LookbackReturnMomentumSignal(
            LookbackReturnSignal.LONG,
            momentum_return,
            "LONG_THRESHOLD_MET",
        )
    if momentum_return <= -cfg.entry_threshold:
        return LookbackReturnMomentumSignal(
            LookbackReturnSignal.SHORT,
            momentum_return,
            "SHORT_THRESHOLD_MET",
        )
    return LookbackReturnMomentumSignal(
        LookbackReturnSignal.NONE,
        momentum_return,
        "THRESHOLD_NOT_MET",
    )


def calculate_risk_levels(
    entry_price: float,
    side: str,
    config: LookbackReturnMomentumConfig | None = None,
    *,
    atr_value: float | None = None,
    atr_metadata: dict[str, object] | None = None,
) -> LookbackReturnMomentumRiskLevels:
    cfg = config or LookbackReturnMomentumConfig()
    entry = _positive_float(entry_price)
    if entry is None:
        raise ValueError("entry_price must be a positive finite number")
    normalized_side = str(side).upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    if cfg.risk_distance_mode == "atr":
        r_distance = _positive_float(atr_value)
        if r_distance is None:
            raise ValueError("atr_value must be a positive finite number for atr risk distance")
        stop_multiple = cfg.stop_loss_atr_multiple
        target_multiple = cfg.take_profit_atr_multiple
        atr_value_for_metadata = r_distance
        atr_period = cfg.atr_period
        atr_smoothing = cfg.atr_smoothing
        atr_bps = (r_distance / entry) * 10_000.0
        minimum_atr_bps = cfg.minimum_atr_bps
    else:
        r_distance = entry * cfg.risk_distance_pct
        stop_multiple = cfg.stop_loss_r
        target_multiple = cfg.take_profit_r
        atr_value_for_metadata = None
        atr_period = None
        atr_smoothing = None
        atr_bps = None
        minimum_atr_bps = None
    risk_per_unit = stop_multiple * r_distance
    if normalized_side == "LONG":
        stop_price = entry - risk_per_unit
        take_profit_price = entry + (target_multiple * r_distance)
    else:
        stop_price = entry + risk_per_unit
        take_profit_price = entry - (target_multiple * r_distance)
    if stop_price <= 0 or take_profit_price <= 0:
        raise ValueError("stop and take-profit prices must be positive")
    return LookbackReturnMomentumRiskLevels(
        side=normalized_side,
        entry_price=entry,
        r_distance=r_distance,
        stop_price=stop_price,
        take_profit_price=take_profit_price,
        risk_per_unit=risk_per_unit,
        risk_distance_mode=cfg.risk_distance_mode,
        atr_value=atr_value_for_metadata,
        atr_period=atr_period,
        atr_smoothing=atr_smoothing,
        stop_loss_atr_multiple=cfg.stop_loss_atr_multiple if cfg.risk_distance_mode == "atr" else None,
        take_profit_atr_multiple=cfg.take_profit_atr_multiple if cfg.risk_distance_mode == "atr" else None,
        atr_bps=atr_bps,
        minimum_atr_bps=minimum_atr_bps,
        atr_metadata=atr_metadata,
    )


def calculate_atr_risk_context(
    candles_so_far: pd.DataFrame | list[dict[str, Any]],
    config: LookbackReturnMomentumConfig | None = None,
) -> dict[str, object]:
    cfg = config or LookbackReturnMomentumConfig()
    frame = _frame(candles_so_far, required=("timestamp", "high", "low", "close"))
    contexts = _calculate_atr_risk_contexts(frame, cfg)
    if contexts:
        return contexts[-1]
    atr_config = AtrConfig(period=cfg.atr_period, smoothing_method=cfg.atr_smoothing)
    return _atr_risk_context_base_metadata(cfg, atr_config) | {
        "atr_value": None,
        "atr_is_valid": False,
        "atr_timestamp": None,
        "invalid_reason": "EMPTY_CANDLES",
    }


def _calculate_atr_risk_contexts(
    frame: pd.DataFrame,
    cfg: LookbackReturnMomentumConfig,
) -> list[dict[str, object]]:
    atr_config = AtrConfig(period=cfg.atr_period, smoothing_method=cfg.atr_smoothing)
    metadata = _atr_risk_context_base_metadata(cfg, atr_config)
    if frame.empty:
        return []
    atr_input = frame.copy(deep=False)
    if "symbol" not in atr_input.columns:
        atr_input = atr_input.copy()
        atr_input["symbol"] = STRATEGY_KEY
    try:
        atr_rows = calculate_atr(atr_input, atr_config)
    except (TypeError, ValueError) as exc:
        return [
            metadata
            | {
                "atr_value": None,
                "atr_is_valid": False,
                "atr_timestamp": candle.get("timestamp"),
                "invalid_reason": str(exc),
            }
            for _, candle in frame.iterrows()
        ]
    contexts: list[dict[str, object]] = []
    for _, row in atr_rows.iterrows():
        latest = row.to_dict()
        atr_value = _positive_float(latest.get("atr")) if bool(latest.get("is_valid")) else None
        contexts.append(
            metadata
            | {
                "atr_value": atr_value,
                "atr_is_valid": atr_value is not None,
                "atr_timestamp": latest.get("timestamp"),
                "true_range": latest.get("true_range"),
                "normalized_atr": latest.get("normalized_atr"),
                "normalized_atr_percent": latest.get("normalized_atr_percent"),
                "volatility_status": latest.get("volatility_status"),
                "invalid_reason": None if atr_value is not None else "INVALID_ATR_RISK_DISTANCE",
            }
        )
    return contexts


def _atr_risk_context_base_metadata(
    cfg: LookbackReturnMomentumConfig,
    atr_config: AtrConfig,
) -> dict[str, object]:
    return {
        **atr_timing_metadata(atr_config),
        "schema_version": "lookback_return_momentum_atr_risk_context_v1",
        "risk_distance_mode": cfg.risk_distance_mode,
        "atr_period": cfg.atr_period,
        "atr_smoothing": cfg.atr_smoothing,
        "stop_loss_atr_multiple": cfg.stop_loss_atr_multiple,
        "take_profit_atr_multiple": cfg.take_profit_atr_multiple,
        "minimum_atr_bps": cfg.minimum_atr_bps,
    }


def build_lookback_return_momentum_actions(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    config: LookbackReturnMomentumConfig | None = None,
    cost_aware_config: LookbackReturnMomentumCostAwareConfig | None = None,
) -> list[StrategyAction]:
    cfg = config or LookbackReturnMomentumConfig()
    frame = _frame(candles, required=("timestamp", "high", "low", "close"))
    if frame.empty:
        return []
    if "timestamp" in frame.columns and not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    actions: list[StrategyAction] = []
    open_position: dict[str, Any] | None = None
    atr_contexts = _calculate_atr_risk_contexts(frame, cfg) if cfg.risk_distance_mode == "atr" else []

    for index, (_, candle) in enumerate(frame.iterrows()):
        if open_position is not None and index > int(open_position["entry_index"]):
            exit_action = _exit_action_for_candle(candle, index, open_position, cfg)
            if exit_action is not None:
                actions.append(exit_action)
                open_position = None
                continue

        if open_position is not None:
            continue

        visible = frame.iloc[: index + 1]
        signal = calculate_lookback_return_momentum_signal(visible, cfg)
        if signal.signal is LookbackReturnSignal.NONE:
            continue
        entry_price = _positive_float(candle["close"])
        if entry_price is None:
            continue
        side = signal.signal.value
        atr_context = atr_contexts[index] if cfg.risk_distance_mode == "atr" else {}
        if cfg.risk_distance_mode == "atr" and not atr_context.get("atr_is_valid"):
            metadata = _invalid_risk_entry_metadata(
                cfg,
                side=side,
                momentum_return=signal.momentum_return,
                signal_reason=signal.reason,
                signal_index=index,
                bars_since_signal=0,
                entry_price=entry_price,
                atr_metadata=atr_context,
            )
            actions.append(
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=candle["timestamp"],
                    reason="INVALID_ATR_RISK_DISTANCE",
                    requested_price=entry_price,
                    metadata=metadata,
                )
            )
            continue
        risk = calculate_risk_levels(
            entry_price,
            side,
            cfg,
            atr_value=atr_context.get("atr_value") if atr_context else None,
            atr_metadata=atr_context or None,
        )
        minimum_atr_decision = minimum_atr_bps_filter_decision(risk, cfg)
        if minimum_atr_decision.get("enabled") and minimum_atr_decision.get("blocked"):
            metadata = _entry_metadata(
                cfg,
                side=side,
                momentum_return=signal.momentum_return,
                risk=risk,
                signal_reason=signal.reason,
                signal_index=index,
                bars_since_signal=0,
                minimum_atr_decision=minimum_atr_decision,
            )
            actions.append(
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=candle["timestamp"],
                    reason="ATR_TOO_SMALL_FOR_COST",
                    requested_price=entry_price,
                    metadata=_skipped_entry_metadata(metadata, "ATR_TOO_SMALL_FOR_COST"),
                )
            )
            continue
        cost_decision = cost_aware_entry_filter_decision(risk, candle, cost_aware_config)
        action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
        metadata = _entry_metadata(
            cfg,
            side=side,
            momentum_return=signal.momentum_return,
            risk=risk,
            signal_reason=signal.reason,
            signal_index=index,
            bars_since_signal=0,
            minimum_atr_decision=minimum_atr_decision,
            cost_aware_decision=cost_decision,
        )
        if cost_decision.get("enabled") and cost_decision.get("blocked"):
            actions.append(
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=candle["timestamp"],
                    reason=str(cost_decision.get("block_reason") or "COST_INFEASIBLE_NET_RR"),
                    requested_price=entry_price,
                    metadata=_blocked_entry_metadata(metadata, cost_decision),
                )
            )
            continue
        actions.append(
            StrategyAction(
                action_type,
                timestamp=candle["timestamp"],
                reason="LOOKBACK_RETURN_MOMENTUM_SIGNAL",
                requested_price=entry_price,
                metadata=metadata,
            )
        )
        open_position = {
            "side": side,
            "entry_index": index,
            "entry_timestamp": candle["timestamp"],
            "entry_price": entry_price,
            "risk": risk,
            "entry_metadata": metadata,
        }

    return actions


def cost_aware_entry_filter_decision(
    risk: LookbackReturnMomentumRiskLevels,
    candle: pd.Series | dict[str, Any],
    config: LookbackReturnMomentumCostAwareConfig | None,
) -> dict[str, object]:
    if config is None or not config.enabled:
        return {}

    side = risk.side.upper()
    if side == "LONG":
        gross_reward_bps = ((risk.take_profit_price - risk.entry_price) / risk.entry_price) * 10_000.0
        gross_risk_bps = ((risk.entry_price - risk.stop_price) / risk.entry_price) * 10_000.0
    elif side == "SHORT":
        gross_reward_bps = ((risk.entry_price - risk.take_profit_price) / risk.entry_price) * 10_000.0
        gross_risk_bps = ((risk.stop_price - risk.entry_price) / risk.entry_price) * 10_000.0
    else:
        return {
            "schema_version": "cost_aware_entry_filter_v1",
            "enabled": True,
            "blocked": True,
            "block_reason": "COST_FILTER_INVALID_SIDE",
        }

    volatility_bps = _candle_volatility_bps(candle)
    effective_slippage = _effective_slippage_bps(config, volatility_bps)
    one_side_cost_bps = config.fee_bps + config.spread_bps + effective_slippage
    round_trip_cost_bps = 2.0 * one_side_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    blocked = (
        gross_reward_bps <= 0.0
        or gross_risk_bps <= 0.0
        or net_reward_bps < config.min_net_reward_bps
        or net_rr is None
        or net_rr < config.min_net_rr
    )
    return {
        "schema_version": "cost_aware_entry_filter_v1",
        "enabled": True,
        "blocked": blocked,
        "block_reason": "COST_INFEASIBLE_NET_RR" if blocked else None,
        "min_net_reward_bps": config.min_net_reward_bps,
        "min_net_rr": config.min_net_rr,
        "entry_price": risk.entry_price,
        "target_price": risk.take_profit_price,
        "stop_price": risk.stop_price,
        "risk_distance_mode": risk.risk_distance_mode,
        "r_distance": risk.r_distance,
        "atr_value": risk.atr_value,
        "atr_period": risk.atr_period,
        "atr_smoothing": risk.atr_smoothing,
        "atr_bps": risk.atr_bps,
        "minimum_atr_bps": risk.minimum_atr_bps,
        "stop_loss_atr_multiple": risk.stop_loss_atr_multiple,
        "take_profit_atr_multiple": risk.take_profit_atr_multiple,
        "gross_reward_bps": gross_reward_bps,
        "gross_risk_bps": gross_risk_bps,
        "estimated_one_side_cost_bps": one_side_cost_bps,
        "estimated_round_trip_cost_bps": round_trip_cost_bps,
        "net_reward_bps": net_reward_bps,
        "net_risk_bps": net_risk_bps,
        "net_rr": net_rr,
        "fee_bps": config.fee_bps,
        "spread_bps": config.spread_bps,
        "slippage_bps": config.slippage_bps,
        "effective_slippage_bps": effective_slippage,
        "volatility_bps": volatility_bps,
        "cost_profile_name": config.cost_profile_name or "manual",
        "liquidity_role": config.liquidity_role,
    }


def _exit_action_for_candle(
    candle: pd.Series,
    index: int,
    open_position: dict[str, Any],
    config: LookbackReturnMomentumConfig,
) -> StrategyAction | None:
    side = str(open_position["side"]).upper()
    risk = open_position["risk"]
    low = _positive_float(candle["low"])
    high = _positive_float(candle["high"])
    close = _positive_float(candle["close"])
    if low is None or high is None or close is None:
        return None

    bars_since_entry = index - int(open_position["entry_index"])
    if side == "LONG":
        stop_hit = low <= risk.stop_price
        target_hit = high >= risk.take_profit_price
        exit_action_type = StrategyActionType.EXIT_LONG
        exit_price = risk.stop_price if stop_hit else risk.take_profit_price if target_hit else close
    else:
        stop_hit = high >= risk.stop_price
        target_hit = low <= risk.take_profit_price
        exit_action_type = StrategyActionType.EXIT_SHORT
        exit_price = risk.stop_price if stop_hit else risk.take_profit_price if target_hit else close

    if stop_hit:
        exit_reason = "STOP_LOSS"
    elif target_hit:
        exit_reason = "TAKE_PROFIT"
    elif bars_since_entry >= config.holding_bars:
        exit_reason = "TIME_EXIT"
    else:
        return None

    metadata = _exit_metadata(
        config,
        open_position,
        exit_reason=exit_reason,
        exit_price=exit_price,
        exit_index=index,
        exit_timestamp=candle["timestamp"],
        bars_since_entry=bars_since_entry,
        stop_hit=stop_hit,
        target_hit=target_hit,
    )
    return StrategyAction(
        exit_action_type,
        timestamp=candle["timestamp"],
        quantity=1.0,
        quantity_mode=StrategyQuantityMode.POSITION_RATIO,
        reason=exit_reason,
        requested_price=exit_price,
        metadata=metadata,
    )


def _entry_metadata(
    config: LookbackReturnMomentumConfig,
    *,
    side: str,
    momentum_return: float | None,
    risk: LookbackReturnMomentumRiskLevels,
    signal_reason: str,
    signal_index: int,
    bars_since_signal: int,
    minimum_atr_decision: dict[str, object] | None = None,
    cost_aware_decision: dict[str, object] | None = None,
) -> dict[str, object]:
    metadata = {
        **_strategy_metadata(config),
        **risk.to_metadata(),
        "signal_side": side,
        "momentum_return": momentum_return,
        "signal_reason": signal_reason,
        "signal_index": signal_index,
        "bars_since_signal": bars_since_signal,
        "entry_rule": "momentum_return_threshold",
        "entry_price_source": "signal_candle_close",
        "requested_price": risk.entry_price,
        "fill_price": risk.entry_price,
        "entry_status": "FILLED",
    }
    if minimum_atr_decision:
        metadata["minimum_atr_bps_filter"] = dict(minimum_atr_decision)
        if minimum_atr_decision.get("enabled"):
            metadata["filters_enabled"] = [
                *list(metadata.get("filters_enabled") or []),
                "minimum_atr_bps_filter_v1",
            ]
    if cost_aware_decision and cost_aware_decision.get("enabled"):
        metadata["cost_aware_entry_filter"] = dict(cost_aware_decision)
        metadata["filters_enabled"] = [
            *list(metadata.get("filters_enabled") or []),
            "cost_aware_entry_filter_v1",
        ]
    return metadata


def minimum_atr_bps_filter_decision(
    risk: LookbackReturnMomentumRiskLevels,
    config: LookbackReturnMomentumConfig | None = None,
) -> dict[str, object]:
    cfg = config or LookbackReturnMomentumConfig()
    if risk.risk_distance_mode != "atr":
        return {}
    enabled = cfg.minimum_atr_bps > 0.0
    atr_bps = risk.atr_bps
    blocked = enabled and (atr_bps is None or atr_bps < cfg.minimum_atr_bps)
    return {
        "schema_version": "minimum_atr_bps_filter_v1",
        "enabled": enabled,
        "blocked": blocked,
        "block_reason": "ATR_TOO_SMALL_FOR_COST" if blocked else None,
        "atr_bps": atr_bps,
        "minimum_atr_bps": cfg.minimum_atr_bps,
        "risk_distance_mode": risk.risk_distance_mode,
        "atr_value": risk.atr_value,
        "entry_price": risk.entry_price,
    }


def _blocked_entry_metadata(
    metadata: dict[str, object],
    cost_aware_decision: dict[str, object],
) -> dict[str, object]:
    return {
        **metadata,
        "entry_status": "REJECTED",
        "fill_price": None,
        "skip_reason": cost_aware_decision.get("block_reason") or "COST_INFEASIBLE_NET_RR",
    }


def _skipped_entry_metadata(
    metadata: dict[str, object],
    skip_reason: str,
) -> dict[str, object]:
    return {
        **metadata,
        "entry_status": "REJECTED",
        "fill_price": None,
        "skip_reason": skip_reason,
        "reason": skip_reason,
    }


def _invalid_risk_entry_metadata(
    config: LookbackReturnMomentumConfig,
    *,
    side: str,
    momentum_return: float | None,
    signal_reason: str,
    signal_index: int,
    bars_since_signal: int,
    entry_price: float,
    atr_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        **_strategy_metadata(config),
        "signal_side": side,
        "momentum_return": momentum_return,
        "signal_reason": signal_reason,
        "signal_index": signal_index,
        "bars_since_signal": bars_since_signal,
        "entry_rule": "momentum_return_threshold",
        "entry_price_source": "signal_candle_close",
        "requested_price": entry_price,
        "fill_price": None,
        "entry_status": "REJECTED",
        "skip_reason": "INVALID_ATR_RISK_DISTANCE",
        "risk_distance_mode": config.risk_distance_mode,
        "atr_metadata": dict(atr_metadata),
        "atr_value": atr_metadata.get("atr_value"),
        "atr_is_valid": atr_metadata.get("atr_is_valid"),
        "reason": "INVALID_ATR_RISK_DISTANCE",
    }


def _exit_metadata(
    config: LookbackReturnMomentumConfig,
    open_position: dict[str, Any],
    *,
    exit_reason: str,
    exit_price: float,
    exit_index: int,
    exit_timestamp: Any,
    bars_since_entry: int,
    stop_hit: bool,
    target_hit: bool,
) -> dict[str, object]:
    risk = open_position["risk"]
    side = str(open_position["side"]).upper()
    realized_r = (
        (exit_price - risk.entry_price) / risk.r_distance
        if side == "LONG"
        else (risk.entry_price - exit_price) / risk.r_distance
    )
    ambiguous = bool(stop_hit and target_hit)
    return {
        **dict(open_position["entry_metadata"]),
        "exit_reason": exit_reason,
        "exit_price": exit_price,
        "exit_index": exit_index,
        "exit_timestamp": exit_timestamp,
        "bars_since_entry": bars_since_entry,
        "stop_hit": bool(stop_hit),
        "target_hit": bool(target_hit),
        "ambiguous_stop_target": ambiguous,
        "intrabar_precedence_policy": "stop_before_target",
        "precedence": "stop_before_target" if ambiguous else None,
        "target_source": (
            "ATR_MULTIPLE"
            if risk.risk_distance_mode == "atr" and exit_reason == "TAKE_PROFIT"
            else "FIXED_R_MULTIPLE"
            if exit_reason == "TAKE_PROFIT"
            else None
        ),
        "realized_r_multiple": realized_r,
        "quantity_ratio": 1.0,
        "action_quantity_ratio": 1.0,
        "remaining_quantity_ratio": 0.0,
        "quantity_mode": StrategyQuantityMode.POSITION_RATIO.value,
    }


def _strategy_metadata(config: LookbackReturnMomentumConfig) -> dict[str, object]:
    return {
        "strategy_key": STRATEGY_KEY,
        "strategy_name": STRATEGY_NAME,
        "strategy_version": STRATEGY_VERSION,
        "strategy_type": "lookback_return_momentum",
        "strategy_scope": "offline_backtest_research_only",
        "lookback_bars": config.lookback_bars,
        "entry_threshold": config.entry_threshold,
        "holding_bars": config.holding_bars,
        "risk_distance_mode": config.risk_distance_mode,
        "atr_period": config.atr_period,
        "atr_smoothing": config.atr_smoothing,
        "stop_loss_atr_multiple": config.stop_loss_atr_multiple,
        "take_profit_atr_multiple": config.take_profit_atr_multiple,
        "minimum_atr_bps": config.minimum_atr_bps,
        "risk_distance_pct": config.risk_distance_pct,
        "stop_loss_r": config.stop_loss_r,
        "take_profit_r": config.take_profit_r,
        "reverse_entry_enabled": False,
        "filters_enabled": [],
    }


def _candle_volatility_bps(candle: pd.Series | dict[str, Any]) -> float | None:
    getter = candle.get if hasattr(candle, "get") else lambda key: None
    high = _positive_float(getter("high"))
    low = _positive_float(getter("low"))
    close = _positive_float(getter("close"))
    if high is None or low is None or close is None:
        return None
    return ((high - low) / close) * 10_000.0


def _effective_slippage_bps(
    config: LookbackReturnMomentumCostAwareConfig,
    volatility_bps: float | None,
) -> float:
    if volatility_bps is None:
        return max(config.slippage_bps, config.minimum_slippage_bps)
    return max(
        config.slippage_bps + (float(volatility_bps) * config.volatility_slippage_multiplier),
        config.minimum_slippage_bps,
    )


def _frame(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    required: tuple[str, ...],
) -> pd.DataFrame:
    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"candles missing required columns: {missing}")
    return frame
