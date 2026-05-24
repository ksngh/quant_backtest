"""Support / resistance zone detection.

This module consumes already-provided confirmed pivot points and emits
mechanical price reaction zones. It does not fetch market data, read secrets,
call exchange APIs, place orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

REQUIRED_SUPPORT_RESISTANCE_PIVOT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "pivot_timestamp",
    "confirmed_timestamp",
    "pivot_index",
    "pivot_type",
    "price",
)

SUPPORT_RESISTANCE_ZONE_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "zone_type",
    "zone_status",
    "zone_low",
    "zone_high",
    "center_price",
    "touch_count",
    "pivot_indices",
    "first_touch_timestamp",
    "last_touch_timestamp",
    "zone_width",
    "atr",
    "is_broken",
    "is_valid",
)


class ZoneType(Enum):
    """Supported support / resistance zone classifications."""

    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    MIXED = "MIXED"


class ZoneStatus(Enum):
    """Supported support / resistance zone status values."""

    VALID = "VALID"
    WEAK = "WEAK"
    STRONG = "STRONG"
    BROKEN = "BROKEN"
    FLIPPED = "FLIPPED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SupportResistanceZoneConfig:
    """Configuration for deterministic support / resistance zone detection."""

    zone_width_atr_multiplier: float = 0.5
    minimum_touch_count: int = 2
    strong_touch_count: int = 3
    lookback_pivot_count: int = 50
    merge_overlapping_zones: bool = True
    use_atr_zone_width: bool = True
    fallback_zone_width_rate: float = 0.003
    breakout_atr_multiplier: float = 0.2
    maximum_zone_width_rate: float = 0.02
    require_confirmed_pivots: bool = True

    def __post_init__(self) -> None:
        if self.zone_width_atr_multiplier <= 0:
            raise ValueError("zone_width_atr_multiplier must be greater than 0")
        if self.minimum_touch_count < 1:
            raise ValueError("minimum_touch_count must be at least 1")
        if self.strong_touch_count < self.minimum_touch_count:
            raise ValueError(
                "strong_touch_count must be greater than or equal to "
                "minimum_touch_count"
            )
        if self.lookback_pivot_count < 1:
            raise ValueError("lookback_pivot_count must be at least 1")
        if self.fallback_zone_width_rate <= 0:
            raise ValueError("fallback_zone_width_rate must be greater than 0")
        if self.breakout_atr_multiplier < 0:
            raise ValueError("breakout_atr_multiplier must be non-negative")
        if self.maximum_zone_width_rate <= 0:
            raise ValueError("maximum_zone_width_rate must be greater than 0")


def detect_support_resistance_zones(
    pivots: pd.DataFrame,
    current_close: float | int | None = None,
    atr: float | int | None = None,
    timestamp: Any | None = None,
    config: SupportResistanceZoneConfig | None = None,
) -> pd.DataFrame:
    """Return deterministic support / resistance zones from pivot points.

    Args:
        pivots: Confirmed pivot rows containing symbol, pivot_timestamp,
            confirmed_timestamp, pivot_index, pivot_type, and price columns.
            If an ``is_confirmed`` column is present and confirmation is
            required, only rows with ``is_confirmed`` equal to ``True`` are
            used.
        current_close: Optional latest close used only to mark broken support
            or resistance zones.
        atr: Optional ATR value used for zone width and breakout buffer. If ATR
            is unavailable, the configured percentage fallback is used for zone
            width and broken-zone checks are skipped.
        timestamp: Optional evaluation timestamp for every output zone. When not
            supplied, the latest included confirmed timestamp is used per zone.
        config: Zone detection configuration. Defaults to
            ``SupportResistanceZoneConfig()``.

    Raises:
        ValueError: If required pivot columns are missing, numeric values are
            invalid, pivot types are unsupported, or configuration values are
            invalid.
    """

    zone_config = config or SupportResistanceZoneConfig()

    if pivots.empty:
        return _empty_zone_frame()

    _validate_pivots(pivots)
    atr_value = _optional_positive_float(atr, "atr")
    current_close_value = _optional_float(current_close, "current_close")

    candidate_pivots = pivots.copy()
    if zone_config.require_confirmed_pivots and "is_confirmed" in candidate_pivots:
        candidate_pivots = candidate_pivots[candidate_pivots["is_confirmed"] == True]

    candidate_pivots = candidate_pivots.tail(zone_config.lookback_pivot_count)
    if candidate_pivots.empty:
        return _empty_zone_frame()

    support_pivots = candidate_pivots[
        candidate_pivots["pivot_type"] == ZonePivotType.PIVOT_LOW.value
    ]
    resistance_pivots = candidate_pivots[
        candidate_pivots["pivot_type"] == ZonePivotType.PIVOT_HIGH.value
    ]

    support_zones = _build_zones(
        support_pivots,
        ZoneType.SUPPORT.value,
        atr_value,
        timestamp,
        zone_config,
    )
    resistance_zones = _build_zones(
        resistance_pivots,
        ZoneType.RESISTANCE.value,
        atr_value,
        timestamp,
        zone_config,
    )

    if zone_config.merge_overlapping_zones:
        support_zones = merge_overlapping_zones(support_zones, zone_config)
        resistance_zones = merge_overlapping_zones(resistance_zones, zone_config)
        all_zones = merge_support_resistance_overlaps(
            support_zones + resistance_zones,
            zone_config,
        )
    else:
        all_zones = support_zones + resistance_zones

    for zone in all_zones:
        update_zone_status(zone, current_close_value, atr_value, zone_config)

    if not all_zones:
        return _empty_zone_frame()
    return pd.DataFrame(all_zones, columns=SUPPORT_RESISTANCE_ZONE_OUTPUT_COLUMNS)


def support_resistance_proximity_feature(
    pivots: pd.DataFrame,
    *,
    current_index: int,
    price: float | int,
    direction: str,
    atr: float | int | None = None,
    config: SupportResistanceZoneConfig | None = None,
) -> dict[str, Any]:
    """Return a no-lookahead support/resistance proximity score feature.

    Only pivots whose confirmation is available at ``current_index`` are used.
    The function is a research/backtest feature helper; it does not make
    trading decisions or access external systems.
    """

    zone_config = config or SupportResistanceZoneConfig()
    price_value = _required_positive_float(price, "price")
    atr_value = _optional_positive_float(atr, "atr")
    if current_index < 0:
        raise ValueError("current_index must be non-negative")
    if pivots.empty:
        return _missing_proximity_feature(
            current_index=current_index,
            price=price_value,
            direction=direction,
            reason="no_pivots",
            config=zone_config,
        )
    if atr_value is None:
        return _missing_proximity_feature(
            current_index=current_index,
            price=price_value,
            direction=direction,
            reason="missing_atr",
            config=zone_config,
        )

    visible_pivots = _visible_confirmed_pivots(pivots, current_index)
    if visible_pivots.empty:
        return _missing_proximity_feature(
            current_index=current_index,
            price=price_value,
            direction=direction,
            reason="no_confirmed_pivots_at_signal_time",
            config=zone_config,
        )

    zones = detect_support_resistance_zones(
        visible_pivots,
        current_close=price_value,
        atr=atr_value,
        timestamp=None,
        config=zone_config,
    )
    if zones.empty:
        return _missing_proximity_feature(
            current_index=current_index,
            price=price_value,
            direction=direction,
            reason="no_confirmed_zone_at_signal_time",
            config=zone_config,
            visible_pivots=visible_pivots,
        )

    expected_zone_type = _expected_zone_type(direction)
    candidates = zones[
        (zones["is_valid"] == True)  # noqa: E712 - explicit pandas comparison
        & (zones["is_broken"] == False)  # noqa: E712
        & (zones["zone_type"].isin([expected_zone_type, ZoneType.MIXED.value]))
    ].copy()
    if candidates.empty:
        return _missing_proximity_feature(
            current_index=current_index,
            price=price_value,
            direction=direction,
            reason="no_active_directional_zone_at_signal_time",
            config=zone_config,
            visible_pivots=visible_pivots,
        )

    candidates["distance_to_zone"] = candidates.apply(
        lambda zone: _distance_to_zone(
            price_value,
            float(zone["zone_low"]),
            float(zone["zone_high"]),
        ),
        axis=1,
    )
    candidates["distance_atr"] = candidates["distance_to_zone"] / atr_value
    selected = candidates.sort_values(
        ["distance_atr", "zone_type", "touch_count"], ascending=[True, True, False]
    ).iloc[0]
    distance_atr = float(selected["distance_atr"])
    raw_score = max(0.0, min(1.0, 1.0 - distance_atr))
    context_side = "SUPPORT" if expected_zone_type == ZoneType.SUPPORT.value else "RESISTANCE"
    context_prefix = "NEAR" if raw_score > 0 else "AWAY_FROM"
    return {
        "feature_available": True,
        "source": "observed_support_resistance_proximity",
        "context": f"{context_prefix}_{context_side}",
        "score": round(raw_score, 6),
        "current_index": int(current_index),
        "price": float(price_value),
        "direction": str(direction),
        "expected_zone_type": expected_zone_type,
        "zone_type": str(selected["zone_type"]),
        "zone_status": str(selected["zone_status"]),
        "zone_low": float(selected["zone_low"]),
        "zone_high": float(selected["zone_high"]),
        "center_price": float(selected["center_price"]),
        "distance_to_zone": float(selected["distance_to_zone"]),
        "distance_atr": distance_atr,
        "touch_count": int(selected["touch_count"]),
        "pivot_indices": tuple(int(value) for value in selected["pivot_indices"]),
        "feature_window_pivots": int(len(visible_pivots)),
        "confirmation_rule": "confirmed_index <= current_index and pivot_index < current_index",
        "latest_confirmed_index": _latest_confirmed_index(visible_pivots),
        "confirmation_delay_bars": _confirmation_delay_bars(
            visible_pivots, current_index
        ),
        "zone_config": {
            "lookback_pivot_count": int(zone_config.lookback_pivot_count),
            "minimum_touch_count": int(zone_config.minimum_touch_count),
            "zone_width_atr_multiplier": float(zone_config.zone_width_atr_multiplier),
        },
    }


class ZonePivotType(Enum):
    """Pivot types consumed by zone detection."""

    PIVOT_HIGH = "PIVOT_HIGH"
    PIVOT_LOW = "PIVOT_LOW"


def merge_overlapping_zones(
    zones: list[dict[str, Any]],
    config: SupportResistanceZoneConfig | None = None,
) -> list[dict[str, Any]]:
    """Merge overlapping same-type zones using deterministic boundaries."""

    zone_config = config or SupportResistanceZoneConfig()
    return _merge_overlapping_zones(zones, zone_config, merge_mixed=False)


def merge_support_resistance_overlaps(
    zones: list[dict[str, Any]],
    config: SupportResistanceZoneConfig | None = None,
) -> list[dict[str, Any]]:
    """Merge overlapping support and resistance zones into MIXED zones."""

    zone_config = config or SupportResistanceZoneConfig()
    return _merge_overlapping_zones(zones, zone_config, merge_mixed=True)


def update_zone_status(
    zone: dict[str, Any],
    current_close: float | None,
    atr: float | None,
    config: SupportResistanceZoneConfig | None = None,
) -> dict[str, Any]:
    """Update a zone dictionary for broken support/resistance status."""

    zone_config = config or SupportResistanceZoneConfig()
    if not zone.get("is_valid", False):
        zone["zone_status"] = ZoneStatus.INVALID.value
        zone["is_broken"] = False
        return zone
    if current_close is None or atr is None:
        return zone

    breakout_buffer = atr * zone_config.breakout_atr_multiplier
    if zone["zone_type"] == ZoneType.SUPPORT.value:
        if current_close < zone["zone_low"] - breakout_buffer:
            zone["is_broken"] = True
            zone["zone_status"] = ZoneStatus.BROKEN.value
    elif zone["zone_type"] == ZoneType.RESISTANCE.value:
        if current_close > zone["zone_high"] + breakout_buffer:
            zone["is_broken"] = True
            zone["zone_status"] = ZoneStatus.BROKEN.value
    return zone


def _build_zones(
    pivots: pd.DataFrame,
    zone_type: str,
    atr: float | None,
    timestamp: Any | None,
    config: SupportResistanceZoneConfig,
) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    if pivots.empty:
        return zones

    prices = pd.to_numeric(pivots["price"], errors="raise")
    for row_position, (_, pivot) in enumerate(pivots.iterrows()):
        pivot_price = float(prices.iloc[row_position])
        zone_width = _calculate_zone_width(pivot_price, atr, config)
        zone_low = pivot_price - zone_width
        zone_high = pivot_price + zone_width

        touches = pivots[(prices >= zone_low) & (prices <= zone_high)].copy()
        touch_count = len(touches)
        if touch_count < config.minimum_touch_count:
            continue

        touch_prices = pd.to_numeric(touches["price"], errors="raise")
        center_price = float(touch_prices.mean())
        zone = _zone_from_touches(
            touches,
            zone_type,
            center_price - zone_width,
            center_price + zone_width,
            center_price,
            touch_count,
            zone_width,
            atr,
            timestamp,
            config,
        )
        zones.append(zone)

    return zones


def _calculate_zone_width(
    reference_price: float,
    atr: float | None,
    config: SupportResistanceZoneConfig,
) -> float:
    if config.use_atr_zone_width and atr is not None:
        return atr * config.zone_width_atr_multiplier
    return reference_price * config.fallback_zone_width_rate


def _zone_from_touches(
    touches: pd.DataFrame,
    zone_type: str,
    zone_low: float,
    zone_high: float,
    center_price: float,
    touch_count: int,
    zone_width: float,
    atr: float | None,
    timestamp: Any | None,
    config: SupportResistanceZoneConfig,
) -> dict[str, Any]:
    sorted_touches = touches.sort_values("pivot_index")
    first_touch = sorted_touches.iloc[0]
    last_touch = sorted_touches.iloc[-1]
    zone_status = _status_for_touch_count(touch_count, config)
    is_valid = touch_count >= config.minimum_touch_count

    if center_price <= 0 or zone_width / center_price > config.maximum_zone_width_rate:
        zone_status = ZoneStatus.INVALID.value
        is_valid = False

    return {
        "symbol": first_touch["symbol"],
        "timestamp": (
            timestamp if timestamp is not None else last_touch["confirmed_timestamp"]
        ),
        "zone_type": zone_type,
        "zone_status": zone_status,
        "zone_low": zone_low,
        "zone_high": zone_high,
        "center_price": center_price,
        "touch_count": touch_count,
        "pivot_indices": [
            int(value) for value in sorted_touches["pivot_index"].tolist()
        ],
        "first_touch_timestamp": first_touch["pivot_timestamp"],
        "last_touch_timestamp": last_touch["pivot_timestamp"],
        "zone_width": zone_width,
        "atr": atr,
        "is_broken": False,
        "is_valid": is_valid,
    }


def _merge_overlapping_zones(
    zones: list[dict[str, Any]],
    config: SupportResistanceZoneConfig,
    *,
    merge_mixed: bool,
) -> list[dict[str, Any]]:
    if not zones:
        return []

    sorted_zones = sorted(zones, key=lambda zone: (zone["zone_low"], zone["zone_high"]))
    merged = [sorted_zones[0].copy()]

    for zone in sorted_zones[1:]:
        previous = merged[-1]
        if _zones_overlap(previous, zone):
            previous_type = previous["zone_type"]
            zone_type = zone["zone_type"]
            if not merge_mixed and previous_type != zone_type:
                merged.append(zone.copy())
                continue

            previous["zone_low"] = min(previous["zone_low"], zone["zone_low"])
            previous["zone_high"] = max(previous["zone_high"], zone["zone_high"])
            previous["center_price"] = (
                previous["zone_low"] + previous["zone_high"]
            ) / 2
            previous["zone_width"] = (previous["zone_high"] - previous["zone_low"]) / 2
            previous["touch_count"] += zone["touch_count"]
            previous["pivot_indices"] = sorted(
                set(previous["pivot_indices"] + zone["pivot_indices"])
            )
            previous["first_touch_timestamp"] = min(
                previous["first_touch_timestamp"],
                zone["first_touch_timestamp"],
            )
            previous["last_touch_timestamp"] = max(
                previous["last_touch_timestamp"],
                zone["last_touch_timestamp"],
            )
            previous["timestamp"] = max(previous["timestamp"], zone["timestamp"])
            if merge_mixed and previous_type != zone_type:
                previous["zone_type"] = ZoneType.MIXED.value
            previous["is_valid"] = _is_zone_valid(previous, config)
            previous["zone_status"] = _status_for_zone(previous, config)
        else:
            merged.append(zone.copy())

    return merged


def _zones_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        first["zone_high"] >= second["zone_low"]
        and second["zone_high"] >= first["zone_low"]
    )


def _is_zone_valid(zone: dict[str, Any], config: SupportResistanceZoneConfig) -> bool:
    if zone["touch_count"] < config.minimum_touch_count:
        return False
    if zone["center_price"] <= 0:
        return False
    return zone["zone_width"] / zone["center_price"] <= config.maximum_zone_width_rate


def _status_for_zone(
    zone: dict[str, Any], config: SupportResistanceZoneConfig
) -> str:
    if not _is_zone_valid(zone, config):
        return ZoneStatus.INVALID.value
    return _status_for_touch_count(zone["touch_count"], config)


def _status_for_touch_count(
    touch_count: int, config: SupportResistanceZoneConfig) -> str:
    if touch_count < config.minimum_touch_count:
        return ZoneStatus.INVALID.value
    if touch_count >= config.strong_touch_count:
        return ZoneStatus.STRONG.value
    return ZoneStatus.WEAK.value


def _validate_pivots(pivots: pd.DataFrame) -> None:
    missing_columns = [
        column
        for column in REQUIRED_SUPPORT_RESISTANCE_PIVOT_COLUMNS
        if column not in pivots.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Pivot data is missing required columns: {missing}")

    try:
        prices = pd.to_numeric(pivots["price"], errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Pivot data contains non-numeric price values") from error
    if prices.isna().any():
        raise ValueError("Pivot data contains missing price values")
    if (prices <= 0).any():
        raise ValueError("Pivot data contains non-positive price values")

    try:
        pivot_indices = pd.to_numeric(pivots["pivot_index"], errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Pivot data contains non-numeric pivot_index values"
        ) from error
    if pivot_indices.isna().any():
        raise ValueError("Pivot data contains missing pivot_index values")

    allowed_pivot_types = {pivot_type.value for pivot_type in ZonePivotType}
    invalid_pivot_types = sorted(set(pivots["pivot_type"]) - allowed_pivot_types)
    if invalid_pivot_types:
        invalid = ", ".join(str(value) for value in invalid_pivot_types)
        raise ValueError(
            f"Pivot data contains unsupported pivot_type values: {invalid}"
        )


def _visible_confirmed_pivots(pivots: pd.DataFrame, current_index: int) -> pd.DataFrame:
    visible = pivots.copy()
    if "is_confirmed" in visible:
        visible = visible[visible["is_confirmed"] == True]  # noqa: E712
    if "confirmed_index" in visible:
        visible = visible[pd.to_numeric(visible["confirmed_index"]) <= current_index]
    visible = visible[pd.to_numeric(visible["pivot_index"]) < current_index]
    visible = visible[
        visible["pivot_type"].isin(
            [ZonePivotType.PIVOT_HIGH.value, ZonePivotType.PIVOT_LOW.value]
        )
    ]
    if visible.empty:
        return visible
    return visible.sort_values(["pivot_index", "confirmed_timestamp"]).reset_index(drop=True)


def _expected_zone_type(direction: str) -> str:
    normalized = str(direction).upper()
    if normalized in {"BULLISH", "LONG", "BUY"}:
        return ZoneType.SUPPORT.value
    if normalized in {"BEARISH", "SHORT", "SELL"}:
        return ZoneType.RESISTANCE.value
    raise ValueError("direction must be bullish/long or bearish/short")


def _distance_to_zone(price: float, zone_low: float, zone_high: float) -> float:
    if zone_low <= price <= zone_high:
        return 0.0
    if price < zone_low:
        return zone_low - price
    return price - zone_high


def _missing_proximity_feature(
    *,
    current_index: int,
    price: float,
    direction: str,
    reason: str,
    config: SupportResistanceZoneConfig,
    visible_pivots: pd.DataFrame | None = None,
) -> dict[str, Any]:
    visible_count = 0 if visible_pivots is None else int(len(visible_pivots))
    return {
        "feature_available": False,
        "source": "missing_context",
        "context": "MISSING_CONTEXT",
        "score": 0.0,
        "missing_context_reason": reason,
        "current_index": int(current_index),
        "price": float(price),
        "direction": str(direction),
        "feature_window_pivots": visible_count,
        "confirmation_rule": "confirmed_index <= current_index and pivot_index < current_index",
        "latest_confirmed_index": (
            None if visible_pivots is None else _latest_confirmed_index(visible_pivots)
        ),
        "confirmation_delay_bars": (
            None
            if visible_pivots is None
            else _confirmation_delay_bars(visible_pivots, current_index)
        ),
        "zone_config": {
            "lookback_pivot_count": int(config.lookback_pivot_count),
            "minimum_touch_count": int(config.minimum_touch_count),
            "zone_width_atr_multiplier": float(config.zone_width_atr_multiplier),
        },
    }


def _latest_confirmed_index(pivots: pd.DataFrame) -> int | None:
    if pivots.empty or "confirmed_index" not in pivots:
        return None
    return int(pd.to_numeric(pivots["confirmed_index"]).max())


def _confirmation_delay_bars(
    pivots: pd.DataFrame, current_index: int
) -> int | None:
    latest = _latest_confirmed_index(pivots)
    if latest is None:
        return None
    return int(current_index - latest)


def _optional_float(value: float | int | None, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} must be numeric when provided") from error
    if pd.isna(result):
        return None
    return result


def _optional_positive_float(
    value: float | int | None, field_name: str
) -> float | None:
    result = _optional_float(value, field_name)
    if result is None:
        return None
    if result <= 0:
        raise ValueError(f"{field_name} must be greater than 0 when provided")
    return result


def _required_positive_float(value: float | int, field_name: str) -> float:
    result = _optional_positive_float(value, field_name)
    if result is None:
        raise ValueError(f"{field_name} must be provided")
    return result


def _empty_zone_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=SUPPORT_RESISTANCE_ZONE_OUTPUT_COLUMNS)
