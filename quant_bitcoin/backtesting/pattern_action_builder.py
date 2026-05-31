from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.costs import (
    LiquidityRole,
    TransactionCostConfig,
    effective_slippage_bps,
    is_zero_transaction_cost_config,
)
from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES
from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, detect_intrabar_touches, resolve_intrabar_decision
from quant_bitcoin.backtesting.pattern_invalidation import (
    PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
    pattern_soft_invalidation_for_event,
)
from quant_bitcoin.backtesting.sizing import SizingRiskSource
from quant_bitcoin.indicators.volume_ratio import (
    VolumeInputMode,
    VolumeRatioBaselineMode,
    VolumeRatioConfig,
    calculate_volume_ratio,
)
from quant_bitcoin.patterns.entry_simulation import (
    PatternEntryConfig,
    PatternEntryMode,
    PatternEntryStatus,
    create_entry_plan_from_event,
    simulate_pattern_entry,
)
from quant_bitcoin.patterns.fvg_channel import (
    FvgChannelConfig,
    channel_id,
    channel_identity,
    detect_fvg_parallel_channel,
    simulate_channel_boundary_exit,
    simulate_channel_retest_entry,
)
from quant_bitcoin.patterns.order_block import OrderBlockConfig, detect_order_blocks
from quant_bitcoin.risk.exit_plan import (
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    RiskExitTarget,
    RiskExitTargetSource,
    target_semantics_metadata,
)
from quant_bitcoin.risk.exit_simulation import (
    PatternExitEvent,
    PatternExitReason,
    SoftInvalidationRule,
    simulate_pattern_exit,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode

_UNSET = object()
PATTERN_EXECUTION_PATH_CANONICAL_FILL_AWARE = "CANONICAL_FILL_AWARE_ACTION_BUILDER"


@dataclass(frozen=True)
class CostAwareEntryFilterConfig:
    enabled: bool = False
    min_net_reward_bps: float = 20.0
    min_net_rr: float = 1.5
    transaction_cost_config: TransactionCostConfig | None = None
    liquidity_role: LiquidityRole = LiquidityRole.TAKER
    cost_profile_name: str | None = None


@dataclass(frozen=True)
class CloseVolumeEntryFilterConfig:
    enabled: bool = False
    window: int = 20
    minimum_volume_ratio: float = 2.0
    low_volume_ratio_threshold: float = 0.5
    applies_to_side: str = "ALL"
    baseline_mode: str = VolumeRatioBaselineMode.PRIOR_ONLY.value
    volume_input_mode: str = VolumeInputMode.BASE_VOLUME.value
    require_full_window: bool = True
    fail_closed_on_invalid: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "close_volume_entry_filter_config_v1",
            "enabled": bool(self.enabled),
            "window": int(self.window),
            "minimum_volume_ratio": float(self.minimum_volume_ratio),
            "low_volume_ratio_threshold": float(self.low_volume_ratio_threshold),
            "applies_to_side": str(self.applies_to_side).upper(),
            "applies_to_sides": _close_volume_filter_applies_to_sides(str(self.applies_to_side).upper()),
            "baseline_mode": str(self.baseline_mode).upper(),
            "volume_input_mode": str(self.volume_input_mode).upper(),
            "require_full_window": bool(self.require_full_window),
            "fail_closed_on_invalid": bool(self.fail_closed_on_invalid),
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class FvgOrderBlockConfluenceConfig:
    enabled: bool = False
    source: str = "local_entry_candles"
    local_break_mode: str = "break_previous_range"
    lookback_bars: int | None = 100
    mode: str = "zone_overlap"
    require_fresh: bool = False
    order_block_config: OrderBlockConfig | None = None

    def __post_init__(self) -> None:
        if _normalize_confluence_source(self.source) not in {"LOCAL_ENTRY_CANDLES", "HISTORICAL_DETECTOR"}:
            raise ValueError("source must be local_entry_candles or historical_detector")
        if _normalize_local_ob_break_mode(self.local_break_mode) not in {"BREAK_PREVIOUS_RANGE", "BREAK_PREVIOUS_BODY"}:
            raise ValueError("local_break_mode must be break_previous_range or break_previous_body")
        if self.lookback_bars is not None and int(self.lookback_bars) < 1:
            raise ValueError("lookback_bars must be at least 1 when supplied")
        if _normalize_confluence_mode(self.mode) not in {
            "ZONE_OVERLAP",
            "ENTRY_PRICE_INSIDE_OB",
            "FVG_MIDPOINT_INSIDE_OB",
        }:
            raise ValueError("mode must be zone_overlap, entry_price_inside_ob, or fvg_midpoint_inside_ob")

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "fvg_order_block_confluence_config_v1",
            "enabled": bool(self.enabled),
            "source": _normalize_confluence_source(self.source),
            "local_break_mode": _normalize_local_ob_break_mode(self.local_break_mode),
            "lookback_bars": None if self.lookback_bars is None else int(self.lookback_bars),
            "mode": _normalize_confluence_mode(self.mode),
            "require_fresh": bool(self.require_fresh),
            "scope": "offline_backtest_research_only",
            "default_behavior_preserved": not self.enabled,
        }


@dataclass(frozen=True)
class OrderBlockEntryVolumeFilterConfig:
    enabled: bool = False
    window: int = 20
    minimum_volume_ratio: float = 1.0
    baseline_mode: str = VolumeRatioBaselineMode.PRIOR_ONLY.value
    volume_input_mode: str = VolumeInputMode.BASE_VOLUME.value
    require_full_window: bool = True
    fail_closed_on_invalid: bool = True

    def __post_init__(self) -> None:
        if int(self.window) < 1:
            raise ValueError("window must be at least 1")
        if float(self.minimum_volume_ratio) < 0:
            raise ValueError("minimum_volume_ratio must be non-negative")

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "order_block_entry_volume_filter_config_v1",
            "enabled": bool(self.enabled),
            "window": int(self.window),
            "minimum_volume_ratio": float(self.minimum_volume_ratio),
            "baseline_mode": str(self.baseline_mode).upper(),
            "volume_input_mode": str(self.volume_input_mode).upper(),
            "require_full_window": bool(self.require_full_window),
            "fail_closed_on_invalid": bool(self.fail_closed_on_invalid),
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class OrderBlockMtfFilterConfig:
    enabled: bool = False
    timeframes: tuple[str, ...] = ("15m", "1h")
    require_all_timeframes: bool = True
    fail_closed_on_missing: bool = True
    order_block_config: OrderBlockConfig | None = None

    def __post_init__(self) -> None:
        normalized = tuple(_normalize_timeframe(value) for value in self.timeframes if str(value).strip())
        if not normalized:
            raise ValueError("timeframes must include at least one timeframe")
        object.__setattr__(self, "timeframes", normalized)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "order_block_mtf_filter_config_v1",
            "enabled": bool(self.enabled),
            "timeframes": list(self.timeframes),
            "require_all_timeframes": bool(self.require_all_timeframes),
            "fail_closed_on_missing": bool(self.fail_closed_on_missing),
            "context_source": "resampled_completed_base_candles",
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class OrderBlockRiskExitConfig:
    mode: str = "PREVIOUS_CANDLE_1R"
    fallback_on_unsupported_entry_mode: bool = True

    def __post_init__(self) -> None:
        normalized = _normalize_order_block_risk_exit_mode(self.mode)
        if normalized not in {"PREVIOUS_CANDLE_1R", "ZONE_STRUCTURAL_2R"}:
            raise ValueError("mode must be previous_candle_1r or zone_structural_2r")
        object.__setattr__(self, "mode", normalized)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "order_block_risk_exit_config_v1",
            "mode": self.mode,
            "enabled": self.mode == "PREVIOUS_CANDLE_1R",
            "fallback_on_unsupported_entry_mode": bool(self.fallback_on_unsupported_entry_mode),
            "supported_entry_modes": [PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value],
            "scope": "offline_backtest_research_only",
        }


def build_fvg_channel_trade_actions(
    event: Any,
    risk_plan: RiskExitPlan,
    channel_candles: pd.DataFrame | list[dict[str, Any]],
    future_candles: pd.DataFrame | list[dict[str, Any]],
    *,
    entry_action_timestamp: Any | None = None,
    position_side: str,
    entry_quantity: float | None = None,
    channel_config: FvgChannelConfig | None = None,
    seen_channel_ids: set[str] | None = None,
    channel_candidate_source: str = "fvg_event_expansion",
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    close_volume_entry_filter_config: CloseVolumeEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
) -> list[StrategyAction]:
    """Build FVG v2 channel-mode actions without ATR-derived stop/target prices."""

    config = channel_config or FvgChannelConfig(enabled=True)
    side = str(position_side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("position_side must be LONG or SHORT")

    base_metadata = {
        **_pattern_event_metadata(event, side, risk_plan),
        "channel_mode": "FVG_V2_PARALLEL_CHANNEL",
        "fvg_channel_mode_enabled": True,
        "atr_used_for_stop_or_target": False,
        "entry_quantity_source": "ACTION_OVERRIDE" if entry_quantity is not None else "ENGINE_CONFIG",
        "engine_sizing_allowed": entry_quantity is None,
        "channel_candidate_source": channel_candidate_source,
        "channel_scan_source": getattr(event, "channel_scan_source", channel_candidate_source),
    }
    channel = detect_fvg_parallel_channel(channel_candles, config)
    if channel is None:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="FVG_CHANNEL_NOT_FOUND",
                metadata={
                    **base_metadata,
                    "channel_rejection": {
                        "schema_version": "fvg_parallel_channel_rejection_v1",
                        "reason": "no valid upward parallel channel in configured window",
                        "window": config.window,
                        "tolerance": config.tolerance,
                    },
                },
            )
        ]

    identity = channel_identity(channel)
    stable_channel_id = channel_id(channel)
    channel_metadata = {
        "channel_id": stable_channel_id,
        "channel_identity": identity,
        "channel_geometry": channel.to_metadata(),
        "fvg_channel": channel.to_metadata(),
    }
    if seen_channel_ids is not None and stable_channel_id in seen_channel_ids:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="FVG_CHANNEL_DUPLICATE",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    "channel_duplicate": True,
                    "channel_skip_reason": "same channel geometry already generated a trade candidate",
                    "channel_seen_after_filled_candidate": True,
                },
            )
        ]

    entry = simulate_channel_retest_entry(channel, future_candles, config, context_candles=channel_candles)
    if entry is None:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="FVG_CHANNEL_RETEST_NOT_FILLED",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    "channel_duplicate": False,
                    "channel_newly_visible": True,
                    "entry_status": "NOT_FILLED",
                    "max_wait_bars": config.max_wait_bars,
                    "channel_seen_after_filled_candidate": False,
                },
            )
        ]
    if (entry.metadata or {}).get("pre_retest_stop_valid") is False:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.timestamp,
                quantity=0.0,
                reason="FVG_CHANNEL_PRE_RETEST_STOP_INVALID",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    **entry.metadata,
                    "channel_duplicate": False,
                    "channel_newly_visible": True,
                    "entry_status": "BLOCKED",
                    "skip_reason": "pre-retest candle stop is missing or invalid for the entry side",
                    "channel_seen_after_filled_candidate": False,
                },
            )
        ]

    order_block_confluence = _fvg_order_block_confluence_decision(
        event,
        position_side=entry.side.value,
        candles=_combine_candle_frames(channel_candles, future_candles),
        config=fvg_order_block_confluence_config,
        entry_price=entry.fill_price,
        entry_timestamp=entry.timestamp,
        fvg_zone_override=_channel_confluence_zone(event, entry),
    )
    if order_block_confluence.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.timestamp,
                quantity=0.0,
                reason="FVG_ORDER_BLOCK_CONFLUENCE_MISSING",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    **entry.metadata,
                    "channel_duplicate": False,
                    "channel_newly_visible": True,
                    "entry_status": "BLOCKED",
                    "skip_reason": "FVG entry candidate has no same-direction Order Block confluence",
                    "fvg_order_block_confluence": order_block_confluence,
                    "channel_seen_after_filled_candidate": False,
                },
            )
        ]

    close_volume_filter = _channel_close_volume_entry_filter_decision(
        entry,
        channel_candles,
        future_candles,
        close_volume_entry_filter_config,
    )
    if close_volume_filter.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.timestamp,
                quantity=0.0,
                reason="LOW_CLOSE_VOLUME_ENTRY_FILTER",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    **entry.metadata,
                    "channel_duplicate": False,
                    "channel_newly_visible": True,
                    "entry_status": "BLOCKED",
                    "skip_reason": "completed signal candle volume ratio is below the configured threshold",
                    "close_volume_entry_filter": close_volume_filter,
                    "channel_seen_after_filled_candidate": False,
                },
            )
        ]

    cost_filter = _channel_cost_aware_entry_filter_decision(
        entry,
        future_candles,
        cost_aware_entry_filter_config,
    )
    if cost_filter.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.timestamp,
                quantity=0.0,
                reason="COST_INFEASIBLE_TAKE_PROFIT",
                metadata={
                    **base_metadata,
                    **channel_metadata,
                    **entry.metadata,
                    "channel_duplicate": False,
                    "channel_newly_visible": True,
                    "entry_status": "BLOCKED",
                    "skip_reason": "intended take-profit target is not net-profitable after estimated round-trip costs",
                    "cost_aware_entry_filter": cost_filter,
                    "channel_seen_after_filled_candidate": False,
                },
            )
        ]
    if seen_channel_ids is not None:
        seen_channel_ids.add(stable_channel_id)

    entry_action_type = StrategyActionType.ENTER_LONG if entry.side.value == "LONG" else StrategyActionType.ENTER_SHORT
    event_metadata = {
        **base_metadata,
        **channel_metadata,
        **entry.metadata,
        "channel_id": stable_channel_id,
        "channel_identity": identity,
        "channel_duplicate": False,
        "channel_newly_visible": True,
        "channel_seen_after_filled_candidate": True,
        "entry_status": "FILLED",
        "entry_price": entry.fill_price,
        "entry_reference": entry.fill_price,
        "risk_per_unit": abs(entry.fill_price - entry.stop_price),
        "requested_price": entry.fill_price,
        "fill_price": entry.fill_price,
        "fill_timestamp": entry.timestamp,
        "fill_candle_index": entry.candle_index,
        "bars_waited": max(0, entry.candle_index - channel.window_end_index),
        "pattern_entry_policy": {
            "schema_version": "pattern_entry_policy_v1",
            "entry_mode": "FVG_V2_PARALLEL_CHANNEL_RETEST",
            "fill_assumption": "CHANNEL_RETEST_CONFIRMATION_CLOSE",
            "fill_price_source": "channel_retest_confirmation_close",
            "entry_trigger": entry.metadata["entry_trigger"],
            "requested_price": entry.fill_price,
            "entry_status": "FILLED",
            "max_wait_bars": config.max_wait_bars,
            "contract": "requested_price is the channel retest confirmation close; stop and target are dynamic channel boundaries and do not use ATR.",
            "target_price_source": entry.metadata.get("target_price_source"),
        },
        "target_semantics": {
            "schema_version": "channel_target_semantics_v1",
            "target_source": "FVG_V2_CHANNEL_WIDTH_PROJECTION",
            "target_price_source": entry.metadata.get("target_price_source"),
            "channel_target_policy": entry.metadata.get("channel_target_policy"),
            "channel_width_at_entry": entry.metadata.get("channel_width_at_entry"),
            "projected_channel_width_target": entry.metadata.get("projected_channel_width_target"),
            "opposite_boundary_target_price": entry.metadata.get("opposite_boundary_target_price"),
            "line_stop_price": entry.stop_price,
            "line_target_price": entry.target_price,
            "atr_used_for_stop_or_target": False,
        },
        "close_volume_entry_filter": close_volume_filter,
        "fvg_order_block_confluence": order_block_confluence,
        "cost_aware_entry_filter": cost_filter,
        "sizing_risk_source": SizingRiskSource.FILL_ADJUSTED.value,
    }
    actions = [
        StrategyAction(
            action_type=entry_action_type,
            timestamp=entry.timestamp,
            quantity=entry_quantity,
            reason="FVG_CHANNEL_RETEST_CONFIRMED",
            metadata=event_metadata,
            requested_price=entry.fill_price,
        )
    ]

    exit_event = simulate_channel_boundary_exit(
        channel,
        entry,
        future_candles,
        allow_same_candle_exit=config.allow_same_candle_exit,
    )
    if exit_event is not None:
        final_exit_type = StrategyActionType.EXIT_LONG if entry.side.value == "LONG" else StrategyActionType.EXIT_SHORT
        exit_metadata = {
            **event_metadata,
            "exit_reason": exit_event.reason.value,
            "target_name": exit_event.target_name,
            "stop_price": exit_event.stop_price,
            "exit_price": exit_event.price,
            "quantity_ratio": 1.0,
            "action_quantity_ratio": 1.0,
            "remaining_quantity_ratio": 0.0,
            "quantity_mode": StrategyQuantityMode.POSITION_RATIO.value,
            "exit_metadata": dict(exit_event.metadata or {}),
            **(exit_event.metadata or {}),
        }
        realized_r = _channel_realized_r(entry.side.value, entry.fill_price, entry.stop_price, exit_event.price)
        if realized_r is not None:
            exit_metadata["realized_r_multiple"] = realized_r
        actions.append(
            StrategyAction(
                action_type=final_exit_type,
                timestamp=exit_event.timestamp,
                quantity=1.0,
                reason=exit_event.reason.value,
                metadata=exit_metadata,
                requested_price=exit_event.price,
                quantity_mode=StrategyQuantityMode.POSITION_RATIO,
            )
        )
    return actions


