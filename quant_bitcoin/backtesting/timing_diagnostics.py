from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Mapping, Sequence


def calculate_trade_timing_diagnostics(
    executions: Sequence[Any],
    price_points: Sequence[Any],
    *,
    divergence_threshold_pct: float = 0.005,
    money_left_threshold_r: float = 0.5,
    immediate_adverse_bars: int = 2,
) -> dict[str, object]:
    """Calculate deterministic entry/exit path diagnostics from saved data."""

    points = [_price_point(point) for point in _iter_price_points(price_points)]
    points = [point for point in points if point is not None]
    high_low_count = len([point for point in points if point["has_high_low"]])
    if points and high_low_count == len(points):
        mode = "HIGH_LOW"
    elif points and high_low_count:
        mode = "MIXED_HIGH_LOW_CLOSE_APPROXIMATION"
    else:
        mode = "CLOSE_ONLY_APPROXIMATION"
    warnings: list[str] = []
    if mode != "HIGH_LOW":
        warnings.append("high/low path unavailable; MFE/MAE uses close-only approximation")
    if not points:
        warnings.append("price path unavailable")

    trades: list[dict[str, object]] = []
    flags: list[dict[str, object]] = []
    for lifecycle in _completed_lifecycles(executions):
        trade = _trade_timing(lifecycle, points)
        if trade is None:
            warnings.append("trade could not be matched to price path")
            continue
        trades.append(trade)
        flags.extend(_trade_flags(trade, divergence_threshold_pct, money_left_threshold_r, immediate_adverse_bars))

    return {
        "schema_version": "trade_timing_diagnostics_v1",
        "path_mode": mode,
        "trade_count": len(trades),
        "completed_trade_count": len(trades),
        "aggregate": _aggregate(trades),
        "trades": tuple(trades),
        "flags": tuple(flags),
        "flag_count": len(flags),
        "warnings": tuple(warnings),
        "partial_exit_policy": "partial exits are approximated as one entry-to-final-exit lifecycle; MFE/MAE is measured over the full lifecycle window",
    }


def _completed_lifecycles(executions: Sequence[Any]) -> list[dict[str, Any]]:
    lifecycles: list[dict[str, Any]] = []
    open_trade: dict[str, Any] | None = None
    for execution in executions:
        action = _action_type(execution)
        quantity = _number(_field(execution, "quantity"))
        if quantity is not None and quantity <= 0:
            continue
        if action in ("ENTER_LONG", "ENTER_SHORT"):
            open_trade = {
                "entry": execution,
                "exits": [],
                "side": "LONG" if action == "ENTER_LONG" else "SHORT",
            }
            continue
        if open_trade is None or action not in ("PARTIAL_EXIT_LONG", "PARTIAL_EXIT_SHORT", "EXIT_LONG", "EXIT_SHORT"):
            continue
        open_trade["exits"].append(execution)
        position_after = _number(_field(execution, "position_after"))
        if action in ("EXIT_LONG", "EXIT_SHORT") or position_after == 0:
            lifecycles.append(open_trade)
            open_trade = None
    return lifecycles


