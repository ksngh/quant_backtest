"""Pattern strategy backtest integration.

This module wires completed candle data, existing pattern detection, existing
risk/exit planning, and the Task 054 exit simulator into a pure historical
backtest workflow. It does not fetch market data, read secrets, call exchange
APIs, place paper or real orders, or persist records.

Current assumptions:
- Fair Value Gap remains the default selected pattern, and each other supported
  selection is wired only through an existing detector plus risk/exit planner
  that operates on the shared pattern contracts.
- Completed candles are evaluated in ascending timestamp order using rolling
  prefixes; only events confirmed on the current candle are eligible, so pattern
  detection never uses candles after the event confirmation candle.
- A simulated entry happens at the plan entry reference on the pattern
  confirmation candle, and exit evaluation starts on the next completed candle.
- Only one simulated position is open at a time. If multiple eligible events are
  confirmed on the same candle, the deterministic sort order is pattern type,
  direction, then event id; the first valid plan is entered and the rest are not
  entered during that open position.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, cast

import pandas as pd

from quant_bitcoin.backtesting.basic import NUMERIC_CANDLE_COLUMNS, STANDARD_CANDLE_COLUMNS
from quant_bitcoin.patterns import (
    AdamAndEveConfig,
    AdamAndEveRiskExitConfig,
    CupAndHandleConfig,
    CupAndHandleRiskExitConfig,
    DiamondConfig,
    DiamondRiskExitConfig,
    FairValueGapConfig,
    FairValueGapRiskExitConfig,
    OrderBlockConfig,
    OrderBlockRiskExitConfig,
    PatternExitReason,
    PatternExitSimulationResult,
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    SoftInvalidationRule,
    TrendlineBreakConfig,
    TrendlineBreakRiskExitConfig,
    create_adam_and_eve_risk_exit_plan,
    create_cup_and_handle_risk_exit_plan,
    create_diamond_risk_exit_plan,
    create_fair_value_gap_risk_exit_plan,
    create_order_block_risk_exit_plan,
    create_trendline_break_risk_exit_plan,
    detect_adam_and_eve_patterns,
    detect_cup_and_handle_patterns,
    detect_diamond_patterns,
    detect_fair_value_gaps,
    detect_order_blocks,
    detect_trendline_breaks,
    simulate_pattern_exit,
)

PatternName = Literal[
    "FAIR_VALUE_GAP",
    "TRENDLINE_BREAK",
    "ORDER_BLOCK",
    "CUP_AND_HANDLE",
    "DIAMOND",
    "ADAM_AND_EVE",
]
DEFAULT_PATTERN: PatternName = "FAIR_VALUE_GAP"
SUPPORTED_PATTERNS: tuple[PatternName, ...] = (
    "FAIR_VALUE_GAP",
    "TRENDLINE_BREAK",
    "ORDER_BLOCK",
    "CUP_AND_HANDLE",
    "DIAMOND",
    "ADAM_AND_EVE",
)
PATTERN_STRATEGY_NAMES: dict[PatternName, str] = {
    pattern: f"{pattern}_PATTERN_STRATEGY" for pattern in SUPPORTED_PATTERNS
}


def validate_pattern_selection(patterns: Iterable[str]) -> tuple[PatternName, ...]:
    """Return one supported pattern identifier or raise a clear validation error."""

    selected = tuple(str(pattern).upper() for pattern in patterns)
    unsupported = [pattern for pattern in selected if pattern not in SUPPORTED_PATTERNS]
    if unsupported:
        supported = ", ".join(SUPPORTED_PATTERNS)
        raise ValueError(
            "unsupported pattern selection: "
            f"{', '.join(unsupported)}. Supported patterns: {supported}"
        )
    if len(selected) > 1:
        raise ValueError(
            "multiple pattern selections are not supported; select exactly one "
            f"pattern from: {', '.join(SUPPORTED_PATTERNS)}"
        )
    return cast(tuple[PatternName, ...], selected)


def strategy_name_for_patterns(patterns: Iterable[str]) -> str:
    """Return the deterministic strategy name for a supported single pattern."""

    selected = validate_pattern_selection(patterns)
    if not selected:
        return "NO_PATTERN_STRATEGY"
    return PATTERN_STRATEGY_NAMES[selected[0]]


@dataclass(frozen=True)
class PatternStrategyBacktestConfig:
    """Configuration for the first pattern strategy backtest workflow."""

    patterns: tuple[PatternName, ...] = (DEFAULT_PATTERN,)
    symbol: str | None = None
    timeframe: str | None = None
    fair_value_gap: FairValueGapConfig = field(default_factory=FairValueGapConfig)
    fair_value_gap_risk_exit: FairValueGapRiskExitConfig = field(
        default_factory=FairValueGapRiskExitConfig
    )
    trendline_break: TrendlineBreakConfig = field(default_factory=TrendlineBreakConfig)
    trendline_break_risk_exit: TrendlineBreakRiskExitConfig = field(
        default_factory=TrendlineBreakRiskExitConfig
    )
    order_block: OrderBlockConfig = field(default_factory=OrderBlockConfig)
    order_block_risk_exit: OrderBlockRiskExitConfig = field(
        default_factory=OrderBlockRiskExitConfig
    )
    cup_and_handle: CupAndHandleConfig = field(default_factory=CupAndHandleConfig)
    cup_and_handle_risk_exit: CupAndHandleRiskExitConfig = field(
        default_factory=CupAndHandleRiskExitConfig
    )
    diamond: DiamondConfig = field(default_factory=DiamondConfig)
    diamond_risk_exit: DiamondRiskExitConfig = field(
        default_factory=DiamondRiskExitConfig
    )
    adam_and_eve: AdamAndEveConfig = field(default_factory=AdamAndEveConfig)
    adam_and_eve_risk_exit: AdamAndEveRiskExitConfig = field(
        default_factory=AdamAndEveRiskExitConfig
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "patterns", validate_pattern_selection(self.patterns))


@dataclass(frozen=True)
class PatternStrategyBacktestTrade:
    """One simulated pattern entry and its exit-analysis outcome."""

    event_id: str
    pattern_type: str
    pattern_direction: str
    pattern_status: str
    pattern_timestamp: Any
    entry_timestamp: Any
    entry_candle_index: int
    entry_price: float
    risk_plan: RiskExitPlan
    exit_reason: PatternExitReason
    exit_timestamp: Any | None
    exit_candle_index: int | None
    exit_price: float | None
    realized_pnl_per_unit: float
    realized_r_multiple: float | None
    remaining_quantity_ratio: float
    exit_simulation: PatternExitSimulationResult
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatternStrategyBacktestResult:
    """Result returned by the pattern strategy backtest workflow."""

    trades: tuple[PatternStrategyBacktestTrade, ...]
    evaluated_candle_count: int
    seen_event_ids: tuple[str, ...]

    @property
    def trade_count(self) -> int:
        """Return the number of simulated pattern entries."""

        return len(self.trades)


def run_pattern_strategy_backtest(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    config: PatternStrategyBacktestConfig | None = None,
) -> PatternStrategyBacktestResult:
    """Run a pure historical pattern strategy backtest over completed candles.

    The workflow normalizes a defensive copy of standard candle data, evaluates
    rolling completed-candle prefixes, detects only the selected supported
    pattern, creates valid risk/exit plans, and delegates all exit decisions to
    ``simulate_pattern_exit``. Caller-provided candle data is not mutated.
    """

    backtest_config = config or PatternStrategyBacktestConfig()
    frame = _normalize_standard_candles(candles)
    if frame.empty or not backtest_config.patterns:
        return PatternStrategyBacktestResult((), len(frame), ())

    trades: list[PatternStrategyBacktestTrade] = []
    seen_event_ids: set[str] = set()
    row_index = 0

    while row_index < len(frame):
        prefix = frame.iloc[: row_index + 1].copy(deep=True)
        current_events = _detect_current_events(prefix, row_index, backtest_config)
        current_events = [event for event in current_events if event.event_id not in seen_event_ids]
        current_events.sort(key=_event_sort_key)

        entered_trade: PatternStrategyBacktestTrade | None = None
        for event in current_events:
            seen_event_ids.add(event.event_id)
            planned = _plan_event(event, prefix, backtest_config)
            if planned is None or planned.status != RiskExitPlanStatus.VALID:
                continue

            future_candles = frame.iloc[row_index + 1 :].copy(deep=True)
            exit_simulation = simulate_pattern_exit(
                planned,
                future_candles,
                soft_invalidation=_soft_invalidation_for_event(event, planned),
            )
            entered_trade = _build_trade(
                event=event,
                entry_candle=frame.iloc[row_index],
                entry_candle_index=row_index,
                risk_plan=planned,
                exit_simulation=exit_simulation,
            )
            trades.append(entered_trade)
            break

        if entered_trade is None:
            row_index += 1
            continue

        if entered_trade.exit_candle_index is None:
            break
        row_index = entered_trade.exit_candle_index + 1

    return PatternStrategyBacktestResult(
        trades=tuple(trades),
        evaluated_candle_count=len(frame),
        seen_event_ids=tuple(sorted(seen_event_ids)),
    )


def _normalize_standard_candles(candles: pd.DataFrame | Iterable[dict[str, Any]]) -> pd.DataFrame:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    missing = [column for column in STANDARD_CANDLE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required candle columns: {', '.join(missing)}")

    normalized = frame.loc[:, STANDARD_CANDLE_COLUMNS].copy(deep=True)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="raise")
    if not normalized.empty and not normalized["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    for column in NUMERIC_CANDLE_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
        if normalized[column].isna().any():
            raise ValueError(f"candle column contains missing values: {column}")
    if (normalized["high"] < normalized["low"]).any():
        raise ValueError("candle high must be greater than or equal to low")
    if (normalized["volume"] < 0).any():
        raise ValueError("candle volume must be non-negative")
    return normalized.reset_index(drop=True)


@dataclass(frozen=True)
class _PatternRegistryEntry:
    detector: Callable[[pd.DataFrame, PatternStrategyBacktestConfig], list[Any]]
    planner: Callable[[Any, pd.DataFrame, PatternStrategyBacktestConfig], Any]
    event_pattern_type: str


def _detect_fair_value_gap_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_fair_value_gaps(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.fair_value_gap,
    )


def _detect_trendline_break_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_trendline_breaks(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.trendline_break,
    )


def _detect_order_block_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_order_blocks(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.order_block,
    )


def _detect_cup_and_handle_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_cup_and_handle_patterns(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.cup_and_handle,
    )


def _detect_diamond_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_diamond_patterns(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.diamond,
    )


def _detect_adam_and_eve_events(
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    return detect_adam_and_eve_patterns(
        prefix,
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=config.adam_and_eve,
    )


def _plan_fair_value_gap_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_fair_value_gap_risk_exit_plan(
        event,
        config=config.fair_value_gap_risk_exit,
    )


def _plan_trendline_break_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_trendline_break_risk_exit_plan(
        event,
        candles=prefix,
        config=config.trendline_break_risk_exit,
    )


def _plan_order_block_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_order_block_risk_exit_plan(
        event,
        config=config.order_block_risk_exit,
    )


def _plan_cup_and_handle_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_cup_and_handle_risk_exit_plan(
        event,
        config=config.cup_and_handle_risk_exit,
    )


def _plan_diamond_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_diamond_risk_exit_plan(
        event,
        candles=prefix,
        config=config.diamond_risk_exit,
    )


def _plan_adam_and_eve_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> Any:
    return create_adam_and_eve_risk_exit_plan(
        event,
        config=config.adam_and_eve_risk_exit,
    )


PATTERN_REGISTRY: dict[PatternName, _PatternRegistryEntry] = {
    "FAIR_VALUE_GAP": _PatternRegistryEntry(
        detector=_detect_fair_value_gap_events,
        planner=_plan_fair_value_gap_event,
        event_pattern_type="FAIR_VALUE_GAP",
    ),
    "TRENDLINE_BREAK": _PatternRegistryEntry(
        detector=_detect_trendline_break_events,
        planner=_plan_trendline_break_event,
        event_pattern_type="TRENDLINE_BREAK",
    ),
    "ORDER_BLOCK": _PatternRegistryEntry(
        detector=_detect_order_block_events,
        planner=_plan_order_block_event,
        event_pattern_type="ORDER_BLOCK",
    ),
    "CUP_AND_HANDLE": _PatternRegistryEntry(
        detector=_detect_cup_and_handle_events,
        planner=_plan_cup_and_handle_event,
        event_pattern_type="CUP_AND_HANDLE",
    ),
    "DIAMOND": _PatternRegistryEntry(
        detector=_detect_diamond_events,
        planner=_plan_diamond_event,
        event_pattern_type="DIAMOND_PATTERN",
    ),
    "ADAM_AND_EVE": _PatternRegistryEntry(
        detector=_detect_adam_and_eve_events,
        planner=_plan_adam_and_eve_event,
        event_pattern_type="ADAM_AND_EVE_PATTERN",
    ),
}


def _detect_current_events(
    prefix: pd.DataFrame,
    row_index: int,
    config: PatternStrategyBacktestConfig,
) -> list[Any]:
    events: list[Any] = []
    for pattern in config.patterns:
        events.extend(PATTERN_REGISTRY[pattern].detector(prefix, config))
    return [event for event in events if event.end_index == row_index]


def _event_sort_key(event: Any) -> tuple[str, str, str]:
    return (event.pattern_type, event.direction, event.event_id)


def _plan_event(
    event: Any,
    prefix: pd.DataFrame,
    config: PatternStrategyBacktestConfig,
) -> RiskExitPlan | None:
    if event.pattern_status != "VALID":
        return None
    selected_pattern = config.patterns[0] if config.patterns else None
    if selected_pattern is None:
        return None
    registry_entry = PATTERN_REGISTRY[selected_pattern]
    if event.pattern_type != registry_entry.event_pattern_type:
        return None
    planned = registry_entry.planner(event, prefix, config)
    return planned.risk_plan


def _soft_invalidation_for_event(
    event: Any,
    plan: RiskExitPlan,
) -> SoftInvalidationRule | None:
    direction = _coerce_direction(plan.direction)
    if event.pattern_type == "FAIR_VALUE_GAP":
        operator = "<=" if direction == RiskExitDirection.LONG else ">="
        return SoftInvalidationRule(
            invalidates_when=f"close {operator} fvg_midpoint",
            reference_price=float(event.zone_mid),
        )
    if event.pattern_type == "TRENDLINE_BREAK":
        operator = "<=" if direction == RiskExitDirection.LONG else ">="
        return SoftInvalidationRule(
            invalidates_when=f"close {operator} trendline_value",
            reference_price=float(event.trendline_value),
        )
    if event.pattern_type == "CUP_AND_HANDLE":
        return SoftInvalidationRule(
            invalidates_when="close < neckline_after_breakout",
            reference_price=float(event.neckline),
        )
    if event.pattern_type == "DIAMOND_PATTERN":
        if direction == RiskExitDirection.LONG:
            return SoftInvalidationRule(
                invalidates_when="close <= upper_boundary_value",
                reference_price=float(event.upper_boundary_value),
            )
        return SoftInvalidationRule(
            invalidates_when="close >= lower_boundary_value",
            reference_price=float(event.lower_boundary_value),
        )
    if event.pattern_type == "ADAM_AND_EVE_PATTERN":
        return SoftInvalidationRule(
            invalidates_when="close < neckline_after_breakout",
            reference_price=float(event.neckline),
        )
    return None


def _build_trade(
    *,
    event: Any,
    entry_candle: pd.Series,
    entry_candle_index: int,
    risk_plan: RiskExitPlan,
    exit_simulation: PatternExitSimulationResult,
) -> PatternStrategyBacktestTrade:
    final_event = exit_simulation.events[-1] if exit_simulation.events else None
    exit_candle_index = None
    if final_event is not None:
        exit_candle_index = entry_candle_index + 1 + final_event.candle_index
    realized_pnl = _realized_pnl_per_unit(risk_plan, exit_simulation)
    realized_r = None
    if risk_plan.risk_per_unit is not None and risk_plan.risk_per_unit > 0:
        realized_r = realized_pnl / risk_plan.risk_per_unit

    return PatternStrategyBacktestTrade(
        event_id=event.event_id,
        pattern_type=event.pattern_type,
        pattern_direction=event.direction,
        pattern_status=event.pattern_status,
        pattern_timestamp=event.timestamp,
        entry_timestamp=entry_candle["timestamp"],
        entry_candle_index=entry_candle_index,
        entry_price=float(risk_plan.entry_price),
        risk_plan=risk_plan,
        exit_reason=exit_simulation.final_reason,
        exit_timestamp=final_event.timestamp if final_event is not None else None,
        exit_candle_index=exit_candle_index,
        exit_price=exit_simulation.final_price,
        realized_pnl_per_unit=realized_pnl,
        realized_r_multiple=realized_r,
        remaining_quantity_ratio=exit_simulation.remaining_quantity_ratio,
        exit_simulation=exit_simulation,
        metadata={
            "same_candle_entry_rule": "pattern_type_direction_event_id_order_first_valid_plan",
            "exit_evaluation": "starts_on_candle_after_entry",
        },
    )


def _realized_pnl_per_unit(
    plan: RiskExitPlan,
    exit_simulation: PatternExitSimulationResult,
) -> float:
    if plan.entry_price is None:
        return 0.0
    direction = _coerce_direction(plan.direction)
    total = 0.0
    for event in exit_simulation.events:
        if direction == RiskExitDirection.LONG:
            total += (event.price - plan.entry_price) * event.quantity_ratio
        else:
            total += (plan.entry_price - event.price) * event.quantity_ratio
    return total


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