def build_pattern_trade_actions(
    event: Any,
    risk_plan: RiskExitPlan,
    future_candles: pd.DataFrame | list[dict[str, Any]],
    *,
    entry_action_timestamp: Any | None = None,
    confirmation_candle: dict[str, Any] | pd.Series | None = None,
    position_side: str,
    entry_quantity: float | None = None,
    soft_invalidation: SoftInvalidationRule | None = None,
    entry_config: PatternEntryConfig | None = None,
    entry_mode: PatternEntryMode = PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
    entry_custom_price: float | None = None,
    intrabar_policy_config: IntrabarPolicyConfig | None = None,
    max_wait_bars: int | None = None,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
    order_block_entry_volume_filter_config: OrderBlockEntryVolumeFilterConfig | None = None,
    order_block_mtf_filter_config: OrderBlockMtfFilterConfig | None = None,
    order_block_risk_exit_config: OrderBlockRiskExitConfig | None = None,
    context_candles: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> list[StrategyAction]:
    side = str(position_side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("position_side must be LONG or SHORT")

    risk_plan_status = getattr(risk_plan, "status", None)
    if risk_plan_status != RiskExitPlanStatus.VALID:
        invalid_reason = (
            "LIQUIDITY_SWEEP_STOP_INVALID"
            if _is_liquidity_sweep_event(event)
            else "RISK_PLAN_INVALID"
        )
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason=invalid_reason,
                metadata={
                    **_pattern_event_metadata(event, side, risk_plan),
                    "risk_plan_status": _status_value(risk_plan_status),
                    "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
                },
            )
        ]

    frame = future_candles.copy(deep=False) if isinstance(future_candles, pd.DataFrame) else pd.DataFrame(future_candles)
    if "open" not in frame.columns and "close" in frame.columns:
        frame["open"] = frame["close"]
    for col in ("timestamp", "open", "high", "low", "close"):
        if col not in frame.columns:
            frame[col] = pd.Series(dtype="float64") if col != "timestamp" else pd.Series(dtype="object")
    frame = frame[["timestamp", "open", "high", "low", "close"]]
    if confirmation_candle is None:
        confirmation_candle = {
            "timestamp": entry_action_timestamp,
            "open": risk_plan.entry_price,
            "high": risk_plan.entry_price,
            "low": risk_plan.entry_price,
            "close": risk_plan.entry_price,
        }
    plan = create_entry_plan_from_event(
        event,
        entry_mode,
        side,
        custom_price=entry_custom_price,
        max_wait_bars=max_wait_bars if max_wait_bars is not None else (entry_config.max_wait_bars if entry_config else None),
    )
    if entry_config is not None:
        plan = plan.__class__(**{**plan.__dict__, "config": entry_config})
    entry = simulate_pattern_entry(plan, confirmation_candle, frame)

    event_metadata = {
        **_pattern_event_metadata(event, side, risk_plan),
        "entry_price": risk_plan.entry_price,
        "entry_reference": risk_plan.entry_price,
        "risk_per_unit": risk_plan.risk_per_unit,
        "entry_mode": plan.mode.value,
        "entry_trigger": entry.entry_trigger,
        "fill_assumption": _fill_assumption(plan.mode),
        "fill_price_source": _fill_price_source(plan.mode),
        "confirmation_close": _candle_value(confirmation_candle, "close"),
        "entry_custom_price": entry_custom_price,
        "entry_quantity_source": "ACTION_OVERRIDE" if entry_quantity is not None else "ENGINE_CONFIG",
        "engine_sizing_allowed": entry_quantity is None,
        "sizing_risk_source": (
            SizingRiskSource.ACTION_OVERRIDE.value
            if entry_quantity is not None
            else SizingRiskSource.ORIGINAL_REFERENCE.value
        ),
    }
    entry_policy = _entry_policy_metadata(
        event=event,
        plan=plan,
        entry=entry,
        entry_reference=risk_plan.entry_price,
        requested_price=entry.fill_price,
        confirmation_close=_candle_value(confirmation_candle, "close"),
        fill_assumption=event_metadata["fill_assumption"],
        fill_price_source=event_metadata["fill_price_source"],
    )
    event_metadata["pattern_entry_policy"] = entry_policy
    event_metadata["pattern_entry_policy_schema_version"] = "pattern_entry_policy_v1"
    if entry_quantity is not None:
        event_metadata["raw_action_quantity"] = entry_quantity
        event_metadata["pattern_quantity_override"] = entry_quantity
    entry_action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT

    if entry.status != PatternEntryStatus.FILLED:
        if entry.status == PatternEntryStatus.INVALID:
            skip_reason = "ENTRY_MODE_INVALID"
        elif _is_liquidity_sweep_event(event):
            skip_reason = "LIQUIDITY_SWEEP_RETEST_NOT_FILLED"
        else:
            skip_reason = "ENTRY_NOT_FILLED"
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason=skip_reason,
            metadata={
                **event_metadata,
                "entry_status": entry.status.value,
                "bars_waited": entry.bars_waited,
                "reason": entry.reason,
                "touch_timestamp": entry.touch_timestamp,
                "touch_candle_index": entry.touch_candle_index,
                "reaction_timestamp": entry.reaction_timestamp,
                "reaction_candle_index": entry.reaction_candle_index,
            },
            )
        ]

    order_block_confluence = _fvg_order_block_confluence_decision(
        event,
        position_side=side,
        candles=_combine_candle_frames(context_candles, frame),
        config=fvg_order_block_confluence_config,
        entry_price=entry.fill_price,
        entry_timestamp=entry.fill_timestamp,
    )
    if order_block_confluence.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.fill_timestamp,
                quantity=0.0,
                reason="FVG_ORDER_BLOCK_CONFLUENCE_MISSING",
                metadata={
                    **event_metadata,
                    "entry_status": entry.status.value,
                    "fill_price": entry.fill_price,
                    "fill_timestamp": entry.fill_timestamp,
                    "fill_candle_index": entry.fill_candle_index,
                    "bars_waited": entry.bars_waited,
                    "skip_reason": "FVG entry candidate has no same-direction Order Block confluence",
                    "fvg_order_block_confluence": order_block_confluence,
                },
            )
        ]
    if order_block_confluence:
        event_metadata["fvg_order_block_confluence"] = order_block_confluence

    order_block_entry_volume = _order_block_entry_volume_filter_decision(
        event,
        entry,
        _combine_candle_frames(context_candles, frame),
        order_block_entry_volume_filter_config,
    )
    if order_block_entry_volume.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.fill_timestamp,
                quantity=0.0,
                reason="ORDER_BLOCK_ENTRY_VOLUME_FILTER",
                metadata={
                    **event_metadata,
                    "entry_status": entry.status.value,
                    "fill_price": entry.fill_price,
                    "fill_timestamp": entry.fill_timestamp,
                    "fill_candle_index": entry.fill_candle_index,
                    "bars_waited": entry.bars_waited,
                    "skip_reason": "Order Block entry candle volume ratio is below the configured threshold",
                    "order_block_entry_volume_filter": order_block_entry_volume,
                },
            )
        ]
    if order_block_entry_volume:
        event_metadata["order_block_entry_volume_filter"] = order_block_entry_volume

    order_block_mtf = _order_block_mtf_filter_decision(
        event,
        position_side=side,
        candles=_combine_candle_frames(context_candles, frame),
        config=order_block_mtf_filter_config,
        entry_timestamp=entry.fill_timestamp,
    )
    if order_block_mtf.get("blocked"):
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.fill_timestamp,
                quantity=0.0,
                reason="ORDER_BLOCK_MTF_FILTER",
                metadata={
                    **event_metadata,
                    "entry_status": entry.status.value,
                    "fill_price": entry.fill_price,
                    "fill_timestamp": entry.fill_timestamp,
                    "fill_candle_index": entry.fill_candle_index,
                    "bars_waited": entry.bars_waited,
                    "skip_reason": "Order Block entry lacks required same-direction higher-timeframe confirmation",
                    "order_block_mtf_filter": order_block_mtf,
                },
            )
        ]
    if order_block_mtf:
        event_metadata["order_block_mtf_filter"] = order_block_mtf

    effective_risk_plan = risk_plan
    order_block_risk_exit = _order_block_risk_exit_decision(
        event,
        risk_plan,
        entry,
        _combine_candle_frames(context_candles, frame),
        order_block_risk_exit_config,
    )
    if order_block_risk_exit:
        event_metadata["order_block_risk_exit"] = order_block_risk_exit["metadata"]
        if order_block_risk_exit["metadata"].get("blocked"):
            return [
                StrategyAction(
                    action_type=StrategyActionType.SKIP,
                    timestamp=entry.fill_timestamp,
                    quantity=0.0,
                    reason="ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                    metadata={
                        **event_metadata,
                        "entry_status": entry.status.value,
                        "fill_price": entry.fill_price,
                        "fill_timestamp": entry.fill_timestamp,
                        "fill_candle_index": entry.fill_candle_index,
                        "bars_waited": entry.bars_waited,
                        "skip_reason": "Order Block previous/current candle stop and target could not be computed",
                    },
                )
            ]
        effective_risk_plan = order_block_risk_exit.get("risk_plan") or risk_plan

    aligned_risk_plan = _align_risk_plan_to_fill_price(effective_risk_plan, entry.fill_price)
    aligned_status = getattr(aligned_risk_plan, "status", None)
    if aligned_status != RiskExitPlanStatus.VALID:
        invalid_metadata = _metadata_with_aligned_risk_plan(event_metadata, effective_risk_plan, aligned_risk_plan)
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="RISK_PLAN_INVALID_AFTER_FILL",
                metadata={
                    **invalid_metadata,
                    "entry_status": entry.status.value,
                    "fill_price": entry.fill_price,
                    "fill_timestamp": entry.fill_timestamp,
                    "fill_candle_index": entry.fill_candle_index,
                    "bars_waited": entry.bars_waited,
                    "risk_plan_status": _status_value(aligned_status),
                    "risk_plan_reasons": tuple(getattr(aligned_risk_plan, "reasons", ()) or ()),
                    "risk_plan_aligned_to_fill": True,
                },
            )
        ]

    cost_filter = _cost_aware_entry_filter_decision(
        aligned_risk_plan,
        frame,
        entry.fill_candle_index,
        cost_aware_entry_filter_config,
    )
    if cost_filter:
        event_metadata["cost_aware_entry_filter"] = cost_filter
        if cost_filter.get("blocked"):
            cost_block_reason = (
                "LIQUIDITY_SWEEP_COST_AWARE_RR_REJECTED"
                if _is_liquidity_sweep_event(event)
                else "COST_INFEASIBLE_NET_RR"
            )
            return [
                StrategyAction(
                    action_type=StrategyActionType.SKIP,
                    timestamp=entry.fill_timestamp,
                    quantity=0.0,
                    reason=cost_block_reason,
                    metadata={
                        **_metadata_with_aligned_risk_plan(event_metadata, effective_risk_plan, aligned_risk_plan),
                        "entry_status": entry.status.value,
                        "fill_price": entry.fill_price,
                        "fill_timestamp": entry.fill_timestamp,
                        "fill_candle_index": entry.fill_candle_index,
                        "bars_waited": entry.bars_waited,
                        "cost_aware_entry_filter": cost_filter,
                    },
                )
            ]

    active_soft_invalidation, pattern_soft_invalidation_metadata = _resolve_pattern_soft_invalidation(
        event,
        aligned_risk_plan,
        soft_invalidation,
    )
    event_metadata["pattern_soft_invalidation"] = pattern_soft_invalidation_metadata
    event_metadata["pattern_soft_invalidation_schema_version"] = PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION

    entry_filled_on_first_candle = _entry_fill_is_first_future_candle(frame, entry.fill_candle_index, entry.fill_timestamp)
    combined_decision_metadata = _combined_entry_exit_metadata(
        aligned_risk_plan,
        frame,
        entry.fill_candle_index,
        intrabar_policy_config,
        entry_filled_on_first_candle=entry_filled_on_first_candle,
    )
    if combined_decision_metadata.get("skipped"):
        skip_metadata = {
            **event_metadata,
            **_metadata_with_aligned_risk_plan(event_metadata, effective_risk_plan, aligned_risk_plan),
            "entry_status": entry.status.value,
            "fill_price": entry.fill_price,
            "fill_timestamp": entry.fill_timestamp,
            "fill_candle_index": entry.fill_candle_index,
            "bars_waited": entry.bars_waited,
            "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
            "combined_intrabar_decision": combined_decision_metadata,
        }
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.fill_timestamp,
                quantity=0.0,
                reason="ENTRY_EXIT_AMBIGUOUS",
                metadata=skip_metadata,
            )
        ]

    event_metadata = _metadata_with_aligned_risk_plan(event_metadata, effective_risk_plan, aligned_risk_plan)
    if combined_decision_metadata:
        event_metadata["combined_intrabar_decision"] = combined_decision_metadata
    actions: list[StrategyAction] = [
        StrategyAction(
            action_type=entry_action_type,
            timestamp=entry.fill_timestamp,
            quantity=entry_quantity,
            reason="PATTERN_CONFIRMED",
            metadata={
                **event_metadata,
                "requested_price": entry.fill_price,
                "fill_price": entry.fill_price,
                "fill_timestamp": entry.fill_timestamp,
                "fill_candle_index": entry.fill_candle_index,
                "bars_waited": entry.bars_waited,
                "touch_timestamp": entry.touch_timestamp,
                "touch_candle_index": entry.touch_candle_index,
                "reaction_timestamp": entry.reaction_timestamp,
                "reaction_candle_index": entry.reaction_candle_index,
                "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
            },
            requested_price=entry.fill_price,
        )
    ]

    start = 0 if entry.fill_candle_index is None else entry.fill_candle_index
    simulation = simulate_pattern_exit(
        aligned_risk_plan,
        frame.iloc[start:],
        soft_invalidation=active_soft_invalidation,
        intrabar_policy_config=intrabar_policy_config,
        entry_filled_on_first_candle=entry_filled_on_first_candle,
    )
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, aligned_risk_plan, side, event_metadata))
    return actions


