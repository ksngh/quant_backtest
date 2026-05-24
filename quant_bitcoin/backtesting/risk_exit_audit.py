from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any, Mapping, Sequence


def calculate_risk_exit_audit(
    executions: Sequence[Any],
    summary_metadata: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    rows = list(executions or ())
    closing = [row for row in rows if _number(_field(row, "gross_pnl")) is not None or _exit_reason(row)]
    counts: dict[str, int] = defaultdict(int)
    pnl_by_reason: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "net_pnl": 0.0, "r_sum": 0.0, "r_count": 0.0})
    partial_net_pnl = 0.0
    total_net_pnl = 0.0
    target_r_values: list[float] = []
    target_price_distances: list[float] = []
    flags: list[dict[str, object]] = []
    validation = {"critical_count": 0, "warnings": []}
    grouped: dict[tuple[str, ...], dict[str, Any]] = defaultdict(_group_accumulator)
    target_source_grouped: dict[str, dict[str, Any]] = defaultdict(_source_accumulator)
    timing_by_exit_timestamp = _timing_by_exit_timestamp(summary_metadata)
    ambiguous_count = 0
    ambiguous_net_pnl = 0.0
    stop_movement_count = 0
    stop_movement_net_pnl = 0.0
    total_cost = 0.0

    for row in rows:
        metadata = _record(_field(row, "metadata"))
        action_type = str(_field(row, "action_type") or "").upper()
        side = str(_field(row, "position_side") or metadata.get("position_side") or "").upper()
        entry_price = _number(_field(row, "entry_price")) or _number(metadata.get("fill_price")) or _number(metadata.get("entry_price"))
        stop_price = _number(_field(row, "stop_price"))
        risk_per_unit = _number(_field(row, "risk_per_unit"))
        if risk_per_unit is not None and risk_per_unit <= 0:
            _critical(validation, "RISK_PER_UNIT_NOT_POSITIVE", {"risk_per_unit": risk_per_unit})
        if entry_price is not None and stop_price is not None:
            if side == "LONG" and stop_price >= entry_price:
                _critical(validation, "LONG_STOP_NOT_BELOW_FILL", {"entry_price": entry_price, "stop_price": stop_price})
            if side == "SHORT" and stop_price <= entry_price:
                _critical(validation, "SHORT_STOP_NOT_ABOVE_FILL", {"entry_price": entry_price, "stop_price": stop_price})
        if _is_take_profit(row) and entry_price is not None:
            target_price = _number(_field(row, "exit_price")) or _number(_field(row, "price"))
            if target_price is not None:
                if side == "LONG" and target_price <= entry_price:
                    _critical(validation, "LONG_TARGET_NOT_ABOVE_FILL", {"entry_price": entry_price, "target_price": target_price})
                if side == "SHORT" and target_price >= entry_price:
                    _critical(validation, "SHORT_TARGET_NOT_BELOW_FILL", {"entry_price": entry_price, "target_price": target_price})
                target_price_distances.append(abs(target_price - entry_price))
            r_multiple = _number(_field(row, "realized_r_multiple"))
            if r_multiple is not None:
                target_r_values.append(r_multiple)
                minimum = _number(metadata.get("minimum_first_target_r"))
                if minimum is not None and r_multiple < minimum:
                    _critical(validation, "FIRST_TARGET_R_BELOW_MINIMUM", {"realized_r_multiple": r_multiple, "minimum_first_target_r": minimum})

    for row in closing:
        reason = _exit_reason(row) or "UNKNOWN"
        metadata = _record(_field(row, "metadata"))
        exit_metadata = _record(metadata.get("exit_metadata"))
        timing = timing_by_exit_timestamp.get(str(_field(row, "timestamp") or ""))
        counts[reason] += 1
        net_pnl = _number(_field(row, "net_pnl")) or 0.0
        r_value = _number(_field(row, "realized_r_multiple"))
        pnl_by_reason[reason]["count"] += 1.0
        pnl_by_reason[reason]["net_pnl"] += net_pnl
        if r_value is not None:
            pnl_by_reason[reason]["r_sum"] += r_value
            pnl_by_reason[reason]["r_count"] += 1.0
        total_net_pnl += net_pnl
        cost = _number(_field(row, "total_cost")) or _number(metadata.get("total_cost")) or 0.0
        total_cost += cost
        group = grouped[_group_key(row, metadata, exit_metadata)]
        _accumulate_group(group, row, net_pnl, r_value, timing, cost)
        source = str(_field(row, "target_source") or exit_metadata.get("target_source") or metadata.get("target_source") or "NONE").upper()
        _accumulate_group(target_source_grouped[source], row, net_pnl, r_value, timing, cost)
        if bool(exit_metadata.get("ambiguous_stop_target")):
            ambiguous_count += 1
            ambiguous_net_pnl += net_pnl
        if bool(exit_metadata.get("stop_moved_by_break_even_or_trailing")):
            stop_movement_count += 1
            stop_movement_net_pnl += net_pnl
        if "PARTIAL_EXIT" in str(_field(row, "action_type") or "").upper():
            partial_net_pnl += net_pnl

    completed_count = len(closing)
    distribution = {
        reason: {
            "count": count,
            "ratio": None if completed_count == 0 else count / completed_count,
            "net_pnl": pnl_by_reason[reason]["net_pnl"],
            "average_net_pnl": pnl_by_reason[reason]["net_pnl"] / count if count else None,
            "average_r": None if pnl_by_reason[reason]["r_count"] == 0 else pnl_by_reason[reason]["r_sum"] / pnl_by_reason[reason]["r_count"],
        }
        for reason, count in sorted(counts.items())
    }
    stop_ratio = _ratio_for(distribution, ("HARD_STOP", "STOP_LOSS", "TRAILING_STOP", "BREAK_EVEN_STOP"))
    time_ratio = _ratio_for(distribution, ("TIME_STOP",))
    soft_ratio = _ratio_for(distribution, ("SOFT_INVALIDATION",))
    expectancy = _summary_expectancy(summary_metadata)
    if expectancy is not None and expectancy < 0:
        if stop_ratio > 0.5:
            flags.append(_flag("HARD_STOP_DOMINATES_NEGATIVE_EXPECTANCY", stop_ratio, "Hard-stop exits dominate a negative-expectancy run."))
        if soft_ratio > 0.5:
            flags.append(_flag("SOFT_INVALIDATION_DOMINATES_NEGATIVE_EXPECTANCY", soft_ratio, "Soft-invalidation exits dominate a negative-expectancy run."))
    if stop_ratio > 0.5:
        flags.append(_flag("STOP_DOMINANT_PATTERN", stop_ratio, "Stop exits dominate completed exits."))
    if time_ratio > 0.5:
        flags.append(_flag("TIME_STOP_DOMINANT_PATTERN", time_ratio, "Time-stop exits dominate completed exits."))
    if soft_ratio > 0.5:
        flags.append(_flag("SOFT_INVALIDATION_DOMINANT_PATTERN", soft_ratio, "Soft-invalidation exits dominate completed exits."))
    cost_dominance_ratio = None if total_net_pnl == 0 else total_cost / abs(total_net_pnl)
    if cost_dominance_ratio is not None and cost_dominance_ratio > 0.5:
        flags.append(_flag("COST_DOMINANT_PATTERN", cost_dominance_ratio, "Transaction costs are large relative to absolute closing PnL."))

    if completed_count == 0:
        validation["warnings"].append("no closing executions available for risk audit")

    return {
        "schema_version": "risk_exit_audit_v1",
        "completed_exit_count": completed_count,
        "exit_reason_distribution": distribution,
        "dominance": {
            "stop_loss_dominance_ratio": stop_ratio,
            "time_stop_dominance_ratio": time_ratio,
            "soft_invalidation_dominance_ratio": soft_ratio,
        },
        "target_quality": {
            "take_profit_average_r": _average(target_r_values),
            "hard_stop_average_r": _average([_reason_average_r(distribution, reason) for reason in distribution if "STOP" in reason]),
            "first_target_hit_rate": None if completed_count == 0 else _target_hit_count(rows, "TP1") / completed_count,
            "final_target_hit_rate": None if completed_count == 0 else _target_hit_count(rows, "TP3") / completed_count,
            "average_target_distance_r": _average(target_r_values),
            "average_target_distance_price": _average(target_price_distances),
            "by_target_source": _finalize_source_groups(target_source_grouped),
        },
        "outcome_attribution": {
            "schema_version": "risk_exit_outcome_attribution_v1",
            "grouping_fields": (
                "pattern_type",
                "direction",
                "entry_mode",
                "target_source",
                "exit_reason",
                "intrabar_policy",
            ),
            "groups": tuple(_finalize_group(group) for group in grouped.values()),
        },
        "path_attribution": {
            "mfe_mae_source": "summary_metadata.timing_diagnostics.trades",
            "groups_with_mfe_mae": len([group for group in grouped.values() if group["mfe_count"] > 0]),
            "average_mfe_r": _average([group["mfe_sum"] / group["mfe_count"] for group in grouped.values() if group["mfe_count"] > 0]),
            "average_mae_r": _average([group["mae_sum"] / group["mae_count"] for group in grouped.values() if group["mae_count"] > 0]),
        },
        "intrabar_ambiguity": {
            "ambiguous_stop_target_count": ambiguous_count,
            "ambiguous_stop_target_net_pnl": ambiguous_net_pnl,
            "ambiguous_stop_target_pnl_contribution_ratio": None if total_net_pnl == 0 else ambiguous_net_pnl / total_net_pnl,
        },
        "stop_movement": {
            "break_even_or_trailing_stop_count": stop_movement_count,
            "break_even_or_trailing_stop_net_pnl": stop_movement_net_pnl,
            "metadata_source": "exit_metadata.stop_moved_by_break_even_or_trailing",
        },
        "cost_dominance": {
            "total_cost": total_cost,
            "cost_to_abs_closing_pnl_ratio": cost_dominance_ratio,
        },
        "partial_exit": {
            "partial_exit_net_pnl": partial_net_pnl,
            "total_closing_net_pnl": total_net_pnl,
            "partial_exit_pnl_contribution_ratio": None if total_net_pnl == 0 else partial_net_pnl / total_net_pnl,
        },
        "validation": validation,
        "flags": tuple(flags),
        "warnings": tuple(validation["warnings"]),
    }


