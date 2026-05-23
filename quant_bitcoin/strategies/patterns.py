from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from quant_bitcoin.patterns import (
    AdamAndEveConfig, AdamAndEveRiskExitConfig, CupAndHandleConfig, CupAndHandleRiskExitConfig,
    DiamondConfig, DiamondRiskExitConfig, FairValueGapConfig, FairValueGapRiskExitConfig,
    OrderBlockConfig, OrderBlockRiskExitConfig, TrendlineBreakConfig, TrendlineBreakRiskExitConfig,
    create_adam_and_eve_risk_exit_plan, create_cup_and_handle_risk_exit_plan, create_diamond_risk_exit_plan,
    create_fair_value_gap_risk_exit_plan, create_order_block_risk_exit_plan, create_trendline_break_risk_exit_plan,
    detect_adam_and_eve_patterns, detect_cup_and_handle_patterns, detect_diamond_patterns,
    detect_fair_value_gaps, detect_order_blocks, detect_trendline_breaks,
)
from quant_bitcoin.backtesting.fvg_detection_cache import IndicatorCache, PatternEvaluationContext, detect_fair_value_gap_at_index
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType



@dataclass(frozen=True)
class PatternEntryFilterConfig:
    allowed_statuses: tuple[str, ...] = ("VALID",)
    minimum_pattern_score: float | None = None
    minimum_risk_reward: float | None = None
    quantity_override: float | None = None


def pattern_direction_to_position_side(direction: str) -> str | None:
    value = str(direction).upper()
    if value == "BULLISH":
        return "LONG"
    if value == "BEARISH":
        return "SHORT"
    return None


@dataclass(frozen=True)
class PatternStrategyBase:
    strategy_key: str
    strategy_name: str
    strategy_version: str = "v1"
    entry_filter_config: PatternEntryFilterConfig = field(default_factory=PatternEntryFilterConfig)

    def evaluate(self, candles_so_far: pd.DataFrame | list[dict[str, Any]], portfolio_state: dict[str, Any] | None = None) -> list[StrategyAction]:
        frame = candles_so_far.copy(deep=True) if isinstance(candles_so_far, pd.DataFrame) else pd.DataFrame(list(candles_so_far))
        missing = [c for c in ("timestamp","open","high","low","close","volume") if c not in frame.columns]
        if missing or frame.empty:
            return []
        if not frame["timestamp"].is_monotonic_increasing:
            raise ValueError("candles must be sorted ascending by timestamp")
        event = self._latest_event(frame)
        if event is None:
            return []
        direction = str(getattr(event, "direction", "")).upper()
        timestamp = getattr(event, "timestamp", frame.iloc[-1]["timestamp"])
        position_side = pattern_direction_to_position_side(direction)
        if position_side is None:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="UNSUPPORTED_DIRECTION", metadata={"pattern_event_id": getattr(event, 'event_id', None), "pattern_type": getattr(event, 'pattern_type', None), "pattern_direction": direction})]
        pattern_status = str(getattr(event, "pattern_status", "")).upper()
        pattern_score = getattr(event, "pattern_score", None)
        risk_reward = getattr(event, "risk_reward", None)
        planned = self._risk_plan(event, frame)
        metadata = {
            "pattern_event_id": getattr(event, 'event_id', None),
            "pattern_type": getattr(event, 'pattern_type', None),
            "pattern_direction": direction,
            "position_side": position_side,
            "pattern_status": pattern_status,
            "pattern_score": pattern_score,
            "risk_reward": risk_reward,
            "entry_reference": getattr(event, 'entry_reference', None),
            "stop_reference": getattr(event, 'stop_reference', None),
            "target_reference": getattr(event, 'target_reference', None),
            "risk_plan": planned,
        }
        if planned is None or planned.status != RiskExitPlanStatus.VALID:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_PLAN_INVALID", metadata=metadata)]
        if pattern_status not in self.entry_filter_config.allowed_statuses:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_STATUS_NOT_ALLOWED", metadata=metadata)]
        if self.entry_filter_config.minimum_pattern_score is not None and (pattern_score is None or pattern_score < self.entry_filter_config.minimum_pattern_score):
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_SCORE_BELOW_MINIMUM", metadata=metadata)]
        if self.entry_filter_config.minimum_risk_reward is not None and (risk_reward is None or risk_reward < self.entry_filter_config.minimum_risk_reward):
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_REWARD_BELOW_MINIMUM", metadata=metadata)]
        action_type = StrategyActionType.ENTER_LONG if position_side == "LONG" else StrategyActionType.ENTER_SHORT
        quantity_override = self.entry_filter_config.quantity_override
        if quantity_override is not None:
            metadata["quantity_override"] = quantity_override
        return [StrategyAction(action_type, timestamp, reason="PATTERN_CONFIRMED", metadata=metadata, quantity=quantity_override)]

    def evaluate_at(self, context: PatternEvaluationContext) -> list[StrategyAction]:
        frame = context.candles.iloc[: context.current_index + 1]
        return self.evaluate(frame, portfolio_state=context.portfolio_state)

    def _latest_event(self, frame: pd.DataFrame):
        raise NotImplementedError

    def _risk_plan(self, event: Any, frame: pd.DataFrame):
        raise NotImplementedError


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
        if not events:
            return []
        event = events[0]
        direction = str(getattr(event, "direction", "")).upper()
        timestamp = getattr(event, "timestamp", context.candles.iloc[context.current_index]["timestamp"])
        position_side = pattern_direction_to_position_side(direction)
        if position_side is None:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="UNSUPPORTED_DIRECTION", metadata={"pattern_event_id": getattr(event, "event_id", None), "pattern_type": getattr(event, "pattern_type", None), "pattern_direction": direction})]
        pattern_status = str(getattr(event, "pattern_status", "")).upper()
        pattern_score = getattr(event, "pattern_score", None)
        risk_reward = getattr(event, "risk_reward", None)
        planned = self._risk_plan(event, context.candles.iloc[: context.current_index + 1])
        metadata = {"pattern_event_id": getattr(event, "event_id", None), "pattern_type": getattr(event, "pattern_type", None), "pattern_direction": direction, "position_side": position_side, "pattern_status": pattern_status, "pattern_score": pattern_score, "risk_reward": risk_reward, "entry_reference": getattr(event, "entry_reference", None), "stop_reference": getattr(event, "stop_reference", None), "target_reference": getattr(event, "target_reference", None), "risk_plan": planned}
        if planned is None or planned.status != RiskExitPlanStatus.VALID:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_PLAN_INVALID", metadata=metadata)]
        if pattern_status not in self.entry_filter_config.allowed_statuses:
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_STATUS_NOT_ALLOWED", metadata=metadata)]
        if self.entry_filter_config.minimum_pattern_score is not None and (pattern_score is None or pattern_score < self.entry_filter_config.minimum_pattern_score):
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="PATTERN_SCORE_BELOW_MINIMUM", metadata=metadata)]
        if self.entry_filter_config.minimum_risk_reward is not None and (risk_reward is None or risk_reward < self.entry_filter_config.minimum_risk_reward):
            return [StrategyAction(StrategyActionType.SKIP, timestamp, reason="RISK_REWARD_BELOW_MINIMUM", metadata=metadata)]
        action_type = StrategyActionType.ENTER_LONG if position_side == "LONG" else StrategyActionType.ENTER_SHORT
        quantity_override = self.entry_filter_config.quantity_override
        if quantity_override is not None:
            metadata["quantity_override"] = quantity_override
        return [StrategyAction(action_type, timestamp, reason="PATTERN_CONFIRMED", metadata=metadata, quantity=quantity_override)]