def _cost_aware_entry_filter_decision(
    risk_plan: RiskExitPlan,
    frame: pd.DataFrame,
    fill_candle_index: int | None,
    config: CostAwareEntryFilterConfig | None,
) -> dict[str, Any]:
    if config is None or not config.enabled:
        return {}

    entry_price = _positive_float(risk_plan.entry_price)
    stop_price = _positive_float(risk_plan.stop_price)
    if entry_price is None or stop_price is None or not risk_plan.targets:
        return {
            "schema_version": "cost_aware_entry_filter_v1",
            "enabled": True,
            "blocked": True,
            "block_reason": "COST_FILTER_INVALID_RISK_PLAN",
        }

    direction = _coerce_direction(risk_plan.direction)
    target_price = float(risk_plan.targets[0].price)
    if direction == RiskExitDirection.LONG:
        gross_reward_bps = ((target_price - entry_price) / entry_price) * 10_000.0
        gross_risk_bps = ((entry_price - stop_price) / entry_price) * 10_000.0
    else:
        gross_reward_bps = ((entry_price - target_price) / entry_price) * 10_000.0
        gross_risk_bps = ((stop_price - entry_price) / entry_price) * 10_000.0

    volatility_bps = _entry_candle_volatility_bps(frame, fill_candle_index)
    cost_config = config.transaction_cost_config or TransactionCostConfig()
    fee_bps = cost_config.maker_fee_bps if config.liquidity_role is LiquidityRole.MAKER else cost_config.taker_fee_bps
    slippage_bps = effective_slippage_bps(cost_config, volatility_bps)
    one_side_cost_bps = fee_bps + cost_config.spread_bps + slippage_bps
    round_trip_cost_bps = 2.0 * one_side_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    blocked = (
        gross_reward_bps <= 0
        or gross_risk_bps <= 0
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
        "gross_reward_bps": gross_reward_bps,
        "gross_risk_bps": gross_risk_bps,
        "estimated_one_side_cost_bps": one_side_cost_bps,
        "estimated_round_trip_cost_bps": round_trip_cost_bps,
        "net_reward_bps": net_reward_bps,
        "net_risk_bps": net_risk_bps,
        "net_rr": net_rr,
        "fee_bps": fee_bps,
        "spread_bps": cost_config.spread_bps,
        "slippage_bps": slippage_bps,
        "effective_slippage_bps": slippage_bps,
        "volatility_bps": volatility_bps,
        "cost_profile_name": config.cost_profile_name or _cost_profile_name(cost_config),
        "liquidity_role": config.liquidity_role.value,
    }


def _channel_cost_aware_entry_filter_decision(
    entry: Any,
    future_candles: pd.DataFrame | list[dict[str, Any]],
    config: CostAwareEntryFilterConfig | None,
) -> dict[str, Any]:
    if config is None:
        return {}

    cost_config = config.transaction_cost_config or TransactionCostConfig()
    auto_enabled = not is_zero_transaction_cost_config(cost_config)
    if not config.enabled and not auto_enabled:
        return {}

    entry_price = _positive_float(getattr(entry, "fill_price", None))
    stop_price = _positive_float(getattr(entry, "stop_price", None))
    target_price = _positive_float(getattr(entry, "target_price", None))
    if entry_price is None or stop_price is None or target_price is None:
        return {
            "schema_version": "cost_aware_entry_filter_v1",
            "enabled": True,
            "blocked": True,
            "block_reason": "COST_FILTER_INVALID_CHANNEL_ENTRY",
        }

    side = str(getattr(getattr(entry, "side", None), "value", getattr(entry, "side", ""))).upper()
    if side == "LONG":
        gross_reward_bps = ((target_price - entry_price) / entry_price) * 10_000.0
        gross_risk_bps = ((entry_price - stop_price) / entry_price) * 10_000.0
    elif side == "SHORT":
        gross_reward_bps = ((entry_price - target_price) / entry_price) * 10_000.0
        gross_risk_bps = ((stop_price - entry_price) / entry_price) * 10_000.0
    else:
        return {
            "schema_version": "cost_aware_entry_filter_v1",
            "enabled": True,
            "blocked": True,
            "block_reason": "COST_FILTER_INVALID_CHANNEL_SIDE",
        }

    volatility_bps = _channel_entry_candle_volatility_bps(future_candles, getattr(entry, "candle_index", None))
    fee_bps = cost_config.maker_fee_bps if config.liquidity_role is LiquidityRole.MAKER else cost_config.taker_fee_bps
    slippage_bps = effective_slippage_bps(cost_config, volatility_bps)
    one_side_cost_bps = fee_bps + cost_config.spread_bps + slippage_bps
    round_trip_cost_bps = 2.0 * one_side_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    min_net_reward_bps = float(config.min_net_reward_bps if config.enabled else 0.0)
    min_net_rr = float(config.min_net_rr if config.enabled else 0.0)
    reward_blocked = net_reward_bps <= min_net_reward_bps if min_net_reward_bps == 0 else net_reward_bps < min_net_reward_bps
    rr_blocked = net_rr is None or net_rr < min_net_rr
    blocked = gross_reward_bps <= 0 or gross_risk_bps <= 0 or reward_blocked or rr_blocked
    return {
        "schema_version": "cost_aware_entry_filter_v1",
        "enabled": True,
        "auto_enabled_by_nonzero_costs": auto_enabled and not config.enabled,
        "blocked": blocked,
        "block_reason": "COST_INFEASIBLE_TAKE_PROFIT" if blocked else None,
        "min_net_reward_bps": min_net_reward_bps,
        "min_net_rr": min_net_rr,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_price": stop_price,
        "channel_width_at_entry": (getattr(entry, "metadata", {}) or {}).get("channel_width_at_entry"),
        "target_price_source": (getattr(entry, "metadata", {}) or {}).get("target_price_source"),
        "projected_channel_width_target": (getattr(entry, "metadata", {}) or {}).get("projected_channel_width_target"),
        "gross_reward_bps": gross_reward_bps,
        "gross_risk_bps": gross_risk_bps,
        "estimated_one_side_cost_bps": one_side_cost_bps,
        "estimated_round_trip_cost_bps": round_trip_cost_bps,
        "net_reward_bps": net_reward_bps,
        "net_risk_bps": net_risk_bps,
        "net_rr": net_rr,
        "fee_bps": fee_bps,
        "spread_bps": cost_config.spread_bps,
        "slippage_bps": slippage_bps,
        "effective_slippage_bps": slippage_bps,
        "volatility_bps": volatility_bps,
        "cost_profile_name": config.cost_profile_name or _cost_profile_name(cost_config),
        "liquidity_role": config.liquidity_role.value,
    }


def _channel_close_volume_entry_filter_decision(
    entry: Any,
    channel_candles: pd.DataFrame | list[dict[str, Any]],
    future_candles: pd.DataFrame | list[dict[str, Any]],
    config: CloseVolumeEntryFilterConfig | None,
) -> dict[str, Any]:
    if config is None or not config.enabled:
        return {
            "schema_version": "close_volume_entry_filter_v1",
            "enabled": False,
        }

    side = str(getattr(getattr(entry, "side", None), "value", getattr(entry, "side", ""))).upper()
    applies_to_side = str(config.applies_to_side).upper()
    applies_to_sides = _close_volume_filter_applies_to_sides(applies_to_side)
    base = {
        "schema_version": "close_volume_entry_filter_v1",
        "enabled": True,
        "applies_to_side": applies_to_side,
        "applies_to_sides": applies_to_sides,
        "entry_side": side,
        "window": int(config.window),
        "minimum_volume_ratio": float(config.minimum_volume_ratio),
        "low_volume_ratio_threshold": float(config.low_volume_ratio_threshold),
        "baseline_mode": str(config.baseline_mode).upper(),
        "volume_input_mode": str(config.volume_input_mode).upper(),
        "require_full_window": bool(config.require_full_window),
        "fail_closed_on_invalid": bool(config.fail_closed_on_invalid),
        "signal_candle_index": getattr(entry, "candle_index", None),
        "signal_timestamp": getattr(entry, "timestamp", None),
    }
    if side not in applies_to_sides:
        return {
            **base,
            "applies": False,
            "passed": True,
            "blocked": False,
            "block_reason": None,
        }

    decision = _close_volume_ratio_decision_row(entry, channel_candles, future_candles, config)
    valid = bool(decision.get("is_valid"))
    ratio = decision.get("volume_ratio")
    passed = valid and ratio is not None and float(ratio) >= float(config.minimum_volume_ratio)
    blocked = not passed if config.fail_closed_on_invalid else (valid and not passed)
    block_reason = "LOW_CLOSE_VOLUME_ENTRY_FILTER" if blocked else None
    if blocked and not valid:
        block_reason = "LOW_CLOSE_VOLUME_ENTRY_FILTER"
    return {
        **base,
        **decision,
        "applies": True,
        "passed": bool(passed),
        "blocked": bool(blocked),
        "block_reason": block_reason,
    }


