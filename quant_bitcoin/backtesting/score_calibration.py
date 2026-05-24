from __future__ import annotations

from math import isfinite
from statistics import median
from typing import Any, Mapping, Sequence


def calculate_score_calibration_diagnostics(
    executions: Sequence[Any] = (),
    summary_metadata: Mapping[str, Any] | None = None,
    *,
    bucket_size: float = 0.2,
    min_trades_per_bucket: int = 3,
) -> dict[str, object]:
    """Evaluate whether heuristic pattern scores line up with realized outcomes."""

    completed_trades = [_trade_row(execution) for execution in executions if _is_completed_trade(execution)]
    scored_trades = [trade for trade in completed_trades if trade["pattern_score"] is not None]
    buckets = _bucket_rows(scored_trades, bucket_size=bucket_size, min_trades_per_bucket=min_trades_per_bucket)
    component_analysis = _component_analysis(scored_trades)
    threshold_sensitivity = _threshold_sensitivity(scored_trades)
    flags = _flags(
        buckets=buckets,
        component_analysis=component_analysis,
        scored_trade_count=len(scored_trades),
        total_completed_trade_count=len(completed_trades),
        min_trades_per_bucket=min_trades_per_bucket,
    )
    warnings = tuple(flag["message"] for flag in flags)
    minimum_score = _configured_minimum_score(summary_metadata)

    return {
        "schema_version": "pattern_score_calibration_v1",
        "score_contract": "pattern_score is a heuristic quality score, not a calibrated probability.",
        "scored_trade_count": len(scored_trades),
        "total_completed_trade_count": len(completed_trades),
        "bucket_size": bucket_size,
        "minimum_pattern_score": minimum_score,
        "buckets": tuple(buckets),
        "component_analysis": component_analysis,
        "threshold_sensitivity": tuple(threshold_sensitivity),
        "flags": tuple(flags),
        "flag_count": len(flags),
        "warnings": warnings,
        "inference_strength": _inference_strength(len(scored_trades), warnings),
    }


def _is_completed_trade(execution: Any) -> bool:
    metadata = _record(_read(execution, "metadata"))
    return _number(_read(execution, "net_pnl", metadata)) is not None or _number(_read(execution, "realized_r_multiple", metadata)) is not None


def _trade_row(execution: Any) -> dict[str, Any]:
    metadata = _record(_read(execution, "metadata"))
    score = _number(_read(execution, "pattern_score", metadata))
    components = _record(_read(execution, "score_components", metadata))
    net_pnl = _number(_read(execution, "net_pnl", metadata))
    realized_r = _number(_read(execution, "realized_r_multiple", metadata))
    return {
        "pattern_score": score,
        "score_bucket": _score_bucket(score),
        "pattern_type": str(_read(execution, "pattern_type", metadata) or "UNKNOWN"),
        "position_side": str(_read(execution, "position_side", metadata) or _read(execution, "position_side") or "UNKNOWN"),
        "net_pnl": net_pnl,
        "realized_r": realized_r,
        "is_win": _is_win(net_pnl, realized_r),
        "score_components": components,
    }


def _bucket_rows(
    trades: Sequence[dict[str, Any]],
    *,
    bucket_size: float,
    min_trades_per_bucket: int,
) -> list[dict[str, object]]:
    if bucket_size <= 0 or bucket_size > 1:
        bucket_size = 0.2
    rows: list[dict[str, object]] = []
    lower = 0.0
    while lower < 1.0:
        upper = min(1.0, lower + bucket_size)
        if upper >= 1.0:
            bucket_trades = [trade for trade in trades if (trade["pattern_score"] or 0.0) >= lower and (trade["pattern_score"] or 0.0) <= upper]
            label = f"[{lower:.1f},1.0]"
        else:
            bucket_trades = [trade for trade in trades if (trade["pattern_score"] or 0.0) >= lower and (trade["pattern_score"] or 0.0) < upper]
            label = f"[{lower:.1f},{upper:.1f})"
        rows.append(_aggregate_row(label, bucket_trades, min_trades_per_bucket=min_trades_per_bucket))
        lower = upper
    return rows