def _field(row: Any, key: str) -> Any:
    if isinstance(row, Mapping):
        if key in row:
            return row.get(key)
        metadata = row.get("metadata")
        if isinstance(metadata, Mapping):
            return metadata.get(key)
        return None
    direct = getattr(row, key, None)
    if direct is not None:
        return direct
    metadata = getattr(row, "metadata", None)
    if isinstance(metadata, Mapping):
        return metadata.get(key)
    return None


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and isfinite(float(value)):
        return float(value)
    return None


def _exit_reason(row: Any) -> str | None:
    reason = _field(row, "exit_reason") or _record(_field(row, "metadata")).get("exit_reason")
    return str(reason).upper() if reason else None


def _is_take_profit(row: Any) -> bool:
    return "TAKE_PROFIT" in str(_exit_reason(row) or "")


def _critical(validation: dict[str, Any], code: str, evidence: dict[str, object]) -> None:
    validation["critical_count"] += 1
    validation["warnings"].append({"code": code, "severity": "CRITICAL", "evidence": evidence})


def _ratio_for(distribution: Mapping[str, Mapping[str, object]], candidates: tuple[str, ...]) -> float:
    return sum(float(value.get("ratio") or 0.0) for reason, value in distribution.items() if any(candidate in reason for candidate in candidates))


