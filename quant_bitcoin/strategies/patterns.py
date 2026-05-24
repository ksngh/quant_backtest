from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from quant_bitcoin.indicators.market_regime import (
    PatternRegimeThresholdConfig,
    evaluate_pattern_regime_thresholds,
)
from quant_bitcoin.patterns import (
    AdamAndEveConfig, AdamAndEveRiskExitConfig, CupAndHandleConfig, CupAndHandleRiskExitConfig,
    DiamondConfig, DiamondRiskExitConfig, FairValueGapConfig, FairValueGapRiskExitConfig,
    OrderBlockConfig, OrderBlockRiskExitConfig, TrendlineBreakConfig, TrendlineBreakRiskExitConfig,
    create_adam_and_eve_risk_exit_plan, create_cup_and_handle_risk_exit_plan, create_diamond_risk_exit_plan,
    create_fair_value_gap_risk_exit_plan, create_order_block_risk_exit_plan, create_trendline_break_risk_exit_plan,
    detect_adam_and_eve_patterns, detect_cup_and_handle_patterns, detect_diamond_patterns,
    detect_fair_value_gaps, detect_order_blocks, detect_trendline_breaks,
)
from quant_bitcoin.backtesting.fvg_detection_cache import (
    PatternEvaluationContext,
    detect_adam_and_eve_at_index,
    detect_cup_and_handle_at_index,
    detect_diamond_at_index,
    detect_fair_value_gap_at_index,
    detect_order_block_at_index,
    detect_trendline_break_at_index,
)
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


PATTERN_EXECUTION_PATH_LEGACY_SIMPLE_ENTRY = "LEGACY_SIMPLE_ENTRY_SIGNAL"


@dataclass(frozen=True)
class PatternEntryFilterConfig:
    allowed_statuses: tuple[str, ...] = ("VALID",)
    minimum_pattern_score: float | None = None
    minimum_risk_reward: float | None = None
    quantity_override: float | None = None
    regime_threshold_config: PatternRegimeThresholdConfig | None = None


def pattern_direction_to_position_side(direction: str) -> str | None:
    value = str(direction).upper()
    if value == "BULLISH":
        return "LONG"
    if value == "BEARISH":
        return "SHORT"
    return None




def _event_to_actions(
    strategy: "PatternStrategyBase",
    event: Any,
    timestamp: Any,
    frame: pd.DataFrame,
    regime_context: dict[str, Any] | None = None,
) -> list[StrategyAction]:
    direction = str(getattr(event, "direction", "")).upper()
    position_side = pattern_direction_to_position_side(direction)
    if position_side is None:
        return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="UNSUPPORTED_DIRECTION", metadata={"pattern_event_id": getattr(event, "event_id", None), "pattern_type": getattr(event, "pattern_type", None), "pattern_direction": direction})]
    pattern_status = str(getattr(event, "pattern_status", "")).upper()
    pattern_score = getattr(
        event,
        "executable_pattern_score",
        getattr(event, "pattern_score", None),
    )
    risk_reward = getattr(event, "risk_reward", None)
    planned = strategy._risk_plan(event, frame)
    metadata = _raw_pattern_metadata(event, direction, position_side, planned, pattern_status, pattern_score, risk_reward)
    regime_decision = evaluate_pattern_regime_thresholds(
        metadata,
        regime_context,
        strategy.entry_filter_config.regime_threshold_config,
    )
    if regime_decision["enabled"]:
        metadata["pattern_regime_thresholds"] = regime_decision
    if regime_decision["blocked"]:
        return [
            StrategyAction(
                StrategyActionType.SKIP,
                timestamp,
                reason=regime_decision["block_reason"],
                metadata=metadata,
            )
        ]
    if planned is None or planned.status != RiskExitPlanStatus.VALID:
        return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_PLAN_INVALID", metadata=metadata)]
    if pattern_status not in strategy.entry_filter_config.allowed_statuses:
        return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_STATUS_NOT_ALLOWED", metadata=metadata)]
    if strategy.entry_filter_config.minimum_pattern_score is not None and (pattern_score is None or pattern_score < strategy.entry_filter_config.minimum_pattern_score):
        return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_SCORE_BELOW_MINIMUM", metadata=metadata)]
    if strategy.entry_filter_config.minimum_risk_reward is not None and (risk_reward is None or risk_reward < strategy.entry_filter_config.minimum_risk_reward):
        return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_REWARD_BELOW_MINIMUM", metadata=metadata)]
    action_type = StrategyActionType.ENTER_LONG if position_side == "LONG" else StrategyActionType.ENTER_SHORT
    quantity_override = strategy.entry_filter_config.quantity_override
    if quantity_override is not None:
        metadata["quantity_override"] = quantity_override
    return [StrategyAction(action_type, timestamp, reason="PATTERN_CONFIRMED", metadata=metadata, quantity=quantity_override)]

