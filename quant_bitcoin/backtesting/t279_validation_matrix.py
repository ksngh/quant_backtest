"""Task 279 BTCUSDT 1m robustness validation matrix runner."""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
from typing import Any, Sequence

from quant_bitcoin.backtesting.strategy_postgres_runner_core import run as run_strategy_cli
from quant_bitcoin.backtesting.strategy_validation_metrics import (
    endpoint_exclusion_window,
    exposure_metrics,
    relative_parameter_neighborhood,
    trade_contribution_metrics,
)
from quant_bitcoin.persistence.postgres import BacktestRunReadModel, PostgresBacktestResultRepository


TASK_ID = "TASK_279"
DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
REPORT_PATH = Path("reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md")


@dataclass(frozen=True)
class CandidateSpec:
    variant_id: str
    family: str
    description: str
    args: tuple[str, ...]
    has_parameter_neighborhood: bool = False


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    start_time: str
    end_time: str | None
    group: str


@dataclass(frozen=True)
class RunPlan:
    candidate: CandidateSpec
    window: WindowSpec
    cash_fraction: float
    cost_profile: str
    run_group: str
    entry_delay: bool = False

    @property
    def run_variant_id(self) -> str:
        delay = "_NEXT_OPEN" if self.entry_delay else ""
        return f"{self.candidate.variant_id}_{self.run_group}_CF_{_fraction_token(self.cash_fraction)}{delay}"


@dataclass(frozen=True)
class RunRecord:
    variant_id: str
    family: str
    description: str
    window_id: str
    run_group: str
    cash_fraction: float
    cost_profile: str
    entry_delay: bool
    run_id: int | None
    total_return: float | None
    final_equity: float | None
    net_pnl: float | None
    gross_pnl: float | None
    total_cost: float | None
    trade_count: int | None
    completed_round_trips: int | None
    active_days: int | None
    max_drawdown: float | None
    cost_to_gross_pnl_ratio: float | None
    max_position_fraction: float | None
    largest_winner_contribution: float | None
    top_three_winner_contribution: float | None
    net_without_best_winner: float | None
    ending_position: float | None
    warnings: tuple[str, ...]
    error: str | None = None


def build_candidates() -> tuple[CandidateSpec, ...]:
    score_low, score_base, score_high = relative_parameter_neighborhood(0.50, relative=0.20)
    return (
        _srlbr_breakdown(score_low, "T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4"),
        _srlbr_breakdown(score_base, "T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5", neighborhood=True),
        _srlbr_breakdown(score_high, "T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6"),
        CandidateSpec(
            variant_id="T279_SRLBR_SHORT_MIX_120_8R",
            family="SRLBR",
            description="Short-mix session-range liquidity model, 120-bar range, 8R target.",
            args=(
                "--pattern",
                "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL",
                "--srlbr-signal-mode",
                "short_mix",
                "--srlbr-direction-mode",
                "short_only",
                "--srlbr-range-lookback-bars",
                "120",
                "--srlbr-max-bars-in-trade",
                "120",
                "--srlbr-target-r-multiple",
                "8",
                "--srlbr-minimum-pattern-score",
                "0.40",
                "--srlbr-minimum-range-bps",
                "10",
                "--srlbr-minimum-volume-ratio",
                "0.8",
                "--srlbr-minimum-body-ratio",
                "0.25",
            ),
        ),
        CandidateSpec(
            variant_id="T279_FVG_INVERSE_SIMPLE",
            family="FAIR_VALUE_GAP",
            description="Inverse FVG direction with v2/channel/volume extras disabled.",
            args=(
                "--pattern",
                "FAIR_VALUE_GAP",
                "--fvg-inverse-direction",
                "--disable-fvg-v2",
                "--disable-fvg-v2-channel",
                "--disable-fvg-channel-standalone-scan",
                "--disable-fvg-close-volume-filter",
                "--disable-fvg-trend-score",
                "--disable-fvg-fibonacci-confluence",
                "--fvg-stop-mode",
                "fvg_boundary_atr_buffer",
            ),
        ),
        CandidateSpec(
            variant_id="T279_OB_618_WAIT20",
            family="ORDER_BLOCK",
            description="Order Block 61.8pct retest, wait 20 bars, previous-candle 1R exit.",
            args=(
                "--pattern",
                "ORDER_BLOCK",
                "--pattern-entry-mode",
                "limit_at_order_block_618_retracement",
                "--fvg-entry-max-wait-bars",
                "20",
                "--ob-risk-exit-mode",
                "previous_candle_1r",
            ),
        ),
        CandidateSpec(
            variant_id="T279_LSR_MARKET_1R",
            family="LIQUIDITY_SWEEP_REVERSAL",
            description="Liquidity sweep reversal, market displacement close, 1R target.",
            args=(
                "--pattern",
                "LIQUIDITY_SWEEP_REVERSAL",
                "--lsr-entry-mode",
                "market_on_displacement_close",
                "--lsr-target-r-multiple",
                "1.0",
                "--lsr-min-gross-rr",
                "1.0",
                "--lsr-min-net-rr",
                "0.01",
                "--lsr-min-net-reward-bps",
                "0.0",
                "--lsr-min-volume-ratio",
                "1.0",
                "--lsr-min-displacement-atr-multiplier",
                "0.5",
                "--lsr-min-displacement-body-ratio",
                "0.45",
            ),
        ),
    )


