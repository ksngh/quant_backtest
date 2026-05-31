"""Task 287 repaired April-20-forward locked OOS/WFO validation.

This module is offline-only research code. It replays previously locked BTCUSDT
1m candidates unchanged on the repaired local candle dataset, persists every
decision-driving simulation, and writes a markdown validation report. It does
not fetch market data, read secrets, call exchange APIs, place orders, use
leverage/futures, or manage live positions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import os
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import CostProfile, COST_PROFILES
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting import t281_high_activity_model as t281
from quant_bitcoin.backtesting import t283_principle_first_microstructure_strategy as t283
from quant_bitcoin.backtesting import t284_task283_multi_axis_robustness_revalidation as t284
from quant_bitcoin.backtesting import t285_regime_robust_multi_window_strategy_repair as t285
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.strategy_persistence_adapter import build_strategy_engine_persistence_payload
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.persistence.postgres import BacktestRunReadModel, PostgresBacktestResultRepository


TASK_ID = "TASK_287"
DATABASE_URL = t283.DATABASE_URL
REPORT_PATH = Path("reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md")
SOURCE = t283.SOURCE
SYMBOL = t283.SYMBOL
INTERVAL = t283.INTERVAL
STARTING_CASH = t283.STARTING_CASH
REQUESTED_START = t285._dt("2026-04-20T00:00:00Z")
OWNER_START_0520 = t285._dt("2026-05-20T00:00:00Z")
OWNER_START_0525 = t285._dt("2026-05-25T00:00:00Z")
PRE_OWNER_END = t285._dt("2026-05-19T23:59:00Z")
STRATEGY_KEY = "task287_repaired_0420_locked_oos_wfo_validation"
STRATEGY_NAME = "TASK287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION"
PRIMARY_CANDIDATE_ID = "T285_R3_CORE_SHORT_ONLY_B2"
TASK283_CANDIDATE_ID = "T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002"
TASK281_CANDIDATE_ID = "T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002"


@dataclass(frozen=True)
class CoverageGuard:
    ok: bool
    duplicate_open_time_count: int
    expected_candle_count: int | None
    failed_reasons: tuple[str, ...]


@dataclass(frozen=True)
class LockedCandidate:
    candidate_id: str
    source_task_id: str
    family: str
    thesis: str
    replay_kind: str
    task285_plan_id: str | None = None
    task281_variant_id: str | None = None
    role: str = "comparison"


@dataclass(frozen=True)
class RunSpec:
    candidate: LockedCandidate
    window: t285.WindowDefinition
    cost_profile_key: str
    run_group: str
    validation_axis: str
    diagnostic_only: bool = False


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
    generated_entries: int = 0
    removed_entries: int = 0
    generated_core_entries: int = 0
    generated_scout_entries: int = 0
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
class CandidateAggregate:
    candidate_id: str
    source_task_id: str
    family: str
    independent_windows: int
    positive_windows: int
    positive_window_fraction: float | None
    independent_return: float | None
    independent_net_pnl: float
    independent_gross_pnl: float
    independent_total_cost: float
    independent_cost_to_gross_pnl_ratio: float | None
    independent_round_trips: int
    full_return: float | None
    full_round_trips: int
    full_cost_to_gross_pnl_ratio: float | None
    pre_owner_return: float | None
    owner_0520_return: float | None
    owner_0525_return: float | None
    cost_2x_full_return: float | None
    cost_3x_full_return: float | None
    high_slippage_full_return: float | None
    max_single_window_net_contribution: float | None
    return_without_top_three_winners: float | None
    full_return_without_top_three_winners: float | None
    full_top_three_winner_contribution: float | None
    cost_mismatch_count: int
    readback_all_ok: bool
    candle_quality_all_ok: bool


@dataclass(frozen=True)
class CandidateDecision:
    candidate_id: str
    status: str
    classification: str
    rows: tuple[tuple[str, str, str, bool], ...]
    failed_gates: tuple[str, ...]
    aggregate: CandidateAggregate


@dataclass(frozen=True)
class GateReport:
    status: str
    primary_candidate_id: str
    decisions: tuple[CandidateDecision, ...]
    coverage_guard: CoverageGuard
    conclusion: str


def candidate_registry() -> tuple[LockedCandidate, ...]:
    primary_plan = _task285_plan(PRIMARY_CANDIDATE_ID)
    baseline_plan = _task285_plan("T285_BASE_LOCKED_B2")
    task281_candidate = _task281_candidate(TASK281_CANDIDATE_ID)
    return (
        LockedCandidate(
            candidate_id=PRIMARY_CANDIDATE_ID,
            source_task_id="TASK_285",
            family=primary_plan.family,
            thesis=primary_plan.thesis,
            replay_kind="task285_plan",
            task285_plan_id=PRIMARY_CANDIDATE_ID,
            role="primary_locked_candidate",
        ),
        LockedCandidate(
            candidate_id=TASK283_CANDIDATE_ID,
            source_task_id="TASK_283",
            family=baseline_plan.family,
            thesis="Task 283/284 locked B2 priority ensemble replayed unchanged as the rejected baseline comparator.",
            replay_kind="task285_plan",
            task285_plan_id="T285_BASE_LOCKED_B2",
            role="locked_baseline_comparator",
        ),
        LockedCandidate(
            candidate_id=TASK281_CANDIDATE_ID,
            source_task_id="TASK_281",
            family=task281_candidate.family,
            thesis=task281_candidate.description,
            replay_kind="task281_candidate",
            task281_variant_id=TASK281_CANDIDATE_ID,
            role="legacy_owner_window_comparator",
        ),
    )


def cost_profile_map() -> dict[str, CostProfile]:
    profiles = t285.cost_profile_map()
    profiles["high_slippage_stress"] = COST_PROFILES["high_slippage_stress"]
    return profiles


def build_validation_windows(latest: datetime) -> tuple[t285.WindowDefinition, ...]:
    latest = t285._as_utc(latest)
    windows: list[t285.WindowDefinition] = [
        t285.WindowDefinition("full_0420_latest", "full_repaired_0420", REQUESTED_START, latest, "full"),
        t285.WindowDefinition("pre_owner_0420_0519", "pre_owner_oos", REQUESTED_START, min(PRE_OWNER_END, latest), "pre_owner"),
        t285.WindowDefinition("owner_replay_0520_latest", "owner_replay", OWNER_START_0520, latest, "owner_replay", True),
        t285.WindowDefinition("owner_replay_0525_latest", "owner_replay", OWNER_START_0525, latest, "owner_replay", True),
    ]
    weekly_starts = [
        ("w1_0420_0426", t285._dt("2026-04-20T00:00:00Z"), t285._dt("2026-04-26T23:59:00Z")),
        ("w2_0427_0503", t285._dt("2026-04-27T00:00:00Z"), t285._dt("2026-05-03T23:59:00Z")),
        ("w3_0504_0510", t285._dt("2026-05-04T00:00:00Z"), t285._dt("2026-05-10T23:59:00Z")),
        ("w4_0511_0517", t285._dt("2026-05-11T00:00:00Z"), t285._dt("2026-05-17T23:59:00Z")),
        ("w5_0518_0524", t285._dt("2026-05-18T00:00:00Z"), t285._dt("2026-05-24T23:59:00Z")),
        ("w6_0525_latest", t285._dt("2026-05-25T00:00:00Z"), latest),
    ]
    for name, start, end in weekly_starts:
        windows.append(t285.WindowDefinition(name, "weekly_independent", start, min(end, latest), "independent"))

    windows.extend(
        [
            t285.WindowDefinition("wfo_0420_0503", "walk_forward_reporting", REQUESTED_START, min(t285._dt("2026-05-03T23:59:00Z"), latest), "wfo"),
            t285.WindowDefinition("wfo_0504_0517", "walk_forward_reporting", t285._dt("2026-05-04T00:00:00Z"), min(t285._dt("2026-05-17T23:59:00Z"), latest), "wfo"),
            t285.WindowDefinition("wfo_0518_latest", "walk_forward_reporting", t285._dt("2026-05-18T00:00:00Z"), latest, "wfo"),
            t285.WindowDefinition("full_0420_drop_first_6h", "endpoint_diagnostic", REQUESTED_START + timedelta(hours=6), latest, "endpoint", True),
            t285.WindowDefinition("full_0420_drop_first_24h", "endpoint_diagnostic", REQUESTED_START + timedelta(hours=24), latest, "endpoint", True),
            t285.WindowDefinition("full_0420_drop_last_6h", "endpoint_diagnostic", REQUESTED_START, latest - timedelta(hours=6), "endpoint", True),
            t285.WindowDefinition("full_0420_drop_last_24h", "endpoint_diagnostic", REQUESTED_START, latest - timedelta(hours=24), "endpoint", True),
            t285.WindowDefinition("owner_0520_drop_last_12h", "endpoint_diagnostic", OWNER_START_0520, latest - timedelta(hours=12), "endpoint", True),
            t285.WindowDefinition("owner_0520_drop_last_24h", "endpoint_diagnostic", OWNER_START_0520, latest - timedelta(hours=24), "endpoint", True),
        ]
    )
    return tuple(window for window in windows if window.end_time >= window.start_time)


def build_run_specs(
    *,
    candidates: Sequence[LockedCandidate] | None = None,
    windows: Sequence[t285.WindowDefinition] | None = None,
    latest: datetime | None = None,
) -> tuple[RunSpec, ...]:
    selected_candidates = tuple(candidates) if candidates is not None else candidate_registry()
    selected_windows = tuple(windows) if windows is not None else build_validation_windows(latest or datetime.now(timezone.utc))
    main_roles = {"full", "pre_owner", "owner_replay", "independent", "wfo"}
    endpoint_roles = {"endpoint"}
    specs: list[RunSpec] = []
    for candidate in selected_candidates:
        for window in selected_windows:
            if window.decision_role in main_roles:
                specs.append(
                    RunSpec(
                        candidate,
                        window,
                        "conservative_crypto_1m",
                        "locked_main_replay",
                        window.decision_role,
                        diagnostic_only=window.decision_role in {"owner_replay", "wfo"},
                    )
                )
            elif window.decision_role in endpoint_roles:
                specs.append(
                    RunSpec(
                        candidate,
                        window,
                        "conservative_crypto_1m",
                        "endpoint_diagnostic",
                        "endpoint_trim",
                        diagnostic_only=True,
                    )
                )
    stress_windows = [window for window in selected_windows if window.window_id in {"full_0420_latest", "pre_owner_0420_0519"}]
    for candidate in selected_candidates:
        for key in ("cost_2x", "cost_3x", "high_slippage_stress"):
            for window in stress_windows:
                specs.append(
                    RunSpec(
                        candidate,
                        window,
                        key,
                        "cost_stress",
                        "cost_sensitivity",
                        diagnostic_only=(window.decision_role != "full"),
                    )
                )
    return tuple(specs)


def run_matrix(*, database_url: str = DATABASE_URL, limit: int | None = None) -> list[RunRecord]:
    coverage = t285.data_coverage(database_url)
    guard = coverage_guard(database_url, coverage)
    if not guard.ok or coverage.available_end_time is None:
        gate = classify_records([], coverage, guard)
        write_report([], coverage=coverage, gate_report=gate, baselines=())
        return []

    windows = build_validation_windows(coverage.available_end_time)
    specs = build_run_specs(candidates=candidate_registry(), windows=windows)
    records: list[RunRecord] = []
    for sequence, spec in enumerate(specs, start=1):
        if limit is not None and sequence > limit:
            break
        records.append(run_one(database_url=database_url, spec=spec))

    gate = classify_records(records, coverage, guard)
    baselines = build_baselines(database_url, windows, records)
    write_report(records, coverage=coverage, gate_report=gate, baselines=baselines)
    return records


def run_one(*, database_url: str, spec: RunSpec) -> RunRecord:
    candles = t283.load_candles(database_url, spec.window.to_t283())
    if candles.empty:
        return _skipped_record(spec, "no_local_candles_for_window")
    quality = t283.candle_quality(candles)
    if not bool(quality["candle_continuity_ok"]):
        return _skipped_record(spec, "local_candle_continuity_gap", quality=quality, candle_count=len(candles))
    endpoint_status = _window_endpoint_status(candles, spec.window)
    if endpoint_status is not None and not spec.window.allow_incomplete:
        return _skipped_record(spec, endpoint_status, quality=quality, candle_count=len(candles))

    profiles = cost_profile_map()
    cost_profile = profiles[spec.cost_profile_key]
    actions, action_meta = generate_locked_actions(candles, spec.candidate, cost_profile)
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
    research = _research_metadata(spec, cost_profile, coverage_window_complete=(endpoint_status is None))
    validation_metadata = {
        "schema_version": "task287_validation_metadata_v1",
        "locked_no_retune": True,
        "replay_kind": spec.candidate.replay_kind,
        "candidate_id": spec.candidate.candidate_id,
        "source_task_id": spec.candidate.source_task_id,
        "source_candidate_pointer": spec.candidate.task285_plan_id or spec.candidate.task281_variant_id,
        "window_complete_required": not spec.window.allow_incomplete,
        "window_endpoint_status": endpoint_status or "exact_window_coverage",
        "signal_execution_separated": True,
        "completed_candle_only": True,
        "intrabar_ambiguity_policy": "stop_first_when_stop_and_target_hit_same_candle",
        "no_strategy_retune": True,
        "generated_entries": int(action_meta.get("generated_entries", 0)),
        "generated_core_entries": int(action_meta.get("generated_core_entries", 0)),
        "generated_scout_entries": int(action_meta.get("generated_scout_entries", 0)),
        "removed_entries": int(action_meta.get("removed_entries", 0)),
        "source_action_generation": action_meta.get("source_action_generation", {}),
    }
    metadata["research"] = research
    metadata["task287_validation"] = validation_metadata
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
        strategy_version=f"task287_{spec.candidate.candidate_id}_{spec.window.window_id}_{spec.cost_profile_key}_v1",
        strategy_parameters={
            "task_id": TASK_ID,
            "candidate_id": spec.candidate.candidate_id,
            "source_task_id": spec.candidate.source_task_id,
            "family": spec.candidate.family,
            "thesis": spec.candidate.thesis,
            "role": spec.candidate.role,
            "replay_kind": spec.candidate.replay_kind,
            "no_retune": True,
            "window": _window_metadata(spec.window),
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
            "task287_validation": validation_metadata,
        },
    )
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    if persisted is None:
        raise RuntimeError(f"Task 287 persisted run could not be read back: {run_id}")
    return analyze_persisted_run(
        persisted,
        spec=spec,
        quality=quality,
        action_meta=action_meta,
    )


def generate_locked_actions(
    candles: pd.DataFrame,
    candidate: LockedCandidate,
    cost_profile: CostProfile,
) -> tuple[list[Any], dict[str, Any]]:
    if candidate.replay_kind == "task285_plan":
        plan = _task285_plan(str(candidate.task285_plan_id))
        source_candidate = t285.candidate_by_id(plan.source_candidate_id)
        actions, source_meta = t285.generate_task285_actions(candles, plan, source_candidate, cost_profile)
        return actions, {
            "schema_version": "task287_action_replay_metadata_v1",
            "generated_entries": source_meta.generated_entries,
            "removed_entries": source_meta.cost_rejections,
            "generated_core_entries": int(source_meta.signal_counts.get("side_SHORT", 0)) if plan.repair_mode == "core_short_only" else 0,
            "generated_scout_entries": 0,
            "source_action_generation": {
                "source_task_id": "TASK_285",
                "task285_plan_id": plan.candidate_id,
                "source_candidate_id": plan.source_candidate_id,
                "signal_counts": source_meta.signal_counts,
                "exit_reasons": source_meta.exit_reasons,
                "factor_schema_version": source_meta.factor_schema_version,
            },
        }
    if candidate.replay_kind == "task281_candidate":
        source_candidate = _task281_candidate(str(candidate.task281_variant_id))
        actions, source_meta = t281.generate_actions(candles, source_candidate)
        return actions, {
            "schema_version": "task287_action_replay_metadata_v1",
            "generated_entries": int(source_meta.get("generated_entries", 0)),
            "removed_entries": 0,
            "generated_core_entries": int(source_meta.get("generated_core_entries", 0)),
            "generated_scout_entries": int(source_meta.get("generated_scout_entries", 0)),
            "source_action_generation": {
                "source_task_id": "TASK_281",
                "variant_id": source_candidate.variant_id,
                "family": source_candidate.family,
                **source_meta,
            },
        }
    raise ValueError(f"unsupported locked replay kind: {candidate.replay_kind}")


def analyze_persisted_run(
    persisted: BacktestRunReadModel,
    *,
    spec: RunSpec,
    quality: dict[str, Any],
    action_meta: dict[str, Any],
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
    validation_meta = (persisted.run.metadata or {}).get("task287_validation") or {}
    readback_ok = bool(
        research.get("task_id") == TASK_ID
        and summary_research.get("task_id") == TASK_ID
        and research.get("candidate_id") == spec.candidate.candidate_id
        and summary_research.get("candidate_id") == spec.candidate.candidate_id
        and validation_meta.get("locked_no_retune") is True
    )
    net_pnl = _float(cost_summary.get("net_pnl"))
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
        net_pnl=net_pnl,
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
        generated_entries=int(action_meta.get("generated_entries", 0)),
        removed_entries=int(action_meta.get("removed_entries", 0)),
        generated_core_entries=int(action_meta.get("generated_core_entries", 0)),
        generated_scout_entries=int(action_meta.get("generated_scout_entries", 0)),
        cost_formula_mismatch_count=cost_audit.mismatch_count,
        summary_cost_mismatch_count=summary_audit.mismatch_count,
        max_cost_mismatch=max(cost_audit.max_abs_mismatch, summary_audit.max_abs_mismatch),
        readback_ok=readback_ok,
        candle_continuity_ok=bool(quality.get("candle_continuity_ok")),
        candle_gap_count=int(quality.get("candle_gap_count") or 0),
        side_attribution=side_attr,
        session_attribution=session_attr,
        regime_attribution=regime_attr,
        outlier_audit=t284.outlier_audit(event_net_pnls, net_pnl or 0.0),
        event_net_pnls=tuple(event_net_pnls),
    )


def coverage_guard(database_url: str, coverage: t285.DataCoverage) -> CoverageGuard:
    duplicate_count = duplicate_open_time_count(database_url)
    expected_count = None
    reasons: list[str] = []
    if coverage.available_start_time is None or coverage.available_end_time is None:
        reasons.append("no_repaired_0420_forward_candles")
    else:
        expected_count = int((coverage.available_end_time - REQUESTED_START).total_seconds() // 60) + 1
        if coverage.available_start_time > REQUESTED_START:
            reasons.append("available_start_after_2026_04_20")
        if coverage.candle_count != expected_count:
            reasons.append("candle_count_does_not_match_continuous_minute_range")
    if coverage.gaps:
        reasons.append("continuity_gaps_detected")
    if duplicate_count != 0:
        reasons.append("duplicate_open_times_detected")
    if not coverage.april20_forward_complete:
        reasons.append("april20_forward_complete_false")
    return CoverageGuard(
        ok=not reasons,
        duplicate_open_time_count=duplicate_count,
        expected_candle_count=expected_count,
        failed_reasons=tuple(reasons),
    )


def duplicate_open_time_count(database_url: str) -> int:
    import psycopg

    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS duplicate_groups
            FROM (
                SELECT open_time
                FROM candles
                WHERE source = %s AND symbol = %s AND interval = %s AND is_closed IS TRUE
                  AND open_time >= %s
                GROUP BY open_time
                HAVING COUNT(*) > 1
            ) duplicates
            """,
            (SOURCE, SYMBOL, INTERVAL, REQUESTED_START),
        ).fetchone()
    return int(row[0] if row else 0)