@dataclass(frozen=True)
class PatternStrategyBase:
    strategy_key: str
    strategy_name: str
    strategy_version: str = "v1"
    entry_filter_config: PatternEntryFilterConfig = field(default_factory=PatternEntryFilterConfig)

    def evaluate(self, candles_so_far: pd.DataFrame | list[dict[str, Any]], portfolio_state: dict[str, Any] | None = None) -> list[StrategyAction]:
        frame = candles_so_far if isinstance(candles_so_far, pd.DataFrame) else pd.DataFrame(candles_so_far)
        missing = [c for c in ("timestamp","open","high","low","close","volume") if c not in frame.columns]
        if missing or frame.empty:
            return []
        if not frame["timestamp"].is_monotonic_increasing:
            raise ValueError("candles must be sorted ascending by timestamp")
        event = self._latest_event(frame)
        if event is None:
            return []
        timestamp = getattr(event, "timestamp", frame.iloc[-1]["timestamp"])
        regime_context = _regime_context_from_portfolio_state(portfolio_state, timestamp)
        return _event_to_actions(self, event, timestamp, frame, regime_context)

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        frame = context.candles.iloc[: context.current_index + 1]
        return self.evaluate(frame, portfolio_state=context.portfolio_state)

    def _latest_event(self, frame: pd.DataFrame):
        raise NotImplementedError

    def _risk_plan(self, event: Any, frame: pd.DataFrame):
        raise NotImplementedError

    def _actions_from_cached_events(
        self,
        context: PatternEvaluationContext,
        events: list[Any],
    ) -> list[StrategyAction]:
        if not events:
            return []
        event = events[0]
        timestamp = getattr(event, "timestamp", context.candles.iloc[context.current_index]["timestamp"])
        return _event_to_actions(
            self,
            event,
            timestamp,
            context.candles.iloc[: context.current_index + 1],
            _regime_context_from_portfolio_state(context.portfolio_state, timestamp),
        )


def _score_metadata_from_event(event: Any) -> dict[str, Any]:
    return {
        "score_components": getattr(event, "score_components", {}),
        "score_component_sources": getattr(event, "score_component_sources", {}),
        "score_limitations": getattr(event, "score_limitations", ()),
        "score_calibration": getattr(event, "score_calibration", {}),
    }


def _raw_pattern_metadata(
    event: Any,
    direction: str,
    position_side: str,
    risk_plan: Any,
    pattern_status: str,
    pattern_score: Any,
    risk_reward: Any,
) -> dict[str, Any]:
    # Raw pattern strategies intentionally emit only a simple entry signal.
    # Canonical backtest runners must expand these signals through
    # build_pattern_trade_actions() before execution/accounting.
    return {
        "pattern_execution_path": PATTERN_EXECUTION_PATH_LEGACY_SIMPLE_ENTRY,
        "canonical_expansion_required": True,
        "pattern_event_id": getattr(event, "event_id", None),
        "event_id": getattr(event, "event_id", None),
        "pattern_type": getattr(event, "pattern_type", None),
        "pattern_direction": direction,
        "position_side": position_side,
        "pattern_status": pattern_status,
        "pattern_score": pattern_score,
        "executable_pattern_score": getattr(event, "executable_pattern_score", pattern_score),
        "diagnostic_pattern_score": getattr(event, "diagnostic_pattern_score", None),
        "risk_reward": risk_reward,
        "volume_ratio": getattr(event, "volume_ratio", None),
        "break_distance_atr": getattr(event, "break_distance_atr", None),
        "displacement_range_atr": getattr(event, "displacement_range_atr", None),
        "gap_size_atr": getattr(event, "gap_size_atr", None),
        "entry_reference": getattr(event, "entry_reference", None),
        "stop_reference": getattr(event, "stop_reference", None),
        "target_reference": getattr(event, "target_reference", None),
        "zone_mid": getattr(event, "zone_mid", None),
        "zone_low": getattr(event, "zone_low", None),
        "zone_high": getattr(event, "zone_high", None),
        "trendline_value": getattr(event, "trendline_value", None),
        "neckline": getattr(event, "neckline", None),
        "upper_boundary_value": getattr(event, "upper_boundary_value", None),
        "lower_boundary_value": getattr(event, "lower_boundary_value", None),
        "risk_plan": risk_plan,
        "risk_plan_status": _status_value(getattr(risk_plan, "status", None)),
        "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
        **_pattern_specific_risk_metadata(event, risk_plan),
        **_score_metadata_from_event(event),
    }


def _regime_context_from_portfolio_state(
    portfolio_state: dict[str, Any] | None,
    timestamp: Any,
) -> dict[str, Any] | None:
    if not isinstance(portfolio_state, dict):
        return None
    direct = portfolio_state.get("market_regime_context")
    if isinstance(direct, dict):
        return direct
    by_timestamp = portfolio_state.get("market_regime_by_timestamp")
    if isinstance(by_timestamp, dict):
        value = by_timestamp.get(timestamp)
        if isinstance(value, dict):
            return value
    regime_keys = {
        "market_regime",
        "volatility_regime",
        "liquidity_regime",
        "spread_regime",
        "trend_regime",
        "mean_reversion_regime",
        "session_tag",
        "weekday_tag",
    }
    context = {key: portfolio_state[key] for key in regime_keys if key in portfolio_state}
    return context or None