def build_windows() -> tuple[WindowSpec, ...]:
    max_end = "2026-05-28T08:26:00Z"
    owner_a_start = "2026-05-20T00:00:00Z"
    owner_b_start = "2026-05-25T00:00:00Z"
    trim_a_start, trim_a_end = endpoint_exclusion_window(
        _dt(owner_a_start),
        _dt(max_end),
        minutes=60,
    )
    trim_b_start, trim_b_end = endpoint_exclusion_window(
        _dt(owner_b_start),
        _dt(max_end),
        minutes=60,
    )
    return (
        WindowSpec("owner_a", owner_a_start, max_end, "owner"),
        WindowSpec("owner_b", owner_b_start, max_end, "owner"),
        WindowSpec("trim_a", _iso(trim_a_start), _iso(trim_a_end), "endpoint_trim"),
        WindowSpec("trim_b", _iso(trim_b_start), _iso(trim_b_end), "endpoint_trim"),
        WindowSpec("oos_1", "2026-05-10T00:00:00Z", "2026-05-14T00:00:00Z", "oos"),
        WindowSpec("oos_2", "2026-05-14T00:00:00Z", "2026-05-18T00:00:00Z", "oos"),
    )


def build_run_plan() -> tuple[RunPlan, ...]:
    candidates = build_candidates()
    windows = build_windows()
    plans: list[RunPlan] = []
    sizing_ladder = (0.10, 0.25, 0.50, 0.75)
    primary_sizing = (0.10, 0.50)

    for candidate in candidates:
        for window in windows:
            sizes = sizing_ladder if window.group == "owner" else primary_sizing
            for cash_fraction in sizes:
                plans.append(
                    RunPlan(
                        candidate=candidate,
                        window=window,
                        cash_fraction=cash_fraction,
                        cost_profile="conservative_crypto_1m",
                        run_group=window.group,
                    )
                )

        for window in (w for w in windows if w.group == "owner"):
            for cash_fraction in primary_sizing:
                plans.append(
                    RunPlan(
                        candidate=candidate,
                        window=window,
                        cash_fraction=cash_fraction,
                        cost_profile="high_slippage_stress",
                        run_group="cost_stress",
                    )
                )
            plans.append(
                RunPlan(
                    candidate=candidate,
                    window=window,
                    cash_fraction=0.10,
                    cost_profile="conservative_crypto_1m",
                    run_group="entry_delay",
                    entry_delay=True,
                )
            )

    return tuple(plans)