def classify_records(records: Sequence[RunRecord], coverage: t285.DataCoverage, guard: CoverageGuard) -> GateReport:
    decisions = tuple(_candidate_decision(candidate, records) for candidate in candidate_registry())
    primary = next((decision for decision in decisions if decision.candidate_id == PRIMARY_CANDIDATE_ID), None)
    if not guard.ok:
        status = "BLOCKED_REPAIRED_DATA_GUARD"
        conclusion = f"Coverage guard failed before promotion decision: {', '.join(guard.failed_reasons)}."
    elif primary and primary.status == "OOS_SUPPORTED_RESEARCH_ONLY":
        status = "LOCKED_PRIMARY_SUPPORTED_RESEARCH_ONLY"
        conclusion = "Primary Task 285 candidate passed the Task 287 locked repaired-data gates; still research-only."
    else:
        status = "LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY"
        failed = ", ".join(primary.failed_gates) if primary else "primary candidate missing"
        conclusion = f"Primary Task 285 candidate did not pass locked repaired-data validation: {failed}."
    if not coverage.april20_forward_complete and "Coverage" not in conclusion:
        conclusion += " April-20-forward data was not complete."
    return GateReport(
        status=status,
        primary_candidate_id=PRIMARY_CANDIDATE_ID,
        decisions=decisions,
        coverage_guard=guard,
        conclusion=conclusion,
    )


