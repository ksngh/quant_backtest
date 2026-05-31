"""Task 284 locked multi-axis revalidation for the Task 283 BTC strategy.

This module is offline-only research validation code. It reuses the Task 283
locked candidate without retuning, persists validation runs with Task 284
metadata, recomputes transaction costs from trade logs, and writes a markdown
report. It does not fetch market data, read secrets, call exchange APIs, place
orders, or manage live positions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import os
from pathlib import Path
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
from quant_bitcoin.backtesting.strategy_validation_metrics import (
    trade_contribution_metrics,
)
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.backtesting import t283_principle_first_microstructure_strategy as t283
from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    PostgresBacktestResultRepository,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


TASK_ID = "TASK_284"
PARENT_TASK_ID = "TASK_283"
LOCKED_CANDIDATE_ID = "T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002"
DATABASE_URL = t283.DATABASE_URL
SOURCE = t283.SOURCE
SYMBOL = t283.SYMBOL
INTERVAL = t283.INTERVAL
STARTING_CASH = t283.STARTING_CASH
STRATEGY_KEY = "task284_task283_locked_robustness_revalidation"
STRATEGY_NAME = "TASK284_TASK283_LOCKED_ROBUSTNESS_REVALIDATION"
REPORT_PATH = Path("reports/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md")


@dataclass(frozen=True)
class ValidationSpec:
    window: t283.WindowSpec
    cost_profile_key: str
    run_group: str
    validation_axis: str
    action_mode: str = "locked_b2"
    diagnostic_only: bool = False
    candidate_id: str = LOCKED_CANDIDATE_ID


@dataclass(frozen=True)
class DataCoverageReport:
    requested_start_time: datetime
    available_start_time: datetime | None
    available_end_time: datetime | None
    candle_count: int
    gap_count: int
    gaps: tuple[tuple[datetime, datetime, int], ...]
    april20_forward_complete: bool


@dataclass(frozen=True)
class BucketAttribution:
    bucket: str
    completed_round_trips: int = 0
    gross_pnl: float = 0.0
    total_cost: float = 0.0
    net_pnl: float = 0.0
    win_rate: float | None = None
    average_net_pnl: float | None = None


@dataclass(frozen=True)
class SummaryCostAudit:
    mismatch_count: int = 0
    max_abs_mismatch: float = 0.0


@dataclass(frozen=True)
class OutlierAudit:
    event_count: int = 0
    net_pnl: float = 0.0
    largest_winner_contribution: float | None = None
    top_three_winner_contribution: float | None = None
    net_without_largest_winner: float = 0.0
    net_without_top_three_winners: float = 0.0
    return_without_largest_winner: float = 0.0
    return_without_top_three_winners: float = 0.0


@dataclass(frozen=True)
class BaselineResult:
    window_id: str
    baseline_id: str
    total_return: float | None
    completed_round_trips: int
    note: str


@dataclass(frozen=True)
class ValidationRecord:
    spec: ValidationSpec
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
    total_fee_cost: float | None = None
    total_spread_cost: float | None = None
    total_slippage_cost: float | None = None
    total_cost: float | None = None
    total_notional: float | None = None
    effective_total_cost_bps: float | None = None
    cost_to_gross_pnl_ratio: float | None = None
    action_entries: int = 0
    cost_formula_mismatch_count: int = 0
    summary_cost_mismatch_count: int = 0
    max_cost_mismatch: float = 0.0
    readback_ok: bool = False
    candle_continuity_ok: bool = False
    candle_gap_count: int = 0
    side_attribution: tuple[BucketAttribution, ...] = ()
    session_attribution: tuple[BucketAttribution, ...] = ()
    regime_attribution: tuple[BucketAttribution, ...] = ()
    outlier_audit: OutlierAudit = OutlierAudit()


@dataclass(frozen=True)
class GateReport:
    status: str
    rows: tuple[tuple[str, str, str, bool], ...]
    failed_gates: tuple[str, ...]
    conclusion: str


def build_validation_specs(latest: datetime) -> tuple[ValidationSpec, ...]:
    latest = _as_utc(latest)
    owner_0520 = t283.WindowSpec("owner_0520_latest", "owner_replay", _dt("2026-05-20T00:00:00Z"), latest)
    owner_0525 = t283.WindowSpec("owner_0525_latest", "owner_replay", _dt("2026-05-25T00:00:00Z"), latest)
    pre_owner = t283.WindowSpec("available_pre_owner_0510_0517", "pre_owner", _dt("2026-05-10T00:00:00Z"), _dt("2026-05-17T15:19:00Z"))
    specs: list[ValidationSpec] = [
        ValidationSpec(owner_0520, "conservative_crypto_1m", "owner_replay", "owner_replay"),
        ValidationSpec(owner_0525, "conservative_crypto_1m", "owner_replay", "owner_replay"),
        ValidationSpec(pre_owner, "conservative_crypto_1m", "pre_owner", "pre_owner"),
    ]

    for base in (owner_0520, owner_0525):
        for hours in (6, 12, 24):
            specs.append(
                ValidationSpec(
                    t283.WindowSpec(
                        f"{base.window_id}_drop_first_{hours}h",
                        "endpoint_trim",
                        base.start_time + timedelta(hours=hours),
                        base.end_time,
                    ),
                    "conservative_crypto_1m",
                    "endpoint_trim",
                    "endpoint_trim",
                )
            )
            specs.append(
                ValidationSpec(
                    t283.WindowSpec(
                        f"{base.window_id}_drop_last_{hours}h",
                        "endpoint_trim",
                        base.start_time,
                        base.end_time - timedelta(hours=hours),
                    ),
                    "conservative_crypto_1m",
                    "endpoint_trim",
                    "endpoint_trim",
                )
            )
        midpoint = base.start_time + ((base.end_time - base.start_time) / 2)
        specs.append(
            ValidationSpec(
                t283.WindowSpec(f"{base.window_id}_first_half", "endpoint_split", base.start_time, midpoint),
                "conservative_crypto_1m",
                "endpoint_split",
                "endpoint_split",
            )
        )
        specs.append(
            ValidationSpec(
                t283.WindowSpec(f"{base.window_id}_second_half", "endpoint_split", midpoint, base.end_time),
                "conservative_crypto_1m",
                "endpoint_split",
                "endpoint_split",
            )
        )

    for base in (owner_0520, owner_0525):
        for key in ("fee_2x", "slippage_2x", "fee_slippage_2x", "high_slippage_stress", "zero"):
            specs.append(ValidationSpec(base, key, "cost_sensitivity", "cost_sensitivity", diagnostic_only=(key == "zero")))

    specs.extend(
        [
            ValidationSpec(pre_owner, "high_slippage_stress", "pre_owner_cost_stress", "cost_sensitivity", diagnostic_only=True),
            ValidationSpec(owner_0520, "conservative_crypto_1m", "execution_assumption", "execution_assumption", action_mode="b1_same_candle_exit", diagnostic_only=True, candidate_id="T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002"),
            ValidationSpec(owner_0525, "conservative_crypto_1m", "execution_assumption", "execution_assumption", action_mode="b1_same_candle_exit", diagnostic_only=True, candidate_id="T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002"),
            ValidationSpec(owner_0520, "conservative_crypto_1m", "execution_assumption", "execution_assumption", action_mode="one_candle_delayed_entry", diagnostic_only=True),
            ValidationSpec(owner_0525, "conservative_crypto_1m", "execution_assumption", "execution_assumption", action_mode="one_candle_delayed_entry", diagnostic_only=True),
        ]
    )
    return tuple(spec for spec in specs if spec.window.end_time > spec.window.start_time)


def cost_profile_map() -> dict[str, CostProfile]:
    base = COST_PROFILES["conservative_crypto_1m"].config
    return {
        **COST_PROFILES,
        "fee_2x": CostProfile(
            "fee_2x",
            "Conservative 1m profile with taker fee doubled.",
            TransactionCostConfig(
                taker_fee_bps=base.taker_fee_bps * 2.0,
                spread_bps=base.spread_bps,
                slippage_bps=base.slippage_bps,
                minimum_slippage_bps=base.minimum_slippage_bps,
                volatility_slippage_multiplier=base.volatility_slippage_multiplier,
            ),
        ),
        "slippage_2x": CostProfile(
            "slippage_2x",
            "Conservative 1m profile with base/minimum/volatility slippage doubled.",
            TransactionCostConfig(
                taker_fee_bps=base.taker_fee_bps,
                spread_bps=base.spread_bps,
                slippage_bps=base.slippage_bps * 2.0,
                minimum_slippage_bps=base.minimum_slippage_bps * 2.0,
                volatility_slippage_multiplier=base.volatility_slippage_multiplier * 2.0,
            ),
        ),
        "fee_slippage_2x": CostProfile(
            "fee_slippage_2x",
            "Conservative 1m profile with taker fee and slippage doubled.",
            TransactionCostConfig(
                taker_fee_bps=base.taker_fee_bps * 2.0,
                spread_bps=base.spread_bps,
                slippage_bps=base.slippage_bps * 2.0,
                minimum_slippage_bps=base.minimum_slippage_bps * 2.0,
                volatility_slippage_multiplier=base.volatility_slippage_multiplier * 2.0,
            ),
        ),
    }


def run_matrix(*, database_url: str, limit: int | None = None) -> list[ValidationRecord]:
    coverage = data_coverage_report(database_url)
    if coverage.available_end_time is None:
        write_report([], coverage=coverage, baselines=(), gate_report=classify_records([], coverage, ()))
        return []
    specs = build_validation_specs(coverage.available_end_time)
    records: list[ValidationRecord] = []
    for index, spec in enumerate(specs, start=1):
        if limit is not None and index > limit:
            break
        records.append(run_one(database_url=database_url, spec=spec))
    baselines = build_baseline_results(database_url, records)
    gate_report = classify_records(records, coverage, baselines)
    write_report(records, coverage=coverage, baselines=baselines, gate_report=gate_report)
    return records


def rewrite_report_from_existing_runs(*, database_url: str) -> list[ValidationRecord]:
    coverage = data_coverage_report(database_url)
    records = load_existing_task284_records(database_url)
    baselines = build_baseline_results(database_url, records)
    gate_report = classify_records(records, coverage, baselines)
    write_report(records, coverage=coverage, baselines=baselines, gate_report=gate_report)
    return records


def load_existing_task284_records(database_url: str) -> list[ValidationRecord]:
    import psycopg

    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id
            FROM backtest_runs
            WHERE metadata->'research'->>'task_id' = %s
            ORDER BY id
            """,
            (TASK_ID,),
        ).fetchall()
    repository = PostgresBacktestResultRepository(database_url)
    records: list[ValidationRecord] = []
    for (run_id,) in rows:
        persisted = repository.load_run_for_graphs(int(run_id))
        if persisted is None:
            continue
        research = (persisted.run.metadata or {}).get("research") or {}
        window = t283.WindowSpec(
            str(research.get("window_id") or f"run_{run_id}"),
            str(research.get("validation_group") or "unknown"),
            _as_utc(persisted.run.requested_start_time or persisted.run.actual_start_time),
            _as_utc(persisted.run.requested_end_time or persisted.run.actual_end_time),
        )
        spec = ValidationSpec(
            window=window,
            cost_profile_key=str(research.get("cost_profile") or "unknown"),
            run_group=str(research.get("run_group") or "unknown"),
            validation_axis=str(research.get("validation_axis") or "unknown"),
            action_mode=str(research.get("action_mode") or "locked_b2"),
            diagnostic_only=bool(research.get("diagnostic_only")),
            candidate_id=str(research.get("candidate_id") or LOCKED_CANDIDATE_ID),
        )
        validation_meta = (persisted.run.metadata or {}).get("task284_validation")
        if not isinstance(validation_meta, dict):
            validation_meta = (persisted.summary.metadata or {}).get("task284_validation")
        action_entries = int((validation_meta or {}).get("action_entries") or 0)
        records.append(
            analyze_persisted_run(
                persisted,
                spec=spec,
                quality={"candle_continuity_ok": True, "candle_gap_count": 0},
                action_entries=action_entries,
            )
        )
    return records