def _trade_timing(lifecycle: Mapping[str, Any], points: Sequence[dict[str, Any]]) -> dict[str, object] | None:
    entry = lifecycle["entry"]
    exits = lifecycle["exits"]
    if not exits:
        return None
    final_exit = exits[-1]
    side = str(lifecycle["side"])
    entry_ts = _timestamp(entry)
    exit_ts = _timestamp(final_exit)
    entry_idx = _find_point_index(points, entry_ts)
    exit_idx = _find_point_index(points, exit_ts)
    if entry_idx is None:
        return None
    if exit_idx is None or exit_idx < entry_idx:
        exit_idx = len(points) - 1
    window = list(points[entry_idx : exit_idx + 1])
    if not window:
        return None

    entry_price = _execution_price(entry)
    exit_price = _execution_price(final_exit)
    if entry_price is None:
        return None
    quantity = _number(_field(entry, "quantity")) or 0.0
    risk_per_unit = _metadata_number(entry, "risk_per_unit")
    realized_r = _metadata_number(final_exit, "realized_r_multiple")
    if realized_r is None:
        realized_r = _number(_field(final_exit, "realized_r_multiple"))

    favorable_values: list[float] = []
    adverse_values: list[float] = []
    close_values: list[float] = []
    for point in window:
        high = float(point["high"])
        low = float(point["low"])
        close = float(point["close"])
        close_values.append(close)
        if side == "LONG":
            favorable_values.append(high - entry_price)
            adverse_values.append(entry_price - low)
        else:
            favorable_values.append(entry_price - low)
            adverse_values.append(high - entry_price)

    mfe_price = max(favorable_values)
    mae_price = max(adverse_values)
    bars_to_mfe = favorable_values.index(mfe_price)
    bars_to_mae = adverse_values.index(mae_price)
    bars_to_first_favorable_close = _bars_to_first_favorable_close(side, entry_price, close_values)
    entry_metadata = _record(_field(entry, "metadata"))
    exit_metadata = _record(_field(final_exit, "metadata"))
    nested_exit_metadata = _record(exit_metadata.get("exit_metadata"))
    reference = _metadata_number(entry, "entry_reference")
    confirmation_close = _metadata_number(entry, "confirmation_close")
    exit_reason = _field(final_exit, "exit_reason") or exit_metadata.get("exit_reason")
    return {
        "entry_timestamp": entry_ts,
        "exit_timestamp": exit_ts,
        "position_side": side,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "mfe_price": mfe_price,
        "mae_price": mae_price,
        "mfe_quote_pnl": mfe_price * quantity,
        "mae_quote_pnl": mae_price * quantity,
        "mfe_r": _safe_div(mfe_price, risk_per_unit),
        "mae_r": _safe_div(mae_price, risk_per_unit),
        "realized_r": realized_r,
        "bars_to_mfe": bars_to_mfe,
        "bars_to_mae": bars_to_mae,
        "bars_to_first_favorable_close": bars_to_first_favorable_close,
        "bars_to_exit": len(window) - 1,
        "exit_reason": exit_reason,
        "pattern_type": entry_metadata.get("pattern_type") or exit_metadata.get("pattern_type"),
        "pattern_direction": entry_metadata.get("pattern_direction") or exit_metadata.get("pattern_direction"),
        "entry_mode": entry_metadata.get("entry_mode") or exit_metadata.get("entry_mode"),
        "target_source": exit_metadata.get("target_source") or nested_exit_metadata.get("target_source"),
        "intrabar_policy": nested_exit_metadata.get("intrabar_policy") or exit_metadata.get("intrabar_policy"),
        "ambiguous_stop_target": bool(nested_exit_metadata.get("ambiguous_stop_target")),
        "stop_moved_by_break_even_or_trailing": bool(nested_exit_metadata.get("stop_moved_by_break_even_or_trailing")),
        "bars_to_stop_loss": len(window) - 1 if _exit_reason_is(exit_reason, ("HARD_STOP", "STOP_LOSS", "TRAILING_STOP", "BREAK_EVEN_STOP")) else None,
        "bars_to_take_profit": len(window) - 1 if _exit_reason_is(exit_reason, ("TAKE_PROFIT", "TARGET", "TARGET_1", "TARGET_2")) else None,
        "bars_to_soft_invalidation": len(window) - 1 if _exit_reason_is(exit_reason, ("SOFT_INVALIDATION",)) else None,
        "bars_to_time_stop": len(window) - 1 if _exit_reason_is(exit_reason, ("TIME_STOP",)) else None,
        "entry_fill_reference_distance": None if reference is None else entry_price - reference,
        "entry_fill_reference_distance_pct": None if reference in (None, 0) else (entry_price - reference) / reference,
        "entry_fill_confirmation_close_distance": None if confirmation_close is None else entry_price - confirmation_close,
        "entry_fill_zone_midpoint_distance": _zone_distance(entry_price, entry_metadata, ("zone_mid", "zone_midpoint", "pattern_midpoint", "midpoint")),
        "entry_fill_zone_boundary_distance": _zone_distance(entry_price, entry_metadata, ("zone_low", "zone_high", "pattern_low", "pattern_high", "lower_boundary_value", "upper_boundary_value")),
    }


def _trade_flags(
    trade: Mapping[str, object],
    divergence_threshold_pct: float,
    money_left_threshold_r: float,
    immediate_adverse_bars: int,
) -> list[dict[str, object]]:
    flags: list[dict[str, object]] = []
    divergence_pct = trade.get("entry_fill_reference_distance_pct")
    side = str(trade.get("position_side") or "").upper()
    is_chasing = False
    if isinstance(divergence_pct, (int, float)):
        value = float(divergence_pct)
        is_chasing = (side == "LONG" and value > divergence_threshold_pct) or (side == "SHORT" and value < -divergence_threshold_pct)
        if not side:
            is_chasing = abs(value) > divergence_threshold_pct
    if is_chasing:
        flags.append(
            {
                "code": "ENTRY_WAS_LATE_CHASING",
                "severity": "WARNING",
                "message": "Entry fill is materially away from the pattern reference.",
                "evidence": {"entry_fill_reference_distance_pct": divergence_pct, "position_side": side or None},
            }
        )
    mfe_r = trade.get("mfe_r")
    realized_r = trade.get("realized_r")
    if isinstance(mfe_r, (int, float)) and isinstance(realized_r, (int, float)) and float(mfe_r) - float(realized_r) > money_left_threshold_r:
        flags.append(
            {
                "code": "EXIT_LEFT_MONEY_ON_TABLE",
                "severity": "WARNING",
                "message": "Maximum favorable excursion materially exceeded realized R.",
                "evidence": {"mfe_r": mfe_r, "realized_r": realized_r},
            }
        )
    mae_r = trade.get("mae_r")
    bars_to_mae = trade.get("bars_to_mae")
    if isinstance(mae_r, (int, float)) and isinstance(bars_to_mae, (int, float)) and float(mae_r) >= 0.5 and int(bars_to_mae) <= immediate_adverse_bars:
        flags.append(
            {
                "code": "IMMEDIATE_ADVERSE_EXCURSION",
                "severity": "WARNING",
                "message": "The worst adverse excursion appeared almost immediately after entry.",
                "evidence": {"mae_r": mae_r, "bars_to_mae": bars_to_mae},
            }
        )
    return flags