def _candidate_decision(candidate: LockedCandidate, records: Sequence[RunRecord]) -> CandidateDecision:
    aggregate = _aggregate_candidate(candidate, records)
    rows = (
        ("Full 0420 latest return", ">= +3pct", _pct(aggregate.full_return), bool(aggregate.full_return is not None and aggregate.full_return >= 0.03)),
        ("Full 0420 latest round trips", ">= 50", str(aggregate.full_round_trips), aggregate.full_round_trips >= 50),
        ("Pre-owner 0420-0519 return", "> 0pct", _pct(aggregate.pre_owner_return), bool(aggregate.pre_owner_return is not None and aggregate.pre_owner_return > 0.0)),
        ("Independent weekly windows", ">= 4", str(aggregate.independent_windows), aggregate.independent_windows >= 4),
        ("Independent positive fraction", ">= 75pct", _ratio(aggregate.positive_window_fraction), bool(aggregate.positive_window_fraction is not None and aggregate.positive_window_fraction >= 0.75)),
        ("Independent aggregate return", ">= +3pct", _pct(aggregate.independent_return), bool(aggregate.independent_return is not None and aggregate.independent_return >= 0.03)),
        ("Single-window winner concentration", "<= 60pct", _ratio(aggregate.max_single_window_net_contribution), bool(aggregate.max_single_window_net_contribution is not None and aggregate.max_single_window_net_contribution <= 0.60)),
        ("Independent return without top-three winners", "> 0pct", _pct(aggregate.return_without_top_three_winners), bool(aggregate.return_without_top_three_winners is not None and aggregate.return_without_top_three_winners > 0.0)),
        ("Full return without top-three winners", "> 0pct", _pct(aggregate.full_return_without_top_three_winners), bool(aggregate.full_return_without_top_three_winners is not None and aggregate.full_return_without_top_three_winners > 0.0)),
        ("Full top-three winner contribution", "<= 70pct", _ratio(aggregate.full_top_three_winner_contribution), bool(aggregate.full_top_three_winner_contribution is not None and aggregate.full_top_three_winner_contribution <= 0.70)),
        ("Full cost/gross PnL", "<= 0.60", _ratio(aggregate.full_cost_to_gross_pnl_ratio), bool(aggregate.full_cost_to_gross_pnl_ratio is not None and aggregate.full_cost_to_gross_pnl_ratio <= 0.60)),
        ("Independent cost/gross PnL", "<= 0.60", _ratio(aggregate.independent_cost_to_gross_pnl_ratio), bool(aggregate.independent_cost_to_gross_pnl_ratio is not None and aggregate.independent_cost_to_gross_pnl_ratio <= 0.60)),
        ("2x cost full return", "> -1pct", _pct(aggregate.cost_2x_full_return), bool(aggregate.cost_2x_full_return is not None and aggregate.cost_2x_full_return > -0.01)),
        ("3x cost full return", "reported and > -3pct", _pct(aggregate.cost_3x_full_return), bool(aggregate.cost_3x_full_return is not None and aggregate.cost_3x_full_return > -0.03)),
        ("High slippage full return", "reported", _pct(aggregate.high_slippage_full_return), aggregate.high_slippage_full_return is not None),
        ("Cost audit mismatches", "0", str(aggregate.cost_mismatch_count), aggregate.cost_mismatch_count == 0),
        ("DB readback", "all task287 metadata read back", str(aggregate.readback_all_ok), aggregate.readback_all_ok),
        ("Candle quality", "all runs continuous", str(aggregate.candle_quality_all_ok), aggregate.candle_quality_all_ok),
    )
    failed = tuple(name for name, _, _, ok in rows if not ok)
    classification = _failure_classification(aggregate, failed)
    status = "OOS_SUPPORTED_RESEARCH_ONLY" if not failed else "OOS_REJECTED_RESEARCH_ONLY"
    return CandidateDecision(
        candidate_id=candidate.candidate_id,
        status=status,
        classification=classification,
        rows=rows,
        failed_gates=failed,
        aggregate=aggregate,
    )