def run_one(*, database_url: str, spec: ValidationSpec) -> ValidationRecord:
    candles = t283.load_candles(database_url, spec.window)
    if candles.empty:
        return _skipped_record(spec, "no_local_candles_for_window")
    quality = t283.candle_quality(candles)
    if not bool(quality["candle_continuity_ok"]):
        return _skipped_record(spec, "local_candle_continuity_gap", quality=quality)
    profiles = cost_profile_map()
    cost_profile = profiles[spec.cost_profile_key]
    candidate = candidate_by_id(spec.candidate_id)
    actions, action_meta = generate_validation_actions(candles, candidate, spec, cost_profile)
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
        "locked_candidate_id": LOCKED_CANDIDATE_ID,
        "candidate_id": candidate.variant_id,
        "validation_mode": "locked_multi_axis_revalidation",
        "no_retune": True,
        "research_only": True,
        "diagnostic_only": spec.diagnostic_only,
        "validation_axis": spec.validation_axis,
        "run_group": spec.run_group,
        "window_id": spec.window.window_id,
        "validation_group": spec.window.validation_group,
        "cost_profile": spec.cost_profile_key,
        "action_mode": spec.action_mode,
        "no_live_trading": True,
    }
    metadata["research"] = research
    metadata["task284_validation"] = {
        "schema_version": "task284_validation_metadata_v1",
        "locked_source": "Task 283 best candidate",
        "signal_execution_separated": True,
        "completed_candle_only": True,
        "intrabar_ambiguity_policy": "stop_first_when_stop_and_target_hit_same_candle",
        "action_entries": action_meta.generated_entries,
        "action_signal_counts": action_meta.signal_counts,
        "action_exit_reasons": action_meta.exit_reasons,
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
        strategy_version=f"task284_{spec.action_mode}_{spec.window.window_id}_{spec.cost_profile_key}_v1",
        strategy_parameters={
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "locked_candidate_id": LOCKED_CANDIDATE_ID,
            "candidate": candidate.variant_id,
            "candidate_params": candidate.params,
            "no_retune": True,
            "diagnostic_only": spec.diagnostic_only,
            "validation_axis": spec.validation_axis,
            "window": {
                "window_id": spec.window.window_id,
                "validation_group": spec.window.validation_group,
                "start_time": _iso(spec.window.start_time),
                "end_time": _iso(spec.window.end_time),
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
            "task284_validation": metadata["task284_validation"],
        },
    )
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    if persisted is None:
        raise RuntimeError(f"Task 284 persisted run could not be read back: {run_id}")
    return analyze_persisted_run(persisted, spec=spec, quality=quality, action_entries=action_meta.generated_entries)


def generate_validation_actions(
    candles: pd.DataFrame,
    candidate: t283.CandidateSpec,
    spec: ValidationSpec,
    cost_profile: CostProfile,
) -> tuple[list[StrategyAction], t283.ActionGenerationMetadata]:
    if spec.action_mode == "one_candle_delayed_entry":
        return generate_one_candle_delayed_entry_actions(candles, candidate)
    return t283.generate_actions(candles, candidate, cost_config=cost_profile.config)


def generate_one_candle_delayed_entry_actions(
    candles: pd.DataFrame,
    candidate: t283.CandidateSpec,
) -> tuple[list[StrategyAction], t283.ActionGenerationMetadata]:
    frame = t283.build_factor_snapshots(candles)
    params = candidate.params
    core_signals = t283._ensemble_core_signals(frame, params)
    scout_signals = t283._ensemble_scout_signals(frame)
    actions: list[StrategyAction] = []
    generated_core = generated_scout = skipped_pre_entry = preemptions = 0
    exit_reasons: dict[str, int] = defaultdict(int)
    index = 960
    while index < len(frame) - 3:
        if index in core_signals:
            side = core_signals[index]
            layer = "core"
            fraction = float(params.get("core_fraction", 1.0))
            target_bps = float(params.get("core_target_bps", 260.0))
            stop_bps = float(params.get("core_stop_bps", 130.0))
            hold_bars = int(params.get("core_hold_bars", 480))
        elif index in scout_signals:
            side = scout_signals[index]
            layer = "scout"
            fraction = float(params.get("scout_fraction", 0.02))
            target_bps = float(params.get("scout_target_bps", 150.0))
            stop_bps = float(params.get("scout_stop_bps", 75.0))
            hold_bars = int(params.get("scout_hold_bars", 120))
        else:
            index += 1
            continue

        condition_index, condition_price, exit_reason = t283._resolve_ensemble_condition_exit(
            frame,
            signal_index=index,
            side=side,
            target_bps=target_bps,
            stop_bps=stop_bps,
            hold_bars=hold_bars,
            core_signals=core_signals,
            preempt_on_core=bool(layer == "scout" and params.get("preempt_scout_on_core", True)),
        )
        entry_index = index + 2
        if condition_index < entry_index or entry_index >= len(frame) - 1:
            skipped_pre_entry += 1
            index = max(condition_index + 1, index + 1)
            continue
        exit_index = min(condition_index + 1, len(frame) - 1)
        entry_price = float(frame.iloc[entry_index]["open"])
        exit_price = float(frame.iloc[exit_index]["open"])
        target = entry_price * (1.0 + target_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 - target_bps / 10_000.0)
        stop = entry_price * (1.0 - stop_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 + stop_bps / 10_000.0)
        if exit_reason == "TASK283_SCOUT_PREEMPT_CORE_SIGNAL":
            preemptions += 1
        exit_reasons[exit_reason] += 1
        event_id = f"T284_DELAY1_{candidate.variant_id}_{layer}_{entry_index}"
        event_actions = t283._entry_exit_actions(
            frame,
            candidate=candidate,
            signal_index=index,
            entry_index=entry_index,
            exit_index=exit_index,
            side=side,
            entry_price=entry_price,
            stop_price=stop,
            target_price=target,
            exit_price=exit_price,
            exit_reason=exit_reason,
            event_id=event_id,
            cash_fraction=fraction,
            signal_name=f"ensemble_{layer}_one_candle_delayed_entry",
            cost_gate={
                "schema_version": "task284_one_candle_delayed_entry_v1",
                "blocked": False,
                "diagnostic_only": True,
                "exit_condition_timestamp": _iso(pd.Timestamp(frame.iloc[condition_index]["timestamp"]).to_pydatetime()),
                "exit_condition_price": float(condition_price),
                "entry_execution_model": "one_candle_delayed_next_open_diagnostic",
                "exit_execution_model": "next_candle_open_after_exit_condition",
            },
            layer=layer,
        )
        for action in event_actions:
            action.metadata["entry_execution_model"] = "one_candle_delayed_next_open_diagnostic"
            action.metadata["task284_execution_diagnostic"] = "one_candle_delayed_entry"
            action.metadata["diagnostic_only"] = True
        actions.extend(event_actions)
        if layer == "core":
            generated_core += 1
        else:
            generated_scout += 1
        index = max(condition_index + 1, index + 1)
    return actions, t283.ActionGenerationMetadata(
        generated_entries=generated_core + generated_scout,
        cost_rejections=skipped_pre_entry,
        signal_counts={"core": generated_core, "scout": generated_scout, "preemptions": preemptions, "skipped_pre_entry": skipped_pre_entry},
        exit_reasons=dict(exit_reasons),
        factor_schema_version="task283_factor_snapshot_v1",
    )


def analyze_persisted_run(
    persisted: BacktestRunReadModel,
    *,
    spec: ValidationSpec,
    quality: dict[str, Any],
    action_entries: int,
) -> ValidationRecord:
    summary = persisted.summary
    metadata = summary.metadata or {}
    cost_summary = metadata.get("cost_summary") if isinstance(metadata.get("cost_summary"), dict) else {}
    event_rows = event_trade_rows(persisted.trades)
    event_net_pnls = [row["net_pnl"] for row in event_rows]
    trade_contrib = trade_contribution_metrics(event_net_pnls)
    cost_audit = t283.audit_persisted_trade_costs(persisted.trades)
    summary_audit = audit_summary_costs(cost_summary, cost_audit)
    side_attr = bucket_attribution(event_rows, key="side")
    session_attr = bucket_attribution(event_rows, key="session")
    regime_attr = (
        *bucket_attribution(event_rows, key="volatility_regime"),
        *bucket_attribution(event_rows, key="trend_alignment"),
        *bucket_attribution(event_rows, key="volume_regime"),
    )
    perf = t283._realized_trade_stats(event_net_pnls, [])
    research = (persisted.run.metadata or {}).get("research") or {}
    summary_research = metadata.get("research") if isinstance(metadata.get("research"), dict) else {}
    readback_ok = bool(
        research.get("task_id") == TASK_ID
        and summary_research.get("task_id") == TASK_ID
        and research.get("parent_task_id") == PARENT_TASK_ID
        and summary_research.get("locked_candidate_id") == LOCKED_CANDIDATE_ID
        and research.get("no_retune") is True
    )
    return ValidationRecord(
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
        total_fee_cost=cost_audit.total_fee_cost,
        total_spread_cost=cost_audit.total_spread_cost,
        total_slippage_cost=cost_audit.total_slippage_cost,
        total_cost=cost_audit.total_cost,
        total_notional=cost_audit.total_notional,
        effective_total_cost_bps=cost_audit.effective_total_cost_bps,
        cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
        action_entries=action_entries,
        cost_formula_mismatch_count=cost_audit.mismatch_count,
        summary_cost_mismatch_count=summary_audit.mismatch_count,
        max_cost_mismatch=max(cost_audit.max_abs_mismatch, summary_audit.max_abs_mismatch),
        readback_ok=readback_ok,
        candle_continuity_ok=bool(quality.get("candle_continuity_ok")),
        candle_gap_count=int(quality.get("candle_gap_count") or 0),
        side_attribution=side_attr,
        session_attribution=session_attr,
        regime_attribution=regime_attr,
        outlier_audit=outlier_audit(event_net_pnls, trade_contrib.net_profit),
    )


def data_coverage_report(database_url: str) -> DataCoverageReport:
    availability = t283.load_data_availability(database_url)
    gaps: list[tuple[datetime, datetime, int]] = []
    if availability.available_start_time and availability.available_end_time:
        candles = t283.load_candles(
            database_url,
            t283.WindowSpec(
                "local_available_coverage_audit",
                "coverage_audit",
                availability.available_start_time,
                availability.available_end_time,
            ),
        )
        timestamps = pd.to_datetime(candles["timestamp"], utc=True).sort_values()
        diffs = timestamps.diff()
        gap_indices = diffs[diffs > pd.Timedelta(minutes=1)].index
        for idx in gap_indices:
            previous_ts = timestamps.loc[idx] - diffs.loc[idx]
            current_ts = timestamps.loc[idx]
            missing = int(diffs.loc[idx] / pd.Timedelta(minutes=1)) - 1
            gaps.append((_as_utc(previous_ts), _as_utc(current_ts), missing))
    april20_complete = bool(
        availability.available_start_time
        and availability.available_start_time <= availability.requested_start_time
        and not gaps
    )
    return DataCoverageReport(
        requested_start_time=availability.requested_start_time,
        available_start_time=availability.available_start_time,
        available_end_time=availability.available_end_time,
        candle_count=availability.candle_count,
        gap_count=len(gaps),
        gaps=tuple(gaps),
        april20_forward_complete=april20_complete,
    )


def audit_summary_costs(cost_summary: dict[str, Any], audit: t283.CostAudit) -> SummaryCostAudit:
    expected = {
        "total_fee_cost": audit.total_fee_cost,
        "total_spread_cost": audit.total_spread_cost,
        "total_slippage_cost": audit.total_slippage_cost,
        "total_cost": audit.total_cost,
    }
    mismatch_count = 0
    max_abs = 0.0
    for key, expected_value in expected.items():
        actual = _float(cost_summary.get(key))
        if actual is None:
            mismatch_count += 1
            max_abs = max(max_abs, abs(expected_value))
            continue
        diff = abs(actual - expected_value)
        if diff > 1e-6:
            mismatch_count += 1
            max_abs = max(max_abs, diff)
    return SummaryCostAudit(mismatch_count=mismatch_count, max_abs_mismatch=max_abs)


def event_trade_rows(trades: Iterable[Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        event_id = str(metadata.get("event_id") or metadata.get("pattern_event_id") or f"sequence_{getattr(trade, 'sequence', 0)}")
        row = rows.setdefault(
            event_id,
            {
                "event_id": event_id,
                "side": str(metadata.get("position_side") or "UNKNOWN"),
                "session": "UNKNOWN",
                "volatility_regime": "vol_UNKNOWN",
                "trend_alignment": "trend_UNKNOWN",
                "volume_regime": "volume_UNKNOWN",
                "realized_vol_bps_30": None,
                "gross_pnl": 0.0,
                "total_cost": 0.0,
                "net_pnl": 0.0,
            },
        )
        row["total_cost"] += _float(metadata.get("total_cost")) or 0.0
        if metadata.get("action_type") in {StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value}:
            snapshot = metadata.get("task283_factor_snapshot") if isinstance(metadata.get("task283_factor_snapshot"), dict) else {}
            row["side"] = str(metadata.get("position_side") or row["side"])
            row["session"] = str(snapshot.get("session_tag") or "UNKNOWN")
            row["volatility_regime"] = volatility_regime(snapshot)
            row["realized_vol_bps_30"] = _float(snapshot.get("realized_vol_bps_30"))
            row["trend_alignment"] = trend_alignment(str(row["side"]), snapshot)
            row["volume_regime"] = volume_regime(snapshot)
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            row["gross_pnl"] += gross
    result = []
    for row in rows.values():
        row["net_pnl"] = float(row["gross_pnl"]) - float(row["total_cost"])
        if row["gross_pnl"] != 0.0 or row["total_cost"] != 0.0:
            result.append(row)
    vol_values = [
        float(row["realized_vol_bps_30"])
        for row in result
        if row.get("realized_vol_bps_30") is not None
    ]
    if vol_values:
        median_vol = float(pd.Series(vol_values).median())
        for row in result:
            value = row.get("realized_vol_bps_30")
            if value is not None:
                row["volatility_regime"] = "vol_HIGH" if float(value) >= median_vol else "vol_LOW"
    return result


def bucket_attribution(rows: Sequence[dict[str, Any]], *, key: str) -> tuple[BucketAttribution, ...]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "UNKNOWN")].append(row)
    output: list[BucketAttribution] = []
    for bucket, values in sorted(grouped.items()):
        net_values = [float(row["net_pnl"]) for row in values]
        gross = sum(float(row["gross_pnl"]) for row in values)
        cost = sum(float(row["total_cost"]) for row in values)
        wins = [value for value in net_values if value > 0.0]
        output.append(
            BucketAttribution(
                bucket=bucket,
                completed_round_trips=len(values),
                gross_pnl=gross,
                total_cost=cost,
                net_pnl=sum(net_values),
                win_rate=None if not values else len(wins) / len(values),
                average_net_pnl=None if not values else sum(net_values) / len(values),
            )
        )
    return tuple(output)


def outlier_audit(event_net_pnls: Sequence[float], net_pnl: float) -> OutlierAudit:
    winners = sorted((float(value) for value in event_net_pnls if value > 0.0), reverse=True)
    largest = winners[0] if winners else 0.0
    top_three = sum(winners[:3])
    net_without_largest = float(net_pnl) - largest
    net_without_top_three = float(net_pnl) - top_three
    return OutlierAudit(
        event_count=len(event_net_pnls),
        net_pnl=float(net_pnl),
        largest_winner_contribution=None if net_pnl <= 0 or not winners else largest / net_pnl,
        top_three_winner_contribution=None if net_pnl <= 0 or not winners else top_three / net_pnl,
        net_without_largest_winner=net_without_largest,
        net_without_top_three_winners=net_without_top_three,
        return_without_largest_winner=net_without_largest / STARTING_CASH,
        return_without_top_three_winners=net_without_top_three / STARTING_CASH,
    )


def build_baseline_results(database_url: str, records: Sequence[ValidationRecord]) -> tuple[BaselineResult, ...]:
    primary_windows = {
        record.spec.window.window_id: record.spec.window
        for record in records
        if record.spec.run_group == "owner_replay" and record.run_id is not None
    }
    baselines: list[BaselineResult] = []
    for window_id, window in sorted(primary_windows.items()):
        candles = t283.load_candles(database_url, window)
        if candles.empty:
            continue
        baselines.append(buy_and_hold_baseline(candles, window_id))
        baselines.append(ma_trend_baseline(candles, window_id))
        reference = next((record for record in records if record.spec.window.window_id == window_id and record.spec.run_group == "owner_replay"), None)
        target_trades = reference.completed_round_trips if reference else 0
        baselines.append(random_entry_baseline(candles, window_id, target_trades=target_trades, seed=284))
    return tuple(baselines)


def buy_and_hold_baseline(candles: pd.DataFrame, window_id: str) -> BaselineResult:
    if len(candles) < 2:
        return BaselineResult(window_id, "buy_and_hold_long", None, 0, "not enough candles")
    first = float(candles.iloc[1]["open"])
    last = float(candles.iloc[-1]["close"])
    return BaselineResult(window_id, "buy_and_hold_long", (last / first) - 1.0, 1, "full notional long, no cost diagnostic")


def ma_trend_baseline(candles: pd.DataFrame, window_id: str) -> BaselineResult:
    frame = candles.copy(deep=True).reset_index(drop=True)
    frame["close"] = pd.to_numeric(frame["close"], errors="raise").astype(float)
    frame["fast"] = frame["close"].shift(1).rolling(20, min_periods=20).mean()
    frame["slow"] = frame["close"].shift(1).rolling(120, min_periods=120).mean()
    returns: list[float] = []
    for index in range(121, len(frame)):
        direction = 1.0 if frame.iloc[index]["fast"] > frame.iloc[index]["slow"] else -1.0
        prev = float(frame.iloc[index - 1]["close"])
        current = float(frame.iloc[index]["close"])
        returns.append(direction * ((current / prev) - 1.0))
    total = math.prod(1.0 + value for value in returns) - 1.0 if returns else None
    return BaselineResult(window_id, "ma20_120_flip_no_cost", total, len(returns), "close-to-close diagnostic, no execution costs")


def random_entry_baseline(candles: pd.DataFrame, window_id: str, *, target_trades: int, seed: int) -> BaselineResult:
    if len(candles) < 240 or target_trades <= 0:
        return BaselineResult(window_id, "random_entry_seed284", None, 0, "not enough candles or target trades")
    rng = __import__("random").Random(seed)
    frame = candles.reset_index(drop=True)
    max_start = len(frame) - 121
    if max_start <= 121:
        return BaselineResult(window_id, "random_entry_seed284", None, 0, "not enough room")
    starts = sorted(rng.sample(range(121, max_start), k=min(target_trades, max_start - 121)))
    pnl_fraction = 0.0
    completed = 0
    for start in starts:
        hold = rng.randint(30, 180)
        end = min(start + hold, len(frame) - 1)
        side = 1.0 if rng.random() >= 0.5 else -1.0
        entry = float(frame.iloc[start]["open"])
        exit_ = float(frame.iloc[end]["open"])
        pnl_fraction += side * ((exit_ / entry) - 1.0)
        completed += 1
    return BaselineResult(window_id, "random_entry_seed284", pnl_fraction, completed, "sum of full-notional random trade returns, no cost diagnostic")


def classify_records(
    records: Sequence[ValidationRecord],
    coverage: DataCoverageReport,
    baselines: Sequence[BaselineResult],
) -> GateReport:
    completed = [record for record in records if record.run_id is not None]
    base_0520 = _record(completed, "owner_0520_latest", "owner_replay", "conservative_crypto_1m")
    base_0525 = _record(completed, "owner_0525_latest", "owner_replay", "conservative_crypto_1m")
    pre_owner = _record(completed, "available_pre_owner_0510_0517", "pre_owner", "conservative_crypto_1m")
    endpoint = [record for record in completed if record.spec.run_group in {"endpoint_trim", "endpoint_split"}]
    cost_stress = [record for record in completed if record.spec.run_group == "cost_sensitivity" and record.spec.cost_profile_key != "zero"]
    execution = [record for record in completed if record.spec.run_group == "execution_assumption"]
    cost_mismatch = sum(record.cost_formula_mismatch_count + record.summary_cost_mismatch_count for record in completed)
    zero_0520 = _record(completed, "owner_0520_latest", "cost_sensitivity", "zero")
    owner_baselines = [baseline for baseline in baselines if baseline.window_id == "owner_0520_latest"]
    rows = (
        ("0520 locked replay return", ">= +3pct", _pct(base_0520.total_return if base_0520 else None), bool(base_0520 and (base_0520.total_return or 0.0) >= 0.03)),
        ("0525 locked replay return", ">= +3pct", _pct(base_0525.total_return if base_0525 else None), bool(base_0525 and (base_0525.total_return or 0.0) >= 0.03)),
        ("0520 locked replay trips", ">= 50", str(base_0520.completed_round_trips if base_0520 else 0), bool(base_0520 and base_0520.completed_round_trips >= 50)),
        ("All cost audit mismatches", "0", str(cost_mismatch), cost_mismatch == 0),
        ("Non-zero base costs", "fee/spread/slippage > 0", _cost_presence(base_0520), bool(base_0520 and (base_0520.total_fee_cost or 0) > 0 and (base_0520.total_spread_cost or 0) > 0 and (base_0520.total_slippage_cost or 0) > 0)),
        ("Pre-owner return", ">= 0pct for robustness", _pct(pre_owner.total_return if pre_owner else None), bool(pre_owner and (pre_owner.total_return or 0.0) >= 0.0)),
        ("Endpoint diagnostics positive", "all > 0pct", f"{sum(1 for r in endpoint if (r.total_return or 0.0) > 0.0)}/{len(endpoint)}", bool(endpoint) and all((r.total_return or 0.0) > 0.0 for r in endpoint)),
        ("Cost stress survives", "all > -3pct", f"{sum(1 for r in cost_stress if (r.total_return or 0.0) > -0.03)}/{len(cost_stress)}", bool(cost_stress) and all((r.total_return or 0.0) > -0.03 for r in cost_stress)),
        ("Execution diagnostics available", ">= 2", str(len(execution)), len(execution) >= 2),
        ("Outlier top-three 0520", "<= 0.70", _ratio(base_0520.outlier_audit.top_three_winner_contribution if base_0520 else None), bool(base_0520 and base_0520.outlier_audit.top_three_winner_contribution is not None and base_0520.outlier_audit.top_three_winner_contribution <= 0.70)),
        ("Return without top-three 0520 winners", "> 0pct", _pct(base_0520.outlier_audit.return_without_top_three_winners if base_0520 else None), bool(base_0520 and base_0520.outlier_audit.return_without_top_three_winners > 0.0)),
        ("April-20 coverage", "complete data required for April claim", "complete" if coverage.april20_forward_complete else "DATA_BLOCKED", coverage.april20_forward_complete),
        ("Baseline diagnostics generated", ">= 3", str(len(owner_baselines)), len(owner_baselines) >= 3),
    )
    failed = tuple(name for name, _, _, ok in rows if not ok)
    if failed:
        status = "ROBUSTNESS_REJECTED_RESEARCH_ONLY"
    else:
        status = "ROBUSTNESS_PASSED_RESEARCH_ONLY"
    conclusion_parts = []
    if pre_owner and (pre_owner.total_return or 0.0) < 0.0:
        conclusion_parts.append("available pre-owner replay is negative")
    if not coverage.april20_forward_complete:
        conclusion_parts.append("complete April-20-forward OOS remains data-blocked")
    if zero_0520 and base_0520 and zero_0520.total_return is not None:
        gap = (zero_0520.total_return or 0.0) - (base_0520.total_return or 0.0)
        conclusion_parts.append(f"zero-cost gap on 0520 is {gap * 100:+.4f}pct")
    if base_0520 and base_0520.outlier_audit.return_without_top_three_winners <= 0.0:
        conclusion_parts.append("0520 net return depends on top-three winners")
    if not conclusion_parts:
        conclusion_parts.append("locked validation did not find a hard robustness failure beyond research-only scope")
    return GateReport(status=status, rows=rows, failed_gates=failed, conclusion="; ".join(conclusion_parts))


def write_report(
    records: Sequence[ValidationRecord],
    *,
    coverage: DataCoverageReport,
    baselines: Sequence[BaselineResult],
    gate_report: GateReport,
) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_ids = ", ".join(str(record.run_id) for record in records if record.run_id is not None) or "-"
    lines = [
        "# Task 284 Task 283 Multi-Axis Robustness Revalidation",
        "",
        f"Status: `{gate_report.status}`",
        "",
        "## Locked Model",
        "",
        f"- Parent task: `{PARENT_TASK_ID}`.",
        f"- Locked candidate: `{LOCKED_CANDIDATE_ID}`.",
        "- Retune policy: no entry threshold, exit threshold, sizing, or signal logic retuning in primary validation.",
        "- Diagnostic-only variants are excluded from promotion decisions.",
        "- Result scope: offline research-only, no live trading.",
        "",
        "## Data Coverage",
        "",
        f"- Requested April-20-forward start: `{_iso(coverage.requested_start_time)}`.",
        f"- Local available start: `{_iso(coverage.available_start_time)}`.",
        f"- Local available end: `{_iso(coverage.available_end_time)}`.",
        f"- Closed candle count from requested start: `{coverage.candle_count}`.",
        f"- Continuity gap count: `{coverage.gap_count}`.",
        f"- April-20-forward complete: `{coverage.april20_forward_complete}`.",
    ]
    if coverage.gaps:
        lines.extend(["", "| Gap Previous Candle | Gap Next Candle | Missing 1m Candles |", "| --- | --- | ---: |"])
        for left, right, missing in coverage.gaps:
            lines.append(f"| `{_iso(left)}` | `{_iso(right)}` | {missing} |")
    else:
        lines.append("- Gaps: `-`.")
    lines.extend(
        [
            "",
            "## Persisted Validation Runs",
            "",
            f"- Task 284 run IDs: `{run_ids}`.",
            "",
            "| Axis | Group | Window | Action Mode | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Cost bps | Formula MM | Summary MM | Status |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.spec.validation_axis,
                    record.spec.run_group,
                    record.spec.window.window_id,
                    record.spec.action_mode,
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
                    _ratio(record.effective_total_cost_bps),
                    str(record.cost_formula_mismatch_count),
                    str(record.summary_cost_mismatch_count),
                    record.status if record.run_id is not None else str(record.skip_reason),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Gate Check", "", "| Gate | Required | Observed | Status |", "| --- | --- | --- | --- |"])
    for name, required, observed, ok in gate_report.rows:
        lines.append(f"| {name} | {required} | {observed} | `{'PASS' if ok else 'FAIL'}` |")

    lines.extend(["", "## Cost Audit", ""])
    for record in records:
        if record.run_id is None:
            continue
        lines.append(
            f"- Run `{record.run_id}` `{record.spec.window.window_id}` `{record.spec.cost_profile_key}`: notional `{_money(record.total_notional)}`, fee `{_money(record.total_fee_cost)}`, spread `{_money(record.total_spread_cost)}`, slippage `{_money(record.total_slippage_cost)}`, total `{_money(record.total_cost)}`, one-way cost `{_ratio(record.effective_total_cost_bps)}` bps, formula mismatch `{record.cost_formula_mismatch_count}`, summary mismatch `{record.summary_cost_mismatch_count}`."
        )

    owner = _record([record for record in records if record.run_id is not None], "owner_0520_latest", "owner_replay", "conservative_crypto_1m")
    if owner:
        lines.extend(["", "## Attribution: 0520 Locked Replay", "", "### Side", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in owner.side_attribution:
            lines.append(_bucket_row(row))
        lines.extend(["", "### Session", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in owner.session_attribution:
            lines.append(_bucket_row(row))
        lines.extend(["", "### Regime", "", "| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
        for row in owner.regime_attribution:
            lines.append(_bucket_row(row))
        lines.extend(
            [
                "",
                "### Outlier Dependence",
                "",
                f"- Largest winner contribution: `{_ratio(owner.outlier_audit.largest_winner_contribution)}`.",
                f"- Top-three winner contribution: `{_ratio(owner.outlier_audit.top_three_winner_contribution)}`.",
                f"- Return without largest winner: `{_pct(owner.outlier_audit.return_without_largest_winner)}`.",
                f"- Return without top-three winners: `{_pct(owner.outlier_audit.return_without_top_three_winners)}`.",
            ]
        )

    lines.extend(["", "## Baselines", "", "| Window | Baseline | Return | Trips | Note |", "| --- | --- | ---: | ---: | --- |"])
    for baseline in baselines:
        lines.append(f"| {baseline.window_id} | `{baseline.baseline_id}` | {_pct(baseline.total_return)} | {baseline.completed_round_trips} | {baseline.note} |")

    lines.extend(
        [
            "",
            "## Bias And Safety Checks",
            "",
            "- Signal/entry separation: Task 283 locked model enters on next candle open; B2 exits on next candle open after the exit condition.",
            "- Completed-candle factors: reused Task 283 factor snapshots, which are prior/completed-candle only.",
            "- MTF context: prior 15m/1h return proxies from completed 1m history; no incomplete higher-timeframe candle is fetched.",
            "- Intrabar ambiguity: stop-first when stop and target are both touched in the same candle.",
            "- Position overlap: action generation advances past the resolved exit and the engine has an open-position guard.",
            "- Live trading safety: no execution client imports, no signed requests, no API keys, no `.env` handling, no order/account endpoints.",
            "",
            "## Conclusion",
            "",
            f"- Final status: `{gate_report.status}`.",
            f"- Failed gates: `{', '.join(gate_report.failed_gates) if gate_report.failed_gates else '-'}`.",
            f"- Interpretation: {gate_report.conclusion}.",
            "- No Task 284 result is promoted beyond `RESEARCH_ONLY`.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def candidate_by_id(candidate_id: str) -> t283.CandidateSpec:
    for candidate in t283.build_candidates():
        if candidate.variant_id == candidate_id:
            return candidate
    raise ValueError(f"unknown Task 283 candidate: {candidate_id}")


def volatility_regime(snapshot: dict[str, Any]) -> str:
    percentile = _float(snapshot.get("realized_vol_percentile_240"))
    if percentile is None:
        vol_bps = _float(snapshot.get("realized_vol_bps_30"))
        if vol_bps is None:
            return "vol_UNKNOWN"
        return "vol_HIGH" if vol_bps >= 10.0 else "vol_LOW"
    return "vol_HIGH" if percentile >= 0.50 else "vol_LOW"


def trend_alignment(side: str, snapshot: dict[str, Any]) -> str:
    trend_15 = _float(snapshot.get("mtf_15m_trend_bps")) or 0.0
    trend_60 = _float(snapshot.get("mtf_1h_trend_bps")) or 0.0
    trend = trend_15 + trend_60
    if abs(trend) < 1e-9:
        return "trend_MIXED"
    if (side == "LONG" and trend > 0.0) or (side == "SHORT" and trend < 0.0):
        return "trend_ALIGNED"
    return "trend_COUNTER"


def volume_regime(snapshot: dict[str, Any]) -> str:
    ratio = _float(snapshot.get("volume_ratio_20"))
    if ratio is None:
        return "volume_UNKNOWN"
    return "volume_EXPANSION" if ratio >= 1.0 else "volume_NORMAL"


def _record(records: Sequence[ValidationRecord], window_id: str, run_group: str, cost_profile_key: str) -> ValidationRecord | None:
    return next(
        (
            record
            for record in records
            if record.spec.window.window_id == window_id
            and record.spec.run_group == run_group
            and record.spec.cost_profile_key == cost_profile_key
            and record.run_id is not None
        ),
        None,
    )


def _skipped_record(
    spec: ValidationSpec,
    reason: str,
    *,
    quality: dict[str, Any] | None = None,
) -> ValidationRecord:
    return ValidationRecord(
        spec=spec,
        run_id=None,
        status="SKIPPED",
        skip_reason=reason,
        candle_continuity_ok=bool((quality or {}).get("candle_continuity_ok", False)),
        candle_gap_count=int((quality or {}).get("candle_gap_count", 0) or 0),
    )


def _bucket_row(row: BucketAttribution) -> str:
    return (
        f"| {row.bucket} | {row.completed_round_trips} | {_ratio(row.win_rate)} | "
        f"{_money(row.gross_pnl)} | {_money(row.total_cost)} | {_money(row.net_pnl)} | {_money(row.average_net_pnl)} |"
    )


def _cost_presence(record: ValidationRecord | None) -> str:
    if record is None:
        return "-"
    return f"fee={_money(record.total_fee_cost)}, spread={_money(record.total_spread_cost)}, slippage={_money(record.total_slippage_cost)}"


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
    parser = argparse.ArgumentParser(description="Run Task 284 locked Task 283 robustness validation.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report-existing", action="store_true", help="Rewrite the report from already persisted Task 284 runs without creating new runs.")
    args = parser.parse_args(argv)
    records = (
        rewrite_report_from_existing_runs(database_url=args.database_url)
        if args.report_existing
        else run_matrix(database_url=args.database_url, limit=args.limit)
    )
    persisted = len([record for record in records if record.run_id is not None])
    print(f"wrote {REPORT_PATH} with {persisted} persisted Task 284 validation runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