def _aggregate_row(
    label: str,
    trades: Sequence[dict[str, Any]],
    *,
    min_trades_per_bucket: int,
) -> dict[str, object]:
    pnls = [trade["net_pnl"] for trade in trades if trade["net_pnl"] is not None]
    r_values = [trade["realized_r"] for trade in trades if trade["realized_r"] is not None]
    wins = [trade for trade in trades if trade["is_win"] is True]
    profits = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_profit = sum(profits)
    gross_loss = abs(sum(losses))
    pattern_types: dict[str, int] = {}
    for trade in trades:
        pattern_types[str(trade["pattern_type"])] = pattern_types.get(str(trade["pattern_type"]), 0) + 1

    profit_factor = None
    infinite_profit_factor = False
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        infinite_profit_factor = True

    return {
        "bucket": label,
        "trade_count": len(trades),
        "sample_warning": len(trades) > 0 and len(trades) < min_trades_per_bucket,
        "average_score": _mean([trade["pattern_score"] for trade in trades if trade["pattern_score"] is not None]),
        "hit_ratio": None if not trades else len(wins) / len(trades),
        "expectancy": _mean(pnls),
        "average_r": _mean(r_values),
        "median_r": median(r_values) if r_values else None,
        "profit_factor": profit_factor,
        "profit_factor_is_infinite": infinite_profit_factor,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pattern_types": pattern_types,
    }


def _component_analysis(trades: Sequence[dict[str, Any]]) -> dict[str, object]:
    total_component_count = 0
    placeholder_component_count = 0
    by_component: dict[str, dict[str, Any]] = {}

    for trade in trades:
        components = _record(trade.get("score_components"))
        present_keys = set()
        for key, raw_component in components.items():
            component = _record(raw_component)
            present_keys.add(str(key))
            total_component_count += 1
            placeholder = _is_placeholder_component(component)
            if placeholder:
                placeholder_component_count += 1
            entry = by_component.setdefault(
                str(key),
                {
                    "component": str(key),
                    "present_count": 0,
                    "placeholder_count": 0,
                    "present_r_values": [],
                    "absent_r_values": [],
                    "weighted_scores": [],
                    "sources": {},
                },
            )
            entry["present_count"] += 1
            entry["placeholder_count"] += 1 if placeholder else 0
            if trade.get("realized_r") is not None:
                entry["present_r_values"].append(trade["realized_r"])
            weighted_score = _number(component.get("weighted_score"))
            if weighted_score is not None:
                entry["weighted_scores"].append(weighted_score)
            source = str(component.get("source") or "UNKNOWN")
            entry["sources"][source] = entry["sources"].get(source, 0) + 1

        for key, entry in by_component.items():
            if key not in present_keys and trade.get("realized_r") is not None:
                entry["absent_r_values"].append(trade["realized_r"])

    components: list[dict[str, object]] = []
    for key in sorted(by_component):
        entry = by_component[key]
        present_average = _mean(entry["present_r_values"])
        absent_average = _mean(entry["absent_r_values"])
        components.append(
            {
                "component": entry["component"],
                "present_count": entry["present_count"],
                "placeholder_count": entry["placeholder_count"],
                "placeholder_rate": None if entry["present_count"] == 0 else entry["placeholder_count"] / entry["present_count"],
                "average_weighted_score": _mean(entry["weighted_scores"]),
                "average_r_when_present": present_average,
                "average_r_when_absent": absent_average,
                "ablation_delta_r": None if present_average is None or absent_average is None else present_average - absent_average,
                "sources": entry["sources"],
            }
        )

    placeholder_rate = None if total_component_count == 0 else placeholder_component_count / total_component_count
    return {
        "total_component_count": total_component_count,
        "placeholder_component_count": placeholder_component_count,
        "placeholder_component_rate": placeholder_rate,
        "components": tuple(components),
    }


