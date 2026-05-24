from __future__ import annotations

from typing import Any, Mapping, Sequence

import pandas as pd

from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType

RETEST_OPPORTUNITY_SCHEMA_VERSION = "fvg_ob_retest_opportunity_v1"

_SUPPORTED_PATTERNS = {"FAIR_VALUE_GAP", "ORDER_BLOCK"}


def build_fvg_ob_retest_opportunity_report(
    actions: Sequence[StrategyAction],
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    regime_by_timestamp: Mapping[Any, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    records = [
        _record_for_action(action, frame, regime_by_timestamp or {})
        for action in actions
        if _supported_action(action)
    ]
    records = [record for record in records if record is not None]
    by_pattern = {
        pattern: _section([record for record in records if record["pattern_type"] == pattern])
        for pattern in sorted(_SUPPORTED_PATTERNS)
    }
    return {
        "schema_version": RETEST_OPPORTUNITY_SCHEMA_VERSION,
        "scope": "offline_research_only",
        "patterns": by_pattern,
        "overall": _section(records),
    }


def _supported_action(action: StrategyAction) -> bool:
    metadata = action.metadata or {}
    pattern = _pattern_key(metadata.get("pattern_type"))
    if pattern not in _SUPPORTED_PATTERNS:
        return False
    entry_policy = metadata.get("pattern_entry_policy")
    if not isinstance(entry_policy, dict):
        return False
    return action.action_type in {
        StrategyActionType.ENTER_LONG,
        StrategyActionType.ENTER_SHORT,
        StrategyActionType.SKIP,
    }


def _record_for_action(
    action: StrategyAction,
    candles: pd.DataFrame,
    regime_by_timestamp: Mapping[Any, Mapping[str, Any]],
) -> dict[str, Any] | None:
    metadata = action.metadata or {}
    policy = metadata.get("pattern_entry_policy")
    if not isinstance(policy, dict):
        return None
    pattern = _pattern_key(metadata.get("pattern_type"))
    side = str(metadata.get("position_side") or "").upper()
    if side not in {"LONG", "SHORT"}:
        return None
    timestamp = _timestamp(getattr(action, "timestamp", None))
    future = _future_candles(candles, timestamp)
    entry_mode = str(policy.get("entry_mode") or metadata.get("entry_mode") or "UNKNOWN")
    is_filled = action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}
    is_not_filled = action.action_type == StrategyActionType.SKIP and getattr(action, "reason", None) == "ENTRY_NOT_FILLED"
    confirmation_close = _number(metadata.get("confirmation_close"))
    target_reference = _number(metadata.get("target_reference") or metadata.get("event_target_reference"))
    fill_price = _number(metadata.get("fill_price") or getattr(action, "requested_price", None))
    reference_price = fill_price if fill_price is not None else confirmation_close
    mfe = _favorable_move(future, side, reference_price)
    adverse = _adverse_move(future, side, fill_price) if is_filled else None
    market_target_hit = (
        _target_touched(future, side, target_reference)
        if is_not_filled and target_reference is not None
        else None
    )
    regime = regime_by_timestamp.get(timestamp, {})
    return {
        "pattern_type": pattern,
        "pattern_direction": str(metadata.get("pattern_direction") or "UNKNOWN"),
        "position_side": side,
        "entry_mode": entry_mode,
        "entry_style": str(policy.get("entry_style") or "UNKNOWN"),
        "filled": is_filled,
        "not_filled": is_not_filled,
        "bars_waited": _number(metadata.get("bars_waited")),
        "max_favorable_move": mfe,
        "adverse_excursion_after_fill": adverse,
        "missed_move": is_not_filled and mfe is not None and mfe > 0,
        "market_entry_target_hit": market_target_hit,
        "pattern_direction_group": str(metadata.get("pattern_direction") or "UNKNOWN"),
        "zone_size_atr_group": _zone_size_group(metadata),
        "volume_ratio_group": _numeric_group(metadata.get("volume_ratio")),
        "displacement_strength_group": _numeric_group(
            metadata.get("displacement_range_atr") or metadata.get("break_distance_atr")
        ),
        "market_regime": str(regime.get("market_regime", "UNKNOWN")),
    }


def _section(records: Sequence[dict[str, Any]], *, include_groups: bool = True) -> dict[str, Any]:
    section = {
        "signal_count": len(records),
        "filled_count": len([record for record in records if record["filled"]]),
        "not_filled_count": len([record for record in records if record["not_filled"]]),
        "missed_trade_count": len([record for record in records if record["missed_move"]]),
        "market_entry_target_hit_count": len([record for record in records if record["market_entry_target_hit"] is True]),
        "fill_rate": _ratio(len([record for record in records if record["filled"]]), len(records)),
        "average_bars_waited": _average(record["bars_waited"] for record in records),
        "average_missed_mfe": _average(
            record["max_favorable_move"] for record in records if record["not_filled"]
        ),
        "average_adverse_excursion_after_fill": _average(
            record["adverse_excursion_after_fill"] for record in records if record["filled"]
        ),
    }
    if include_groups:
        section["groups"] = {
            "pattern_direction": _group(records, "pattern_direction_group"),
            "zone_size_atr": _group(records, "zone_size_atr_group"),
            "volume_ratio": _group(records, "volume_ratio_group"),
            "displacement_strength": _group(records, "displacement_strength_group"),
            "market_regime": _group(records, "market_regime"),
            "entry_mode": _group(records, "entry_mode"),
        }
    return section


def _group(records: Sequence[dict[str, Any]], key: str) -> dict[str, Any]:
    values = sorted({str(record.get(key, "UNKNOWN")) for record in records})
    return {
        value: _section(
            [record for record in records if str(record.get(key, "UNKNOWN")) == value],
            include_groups=False,
        )
        for value in values
    }


def _future_candles(candles: pd.DataFrame, timestamp: pd.Timestamp | None) -> pd.DataFrame:
    if timestamp is None or candles.empty or "timestamp" not in candles.columns:
        return candles.iloc[0:0]
    return candles[candles["timestamp"] >= timestamp].reset_index(drop=True)


def _favorable_move(candles: pd.DataFrame, side: str, reference_price: float | None) -> float | None:
    if reference_price is None or candles.empty:
        return None
    if side == "LONG":
        return max(0.0, float(candles["high"].max()) - reference_price)
    return max(0.0, reference_price - float(candles["low"].min()))


def _adverse_move(candles: pd.DataFrame, side: str, fill_price: float | None) -> float | None:
    if fill_price is None or candles.empty:
        return None
    if side == "LONG":
        return max(0.0, fill_price - float(candles["low"].min()))
    return max(0.0, float(candles["high"].max()) - fill_price)


def _target_touched(candles: pd.DataFrame, side: str, target: float | None) -> bool:
    if target is None or candles.empty:
        return False
    if side == "LONG":
        return bool((candles["high"].astype(float) >= target).any())
    return bool((candles["low"].astype(float) <= target).any())


def _zone_size_group(metadata: Mapping[str, Any]) -> str:
    low = _number(metadata.get("zone_low") or metadata.get("lower_boundary_value"))
    high = _number(metadata.get("zone_high") or metadata.get("upper_boundary_value"))
    atr = _number((metadata.get("atr_metadata") or {}).get("atr") if isinstance(metadata.get("atr_metadata"), dict) else None)
    if low is not None and high is not None and atr is not None and atr > 0:
        return _numeric_group(abs(high - low) / atr)
    return _numeric_group(metadata.get("gap_size_atr") or metadata.get("zone_size_atr"))


def _numeric_group(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "UNKNOWN"
    if number < 1:
        return "LT_1"
    if number < 2:
        return "ONE_TO_TWO"
    return "GTE_2"


def _average(values: Any) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return None if not numeric else sum(numeric) / len(numeric)


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


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