def _aggregate_candidate(candidate: LockedCandidate, records: Sequence[RunRecord]) -> CandidateAggregate:
    completed = [record for record in records if record.run_id is not None and record.spec.candidate.candidate_id == candidate.candidate_id]
    independent = [
        record
        for record in completed
        if record.spec.window.decision_role == "independent" and record.spec.cost_profile_key == "conservative_crypto_1m"
    ]
    full = _record(completed, "full_0420_latest", "conservative_crypto_1m")
    pre_owner = _record(completed, "pre_owner_0420_0519", "conservative_crypto_1m")
    owner_0520 = _record(completed, "owner_replay_0520_latest", "conservative_crypto_1m")
    owner_0525 = _record(completed, "owner_replay_0525_latest", "conservative_crypto_1m")
    cost_2x = _record(completed, "full_0420_latest", "cost_2x")
    cost_3x = _record(completed, "full_0420_latest", "cost_3x")
    high_slippage = _record(completed, "full_0420_latest", "high_slippage_stress")
    net_values = [float(record.net_pnl or 0.0) for record in independent]
    gross = sum(float(record.gross_pnl or 0.0) for record in independent)
    net = sum(net_values)
    total_cost = sum(float(record.total_cost or 0.0) for record in independent)
    positive_net = sum(value for value in net_values if value > 0.0)
    positive_windows = len([value for value in net_values if value > 0.0])
    max_single = None if positive_net <= 0.0 else max((value for value in net_values if value > 0.0), default=0.0) / positive_net
    event_pnls = [pnl for record in independent for pnl in record.event_net_pnls]
    winners = sorted((pnl for pnl in event_pnls if pnl > 0.0), reverse=True)
    without_top_three = None if not independent else (net - sum(winners[:3])) / STARTING_CASH
    readback_all_ok = bool(completed) and all(record.readback_ok for record in completed)
    candle_quality_all_ok = bool(completed) and all(record.candle_continuity_ok and record.candle_gap_count == 0 for record in completed)
    cost_mismatch = sum(record.cost_formula_mismatch_count + record.summary_cost_mismatch_count for record in completed)
    return CandidateAggregate(
        candidate_id=candidate.candidate_id,
        source_task_id=candidate.source_task_id,
        family=candidate.family,
        independent_windows=len(independent),
        positive_windows=positive_windows,
        positive_window_fraction=None if not independent else positive_windows / len(independent),
        independent_return=None if not independent else net / STARTING_CASH,
        independent_net_pnl=net,
        independent_gross_pnl=gross,
        independent_total_cost=total_cost,
        independent_cost_to_gross_pnl_ratio=None if gross <= 0.0 else total_cost / gross,
        independent_round_trips=sum(record.completed_round_trips for record in independent),
        full_return=full.total_return if full else None,
        full_round_trips=full.completed_round_trips if full else 0,
        full_cost_to_gross_pnl_ratio=full.cost_to_gross_pnl_ratio if full else None,
        pre_owner_return=pre_owner.total_return if pre_owner else None,
        owner_0520_return=owner_0520.total_return if owner_0520 else None,
        owner_0525_return=owner_0525.total_return if owner_0525 else None,
        cost_2x_full_return=cost_2x.total_return if cost_2x else None,
        cost_3x_full_return=cost_3x.total_return if cost_3x else None,
        high_slippage_full_return=high_slippage.total_return if high_slippage else None,
        max_single_window_net_contribution=max_single,
        return_without_top_three_winners=without_top_three,
        full_return_without_top_three_winners=full.outlier_audit.return_without_top_three_winners if full else None,
        full_top_three_winner_contribution=full.outlier_audit.top_three_winner_contribution if full else None,
        cost_mismatch_count=cost_mismatch,
        readback_all_ok=readback_all_ok,
        candle_quality_all_ok=candle_quality_all_ok,
    )


