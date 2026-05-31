"""Task 282 locked validation for the Task 281 selected BTCUSDT 1m model.

This module is offline-only research validation code. It reuses the Task 281
locked action generator without retuning, runs predeclared validation windows,
persists simulated backtests, and writes a markdown audit report. It does not
fetch market data, read secrets, call exchange APIs, place orders, or manage
live positions.
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

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.strategy_engine import (
    StrategyEngineConfig,
    run_strategy_backtest_engine,
)
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.backtesting.strategy_validation_metrics import trade_contribution_metrics
from quant_bitcoin.backtesting import t281_high_activity_model as t281
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    BacktestTradeReadModel,
    PostgresBacktestResultRepository,
    PostgresCandleRepository,
)
from quant_bitcoin.strategies.actions import StrategyActionType


TASK_ID = "TASK_282"
SOURCE_TASK_ID = "TASK_281"
LOCKED_SOURCE_RUN_ID = 892
LOCKED_VARIANT_ID = "T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002"
SOURCE_RUN_RETURN = 0.0572947767943437
SOURCE_RUN_TRIPS = 62

DATABASE_URL = t281.DATABASE_URL
SOURCE = t281.SOURCE
SYMBOL = t281.SYMBOL
INTERVAL = t281.INTERVAL
STARTING_CASH = t281.STARTING_CASH
REPORT_PATH = Path("reports/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md")
STRATEGY_KEY = "task282_task281_locked_oos_wfo_validation"
STRATEGY_NAME = "TASK282_TASK281_LOCKED_OOS_WFO_VALIDATION"


@dataclass(frozen=True)
class ValidationWindow:
    window_id: str
    validation_group: str
    start_time: datetime
    end_time: datetime


@dataclass(frozen=True)
class ValidationSpec:
    window: ValidationWindow
    cost_profile_key: str


@dataclass(frozen=True)
class DataAvailability:
    requested_start_time: datetime
    available_start_time: datetime | None
    available_end_time: datetime | None
    candle_count: int


@dataclass(frozen=True)
class CostAudit:
    mismatch_count: int = 0
    max_abs_mismatch: float = 0.0
    total_notional: float = 0.0
    total_fee_cost: float = 0.0
    total_spread_cost: float = 0.0
    total_slippage_cost: float = 0.0
    total_cost: float = 0.0
    effective_fee_bps: float | None = None
    effective_spread_bps: float | None = None
    effective_slippage_bps: float | None = None
    effective_total_cost_bps: float | None = None
    min_slippage_bps: float | None = None
    avg_slippage_bps: float | None = None
    max_slippage_bps: float | None = None


@dataclass(frozen=True)
class Attribution:
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_cost: float = 0.0
    completed_round_trips: int = 0
    execution_count: int = 0


@dataclass(frozen=True)
class ValidationRecord:
    window_id: str
    validation_group: str
    cost_profile: str
    requested_start_time: datetime
    requested_end_time: datetime
    run_id: int | None = None
    status: str = "SKIPPED_NO_DATA"
    skip_reason: str | None = None
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    candle_count: int = 0
    total_return: float | None = None
    final_equity: float | None = None
    trade_count: int = 0
    completed_round_trips: int = 0
    active_trade_days: int = 0
    closed_trade_net_pnl: float | None = None
    open_position_contribution: float | None = None
    max_drawdown: float | None = None
    gross_pnl: float | None = None
    net_pnl: float | None = None
    total_fee_cost: float | None = None
    total_spread_cost: float | None = None
    total_slippage_cost: float | None = None
    total_cost: float | None = None
    total_notional: float | None = None
    effective_total_cost_bps: float | None = None
    cost_to_gross_pnl_ratio: float | None = None
    largest_winner_contribution: float | None = None
    top_three_winner_contribution: float | None = None
    best_day_contribution: float | None = None
    worst_day_contribution: float | None = None
    generated_entries: int = 0
    generated_core_entries: int = 0
    generated_scout_entries: int = 0
    preempt_exits: int = 0
    core_attribution: Attribution = Attribution()
    scout_attribution: Attribution = Attribution()
    long_attribution: Attribution = Attribution()
    short_attribution: Attribution = Attribution()
    sunday_core_executions: int = 0
    cost_audit: CostAudit = CostAudit()
    candle_sorted: bool = False
    candle_continuity_ok: bool = False
    candle_gap_count: int = 0
    final_open_position: bool = False
    negative_cash_count: int = 0
    impossible_position_count: int = 0
    readback_ok: bool = False
    anomaly_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateReport:
    status: str
    gate_results: tuple[tuple[str, str, str, bool], ...]
    reasons: tuple[str, ...]


def locked_candidate() -> t281.CandidateSpec:
    """Return the exact Task 281 source-run candidate without retuning."""

    matches = [
        candidate
        for candidate in t281.build_candidates("batch1")
        if candidate.variant_id == LOCKED_VARIANT_ID
    ]
    if len(matches) != 1:
        raise RuntimeError(f"locked Task 281 candidate not found exactly once: {LOCKED_VARIANT_ID}")
    return matches[0]


def build_validation_windows(latest: datetime) -> tuple[ValidationWindow, ...]:
    latest = _as_utc(latest)
    windows = (
        ValidationWindow("full_0420_latest", "primary", _dt("2026-04-20T00:00:00Z"), latest),
        ValidationWindow("pre_owner_0420_0519", "primary", _dt("2026-04-20T00:00:00Z"), _dt("2026-05-19T23:59:00Z")),
        ValidationWindow("owner_replay_0520_latest", "primary", _dt("2026-05-20T00:00:00Z"), latest),
        ValidationWindow("w1_0420_0426", "weekly", _dt("2026-04-20T00:00:00Z"), _dt("2026-04-26T23:59:00Z")),
        ValidationWindow("w2_0427_0503", "weekly", _dt("2026-04-27T00:00:00Z"), _dt("2026-05-03T23:59:00Z")),
        ValidationWindow("w3_0504_0510", "weekly", _dt("2026-05-04T00:00:00Z"), _dt("2026-05-10T23:59:00Z")),
        ValidationWindow("w4_0511_0517", "weekly", _dt("2026-05-11T00:00:00Z"), _dt("2026-05-17T23:59:00Z")),
        ValidationWindow("w5_0518_0524", "weekly", _dt("2026-05-18T00:00:00Z"), _dt("2026-05-24T23:59:00Z")),
        ValidationWindow("w6_0525_latest", "weekly", _dt("2026-05-25T00:00:00Z"), latest),
        ValidationWindow("full_0420_latest_drop_first_day", "endpoint_trim", _dt("2026-04-21T00:00:00Z"), latest),
        ValidationWindow("full_0420_latest_drop_last_day", "endpoint_trim", _dt("2026-04-20T00:00:00Z"), latest - timedelta(days=1)),
        ValidationWindow("owner_0520_latest_drop_last_12h", "endpoint_trim", _dt("2026-05-20T00:00:00Z"), latest - timedelta(hours=12)),
        ValidationWindow("owner_0520_latest_drop_last_24h", "endpoint_trim", _dt("2026-05-20T00:00:00Z"), latest - timedelta(days=1)),
    )
    return tuple(window for window in windows if window.end_time >= window.start_time)


def build_validation_specs(latest: datetime) -> tuple[ValidationSpec, ...]:
    windows = build_validation_windows(latest)
    primary_specs = tuple(
        ValidationSpec(window=window, cost_profile_key="conservative_crypto_1m")
        for window in windows
    )
    stress_window_ids = {
        "full_0420_latest",
        "pre_owner_0420_0519",
        "owner_replay_0520_latest",
    }
    stress_specs = tuple(
        ValidationSpec(window=window, cost_profile_key="high_slippage_stress")
        for window in windows
        if window.window_id in stress_window_ids
    )
    return primary_specs + stress_specs


def run_matrix(
    *,
    database_url: str,
    limit: int | None = None,
) -> list[ValidationRecord]:
    availability = load_data_availability(database_url)
    if availability.available_end_time is None:
        records: list[ValidationRecord] = []
        write_report(records, availability=availability)
        return records

    records = []
    for sequence, spec in enumerate(build_validation_specs(availability.available_end_time), start=1):
        if limit is not None and sequence > limit:
            break
        records.append(run_one(database_url=database_url, spec=spec))
    write_report(records, availability=availability)
    return records


def run_one(*, database_url: str, spec: ValidationSpec) -> ValidationRecord:
    candidate = locked_candidate()
    candles = load_candles(database_url, spec.window)
    if candles.empty:
        return ValidationRecord(
            window_id=spec.window.window_id,
            validation_group=spec.window.validation_group,
            cost_profile=spec.cost_profile_key,
            requested_start_time=spec.window.start_time,
            requested_end_time=spec.window.end_time,
            status="SKIPPED_NO_DATA",
            skip_reason="no_local_candles_for_requested_window",
        )

    quality = candle_quality(candles)
    actual_start = pd.Timestamp(candles.iloc[0]["timestamp"]).to_pydatetime()
    actual_end = pd.Timestamp(candles.iloc[-1]["timestamp"]).to_pydatetime()
    if not bool(quality.get("candle_continuity_ok")):
        return ValidationRecord(
            window_id=spec.window.window_id,
            validation_group=spec.window.validation_group,
            cost_profile=spec.cost_profile_key,
            requested_start_time=spec.window.start_time,
            requested_end_time=spec.window.end_time,
            status="BLOCKED_CANDLE_CONTINUITY",
            skip_reason="local_candles_have_internal_1m_gap_or_duplicate",
            actual_start_time=actual_start,
            actual_end_time=actual_end,
            candle_count=len(candles),
            candle_sorted=bool(quality.get("candle_sorted")),
            candle_continuity_ok=False,
            candle_gap_count=int(quality.get("candle_gap_count") or 0),
            anomaly_reasons=("candle_continuity_gap",),
        )
    actions, action_metadata = t281.generate_actions(candles, candidate)
    cost_config = COST_PROFILES[spec.cost_profile_key].config
    config = StrategyEngineConfig(
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        transaction_cost_config=cost_config,
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
        "source_task_id": SOURCE_TASK_ID,
        "locked_source_run_id": LOCKED_SOURCE_RUN_ID,
        "locked_variant_id": LOCKED_VARIANT_ID,
        "locked_strategy_no_retune": True,
        "window_id": spec.window.window_id,
        "validation_group": spec.window.validation_group,
        "requested_start_time": _iso(spec.window.start_time),
        "requested_end_time": _iso(spec.window.end_time),
        "actual_start_time": _iso(actual_start),
        "actual_end_time": _iso(actual_end),
        "cost_profile": spec.cost_profile_key,
        "result_status": "COMPLETED_VALIDATION_RESEARCH_ONLY",
    }
    action_metadata = {
        **action_metadata,
        "task282_reuse_source_task_id": SOURCE_TASK_ID,
        "task282_locked_source_run_id": LOCKED_SOURCE_RUN_ID,
        "task282_locked_strategy_no_retune": True,
    }
    metadata["research"] = research
    metadata["task282_validation"] = {
        "schema_version": "task282_validation_metadata_v1",
        "source_task_id": SOURCE_TASK_ID,
        "locked_source_run_id": LOCKED_SOURCE_RUN_ID,
        "locked_variant_id": LOCKED_VARIANT_ID,
        "locked_strategy_no_retune": True,
        "candle_quality": quality,
    }
    metadata["task281_action_generation"] = action_metadata
    metadata["cost_profile"] = COST_PROFILES[spec.cost_profile_key].to_metadata()

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
        strategy_version=f"task282_{spec.window.window_id}_{spec.cost_profile_key}_v1",
        strategy_parameters={
            "source_task_id": SOURCE_TASK_ID,
            "locked_source_run_id": LOCKED_SOURCE_RUN_ID,
            "locked_variant_id": LOCKED_VARIANT_ID,
            "locked_strategy_no_retune": True,
            "candidate": candidate.variant_id,
            "family": candidate.family,
            "params": candidate.params,
            "validation_window": {
                "window_id": spec.window.window_id,
                "validation_group": spec.window.validation_group,
                "requested_start_time": _iso(spec.window.start_time),
                "requested_end_time": _iso(spec.window.end_time),
            },
            "cost_profile": COST_PROFILES[spec.cost_profile_key].to_metadata(),
            "cost_profile_key": spec.cost_profile_key,
            "research": research,
        },
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        engine_name="StrategyEngine",
        engine_version="strategy_engine_v1",
        run_metadata={
            "research": research,
            "cost_profile": COST_PROFILES[spec.cost_profile_key].to_metadata(),
            "task281_action_generation": action_metadata,
            "task282_validation": metadata["task282_validation"],
        },
    )
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    if persisted is None:
        raise RuntimeError(f"Task 282 persisted run could not be read back: {run_id}")
    return analyze_persisted_run(
        persisted,
        spec=spec,
        quality=quality,
        generated_entries=int(action_metadata.get("generated_entries", 0)),
        generated_core_entries=int(action_metadata.get("generated_core_entries", 0)),
        generated_scout_entries=int(action_metadata.get("generated_scout_entries", 0)),
        preempt_exits=int(action_metadata.get("preempt_exits", 0)),
    )


def load_data_availability(database_url: str) -> DataAvailability:
    import psycopg
    from psycopg.rows import dict_row

    requested_start = _dt("2026-04-20T00:00:00Z")
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        row = connection.execute(
            """
            SELECT MIN(open_time) AS min_time, MAX(open_time) AS max_time, COUNT(*) AS candle_count
            FROM candles
            WHERE source = %s AND symbol = %s AND interval = %s AND is_closed IS TRUE
              AND open_time >= %s
            """,
            (SOURCE, SYMBOL, INTERVAL, requested_start),
        ).fetchone()
    return DataAvailability(
        requested_start_time=requested_start,
        available_start_time=_as_utc(row["min_time"]) if row and row["min_time"] else None,
        available_end_time=_as_utc(row["max_time"]) if row and row["max_time"] else None,
        candle_count=int(row["candle_count"] or 0) if row else 0,
    )


def load_candles(database_url: str, window: ValidationWindow) -> pd.DataFrame:
    candles = PostgresCandleRepository(database_url).load_standard_candles(
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=window.start_time,
        end_time=window.end_time,
    )
    frame = pd.DataFrame(candles)
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame[["timestamp", "open", "high", "low", "close", "volume"]]


def candle_quality(candles: pd.DataFrame) -> dict[str, object]:
    if candles.empty:
        return {
            "candle_sorted": True,
            "candle_continuity_ok": False,
            "candle_gap_count": 0,
            "duplicate_timestamp_count": 0,
        }
    timestamps = pd.to_datetime(candles["timestamp"], utc=True)
    sorted_ok = bool(timestamps.is_monotonic_increasing)
    duplicate_count = int(timestamps.duplicated().sum())
    diffs = timestamps.sort_values().diff().dropna()
    gap_count = int((diffs != pd.Timedelta(minutes=1)).sum())
    return {
        "candle_sorted": sorted_ok,
        "candle_continuity_ok": sorted_ok and duplicate_count == 0 and gap_count == 0,
        "candle_gap_count": gap_count,
        "duplicate_timestamp_count": duplicate_count,
    }


def analyze_persisted_run(
    persisted: BacktestRunReadModel,
    *,
    spec: ValidationSpec,
    quality: dict[str, object],
    generated_entries: int,
    generated_core_entries: int,
    generated_scout_entries: int,
    preempt_exits: int,
) -> ValidationRecord:
    summary = persisted.summary
    metadata = summary.metadata or {}
    cost_summary = metadata.get("cost_summary") if isinstance(metadata.get("cost_summary"), dict) else {}
    event_net_pnls = paired_event_net_pnls(persisted.trades)
    contribution = trade_contribution_metrics(event_net_pnls)
    cost_audit = audit_persisted_trade_costs(persisted.trades)
    daily_contribution = daily_contribution_metrics(persisted.trades, contribution.net_profit)
    layer_attr = layer_attribution(persisted.trades)
    side_attr = side_attribution(persisted.trades)
    active_days = active_trade_days(persisted.trades)
    anomaly_reasons = anomaly_checks(persisted, quality=quality, cost_audit=cost_audit)
    research = (persisted.run.metadata or {}).get("research") or {}
    summary_research = (metadata.get("research") or {}) if isinstance(metadata.get("research"), dict) else {}
    readback_ok = bool(
        research.get("task_id") == TASK_ID
        and summary_research.get("task_id") == TASK_ID
        and research.get("locked_source_run_id") == LOCKED_SOURCE_RUN_ID
        and summary_research.get("locked_source_run_id") == LOCKED_SOURCE_RUN_ID
    )
    ending_position = float(summary.ending_position)
    open_position_contribution = 0.0 if ending_position == 0.0 else ending_position * float(summary.final_price or 0.0)

    return ValidationRecord(
        window_id=spec.window.window_id,
        validation_group=spec.window.validation_group,
        cost_profile=spec.cost_profile_key,
        requested_start_time=spec.window.start_time,
        requested_end_time=spec.window.end_time,
        run_id=persisted.run.id,
        status="COMPLETED_VALIDATION_RESEARCH_ONLY",
        actual_start_time=persisted.run.actual_start_time,
        actual_end_time=persisted.run.actual_end_time,
        candle_count=int(persisted.run.candle_count),
        total_return=float(summary.total_return),
        final_equity=float(summary.final_equity),
        trade_count=int(summary.trade_count),
        completed_round_trips=len(event_net_pnls),
        active_trade_days=active_days,
        closed_trade_net_pnl=float(cost_summary.get("net_pnl") or 0.0),
        open_position_contribution=open_position_contribution,
        max_drawdown=float((metadata.get("performance_metrics") or {}).get("max_drawdown") or _summary_max_drawdown(metadata) or 0.0),
        gross_pnl=_float(cost_summary.get("gross_pnl") if cost_summary else metadata.get("gross_pnl")),
        net_pnl=_float(cost_summary.get("net_pnl") if cost_summary else metadata.get("net_pnl")),
        total_fee_cost=cost_audit.total_fee_cost,
        total_spread_cost=cost_audit.total_spread_cost,
        total_slippage_cost=cost_audit.total_slippage_cost,
        total_cost=cost_audit.total_cost,
        total_notional=cost_audit.total_notional,
        effective_total_cost_bps=cost_audit.effective_total_cost_bps,
        cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
        largest_winner_contribution=contribution.largest_winner_contribution,
        top_three_winner_contribution=contribution.top_three_winner_contribution,
        best_day_contribution=daily_contribution[0],
        worst_day_contribution=daily_contribution[1],
        generated_entries=generated_entries,
        generated_core_entries=generated_core_entries,
        generated_scout_entries=generated_scout_entries,
        preempt_exits=preempt_exits,
        core_attribution=layer_attr.get("core", Attribution()),
        scout_attribution=layer_attr.get("scout", Attribution()),
        long_attribution=side_attr.get("LONG", Attribution()),
        short_attribution=side_attr.get("SHORT", Attribution()),
        sunday_core_executions=sunday_core_execution_count(persisted.trades),
        cost_audit=cost_audit,
        candle_sorted=bool(quality.get("candle_sorted")),
        candle_continuity_ok=bool(quality.get("candle_continuity_ok")),
        candle_gap_count=int(quality.get("candle_gap_count") or 0),
        final_open_position=abs(ending_position) > 1e-12,
        negative_cash_count=negative_cash_count(persisted.trades),
        impossible_position_count=impossible_position_count(persisted.trades),
        readback_ok=readback_ok,
        anomaly_reasons=anomaly_reasons,
    )


def audit_persisted_trade_costs(trades: Iterable[Any]) -> CostAudit:
    mismatch_count = 0
    max_abs_mismatch = 0.0
    total_notional = total_fee = total_spread = total_slippage = total_cost = 0.0
    slippage_values: list[float] = []
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        breakdown = metadata.get("cost_breakdown") or {}
        notional = _float(breakdown.get("gross_notional"))
        if notional is None:
            price = _float(getattr(trade, "price", None)) or 0.0
            quantity = _float(getattr(trade, "quantity", None)) or 0.0
            notional = price * quantity
        fee_bps = _float(breakdown.get("fee_bps")) or 0.0
        spread_bps = _float(breakdown.get("spread_bps")) or 0.0
        slippage_bps = _float(breakdown.get("effective_slippage_bps"))
        if slippage_bps is None:
            slippage_bps = _float(breakdown.get("slippage_bps")) or 0.0
        fee = _float(metadata.get("fee_cost")) or _float(breakdown.get("fee_cost")) or 0.0
        spread = _float(metadata.get("spread_cost")) or _float(breakdown.get("spread_cost")) or 0.0
        slippage = _float(metadata.get("slippage_cost")) or _float(breakdown.get("slippage_cost")) or 0.0
        cost = _float(metadata.get("total_cost")) or _float(breakdown.get("total_cost")) or 0.0
        expected_fee = notional * fee_bps / 10_000.0
        expected_spread = notional * spread_bps / 10_000.0
        expected_slippage = notional * slippage_bps / 10_000.0
        expected_total = expected_fee + expected_spread + expected_slippage
        diff = max(
            abs(fee - expected_fee),
            abs(spread - expected_spread),
            abs(slippage - expected_slippage),
            abs(cost - expected_total),
        )
        if diff > 1e-6:
            mismatch_count += 1
            max_abs_mismatch = max(max_abs_mismatch, diff)
        total_notional += notional
        total_fee += fee
        total_spread += spread
        total_slippage += slippage
        total_cost += cost
        slippage_values.append(slippage_bps)
    if total_notional <= 0:
        return CostAudit(mismatch_count=mismatch_count, max_abs_mismatch=max_abs_mismatch)
    return CostAudit(
        mismatch_count=mismatch_count,
        max_abs_mismatch=max_abs_mismatch,
        total_notional=total_notional,
        total_fee_cost=total_fee,
        total_spread_cost=total_spread,
        total_slippage_cost=total_slippage,
        total_cost=total_cost,
        effective_fee_bps=(total_fee / total_notional) * 10_000.0,
        effective_spread_bps=(total_spread / total_notional) * 10_000.0,
        effective_slippage_bps=(total_slippage / total_notional) * 10_000.0,
        effective_total_cost_bps=(total_cost / total_notional) * 10_000.0,
        min_slippage_bps=min(slippage_values) if slippage_values else None,
        avg_slippage_bps=sum(slippage_values) / len(slippage_values) if slippage_values else None,
        max_slippage_bps=max(slippage_values) if slippage_values else None,
    )


def paired_event_net_pnls(trades: Iterable[Any]) -> list[float]:
    events: dict[str, dict[str, float | bool]] = defaultdict(lambda: {"gross": 0.0, "cost": 0.0, "closed": False})
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        event_id = str(metadata.get("event_id") or metadata.get("pattern_event_id") or f"sequence_{getattr(trade, 'sequence', 0)}")
        events[event_id]["cost"] = float(events[event_id]["cost"]) + (_float(metadata.get("total_cost")) or 0.0)
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            events[event_id]["gross"] = float(events[event_id]["gross"]) + gross
            events[event_id]["closed"] = True
    return [
        float(values["gross"]) - float(values["cost"])
        for values in events.values()
        if bool(values["closed"])
    ]


def active_trade_days(trades: Iterable[Any]) -> int:
    days: set[str] = set()
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        if metadata.get("action_type") in {StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value}:
            if float(getattr(trade, "quantity", 0.0) or 0.0) > 0:
                days.add(str(pd.Timestamp(getattr(trade, "candle_open_time")).date()))
    return len(days)


def daily_contribution_metrics(trades: Iterable[Any], net_profit: float) -> tuple[float | None, float | None]:
    daily: dict[str, float] = defaultdict(float)
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        day = str(pd.Timestamp(getattr(trade, "candle_open_time")).date())
        gross = _float(metadata.get("gross_pnl")) or 0.0
        cost = _float(metadata.get("total_cost")) or 0.0
        daily[day] += gross - cost
    if not daily or net_profit <= 0:
        return None, None
    return max(daily.values()) / net_profit, min(daily.values()) / net_profit


def layer_attribution(trades: Iterable[Any]) -> dict[str, Attribution]:
    rows: dict[str, dict[str, float]] = defaultdict(lambda: {"gross": 0.0, "cost": 0.0, "trips": 0.0, "execs": 0.0})
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        layer = str(metadata.get("task281_layer") or "unknown")
        rows[layer]["execs"] += 1.0
        rows[layer]["cost"] += _float(metadata.get("total_cost")) or 0.0
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            rows[layer]["gross"] += gross
            rows[layer]["trips"] += 1.0
    return {
        key: Attribution(
            gross_pnl=row["gross"],
            total_cost=row["cost"],
            net_pnl=row["gross"] - row["cost"],
            completed_round_trips=int(row["trips"]),
            execution_count=int(row["execs"]),
        )
        for key, row in rows.items()
    }


def side_attribution(trades: Iterable[Any]) -> dict[str, Attribution]:
    rows: dict[str, dict[str, float]] = defaultdict(lambda: {"gross": 0.0, "cost": 0.0, "trips": 0.0, "execs": 0.0})
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        side = str(metadata.get("position_side") or "unknown")
        rows[side]["execs"] += 1.0
        rows[side]["cost"] += _float(metadata.get("total_cost")) or 0.0
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            rows[side]["gross"] += gross
            rows[side]["trips"] += 1.0
    return {
        key: Attribution(
            gross_pnl=row["gross"],
            total_cost=row["cost"],
            net_pnl=row["gross"] - row["cost"],
            completed_round_trips=int(row["trips"]),
            execution_count=int(row["execs"]),
        )
        for key, row in rows.items()
    }


def sunday_core_execution_count(trades: Iterable[Any]) -> int:
    count = 0
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        if metadata.get("task281_layer") != "core":
            continue
        timestamp = pd.Timestamp(getattr(trade, "candle_open_time"))
        if timestamp.weekday() == 6 and 12 <= timestamp.hour <= 18:
            count += 1
    return count


def negative_cash_count(trades: Iterable[Any]) -> int:
    count = 0
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        values = [
            _float(getattr(trade, "cash_after", None)),
            _float(metadata.get("free_cash_after")),
            _float(metadata.get("available_buying_power_after")),
        ]
        if any(value is not None and value < -1e-6 for value in values):
            count += 1
    return count


def impossible_position_count(trades: Iterable[Any]) -> int:
    count = 0
    for trade in trades:
        position = _float(getattr(trade, "position_after", None))
        quantity = _float(getattr(trade, "quantity", None))
        price = _float(getattr(trade, "price", None))
        if any(value is None or not math.isfinite(value) for value in (position, quantity, price)):
            count += 1
    return count


def anomaly_checks(
    persisted: BacktestRunReadModel,
    *,
    quality: dict[str, object],
    cost_audit: CostAudit,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if cost_audit.mismatch_count:
        reasons.append("cost_formula_mismatch")
    if not bool(quality.get("candle_sorted")):
        reasons.append("candle_timestamps_not_sorted")
    if not bool(quality.get("candle_continuity_ok")):
        reasons.append("candle_continuity_gap")
    if negative_cash_count(persisted.trades):
        reasons.append("negative_cash_or_buying_power")
    if impossible_position_count(persisted.trades):
        reasons.append("impossible_position_or_price")
    if abs(float(persisted.summary.ending_position)) > 1e-12:
        reasons.append("final_open_position")
    return tuple(reasons)


def classify_validation(records: Sequence[ValidationRecord], availability: DataAvailability) -> GateReport:
    completed = [
        record
        for record in records
        if record.status == "COMPLETED_VALIDATION_RESEARCH_ONLY"
    ]
    conservative = [record for record in completed if record.cost_profile == "conservative_crypto_1m"]
    stress = [record for record in completed if record.cost_profile == "high_slippage_stress"]
    by_window = {record.window_id: record for record in conservative}
    stress_by_window = {record.window_id: record for record in stress}
    full = by_window.get("full_0420_latest")
    pre_owner = by_window.get("pre_owner_0420_0519")
    owner = by_window.get("owner_replay_0520_latest")
    weekly = [record for record in conservative if record.validation_group == "weekly" and record.completed_round_trips >= 10]
    weekly_positive = [record for record in weekly if (record.total_return or 0.0) > 0.0]
    anomaly_records = [record for record in conservative if record.anomaly_reasons or not record.readback_ok]

    owner_replay_ok = bool(
        owner
        and owner.total_return is not None
        and abs(owner.total_return - SOURCE_RUN_RETURN) <= 1e-10
        and owner.completed_round_trips == SOURCE_RUN_TRIPS
    )
    full_positive = bool(full and (full.total_return or 0.0) > 0.0)
    pre_positive = bool(pre_owner and (pre_owner.total_return or 0.0) > 0.0)
    weekly_ok = bool(weekly and len(weekly_positive) >= math.ceil(len(weekly) / 2))
    full_largest_ok = bool(full and full.largest_winner_contribution is not None and full.largest_winner_contribution <= 0.40)
    full_top3_ok = bool(full and full.top_three_winner_contribution is not None and full.top_three_winner_contribution <= 0.70)
    full_cost_ok = bool(full and full.cost_to_gross_pnl_ratio is not None and full.cost_to_gross_pnl_ratio <= 0.60)
    full_stress = stress_by_window.get("full_0420_latest")
    pre_stress = stress_by_window.get("pre_owner_0420_0519")
    full_stress_ok = bool(full_stress and (full_stress.total_return or 0.0) > -0.03)
    pre_stress_ok = bool(pre_stress and (pre_stress.total_return or 0.0) > -0.03)
    no_anomaly = not anomaly_records
    has_pre_owner_data = bool(
        availability.available_start_time
        and availability.available_start_time < _dt("2026-05-20T00:00:00Z")
    )

    gate_rows = (
        ("Data before owner window", "available_start < 2026-05-20", _iso(availability.available_start_time) if availability.available_start_time else "-", has_pre_owner_data),
        ("Owner replay reproducibility", "return/trips match run 892", _record_value(owner), owner_replay_ok),
        ("Full 0420-latest return", "> 0", _pct(full.total_return) if full else "-", full_positive),
        ("Pre-owner return", "> 0", _pct(pre_owner.total_return) if pre_owner else "-", pre_positive),
        ("Weekly consistency", ">= half positive among >=10-trip weeks", f"{len(weekly_positive)}/{len(weekly)}", weekly_ok),
        ("Full largest winner contribution", "<= 0.40", _ratio(full.largest_winner_contribution) if full else "-", full_largest_ok),
        ("Full top-three winner contribution", "<= 0.70", _ratio(full.top_three_winner_contribution) if full else "-", full_top3_ok),
        ("Full cost/gross PnL", "<= 0.60", _ratio(full.cost_to_gross_pnl_ratio) if full else "-", full_cost_ok),
        ("Full high-slippage stress", "> -3pct", _pct(stress_by_window["full_0420_latest"].total_return) if "full_0420_latest" in stress_by_window else "-", full_stress_ok),
        ("Pre-owner high-slippage stress", "> -3pct", _pct(stress_by_window["pre_owner_0420_0519"].total_return) if "pre_owner_0420_0519" in stress_by_window else "-", pre_stress_ok),
        ("Accounting/anomaly checks", "no anomalies", ",".join(record.window_id for record in anomaly_records) or "-", no_anomaly),
    )
    failed = [name for name, _, _, ok in gate_rows if not ok]
    if not has_pre_owner_data or pre_owner is None or owner is None:
        status = "DATA_BLOCKED_RESEARCH_ONLY"
    elif not no_anomaly:
        status = "INVALID_DUE_TO_COST_OR_ACCOUNTING_ANOMALY"
    elif not failed:
        status = "OOS_SUPPORTED_RESEARCH_ONLY"
    elif not pre_positive or not weekly_ok:
        status = "LIKELY_OVERFIT_RESEARCH_ONLY"
    elif full is None:
        status = "DATA_BLOCKED_RESEARCH_ONLY"
    else:
        status = "UNSTABLE_RESEARCH_ONLY"
    return GateReport(status=status, gate_results=gate_rows, reasons=tuple(failed))


def write_report(records: Sequence[ValidationRecord], *, availability: DataAvailability) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gate_report = classify_validation(records, availability)
    completed = [record for record in records if record.run_id is not None]
    run_ids = ", ".join(str(record.run_id) for record in completed) if completed else "-"
    lines = [
        "# Task 282 Task 281 Locked OOS/WFO Validation From 2026-04-20",
        "",
        f"Status: `{gate_report.status}`",
        "",
        "## Locked Strategy",
        "",
        f"- Source task: `{SOURCE_TASK_ID}`.",
        f"- Source run: `{LOCKED_SOURCE_RUN_ID}`.",
        f"- Locked variant: `{LOCKED_VARIANT_ID}`.",
        "- No-retune declaration: `True`.",
        "- Validation scope: offline simulated BTCUSDT 1m only; no live/order/private exchange endpoints.",
        "",
        "## Data Availability",
        "",
        f"- Requested validation start: `{_iso(availability.requested_start_time)}`.",
        f"- Local available start: `{_iso(availability.available_start_time) if availability.available_start_time else '-'}`.",
        f"- Local available end: `{_iso(availability.available_end_time) if availability.available_end_time else '-'}`.",
        f"- Local closed candles from requested start onward: `{availability.candle_count}`.",
        "- Data note: April 20-2026 through local available start is not fabricated; windows report actual persisted candle starts.",
        "",
        "## Run IDs",
        "",
        f"- Task 282 persisted run IDs: `{run_ids}`.",
        "",
        "## Validation Runs",
        "",
        "| Window | Group | Cost | Run | Requested | Actual | Return | Trips | Active Days | Gross | Net | Cost | Cost/Gross | Top1 | Top3 | Max DD | Notional | Cost bps | Status | Anomalies |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.window_id,
                    record.validation_group,
                    record.cost_profile,
                    str(record.run_id) if record.run_id is not None else "-",
                    f"{_date(record.requested_start_time)}..{_date(record.requested_end_time)}",
                    f"{_date(record.actual_start_time)}..{_date(record.actual_end_time)}" if record.actual_start_time else "-",
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    str(record.active_trade_days),
                    _money(record.gross_pnl),
                    _money(record.net_pnl),
                    _money(record.total_cost),
                    _ratio(record.cost_to_gross_pnl_ratio),
                    _ratio(record.largest_winner_contribution),
                    _ratio(record.top_three_winner_contribution),
                    _pct(record.max_drawdown),
                    _money(record.total_notional),
                    _ratio(record.effective_total_cost_bps),
                    record.status if record.run_id is not None else str(record.skip_reason),
                    ",".join(record.anomaly_reasons) or "-",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Gate Check",
            "",
            "| Gate | Required | Observed | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for name, required, observed, ok in gate_report.gate_results:
        lines.append(f"| {name} | {required} | {observed} | `{'PASS' if ok else 'FAIL'}` |")
    lines.extend(["", "## Cost Audit", ""])
    for record in completed:
        audit = record.cost_audit
        lines.extend(
            [
                f"- Run `{record.run_id}` `{record.window_id}` `{record.cost_profile}`: notional `{_money(audit.total_notional)}`, fee `{_money(audit.total_fee_cost)}`, spread `{_money(audit.total_spread_cost)}`, slippage `{_money(audit.total_slippage_cost)}`, total `{_money(audit.total_cost)}`, one-way cost `{_ratio(audit.effective_total_cost_bps)}` bps, mismatch count `{audit.mismatch_count}`, max mismatch `{audit.max_abs_mismatch:.10f}`.",
            ]
        )
    lines.extend(["", "## Attribution Checks", ""])
    for record in completed:
        lines.append(
            f"- Run `{record.run_id}` `{record.window_id}`: core net `{_money(record.core_attribution.net_pnl)}` over `{record.core_attribution.completed_round_trips}` trips, scout net `{_money(record.scout_attribution.net_pnl)}` over `{record.scout_attribution.completed_round_trips}` trips, LONG net `{_money(record.long_attribution.net_pnl)}`, SHORT net `{_money(record.short_attribution.net_pnl)}`, Sunday core executions `{record.sunday_core_executions}`."
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Final interpretation: `{gate_report.status}`.",
            f"- Failed gates: `{', '.join(gate_report.reasons) if gate_report.reasons else '-'}`.",
            "- The validation does not retune the model and does not promote the strategy beyond research-only.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def _summary_max_drawdown(metadata: dict[str, Any]) -> float | None:
    diagnostics = metadata.get("performance_diagnostics")
    if isinstance(diagnostics, dict):
        return _float(diagnostics.get("max_drawdown"))
    return None


def _record_value(record: ValidationRecord | None) -> str:
    if record is None:
        return "-"
    return f"{_pct(record.total_return)} / {record.completed_round_trips}"


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str:
    if value is None:
        return "-"
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _date(value: datetime | None) -> str:
    if value is None:
        return "-"
    return _iso(value)[:10]


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
    parser = argparse.ArgumentParser(description="Run Task 282 locked OOS/WFO validation for Task 281 run 892.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    records = run_matrix(database_url=args.database_url, limit=args.limit)
    persisted = len([record for record in records if record.run_id is not None])
    print(f"wrote {REPORT_PATH} with {persisted} persisted Task 282 validation runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
