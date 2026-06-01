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

from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


STRATEGY_KEY = "LOOKBACK_RETURN_MOMENTUM"
STRATEGY_NAME = "LOOKBACK_RETURN_MOMENTUM_RESEARCH_STRATEGY"
STRATEGY_VERSION = "v1"
DEFAULT_RISK_DISTANCE_PCT = 0.002


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


@dataclass(frozen=True)
class LookbackReturnMomentumConfig:
    lookback_bars: int = 20
    entry_threshold: float = 0.001
    holding_bars: int = 5
    risk_distance_pct: float = DEFAULT_RISK_DISTANCE_PCT
    stop_loss_r: float = 1.0
    take_profit_r: float = 1.5

    def __post_init__(self) -> None:
        if int(self.lookback_bars) < 1:
            raise ValueError("lookback_bars must be at least 1")
        if int(self.holding_bars) < 1:
            raise ValueError("holding_bars must be at least 1")
        _require_positive_finite("entry_threshold", self.entry_threshold)
        _require_positive_finite("risk_distance_pct", self.risk_distance_pct)
        _require_positive_finite("stop_loss_r", self.stop_loss_r)
        _require_positive_finite("take_profit_r", self.take_profit_r)
        object.__setattr__(self, "lookback_bars", int(self.lookback_bars))
        object.__setattr__(self, "holding_bars", int(self.holding_bars))
        object.__setattr__(self, "entry_threshold", float(self.entry_threshold))
        object.__setattr__(self, "risk_distance_pct", float(self.risk_distance_pct))
        object.__setattr__(self, "stop_loss_r", float(self.stop_loss_r))
        object.__setattr__(self, "take_profit_r", float(self.take_profit_r))

    def to_metadata(self) -> dict[str, object]:
        return {
            "schema_version": "lookback_return_momentum_config_v1",
            "enabled": True,
            "strategy_key": STRATEGY_KEY,
            "strategy_version": STRATEGY_VERSION,
            "lookback_bars": self.lookback_bars,
            "entry_threshold": self.entry_threshold,
            "holding_bars": self.holding_bars,
            "risk_distance_pct": self.risk_distance_pct,
            "stop_loss_r": self.stop_loss_r,
            "take_profit_r": self.take_profit_r,
            "risk_distance_rule": "R_distance = entry_price * risk_distance_pct",
            "entry_timing": "signal_candle_close",
            "exit_precedence": "stop_loss_then_take_profit_then_time_exit",
            "position_policy": "flat_only_no_reverse",
            "scope": "offline_backtest_research_only",
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

    def to_metadata(self) -> dict[str, object]:
        return {
            "position_side": self.side,
            "entry_price": self.entry_price,
            "r_distance": self.r_distance,
            "risk_per_unit": self.risk_per_unit,
            "stop_price": self.stop_price,
            "take_profit_price": self.take_profit_price,
            "target_price": self.take_profit_price,
        }


@dataclass(frozen=True)
class LookbackReturnMomentumStrategy:
    config: LookbackReturnMomentumConfig = LookbackReturnMomentumConfig()
    strategy_key: str = STRATEGY_KEY
    strategy_name: str = STRATEGY_NAME
    strategy_version: str = STRATEGY_VERSION

    def evaluate(
        self,
        candles_so_far: pd.DataFrame | list[dict[str, Any]],
        portfolio_state: dict[str, Any] | None = None,
    ) -> list[StrategyAction]:
        frame = _frame(candles_so_far, required=("timestamp", "close"))
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
        risk = calculate_risk_levels(entry_price, side, self.config)
        action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
        return [
            StrategyAction(
                action_type,
                timestamp=latest["timestamp"],
                reason="LOOKBACK_RETURN_MOMENTUM_SIGNAL",
                requested_price=entry_price,
                metadata=_entry_metadata(
                    self.config,
                    side=side,
                    momentum_return=signal.momentum_return,
                    risk=risk,
                    signal_reason=signal.reason,
                    signal_index=len(frame) - 1,
                    bars_since_signal=0,
                ),
            )
        ]


def config_for_timeframe(
    interval: str,
    *,
    lookback_bars: int | None = None,
    entry_threshold: float | None = None,
    holding_bars: int | None = None,
    risk_distance_pct: float | None = None,
    stop_loss_r: float | None = None,
    take_profit_r: float | None = None,
) -> LookbackReturnMomentumConfig:
    values = dict(TIMEFRAME_DEFAULTS.get(str(interval).lower(), TIMEFRAME_DEFAULTS["1m"]))
    overrides = {
        "lookback_bars": lookback_bars,
        "entry_threshold": entry_threshold,
        "holding_bars": holding_bars,
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
) -> LookbackReturnMomentumRiskLevels:
    cfg = config or LookbackReturnMomentumConfig()
    entry = _positive_float(entry_price)
    if entry is None:
        raise ValueError("entry_price must be a positive finite number")
    normalized_side = str(side).upper()
    if normalized_side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    r_distance = entry * cfg.risk_distance_pct
    risk_per_unit = cfg.stop_loss_r * r_distance
    if normalized_side == "LONG":
        stop_price = entry - risk_per_unit
        take_profit_price = entry + (cfg.take_profit_r * r_distance)
    else:
        stop_price = entry + risk_per_unit
        take_profit_price = entry - (cfg.take_profit_r * r_distance)
    if stop_price <= 0 or take_profit_price <= 0:
        raise ValueError("stop and take-profit prices must be positive")
    return LookbackReturnMomentumRiskLevels(
        side=normalized_side,
        entry_price=entry,
        r_distance=r_distance,
        stop_price=stop_price,
        take_profit_price=take_profit_price,
        risk_per_unit=risk_per_unit,
    )


def build_lookback_return_momentum_actions(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    config: LookbackReturnMomentumConfig | None = None,
) -> list[StrategyAction]:
    cfg = config or LookbackReturnMomentumConfig()
    frame = _frame(candles, required=("timestamp", "high", "low", "close"))
    if frame.empty:
        return []
    if "timestamp" in frame.columns and not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    actions: list[StrategyAction] = []
    open_position: dict[str, Any] | None = None

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
        risk = calculate_risk_levels(entry_price, side, cfg)
        action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
        metadata = _entry_metadata(
            cfg,
            side=side,
            momentum_return=signal.momentum_return,
            risk=risk,
            signal_reason=signal.reason,
            signal_index=index,
            bars_since_signal=0,
        )
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
) -> dict[str, object]:
    return {
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
        "target_source": "FIXED_R_MULTIPLE" if exit_reason == "TAKE_PROFIT" else None,
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
        "risk_distance_pct": config.risk_distance_pct,
        "stop_loss_r": config.stop_loss_r,
        "take_profit_r": config.take_profit_r,
        "reverse_entry_enabled": False,
        "filters_enabled": [],
    }


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