def _status_value(status: Any) -> str | None:
    if status is None:
        return None
    return str(status.value if hasattr(status, "value") else status)


def _pattern_specific_risk_metadata(event: Any, risk_plan: Any) -> dict[str, Any]:
    if getattr(event, "pattern_type", None) != "ADAM_AND_EVE_PATTERN":
        return {}
    structural_stop = getattr(risk_plan, "structural_stop", None)
    inferred_stop_mode = getattr(event, "stop_reference_mode", None)
    try:
        if structural_stop is not None:
            stop_value = float(structural_stop)
            eve_low = float(getattr(event, "eve_low_price"))
            wider_low = min(float(getattr(event, "adam_low_price")), eve_low)
            if stop_value == eve_low:
                inferred_stop_mode = "EVE_LOW"
            elif stop_value == wider_low:
                inferred_stop_mode = "WIDER_ADAM_EVE_LOW"
    except (TypeError, ValueError):
        pass
    return {
        "risk_stop_mode": inferred_stop_mode,
        "stop_reference_mode": getattr(event, "stop_reference_mode", None),
        "detector_reference_stop": getattr(event, "detector_reference_stop", None),
        "detector_reference_risk_reward": getattr(
            event,
            "detector_reference_risk_reward",
            None,
        ),
    }


@dataclass(frozen=True)
class FairValueGapStrategy(PatternStrategyBase):
    detector_config: FairValueGapConfig = FairValueGapConfig()
    risk_config: FairValueGapRiskExitConfig = FairValueGapRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("FAIR_VALUE_GAP", "FAIR_VALUE_GAP_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events = [e for e in detect_fair_value_gaps(frame, config=self.detector_config) if getattr(e, 'end_index', None) == len(frame)-1]
        return events[0] if events else None
    def _risk_plan(self, event, frame): return create_fair_value_gap_risk_exit_plan(event, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_fair_value_gap_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)

@dataclass(frozen=True)
class TrendlineBreakStrategy(PatternStrategyBase):
    detector_config: TrendlineBreakConfig = TrendlineBreakConfig(); risk_config: TrendlineBreakRiskExitConfig = TrendlineBreakRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("TRENDLINE_BREAK", "TRENDLINE_BREAK_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_trendline_breaks(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_trendline_break_risk_exit_plan(event, candles=frame, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_trendline_break_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)

@dataclass(frozen=True)
class OrderBlockStrategy(PatternStrategyBase):
    detector_config: OrderBlockConfig = OrderBlockConfig(); risk_config: OrderBlockRiskExitConfig = OrderBlockRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("ORDER_BLOCK", "ORDER_BLOCK_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_order_blocks(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_order_block_risk_exit_plan(event, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_order_block_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)

@dataclass(frozen=True)
class CupAndHandleStrategy(PatternStrategyBase):
    detector_config: CupAndHandleConfig = CupAndHandleConfig(); risk_config: CupAndHandleRiskExitConfig = CupAndHandleRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("CUP_AND_HANDLE", "CUP_AND_HANDLE_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_cup_and_handle_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_cup_and_handle_risk_exit_plan(event, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_cup_and_handle_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)

@dataclass(frozen=True)
class DiamondStrategy(PatternStrategyBase):
    detector_config: DiamondConfig = DiamondConfig(); risk_config: DiamondRiskExitConfig = DiamondRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("DIAMOND", "DIAMOND_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_diamond_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_diamond_risk_exit_plan(event, candles=frame, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_diamond_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)

@dataclass(frozen=True)
class AdamAndEveStrategy(PatternStrategyBase):
    detector_config: AdamAndEveConfig = AdamAndEveConfig(); risk_config: AdamAndEveRiskExitConfig = AdamAndEveRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("ADAM_AND_EVE", "ADAM_AND_EVE_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_adam_and_eve_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_adam_and_eve_risk_exit_plan(event, config=self.risk_config).risk_plan

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        events = detect_adam_and_eve_at_index(context, config=self.detector_config)
        return self._actions_from_cached_events(context, events)


def strategy_for_pattern(pattern: str, *, entry_filter_config: PatternEntryFilterConfig | None = None) -> PatternStrategyBase:
    key = pattern.upper()
    mapping: dict[str, Callable[[], PatternStrategyBase]] = {
        "FAIR_VALUE_GAP": FairValueGapStrategy,
        "TRENDLINE_BREAK": TrendlineBreakStrategy,
        "ORDER_BLOCK": OrderBlockStrategy,
        "CUP_AND_HANDLE": CupAndHandleStrategy,
        "DIAMOND": DiamondStrategy,
        "ADAM_AND_EVE": AdamAndEveStrategy,
    }
    if key not in mapping:
        raise ValueError(f"unsupported pattern: {pattern}")
    strategy = mapping[key]()
    if entry_filter_config is None:
        return strategy
    return type(strategy)(entry_filter_config=entry_filter_config)