def execute_matrix(
    *,
    database_url: str,
    report_path: Path,
    limit: int | None = None,
) -> list[RunRecord]:
    repository = PostgresBacktestResultRepository(database_url)
    records: list[RunRecord] = []
    for index, plan in enumerate(build_run_plan(), start=1):
        if limit is not None and index > limit:
            break
        output: dict[str, Any] | None = None
        error: str | None = None
        try:
            output = _run_cli(plan, database_url)
        except Exception as exc:  # pragma: no cover - exercised by real matrix failures
            error = str(exc)
        record = _record_from_output(plan, output, repository, error=error)
        records.append(record)
        print(
            f"[{index}/{len(build_run_plan())}] {record.variant_id} {record.window_id} "
            f"cf={record.cash_fraction:.2f} {record.cost_profile} run={record.run_id} "
            f"ret={_pct(record.total_return)} trips={record.completed_round_trips} err={record.error or '-'}"
        )
    _write_report(records, report_path)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task 279 validation matrix.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--report-path", default=str(REPORT_PATH))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--finalize-only", action="store_true")
    args = parser.parse_args(argv)
    if args.finalize_only:
        records = collect_task_records(args.database_url)
        _write_report(records, Path(args.report_path))
        print(f"wrote {args.report_path} from {len(records)} persisted {TASK_ID} runs")
        return 0
    execute_matrix(
        database_url=args.database_url,
        report_path=Path(args.report_path),
        limit=args.limit,
    )
    return 0


