"""Task 281 high-activity BTCUSDT 1m research runner.

This module is offline-only research code. It consumes local candles, emits
deterministic completed-candle actions, runs the existing strategy engine, and
persists simulated backtests. It does not fetch market data, read secrets, call
exchange APIs, place orders, or manage live positions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Sequence

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
from quant_bitcoin.backtesting.strategy_validation_metrics import (
    trade_contribution_metrics,
)
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.persistence.postgres import (
    PostgresBacktestResultRepository,
    PostgresCandleRepository,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


TASK_ID = "TASK_281"
DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
REPORT_PATH = Path("reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md")
SOURCE = "binance_spot"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
STARTING_CASH = 1_000_000.0
STRATEGY_KEY = "task281_owner_window_high_activity"
STRATEGY_NAME = "TASK281_OWNER_WINDOW_HIGH_ACTIVITY_TARGET_RETURN_SEARCH"


@dataclass(frozen=True)
class CandidateSpec:
    variant_id: str
    family: str
    description: str
    params: dict[str, Any]


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    start_time: str
    end_time: str
    run_group: str


@dataclass(frozen=True)
class RunRecord:
    variant_id: str
    family: str
    window_id: str
    run_group: str
    cost_profile: str
    run_id: int
    total_return: float
    final_equity: float
    trade_count: int
    completed_round_trips: int
    active_trade_days: int
    gross_pnl: float | None
    net_pnl: float | None
    closed_trade_net_pnl: float
    open_position_contribution: float
    total_fee_cost: float | None
    total_spread_cost: float | None
    total_slippage_cost: float | None
    total_cost: float | None
    cost_to_gross_pnl_ratio: float | None
    largest_winner_contribution: float | None
    top_three_winner_contribution: float | None
    max_drawdown: float
    generated_entries: int
    generated_core_entries: int
    generated_scout_entries: int
    preempt_exits: int
    cost_verified: bool
    persisted_readback_ok: bool
    result_status: str
    pass_fail_reason: str


def build_windows() -> tuple[WindowSpec, ...]:
    return (
        WindowSpec(
            window_id="owner_0520",
            start_time="2026-05-20T00:00:00Z",
            end_time="2026-05-30T00:00:00Z",
            run_group="owner",
        ),
    )


def build_candidates(batch: str = "batch1") -> tuple[CandidateSpec, ...]:
    """Return the bounded Task 281 candidate grid.

    The grid intentionally includes failed scouts and core-only diagnostics
    before the priority ensemble so the report records the activity/edge
    tradeoff that drove the final candidate choice.
    """

    if batch != "batch1":
        raise ValueError("supported Task 281 batches: batch1")
    return (
        CandidateSpec(
            variant_id="T281_B1_ACTIVITY_SCOUT_H120_T150_S75_FF002",
            family="ACTIVITY_TREND_SCOUT",
            description="High-activity trend/momentum scout sleeve without the range-fade core.",
            params={
                "core_enabled": False,
                "scout_enabled": True,
                "scout_fraction": 0.02,
                "scout_hold_bars": 120,
                "scout_target_bps": 150.0,
                "scout_stop_bps": 75.0,
                "preempt_scout_on_core": False,
            },
        ),
        CandidateSpec(
            variant_id="T281_B1_FILTERED_CORE_RANGE_FADE_CF100",
            family="LIQUIDITY_RANGE_FADE_CORE",
            description="Filtered bearish failed-range-break core only; high edge but too few trades.",
            params={
                "core_enabled": True,
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_incomplete_hold": True,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_enabled": False,
            },
        ),
        CandidateSpec(
            variant_id="T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002",
            family="PRIORITY_CORE_ACTIVITY_SCOUT",
            description="Filtered range-fade short core plus low-notional activity scout; scout exits when core appears.",
            params={
                "core_enabled": True,
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_incomplete_hold": True,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_enabled": True,
                "scout_fraction": 0.02,
                "scout_hold_bars": 120,
                "scout_target_bps": 150.0,
                "scout_stop_bps": 75.0,
                "preempt_scout_on_core": True,
                "same_candle_core_after_preempt": True,
            },
        ),
        CandidateSpec(
            variant_id="T281_B1_PRIORITY_ENSEMBLE_H90_T90_S50_CF100_FF002",
            family="PRIORITY_CORE_ACTIVITY_SCOUT",
            description="Same core with shorter 90-bar scout recycle geometry.",
            params={
                "core_enabled": True,
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_incomplete_hold": True,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_enabled": True,
                "scout_fraction": 0.02,
                "scout_hold_bars": 90,
                "scout_target_bps": 90.0,
                "scout_stop_bps": 50.0,
                "preempt_scout_on_core": True,
                "same_candle_core_after_preempt": True,
            },
        ),
        CandidateSpec(
            variant_id="T281_B1_PRIORITY_ENSEMBLE_H60_T70_S40_CF100_FF002",
            family="PRIORITY_CORE_ACTIVITY_SCOUT",
            description="Same core with faster 60-bar scout recycle geometry.",
            params={
                "core_enabled": True,
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_incomplete_hold": True,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_enabled": True,
                "scout_fraction": 0.02,
                "scout_hold_bars": 60,
                "scout_target_bps": 70.0,
                "scout_stop_bps": 40.0,
                "preempt_scout_on_core": True,
                "same_candle_core_after_preempt": True,
            },
        ),
    )


def generate_actions(candles: pd.DataFrame, candidate: CandidateSpec) -> tuple[list[StrategyAction], dict[str, Any]]:
    frame = _enrich(candles)
    params = candidate.params
    core_signals = _core_signal_by_index(frame, params) if params.get("core_enabled", False) else {}
    scout_signals = _scout_signal_by_index(frame) if params.get("scout_enabled", False) else {}
    warmup = int(params.get("warmup_bars", 960))
    actions: list[StrategyAction] = []
    index = warmup
    generated_core = 0
    generated_scout = 0
    preempt_exits = 0
    exit_reasons: dict[str, int] = {}

    while index < len(frame) - 2:
        if index in core_signals:
            side = core_signals[index]
            fraction = float(params.get("core_fraction", 1.0))
            target_bps = float(params.get("core_target_bps", 260.0))
            stop_bps = float(params.get("core_stop_bps", 130.0))
            hold_bars = int(params.get("core_hold_bars", 480))
            layer = "core"
        elif index in scout_signals:
            side = scout_signals[index]
            fraction = float(params.get("scout_fraction", 0.02))
            target_bps = float(params.get("scout_target_bps", 150.0))
            stop_bps = float(params.get("scout_stop_bps", 75.0))
            hold_bars = int(params.get("scout_hold_bars", 120))
            layer = "scout"
        else:
            index += 1
            continue

        exit_index, exit_price, exit_reason = _resolve_exit(
            frame,
            index,
            side,
            target_bps,
            stop_bps,
            hold_bars,
            core_signals=core_signals,
            preempt_on_core=bool(params.get("preempt_scout_on_core", False) and layer == "scout"),
        )
        if exit_reason == "T281_SCOUT_PREEMPT_CORE_SIGNAL":
            preempt_exits += 1
        exit_reasons[exit_reason] = exit_reasons.get(exit_reason, 0) + 1
        event_id = f"{candidate.variant_id}_{layer}_{index}"
        actions.extend(
            _entry_exit_actions(
                frame,
                entry_index=index,
                exit_index=exit_index,
                side=side,
                position_fraction=fraction,
                event_id=event_id,
                candidate=candidate,
                layer=layer,
                target_bps=target_bps,
                stop_bps=stop_bps,
                hold_bars=hold_bars,
                exit_price=exit_price,
                exit_reason=exit_reason,
            )
        )
        if layer == "core":
            generated_core += 1
        else:
            generated_scout += 1
        if exit_reason == "T281_SCOUT_PREEMPT_CORE_SIGNAL" and params.get("same_candle_core_after_preempt", False):
            index = exit_index
        else:
            index = max(exit_index + 1, index + 1)

    return actions, {
        "schema_version": "task281_action_generation_v1",
        "task_id": TASK_ID,
        "variant_id": candidate.variant_id,
        "family": candidate.family,
        "completed_candle_only": True,
        "no_lookahead_entry_signals": True,
        "scout_preempt_is_current_candle_exit_rule": True,
        "generated_entries": generated_core + generated_scout,
        "generated_core_entries": generated_core,
        "generated_scout_entries": generated_scout,
        "preempt_exits": preempt_exits,
        "exit_reasons": exit_reasons,
        "core_signal_count": len(core_signals),
        "scout_signal_count": len(scout_signals),
    }


def run_matrix(
    *,
    database_url: str,
    batch: str = "batch1",
    limit: int | None = None,
) -> list[RunRecord]:
    candidates = build_candidates(batch)
    windows = build_windows()
    records: list[RunRecord] = []
    planned = 0
    cost_profile_key = "conservative_crypto_1m"
    cost_config = COST_PROFILES[cost_profile_key].config
    for candidate in candidates:
        for window in windows:
            planned += 1
            if limit is not None and planned > limit:
                write_report(records, planned_candidates=len(candidates), batch=batch)
                return records
            records.append(
                run_one(
                    database_url=database_url,
                    candidate=candidate,
                    window=window,
                    cost_profile_key=cost_profile_key,
                    cost_config=cost_config,
                    run_group=window.run_group,
                )
            )
    write_report(records, planned_candidates=len(candidates), batch=batch)
    return records


def run_one(
    *,
    database_url: str,
    candidate: CandidateSpec,
    window: WindowSpec,
    cost_profile_key: str,
    cost_config: TransactionCostConfig,
    run_group: str,
) -> RunRecord:
    candles = _load_candles(database_url, window)
    actions, action_metadata = generate_actions(candles, candidate)
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
    closing_net = _closing_net_pnls(result)
    contribution = trade_contribution_metrics(closing_net)
    cost_summary = metadata.get("cost_summary") if isinstance(metadata.get("cost_summary"), dict) else {}
    active_days = _active_trade_days(result)
    gross_pnl = _summary_float(metadata, "gross_pnl")
    net_pnl = _summary_float(metadata, "net_pnl")
    closed_trade_net = float(net_pnl or 0.0)
    ending_position = float(result.summary.ending_position)
    open_position_contribution = 0.0 if ending_position == 0.0 else float(ending_position * result.summary.final_price)
    total_cost = _dict_float(cost_summary, "total_cost")
    total_fee_cost = _dict_float(cost_summary, "total_fee_cost")
    total_spread_cost = _dict_float(cost_summary, "total_spread_cost")
    total_slippage_cost = _dict_float(cost_summary, "total_slippage_cost")
    cost_ratio = _dict_float(cost_summary, "cost_to_gross_pnl_ratio")
    cost_verified = all(
        value is not None and value > 0.0
        for value in (total_fee_cost, total_spread_cost, total_slippage_cost, total_cost)
    )
    status, reason = _gate_status(
        total_return=float(result.summary.total_return),
        completed_round_trips=len(closing_net),
        active_days=active_days,
        cost_to_gross_pnl_ratio=cost_ratio,
        largest_winner_contribution=contribution.largest_winner_contribution,
        top_three_winner_contribution=contribution.top_three_winner_contribution,
        trade_count=int(result.summary.trade_count),
    )
    research = {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "scope": "offline_backtest_research_only",
        "task_id": TASK_ID,
        "variant_id": candidate.variant_id,
        "window_id": window.window_id,
        "run_group": run_group,
        "batch": _candidate_batch(candidate),
        "result_status": status,
        "pass_fail_reason": reason,
    }
    metadata["research"] = research
    metadata["task281_action_generation"] = action_metadata
    metadata["cost_profile"] = COST_PROFILES[cost_profile_key].to_metadata()
    metadata["task281_gate_status"] = {
        "schema_version": "task281_gate_status_v1",
        "status": status,
        "pass_fail_reason": reason,
        "return_gate_min": 0.03,
        "round_trip_gate_min": 50,
        "active_trade_days_min": 5,
        "cost_to_gross_pnl_max": 0.60,
        "largest_winner_contribution_max": 0.40,
        "top_three_winner_contribution_max": 0.70,
    }
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=_dt(window.start_time),
        end_time=_dt(window.end_time),
        strategy_key=STRATEGY_KEY,
        strategy_name=STRATEGY_NAME,
        strategy_version=f"task281_{_candidate_batch(candidate)}_v1",
        strategy_parameters={
            "candidate": candidate.variant_id,
            "family": candidate.family,
            "params": candidate.params,
            "cost_profile": COST_PROFILES[cost_profile_key].to_metadata(),
            "cost_profile_key": cost_profile_key,
            "research": research,
        },
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        engine_name="StrategyEngine",
        engine_version="strategy_engine_v1",
        run_metadata={
            "research": research,
            "cost_profile": COST_PROFILES[cost_profile_key].to_metadata(),
            "task281_action_generation": action_metadata,
        },
    )
    repository = PostgresBacktestResultRepository(database_url)
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    persisted_readback_ok = bool(
        persisted
        and persisted.run.metadata
        and ((persisted.run.metadata.get("research") or {}).get("task_id") == TASK_ID)
        and persisted.summary.metadata
        and ((persisted.summary.metadata.get("research") or {}).get("task_id") == TASK_ID)
    )
    return RunRecord(
        variant_id=candidate.variant_id,
        family=candidate.family,
        window_id=window.window_id,
        run_group=run_group,
        cost_profile=cost_profile_key,
        run_id=run_id,
        total_return=float(result.summary.total_return),
        final_equity=float(result.summary.final_equity),
        trade_count=int(result.summary.trade_count),
        completed_round_trips=len(closing_net),
        active_trade_days=active_days,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        closed_trade_net_pnl=closed_trade_net,
        open_position_contribution=open_position_contribution,
        total_fee_cost=total_fee_cost,
        total_spread_cost=total_spread_cost,
        total_slippage_cost=total_slippage_cost,
        total_cost=total_cost,
        cost_to_gross_pnl_ratio=cost_ratio,
        largest_winner_contribution=contribution.largest_winner_contribution,
        top_three_winner_contribution=contribution.top_three_winner_contribution,
        max_drawdown=float(result.summary.max_drawdown),
        generated_entries=int(action_metadata.get("generated_entries", 0)),
        generated_core_entries=int(action_metadata.get("generated_core_entries", 0)),
        generated_scout_entries=int(action_metadata.get("generated_scout_entries", 0)),
        preempt_exits=int(action_metadata.get("preempt_exits", 0)),
        cost_verified=cost_verified,
        persisted_readback_ok=persisted_readback_ok,
        result_status=status,
        pass_fail_reason=reason,
    )


def write_report(records: Sequence[RunRecord], *, planned_candidates: int, batch: str) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    passed = [record for record in records if record.result_status == "PROMISING_RESEARCH_ONLY"]
    best_pool = passed if passed else list(records)
    best = max(best_pool, key=lambda item: item.total_return, default=None)
    run_ids = ", ".join(str(record.run_id) for record in records) if records else "-"
    actual_end = "-"
    if records:
        actual_end = "see DB actual_end_time per run; local candle load ended at 2026-05-28T08:26:00Z in this dataset"
    lines = [
        "# Task 281 Owner Window 0520 High-Activity Target Return Search",
        "",
        f"Status: `{'PROMISING_RESEARCH_ONLY' if passed else 'IN_PROGRESS_RESEARCH_ONLY'}`",
        "",
        "## Iteration State",
        "",
        f"- Batch: `{batch}`",
        f"- Planned candidates in batch: `{planned_candidates}`",
        f"- Persisted runs in this invocation: `{len(records)}`",
        f"- Task 281 run IDs: `{run_ids}`",
        "- Primary window: `2026-05-20T00:00:00Z` through latest locally available BTCUSDT 1m candle.",
        f"- Actual local end note: {actual_end}.",
        "- Loop policy: continue inside Task 281 if primary gates fail; this batch found a passing research-only candidate." if passed else "- Loop policy: continue inside Task 281 because no candidate passed yet.",
        "",
        "## Strategy Thesis",
        "",
        "- Core sleeve: bearish failed range-break/fade after medium-term downside pressure. It enters SHORT only from completed candles when the current candle sweeps above the prior 60-bar high but closes back below it, while 240-minute return is negative and the entry has enough remaining candles for the 480-bar hold geometry.",
        "- Safety/consistency filters: skip the incomplete endpoint and skip Sunday 12:00-18:00 UTC core entries, which were isolated as a poor-liquidity reversal pocket in this fixed research window.",
        "- Activity scout sleeve: low-notional deterministic trend/momentum scout using prior 60-minute, prior 720-minute, and prior 15-minute returns. It recycles capital with fixed target/stop/time exits and exits immediately when a core signal appears so the core can enter on the same completed candle.",
        "- Sizing: core uses fixed notional equal to configured cash fraction of starting quote cash; scout uses a small fixed notional fraction. No leverage, futures, borrow, funding, liquidation, live orders, or exchange private endpoints are used.",
        "",
        "## Candidate Runs",
        "",
        "| Variant | Family | Run | Return | Trips | Active Days | Core | Scout | Preempt | Gross | Cost | Cost/Gross | Top1 | Top3 | Max DD | Status | Reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.variant_id,
                    record.family,
                    str(record.run_id),
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    str(record.active_trade_days),
                    str(record.generated_core_entries),
                    str(record.generated_scout_entries),
                    str(record.preempt_exits),
                    _money(record.gross_pnl),
                    _money(record.total_cost),
                    _ratio(record.cost_to_gross_pnl_ratio),
                    _ratio(record.largest_winner_contribution),
                    _ratio(record.top_three_winner_contribution),
                    _pct(record.max_drawdown),
                    record.result_status,
                    record.pass_fail_reason,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Best Candidate", ""])
    if best is None:
        lines.append("- No Task 281 runs were persisted.")
    else:
        lines.extend(
            [
                f"- Best run: `{best.run_id}` `{best.variant_id}`.",
                f"- Net total return: `{_pct(best.total_return)}`.",
                f"- Completed round trips: `{best.completed_round_trips}`.",
                f"- Active trade days: `{best.active_trade_days}`.",
                f"- Final equity: `{_money(best.final_equity)}`.",
                f"- Closed-trade net PnL: `{_money(best.closed_trade_net_pnl)}`.",
                f"- Open-position contribution at final equity: `{_money(best.open_position_contribution)}`.",
                f"- Result status: `{best.result_status}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Gate Check",
            "",
            "| Gate | Required | Best | Status |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    if best is not None:
        gate_rows = [
            ("Total return", ">= +3.0000pct", _pct(best.total_return), best.total_return >= 0.03),
            ("Completed round trips", ">= 50", str(best.completed_round_trips), best.completed_round_trips >= 50),
            ("Active trade days", ">= 5", str(best.active_trade_days), best.active_trade_days >= 5),
            ("Cost/gross PnL", "<= 0.60", _ratio(best.cost_to_gross_pnl_ratio), (best.cost_to_gross_pnl_ratio or 99.0) <= 0.60),
            ("Largest winner/net", "<= 0.40", _ratio(best.largest_winner_contribution), (best.largest_winner_contribution or 99.0) <= 0.40),
            ("Top three winners/net", "<= 0.70", _ratio(best.top_three_winner_contribution), (best.top_three_winner_contribution or 99.0) <= 0.70),
            ("Cost readback", "fee/spread/slippage > 0", str(best.cost_verified and best.persisted_readback_ok), best.cost_verified and best.persisted_readback_ok),
        ]
        for name, required, value, ok in gate_rows:
            lines.append(f"| {name} | {required} | {value} | `{'PASS' if ok else 'FAIL'}` |")
    lines.extend(["", "## Cost Accounting", ""])
    if best is not None:
        lines.extend(
            [
                f"- Cost profile: `{best.cost_profile}`.",
                f"- Fee cost: `{_money(best.total_fee_cost)}`.",
                f"- Spread cost: `{_money(best.total_spread_cost)}`.",
                f"- Slippage cost: `{_money(best.total_slippage_cost)}`.",
                f"- Total cost: `{_money(best.total_cost)}`.",
                f"- Cost verification: `{'PASS' if best.cost_verified else 'FAIL'}`.",
                f"- DB readback verification: `{'PASS' if best.persisted_readback_ok else 'FAIL'}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Research Risk",
            "",
            "- This is `RESEARCH_ONLY` and fixed-window tuned. The Sunday/session filter and scout geometry were selected after inspecting the 2026-05-20+ owner window, so the result is data-snooping-prone until a future locked OOS/walk-forward task validates it unchanged.",
            "- The strategy remains offline-only and does not imply live readiness.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def _core_signal_by_index(frame: pd.DataFrame, params: dict[str, Any]) -> dict[int, str]:
    signals: dict[int, str] = {}
    skip_hours = set(int(value) for value in params.get("core_skip_sunday_hours_utc", []))
    hold_bars = int(params.get("core_hold_bars", 480))
    for index in range(960, len(frame) - 2):
        if params.get("core_skip_incomplete_hold", True) and index > len(frame) - 1 - hold_bars:
            continue
        timestamp = pd.Timestamp(frame.iloc[index]["timestamp"])
        if timestamp.weekday() == 6 and timestamp.hour in skip_hours:
            continue
        row = frame.iloc[index]
        prior_high = _positive(row.get("range_high_prior_60"))
        ret_60 = _number(row.get("return_bps_prior_60"))
        ret_240 = _number(row.get("return_bps_prior_240"))
        if prior_high is None or ret_60 is None or ret_240 is None:
            continue
        ret_60_vote = -1 if ret_60 < -80.0 else (1 if ret_60 > 80.0 else 0)
        ret_240_vote = -1 if ret_240 < -20.0 else (1 if ret_240 > 20.0 else 0)
        fade_vote = -1 if float(row["high"]) > prior_high and float(row["close"]) < prior_high else 0
        if ret_60_vote + ret_240_vote + fade_vote <= -2:
            signals[index] = "SHORT"
    return signals


def _scout_signal_by_index(frame: pd.DataFrame) -> dict[int, str]:
    signals: dict[int, str] = {}
    for index in range(960, len(frame) - 2):
        row = frame.iloc[index]
        ret_60 = _number(row.get("return_bps_prior_60"))
        ret_720 = _number(row.get("return_bps_prior_720"))
        ret_15 = _number(row.get("return_bps_prior_15"))
        if ret_60 is None or ret_720 is None or ret_15 is None:
            continue
        score = _directional_vote(ret_60, 0.0) + _directional_vote(ret_720, 20.0) + _directional_vote(ret_15, 10.0)
        if score >= 2:
            signals[index] = "LONG"
        elif score <= -2:
            signals[index] = "SHORT"
    return signals


def _resolve_exit(
    frame: pd.DataFrame,
    entry_index: int,
    side: str,
    target_bps: float,
    stop_bps: float,
    hold_bars: int,
    *,
    core_signals: dict[int, str],
    preempt_on_core: bool,
) -> tuple[int, float, str]:
    entry = float(frame.iloc[entry_index]["close"])
    if side == "LONG":
        target = entry * (1.0 + (target_bps / 10_000.0))
        stop = entry * (1.0 - (stop_bps / 10_000.0))
    else:
        target = entry * (1.0 - (target_bps / 10_000.0))
        stop = entry * (1.0 + (stop_bps / 10_000.0))
    end = min(len(frame) - 1, entry_index + int(hold_bars))
    for index in range(entry_index + 1, end + 1):
        if preempt_on_core and index in core_signals:
            return index, float(frame.iloc[index]["close"]), "T281_SCOUT_PREEMPT_CORE_SIGNAL"
        row = frame.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        if side == "LONG":
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            stop_hit = high >= stop
            target_hit = low <= target
        if stop_hit and target_hit:
            return index, stop, "T281_CONSERVATIVE_STOP_FIRST"
        if stop_hit:
            return index, stop, "T281_STOP"
        if target_hit:
            return index, target, "T281_TARGET"
    return end, float(frame.iloc[end]["close"]), "T281_TIME_EXIT"


def _entry_exit_actions(
    frame: pd.DataFrame,
    *,
    entry_index: int,
    exit_index: int,
    side: str,
    position_fraction: float,
    event_id: str,
    candidate: CandidateSpec,
    layer: str,
    target_bps: float,
    stop_bps: float,
    hold_bars: int,
    exit_price: float,
    exit_reason: str,
) -> list[StrategyAction]:
    entry_price = float(frame.iloc[entry_index]["close"])
    quantity = (STARTING_CASH * float(position_fraction)) / entry_price
    entry_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
    exit_type = StrategyActionType.EXIT_LONG if side == "LONG" else StrategyActionType.EXIT_SHORT
    metadata = {
        "pattern_type": "TASK281_PRIORITY_CORE_ACTIVITY_SCOUT",
        "pattern_event_id": event_id,
        "event_id": event_id,
        "canonical_pattern_action": True,
        "position_side": side,
        "pattern_direction": "BULLISH" if side == "LONG" else "BEARISH",
        "strategy_variant_id": candidate.variant_id,
        "task281_family": candidate.family,
        "task281_layer": layer,
        "entry_price": entry_price,
        "position_fraction_of_starting_cash": float(position_fraction),
        "quantity_sizing_source": "TASK281_FIXED_STARTING_CASH_FRACTION",
        "target_bps": float(target_bps),
        "stop_bps": float(stop_bps),
        "hold_bars": int(hold_bars),
        "risk_per_unit": abs(entry_price - (entry_price * (1.0 + stop_bps / 10_000.0 if side == "SHORT" else 1.0 - stop_bps / 10_000.0))),
        "completed_candle_only": True,
        "offline_research_only": True,
    }
    return [
        StrategyAction(
            action_type=entry_type,
            timestamp=frame.iloc[entry_index]["timestamp"],
            quantity=quantity,
            reason="T281_SIGNAL_CONFIRMED",
            metadata=metadata,
            requested_price=entry_price,
        ),
        StrategyAction(
            action_type=exit_type,
            timestamp=frame.iloc[exit_index]["timestamp"],
            quantity=1.0,
            quantity_mode=StrategyQuantityMode.POSITION_RATIO,
            reason=exit_reason,
            metadata={
                **metadata,
                "exit_reason": exit_reason,
                "target_name": exit_reason,
                "requested_exit_price": float(exit_price),
            },
            requested_price=float(exit_price),
        ),
    ]


def _enrich(candles: pd.DataFrame) -> pd.DataFrame:
    frame = candles.copy(deep=True).reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = frame[col].astype(float)
    for window in (60, 240):
        frame[f"range_high_prior_{window}"] = frame["high"].rolling(window, min_periods=window).max().shift(1)
        frame[f"range_low_prior_{window}"] = frame["low"].rolling(window, min_periods=window).min().shift(1)
    for window in (15, 60, 240, 720):
        frame[f"return_bps_prior_{window}"] = (
            (frame["close"].shift(1) / frame["close"].shift(window + 1)) - 1.0
        ) * 10_000.0
    return frame


def _load_candles(database_url: str, window: WindowSpec) -> pd.DataFrame:
    candles = PostgresCandleRepository(database_url).load_standard_candles(
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=_dt(window.start_time),
        end_time=_dt(window.end_time),
    )
    frame = pd.DataFrame(candles)
    if frame.empty:
        raise RuntimeError(f"no candles for {window.window_id}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame[["timestamp", "open", "high", "low", "close", "volume"]]


def _closing_net_pnls(result: Any) -> list[float]:
    values: list[float] = []
    for execution in result.executions:
        action_type = str(getattr(execution, "action_type", ""))
        if action_type in {StrategyActionType.EXIT_LONG.value, StrategyActionType.EXIT_SHORT.value}:
            net = getattr(execution, "net_pnl", None)
            quantity = float(getattr(execution, "quantity", 0.0) or 0.0)
            if net is not None and quantity > 0:
                values.append(float(net))
    return values


def _active_trade_days(result: Any) -> int:
    days: set[str] = set()
    for execution in result.executions:
        action_type = str(getattr(execution, "action_type", ""))
        quantity = float(getattr(execution, "quantity", 0.0) or 0.0)
        if action_type in {StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value} and quantity > 0:
            days.add(str(pd.Timestamp(execution.timestamp).date()))
    return len(days)


def _gate_status(
    *,
    total_return: float,
    completed_round_trips: int,
    active_days: int,
    cost_to_gross_pnl_ratio: float | None,
    largest_winner_contribution: float | None,
    top_three_winner_contribution: float | None,
    trade_count: int,
) -> tuple[str, str]:
    failures: list[str] = []
    if total_return < 0.03:
        failures.append("return_lt_3pct")
    if completed_round_trips < 50:
        failures.append("round_trips_lt_50")
    if active_days < 5:
        failures.append("active_days_lt_5")
    if cost_to_gross_pnl_ratio is None or cost_to_gross_pnl_ratio > 0.60:
        failures.append("cost_to_gross_gt_0p60")
    if largest_winner_contribution is None or largest_winner_contribution > 0.40:
        failures.append("largest_winner_gt_0p40")
    if top_three_winner_contribution is None or top_three_winner_contribution > 0.70:
        failures.append("top_three_winners_gt_0p70")
    if trade_count < completed_round_trips * 2:
        failures.append("trade_count_below_round_trip_executions")
    if failures:
        return "REJECTED_RESEARCH_ONLY", ",".join(failures)
    return "PROMISING_RESEARCH_ONLY", "all_task281_primary_gates_passed"


def _summary_float(metadata: dict[str, Any], key: str) -> float | None:
    value = metadata.get(key) if isinstance(metadata, dict) else None
    return None if value is None else float(value)


def _dict_float(metadata: dict[str, Any], key: str) -> float | None:
    value = metadata.get(key) if isinstance(metadata, dict) else None
    return None if value is None else float(value)


def _directional_vote(value: float, threshold: float) -> int:
    if value > threshold:
        return 1
    if value < -threshold:
        return -1
    return 0


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _positive(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _candidate_batch(candidate: CandidateSpec) -> str:
    if candidate.variant_id.startswith("T281_B1_"):
        return "batch1"
    return "batch_unknown"


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
    parser = argparse.ArgumentParser(description="Run Task 281 high-activity owner-window model batch.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--batch", default="batch1")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    records = run_matrix(database_url=args.database_url, batch=args.batch, limit=args.limit)
    print(f"wrote {REPORT_PATH} with {len(records)} persisted Task 281 runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