def _threshold_sensitivity(trades: Sequence[dict[str, Any]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for threshold in (0.0, 0.2, 0.4, 0.6, 0.8):
        selected = [trade for trade in trades if (trade["pattern_score"] or 0.0) >= threshold]
        aggregate = _aggregate_row(f">={threshold:.1f}", selected, min_trades_per_bucket=1)
        rows.append(
            {
                "minimum_pattern_score": threshold,
                "trade_count": aggregate["trade_count"],
                "hit_ratio": aggregate["hit_ratio"],
                "expectancy": aggregate["expectancy"],
                "average_r": aggregate["average_r"],
                "median_r": aggregate["median_r"],
                "profit_factor": aggregate["profit_factor"],
                "profit_factor_is_infinite": aggregate["profit_factor_is_infinite"],
            }
        )
    return rows


def _flags(
    *,
    buckets: Sequence[Mapping[str, Any]],
    component_analysis: Mapping[str, Any],
    scored_trade_count: int,
    total_completed_trade_count: int,
    min_trades_per_bucket: int,
) -> list[dict[str, object]]:
    flags: list[dict[str, object]] = []
    if scored_trade_count == 0:
        flags.append(
            _flag(
                "MISSING_SCORE_METADATA",
                "WARNING",
                "No completed trade has pattern_score metadata.",
                {"total_completed_trade_count": total_completed_trade_count},
            )
        )
        return flags

    small_buckets = [bucket["bucket"] for bucket in buckets if bucket["trade_count"] and bucket["trade_count"] < min_trades_per_bucket]
    if small_buckets:
        flags.append(
            _flag(
                "SCORE_BUCKET_SAMPLE_TOO_SMALL",
                "INFO",
                "One or more score buckets has too few completed trades for strong inference.",
                {"buckets": tuple(small_buckets), "min_trades_per_bucket": min_trades_per_bucket},
            )
        )

    metric_values = [
        bucket["average_r"] if bucket["average_r"] is not None else bucket["expectancy"]
        for bucket in buckets
        if bucket["trade_count"] and (bucket["average_r"] is not None or bucket["expectancy"] is not None)
    ]
    if len(metric_values) >= 2 and any(metric_values[index] < metric_values[index - 1] for index in range(1, len(metric_values))):
        flags.append(
            _flag(
                "NO_MONOTONIC_SCORE_IMPROVEMENT",
                "WARNING",
                "Higher score buckets do not show monotonic realized outcome improvement.",
                {"bucket_metric_values": tuple(metric_values)},
            )
        )

    placeholder_rate = _number(component_analysis.get("placeholder_component_rate"))
    if placeholder_rate is not None and placeholder_rate >= 0.5:
        flags.append(
            _flag(
                "PLACEHOLDER_COMPONENT_DOMINATES_SCORE",
                "WARNING",
                "Placeholder score components account for at least half of observed component metadata.",
                {"placeholder_component_rate": placeholder_rate},
            )
        )

    high_buckets = [bucket for bucket in buckets if str(bucket.get("bucket", "")).startswith("[0.8")]
    high_bucket = high_buckets[0] if high_buckets else None
    if high_bucket and high_bucket["trade_count"]:
        average_r = _number(high_bucket.get("average_r"))
        expectancy = _number(high_bucket.get("expectancy"))
        if (average_r is not None and average_r < 0) or (expectancy is not None and expectancy < 0):
            flags.append(
                _flag(
                    "HIGH_SCORE_NEGATIVE_EXPECTANCY",
                    "WARNING",
                    "The highest score bucket has negative realized expectancy or average R.",
                    {"bucket": high_bucket.get("bucket"), "expectancy": expectancy, "average_r": average_r},
                )
            )
    return flags


def _flag(code: str, severity: str, message: str, evidence: Mapping[str, Any]) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "category": "score_calibration",
        "message": message,
        "evidence": dict(evidence),
        "suggested_next_analysis": "Compare pattern score thresholds against walk-forward/OOS validation before changing strategy settings.",
    }


def _configured_minimum_score(summary_metadata: Mapping[str, Any] | None) -> float | None:
    metadata = _record(summary_metadata)
    candidates = (
        _read(metadata, "minimum_pattern_score"),
        _read(_record(metadata.get("strategy_parameters")), "minimum_pattern_score"),
        _read(_record(metadata.get("workflow_settings")), "minimum_pattern_score"),
    )
    for candidate in candidates:
        value = _number(candidate)
        if value is not None:
            return value
    return None


def _inference_strength(scored_trade_count: int, warnings: Sequence[str]) -> str:
    if scored_trade_count == 0:
        return "PARTIAL"
    if scored_trade_count < 10 or warnings:
        return "WEAK"
    return "NORMAL"


def _is_win(net_pnl: float | None, realized_r: float | None) -> bool | None:
    if net_pnl is not None:
        return net_pnl > 0
    if realized_r is not None:
        return realized_r > 0
    return None


def _score_bucket(score: float | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 0.8:
        return "HIGH"
    if score >= 0.6:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "NONE"


def _is_placeholder_component(component: Mapping[str, Any]) -> bool:
    if component.get("is_placeholder") is True:
        return True
    text = " ".join(
        str(value).lower()
        for key, value in component.items()
        if key in {"source", "description", "limitation", "limitations", "reason"}
    )
    return "placeholder" in text


def _read(source: Any, key: str, fallback: Mapping[str, Any] | None = None) -> Any:
    if isinstance(source, Mapping) and key in source:
        return source.get(key)
    if source is not None and hasattr(source, key):
        return getattr(source, key)
    if fallback is not None:
        return fallback.get(key)
    return None


def _record(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric if isfinite(numeric) else None
    return None


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)