def _iter_price_points(price_points: Any) -> Iterable[Any]:
    if hasattr(price_points, "to_dict"):
        try:
            return price_points.to_dict("records")
        except TypeError:
            pass
    return price_points or ()


def _price_point(value: Any) -> dict[str, object] | None:
    timestamp = _field(value, "timestamp") or _field(value, "candle_open_time")
    close = _number(_field(value, "close")) or _number(_field(value, "close_price"))
    if timestamp is None or close is None:
        return None
    high = _number(_field(value, "high"))
    low = _number(_field(value, "low"))
    return {
        "timestamp": _ts_key(timestamp),
        "high": high if high is not None else close,
        "low": low if low is not None else close,
        "close": close,
        "has_high_low": high is not None and low is not None,
    }


def _find_point_index(points: Sequence[Mapping[str, Any]], timestamp: str | None) -> int | None:
    if timestamp is None:
        return None
    for index, point in enumerate(points):
        if point.get("timestamp") == timestamp:
            return index
    return None


def _bars_to_first_favorable_close(side: str, entry_price: float, closes: Sequence[float]) -> int | None:
    for index, close in enumerate(closes):
        if side == "LONG" and close > entry_price:
            return index
        if side == "SHORT" and close < entry_price:
            return index
    return None


def _action_type(execution: Any) -> str:
    raw = _field(execution, "action_type") or _field(execution, "position_signal") or _field(execution, "signal")
    action = str(raw or "").upper()
    return {
        "LONG_ENTRY": "ENTER_LONG",
        "SHORT_ENTRY": "ENTER_SHORT",
        "LONG_EXIT": "EXIT_LONG",
        "SHORT_EXIT": "EXIT_SHORT",
        "LONG_PARTIAL_EXIT": "PARTIAL_EXIT_LONG",
        "SHORT_PARTIAL_EXIT": "PARTIAL_EXIT_SHORT",
    }.get(action, action)


def _execution_price(execution: Any) -> float | None:
    return _number(_field(execution, "raw_price")) or _number(_field(execution, "fill_price")) or _number(_field(execution, "price"))


def _metadata_number(execution: Any, key: str) -> float | None:
    return _number(_record(_field(execution, "metadata")).get(key))


def _zone_distance(entry_price: float, metadata: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    candidates = [_number(metadata.get(key)) for key in keys]
    candidates = [value for value in candidates if value is not None]
    if not candidates:
        return None
    return min((entry_price - value for value in candidates), key=abs)


def _aggregate(trades: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "average_mfe_r": _average(_numeric_values(trades, "mfe_r")),
        "average_mae_r": _average(_numeric_values(trades, "mae_r")),
        "average_realized_r": _average(_numeric_values(trades, "realized_r")),
        "average_bars_to_mfe": _average(_numeric_values(trades, "bars_to_mfe")),
        "average_bars_to_mae": _average(_numeric_values(trades, "bars_to_mae")),
    }


def _numeric_values(rows: Sequence[Mapping[str, object]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)) and isfinite(float(value)):
            values.append(float(value))
    return values


def _average(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _exit_reason_is(reason: Any, candidates: tuple[str, ...]) -> bool:
    normalized = str(reason or "").upper()
    return any(candidate in normalized for candidate in candidates)


def _safe_div(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _timestamp(execution: Any) -> str | None:
    value = _field(execution, "timestamp") or _field(execution, "candle_open_time")
    return None if value is None else _ts_key(value)


def _ts_key(value: Any) -> str:
    return value.isoformat().replace("+00:00", "Z") if hasattr(value, "isoformat") else str(value)


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and isfinite(float(value)):
        return float(value)
    return None


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        if key in value:
            return value.get(key)
        metadata = value.get("metadata")
        if isinstance(metadata, Mapping):
            return metadata.get(key)
        return None
    direct = getattr(value, key, None)
    if direct is not None:
        return direct
    metadata = getattr(value, "metadata", None)
    if isinstance(metadata, Mapping):
        return metadata.get(key)
    return None