def _order_block_entry_volume_filter_decision(
    event: Any,
    entry: Any,
    candles: pd.DataFrame | list[dict[str, Any]],
    config: OrderBlockEntryVolumeFilterConfig | None,
) -> dict[str, Any]:
    if not _is_order_block_event(event):
        return {}
    if config is None or not config.enabled:
        return {
            "schema_version": "order_block_entry_volume_filter_v1",
            "enabled": False,
        }
    base = {
        "schema_version": "order_block_entry_volume_filter_v1",
        "enabled": True,
        "window": int(config.window),
        "minimum_volume_ratio": float(config.minimum_volume_ratio),
        "baseline_mode": str(config.baseline_mode).upper(),
        "volume_input_mode": str(config.volume_input_mode).upper(),
        "require_full_window": bool(config.require_full_window),
        "fail_closed_on_invalid": bool(config.fail_closed_on_invalid),
        "signal_timestamp": getattr(entry, "fill_timestamp", None),
        "signal_candle_index": getattr(entry, "fill_candle_index", None),
    }
    decision = _volume_ratio_decision_at_timestamp(
        candles,
        getattr(entry, "fill_timestamp", None),
        window=int(config.window),
        minimum_volume_ratio=float(config.minimum_volume_ratio),
        baseline_mode=str(config.baseline_mode).upper(),
        volume_input_mode=str(config.volume_input_mode).upper(),
        require_full_window=bool(config.require_full_window),
    )
    valid = bool(decision.get("is_valid"))
    ratio = decision.get("volume_ratio")
    passed = valid and ratio is not None and float(ratio) >= float(config.minimum_volume_ratio)
    blocked = not passed if config.fail_closed_on_invalid else (valid and not passed)
    return {
        **base,
        **decision,
        "passed": bool(passed),
        "blocked": bool(blocked),
        "block_reason": "ORDER_BLOCK_ENTRY_VOLUME_FILTER" if blocked else None,
    }


def _order_block_mtf_filter_decision(
    event: Any,
    *,
    position_side: str,
    candles: pd.DataFrame | list[dict[str, Any]],
    config: OrderBlockMtfFilterConfig | None,
    entry_timestamp: Any | None,
) -> dict[str, Any]:
    if not _is_order_block_event(event):
        return {}
    if config is None or not config.enabled:
        return {
            "schema_version": "order_block_mtf_filter_v1",
            "enabled": False,
        }

    side = str(position_side).upper()
    required_direction = _required_order_block_direction(side)
    base = {
        "schema_version": "order_block_mtf_filter_v1",
        "enabled": True,
        "timeframes": list(config.timeframes),
        "require_all_timeframes": bool(config.require_all_timeframes),
        "fail_closed_on_missing": bool(config.fail_closed_on_missing),
        "context_source": "resampled_completed_base_candles",
        "effective_position_side": side,
        "required_order_block_direction": required_direction,
        "decision_timestamp": entry_timestamp,
        "no_lookahead": True,
    }
    if required_direction is None:
        return {**base, "passed": False, "blocked": True, "block_reason": "ORDER_BLOCK_MTF_FILTER", "invalid_reason": "UNSUPPORTED_POSITION_SIDE"}

    timeframe_results = []
    for timeframe in config.timeframes:
        result = _order_block_mtf_timeframe_decision(
            candles,
            timeframe=timeframe,
            entry_timestamp=entry_timestamp,
            required_direction=required_direction,
            config=config.order_block_config,
        )
        timeframe_results.append(result)

    passed_count = sum(1 for result in timeframe_results if result.get("passed"))
    missing_count = sum(1 for result in timeframe_results if result.get("invalid_reason"))
    if config.require_all_timeframes:
        passed = passed_count == len(timeframe_results)
    else:
        passed = passed_count > 0
    blocked = not passed
    if missing_count and not config.fail_closed_on_missing:
        blocked = False if not config.require_all_timeframes else passed_count > 0 and not passed
        passed = not blocked
    return {
        **base,
        "timeframe_results": timeframe_results,
        "passed_timeframe_count": passed_count,
        "checked_timeframe_count": len(timeframe_results),
        "passed": bool(passed),
        "blocked": bool(blocked),
        "block_reason": "ORDER_BLOCK_MTF_FILTER" if blocked else None,
    }


def _order_block_risk_exit_decision(
    event: Any,
    risk_plan: RiskExitPlan,
    entry: Any,
    candles: pd.DataFrame | list[dict[str, Any]],
    config: OrderBlockRiskExitConfig | None,
) -> dict[str, Any]:
    if not _is_order_block_event(event):
        return {}
    resolved = config or OrderBlockRiskExitConfig(mode="ZONE_STRUCTURAL_2R")
    entry_mode = getattr(getattr(entry, "plan", None), "mode", None)
    entry_mode_value = entry_mode.value if hasattr(entry_mode, "value") else str(entry_mode or "")
    base = {
        "schema_version": "order_block_risk_exit_v1",
        "selected_mode": resolved.mode,
        "enabled": resolved.mode == "PREVIOUS_CANDLE_1R",
        "entry_mode": entry_mode_value,
        "supported_entry_modes": [PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value],
        "fallback_on_unsupported_entry_mode": bool(resolved.fallback_on_unsupported_entry_mode),
        "decision_timestamp": getattr(entry, "fill_timestamp", None),
        "no_lookahead": True,
        "scope": "offline_backtest_research_only",
    }
    if resolved.mode == "ZONE_STRUCTURAL_2R":
        return {
            "metadata": {
                **base,
                "applied": False,
                "passed": True,
                "blocked": False,
                "fallback_to_existing_risk_plan": True,
                "fallback_reason": "ZONE_STRUCTURAL_2R_COMPATIBILITY_MODE",
            },
            "risk_plan": risk_plan,
        }
    if entry_mode is not PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        metadata = {
            **base,
            "applied": False,
            "passed": True,
            "blocked": False,
            "fallback_to_existing_risk_plan": True,
            "fallback_reason": "UNSUPPORTED_ENTRY_MODE_FOR_PREVIOUS_CANDLE_1R",
        }
        if not resolved.fallback_on_unsupported_entry_mode:
            metadata.update(
                {
                    "passed": False,
                    "blocked": True,
                    "block_reason": "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                    "invalid_reason": "UNSUPPORTED_ENTRY_MODE_FOR_PREVIOUS_CANDLE_1R",
                }
            )
        return {"metadata": metadata, "risk_plan": risk_plan}

    visible = _visible_confluence_candles(candles, getattr(entry, "fill_timestamp", None))
    missing_columns = [
        column
        for column in ("timestamp", "open", "high", "low", "close")
        if column not in visible.columns
    ]
    if visible.empty:
        return {
            "metadata": {
                **base,
                "applied": False,
                "passed": False,
                "blocked": True,
                "block_reason": "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                "invalid_reason": "CURRENT_CANDLE_MISSING",
            },
            "risk_plan": risk_plan,
        }
    if missing_columns:
        return {
            "metadata": {
                **base,
                "applied": False,
                "passed": False,
                "blocked": True,
                "block_reason": "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                "invalid_reason": "ORDER_BLOCK_RISK_CANDLE_COLUMNS_MISSING",
                "missing_columns": missing_columns,
            },
            "risk_plan": risk_plan,
        }
    if len(visible) < 2:
        current = visible.iloc[-1]
        return {
            "metadata": {
                **base,
                "applied": False,
                "passed": False,
                "blocked": True,
                "block_reason": "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                "invalid_reason": "PREVIOUS_CANDLE_MISSING",
                "current_candle": _local_ob_candle_metadata(current, len(visible) - 1),
            },
            "risk_plan": risk_plan,
        }

    previous_index = len(visible) - 2
    current_index = len(visible) - 1
    previous = visible.iloc[previous_index]
    current = visible.iloc[current_index]
    direction = _coerce_direction(risk_plan.direction)
    current_close = _positive_float(current.get("close"))
    previous_low = _positive_float(previous.get("low"))
    previous_high = _positive_float(previous.get("high"))
    side = direction.value
    if side == "LONG":
        stop_price = previous_low
        risk_distance = None if current_close is None or previous_low is None else current_close - previous_low
        target_price = None if current_close is None or risk_distance is None else current_close + risk_distance
        stop_source = "PREVIOUS_CANDLE_LOW"
    else:
        stop_price = previous_high
        risk_distance = None if current_close is None or previous_high is None else previous_high - current_close
        target_price = None if current_close is None or risk_distance is None else current_close - risk_distance
        stop_source = "PREVIOUS_CANDLE_HIGH"

    candle_metadata = {
        "previous_candle": _local_ob_candle_metadata(previous, previous_index),
        "current_candle": _local_ob_candle_metadata(current, current_index),
        "entry_price_source": "CURRENT_CONFIRMATION_CLOSE",
        "formula_entry_price": current_close,
        "actual_fill_price": getattr(entry, "fill_price", None),
        "stop_source": stop_source,
        "target_source": "CURRENT_CLOSE_SYMMETRIC_1R",
        "target_r_multiple": 1.0,
        "risk_distance": risk_distance,
        "target_distance": risk_distance,
        "stop_price": stop_price,
        "target_price": target_price,
    }
    if (
        current_close is None
        or stop_price is None
        or target_price is None
        or risk_distance is None
        or risk_distance <= 0
        or not isfinite(risk_distance)
        or not isfinite(target_price)
    ):
        return {
            "metadata": {
                **base,
                **candle_metadata,
                "applied": False,
                "passed": False,
                "blocked": True,
                "block_reason": "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID",
                "invalid_reason": "NON_POSITIVE_PREVIOUS_CANDLE_RISK",
            },
            "risk_plan": risk_plan,
        }

    target = RiskExitTarget(
        name="TP1",
        price=target_price,
        source=RiskExitTargetSource.R_MULTIPLE,
        r_multiple=1.0,
        metadata={
            "rule": "order_block_previous_candle_1r",
            "target_source": "CURRENT_CLOSE_SYMMETRIC_1R",
            "stop_source": stop_source,
            "risk_distance": risk_distance,
        },
    )
    target_semantics = target_semantics_metadata(
        direction=direction,
        entry_price=current_close,
        risk_per_unit=risk_distance,
        detector_target_reference=getattr(event, "target_reference", None),
        r_multiple_targets=(target,),
        structural_targets=(),
        measured_targets=(),
        risk_targets=(target,),
    )
    target_semantics["order_block_risk_exit_mode"] = "PREVIOUS_CANDLE_1R"
    adjusted_plan = RiskExitPlan(
        direction=direction,
        entry_price=current_close,
        structural_stop=stop_price,
        atr=0.0,
        atr_buffer_multiplier=0.0,
        atr_buffer=0.0,
        stop_price=stop_price,
        risk_per_unit=risk_distance,
        targets=(target,),
        status=RiskExitPlanStatus.VALID,
        reasons=(),
        minimum_first_target_r=risk_plan.minimum_first_target_r,
        time_stop=risk_plan.time_stop,
        break_even=risk_plan.break_even,
        trailing_stop=risk_plan.trailing_stop,
        partial_exits=(),
        atr_metadata={
            **dict(getattr(risk_plan, "atr_metadata", {}) or {}),
            "atr_used_for_order_block_previous_candle_risk": False,
        },
        target_semantics=target_semantics,
    )
    return {
        "metadata": {
            **base,
            **candle_metadata,
            "applied": True,
            "passed": True,
            "blocked": False,
            "block_reason": None,
            "fallback_to_existing_risk_plan": False,
        },
        "risk_plan": adjusted_plan,
    }


def _order_block_mtf_timeframe_decision(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    timeframe: str,
    entry_timestamp: Any | None,
    required_direction: str,
    config: OrderBlockConfig | None,
) -> dict[str, Any]:
    base = {
        "timeframe": timeframe,
        "passed": False,
        "required_order_block_direction": required_direction,
    }
    try:
        higher = _completed_resampled_candles(candles, timeframe, entry_timestamp)
    except ValueError as exc:
        return {**base, "invalid_reason": str(exc), "available_order_block_count": 0, "same_direction_order_block_count": 0}
    if higher.empty:
        return {**base, "invalid_reason": "MTF_CANDLE_CONTEXT_MISSING", "available_order_block_count": 0, "same_direction_order_block_count": 0}
    try:
        order_blocks = detect_order_blocks(higher, config=config or OrderBlockConfig())
    except (TypeError, ValueError) as exc:
        return {**base, "invalid_reason": "MTF_ORDER_BLOCK_DETECTION_FAILED", "error": str(exc), "available_order_block_count": 0, "same_direction_order_block_count": 0}
    same_direction = [
        order_block
        for order_block in order_blocks
        if str(getattr(order_block, "direction", "")).upper() == required_direction
    ]
    if not same_direction:
        return {
            **base,
            "available_candle_count": len(higher),
            "available_order_block_count": len(order_blocks),
            "same_direction_order_block_count": 0,
            "match_reason": "NO_SAME_DIRECTION_MTF_ORDER_BLOCK",
        }
    latest = max(same_direction, key=lambda ob: int(getattr(ob, "end_index", -1)))
    return {
        **base,
        "passed": True,
        "available_candle_count": len(higher),
        "available_order_block_count": len(order_blocks),
        "same_direction_order_block_count": len(same_direction),
        "matched_order_block_event_id": getattr(latest, "event_id", None),
        "matched_order_block_direction": getattr(latest, "direction", None),
        "matched_order_block_timestamp": getattr(latest, "timestamp", None),
        "matched_order_block_zone_low": getattr(latest, "zone_low", None),
        "matched_order_block_zone_high": getattr(latest, "zone_high", None),
        "match_reason": "SAME_DIRECTION_MTF_ORDER_BLOCK",
    }