def build_baselines(
    database_url: str,
    windows: Sequence[t285.WindowDefinition],
    records: Sequence[RunRecord],
) -> tuple[t284.BaselineResult, ...]:
    baseline_windows = [
        window
        for window in windows
        if window.window_id in {"full_0420_latest", "pre_owner_0420_0519", "owner_replay_0520_latest", "owner_replay_0525_latest"}
    ]
    baselines: list[t284.BaselineResult] = []
    for window in baseline_windows:
        candles = t283.load_candles(database_url, window.to_t283())
        if candles.empty:
            continue
        target_trades = next(
            (
                record.completed_round_trips
                for record in records
                if record.run_id is not None
                and record.spec.candidate.candidate_id == PRIMARY_CANDIDATE_ID
                and record.spec.window.window_id == window.window_id
                and record.spec.cost_profile_key == "conservative_crypto_1m"
            ),
            0,
        )
        baselines.append(t284.buy_and_hold_baseline(candles, window.window_id))
        baselines.append(t284.ma_trend_baseline(candles, window.window_id))
        baselines.append(t284.random_entry_baseline(candles, window.window_id, target_trades=target_trades, seed=287))
    return tuple(baselines)


def write_report(
    records: Sequence[RunRecord],
    *,
    coverage: t285.DataCoverage,
    gate_report: GateReport,
    baselines: Sequence[t284.BaselineResult],
) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_ids = ", ".join(str(record.run_id) for record in records if record.run_id is not None) or "-"
    lines = [
        "# Task 287 Repaired 0420 Locked OOS/WFO Validation",
        "",
        f"Status: `{gate_report.status}`",
        "",
        "## Scope",
        "",
        "- Purpose: replay locked research candidates unchanged on the repaired BTCUSDT 1m April-20-forward dataset.",
        "- Retune policy: `no_retune`; no entry, exit, sizing, filter, or parameter search is allowed in this task.",
        "- Result scope: `RESEARCH_ONLY`; no live trading, no private exchange endpoints, no futures, no leverage.",
        "- Primary candidate: `T285_R3_CORE_SHORT_ONLY_B2`.",
        "- Comparators: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`, `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.",
        "",
        "## Repaired Data Coverage",
        "",
        f"- Requested start: `{t285._iso(coverage.requested_start_time)}`.",
        f"- Available start: `{t285._iso(coverage.available_start_time)}`.",
        f"- Available end: `{t285._iso(coverage.available_end_time)}`.",
        f"- Closed candle count: `{coverage.candle_count}`.",
        f"- Expected continuous count: `{gate_report.coverage_guard.expected_candle_count}`.",
        f"- Continuity gaps: `{len(coverage.gaps)}`.",
        f"- Duplicate open-time groups: `{gate_report.coverage_guard.duplicate_open_time_count}`.",
        f"- April-20-forward complete: `{coverage.april20_forward_complete}`.",
        f"- Coverage guard: `{'PASS' if gate_report.coverage_guard.ok else 'FAIL'}` `{', '.join(gate_report.coverage_guard.failed_reasons) or '-'}`.",
        "",
        "## Locked Strategy Rationale",
        "",
        "- `T285_R3_CORE_SHORT_ONLY_B2`: failed-rally/liquidity-sweep short core. The market thesis is that recent highs concentrate stop and breakout liquidity; when BTC sweeps that area, closes back inside, and broader short-term pressure is bearish, forced buying may exhaust and price can revert downward. Task 285 locked this as a core-only short repair because prior validation showed profits were concentrated in the short core while long/scout sleeves diluted results.",
        "- `T283_B2...`: same principle-first LSR/MTF ensemble before Task 285 side/layer repair, kept as a baseline comparator.",
        "- `T281_B1...`: earlier owner-window high-activity core/scout model, kept as a legacy comparator to detect whether the repaired data changes the prior overfit diagnosis.",
        "",
        "## Validation Design",
        "",
        "- Base cost: `conservative_crypto_1m` with taker fee, spread, base/minimum slippage, and volatility slippage.",
        "- Stress costs: `cost_2x`, `cost_3x`, and `high_slippage_stress` on full/pre-owner windows.",
        "- Signal/execution: completed signal candle, next-candle execution where inherited from Task 283 B2; conservative stop-first if stop and target hit the same candle.",
        "- Windows: full 0420-latest, pre-owner 0420-0519, owner replays 0520/0525, six non-overlapping weekly independent windows, WFO reporting partitions, and endpoint trims.",
        "- Persistence: every completed run is saved with `research.task_id = TASK_287`, `research.validation_mode = repaired_0420_locked_oos_wfo`, `no_retune = true`, repaired-data metadata, candidate/window/cost metadata, and source-reference run IDs.",
        "",
        "## Persisted Runs",
        "",
        f"- Task 287 run IDs: `{run_ids}`.",
        "",
        "| Candidate | Source | Window | Role | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Fee | Spread | Slippage | Cost MM | Readback | Status |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record.spec.candidate.candidate_id}`",
                    f"`{record.spec.candidate.source_task_id}`",
                    f"`{record.spec.window.window_id}`",
                    record.spec.window.decision_role,
                    f"`{record.spec.cost_profile_key}`",
                    str(record.run_id) if record.run_id is not None else "-",
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    _ratio(record.win_rate),
                    _ratio(record.profit_factor),
                    _money(record.gross_pnl),
                    _money(record.net_pnl),
                    _money(record.total_cost),
                    _ratio(record.cost_to_gross_pnl_ratio),
                    _money(record.total_fee_cost),
                    _money(record.total_spread_cost),
                    _money(record.total_slippage_cost),
                    str(record.cost_formula_mismatch_count + record.summary_cost_mismatch_count),
                    str(record.readback_ok),
                    record.status if record.run_id is not None else str(record.skip_reason),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Candidate Aggregates",
            "",
            "| Candidate | Source | Independent Windows | Positive | Indep Return | Full Return | Full Trips | Pre-owner | 0520 | 0525 | 2x Full | 3x Full | High Slip Full | Cost/Gross Full | Cost/Gross Indep | No Top3 Indep | No Top3 Full | Cost MM | Classification |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for decision in gate_report.decisions:
        aggregate = decision.aggregate
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{aggregate.candidate_id}`",
                    f"`{aggregate.source_task_id}`",
                    str(aggregate.independent_windows),
                    _ratio(aggregate.positive_window_fraction),
                    _pct(aggregate.independent_return),
                    _pct(aggregate.full_return),
                    str(aggregate.full_round_trips),
                    _pct(aggregate.pre_owner_return),
                    _pct(aggregate.owner_0520_return),
                    _pct(aggregate.owner_0525_return),
                    _pct(aggregate.cost_2x_full_return),
                    _pct(aggregate.cost_3x_full_return),
                    _pct(aggregate.high_slippage_full_return),
                    _ratio(aggregate.full_cost_to_gross_pnl_ratio),
                    _ratio(aggregate.independent_cost_to_gross_pnl_ratio),
                    _pct(aggregate.return_without_top_three_winners),
                    _pct(aggregate.full_return_without_top_three_winners),
                    str(aggregate.cost_mismatch_count),
                    decision.classification,
                ]
            )
            + " |"
        )

    lines.extend(["", "## Gate Check", ""])
    for decision in gate_report.decisions:
        lines.extend(
            [
                f"### `{decision.candidate_id}`",
                "",
                f"- Status: `{decision.status}`.",
                f"- Classification: `{decision.classification}`.",
                f"- Failed gates: `{', '.join(decision.failed_gates) if decision.failed_gates else '-'}`.",
                "",
                "| Gate | Required | Observed | Status |",
                "| --- | --- | --- | --- |",
            ]
        )
        for name, required, observed, ok in decision.rows:
            lines.append(f"| {name} | {required} | {observed} | `{'PASS' if ok else 'FAIL'}` |")
        lines.append("")

    lines.extend(
        [
            "## Baselines",
            "",
            "| Window | Baseline | Return | Trades | Note |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for baseline in baselines:
        lines.append(
            f"| `{baseline.window_id}` | `{baseline.baseline_id}` | {_pct(baseline.total_return)} | {baseline.completed_round_trips} | {baseline.note} |"
        )

    lines.extend(
        [
            "",
            "## Cost Verification",
            "",
            "- Every persisted run is audited from trade metadata against the summary cost fields.",
            "- A valid run must have zero formula mismatches and zero summary mismatches.",
            "- Base and stress costs are decision-driving; zero-cost diagnostics are intentionally not used in Task 287.",
        ]
    )
    for record in records:
        if record.run_id is None:
            continue
        lines.append(
            f"- Run `{record.run_id}` `{record.spec.candidate.candidate_id}` `{record.spec.window.window_id}` `{record.spec.cost_profile_key}`: notional `{_money(record.total_notional)}`, fee `{_money(record.total_fee_cost)}`, spread `{_money(record.total_spread_cost)}`, slippage `{_money(record.total_slippage_cost)}`, total `{_money(record.total_cost)}`, effective one-way cost `{_ratio(record.effective_total_cost_bps)}` bps, formula mismatch `{record.cost_formula_mismatch_count}`, summary mismatch `{record.summary_cost_mismatch_count}`, max mismatch `{record.max_cost_mismatch:.8f}`."
        )

    lines.extend(
        [
            "",
            "## Overfit And Failure Diagnostics",
            "",
            "- Owner windows are reported but do not promote a model by themselves.",
            "- The independent promotion evidence is the six weekly windows from 2026-04-20 forward plus the separate pre-owner gate.",
            "- Return concentration is checked by removing the top three event winners from full and weekly aggregates.",
            "- Cost fragility is checked by 2x/3x/high-slippage stress on the full repaired window.",
            "- A candidate with fewer than 50 completed round trips on the full window is rejected as insufficient sample even if return is high.",
            "",
            "## Implementation Checklist",
            "",
            "- Look-ahead bias: inherited completed-candle factor construction; no future candle fields are used for entry signals.",
            "- Candle close signal: yes for inherited signal candidates.",
            "- Next candle execution: inherited Task 283 B2 shifted execution for Task 283/285 candidates.",
            "- Stop/take intrabar ambiguity: conservative stop-first inherited from source runners.",
            "- Long/short separation: side attribution recorded for every persisted run.",
            "- Fee both ways: engine cost summary and trade-level audit recorded.",
            "- Slippage/spread: base, 2x, 3x, and high-slippage stress profiles recorded.",
            "- Position overlap: inherited deterministic action generation and engine open-position guard.",
            "- Data gaps and duplicates: checked before simulation and per-window during each run.",
            "- Trade log, entry/exit reason, factor snapshot: persisted through strategy-engine trade metadata.",
            "- Paper/live trading: not performed.",
            "",
            "## Conclusion",
            "",
            f"- Final status: `{gate_report.status}`.",
            f"- Interpretation: {gate_report.conclusion}",
            "- No strategy is promoted to live or paper trading by this task; this is a locked offline validation record.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def _research_metadata(spec: RunSpec, cost_profile: CostProfile, *, coverage_window_complete: bool) -> dict[str, Any]:
    return {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "scope": "offline_backtest_research_only",
        "task_id": TASK_ID,
        "parent_task_ids": ["TASK_281", "TASK_283", "TASK_284", "TASK_285", "TASK_286"],
        "source_task_id": spec.candidate.source_task_id,
        "validation_mode": "repaired_0420_locked_oos_wfo",
        "candidate_id": spec.candidate.candidate_id,
        "candidate_family": spec.candidate.family,
        "candidate_role": spec.candidate.role,
        "replay_kind": spec.candidate.replay_kind,
        "window_id": spec.window.window_id,
        "validation_group": spec.window.validation_group,
        "decision_role": spec.window.decision_role,
        "run_group": spec.run_group,
        "validation_axis": spec.validation_axis,
        "diagnostic_only": spec.diagnostic_only,
        "cost_profile": spec.cost_profile_key,
        "cost_profile_metadata": cost_profile.to_metadata(),
        "source_reference_run_ids": list(_source_reference_run_ids(spec.candidate.candidate_id)),
        "repaired_data_declaration": {
            "task_id": "TASK_286",
            "source": SOURCE,
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "required_start_time": t285._iso(REQUESTED_START),
            "coverage_window_complete": coverage_window_complete,
            "strict_coverage_required": True,
        },
        "no_retune": True,
        "no_live_trading": True,
        "research_only": True,
    }


def _window_metadata(window: t285.WindowDefinition) -> dict[str, Any]:
    return {
        "window_id": window.window_id,
        "validation_group": window.validation_group,
        "decision_role": window.decision_role,
        "start_time": t285._iso(window.start_time),
        "end_time": t285._iso(window.end_time),
        "allow_incomplete": window.allow_incomplete,
    }


def _window_endpoint_status(candles: pd.DataFrame, window: t285.WindowDefinition) -> str | None:
    timestamps = pd.to_datetime(candles["timestamp"], utc=True)
    first = t285._as_utc(timestamps.iloc[0])
    last = t285._as_utc(timestamps.iloc[-1])
    if first != window.start_time:
        return "window_start_endpoint_mismatch"
    if last != window.end_time:
        return "window_end_endpoint_mismatch"
    return None


def _record(records: Sequence[RunRecord], window_id: str, cost_profile_key: str) -> RunRecord | None:
    return next(
        (
            record
            for record in records
            if record.spec.window.window_id == window_id and record.spec.cost_profile_key == cost_profile_key
        ),
        None,
    )


def _failure_classification(aggregate: CandidateAggregate, failed: Sequence[str]) -> str:
    failed_set = set(failed)
    if "Cost audit mismatches" in failed_set or "DB readback" in failed_set or "Candle quality" in failed_set:
        return "INVALID_ACCOUNTING_OR_DATA"
    if "Full 0420 latest round trips" in failed_set or "Independent weekly windows" in failed_set:
        return "SAMPLE_SIZE_INSUFFICIENT"
    if "2x cost full return" in failed_set or "3x cost full return" in failed_set or "Full cost/gross PnL" in failed_set:
        return "COST_FRAGILE"
    if (
        "Independent return without top-three winners" in failed_set
        or "Full return without top-three winners" in failed_set
        or "Full top-three winner contribution" in failed_set
        or "Single-window winner concentration" in failed_set
    ):
        return "OUTLIER_DEPENDENT"
    if "Pre-owner 0420-0519 return" in failed_set or "Independent positive fraction" in failed_set:
        return "REGIME_UNSTABLE_OR_OVERFIT"
    if aggregate.full_return is not None and aggregate.full_return < 0.03:
        return "RETURN_TARGET_NOT_MET"
    return "ROBUSTNESS_GATE_FAILED"


def _task285_plan(candidate_id: str) -> t285.CandidatePlan:
    for plan in t285.build_candidate_plans():
        if plan.candidate_id == candidate_id:
            return plan
    raise ValueError(f"unknown Task 285 plan: {candidate_id}")


def _task281_candidate(candidate_id: str) -> t281.CandidateSpec:
    for candidate in t281.build_candidates():
        if candidate.variant_id == candidate_id:
            return candidate
    raise ValueError(f"unknown Task 281 candidate: {candidate_id}")


def _source_reference_run_ids(candidate_id: str) -> tuple[int, ...]:
    if candidate_id == PRIMARY_CANDIDATE_ID:
        return (1016, 1017, 1018, 1019, 1020, 1041, 1042)
    if candidate_id == TASK283_CANDIDATE_ID:
        return (950, 951, 959, 960, 961, 962)
    if candidate_id == TASK281_CANDIDATE_ID:
        return (892, 900, 901, 902, 908)
    return ()


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


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


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
    parser = argparse.ArgumentParser(description="Run Task 287 repaired 0420 locked OOS/WFO validation.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    records = run_matrix(database_url=args.database_url, limit=args.limit)
    persisted = len([record for record in records if record.run_id is not None])
    print(f"wrote {REPORT_PATH} with {persisted} persisted Task 287 runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
