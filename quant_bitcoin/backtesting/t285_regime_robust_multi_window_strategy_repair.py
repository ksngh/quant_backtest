"""Task 285 regime-robust multi-window strategy repair runner.

This module is offline-only research code. It replays the rejected Task 283/284
candidate, applies deterministic repair filters, runs gap-aware multi-window
validation, persists simulated backtests, and writes a markdown report. It does
not fetch market data, read secrets, call exchange APIs, place orders, or manage
live positions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Iterable, Sequence

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, CostProfile
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.strategy_engine import (
    StrategyEngineConfig,
    run_strategy_backtest_engine,
)
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.backtesting import t283_principle_first_microstructure_strategy as t283
from quant_bitcoin.backtesting import t284_task283_multi_axis_robustness_revalidation as t284
from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    PostgresBacktestResultRepository,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
)


TASK_ID = "TASK_285"
PARENT_TASK_ID = "TASK_283"
PARENT_VALIDATION_TASK_ID = "TASK_284"
LOCKED_CANDIDATE_ID = "T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002"
DATABASE_URL = t283.DATABASE_URL
SOURCE = t283.SOURCE
SYMBOL = t283.SYMBOL
INTERVAL = t283.INTERVAL
STARTING_CASH = t283.STARTING_CASH
STRATEGY_KEY = "task285_regime_robust_multi_window_strategy_repair"
STRATEGY_NAME = "TASK285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR"
REPORT_PATH = Path("reports/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md")


@dataclass(frozen=True)
class Gap:
    previous_time: datetime
    next_time: datetime
    missing_candles: int


@dataclass(frozen=True)
class CompleteRange:
    start_time: datetime
    end_time: datetime
    candle_count: int


@dataclass(frozen=True)
class DataCoverage:
    requested_start_time: datetime
    available_start_time: datetime | None
    available_end_time: datetime | None
    candle_count: int
    gaps: tuple[Gap, ...]
    complete_ranges: tuple[CompleteRange, ...]
    april20_forward_complete: bool


@dataclass(frozen=True)
class WindowDefinition:
    window_id: str
    validation_group: str
    start_time: datetime
    end_time: datetime
    decision_role: str = "independent"
    allow_incomplete: bool = False

    def to_t283(self) -> t283.WindowSpec:
        return t283.WindowSpec(
            self.window_id,
            self.validation_group,
            self.start_time,
            self.end_time,
        )


@dataclass(frozen=True)
class CandidatePlan:
    candidate_id: str
    family: str
    source_candidate_id: str
    repair_mode: str
    thesis: str
    decision_role: str = "repair_candidate"
    explicit_single_side: str | None = None


@dataclass(frozen=True)
class RunSpec:
    candidate: CandidatePlan
    window: WindowDefinition
    cost_profile_key: str
    run_group: str
    validation_axis: str
    diagnostic_only: bool = False


@dataclass(frozen=True)
class CandidateAggregate:
    candidate_id: str
    independent_windows: int
    positive_windows: int
    positive_window_fraction: float | None
    aggregate_return: float | None
    net_pnl: float
    gross_pnl: float
    total_cost: float
    completed_round_trips: int
    cost_mismatch_count: int
    max_single_window_net_contribution: float | None
    return_without_top_three_winners: float | None
    earliest_window_cost_dominated: bool
    long_net_pnl: float
    long_trips: int
    short_net_pnl: float
    short_trips: int


@dataclass(frozen=True)
class RunRecord:
    spec: RunSpec
    run_id: int | None
    status: str
    skip_reason: str | None = None
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    candle_count: int = 0
    total_return: float | None = None
    final_equity: float | None = None
    trade_count: int = 0
    completed_round_trips: int = 0
    gross_pnl: float | None = None
    net_pnl: float | None = None
    max_drawdown: float | None = None
    win_rate: float | None = None
    profit_factor: float | None = None
    expectancy: float | None = None
    total_fee_cost: float | None = None
    total_spread_cost: float | None = None
    total_slippage_cost: float | None = None
    total_cost: float | None = None
    total_notional: float | None = None
    effective_total_cost_bps: float | None = None
    cost_to_gross_pnl_ratio: float | None = None
    action_entries_before_filter: int = 0
    action_entries: int = 0
    removed_entries: int = 0
    cost_formula_mismatch_count: int = 0
    summary_cost_mismatch_count: int = 0
    max_cost_mismatch: float = 0.0
    readback_ok: bool = False
    candle_continuity_ok: bool = False
    candle_gap_count: int = 0
    side_attribution: tuple[t284.BucketAttribution, ...] = ()
    session_attribution: tuple[t284.BucketAttribution, ...] = ()
    regime_attribution: tuple[t284.BucketAttribution, ...] = ()
    outlier_audit: t284.OutlierAudit = t284.OutlierAudit()
    event_net_pnls: tuple[float, ...] = ()


@dataclass(frozen=True)
class GateReport:
    status: str
    selected_candidate_id: str | None
    rows: tuple[tuple[str, str, str, bool], ...]
    failed_gates: tuple[str, ...]
    conclusion: str
    candidate_aggregates: tuple[CandidateAggregate, ...]


def build_candidate_plans() -> tuple[CandidatePlan, ...]:
    return (
        CandidatePlan(
            candidate_id="T285_BASE_LOCKED_B2",
            family="BASELINE_LOCKED_TASK283_B2",
            source_candidate_id=LOCKED_CANDIDATE_ID,
            repair_mode="baseline_no_repair",
            thesis="Locked Task 283/284 candidate replayed as the rejected baseline.",
            decision_role="baseline",
        ),
        CandidatePlan(
            candidate_id="T285_R1_SHORT_ONLY_B2",
            family="SINGLE_SIDE_FAILED_RALLY_SHORT",
            source_candidate_id=LOCKED_CANDIDATE_ID,
            repair_mode="short_only",
            thesis=(
                "Task 284 showed the edge was short-side concentrated, so this repair "
                "turns off the losing long sleeve and retests the thesis as a declared "
                "single-side failed-rally short model."
            ),
            explicit_single_side="SHORT",
        ),
        CandidatePlan(
            candidate_id="T285_R2_SHORT_REGIME_B2",
            family="REGIME_FILTERED_FAILED_RALLY_SHORT",
            source_candidate_id=LOCKED_CANDIDATE_ID,
            repair_mode="short_regime_filter",
            thesis=(
                "Short only when completed 15m/1h return pressure is not bullish and "
                "participation is adequate, reducing shorts in rebound or thin-drift regimes."
            ),
            explicit_single_side="SHORT",
        ),
        CandidatePlan(
            candidate_id="T285_R3_CORE_SHORT_ONLY_B2",
            family="CORE_ONLY_BEARISH_LIQUIDITY_SWEEP_SHORT",
            source_candidate_id=LOCKED_CANDIDATE_ID,
            repair_mode="core_short_only",
            thesis=(
                "Keep only the full-size core short layer and remove the small activity "
                "scout sleeve to test whether the signal survives without turnover padding."
            ),
            explicit_single_side="SHORT",
        ),
    )


def cost_profile_map() -> dict[str, CostProfile]:
    base = COST_PROFILES["conservative_crypto_1m"].config
    return {
        **COST_PROFILES,
        "cost_2x": CostProfile(
            "cost_2x",
            "Conservative 1m profile with fee, spread, slippage, minimum slippage, and volatility slippage doubled.",
            TransactionCostConfig(
                taker_fee_bps=base.taker_fee_bps * 2.0,
                spread_bps=base.spread_bps * 2.0,
                slippage_bps=base.slippage_bps * 2.0,
                minimum_slippage_bps=base.minimum_slippage_bps * 2.0,
                volatility_slippage_multiplier=base.volatility_slippage_multiplier * 2.0,
            ),
        ),
        "cost_3x": CostProfile(
            "cost_3x",
            "Conservative 1m profile with fee, spread, slippage, minimum slippage, and volatility slippage tripled.",
            TransactionCostConfig(
                taker_fee_bps=base.taker_fee_bps * 3.0,
                spread_bps=base.spread_bps * 3.0,
                slippage_bps=base.slippage_bps * 3.0,
                minimum_slippage_bps=base.minimum_slippage_bps * 3.0,
                volatility_slippage_multiplier=base.volatility_slippage_multiplier * 3.0,
            ),
        ),
    }


def parse_window_definition(value: str) -> WindowDefinition:
    text = value.strip()
    if "|" in text:
        parts = [part.strip() for part in text.split("|")]
    elif "," in text:
        parts = [part.strip() for part in text.split(",")]
    else:
        match = re.match(r"^([^:]+):(.+?Z):(.+?Z)$", text)
        if not match:
            raise ValueError("window must be name|start|end, name,start,end, or name:startZ:endZ")
        parts = [match.group(1), match.group(2), match.group(3)]
    if len(parts) != 3 or not all(parts):
        raise ValueError("window must include name, start, and end")
    start = _dt(parts[1])
    end = _dt(parts[2])
    if end <= start:
        raise ValueError("window end must be after start")
    return WindowDefinition(parts[0], "explicit_independent", start, end, "independent", False)


def load_window_config(path: str | Path) -> tuple[WindowDefinition, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("window config must be a JSON list")
    windows: list[WindowDefinition] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each window config item must be an object")
        window_id = str(item["name"])
        start = _dt(str(item["start"]))
        end = _dt(str(item["end"]))
        if end <= start:
            raise ValueError(f"window {window_id} end must be after start")
        windows.append(
            WindowDefinition(
                window_id=window_id,
                validation_group=str(item.get("validation_group") or "configured_independent"),
                start_time=start,
                end_time=end,
                decision_role=str(item.get("decision_role") or "independent"),
                allow_incomplete=bool(item.get("allow_incomplete", False)),
            )
        )
    return tuple(windows)


def detect_candle_gaps(candles: pd.DataFrame) -> tuple[Gap, ...]:
    if candles.empty:
        return ()
    timestamps = pd.to_datetime(candles["timestamp"], utc=True).sort_values().drop_duplicates()
    diffs = timestamps.diff()
    gaps: list[Gap] = []
    for idx in diffs[diffs > pd.Timedelta(minutes=1)].index:
        next_time = _as_utc(timestamps.loc[idx])
        previous_time = _as_utc(timestamps.loc[idx] - diffs.loc[idx])
        missing = int(diffs.loc[idx] / pd.Timedelta(minutes=1)) - 1
        gaps.append(Gap(previous_time, next_time, missing))
    return tuple(gaps)


def split_complete_ranges(candles: pd.DataFrame) -> tuple[CompleteRange, ...]:
    if candles.empty:
        return ()
    timestamps = list(pd.to_datetime(candles["timestamp"], utc=True).sort_values().drop_duplicates())
    if not timestamps:
        return ()
    ranges: list[CompleteRange] = []
    start = timestamps[0]
    previous = timestamps[0]
    count = 1
    for current in timestamps[1:]:
        if current - previous != pd.Timedelta(minutes=1):
            ranges.append(CompleteRange(_as_utc(start), _as_utc(previous), count))
            start = current
            count = 1
        else:
            count += 1
        previous = current
    ranges.append(CompleteRange(_as_utc(start), _as_utc(previous), count))
    return tuple(ranges)


def data_coverage(database_url: str) -> DataCoverage:
    availability = t283.load_data_availability(database_url)
    ranges: tuple[CompleteRange, ...] = ()
    gaps: tuple[Gap, ...] = ()
    if availability.available_start_time and availability.available_end_time:
        candles = t283.load_candles(
            database_url,
            t283.WindowSpec(
                "task285_coverage_audit",
                "coverage_audit",
                availability.available_start_time,
                availability.available_end_time,
            ),
        )
        gaps = detect_candle_gaps(candles)
        ranges = split_complete_ranges(candles)
    april20_complete = bool(
        availability.available_start_time
        and availability.available_start_time <= availability.requested_start_time
        and not gaps
    )
    return DataCoverage(
        requested_start_time=availability.requested_start_time,
        available_start_time=availability.available_start_time,
        available_end_time=availability.available_end_time,
        candle_count=availability.candle_count,
        gaps=gaps,
        complete_ranges=ranges,
        april20_forward_complete=april20_complete,
    )


def build_default_windows(latest: datetime) -> tuple[WindowDefinition, ...]:
    latest = _as_utc(latest)
    candidates = [
        WindowDefinition(
            "available_pre_owner_0510_0517",
            "independent_pre_owner",
            _dt("2026-05-10T00:00:00Z"),
            min(_dt("2026-05-17T15:19:00Z"), latest),
        ),
        WindowDefinition("owner_segment_0520_0522", "independent_owner_segment", _dt("2026-05-20T00:00:00Z"), min(_dt("2026-05-22T00:00:00Z"), latest)),
        WindowDefinition("owner_segment_0522_0524", "independent_owner_segment", _dt("2026-05-22T00:00:00Z"), min(_dt("2026-05-24T00:00:00Z"), latest)),
        WindowDefinition("owner_segment_0524_0526", "independent_owner_segment", _dt("2026-05-24T00:00:00Z"), min(_dt("2026-05-26T00:00:00Z"), latest)),
        WindowDefinition("owner_segment_0526_latest", "independent_owner_segment", _dt("2026-05-26T00:00:00Z"), latest),
        WindowDefinition("owner_0520_full", "owner_replay_diagnostic", _dt("2026-05-20T00:00:00Z"), latest, "diagnostic", False),
        WindowDefinition("owner_0525_full", "owner_replay_diagnostic", _dt("2026-05-25T00:00:00Z"), latest, "diagnostic", False),
    ]
    return tuple(window for window in candidates if window.end_time > window.start_time)


def build_auto_weekly_windows(coverage: DataCoverage) -> tuple[WindowDefinition, ...]:
    windows: list[WindowDefinition] = []
    for range_index, complete_range in enumerate(coverage.complete_ranges, start=1):
        start = complete_range.start_time
        end_limit = complete_range.end_time
        window_index = 1
        while start + pd.Timedelta(days=7) <= pd.Timestamp(end_limit):
            end = _as_utc(pd.Timestamp(start) + pd.Timedelta(days=7))
            windows.append(
                WindowDefinition(
                    f"auto_complete_range_{range_index}_week_{window_index}",
                    "auto_complete_weekly",
                    start,
                    end,
                    "independent",
                    False,
                )
            )
            start = end
            window_index += 1
    return tuple(windows)


def build_run_specs(
    *,
    windows: Sequence[WindowDefinition],
    selected_candidate_id: str | None = None,
    include_stress: bool = False,
    include_primary: bool = True,
) -> tuple[RunSpec, ...]:
    plans = build_candidate_plans()
    independent = [window for window in windows if window.decision_role == "independent"]
    diagnostic = [window for window in windows if window.decision_role != "independent"]
    specs: list[RunSpec] = []
    if include_primary:
        for plan in plans:
            for window in independent:
                specs.append(RunSpec(plan, window, "conservative_crypto_1m", "independent_primary", "multi_window_primary"))
    if selected_candidate_id:
        selected = next(plan for plan in plans if plan.candidate_id == selected_candidate_id)
        for window in diagnostic:
            specs.append(RunSpec(selected, window, "conservative_crypto_1m", "owner_overlap_diagnostic", "owner_diagnostic", True))
        if include_stress:
            for key in ("cost_2x", "cost_3x"):
                for window in independent:
                    specs.append(RunSpec(selected, window, key, "cost_stress", "cost_sensitivity", key == "cost_3x"))
    return tuple(specs)


def run_matrix(
    *,
    database_url: str,
    windows: Sequence[WindowDefinition] | None = None,
    limit: int | None = None,
) -> list[RunRecord]:
    coverage = data_coverage(database_url)
    if coverage.available_end_time is None:
        gate = classify_records([], coverage)
        write_report([], coverage=coverage, gate_report=gate)
        return []
    selected_windows = tuple(windows) if windows is not None else build_default_windows(coverage.available_end_time)
    primary_specs = build_run_specs(windows=selected_windows)
    records: list[RunRecord] = []
    sequence = 0
    for spec in primary_specs:
        sequence += 1
        if limit is not None and sequence > limit:
            gate = classify_records(records, coverage)
            write_report(records, coverage=coverage, gate_report=gate)
            return records
        records.append(run_one(database_url=database_url, spec=spec))
    preliminary_gate = classify_records(records, coverage)
    if preliminary_gate.selected_candidate_id is not None:
        stress_specs = build_run_specs(
            windows=selected_windows,
            selected_candidate_id=preliminary_gate.selected_candidate_id,
            include_stress=True,
            include_primary=False,
        )
        for spec in stress_specs:
            sequence += 1
            if limit is not None and sequence > limit:
                break
            records.append(run_one(database_url=database_url, spec=spec))
    gate = classify_records(records, coverage)
    write_report(records, coverage=coverage, gate_report=gate)
    return records


def run_one(*, database_url: str, spec: RunSpec) -> RunRecord:
    candles = t283.load_candles(database_url, spec.window.to_t283())
    if candles.empty:
        return _skipped_record(spec, "no_local_candles_for_window")
    quality = t283.candle_quality(candles)
    if not bool(quality["candle_continuity_ok"]) and not spec.window.allow_incomplete:
        return _skipped_record(spec, "local_candle_continuity_gap", quality=quality, candle_count=len(candles))
    profiles = cost_profile_map()
    cost_profile = profiles[spec.cost_profile_key]
    source_candidate = candidate_by_id(spec.candidate.source_candidate_id)
    actions, action_meta = generate_task285_actions(candles, spec.candidate, source_candidate, cost_profile)
    config = StrategyEngineConfig(
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        transaction_cost_config=cost_profile.config,
        default_liquidity_role=LiquidityRole.TAKER,
        allow_short=True,
        interval=INTERVAL,
        position_sizing=PositionSizingConfig(
            mode=PositionSizingMode.FIXED_QUANTITY,
            insufficient_funds_policy=InsufficientFundsPolicy.RESIZE,
        ),
        short_exposure_mode=ShortExposureMode.CASH_BOUNDED,
        enforce_candle_continuity=True,
    )
    result = run_strategy_backtest_engine(candles, actions, config=config)
    metadata = result.summary.metadata if isinstance(result.summary.metadata, dict) else {}
    research = {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "scope": "offline_backtest_research_only",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "parent_validation_task_id": PARENT_VALIDATION_TASK_ID,
        "source_candidate_id": spec.candidate.source_candidate_id,
        "candidate_id": spec.candidate.candidate_id,
        "candidate_family": spec.candidate.family,
        "repair_mode": spec.candidate.repair_mode,
        "explicit_single_side": spec.candidate.explicit_single_side,
        "window_id": spec.window.window_id,
        "validation_group": spec.window.validation_group,
        "decision_role": spec.window.decision_role,
        "run_group": spec.run_group,
        "validation_axis": spec.validation_axis,
        "diagnostic_only": spec.diagnostic_only,
        "cost_profile": spec.cost_profile_key,
        "no_live_trading": True,
        "research_only": True,
    }
    metadata["research"] = research
    metadata["task285_validation"] = {
        "schema_version": "task285_validation_metadata_v1",
        "source_candidate_id": spec.candidate.source_candidate_id,
        "repair_mode": spec.candidate.repair_mode,
        "action_entries_before_filter": action_meta.signal_counts.get("before_filter", action_meta.generated_entries),
        "action_entries": action_meta.generated_entries,
        "removed_entries": action_meta.cost_rejections,
        "action_signal_counts": action_meta.signal_counts,
        "action_exit_reasons": action_meta.exit_reasons,
        "window_complete_required": not spec.window.allow_incomplete,
        "signal_execution_separated": True,
        "completed_candle_only": True,
        "intrabar_ambiguity_policy": "stop_first_when_stop_and_target_hit_same_candle",
    }
    metadata["cost_profile"] = cost_profile.to_metadata()
    repository = PostgresBacktestResultRepository(database_url)
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=spec.window.start_time,
        end_time=spec.window.end_time,
        strategy_key=STRATEGY_KEY,
        strategy_name=STRATEGY_NAME,
        strategy_version=f"task285_{spec.candidate.candidate_id}_{spec.window.window_id}_{spec.cost_profile_key}_v1",
        strategy_parameters={
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "source_candidate_id": spec.candidate.source_candidate_id,
            "candidate": spec.candidate.candidate_id,
            "family": spec.candidate.family,
            "repair_mode": spec.candidate.repair_mode,
            "thesis": spec.candidate.thesis,
            "window": {
                "window_id": spec.window.window_id,
                "validation_group": spec.window.validation_group,
                "decision_role": spec.window.decision_role,
                "start_time": _iso(spec.window.start_time),
                "end_time": _iso(spec.window.end_time),
                "allow_incomplete": spec.window.allow_incomplete,
            },
            "cost_profile_key": spec.cost_profile_key,
            "cost_profile": cost_profile.to_metadata(),
            "research": research,
        },
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        engine_name="StrategyEngine",
        engine_version="strategy_engine_v1",
        run_metadata={
            "research": research,
            "cost_profile": cost_profile.to_metadata(),
            "task285_validation": metadata["task285_validation"],
        },
    )
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    if persisted is None:
        raise RuntimeError(f"Task 285 persisted run could not be read back: {run_id}")
    return analyze_persisted_run(
        persisted,
        spec=spec,
        quality=quality,
        action_entries_before_filter=action_meta.signal_counts.get("before_filter", action_meta.generated_entries),
        action_entries=action_meta.generated_entries,
        removed_entries=action_meta.cost_rejections,
    )


def generate_task285_actions(
    candles: pd.DataFrame,
    plan: CandidatePlan,
    source_candidate: t283.CandidateSpec,
    cost_profile: CostProfile,
) -> tuple[list[StrategyAction], t283.ActionGenerationMetadata]:
    actions, base_meta = t283.generate_actions(candles, source_candidate, cost_config=cost_profile.config)
    filtered = filter_actions_for_plan(actions, plan)
    before_entries = len([action for action in actions if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}])
    after_entries = len([action for action in filtered if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}])
    exit_reasons: dict[str, int] = defaultdict(int)
    side_counts: dict[str, int] = defaultdict(int)
    for action in filtered:
        if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}:
            side_counts[str(action.metadata.get("position_side") or "UNKNOWN")] += 1
        if action.action_type in {StrategyActionType.EXIT_LONG, StrategyActionType.EXIT_SHORT}:
            exit_reasons[str(action.metadata.get("exit_reason") or action.reason or "UNKNOWN")] += 1
    return filtered, t283.ActionGenerationMetadata(
        generated_entries=after_entries,
        cost_rejections=max(0, before_entries - after_entries),
        signal_counts={
            "before_filter": before_entries,
            "after_filter": after_entries,
            "removed_by_task285_filter": max(0, before_entries - after_entries),
            "base_generated_entries": base_meta.generated_entries,
            **{f"side_{key}": value for key, value in side_counts.items()},
        },
        exit_reasons=dict(exit_reasons),
        factor_schema_version=base_meta.factor_schema_version,
    )


def filter_actions_for_plan(actions: Sequence[StrategyAction], plan: CandidatePlan) -> list[StrategyAction]:
    grouped: dict[str, list[StrategyAction]] = defaultdict(list)
    order: list[str] = []
    for action in actions:
        event_id = str(action.metadata.get("event_id") or action.metadata.get("pattern_event_id") or "")
        if not event_id:
            continue
        if event_id not in grouped:
            order.append(event_id)
        grouped[event_id].append(action)
    filtered: list[StrategyAction] = []
    for event_id in order:
        group = grouped[event_id]
        entry = next((action for action in group if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}), None)
        if entry is None:
            continue
        if _allow_event(entry, plan):
            filtered.extend(_copy_action_for_task285(action, plan) for action in group)
    return filtered


def _allow_event(entry: StrategyAction, plan: CandidatePlan) -> bool:
    if plan.repair_mode == "baseline_no_repair":
        return True
    side = str(entry.metadata.get("position_side") or "")
    snapshot = entry.metadata.get("task283_factor_snapshot")
    if not isinstance(snapshot, dict):
        snapshot = {}
    if plan.repair_mode == "short_only":
        return side == "SHORT"
    if plan.repair_mode == "core_short_only":
        return side == "SHORT" and str(entry.metadata.get("task283_layer") or "").lower() == "core"
    if plan.repair_mode == "short_regime_filter":
        trend_15 = _float(snapshot.get("mtf_15m_trend_bps")) or 0.0
        trend_60 = _float(snapshot.get("mtf_1h_trend_bps")) or 0.0
        volume_ratio = _float(snapshot.get("volume_ratio_20")) or 0.0
        realized_vol = _float(snapshot.get("realized_vol_percentile_240"))
        volatility_ok = realized_vol is None or realized_vol >= 0.20
        return side == "SHORT" and (trend_15 + trend_60) <= 20.0 and volume_ratio >= 0.75 and volatility_ok
    raise ValueError(f"unsupported Task 285 repair mode: {plan.repair_mode}")


def _copy_action_for_task285(action: StrategyAction, plan: CandidatePlan) -> StrategyAction:
    metadata = {
        **action.metadata,
        "task285_candidate_id": plan.candidate_id,
        "task285_candidate_family": plan.family,
        "task285_repair_mode": plan.repair_mode,
        "task285_explicit_single_side": plan.explicit_single_side,
        "task285_source_candidate_id": plan.source_candidate_id,
        "task285_offline_research_only": True,
    }
    return StrategyAction(
        action_type=action.action_type,
        timestamp=action.timestamp,
        quantity=action.quantity,
        reason=action.reason,
        metadata=metadata,
        requested_price=action.requested_price,
        quantity_mode=action.quantity_mode,
    )


def analyze_persisted_run(
    persisted: BacktestRunReadModel,
    *,
    spec: RunSpec,
    quality: dict[str, Any],
    action_entries_before_filter: int,
    action_entries: int,
    removed_entries: int,
) -> RunRecord:
    summary = persisted.summary
    metadata = summary.metadata or {}
    cost_summary = metadata.get("cost_summary") if isinstance(metadata.get("cost_summary"), dict) else {}
    event_rows = t284.event_trade_rows(persisted.trades)
    event_net_pnls = [float(row["net_pnl"]) for row in event_rows]
    cost_audit = t283.audit_persisted_trade_costs(persisted.trades)
    summary_audit = t284.audit_summary_costs(cost_summary, cost_audit)
    perf = t283._realized_trade_stats(event_net_pnls, [])
    side_attr = t284.bucket_attribution(event_rows, key="side")
    session_attr = t284.bucket_attribution(event_rows, key="session")
    regime_attr = (
        *t284.bucket_attribution(event_rows, key="volatility_regime"),
        *t284.bucket_attribution(event_rows, key="trend_alignment"),
        *t284.bucket_attribution(event_rows, key="volume_regime"),
    )
    research = (persisted.run.metadata or {}).get("research") or {}
    summary_research = metadata.get("research") if isinstance(metadata.get("research"), dict) else {}
    validation_meta = (persisted.run.metadata or {}).get("task285_validation") or {}
    readback_ok = bool(
        research.get("task_id") == TASK_ID
        and summary_research.get("task_id") == TASK_ID
        and research.get("candidate_id") == spec.candidate.candidate_id
        and summary_research.get("candidate_id") == spec.candidate.candidate_id
        and validation_meta.get("repair_mode") == spec.candidate.repair_mode
    )
    return RunRecord(
        spec=spec,
        run_id=persisted.run.id,
        status="COMPLETED_RESEARCH_ONLY",
        actual_start_time=persisted.run.actual_start_time,
        actual_end_time=persisted.run.actual_end_time,
        candle_count=int(persisted.run.candle_count),
        total_return=float(summary.total_return),
        final_equity=float(summary.final_equity),
        trade_count=int(summary.trade_count),
        completed_round_trips=len(event_net_pnls),
        gross_pnl=_float(cost_summary.get("gross_pnl")),
        net_pnl=_float(cost_summary.get("net_pnl")),
        max_drawdown=float((metadata.get("performance_metrics") or {}).get("max_drawdown") or 0.0),
        win_rate=_float(perf.get("win_rate")),
        profit_factor=_float(perf.get("profit_factor")),
        expectancy=_float(perf.get("expectancy")),
        total_fee_cost=cost_audit.total_fee_cost,
        total_spread_cost=cost_audit.total_spread_cost,
        total_slippage_cost=cost_audit.total_slippage_cost,
        total_cost=cost_audit.total_cost,
        total_notional=cost_audit.total_notional,
        effective_total_cost_bps=cost_audit.effective_total_cost_bps,
        cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
        action_entries_before_filter=action_entries_before_filter,
        action_entries=action_entries,
        removed_entries=removed_entries,
        cost_formula_mismatch_count=cost_audit.mismatch_count,
        summary_cost_mismatch_count=summary_audit.mismatch_count,
        max_cost_mismatch=max(cost_audit.max_abs_mismatch, summary_audit.max_abs_mismatch),
        readback_ok=readback_ok,
        candle_continuity_ok=bool(quality.get("candle_continuity_ok")),
        candle_gap_count=int(quality.get("candle_gap_count") or 0),
        side_attribution=side_attr,
        session_attribution=session_attr,
        regime_attribution=regime_attr,
        outlier_audit=t284.outlier_audit(event_net_pnls, _float(cost_summary.get("net_pnl")) or 0.0),
        event_net_pnls=tuple(event_net_pnls),
    )


def classify_records(records: Sequence[RunRecord], coverage: DataCoverage) -> GateReport:
    aggregates = candidate_aggregates(records)
    repair_aggregates = [agg for agg in aggregates if _candidate_plan(agg.candidate_id).decision_role != "baseline"]
    selected = max(repair_aggregates, key=lambda agg: agg.aggregate_return if agg.aggregate_return is not None else -math.inf, default=None)
    if selected is None:
        return GateReport(
            status="BLOCKED",
            selected_candidate_id=None,
            rows=(("Repair candidates", ">= 1 completed", "0", False),),
            failed_gates=("Repair candidates",),
            conclusion="No completed repair-candidate records were available.",
            candidate_aggregates=aggregates,
        )
    stress_2x = aggregate_for_cost(records, selected.candidate_id, "cost_2x")
    stress_3x = aggregate_for_cost(records, selected.candidate_id, "cost_3x")
    single_side_ok = True
    plan = _candidate_plan(selected.candidate_id)
    if plan.explicit_single_side is None and (selected.long_net_pnl <= 0.0 or selected.short_net_pnl <= 0.0):
        single_side_ok = False
    rows = (
        ("Independent complete windows", ">= 4 when data allows", str(selected.independent_windows), selected.independent_windows >= 4),
        ("Total completed round trips", ">= 50", str(selected.completed_round_trips), selected.completed_round_trips >= 50),
        ("Positive independent windows", ">= 75pct", _ratio(selected.positive_window_fraction), bool(selected.positive_window_fraction is not None and selected.positive_window_fraction >= 0.75)),
        ("Aggregate independent return", ">= +3pct", _pct(selected.aggregate_return), bool(selected.aggregate_return is not None and selected.aggregate_return >= 0.03)),
        ("Single-window net contribution", "<= 60pct", _ratio(selected.max_single_window_net_contribution), bool(selected.max_single_window_net_contribution is not None and selected.max_single_window_net_contribution <= 0.60)),
        ("Return without top-three winners", "> 0pct", _pct(selected.return_without_top_three_winners), bool(selected.return_without_top_three_winners is not None and selected.return_without_top_three_winners > 0.0)),
        ("Cost audit mismatches", "0", str(selected.cost_mismatch_count), selected.cost_mismatch_count == 0),
        ("Earliest OOS cost domination", "not gross positive / net negative", str(selected.earliest_window_cost_dominated), not selected.earliest_window_cost_dominated),
        ("Side classification", "single-side declared or both sleeves healthy", plan.explicit_single_side or "multi-side", single_side_ok),
        ("2x cost stress", "> -1pct aggregate", _pct(stress_2x.aggregate_return if stress_2x else None), bool(stress_2x and stress_2x.aggregate_return is not None and stress_2x.aggregate_return > -0.01)),
        ("3x cost stress", "reported", _pct(stress_3x.aggregate_return if stress_3x else None), stress_3x is not None),
        ("Formula and summary cost audit", "0 mismatches", str(selected.cost_mismatch_count), selected.cost_mismatch_count == 0),
        ("Fixed owner windows not sole proof", "independent windows used", str(selected.independent_windows), selected.independent_windows >= 4),
    )
    failed = tuple(name for name, _, _, ok in rows if not ok)
    if selected.independent_windows < 4:
        status = "DATA_LIMITED_RESEARCH_ONLY"
    elif failed:
        status = "ROBUSTNESS_REJECTED_RESEARCH_ONLY"
    else:
        status = "ROBUST_MULTI_WINDOW_RESEARCH_CANDIDATE"
    conclusion_bits = [
        f"selected `{selected.candidate_id}` with aggregate independent return {_pct(selected.aggregate_return)}",
        f"{selected.completed_round_trips} independent trips",
    ]
    if not coverage.april20_forward_complete:
        conclusion_bits.append("complete April-20-forward data remains unavailable")
    if failed:
        conclusion_bits.append(f"failed gates: {', '.join(failed)}")
    else:
        conclusion_bits.append("all Task 285 promotion gates passed under local data constraints")
    return GateReport(
        status=status,
        selected_candidate_id=selected.candidate_id,
        rows=rows,
        failed_gates=failed,
        conclusion="; ".join(conclusion_bits),
        candidate_aggregates=aggregates,
    )


def candidate_aggregates(records: Sequence[RunRecord]) -> tuple[CandidateAggregate, ...]:
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        if (
            record.run_id is not None
            and record.spec.window.decision_role == "independent"
            and record.spec.cost_profile_key == "conservative_crypto_1m"
            and not record.spec.diagnostic_only
        ):
            grouped[record.spec.candidate.candidate_id].append(record)
    return tuple(_aggregate_candidate(candidate_id, values) for candidate_id, values in sorted(grouped.items()))


def aggregate_for_cost(records: Sequence[RunRecord], candidate_id: str, cost_profile_key: str) -> CandidateAggregate | None:
    values = [
        record
        for record in records
        if record.run_id is not None
        and record.spec.candidate.candidate_id == candidate_id
        and record.spec.window.decision_role == "independent"
        and record.spec.cost_profile_key == cost_profile_key
    ]
    return _aggregate_candidate(candidate_id, values) if values else None


def _aggregate_candidate(candidate_id: str, values: Sequence[RunRecord]) -> CandidateAggregate:
    net_values = [float(record.net_pnl or 0.0) for record in values]
    gross = sum(float(record.gross_pnl or 0.0) for record in values)
    net = sum(net_values)
    total_cost = sum(float(record.total_cost or 0.0) for record in values)
    positive = len([value for value in net_values if value > 0.0])
    positive_net = sum(value for value in net_values if value > 0.0)
    max_contribution = None if positive_net <= 0.0 else max((value for value in net_values if value > 0.0), default=0.0) / positive_net
    event_pnls = [pnl for record in values for pnl in record.event_net_pnls]
    winners = sorted((pnl for pnl in event_pnls if pnl > 0.0), reverse=True)
    without_top_three = (net - sum(winners[:3])) / STARTING_CASH if values else None
    ordered = sorted(values, key=lambda record: record.spec.window.start_time)
    earliest = ordered[0] if ordered else None
    long_net = long_trips = short_net = short_trips = 0
    for record in values:
        for row in record.side_attribution:
            if row.bucket == "LONG":
                long_net += row.net_pnl
                long_trips += row.completed_round_trips
            if row.bucket == "SHORT":
                short_net += row.net_pnl
                short_trips += row.completed_round_trips
    return CandidateAggregate(
        candidate_id=candidate_id,
        independent_windows=len(values),
        positive_windows=positive,
        positive_window_fraction=None if not values else positive / len(values),
        aggregate_return=None if not values else net / STARTING_CASH,
        net_pnl=net,
        gross_pnl=gross,
        total_cost=total_cost,
        completed_round_trips=sum(record.completed_round_trips for record in values),
        cost_mismatch_count=sum(record.cost_formula_mismatch_count + record.summary_cost_mismatch_count for record in values),
        max_single_window_net_contribution=max_contribution,
        return_without_top_three_winners=without_top_three,
        earliest_window_cost_dominated=bool(earliest and (earliest.gross_pnl or 0.0) > 0.0 and (earliest.net_pnl or 0.0) < 0.0),
        long_net_pnl=long_net,
        long_trips=long_trips,
        short_net_pnl=short_net,
        short_trips=short_trips,
    )


def write_report(
    records: Sequence[RunRecord],
    *,
    coverage: DataCoverage,
    gate_report: GateReport,
) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_ids = ", ".join(str(record.run_id) for record in records if record.run_id is not None) or "-"
    lines = [
        "# Task 285 Regime-Robust Multi-Window Strategy Repair",
        "",
        f"Status: `{gate_report.status}`",
        "",
        "## Purpose",
        "",
        "- Repair or reject the Task 283/284 candidate using configurable, gap-aware, non-overlapping BTCUSDT 1m validation windows.",
        "- Result scope: offline research-only, no live trading, no exchange orders, no futures/leverage.",
        "",
        "## Data Coverage",
        "",
        f"- Requested April-20-forward start: `{_iso(coverage.requested_start_time)}`.",
        f"- Local available start: `{_iso(coverage.available_start_time)}`.",
        f"- Local available end: `{_iso(coverage.available_end_time)}`.",
        f"- Closed candle count from requested start: `{coverage.candle_count}`.",
        f"- Continuity gaps: `{len(coverage.gaps)}`.",
        f"- April-20-forward complete: `{coverage.april20_forward_complete}`.",
    ]
    if coverage.gaps:
        lines.extend(["", "| Gap Previous Candle | Gap Next Candle | Missing 1m Candles |", "| --- | --- | ---: |"])
        for gap in coverage.gaps:
            lines.append(f"| `{_iso(gap.previous_time)}` | `{_iso(gap.next_time)}` | {gap.missing_candles} |")
    lines.extend(["", "### Complete Local Ranges", "", "| Start | End | Candles |", "| --- | --- | ---: |"])
    for complete_range in coverage.complete_ranges:
        lines.append(f"| `{_iso(complete_range.start_time)}` | `{_iso(complete_range.end_time)}` | {complete_range.candle_count} |")

    lines.extend(["", "## Candidate Repair Set", "", "| Candidate | Family | Repair Mode | Thesis |", "| --- | --- | --- | --- |"])
    for plan in build_candidate_plans():
        lines.append(f"| `{plan.candidate_id}` | `{plan.family}` | `{plan.repair_mode}` | {plan.thesis} |")

    lines.extend(
        [
            "",
            "## Persisted Runs",
            "",
            f"- Task 285 run IDs: `{run_ids}`.",
            "",
            "| Candidate | Group | Window | Role | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Formula MM | Summary MM | Status |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.spec.candidate.candidate_id,
                    record.spec.run_group,
                    record.spec.window.window_id,
                    record.spec.window.decision_role,
                    record.spec.cost_profile_key,
                    str(record.run_id) if record.run_id is not None else "-",
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    _ratio(record.win_rate),
                    _ratio(record.profit_factor),
                    _money(record.gross_pnl),
                    _money(record.net_pnl),
                    _money(record.total_cost),
                    _ratio(record.cost_to_gross_pnl_ratio),
                    str(record.cost_formula_mismatch_count),
                    str(record.summary_cost_mismatch_count),
                    record.status if record.run_id is not None else str(record.skip_reason),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Candidate Aggregates", "", "| Candidate | Windows | Positive | Return | Trips | Gross | Net | Cost | Max Window Contrib | No Top3 Return | Long Net | Short Net | Cost MM |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for aggregate in gate_report.candidate_aggregates:
        lines.append(
            "| "
            + " | ".join(
                [
                    aggregate.candidate_id,
                    str(aggregate.independent_windows),
                    _ratio(aggregate.positive_window_fraction),
                    _pct(aggregate.aggregate_return),
                    str(aggregate.completed_round_trips),
                    _money(aggregate.gross_pnl),
                    _money(aggregate.net_pnl),
                    _money(aggregate.total_cost),
                    _ratio(aggregate.max_single_window_net_contribution),
                    _pct(aggregate.return_without_top_three_winners),
                    _money(aggregate.long_net_pnl),
                    _money(aggregate.short_net_pnl),
                    str(aggregate.cost_mismatch_count),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Gate Check", "", f"- Selected candidate: `{gate_report.selected_candidate_id or '-'}`.", "", "| Gate | Required | Observed | Status |", "| --- | --- | --- | --- |"])
    for name, required, observed, ok in gate_report.rows:
        lines.append(f"| {name} | {required} | {observed} | `{'PASS' if ok else 'FAIL'}` |")

    lines.extend(["", "## Cost Audit", ""])
    for record in records:
        if record.run_id is None:
            continue
        lines.append(
            f"- Run `{record.run_id}` `{record.spec.candidate.candidate_id}` `{record.spec.window.window_id}` `{record.spec.cost_profile_key}`: notional `{_money(record.total_notional)}`, fee `{_money(record.total_fee_cost)}`, spread `{_money(record.total_spread_cost)}`, slippage `{_money(record.total_slippage_cost)}`, total `{_money(record.total_cost)}`, one-way cost `{_ratio(record.effective_total_cost_bps)}` bps, formula mismatch `{record.cost_formula_mismatch_count}`, summary mismatch `{record.summary_cost_mismatch_count}`."
        )

    selected_records = [
        record
        for record in records
        if record.run_id is not None
        and record.spec.candidate.candidate_id == gate_report.selected_candidate_id
        and record.spec.window.decision_role == "independent"
        and record.spec.cost_profile_key == "conservative_crypto_1m"
    ]
    if selected_records:
        lines.extend(["", "## Selected Candidate Attribution", "", "### Side Aggregate", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in aggregate_bucket_rows(selected_records, "side_attribution"):
            lines.append(_bucket_row(row))
        lines.extend(["", "### Session Aggregate", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in aggregate_bucket_rows(selected_records, "session_attribution"):
            lines.append(_bucket_row(row))
        lines.extend(["", "### Regime Aggregate", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in aggregate_bucket_rows(selected_records, "regime_attribution"):
            lines.append(_bucket_row(row))

    lines.extend(
        [
            "",
            "## Bias And Safety Checks",
            "",
            "- Signal/entry separation: inherited Task 283 B2 next-open entry and next-open-after-exit-condition behavior.",
            "- Completed-candle factors: inherited Task 283 factor snapshots; no future candle fields are used for entries.",
            "- Incomplete windows: skipped unless a window explicitly allows incomplete diagnostics.",
            "- Fixed owner windows: diagnostic-only in Task 285 gate logic.",
            "- Cost handling: entry/exit taker fees, spread, slippage, minimum slippage, and volatility slippage are included.",
            "- Stress handling: selected repair candidate is retested at 2x and 3x cost assumptions.",
            "- Live trading safety: no execution client imports, no signed requests, no API keys, no `.env` handling, no order/account endpoints.",
            "",
            "## Conclusion",
            "",
            f"- Final status: `{gate_report.status}`.",
            f"- Failed gates: `{', '.join(gate_report.failed_gates) if gate_report.failed_gates else '-'}`.",
            f"- Interpretation: {gate_report.conclusion}.",
            "- No Task 285 result is promoted beyond research-only unless the status is explicitly `ROBUST_MULTI_WINDOW_RESEARCH_CANDIDATE` and a later task assigns paper-trading design.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def aggregate_bucket_rows(records: Sequence[RunRecord], attr_name: str) -> tuple[t284.BucketAttribution, ...]:
    grouped: dict[str, list[t284.BucketAttribution]] = defaultdict(list)
    for record in records:
        for row in getattr(record, attr_name):
            grouped[row.bucket].append(row)
    output: list[t284.BucketAttribution] = []
    for bucket, rows in sorted(grouped.items()):
        trips = sum(row.completed_round_trips for row in rows)
        gross = sum(row.gross_pnl for row in rows)
        cost = sum(row.total_cost for row in rows)
        net = sum(row.net_pnl for row in rows)
        wins_estimate = sum((row.win_rate or 0.0) * row.completed_round_trips for row in rows)
        output.append(
            t284.BucketAttribution(
                bucket=bucket,
                completed_round_trips=trips,
                gross_pnl=gross,
                total_cost=cost,
                net_pnl=net,
                win_rate=None if trips == 0 else wins_estimate / trips,
                average_net_pnl=None if trips == 0 else net / trips,
            )
        )
    return tuple(output)


def candidate_by_id(candidate_id: str) -> t283.CandidateSpec:
    for candidate in t283.build_candidates():
        if candidate.variant_id == candidate_id:
            return candidate
    raise ValueError(f"unknown Task 283 candidate: {candidate_id}")


def _candidate_plan(candidate_id: str) -> CandidatePlan:
    for plan in build_candidate_plans():
        if plan.candidate_id == candidate_id:
            return plan
    raise ValueError(f"unknown Task 285 candidate: {candidate_id}")


def _skipped_record(
    spec: RunSpec,
    reason: str,
    *,
    quality: dict[str, Any] | None = None,
    candle_count: int = 0,
) -> RunRecord:
    return RunRecord(
        spec=spec,
        run_id=None,
        status="SKIPPED",
        skip_reason=reason,
        candle_count=candle_count,
        candle_continuity_ok=bool((quality or {}).get("candle_continuity_ok", False)),
        candle_gap_count=int((quality or {}).get("candle_gap_count", 0) or 0),
    )


def _bucket_row(row: t284.BucketAttribution) -> str:
    return (
        f"| {row.bucket} | {row.completed_round_trips} | {_ratio(row.win_rate)} | "
        f"{_money(row.gross_pnl)} | {_money(row.total_cost)} | {_money(row.net_pnl)} | {_money(row.average_net_pnl)} |"
    )


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _as_utc(value: datetime | pd.Timestamp) -> datetime:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(timezone.utc)
    return timestamp.tz_convert(timezone.utc).to_pydatetime()


def _iso(value: datetime | pd.Timestamp | None) -> str:
    if value is None:
        return "-"
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:+.4f}pct"


def _money(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task 285 regime-robust multi-window strategy repair.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--window", action="append", default=[], help="Named window as name|start|end, name,start,end, or name:startZ:endZ")
    parser.add_argument("--window-config", default=None, help="JSON list of named windows.")
    parser.add_argument("--auto-weekly-windows", action="store_true", help="Use auto-discovered complete weekly windows instead of defaults when available.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    windows: tuple[WindowDefinition, ...] | None = None
    if args.window_config:
        windows = load_window_config(args.window_config)
    if args.window:
        explicit = tuple(parse_window_definition(value) for value in args.window)
        windows = explicit if windows is None else (*windows, *explicit)
    if args.auto_weekly_windows:
        coverage = data_coverage(args.database_url)
        auto = build_auto_weekly_windows(coverage)
        if auto:
            windows = auto if windows is None else (*windows, *auto)

    records = run_matrix(database_url=args.database_url, windows=windows, limit=args.limit)
    persisted = len([record for record in records if record.run_id is not None])
    print(f"wrote {REPORT_PATH} with {persisted} persisted Task 285 runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