def _volume_ratio_decision_at_timestamp(
    candles: pd.DataFrame | list[dict[str, Any]],
    timestamp: Any | None,
    *,
    window: int,
    minimum_volume_ratio: float,
    baseline_mode: str,
    volume_input_mode: str,
    require_full_window: bool,
) -> dict[str, Any]:
    frame = _visible_confluence_candles(candles, timestamp)
    if frame.empty:
        return {"is_valid": False, "invalid_reason": "ENTRY_CANDLE_NOT_FOUND", "current_volume": None, "baseline_volume": None, "volume_ratio": None, "volume_status": "INVALID"}
    if "volume" not in frame.columns:
        return {"is_valid": False, "invalid_reason": "VOLUME_COLUMN_MISSING", "current_volume": None, "baseline_volume": None, "volume_ratio": None, "volume_status": "INVALID"}
    required = ["timestamp", "volume"]
    if "symbol" not in frame.columns:
        frame = frame.copy()
        frame["symbol"] = "UNKNOWN"
    try:
        rows = calculate_volume_ratio(
            frame.copy(),
            VolumeRatioConfig(
                window=window,
                minimum_volume_ratio_for_confirmation=minimum_volume_ratio,
                high_volume_ratio_threshold=max(2.0, minimum_volume_ratio),
                low_volume_ratio_threshold=min(0.5, minimum_volume_ratio),
                require_full_window=require_full_window,
                baseline_mode=baseline_mode,
                volume_input_mode=volume_input_mode,
            ),
        )
    except (TypeError, ValueError) as exc:
        return {"is_valid": False, "invalid_reason": str(exc), "current_volume": None, "baseline_volume": None, "volume_ratio": None, "volume_status": "INVALID"}
    latest = rows.iloc[-1].to_dict()
    return {
        "is_valid": bool(latest.get("is_valid")),
        "invalid_reason": None if bool(latest.get("is_valid")) else "VOLUME_RATIO_INVALID",
        "current_volume": latest.get("volume"),
        "baseline_volume": latest.get("average_volume"),
        "volume_ratio": latest.get("volume_ratio"),
        "volume_status": latest.get("volume_status"),
        "volume_confirmation": bool(latest.get("volume_confirmation")),
        "minimum_volume_ratio_for_confirmation": latest.get("minimum_volume_ratio_for_confirmation"),
        "volume_ratio_metadata": rows.attrs.get("volume_ratio_metadata", {}),
    }


def _fvg_order_block_confluence_decision(
    event: Any,
    *,
    position_side: str,
    candles: pd.DataFrame | list[dict[str, Any]],
    config: FvgOrderBlockConfluenceConfig | None,
    entry_price: float | int | None,
    entry_timestamp: Any | None = None,
    fvg_zone_override: tuple[float, float, str] | None = None,
) -> dict[str, Any]:
    if config is None or not config.enabled:
        return {}

    side = str(position_side).upper()
    required_direction = _required_order_block_direction(side)
    source = _normalize_confluence_source(config.source)
    local_break_mode = _normalize_local_ob_break_mode(config.local_break_mode)
    mode = _normalize_confluence_mode(config.mode)
    fvg_zone = _fvg_confluence_zone(event, fvg_zone_override)
    fvg_midpoint = None if fvg_zone is None else (fvg_zone[0] + fvg_zone[1]) / 2.0
    entry = _positive_float(entry_price)
    base = {
        "schema_version": "fvg_order_block_confluence_v1",
        "enabled": True,
        "passed": False,
        "blocked": True,
        "block_reason": "FVG_ORDER_BLOCK_CONFLUENCE_MISSING",
        "source": source,
        "local_break_mode": local_break_mode,
        "mode": mode,
        "lookback_bars": None if config.lookback_bars is None else int(config.lookback_bars),
        "require_fresh": bool(config.require_fresh),
        "effective_position_side": side,
        "required_order_block_direction": required_direction,
        "fvg_event_id": getattr(event, "event_id", None),
        "fvg_zone_low": None if fvg_zone is None else fvg_zone[0],
        "fvg_zone_high": None if fvg_zone is None else fvg_zone[1],
        "fvg_zone_source": None if fvg_zone is None else fvg_zone[2],
        "fvg_midpoint": fvg_midpoint,
        "entry_price": entry,
        "decision_timestamp": entry_timestamp,
        "no_lookahead": True,
    }
    if required_direction is None:
        return {**base, "invalid_reason": "UNSUPPORTED_POSITION_SIDE"}
    if source == "LOCAL_ENTRY_CANDLES":
        return _local_fvg_order_block_confluence_decision(
            base=base,
            side=side,
            candles=candles,
            entry_timestamp=entry_timestamp,
            local_break_mode=local_break_mode,
        )
    return _historical_fvg_order_block_confluence_decision(
        base=base,
        event=event,
        candles=candles,
        config=config,
        entry=entry,
        entry_timestamp=entry_timestamp,
        fvg_zone=fvg_zone,
        fvg_midpoint=fvg_midpoint,
        mode=mode,
        required_direction=required_direction,
    )


def _local_fvg_order_block_confluence_decision(
    *,
    base: dict[str, Any],
    side: str,
    candles: pd.DataFrame | list[dict[str, Any]],
    entry_timestamp: Any | None,
    local_break_mode: str,
) -> dict[str, Any]:
    visible = _visible_confluence_candles(candles, entry_timestamp)
    if visible.empty:
        return {**base, "invalid_reason": "CURRENT_CANDLE_MISSING", "local_order_block_passed": False}
    missing = [column for column in ("timestamp", "open", "high", "low", "close") if column not in visible.columns]
    if missing:
        return {
            **base,
            "invalid_reason": "LOCAL_ORDER_BLOCK_CANDLE_COLUMNS_MISSING",
            "missing_columns": missing,
            "local_order_block_passed": False,
        }
    if len(visible) < 2:
        current = visible.iloc[-1]
        return {
            **base,
            "invalid_reason": "PREVIOUS_CANDLE_MISSING",
            "current_candle": _local_ob_candle_metadata(current, len(visible) - 1),
            "local_order_block_passed": False,
        }

    previous_index = len(visible) - 2
    current_index = len(visible) - 1
    previous = visible.iloc[previous_index]
    current = visible.iloc[current_index]
    previous_open = _positive_float(previous.get("open"))
    previous_high = _positive_float(previous.get("high"))
    previous_low = _positive_float(previous.get("low"))
    previous_close = _positive_float(previous.get("close"))
    current_open = _positive_float(current.get("open"))
    current_close = _positive_float(current.get("close"))
    candle_metadata = {
        "previous_candle": _local_ob_candle_metadata(previous, previous_index),
        "current_candle": _local_ob_candle_metadata(current, current_index),
        "local_ob_zone_low": previous_low,
        "local_ob_zone_high": previous_high,
    }
    if None in (previous_open, previous_high, previous_low, previous_close, current_open, current_close):
        return {
            **base,
            **candle_metadata,
            "invalid_reason": "LOCAL_ORDER_BLOCK_PRICE_MISSING",
            "local_order_block_passed": False,
        }

    if side == "LONG":
        previous_ok = previous_close < previous_open
        current_ok = current_close > current_open
        if local_break_mode == "BREAK_PREVIOUS_BODY":
            break_reference = max(previous_open, previous_close)
        else:
            break_reference = previous_high
        break_ok = current_close > break_reference
        failure_reason = (
            None
            if previous_ok and current_ok and break_ok
            else (
                "PREVIOUS_CANDLE_NOT_OPPOSING_SIDE"
                if not previous_ok
                else "CURRENT_CANDLE_NOT_CONFIRMING_SIDE"
                if not current_ok
                else "LOCAL_ORDER_BLOCK_BREAK_NOT_CONFIRMED"
            )
        )
    else:
        previous_ok = previous_close > previous_open
        current_ok = current_close < current_open
        if local_break_mode == "BREAK_PREVIOUS_BODY":
            break_reference = min(previous_open, previous_close)
        else:
            break_reference = previous_low
        break_ok = current_close < break_reference
        failure_reason = (
            None
            if previous_ok and current_ok and break_ok
            else (
                "PREVIOUS_CANDLE_NOT_OPPOSING_SIDE"
                if not previous_ok
                else "CURRENT_CANDLE_NOT_CONFIRMING_SIDE"
                if not current_ok
                else "LOCAL_ORDER_BLOCK_BREAK_NOT_CONFIRMED"
            )
        )

    passed = failure_reason is None
    return {
        **base,
        **candle_metadata,
        "local_order_block_passed": passed,
        "passed": passed,
        "blocked": not passed,
        "block_reason": None if passed else "FVG_ORDER_BLOCK_CONFLUENCE_MISSING",
        "invalid_reason": failure_reason,
        "local_break_reference": break_reference,
        "local_break_confirmed": break_ok,
        "local_previous_candle_opposing_side": previous_ok,
        "local_current_candle_confirming_side": current_ok,
        "matched_order_block_direction": base["required_order_block_direction"] if passed else None,
        "matched_order_block_zone_low": previous_low if passed else None,
        "matched_order_block_zone_high": previous_high if passed else None,
        "match_reason": "LOCAL_ENTRY_CANDLE_ORDER_BLOCK" if passed else failure_reason,
    }


def _historical_fvg_order_block_confluence_decision(
    *,
    base: dict[str, Any],
    event: Any,
    candles: pd.DataFrame | list[dict[str, Any]],
    config: FvgOrderBlockConfluenceConfig,
    entry: float | None,
    entry_timestamp: Any | None,
    fvg_zone: tuple[float, float, str] | None,
    fvg_midpoint: float | None,
    mode: str,
    required_direction: str,
) -> dict[str, Any]:
    if mode in {"ZONE_OVERLAP", "FVG_MIDPOINT_INSIDE_OB"} and fvg_zone is None:
        return {**base, "invalid_reason": "FVG_ZONE_MISSING"}
    if mode == "ENTRY_PRICE_INSIDE_OB" and entry is None:
        return {**base, "invalid_reason": "ENTRY_PRICE_MISSING"}

    visible = _visible_confluence_candles(candles, entry_timestamp)
    if visible.empty:
        return {**base, "invalid_reason": "CONFLUENCE_CANDLE_CONTEXT_MISSING"}
    missing = [column for column in ("timestamp", "open", "high", "low", "close", "volume") if column not in visible.columns]
    if missing:
        return {**base, "invalid_reason": "ORDER_BLOCK_CANDLE_COLUMNS_MISSING", "missing_columns": missing}

    try:
        order_blocks = detect_order_blocks(visible, config=config.order_block_config)
    except (TypeError, ValueError) as exc:
        return {**base, "invalid_reason": "ORDER_BLOCK_DETECTION_FAILED", "error": str(exc)}

    decision_index = len(visible) - 1
    same_direction = [
        order_block
        for order_block in order_blocks
        if str(getattr(order_block, "direction", "")).upper() == required_direction
        and _order_block_available_for_decision(order_block, decision_index, config)
    ]
    candidates_checked = 0
    for order_block in sorted(same_direction, key=lambda ob: int(getattr(ob, "end_index", -1)), reverse=True):
        candidates_checked += 1
        match = _order_block_zone_match(
            mode=mode,
            fvg_zone=fvg_zone,
            fvg_midpoint=fvg_midpoint,
            entry_price=entry,
            order_block=order_block,
        )
        if not match["matched"]:
            continue
        return {
            **base,
            "passed": True,
            "blocked": False,
            "block_reason": None,
            "candidates_checked": candidates_checked,
            "available_order_block_count": len(order_blocks),
            "same_direction_order_block_count": len(same_direction),
            "matched_order_block_event_id": getattr(order_block, "event_id", None),
            "matched_order_block_direction": getattr(order_block, "direction", None),
            "matched_order_block_state": getattr(order_block, "order_block_state", None),
            "matched_order_block_status": getattr(order_block, "pattern_status", None),
            "matched_order_block_zone_low": getattr(order_block, "zone_low", None),
            "matched_order_block_zone_high": getattr(order_block, "zone_high", None),
            "matched_order_block_end_index": getattr(order_block, "end_index", None),
            "matched_order_block_timestamp": getattr(order_block, "timestamp", None),
            **match,
        }

    return {
        **base,
        "candidates_checked": candidates_checked,
        "available_order_block_count": len(order_blocks),
        "same_direction_order_block_count": len(same_direction),
    }


def _required_order_block_direction(position_side: str) -> str | None:
    side = str(position_side).upper()
    if side == "LONG":
        return "BULLISH"
    if side == "SHORT":
        return "BEARISH"
    return None


def _normalize_confluence_mode(value: object) -> str:
    return str(value or "zone_overlap").strip().upper()


def _normalize_confluence_source(value: object) -> str:
    return str(value or "local_entry_candles").strip().upper()


def _normalize_local_ob_break_mode(value: object) -> str:
    return str(value or "break_previous_range").strip().upper()


def _normalize_order_block_risk_exit_mode(value: object) -> str:
    return str(value or "previous_candle_1r").strip().upper()