def _summary_expectancy(summary_metadata: Mapping[str, Any] | None) -> float | None:
    attribution = _record(_record(summary_metadata).get("trade_attribution"))
    return _number(_record(attribution.get("trade_metrics")).get("expectancy"))


def _flag(code: str, ratio: float, message: str) -> dict[str, object]:
    return {"code": code, "severity": "WARNING", "message": message, "evidence": {"dominance_ratio": ratio}}


def _average(values: Sequence[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None and isfinite(float(value))]
    return None if not clean else sum(clean) / len(clean)


def _reason_average_r(distribution: Mapping[str, Mapping[str, object]], reason: str) -> float | None:
    return _number(distribution[reason].get("average_r")) if reason in distribution else None


def _target_hit_count(rows: Sequence[Any], target_name: str) -> int:
    return len([row for row in rows if str(_field(row, "target_name") or "").upper() == target_name])


def _timing_by_exit_timestamp(summary_metadata: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    timing = _record(_record(summary_metadata).get("timing_diagnostics"))
    trades = timing.get("trades")
    if not isinstance(trades, Sequence):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for trade in trades:
        if isinstance(trade, Mapping) and trade.get("exit_timestamp") is not None:
            result[str(trade["exit_timestamp"])] = trade
    return result


def _group_key(row: Any, metadata: Mapping[str, Any], exit_metadata: Mapping[str, Any]) -> tuple[str, ...]:
    return (
        str(metadata.get("pattern_type") or "UNKNOWN").upper(),
        str(metadata.get("pattern_direction") or metadata.get("position_side") or _field(row, "position_side") or "UNKNOWN").upper(),
        str(metadata.get("entry_mode") or "UNKNOWN").upper(),
        str(_field(row, "target_source") or exit_metadata.get("target_source") or metadata.get("target_source") or "NONE").upper(),
        _exit_reason(row) or "UNKNOWN",
        str(exit_metadata.get("intrabar_policy") or metadata.get("intrabar_policy") or "UNKNOWN").upper(),
    )


def _group_accumulator() -> dict[str, Any]:
    return {
        "key": None,
        "count": 0,
        "net_pnl": 0.0,
        "cost": 0.0,
        "r_sum": 0.0,
        "r_count": 0,
        "mfe_sum": 0.0,
        "mfe_count": 0,
        "mae_sum": 0.0,
        "mae_count": 0,
        "ambiguous_stop_target_count": 0,
    }


def _source_accumulator() -> dict[str, Any]:
    return _group_accumulator()


def _accumulate_group(
    group: dict[str, Any],
    row: Any,
    net_pnl: float,
    r_value: float | None,
    timing: Mapping[str, Any] | None,
    cost: float,
) -> None:
    metadata = _record(_field(row, "metadata"))
    exit_metadata = _record(metadata.get("exit_metadata"))
    group["key"] = _group_key(row, metadata, exit_metadata)
    group["count"] += 1
    group["net_pnl"] += net_pnl
    group["cost"] += cost
    if r_value is not None:
        group["r_sum"] += r_value
        group["r_count"] += 1
    mfe_r = _number(_record(timing).get("mfe_r"))
    mae_r = _number(_record(timing).get("mae_r"))
    if mfe_r is not None:
        group["mfe_sum"] += mfe_r
        group["mfe_count"] += 1
    if mae_r is not None:
        group["mae_sum"] += mae_r
        group["mae_count"] += 1
    if bool(exit_metadata.get("ambiguous_stop_target")):
        group["ambiguous_stop_target_count"] += 1


def _finalize_group(group: Mapping[str, Any]) -> dict[str, Any]:
    key = tuple(group.get("key") or ("UNKNOWN", "UNKNOWN", "UNKNOWN", "NONE", "UNKNOWN", "UNKNOWN"))
    return {
        "pattern_type": key[0],
        "direction": key[1],
        "entry_mode": key[2],
        "target_source": key[3],
        "exit_reason": key[4],
        "intrabar_policy": key[5],
        "count": int(group["count"]),
        "net_pnl": group["net_pnl"],
        "average_net_pnl": None if group["count"] == 0 else group["net_pnl"] / group["count"],
        "average_realized_r": None if group["r_count"] == 0 else group["r_sum"] / group["r_count"],
        "average_mfe_r": None if group["mfe_count"] == 0 else group["mfe_sum"] / group["mfe_count"],
        "average_mae_r": None if group["mae_count"] == 0 else group["mae_sum"] / group["mae_count"],
        "ambiguous_stop_target_count": int(group["ambiguous_stop_target_count"]),
        "total_cost": group["cost"],
    }


def _finalize_source_groups(groups: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        source: {
            "count": int(group["count"]),
            "net_pnl": group["net_pnl"],
            "average_realized_r": None if group["r_count"] == 0 else group["r_sum"] / group["r_count"],
            "average_mfe_r": None if group["mfe_count"] == 0 else group["mfe_sum"] / group["mfe_count"],
            "average_mae_r": None if group["mae_count"] == 0 else group["mae_sum"] / group["mae_count"],
            "total_cost": group["cost"],
        }
        for source, group in sorted(groups.items())
    }