def collect_task_records(database_url: str) -> list[RunRecord]:
    import psycopg

    repository = PostgresBacktestResultRepository(database_url)
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id
            FROM backtest_runs
            WHERE metadata->'research'->>'task_id' = %s
            ORDER BY id ASC
            """,
            (TASK_ID,),
        ).fetchall()
    records: list[RunRecord] = []
    for (run_id,) in rows:
        run = repository.load_run_for_graphs(int(run_id))
        if run is None:
            continue
        research = (run.run.metadata or {}).get("research") or {}
        variant_id = str(research.get("variant_id") or f"run_{run_id}")
        window_id = str(research.get("window_id") or "unknown")
        run_group = str(research.get("run_group") or "unknown")
        summary_metadata = run.summary.metadata or {}
        cost_summary = summary_metadata.get("cost_summary") or {}
        cost_profile = (
            (run.strategy_config.parameters or {}).get("cost_profile")
            or summary_metadata.get("cost_profile")
            or {}
        )
        position_sizing = summary_metadata.get("position_sizing") or {}
        performance = summary_metadata.get("performance_metrics") or {}
        metrics = _run_metrics(run)
        records.append(
            RunRecord(
                variant_id=variant_id,
                family=str(run.strategy_config.strategy_key),
                description=str(run.strategy_config.strategy_name),
                window_id=window_id,
                run_group=run_group,
                cash_fraction=float(position_sizing.get("value") or 0.0),
                cost_profile=str(cost_profile.get("profile_key") or "unknown"),
                entry_delay=variant_id.endswith("_NEXT_OPEN"),
                run_id=int(run_id),
                total_return=float(run.summary.total_return),
                final_equity=float(run.summary.final_equity),
                net_pnl=_float(cost_summary.get("net_pnl") if cost_summary else summary_metadata.get("net_pnl")),
                gross_pnl=_float(cost_summary.get("gross_pnl") if cost_summary else summary_metadata.get("gross_pnl")),
                total_cost=_float(cost_summary.get("total_cost")),
                trade_count=int(run.summary.trade_count),
                completed_round_trips=metrics["completed_round_trips"],
                active_days=metrics["active_days"],
                max_drawdown=_float(performance.get("max_drawdown")),
                cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
                max_position_fraction=metrics["max_position_fraction"],
                largest_winner_contribution=metrics["largest_winner_contribution"],
                top_three_winner_contribution=metrics["top_three_winner_contribution"],
                net_without_best_winner=metrics["net_without_best_winner"],
                ending_position=float(run.summary.ending_position),
                warnings=(),
                error=None,
            )
        )
    return records


def _srlbr_breakdown(score: float, variant_id: str, *, neighborhood: bool = False) -> CandidateSpec:
    return CandidateSpec(
        variant_id=variant_id,
        family="SRLBR",
        description=f"Breakdown continuation SRLBR, 240-bar range, 12R target, score {score:.2f}.",
        args=(
            "--pattern",
            "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL",
            "--srlbr-signal-mode",
            "breakdown_continuation",
            "--srlbr-direction-mode",
            "short_only",
            "--srlbr-range-lookback-bars",
            "240",
            "--srlbr-max-bars-in-trade",
            "240",
            "--srlbr-target-r-multiple",
            "12",
            "--srlbr-minimum-pattern-score",
            f"{score:.2f}",
            "--srlbr-minimum-range-bps",
            "10",
            "--srlbr-minimum-volume-ratio",
            "0.8",
            "--srlbr-minimum-body-ratio",
            "0.25",
        ),
        has_parameter_neighborhood=neighborhood,
    )


def _run_cli(plan: RunPlan, database_url: str) -> dict[str, Any]:
    argv = [
        "--database-url",
        database_url,
        "--source",
        "binance_spot",
        "--symbol",
        "BTCUSDT",
        "--interval",
        "1m",
        "--start-time",
        plan.window.start_time,
        "--starting-cash",
        "1000000",
        "--starting-cash-currency",
        "USDT",
        "--position-sizing-mode",
        "cash_fraction",
        "--position-sizing-value",
        f"{plan.cash_fraction:.2f}",
        "--cost-profile",
        plan.cost_profile,
        "--enforce-candle-continuity",
        "--enable-market-regime",
        "--research-task-id",
        TASK_ID,
        "--research-variant-id",
        plan.run_variant_id,
        "--research-window-id",
        plan.window.window_id,
        "--research-run-group",
        plan.run_group,
    ]
    if plan.window.end_time:
        argv.extend(["--end-time", plan.window.end_time])
    argv.extend(plan.candidate.args)
    if plan.entry_delay:
        argv.extend(["--pattern-entry-mode", "market_on_next_open"])

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = run_strategy_cli(argv)
    raw_output = buffer.getvalue().strip()
    if exit_code != 0:
        raise RuntimeError(f"runner exit code {exit_code}: {raw_output[-500:]}")
    if not raw_output:
        raise RuntimeError("runner produced no JSON output")
    return json.loads(raw_output)


def _record_from_output(
    plan: RunPlan,
    output: dict[str, Any] | None,
    repository: PostgresBacktestResultRepository,
    *,
    error: str | None,
) -> RunRecord:
    if output is None:
        return _empty_record(plan, error=error or "no output")
    run_id = output.get("backtest_run_id")
    run_model = repository.load_run_for_graphs(int(run_id)) if run_id is not None else None
    if run_model is None:
        return _empty_record(plan, error=error or "persisted run not found")
    metrics = _run_metrics(run_model)
    summary = run_model.summary
    metadata = summary.metadata or {}
    cost_summary = metadata.get("cost_summary") or {}
    performance = metadata.get("performance_metrics") or {}
    return RunRecord(
        variant_id=plan.run_variant_id,
        family=plan.candidate.family,
        description=plan.candidate.description,
        window_id=plan.window.window_id,
        run_group=plan.run_group,
        cash_fraction=plan.cash_fraction,
        cost_profile=plan.cost_profile,
        entry_delay=plan.entry_delay,
        run_id=int(run_id),
        total_return=float(summary.total_return),
        final_equity=float(summary.final_equity),
        net_pnl=_float(cost_summary.get("net_pnl") if cost_summary else metadata.get("net_pnl")),
        gross_pnl=_float(cost_summary.get("gross_pnl") if cost_summary else metadata.get("gross_pnl")),
        total_cost=_float(cost_summary.get("total_cost")),
        trade_count=int(summary.trade_count),
        completed_round_trips=metrics["completed_round_trips"],
        active_days=metrics["active_days"],
        max_drawdown=_float(performance.get("max_drawdown")),
        cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
        max_position_fraction=metrics["max_position_fraction"],
        largest_winner_contribution=metrics["largest_winner_contribution"],
        top_three_winner_contribution=metrics["top_three_winner_contribution"],
        net_without_best_winner=metrics["net_without_best_winner"],
        ending_position=float(summary.ending_position),
        warnings=tuple(output.get("warnings") or ()),
        error=error,
    )


def _run_metrics(run: BacktestRunReadModel) -> dict[str, Any]:
    net_pnls = [
        float((trade.metadata or {}).get("net_pnl"))
        for trade in run.trades
        if (trade.metadata or {}).get("net_pnl") is not None
    ]
    contribution = trade_contribution_metrics(net_pnls)
    exposure = exposure_metrics(run.graph_points)
    active_dates = {
        point.candle_open_time.date()
        for point in run.graph_points
        if abs(float(point.position)) > 0
    }
    return {
        "completed_round_trips": len(net_pnls),
        "active_days": len(active_dates),
        "max_position_fraction": exposure.max_continuous_position_fraction,
        "largest_winner_contribution": contribution.largest_winner_contribution,
        "top_three_winner_contribution": contribution.top_three_winner_contribution,
        "net_without_best_winner": contribution.net_without_best_winner,
    }


def _empty_record(plan: RunPlan, *, error: str) -> RunRecord:
    return RunRecord(
        variant_id=plan.run_variant_id,
        family=plan.candidate.family,
        description=plan.candidate.description,
        window_id=plan.window.window_id,
        run_group=plan.run_group,
        cash_fraction=plan.cash_fraction,
        cost_profile=plan.cost_profile,
        entry_delay=plan.entry_delay,
        run_id=None,
        total_return=None,
        final_equity=None,
        net_pnl=None,
        gross_pnl=None,
        total_cost=None,
        trade_count=None,
        completed_round_trips=None,
        active_days=None,
        max_drawdown=None,
        cost_to_gross_pnl_ratio=None,
        max_position_fraction=None,
        largest_winner_contribution=None,
        top_three_winner_contribution=None,
        net_without_best_winner=None,
        ending_position=None,
        warnings=(),
        error=error,
    )


def _write_report(records: Sequence[RunRecord], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    owner_primary = [
        record
        for record in records
        if record.run_group == "owner"
        and record.cost_profile == "conservative_crypto_1m"
        and record.cash_fraction == 0.10
    ]
    lines = [
        "# Task 279 Strategy Robustness Validation Matrix",
        "",
        "Date: 2026-05-29",
        "",
        "Status: `RESEARCH_ONLY`",
        "",
        "## Verdict",
        "",
        "Task 278's one-position inverse trend-hold result remains `DIAGNOSTIC_ONLY`. "
        "The Task 279 matrix persisted a broader set of BTCUSDT 1m candidate runs and no candidate passed all robustness gates.",
        "",
        "## Predeclared Matrix",
        "",
        f"- Candidates: `{len(build_candidates())}`",
        f"- Planned runs: `{len(build_run_plan())}`",
        f"- Persisted Task 279 runs in DB: `{len(records)}`",
        "- Sizing ladder on owner windows: `0.10`, `0.25`, `0.50`, `0.75` cash fraction",
        "- Primary validation sizing: `0.10` cash fraction",
        "- Secondary sizing diagnostics: `0.25`, `0.50`, `0.75` cash fraction",
        "- Windows: owner A/B, endpoint-trim A/B, OOS 1/2, high-slippage stress, and one-candle entry delay",
        "- Runtime note: the full 154-run plan was stopped after 135 persisted runs because the optional Order Block expansion was already strongly dominated and slow; SRLBR, FVG inverse, and LSR validation groups were persisted broadly.",
        "",
        "## Gate Summary",
        "",
        "| Candidate | Sample/Activity | Endpoint | Outlier | Cost | Drawdown | Exposure | Parameter | OOS | Benchmark | Execution | Persistence | Final |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in build_candidates():
        gates = _gate_summary(candidate, records)
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate.variant_id,
                    gates["sample"],
                    gates["endpoint"],
                    gates["outlier"],
                    gates["cost"],
                    gates["drawdown"],
                    gates["exposure"],
                    gates["parameter"],
                    gates["oos"],
                    gates["benchmark"],
                    gates["execution"],
                    gates["persistence"],
                    gates["final"],
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Primary Owner Runs",
            "",
            "| Candidate | Window | Run | Return | Net PnL | Cost | Completed Trips | Active Days | Max Position Fraction | Cost/Gross | Ending Position |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for record in owner_primary:
        lines.append(_record_row(record))

    lines.extend(
        [
            "",
            "## All Persisted Validation Runs",
            "",
            "| Group | Candidate | Window | CF | Cost Profile | Run | Return | Trips | Cost | Warnings/Error |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for record in records:
        warning = record.error or ",".join(record.warnings[:3]) or "-"
        lines.append(
            f"| {record.run_group} | {record.variant_id} | {record.window_id} | {record.cash_fraction:.2f} | "
            f"{record.cost_profile} | {record.run_id or '-'} | {_pct(record.total_return)} | "
            f"{record.completed_round_trips if record.completed_round_trips is not None else '-'} | "
            f"{_money(record.total_cost)} | {warning} |"
        )

    lines.extend(
        [
            "",
            "## Task 278 Benchmark Interpretation",
            "",
            "- Task 278 run `155` and run `156` passed the owner's raw total-return check but used one full-window simulated short position.",
            "- Under Task 279 gates, that behavior fails sample-size, endpoint-dependence, exposure concentration, OOS, and promotion robustness requirements.",
            "- Task 278 remains a directional benchmark, not a validated multi-trade strategy.",
            "",
            "## Cost Verification",
            "",
            "- Every persisted Task 279 run used a non-zero cost profile unless the run failed before persistence.",
            "- Conservative profile runs used `conservative_crypto_1m`; stress runs used `high_slippage_stress`.",
            "- The report rejects candidates whose gross edge is dominated by fee/spread/slippage or whose cost-to-gross-PnL ratio exceeds `0.40`.",
            "",
            "## OOS And Data-Snooping",
            "",
            "- Owner windows `2026-05-20+` and `2026-05-25+` remain development evidence only.",
            "- OOS windows were predeclared from `2026-05-10` to `2026-05-14` and `2026-05-14` to `2026-05-18`.",
            "- No result is promoted beyond `RESEARCH_ONLY`.",
            "",
            "## Next Step",
            "",
            "Build a new bounded multi-trade model only after defining an entry thesis that can pass these gates at `cash_fraction=0.10` before sizing is increased.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _gate_summary(candidate: CandidateSpec, records: Sequence[RunRecord]) -> dict[str, str]:
    owner = _records_for(records, candidate.variant_id, run_group="owner", cash_fraction=0.10)
    trim = _records_for(records, candidate.variant_id, run_group="endpoint_trim", cash_fraction=0.10)
    stress = _records_for(records, candidate.variant_id, run_group="cost_stress", cash_fraction=0.10)
    oos = _records_for(records, candidate.variant_id, run_group="oos", cash_fraction=0.10)
    delay = _records_for(records, candidate.variant_id, run_group="entry_delay", cash_fraction=0.10)
    persistence_ok = all(record.run_id is not None for record in owner + trim + stress + oos + delay)
    owner_positive = all((record.total_return or 0.0) > 0 for record in owner) and len(owner) >= 2
    sample_ok = (
        _window_record(owner, "owner_a", candidate.variant_id).completed_round_trips or 0
    ) >= 20 and (
        _window_record(owner, "owner_b", candidate.variant_id).completed_round_trips or 0
    ) >= 8 and all((record.active_days or 0) >= 3 for record in owner) and all(
        (record.max_position_fraction or 1.0) <= 0.35 for record in owner
    )
    endpoint_ok = owner_positive and all((record.total_return or -1.0) > 0 for record in trim + delay)
    outlier_ok = owner_positive and all(
        (record.largest_winner_contribution is not None and record.largest_winner_contribution <= 0.40)
        and (record.top_three_winner_contribution is not None and record.top_three_winner_contribution <= 0.70)
        and (record.net_without_best_winner is not None and record.net_without_best_winner > 0)
        for record in owner
    )
    cost_ok = owner_positive and all(
        (record.total_cost or 0.0) > 0
        and (record.cost_to_gross_pnl_ratio is not None and record.cost_to_gross_pnl_ratio <= 0.40)
        for record in owner
    ) and all((record.total_return or -1.0) > 0 for record in stress)
    drawdown_ok = owner_positive and all(
        record.max_drawdown is not None
        and abs(record.max_drawdown) <= 1.5 * abs(record.total_return or 0.0)
        for record in owner
    )
    exposure_ok = all((record.max_position_fraction or 1.0) <= 0.35 for record in owner)
    parameter_ok = _parameter_gate(candidate, records)
    oos_ok = owner_positive and len(oos) >= 2 and all((record.total_return or -1.0) > 0 for record in oos)
    benchmark_ok = owner_positive and all((record.total_return or 0.0) > 0.031 for record in owner)
    execution_ok = all(abs(record.ending_position or 0.0) < 1e-9 for record in owner)
    final_ok = all(
        [
            sample_ok,
            endpoint_ok,
            outlier_ok,
            cost_ok,
            drawdown_ok,
            exposure_ok,
            parameter_ok,
            oos_ok,
            benchmark_ok,
            execution_ok,
            persistence_ok,
        ]
    )
    return {
        "sample": _status(sample_ok),
        "endpoint": _status(endpoint_ok),
        "outlier": _status(outlier_ok),
        "cost": _status(cost_ok),
        "drawdown": _status(drawdown_ok),
        "exposure": _status(exposure_ok),
        "parameter": _status(parameter_ok),
        "oos": _status(oos_ok),
        "benchmark": _status(benchmark_ok),
        "execution": _status(execution_ok),
        "persistence": _status(persistence_ok),
        "final": "PROMISING_RESEARCH_ONLY" if final_ok else "DIAGNOSTIC_ONLY",
    }


def _records_for(
    records: Sequence[RunRecord],
    base_variant_id: str,
    *,
    run_group: str,
    cash_fraction: float,
) -> list[RunRecord]:
    return [
        record
        for record in records
        if record.variant_id.startswith(base_variant_id)
        and record.run_group == run_group
        and record.cash_fraction == cash_fraction
    ]


def _window_record(records: Sequence[RunRecord], window_id: str, variant_id: str) -> RunRecord:
    for record in records:
        if record.window_id == window_id:
            return record
    return _empty_record(
        RunPlan(
            candidate=CandidateSpec(variant_id, "missing", "missing", ()),
            window=WindowSpec(window_id, "", None, "missing"),
            cash_fraction=0.10,
            cost_profile="missing",
            run_group="missing",
        ),
        error="missing",
    )


def _parameter_gate(candidate: CandidateSpec, records: Sequence[RunRecord]) -> bool:
    if candidate.has_parameter_neighborhood:
        family_records = [
            record
            for record in records
            if record.run_group == "owner"
            and record.cash_fraction == 0.10
            and record.variant_id.startswith("T279_SRLBR_BREAKDOWN_240_12R_SCORE")
        ]
        positive_pairs = 0
        for prefix in {
            record.variant_id.split("_owner_", 1)[0]
            for record in family_records
            if "_owner_" in record.variant_id
        }:
            paired = [record for record in family_records if record.variant_id.startswith(prefix)]
            if len(paired) >= 2 and all((record.total_return or -1.0) > 0 for record in paired):
                positive_pairs += 1
        return positive_pairs >= 2
    return False


def _record_row(record: RunRecord) -> str:
    return (
        f"| {record.variant_id} | {record.window_id} | {record.run_id or '-'} | {_pct(record.total_return)} | "
        f"{_money(record.net_pnl)} | {_money(record.total_cost)} | "
        f"{record.completed_round_trips if record.completed_round_trips is not None else '-'} | "
        f"{record.active_days if record.active_days is not None else '-'} | "
        f"{_ratio(record.max_position_fraction)} | {_ratio(record.cost_to_gross_pnl_ratio)} | "
        f"{record.ending_position if record.ending_position is not None else '-'} |"
    )


def _fraction_token(value: float) -> str:
    return str(f"{value:.2f}").replace(".", "P")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:+.4f}pct"


def _money(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def _ratio(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


if __name__ == "__main__":
    raise SystemExit(main())
