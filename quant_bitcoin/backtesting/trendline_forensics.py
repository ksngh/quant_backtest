from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType

TRENDLINE_FALSE_BREAKOUT_SCHEMA_VERSION = "trendline_false_breakout_forensics_v1"


def build_trendline_false_breakout_forensics(
    actions: Sequence[StrategyAction],
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    lookahead_bars: int = 5,
) -> dict[str, Any]:
    if lookahead_bars < 1:
        raise ValueError("lookahead_bars must be at least 1")
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    records = [
        record
        for action in actions
        if (record := _record_for_action(action, frame, lookahead_bars)) is not None
    ]
    return {
        "schema_version": TRENDLINE_FALSE_BREAKOUT_SCHEMA_VERSION,
        "scope": "offline_research_only",
        "lookahead_bars": lookahead_bars,
        "event_count": len(records),
        "outcomes": _outcome_counts(records),
        "groups": {
            "touch_count": _group(records, "touch_count_group"),
            "slope": _group(records, "slope_group"),
            "break_distance_atr": _group(records, "break_distance_atr_group"),
            "volume_ratio": _group(records, "volume_ratio_group"),
            "displacement_confirmed": _group(records, "displacement_confirmed_group"),
            "pivot_confirmation_delay": _group(records, "pivot_confirmation_delay_group"),
        },
        "records": records,
    }


def _record_for_action(
    action: StrategyAction,
    candles: pd.DataFrame,
    lookahead_bars: int,
) -> dict[str, Any] | None:
    metadata = action.metadata or {}
    if _pattern_key(metadata.get("pattern_type")) != "TRENDLINE_BREAK":
        return None
    if action.action_type not in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}:
        return None
    side = str(metadata.get("position_side") or "").upper()
    if side not in {"LONG", "SHORT"}:
        return None
    timestamp = _timestamp(getattr(action, "timestamp", None))
    path = _future_candles(candles, timestamp, lookahead_bars)
    entry = _number(metadata.get("fill_price") or getattr(action, "requested_price", None) or metadata.get("confirmation_close"))
    risk = _number(metadata.get("risk_per_unit") or metadata.get("fill_adjusted_risk_per_unit"))
    trendline = _number(metadata.get("trendline_value"))
    classification = _classify_path(path, side, trendline, entry, risk)
    pivot_metadata = metadata.get("pivot_metadata") if isinstance(metadata.get("pivot_metadata"), dict) else {}
    return {
        "event_id": metadata.get("event_id") or metadata.get("pattern_event_id"),
        "position_side": side,
        "outcome": classification["outcome"],
        "bars_to_reentry": classification["bars_to_reentry"],
        "max_favorable_r_before_reentry": classification["max_favorable_r_before_reentry"],
        "realized_r_after_reentry": classification["realized_r_after_reentry"],
        "touch_count": metadata.get("touch_count"),
        "touch_count_group": str(metadata.get("touch_count") or "UNKNOWN"),
        "slope_group": _signed_group(metadata.get("trendline_slope")),
        "break_distance_atr_group": _numeric_group(metadata.get("break_distance_atr")),
        "volume_ratio_group": _numeric_group(metadata.get("volume_ratio")),
        "displacement_confirmed_group": str(bool(metadata.get("displacement_confirmed"))),
        "pivot_confirmation_delay_group": str(pivot_metadata.get("confirmation_delay", "UNKNOWN")),
    }