def _normalize_timeframe(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        raise ValueError("timeframe must not be empty")
    if text.endswith("m") and text[:-1].isdigit() and int(text[:-1]) > 0:
        return text
    if text.endswith("h") and text[:-1].isdigit() and int(text[:-1]) > 0:
        return text
    if text.endswith("d") and text[:-1].isdigit() and int(text[:-1]) > 0:
        return text
    raise ValueError(f"unsupported timeframe: {value}")


def _timeframe_delta(timeframe: str) -> pd.Timedelta:
    normalized = _normalize_timeframe(timeframe)
    unit = normalized[-1]
    amount = int(normalized[:-1])
    if unit == "m":
        return pd.Timedelta(minutes=amount)
    if unit == "h":
        return pd.Timedelta(hours=amount)
    if unit == "d":
        return pd.Timedelta(days=amount)
    raise ValueError(f"unsupported timeframe: {timeframe}")


def _timeframe_resample_rule(timeframe: str) -> str:
    normalized = _normalize_timeframe(timeframe)
    unit = normalized[-1]
    amount = normalized[:-1]
    if unit == "m":
        return f"{amount}min"
    if unit == "h":
        return f"{amount}h"
    if unit == "d":
        return f"{amount}D"
    raise ValueError(f"unsupported timeframe: {timeframe}")


def _completed_resampled_candles(
    candles: pd.DataFrame | list[dict[str, Any]],
    timeframe: str,
    decision_timestamp: Any | None,
) -> pd.DataFrame:
    frame = _visible_confluence_candles(candles, decision_timestamp)
    if frame.empty:
        return pd.DataFrame()
    missing = [column for column in ("timestamp", "open", "high", "low", "close", "volume") if column not in frame.columns]
    if missing:
        raise ValueError(f"MTF_CANDLE_COLUMNS_MISSING: {','.join(missing)}")
    try:
        timestamps = pd.to_datetime(frame["timestamp"], utc=True)
        decision = pd.to_datetime(decision_timestamp, utc=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"MTF_TIMESTAMP_INVALID: {exc}") from exc
    working = frame.copy()
    working["timestamp"] = timestamps
    working = working.sort_values("timestamp").set_index("timestamp")
    aggregation = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    if "symbol" in working.columns:
        aggregation["symbol"] = "last"
    resampled = working.resample(_timeframe_resample_rule(timeframe), label="left", closed="left").agg(aggregation)
    resampled = resampled.dropna(subset=["open", "high", "low", "close"]).reset_index()
    complete_until = resampled["timestamp"] + _timeframe_delta(timeframe)
    resampled = resampled.loc[complete_until <= decision].reset_index(drop=True)
    if "symbol" not in resampled.columns:
        resampled["symbol"] = "UNKNOWN"
    return resampled[["symbol", "timestamp", "open", "high", "low", "close", "volume"]]


def _is_order_block_event(event: Any) -> bool:
    return str(getattr(event, "pattern_type", "")).upper() == "ORDER_BLOCK"


def _local_ob_candle_metadata(candle: Any, index: int) -> dict[str, Any]:
    return {
        "index": int(index),
        "timestamp": candle.get("timestamp"),
        "open": _positive_float(candle.get("open")),
        "high": _positive_float(candle.get("high")),
        "low": _positive_float(candle.get("low")),
        "close": _positive_float(candle.get("close")),
    }


def _fvg_confluence_zone(event: Any, override: tuple[float, float, str] | None) -> tuple[float, float, str] | None:
    zone_low = _positive_float(getattr(event, "zone_low", None))
    zone_high = _positive_float(getattr(event, "zone_high", None))
    if zone_low is not None and zone_high is not None and zone_high > zone_low:
        return zone_low, zone_high, "fvg_event_zone"
    if override is None:
        return None
    low, high, source = override
    if high <= low:
        return None
    return low, high, source


def _channel_confluence_zone(event: Any, entry: Any) -> tuple[float, float, str] | None:
    if _positive_float(getattr(event, "zone_low", None)) is not None and _positive_float(getattr(event, "zone_high", None)) is not None:
        return None
    metadata = getattr(entry, "metadata", {}) or {}
    lower = _positive_float(metadata.get("channel_lower_line_price_at_entry"))
    upper = _positive_float(metadata.get("channel_upper_line_price_at_entry"))
    if lower is None or upper is None:
        return None
    return min(lower, upper), max(lower, upper), "channel_entry_band"


def _visible_confluence_candles(
    candles: pd.DataFrame | list[dict[str, Any]],
    decision_timestamp: Any | None,
) -> pd.DataFrame:
    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if frame.empty:
        return frame
    frame = frame.copy()
    if "timestamp" not in frame.columns or decision_timestamp is None:
        return frame.reset_index(drop=True)
    try:
        timestamps = pd.to_datetime(frame["timestamp"], utc=True)
        decision = pd.to_datetime(decision_timestamp, utc=True)
        return frame.loc[timestamps <= decision].reset_index(drop=True)
    except (TypeError, ValueError):
        matches = frame.index[frame["timestamp"] == decision_timestamp].tolist()
        if matches:
            return frame.iloc[: matches[-1] + 1].reset_index(drop=True)
        return frame.reset_index(drop=True)


def _combine_candle_frames(*sources: pd.DataFrame | list[dict[str, Any]] | None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source in sources:
        if source is None:
            continue
        frame = source.copy(deep=False) if isinstance(source, pd.DataFrame) else pd.DataFrame(source)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "timestamp" in combined.columns:
        try:
            combined = combined.sort_values("timestamp")
        except TypeError:
            pass
        combined = combined.drop_duplicates(subset=["timestamp"], keep="first")
    return combined.reset_index(drop=True)


def _order_block_available_for_decision(
    order_block: Any,
    decision_index: int,
    config: FvgOrderBlockConfluenceConfig,
) -> bool:
    end_index = getattr(order_block, "end_index", None)
    if not isinstance(end_index, int):
        try:
            end_index = int(end_index)
        except (TypeError, ValueError):
            return False
    if end_index > decision_index:
        return False
    if config.lookback_bars is not None and decision_index - end_index > int(config.lookback_bars):
        return False
    if config.require_fresh and str(getattr(order_block, "order_block_state", "")).upper() != "FRESH":
        return False
    return True


def _order_block_zone_match(
    *,
    mode: str,
    fvg_zone: tuple[float, float, str] | None,
    fvg_midpoint: float | None,
    entry_price: float | None,
    order_block: Any,
) -> dict[str, Any]:
    ob_low = _positive_float(getattr(order_block, "zone_low", None))
    ob_high = _positive_float(getattr(order_block, "zone_high", None))
    if ob_low is None or ob_high is None or ob_high <= ob_low:
        return {"matched": False, "match_reason": "ORDER_BLOCK_ZONE_INVALID"}
    if mode == "ENTRY_PRICE_INSIDE_OB":
        matched = entry_price is not None and ob_low <= entry_price <= ob_high
        return {
            "matched": matched,
            "match_reason": "ENTRY_PRICE_INSIDE_OB" if matched else "ENTRY_PRICE_OUTSIDE_OB",
            "price_checked": entry_price,
        }
    if mode == "FVG_MIDPOINT_INSIDE_OB":
        matched = fvg_midpoint is not None and ob_low <= fvg_midpoint <= ob_high
        return {
            "matched": matched,
            "match_reason": "FVG_MIDPOINT_INSIDE_OB" if matched else "FVG_MIDPOINT_OUTSIDE_OB",
            "price_checked": fvg_midpoint,
        }
    if fvg_zone is None:
        return {"matched": False, "match_reason": "FVG_ZONE_MISSING"}
    fvg_low, fvg_high, _source = fvg_zone
    overlap_low = max(fvg_low, ob_low)
    overlap_high = min(fvg_high, ob_high)
    overlap = overlap_high - overlap_low
    matched = overlap > 0
    return {
        "matched": matched,
        "match_reason": "ZONE_OVERLAP" if matched else "ZONE_DOES_NOT_OVERLAP",
        "overlap_low": overlap_low if matched else None,
        "overlap_high": overlap_high if matched else None,
        "overlap_size": overlap if matched else 0.0,
    }


def _close_volume_filter_applies_to_sides(applies_to_side: str) -> list[str]:
    normalized = str(applies_to_side).upper()
    if normalized in {"ALL", "BOTH", "LONG_SHORT"}:
        return ["LONG", "SHORT"]
    if normalized in {"LONG", "SHORT"}:
        return [normalized]
    return [normalized]


def _close_volume_ratio_decision_row(
    entry: Any,
    channel_candles: pd.DataFrame | list[dict[str, Any]],
    future_candles: pd.DataFrame | list[dict[str, Any]],
    config: CloseVolumeEntryFilterConfig,
) -> dict[str, Any]:
    frame = _volume_filter_frame(channel_candles, future_candles)
    entry_index = getattr(entry, "candle_index", None)
    entry_position = _volume_filter_entry_position(frame, entry_index, getattr(entry, "timestamp", None))
    if entry_position is None:
        return {
            "is_valid": False,
            "invalid_reason": "ENTRY_CANDLE_NOT_FOUND",
            "current_volume": None,
            "baseline_volume": None,
            "volume_ratio": None,
            "volume_status": "INVALID",
        }
    if "volume" not in frame.columns:
        return {
            "is_valid": False,
            "invalid_reason": "VOLUME_COLUMN_MISSING",
            "current_volume": None,
            "baseline_volume": None,
            "volume_ratio": None,
            "volume_status": "INVALID",
        }

    ratio_frame = frame.iloc[: entry_position + 1].copy()
    if "symbol" not in ratio_frame.columns:
        ratio_frame["symbol"] = "UNKNOWN"
    try:
        rows = calculate_volume_ratio(
            ratio_frame,
            VolumeRatioConfig(
                window=int(config.window),
                minimum_volume_ratio_for_confirmation=float(config.minimum_volume_ratio),
                high_volume_ratio_threshold=max(2.0, float(config.minimum_volume_ratio)),
                low_volume_ratio_threshold=float(config.low_volume_ratio_threshold),
                require_full_window=bool(config.require_full_window),
                baseline_mode=str(config.baseline_mode).upper(),
                volume_input_mode=str(config.volume_input_mode).upper(),
            ),
        )
    except (TypeError, ValueError) as exc:
        return {
            "is_valid": False,
            "invalid_reason": str(exc),
            "current_volume": None,
            "baseline_volume": None,
            "volume_ratio": None,
            "volume_status": "INVALID",
        }
    latest = rows.iloc[-1].to_dict()
    metadata = rows.attrs.get("volume_ratio_metadata", {})
    return {
        "is_valid": bool(latest.get("is_valid")),
        "invalid_reason": None if bool(latest.get("is_valid")) else "VOLUME_RATIO_INVALID",
        "current_volume": latest.get("volume"),
        "baseline_volume": latest.get("average_volume"),
        "volume_ratio": latest.get("volume_ratio"),
        "volume_status": latest.get("volume_status"),
        "volume_confirmation": bool(latest.get("volume_confirmation")),
        "minimum_volume_ratio_for_confirmation": latest.get("minimum_volume_ratio_for_confirmation"),
        "volume_ratio_metadata": metadata,
    }


def _volume_filter_frame(
    channel_candles: pd.DataFrame | list[dict[str, Any]],
    future_candles: pd.DataFrame | list[dict[str, Any]],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source in (channel_candles, future_candles):
        frame = source.copy(deep=False) if isinstance(source, pd.DataFrame) else pd.DataFrame(source)
        if frame.empty:
            continue
        records = frame.reset_index(drop=False).rename(columns={"index": "_source_index"})
        if records["_source_index"].map(lambda value: isinstance(value, int)).all():
            records["candle_index"] = records["_source_index"].astype(int)
        elif "candle_index" not in records.columns:
            records["candle_index"] = range(len(records))
        frames.append(records)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined.sort_values("candle_index").reset_index(drop=True)


def _volume_filter_entry_position(frame: pd.DataFrame, entry_index: Any, entry_timestamp: Any) -> int | None:
    if frame.empty:
        return None
    if entry_index is not None and "candle_index" in frame.columns:
        matches = frame.index[frame["candle_index"] == entry_index].tolist()
        if matches:
            return int(matches[0])
    if entry_timestamp is not None and "timestamp" in frame.columns:
        matches = frame.index[frame["timestamp"] == entry_timestamp].tolist()
        if matches:
            return int(matches[0])
    return None


def _channel_entry_candle_volatility_bps(
    candles: pd.DataFrame | list[dict[str, Any]],
    candle_index: Any,
) -> float | None:
    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if frame.empty:
        return None
    candle = None
    if candle_index is not None and candle_index in frame.index:
        candle = frame.loc[candle_index]
    elif "candle_index" in frame.columns and candle_index is not None:
        matches = frame[frame["candle_index"] == candle_index]
        if not matches.empty:
            candle = matches.iloc[0]
    elif isinstance(candle_index, int) and 0 <= candle_index < len(frame):
        candle = frame.iloc[candle_index]
    if candle is None:
        return None
    high = _positive_float(candle.get("high"))
    low = _positive_float(candle.get("low"))
    close = _positive_float(candle.get("close"))
    if high is None or low is None or close is None:
        return None
    return ((high - low) / close) * 10_000.0


def _entry_candle_volatility_bps(frame: pd.DataFrame, fill_candle_index: int | None) -> float | None:
    if fill_candle_index is None or fill_candle_index < 0 or fill_candle_index >= len(frame):
        return None
    candle = frame.iloc[fill_candle_index]
    high = _positive_float(candle.get("high"))
    low = _positive_float(candle.get("low"))
    close = _positive_float(candle.get("close"))
    if high is None or low is None or close is None:
        return None
    return ((high - low) / close) * 10_000.0


def _cost_profile_name(config: TransactionCostConfig | None) -> str:
    if is_zero_transaction_cost_config(config):
        return "zero"
    for key, profile in COST_PROFILES.items():
        if profile.config == config:
            return key
    return "manual"


def _to_exit_action(exit_event: PatternExitEvent, risk_plan: RiskExitPlan, position_side: str, base_metadata: dict[str, Any]) -> StrategyAction:
    final_exit = exit_event.remaining_quantity_ratio <= 0
    action_type = StrategyActionType.EXIT_LONG if (position_side == "LONG" and final_exit) else StrategyActionType.PARTIAL_EXIT_LONG if position_side == "LONG" else StrategyActionType.EXIT_SHORT if final_exit else StrategyActionType.PARTIAL_EXIT_SHORT
    action_quantity_ratio = 1.0 if final_exit else exit_event.quantity_ratio
    metadata = {**base_metadata, "exit_reason": exit_event.reason.value, "target_name": exit_event.target_name, "stop_price": exit_event.stop_price, "exit_price": exit_event.price, "quantity_ratio": exit_event.quantity_ratio, "action_quantity_ratio": action_quantity_ratio, "remaining_quantity_ratio": exit_event.remaining_quantity_ratio, "quantity_mode": StrategyQuantityMode.POSITION_RATIO.value}
    realized_r = _realized_r_multiple(exit_event, risk_plan)
    if realized_r is not None:
        metadata["realized_r_multiple"] = realized_r
    if exit_event.metadata:
        metadata["exit_metadata"] = dict(exit_event.metadata)
        if "target_source" in exit_event.metadata:
            metadata["target_source"] = exit_event.metadata["target_source"]
    return StrategyAction(action_type=action_type, timestamp=exit_event.timestamp, quantity=action_quantity_ratio, reason=exit_event.reason.value, metadata=metadata, requested_price=exit_event.price, quantity_mode=StrategyQuantityMode.POSITION_RATIO)


def _resolve_pattern_soft_invalidation(
    event: Any,
    risk_plan: RiskExitPlan,
    explicit_soft_invalidation: SoftInvalidationRule | None,
) -> tuple[SoftInvalidationRule | None, dict[str, Any]]:
    if explicit_soft_invalidation is not None:
        return explicit_soft_invalidation, {
            "schema_version": PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
            "enabled": True,
            "supported": True,
            "source": "explicit_soft_invalidation_argument",
            "rule": explicit_soft_invalidation.metadata.get("rule") if explicit_soft_invalidation.metadata else None,
            "invalidates_when": explicit_soft_invalidation.invalidates_when,
            "reference_field": explicit_soft_invalidation.metadata.get("reference_field") if explicit_soft_invalidation.metadata else None,
            "reference_price": explicit_soft_invalidation.reference_price,
            "max_bars_after_entry": explicit_soft_invalidation.max_bars_after_entry,
        }
    adapted = pattern_soft_invalidation_for_event(event, risk_plan)
    return adapted.rule, adapted.metadata


def _realized_r_multiple(exit_event: PatternExitEvent, risk_plan: RiskExitPlan) -> float | None:
    if risk_plan.entry_price is None or risk_plan.risk_per_unit is None or risk_plan.risk_per_unit <= 0:
        return None
    direction = _coerce_direction(risk_plan.direction)
    raw_r = (exit_event.price - risk_plan.entry_price) / risk_plan.risk_per_unit if direction == RiskExitDirection.LONG else (risk_plan.entry_price - exit_event.price) / risk_plan.risk_per_unit
    return round(raw_r, 10)


def _channel_realized_r(side: str, entry_price: float, stop_price: float, exit_price: float) -> float | None:
    risk = abs(float(entry_price) - float(stop_price))
    if risk <= 0 or not isfinite(risk):
        return None
    if side == "LONG":
        return round((float(exit_price) - float(entry_price)) / risk, 10)
    if side == "SHORT":
        return round((float(entry_price) - float(exit_price)) / risk, 10)
    return None


def _align_risk_plan_to_fill_price(risk_plan: RiskExitPlan, fill_price: float | int | None) -> RiskExitPlan:
    fill = _positive_float(fill_price)
    if fill is None:
        return _risk_plan_copy(
            risk_plan,
            status=RiskExitPlanStatus.INVALID,
            reasons=("fill_price must be a finite positive number",),
            targets=(),
        )
    try:
        direction = _coerce_direction(risk_plan.direction)
    except ValueError:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            status=RiskExitPlanStatus.INVALID,
            reasons=("direction must be LONG or SHORT",),
            targets=(),
        )

    stop_reference = _positive_float(risk_plan.structural_stop)
    atr_value = _non_negative_float(risk_plan.atr)
    if stop_reference is None or atr_value is None:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            status=RiskExitPlanStatus.INVALID,
            reasons=("structural_stop and atr are required to align risk plan to fill price",),
            targets=(),
        )

    atr_buffer_multiplier = float(risk_plan.atr_buffer_multiplier)
    atr_buffer = atr_value * atr_buffer_multiplier
    if direction == RiskExitDirection.LONG:
        stop_price = stop_reference - atr_buffer
        risk_per_unit = fill - stop_price
    else:
        stop_price = stop_reference + atr_buffer
        risk_per_unit = stop_price - fill

    reasons: list[str] = []
    if stop_price <= 0 or not isfinite(stop_price):
        reasons.append("stop_price must be a finite positive number after fill alignment")
    if risk_per_unit <= 0 or not isfinite(risk_per_unit):
        reasons.append("risk_per_unit must be positive after fill alignment")
    if reasons:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.INVALID,
            reasons=tuple(reasons),
            targets=(),
        )

    targets = _aligned_targets(risk_plan, direction, fill, risk_per_unit)
    if not targets:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.INVALID,
            reasons=("at least one actionable target is required after fill alignment",),
            targets=(),
        )

    first_target_r = targets[0].r_multiple
    if first_target_r is not None and first_target_r < risk_plan.minimum_first_target_r:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.SKIPPED,
            reasons=(
                "first actionable target is below minimum_first_target_r "
                f"({first_target_r} < {risk_plan.minimum_first_target_r}) after fill alignment",
            ),
            targets=targets,
            target_semantics=_aligned_target_semantics(risk_plan, direction, fill, risk_per_unit, targets),
        )

    return _risk_plan_copy(
        risk_plan,
        entry_price=fill,
        atr_buffer=atr_buffer,
        stop_price=stop_price,
        risk_per_unit=risk_per_unit,
        status=RiskExitPlanStatus.VALID,
        reasons=(),
        targets=targets,
        target_semantics=_aligned_target_semantics(risk_plan, direction, fill, risk_per_unit, targets),
    )


