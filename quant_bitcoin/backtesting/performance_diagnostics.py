from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence


class DiagnosticSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class DiagnosticFlag:
    code: str
    severity: DiagnosticSeverity
    category: str
    message: str
    evidence: dict[str, object]
    suggested_next_analysis: str

    def to_metadata(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "evidence": self.evidence,
            "suggested_next_analysis": self.suggested_next_analysis,
        }


def calculate_backtest_performance_diagnostics(
    summary_metadata: Mapping[str, Any] | None,
    executions: Sequence[Any] = (),
    graph_points: Sequence[Any] = (),
    run_parameters: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Classify saved-run performance issues from persisted simulation data only."""

    metadata = dict(summary_metadata or {})
    performance = _record(metadata.get("performance_metrics"))
    attribution = _record(metadata.get("trade_attribution"))
    trade_metrics = _record(attribution.get("trade_metrics"))
    exposure = _record(attribution.get("exposure"))
    turnover = _record(attribution.get("turnover"))
    cost_summary = _record(metadata.get("cost_summary"))
    short_performance = _record(metadata.get("short_performance"))
    short_economics = _record(metadata.get("short_economics"))

    flags: list[DiagnosticFlag] = []
    warnings: list[str] = []
    if not performance:
        warnings.append("performance_metrics metadata missing")
    if not attribution:
        warnings.append("trade_attribution metadata missing")
    if not cost_summary:
        warnings.append("cost_summary metadata missing")

    completed = _number(trade_metrics, "completed_trade_count")
    if completed is not None and completed < 5:
        warnings.append("sample size is small; inference strength is weak")

    _append_metric_flags(flags, trade_metrics, performance, exposure, turnover, cost_summary)
    _append_short_flag(flags, short_performance, short_economics)
    _append_execution_flags(flags, executions)
    _append_exit_reason_dominance_flags(flags, attribution)

    suggested = tuple(dict.fromkeys(flag.suggested_next_analysis for flag in flags))
    return {
        "schema_version": "backtest_performance_diagnostics_v1",
        "flags": tuple(flag.to_metadata() for flag in flags),
        "flag_count": len(flags),
        "highest_severity": _highest_severity(flags),
        "warnings": tuple(warnings),
        "suggested_next_analysis": suggested,
        "inference_strength": _inference_strength(completed, warnings),
        "run_parameters_seen": sorted(str(key) for key in (run_parameters or {}).keys()),
        "graph_point_count": len(graph_points),
    }


def _append_metric_flags(
    flags: list[DiagnosticFlag],
    trade_metrics: Mapping[str, Any],
    performance: Mapping[str, Any],
    exposure: Mapping[str, Any],
    turnover: Mapping[str, Any],
    cost_summary: Mapping[str, Any],
) -> None:
    expectancy = _number(trade_metrics, "expectancy")
    if expectancy is not None and expectancy < 0:
        flags.append(
            _flag(
                "NEGATIVE_EXPECTANCY",
                DiagnosticSeverity.WARNING,
                "alpha",
                "Completed trade lifecycle expectancy is negative.",
                {"expectancy": expectancy},
                "Inspect entry/exit lifecycle examples and pattern-specific attribution.",
            )
        )

    hit_ratio = _number(trade_metrics, "hit_ratio")
    if hit_ratio is not None and hit_ratio < 0.4:
        flags.append(
            _flag(
                "LOW_HIT_RATE",
                DiagnosticSeverity.WARNING,
                "alpha",
                "The strategy wins too infrequently to support the current payoff profile.",
                {"hit_ratio": hit_ratio},
                "Compare signal timing against MFE/MAE and check whether entries are chasing late moves.",
            )
        )

    payoff_ratio = _number(trade_metrics, "payoff_ratio")
    if payoff_ratio is not None and payoff_ratio < 1.0:
        flags.append(
            _flag(
                "POOR_PAYOFF_RATIO",
                DiagnosticSeverity.WARNING,
                "risk_reward",
                "Average wins are smaller than average losses.",
                {"payoff_ratio": payoff_ratio},
                "Audit stop distance, target placement, and partial-exit dominance.",
            )
        )

    cost_ratio = _number(cost_summary, "cost_to_gross_pnl_ratio")
    gross_pnl = _number(cost_summary, "gross_pnl")
    net_pnl = _number(cost_summary, "net_pnl")
    if (cost_ratio is not None and cost_ratio > 0.2) or ((gross_pnl or 0.0) > 0 and (net_pnl or 0.0) < 0):
        flags.append(
            _flag(
                "HIGH_COST_DRAG",
                DiagnosticSeverity.CRITICAL if (gross_pnl or 0.0) > 0 and (net_pnl or 0.0) < 0 else DiagnosticSeverity.WARNING,
                "cost",
                "Transaction costs consume a large share of gross edge.",
                {"cost_to_gross_pnl_ratio": cost_ratio, "gross_pnl": gross_pnl, "net_pnl": net_pnl},
                "Run cost sensitivity and compare maker/taker, spread, and slippage assumptions.",
            )
        )

    max_drawdown = _number(performance, "max_drawdown")
    max_drawdown_duration = _number(performance, "max_drawdown_duration_periods")
    if (max_drawdown is not None and max_drawdown <= -0.2) or (max_drawdown_duration is not None and max_drawdown_duration > 20):
        flags.append(
            _flag(
                "LARGE_OR_PERSISTENT_DRAWDOWN",
                DiagnosticSeverity.WARNING,
                "drawdown",
                "Drawdown depth or duration is large enough to weaken the run.",
                {"max_drawdown": max_drawdown, "max_drawdown_duration_periods": max_drawdown_duration},
                "Review drawdown segments and regime attribution during equity stagnation.",
            )
        )

    completed = _number(trade_metrics, "completed_trade_count")
    if completed is not None and completed == 0:
        flags.append(
            _flag(
                "NO_COMPLETED_TRADES",
                DiagnosticSeverity.WARNING,
                "sample",
                "No completed trade lifecycle exists, so performance inference is weak.",
                {"completed_trade_count": completed},
                "Extend the sample window or inspect no-fill/open-position behavior.",
            )
        )

    exposure_fraction = _number(exposure, "exposure_fraction")
    if exposure_fraction is not None and exposure_fraction < 0.05:
        flags.append(
            _flag(
                "LOW_EXPOSURE",
                DiagnosticSeverity.INFO,
                "exposure",
                "The strategy spends very little time in a position.",
                {"exposure_fraction": exposure_fraction},
                "Check whether filters or entry modes suppress most opportunities.",
            )
        )

    turnover_ratio = _number(turnover, "turnover_ratio")
    if turnover_ratio is not None and turnover_ratio > 10:
        flags.append(
            _flag(
                "HIGH_TURNOVER",
                DiagnosticSeverity.WARNING,
                "execution",
                "Filled notional is high relative to starting equity.",
                {"turnover_ratio": turnover_ratio},
                "Inspect churn, duplicate entries, and cost sensitivity.",
            )
        )

    if _bool(cost_summary, "zero_transaction_cost_assumption") is True:
        flags.append(
            _flag(
                "ZERO_COST_ASSUMPTION",
                DiagnosticSeverity.WARNING,
                "cost",
                "This run assumes zero fees, spread, and slippage.",
                {"zero_transaction_cost_assumption": True},
                "Rerun with realistic transaction-cost presets before trusting net performance.",
            )
        )


def _append_short_flag(
    flags: list[DiagnosticFlag],
    short_performance: Mapping[str, Any],
    short_economics: Mapping[str, Any],
) -> None:
    short_close_count = _number(short_performance, "short_close_count")
    has_short_policy = bool(short_economics)
    if (short_close_count is not None and short_close_count > 0) or has_short_policy:
        flags.append(
            _flag(
                "SHORT_SIMULATION_ONLY",
                DiagnosticSeverity.INFO,
                "short_economics",
                "Short results are simulation-only and omit borrow/funding/liquidation economics.",
                {"short_close_count": short_close_count, "short_economics_scope": short_economics.get("scope")},
                "Separate long and short attribution before comparing live feasibility.",
            )
        )


def _append_execution_flags(flags: list[DiagnosticFlag], executions: Sequence[Any]) -> None:
    fill_divergence_count = 0
    negative_take_profit_count = 0
    for execution in executions:
        metadata = _record(_field(execution, "metadata"))
        fill = _number(metadata, "fill_price")
        reference = _number(metadata, "entry_reference")
        aligned = _bool(metadata, "risk_plan_aligned_to_fill")
        if aligned is True or (fill is not None and reference is not None and abs(fill - reference) > 1e-12):
            fill_divergence_count += 1

        exit_reason = str(_field(execution, "exit_reason") or metadata.get("exit_reason") or "").upper()
        gross_pnl = _number_or_field(execution, metadata, "gross_pnl")
        net_pnl = _number_or_field(execution, metadata, "net_pnl")
        if exit_reason == "TAKE_PROFIT" and ((gross_pnl is not None and gross_pnl < 0) or (net_pnl is not None and net_pnl < 0)):
            negative_take_profit_count += 1

    if fill_divergence_count:
        flags.append(
            _flag(
                "ENTRY_FILL_REFERENCE_DIVERGENCE",
                DiagnosticSeverity.INFO,
                "fill_model",
                "Some entries filled away from the original reference price.",
                {"execution_count": fill_divergence_count},
                "Compare market-on-confirmation entries against retest/limit entry experiments.",
            )
        )
    if negative_take_profit_count:
        flags.append(
            _flag(
                "TAKE_PROFIT_NEGATIVE_PNL_ANOMALY",
                DiagnosticSeverity.CRITICAL,
                "mechanical_anomaly",
                "At least one take-profit exit realized negative PnL.",
                {"execution_count": negative_take_profit_count},
                "Inspect fill price, target price, realized R, and stale risk-plan metadata immediately.",
            )
        )


def _append_exit_reason_dominance_flags(flags: list[DiagnosticFlag], attribution: Mapping[str, Any]) -> None:
    by_exit_reason = _record(_record(attribution.get("attribution")).get("by_exit_reason"))
    if not by_exit_reason:
        return
    total_completed = sum(_number(_record(value), "completed_trade_count") or 0.0 for value in by_exit_reason.values())
    if total_completed <= 0:
        return
    for code, reason_tokens, message, suggestion in (
        ("SOFT_INVALIDATION_DOMINANT", ("SOFT_INVALIDATION",), "Soft invalidation dominates completed exits.", "Audit soft invalidation thresholds and close-based invalidation timing."),
        ("TIME_STOP_DOMINANT", ("TIME_STOP",), "Time-stop exits dominate completed exits.", "Inspect whether targets are too distant or max-bars settings are too short."),
        ("STOP_LOSS_DOMINANT", ("HARD_STOP", "STOP_LOSS"), "Stop-loss exits dominate completed exits.", "Audit stop placement, entry timing, and same-candle stop/target sequencing."),
    ):
        count = 0.0
        for reason, value in by_exit_reason.items():
            if any(token in str(reason).upper() for token in reason_tokens):
                count += _number(_record(value), "completed_trade_count") or 0.0
        if count / total_completed >= 0.5:
            flags.append(
                _flag(
                    code,
                    DiagnosticSeverity.WARNING,
                    "exit_policy",
                    message,
                    {"dominant_exit_count": count, "completed_trade_count": total_completed, "share": count / total_completed},
                    suggestion,
                )
            )


def _flag(
    code: str,
    severity: DiagnosticSeverity,
    category: str,
    message: str,
    evidence: dict[str, object],
    suggested_next_analysis: str,
) -> DiagnosticFlag:
    return DiagnosticFlag(code, severity, category, message, evidence, suggested_next_analysis)


def _highest_severity(flags: Sequence[DiagnosticFlag]) -> str | None:
    order = {DiagnosticSeverity.INFO: 1, DiagnosticSeverity.WARNING: 2, DiagnosticSeverity.CRITICAL: 3}
    if not flags:
        return None
    return max(flags, key=lambda flag: order[flag.severity]).severity.value


def _inference_strength(completed_trade_count: float | None, warnings: Sequence[str]) -> str:
    if completed_trade_count is None:
        return "PARTIAL"
    if completed_trade_count < 5 or any("missing" in warning for warning in warnings):
        return "WEAK"
    return "NORMAL"


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(record: Mapping[str, Any], key: str) -> float | None:
    value = record.get(key)
    if isinstance(value, (int, float)) and isfinite(float(value)):
        return float(value)
    return None


def _bool(record: Mapping[str, Any], key: str) -> bool | None:
    value = record.get(key)
    return value if isinstance(value, bool) else None


def _number_or_field(execution: Any, metadata: Mapping[str, Any], key: str) -> float | None:
    value = _field(execution, key)
    if isinstance(value, (int, float)) and isfinite(float(value)):
        return float(value)
    return _number(metadata, key)


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)