def _classify_path(
    path: pd.DataFrame,
    side: str,
    trendline: float | None,
    entry: float | None,
    risk: float | None,
) -> dict[str, Any]:
    if path.empty or trendline is None:
        return {
            "outcome": "no_follow_through",
            "bars_to_reentry": None,
            "max_favorable_r_before_reentry": None,
            "realized_r_after_reentry": None,
        }
    reentry_index = _reentry_index(path, side, trendline)
    before = path if reentry_index is None else path.iloc[: reentry_index + 1]
    max_favorable_r = _max_favorable_r(before, side, entry, risk)
    realized_after = (
        None
        if reentry_index is None
        else _realized_r_after(path.iloc[reentry_index:], side, entry, risk)
    )
    if reentry_index is not None:
        outcome = "failed_breakout" if (max_favorable_r is None or max_favorable_r < 0.5) else "reentered_trendline"
    elif _first_close_follows_through(path, side, trendline) and (max_favorable_r is not None and max_favorable_r >= 1.0):
        outcome = "immediate_follow_through"
    elif _chopped_inside(path, side, trendline):
        outcome = "chopped_inside"
    else:
        outcome = "no_follow_through"
    return {
        "outcome": outcome,
        "bars_to_reentry": None if reentry_index is None else reentry_index + 1,
        "max_favorable_r_before_reentry": max_favorable_r,
        "realized_r_after_reentry": realized_after,
    }


def _reentry_index(path: pd.DataFrame, side: str, trendline: float) -> int | None:
    for index, candle in path.reset_index(drop=True).iterrows():
        close = float(candle["close"])
        if side == "LONG" and close < trendline:
            return int(index)
        if side == "SHORT" and close > trendline:
            return int(index)
    return None


def _max_favorable_r(path: pd.DataFrame, side: str, entry: float | None, risk: float | None) -> float | None:
    if path.empty or entry is None or risk is None or risk <= 0:
        return None
    if side == "LONG":
        move = float(path["high"].max()) - entry
    else:
        move = entry - float(path["low"].min())
    return max(0.0, move / risk)


def _realized_r_after(path: pd.DataFrame, side: str, entry: float | None, risk: float | None) -> float | None:
    if path.empty or entry is None or risk is None or risk <= 0:
        return None
    close = float(path.iloc[-1]["close"])
    return (close - entry) / risk if side == "LONG" else (entry - close) / risk


def _first_close_follows_through(path: pd.DataFrame, side: str, trendline: float) -> bool:
    close = float(path.iloc[0]["close"])
    return close > trendline if side == "LONG" else close < trendline


def _chopped_inside(path: pd.DataFrame, side: str, trendline: float) -> bool:
    closes = [float(value) for value in path["close"]]
    favorable = [close > trendline if side == "LONG" else close < trendline for close in closes]
    return any(favorable) and not all(favorable)


def _future_candles(candles: pd.DataFrame, timestamp: pd.Timestamp | None, lookahead_bars: int) -> pd.DataFrame:
    if timestamp is None or candles.empty or "timestamp" not in candles.columns:
        return candles.iloc[0:0]
    return candles[candles["timestamp"] >= timestamp].head(lookahead_bars).reset_index(drop=True)


def _outcome_counts(records: Sequence[dict[str, Any]]) -> dict[str, int]:
    outcomes = ("immediate_follow_through", "reentered_trendline", "failed_breakout", "chopped_inside", "no_follow_through")
    return {outcome: len([record for record in records if record["outcome"] == outcome]) for outcome in outcomes}


def _group(records: Sequence[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    values = sorted({str(record.get(key, "UNKNOWN")) for record in records})
    return {
        value: {
            "event_count": len(group),
            "outcomes": _outcome_counts(group),
            "average_bars_to_reentry": _average(record["bars_to_reentry"] for record in group),
            "average_max_favorable_r_before_reentry": _average(record["max_favorable_r_before_reentry"] for record in group),
            "average_realized_r_after_reentry": _average(record["realized_r_after_reentry"] for record in group),
        }
        for value in values
        for group in ([record for record in records if str(record.get(key, "UNKNOWN")) == value],)
    }


def _numeric_group(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "UNKNOWN"
    if number < 0.5:
        return "LT_0_5"
    if number < 1.0:
        return "0_5_TO_1"
    return "GTE_1"


def _signed_group(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "UNKNOWN"
    if number > 0:
        return "POSITIVE"
    if number < 0:
        return "NEGATIVE"
    return "FLAT"


def _average(values: Any) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return None if not numeric else sum(numeric) / len(numeric)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def _timestamp(value: Any) -> pd.Timestamp | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _pattern_key(value: Any) -> str:
    text = str(value or "").upper()
    if text.endswith("_PATTERN"):
        text = text.removesuffix("_PATTERN")
    return text