@dataclass(frozen=True)
class TrendlineBreakStrategy(PatternStrategyBase):
    detector_config: TrendlineBreakConfig = TrendlineBreakConfig(); risk_config: TrendlineBreakRiskExitConfig = TrendlineBreakRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("TRENDLINE_BREAK", "TRENDLINE_BREAK_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_trendline_breaks(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_trendline_break_risk_exit_plan(event, candles=frame, config=self.risk_config).risk_plan

@dataclass(frozen=True)
class OrderBlockStrategy(PatternStrategyBase):
    detector_config: OrderBlockConfig = OrderBlockConfig(); risk_config: OrderBlockRiskExitConfig = OrderBlockRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("ORDER_BLOCK", "ORDER_BLOCK_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_order_blocks(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_order_block_risk_exit_plan(event, config=self.risk_config).risk_plan

@dataclass(frozen=True)
class CupAndHandleStrategy(PatternStrategyBase):
    detector_config: CupAndHandleConfig = CupAndHandleConfig(); risk_config: CupAndHandleRiskExitConfig = CupAndHandleRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("CUP_AND_HANDLE", "CUP_AND_HANDLE_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_cup_and_handle_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_cup_and_handle_risk_exit_plan(event, config=self.risk_config).risk_plan

@dataclass(frozen=True)
class DiamondStrategy(PatternStrategyBase):
    detector_config: DiamondConfig = DiamondConfig(); risk_config: DiamondRiskExitConfig = DiamondRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("DIAMOND", "DIAMOND_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_diamond_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_diamond_risk_exit_plan(event, config=self.risk_config).risk_plan

@dataclass(frozen=True)
class AdamAndEveStrategy(PatternStrategyBase):
    detector_config: AdamAndEveConfig = AdamAndEveConfig(); risk_config: AdamAndEveRiskExitConfig = AdamAndEveRiskExitConfig()
    def __init__(self, entry_filter_config: PatternEntryFilterConfig = PatternEntryFilterConfig()): super().__init__("ADAM_AND_EVE", "ADAM_AND_EVE_PATTERN_STRATEGY", entry_filter_config=entry_filter_config)
    def _latest_event(self, frame):
        events=[e for e in detect_adam_and_eve_patterns(frame, config=self.detector_config) if getattr(e,'end_index',None)==len(frame)-1]; return events[0] if events else None
    def _risk_plan(self, event, frame): return create_adam_and_eve_risk_exit_plan(event, config=self.risk_config).risk_plan


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