def _aligned_targets(
    risk_plan: RiskExitPlan,
    direction: RiskExitDirection,
    entry_price: float,
    risk_per_unit: float,
) -> tuple[RiskExitTarget, ...]:
    r_multiples = []
    candidates: list[RiskExitTarget] = []

    for target in risk_plan.targets:
        source = _coerce_target_source(target.source)
        if source == RiskExitTargetSource.R_MULTIPLE and target.r_multiple is not None:
            r_multiples.append(float(target.r_multiple))
            continue

        target_price = _positive_float(target.price)
        if target_price is None or not _is_actionable_target(direction, entry_price, target_price):
            continue
        r_multiple = _target_r_multiple(direction, entry_price, target_price, risk_per_unit)
        if r_multiple < risk_plan.minimum_first_target_r:
            continue
        candidates.append(
            RiskExitTarget(
                name=target.name,
                price=target_price,
                source=source,
                r_multiple=r_multiple,
                metadata={**dict(target.metadata), "fill_adjusted": True},
            )
        )

    if not r_multiples:
        r_multiples = [float(target.r_multiple) for target in risk_plan.targets if target.r_multiple is not None]
    if not r_multiples:
        r_multiples = [1.0, 2.0, 3.0]

    for multiple in dict.fromkeys(r_multiples):
        price = entry_price + (risk_per_unit * multiple) if direction == RiskExitDirection.LONG else entry_price - (risk_per_unit * multiple)
        candidates.append(
            RiskExitTarget(
                name="TP",
                price=price,
                source=RiskExitTargetSource.R_MULTIPLE,
                r_multiple=multiple,
                metadata={"rule": "r_multiple", "fill_adjusted": True},
            )
        )

    candidates.sort(key=lambda target: target.price, reverse=direction == RiskExitDirection.SHORT)
    return tuple(
        RiskExitTarget(
            name=f"TP{index}",
            price=target.price,
            source=target.source,
            r_multiple=target.r_multiple,
            metadata=dict(target.metadata),
        )
        for index, target in enumerate(candidates, start=1)
        if _is_actionable_target(direction, entry_price, target.price)
    )


def _risk_plan_copy(
    risk_plan: RiskExitPlan,
    *,
    entry_price: float | None | object = _UNSET,
    atr_buffer: float | None | object = _UNSET,
    stop_price: float | None | object = _UNSET,
    risk_per_unit: float | None | object = _UNSET,
    targets: tuple[RiskExitTarget, ...] | object = _UNSET,
    status: RiskExitPlanStatus | object = _UNSET,
    reasons: tuple[str, ...] | object = _UNSET,
    target_semantics: dict[str, Any] | object = _UNSET,
) -> RiskExitPlan:
    return RiskExitPlan(
        direction=risk_plan.direction,
        entry_price=risk_plan.entry_price if entry_price is _UNSET else entry_price,
        structural_stop=risk_plan.structural_stop,
        atr=risk_plan.atr,
        atr_buffer_multiplier=risk_plan.atr_buffer_multiplier,
        atr_buffer=risk_plan.atr_buffer if atr_buffer is _UNSET else atr_buffer,
        stop_price=risk_plan.stop_price if stop_price is _UNSET else stop_price,
        risk_per_unit=risk_plan.risk_per_unit if risk_per_unit is _UNSET else risk_per_unit,
        targets=risk_plan.targets if targets is _UNSET else targets,
        status=risk_plan.status if status is _UNSET else status,
        reasons=risk_plan.reasons if reasons is _UNSET else reasons,
        minimum_first_target_r=risk_plan.minimum_first_target_r,
        time_stop=risk_plan.time_stop,
        break_even=risk_plan.break_even,
        trailing_stop=risk_plan.trailing_stop,
        partial_exits=risk_plan.partial_exits,
        atr_metadata=risk_plan.atr_metadata,
        target_semantics=risk_plan.target_semantics if target_semantics is _UNSET else target_semantics,
    )


def _metadata_with_aligned_risk_plan(
    metadata: dict[str, Any],
    original_plan: RiskExitPlan,
    aligned_plan: RiskExitPlan,
) -> dict[str, Any]:
    aligned = not _same_number(original_plan.entry_price, aligned_plan.entry_price)
    if metadata.get("entry_quantity_source") == "ACTION_OVERRIDE":
        sizing_risk_source = SizingRiskSource.ACTION_OVERRIDE.value
    elif aligned_plan.risk_per_unit is None or aligned_plan.risk_per_unit <= 0:
        sizing_risk_source = SizingRiskSource.MISSING.value
    else:
        sizing_risk_source = SizingRiskSource.FILL_ADJUSTED.value
    return {
        **metadata,
        "entry_price": aligned_plan.entry_price,
        "entry_reference": original_plan.entry_price,
        "risk_per_unit": aligned_plan.risk_per_unit,
        "original_risk_plan_entry_price": original_plan.entry_price,
        "original_risk_per_unit": original_plan.risk_per_unit,
        "fill_adjusted_risk_plan_entry_price": aligned_plan.entry_price,
        "fill_adjusted_risk_per_unit": aligned_plan.risk_per_unit,
        "risk_plan_aligned_to_fill": aligned,
        "sizing_risk_source": sizing_risk_source,
        "target_semantics": _metadata_target_semantics(metadata, aligned_plan),
    }


def _aligned_target_semantics(
    original_plan: RiskExitPlan,
    direction: RiskExitDirection,
    entry_price: float,
    risk_per_unit: float,
    targets: tuple[RiskExitTarget, ...],
) -> dict[str, Any]:
    original_semantics = dict(getattr(original_plan, "target_semantics", {}) or {})
    return target_semantics_metadata(
        direction=direction,
        entry_price=entry_price,
        risk_per_unit=risk_per_unit,
        detector_target_reference=original_semantics.get("detector_target_reference"),
        r_multiple_targets=tuple(
            target
            for target in targets
            if _coerce_target_source(target.source) == RiskExitTargetSource.R_MULTIPLE
        ),
        structural_targets=_semantic_prices(original_semantics, "structural_targets"),
        measured_targets=_semantic_prices(original_semantics, "measured_targets"),
        risk_targets=targets,
    )


def _metadata_target_semantics(metadata: dict[str, Any], risk_plan: RiskExitPlan) -> dict[str, Any]:
    target_semantics = dict(getattr(risk_plan, "target_semantics", {}) or {})
    if not target_semantics:
        return {}
    if target_semantics.get("detector_target_reference") is None:
        target_semantics["detector_target_reference"] = metadata.get("event_target_reference")
    return target_semantics


def _semantic_prices(target_semantics: dict[str, Any], key: str) -> tuple[float, ...]:
    prices: list[float] = []
    for target in target_semantics.get(key, ()) or ():
        if isinstance(target, dict) and target.get("price") is not None:
            prices.append(float(target["price"]))
    return tuple(prices)


def _target_r_multiple(
    direction: RiskExitDirection,
    entry_price: float,
    target_price: float,
    risk_per_unit: float,
) -> float:
    if direction == RiskExitDirection.LONG:
        return (target_price - entry_price) / risk_per_unit
    return (entry_price - target_price) / risk_per_unit


def _is_actionable_target(direction: RiskExitDirection, entry_price: float, target_price: float) -> bool:
    if direction == RiskExitDirection.LONG:
        return target_price > entry_price
    return target_price < entry_price


def _coerce_target_source(source: RiskExitTargetSource | str) -> RiskExitTargetSource:
    if isinstance(source, RiskExitTargetSource):
        return source
    return RiskExitTargetSource(str(source).split(".")[-1].upper())


def _positive_float(value: float | int | None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result) or result <= 0:
        return None
    return result


def _non_negative_float(value: float | int | None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result) or result < 0:
        return None
    return result


def _same_number(left: float | int | None, right: float | int | None) -> bool:
    try:
        return abs(float(left) - float(right)) < 1e-12
    except (TypeError, ValueError):
        return left == right


def _score_metadata_from_event(event: Any) -> dict[str, Any]:
    return {
        "score_components": getattr(event, "score_components", {}),
        "score_component_sources": getattr(event, "score_component_sources", {}),
        "score_limitations": getattr(event, "score_limitations", ()),
        "score_calibration": getattr(event, "score_calibration", {}),
    }


def _entry_policy_metadata(
    *,
    event: Any,
    plan: Any,
    entry: Any,
    entry_reference: float | None,
    requested_price: float | None,
    confirmation_close: Any,
    fill_assumption: str,
    fill_price_source: str,
) -> dict[str, Any]:
    return {
        "schema_version": "pattern_entry_policy_v1",
        "pattern_type": getattr(event, "pattern_type", None),
        "entry_mode": plan.mode.value,
        "fill_assumption": fill_assumption,
        "fill_price_source": fill_price_source,
        "entry_trigger": entry.plan.config.entry_trigger.value if hasattr(entry.plan.config.entry_trigger, "value") else str(entry.plan.config.entry_trigger),
        "entry_reference": entry_reference,
        "requested_price": requested_price,
        "confirmation_close": confirmation_close,
        "bars_waited": entry.bars_waited,
        "touch_timestamp": entry.touch_timestamp,
        "touch_candle_index": entry.touch_candle_index,
        "reaction_timestamp": entry.reaction_timestamp,
        "reaction_candle_index": entry.reaction_candle_index,
        "entry_status": entry.status.value,
        "limit_price": plan.limit_price,
        "max_wait_bars": plan.config.max_wait_bars,
        "expire_status": plan.config.expire_status.value,
        "invalid_reason": entry.reason if entry.status == PatternEntryStatus.INVALID else None,
        "supported_modes": _supported_entry_modes(getattr(event, "pattern_type", None)),
        "contract": "requested_price is the simulated fill price used by strategy-engine sizing and costs; entry_reference is research metadata only.",
        "entry_mode_hypothesis": _entry_mode_hypothesis(getattr(event, "pattern_type", None), plan.mode),
        "entry_style": _entry_style(plan.mode),
        "entry_reference_distance": _distance(requested_price, entry_reference),
        "zone_distance": _zone_distance(event, requested_price),
        "zone_boundary_variant": _zone_boundary_variant(plan.mode),
    }


def _combined_entry_exit_metadata(
    risk_plan: RiskExitPlan,
    frame: pd.DataFrame,
    fill_candle_index: int | None,
    intrabar_policy_config: IntrabarPolicyConfig | None,
    *,
    entry_filled_on_first_candle: bool,
) -> dict[str, Any]:
    if not entry_filled_on_first_candle or fill_candle_index is None or frame.empty or not risk_plan.targets:
        return {}
    candle = frame.iloc[fill_candle_index]
    first_target = risk_plan.targets[0]
    touches = detect_intrabar_touches(
        high=float(candle["high"]),
        low=float(candle["low"]),
        entry_price=float(risk_plan.entry_price),
        stop_price=float(risk_plan.stop_price),
        target_price=float(first_target.price),
    )
    if not (touches.entry_touched and (touches.stop_touched or touches.target_touched)):
        return {}
    decision = resolve_intrabar_decision(
        direction=str(risk_plan.direction.value if hasattr(risk_plan.direction, "value") else risk_plan.direction),
        touches=touches,
        config=intrabar_policy_config,
    )
    return {
        "schema_version": "combined_entry_exit_intrabar_decision_v1",
        "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
        "entry_touched": touches.entry_touched,
        "stop_touched": touches.stop_touched,
        "target_touched": touches.target_touched,
        "ambiguous_stop_target": touches.ambiguous_stop_target,
        "ambiguous_entry_stop_target": touches.ambiguous_entry_stop_target,
        "is_ambiguous": decision.is_ambiguous,
        "decision_reason": decision.reason,
        "decision_outcome": decision.outcome,
        "skipped": decision.skipped,
        "candle_index": fill_candle_index,
    }


def _entry_fill_is_first_future_candle(frame: pd.DataFrame, fill_candle_index: int | None, fill_timestamp: Any) -> bool:
    if fill_candle_index is None or frame.empty or fill_candle_index != 0:
        return False
    return _same_value(frame.iloc[0]["timestamp"], fill_timestamp)


def _same_value(left: Any, right: Any) -> bool:
    try:
        return bool(left == right)
    except ValueError:
        return False


def _supported_entry_modes(pattern_type: Any) -> tuple[str, ...]:
    pattern = str(pattern_type or "").upper()
    base_modes = (
        PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value,
        PatternEntryMode.MARKET_ON_NEXT_OPEN.value,
        PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE.value,
        PatternEntryMode.LIMIT_AT_CUSTOM_PRICE.value,
    )
    zone_modes = (
        PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT.value,
        PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY.value,
        PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY.value,
        PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY.value,
    )
    order_block_modes = (
        PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT.value,
    )
    if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK", "DIAMOND"}:
        modes = (*base_modes, *zone_modes)
        if pattern == "ORDER_BLOCK":
            return (*modes, *order_block_modes)
        return modes
    if pattern == "LIQUIDITY_SWEEP_REVERSAL":
        return (
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE.value,
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value,
            PatternEntryMode.MARKET_ON_NEXT_OPEN.value,
            PatternEntryMode.LIMIT_AT_CUSTOM_PRICE.value,
        )
    if pattern in {"TRENDLINE_BREAK", "CUP_AND_HANDLE", "ADAM_AND_EVE"}:
        if pattern == "TRENDLINE_BREAK":
            return (*base_modes, PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST.value)
        if pattern == "CUP_AND_HANDLE":
            return (*base_modes, PatternEntryMode.LIMIT_AT_NECKLINE_RETEST.value)
        return base_modes
    return (*base_modes, *zone_modes)


def _pattern_event_metadata(event: Any, position_side: str, risk_plan: RiskExitPlan) -> dict[str, Any]:
    return {
        "pattern_execution_path": PATTERN_EXECUTION_PATH_CANONICAL_FILL_AWARE,
        "canonical_pattern_action": True,
        "canonical_expansion_required": False,
        "pattern_event_id": getattr(event, "event_id", None),
        "event_id": getattr(event, "event_id", None),
        "pattern_type": getattr(event, "pattern_type", None),
        "pattern_direction": str(getattr(event, "pattern_direction", getattr(event, "direction", ""))).upper(),
        "position_side": position_side,
        "fvg_direction_mode": getattr(event, "fvg_direction_mode", None),
        "fvg_inverse_direction_enabled": getattr(event, "fvg_inverse_direction_enabled", None),
        "original_position_side": getattr(event, "original_position_side", position_side),
        "effective_position_side": getattr(event, "effective_position_side", position_side),
        "direction_inversion_reason": getattr(event, "direction_inversion_reason", None),
        "pattern_status": getattr(event, "pattern_status", None),
        "pattern_score": getattr(event, "pattern_score", None),
        "executable_pattern_score": getattr(
            event,
            "executable_pattern_score",
            getattr(event, "pattern_score", None),
        ),
        "diagnostic_pattern_score": getattr(event, "diagnostic_pattern_score", None),
        "risk_reward": getattr(event, "risk_reward", None),
        "event_entry_reference": getattr(event, "entry_reference", None),
        "event_stop_reference": getattr(event, "stop_reference", None),
        "event_target_reference": getattr(event, "target_reference", None),
        "target_semantics": _event_target_semantics(event, risk_plan),
        "stop_reference": getattr(event, "stop_reference", getattr(risk_plan, "structural_stop", None)),
        "target_reference": getattr(event, "target_reference", None),
        "zone_mid": getattr(event, "zone_mid", None),
        "zone_low": getattr(event, "zone_low", None),
        "zone_high": getattr(event, "zone_high", None),
        "trendline_value": getattr(event, "trendline_value", None),
        "neckline": getattr(event, "neckline", None),
        "upper_boundary_value": getattr(event, "upper_boundary_value", None),
        "lower_boundary_value": getattr(event, "lower_boundary_value", None),
        "risk_plan_status": _status_value(getattr(risk_plan, "status", None)),
        "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
        "atr_metadata": getattr(event, "atr_metadata", {}) or getattr(risk_plan, "atr_metadata", {}),
        "mtf_trend_score": getattr(event, "mtf_trend_score", None),
        "mtf_trend_direction": getattr(event, "mtf_trend_direction", None),
        "mtf_trend_aligned": getattr(event, "mtf_trend_aligned", None),
        "mtf_trend_metadata": getattr(event, "mtf_trend_metadata", {}),
        "fib_confluence_pass": getattr(event, "fib_confluence_pass", None),
        "fib_retracement_level": getattr(event, "fib_retracement_level", None),
        "fib_metadata": getattr(event, "fib_metadata", {}),
        "risk_plan_atr_metadata": getattr(risk_plan, "atr_metadata", {}),
        "atr_buffer_multiplier": getattr(risk_plan, "atr_buffer_multiplier", None),
        **_liquidity_sweep_event_metadata(event),
        **_score_metadata_from_event(event),
    }


def _event_target_semantics(event: Any, risk_plan: RiskExitPlan) -> dict[str, Any]:
    target_semantics = dict(getattr(risk_plan, "target_semantics", {}) or {})
    if not target_semantics:
        return {}
    if target_semantics.get("detector_target_reference") is None:
        target_semantics["detector_target_reference"] = getattr(event, "target_reference", None)
    return target_semantics


def _fill_assumption(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "MARKET"
    return "REFERENCE_LIMIT"


def _fill_price_source(mode: PatternEntryMode) -> str:
    if mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        return "CONFIRMATION_CLOSE"
    if mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
        return "NEXT_OPEN"
    if mode == PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE:
        return "ENTRY_REFERENCE"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
        return "PATTERN_MIDPOINT"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY:
        return "PATTERN_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
        return "PATTERN_NEAR_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY:
        return "PATTERN_FAR_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
        return "ORDER_BLOCK_618_RETRACEMENT"
    if mode == PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST:
        return "TRENDLINE_RETEST"
    if mode == PatternEntryMode.LIMIT_AT_NECKLINE_RETEST:
        return "NECKLINE_RETEST"
    return "CUSTOM_PRICE"


def _entry_style(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "CHASE_OR_MOMENTUM"
    return "RETEST_LIMIT"


def _zone_boundary_variant(mode: PatternEntryMode) -> str | None:
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
        return "NEAR_BOUNDARY"
    if mode in (PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY, PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY):
        return "FAR_OR_STOP_SIDE_BOUNDARY"
    return None


def _entry_mode_hypothesis(pattern_type: Any, mode: PatternEntryMode) -> str:
    pattern = str(pattern_type or "").upper()
    if mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        return "CHASE_MOMENTUM_CONFIRMATION_CLOSE" if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK"} else "CONFIRMATION_CLOSE"
    if mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
        return "CHASE_MOMENTUM_NEXT_OPEN" if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK"} else "NEXT_OPEN"
    if pattern == "FAIR_VALUE_GAP":
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
            return "RETEST_GAP_MIDPOINT"
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
            return "RETEST_NEAR_GAP_BOUNDARY"
        if mode in (PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY, PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY):
            return "RETEST_DEEP_GAP_BOUNDARY"
    if pattern == "ORDER_BLOCK":
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
            return "RETEST_ORDER_BLOCK_MIDPOINT"
        if mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
            return "RETEST_ORDER_BLOCK_618_RETRACEMENT"
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY:
            return "RETEST_ORDER_BLOCK_STOP_SIDE_BOUNDARY"
    if pattern == "LIQUIDITY_SWEEP_REVERSAL":
        if mode == PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE:
            return "RETEST_SELECTED_FVG_OR_OB_LEVEL"
        if mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
            return "DIAGNOSTIC_CHASE_RECLAIM_DISPLACEMENT_CLOSE"
    if mode == PatternEntryMode.LIMIT_AT_CUSTOM_PRICE:
        return "CUSTOM_RESEARCH_PRICE"
    return "LEGACY_OR_REFERENCE_LIMIT"


def _is_liquidity_sweep_event(event: Any) -> bool:
    return str(getattr(event, "pattern_type", "")).upper() == "LIQUIDITY_SWEEP_REVERSAL"


def _liquidity_sweep_event_metadata(event: Any) -> dict[str, Any]:
    if not _is_liquidity_sweep_event(event):
        return {}
    keys = (
        "liquidity_pool_index",
        "liquidity_pool_timestamp",
        "liquidity_pool_price",
        "liquidity_pool_source",
        "sweep_candle_index",
        "sweep_candle_timestamp",
        "sweep_extreme_price",
        "sweep_distance",
        "sweep_distance_atr",
        "sweep_distance_bps",
        "reclaim_candle_index",
        "reclaim_candle_timestamp",
        "reclaim_close",
        "reclaim_lag_bars",
        "displacement_candle_index",
        "displacement_direction",
        "displacement_range_atr",
        "displacement_body_ratio",
        "volume_ratio",
        "fvg_confluence_pass",
        "fvg_event_id",
        "fvg_zone_low",
        "fvg_zone_high",
        "order_block_confluence_pass",
        "order_block_event_id",
        "order_block_zone_low",
        "order_block_zone_high",
        "target_source",
        "entry_source",
        "regime_metadata",
        "mtf_metadata",
    )
    return {
        "liquidity_sweep_reversal": {
            "schema_version": "liquidity_sweep_reversal_event_v1",
            **{key: getattr(event, key, None) for key in keys},
        }
    }


def _distance(left: float | int | None, right: float | int | None) -> float | None:
    if left is None or right is None:
        return None
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _zone_distance(event: Any, price: float | int | None) -> dict[str, float] | None:
    if price is None:
        return None
    zone_low = _positive_float(getattr(event, "zone_low", None))
    zone_high = _positive_float(getattr(event, "zone_high", None))
    if zone_low is None or zone_high is None:
        return None
    zone_mid = (zone_low + zone_high) / 2.0
    fill = float(price)
    return {
        "from_zone_low": fill - zone_low,
        "from_zone_mid": fill - zone_mid,
        "from_zone_high": fill - zone_high,
    }


def _candle_value(candle: dict[str, Any] | pd.Series, name: str) -> Any:
    return candle.get(name) if isinstance(candle, dict) else candle[name]


def _status_value(status: Any) -> str | None:
    if status is None:
        return None
    return str(status.value if hasattr(status, "value") else status)


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
