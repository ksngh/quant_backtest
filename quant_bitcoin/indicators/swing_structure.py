"""Swing structure classification from confirmed pivot events.

This module consumes already-provided, confirmed pivot events and labels
same-type pivot relationships such as higher highs and lower lows. It does not
fetch market data, read secrets, call exchange APIs, place orders, or make
trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from quant_bitcoin.indicators.pivots import PivotType

REQUIRED_SWING_STRUCTURE_COLUMNS: tuple[str, ...] = (
    "symbol",
    "pivot_timestamp",
    "confirmed_timestamp",
    "pivot_index",
    "confirmed_index",
    "pivot_type",
    "price",
    "is_confirmed",
)

SWING_STRUCTURE_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "pivot_timestamp",
    "pivot_type",
    "pivot_price",
    "previous_same_type_pivot_price",
    "swing_label",
    "change_rate",
    "market_structure_status",
)


class SwingLabel(Enum):
    """Supported swing structure labels."""

    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"
    EQUAL_HIGH = "EQUAL_HIGH"
    EQUAL_LOW = "EQUAL_LOW"
    EQUAL_OR_NOISE = "EQUAL_OR_NOISE"
    UNKNOWN = "UNKNOWN"


class MarketStructureStatus(Enum):
    """Supported market structure statuses."""

    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGE = "RANGE"
    TRANSITION = "TRANSITION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SwingStructureConfig:
    """Configuration for deterministic swing structure classification."""

    minimum_price_change_rate: float = 0.0
    minimum_price_change_atr_multiplier: float | None = None
    use_atr_threshold: bool = False
    ignore_equal_price: bool = True
    structure_window: int = 20

    def __post_init__(self) -> None:
        if self.minimum_price_change_rate < 0:
            raise ValueError("minimum_price_change_rate must be non-negative")
        if self.structure_window < 1:
            raise ValueError("structure_window must be at least 1")
        if self.minimum_price_change_atr_multiplier is not None:
            if self.minimum_price_change_atr_multiplier < 0:
                raise ValueError(
                    "minimum_price_change_atr_multiplier must be non-negative"
                )
        if self.use_atr_threshold and self.minimum_price_change_atr_multiplier is None:
            raise ValueError(
                "minimum_price_change_atr_multiplier is required when "
                "use_atr_threshold is true"
            )


def classify_swing_structure(
    pivots: pd.DataFrame, config: SwingStructureConfig | None = None
) -> pd.DataFrame:
    """Return swing labels and market status for confirmed pivot events.

    Args:
        pivots: Pivot event data containing the required swing structure input
            columns. Only confirmed ``PIVOT_HIGH`` and ``PIVOT_LOW`` rows are
            used; unconfirmed rows and unsupported pivot types are ignored.
        config: Swing structure configuration. Defaults to
            ``SwingStructureConfig()``.

    Raises:
        ValueError: If required columns are missing or numeric fields are
            malformed. Missing current pivot prices are treated as an UNKNOWN
            classification row rather than a malformed input error.
    """

    swing_config = config or SwingStructureConfig()
    _validate_pivots(pivots, swing_config)

    if pivots.empty:
        return _empty_swing_structure_frame()

    confirmed_pivots = pivots[
        (pivots["is_confirmed"] == True)  # noqa: E712 - explicit owner rule
        & pivots["pivot_type"].isin(
            [PivotType.PIVOT_HIGH.value, PivotType.PIVOT_LOW.value]
        )
    ]

    if confirmed_pivots.empty:
        return _empty_swing_structure_frame()

    results: list[dict[str, Any]] = []
    previous_high: dict[str, Any] | None = None
    previous_low: dict[str, Any] | None = None
    high_labels: list[str] = []
    low_labels: list[str] = []
    previous_market_status = MarketStructureStatus.UNKNOWN.value

    for _, pivot in confirmed_pivots.iterrows():
        pivot_type = str(pivot["pivot_type"])
        current_price = _optional_float(pivot["price"])
        previous_price: float | None = None
        change_rate: float | None = None

        if current_price is None:
            label = SwingLabel.UNKNOWN.value
            market_status = MarketStructureStatus.UNKNOWN.value
        elif pivot_type == PivotType.PIVOT_HIGH.value:
            if previous_high is None:
                label = SwingLabel.UNKNOWN.value
            else:
                previous_price = previous_high["price"]
                label, change_rate = classify_high(
                    current_price,
                    previous_price,
                    _optional_float(pivot.get("atr")),
                    swing_config,
                )

            previous_high = {"price": current_price}
            _append_recent_label(high_labels, label, swing_config.structure_window)
            market_status = classify_market_status(
                high_labels,
                low_labels,
                previous_market_status,
            )
        else:
            if previous_low is None:
                label = SwingLabel.UNKNOWN.value
            else:
                previous_price = previous_low["price"]
                label, change_rate = classify_low(
                    current_price,
                    previous_price,
                    _optional_float(pivot.get("atr")),
                    swing_config,
                )

            previous_low = {"price": current_price}
            _append_recent_label(low_labels, label, swing_config.structure_window)
            market_status = classify_market_status(
                high_labels,
                low_labels,
                previous_market_status,
            )

        results.append(
            {
                "symbol": pivot["symbol"],
                "timestamp": pivot["confirmed_timestamp"],
                "pivot_timestamp": pivot["pivot_timestamp"],
                "pivot_type": pivot_type,
                "pivot_price": current_price,
                "previous_same_type_pivot_price": previous_price,
                "swing_label": label,
                "change_rate": change_rate,
                "market_structure_status": market_status,
            }
        )
        previous_market_status = market_status

    return pd.DataFrame(results, columns=SWING_STRUCTURE_OUTPUT_COLUMNS)


def swing_structure_alignment_feature(
    pivots: pd.DataFrame,
    *,
    current_index: int,
    direction: str,
    config: SwingStructureConfig | None = None,
) -> dict[str, Any]:
    """Return a no-lookahead swing-structure alignment score feature."""

    if current_index < 0:
        raise ValueError("current_index must be non-negative")
    swing_config = config or SwingStructureConfig()
    if pivots.empty:
        return _missing_alignment_feature(
            current_index=current_index,
            direction=direction,
            reason="no_pivots",
            config=swing_config,
        )
    visible_pivots = _visible_confirmed_pivots(pivots, current_index)
    if visible_pivots.empty:
        return _missing_alignment_feature(
            current_index=current_index,
            direction=direction,
            reason="no_confirmed_pivots_at_signal_time",
            config=swing_config,
        )

    structures = classify_swing_structure(visible_pivots, swing_config)
    if structures.empty:
        return _missing_alignment_feature(
            current_index=current_index,
            direction=direction,
            reason="insufficient_swing_structure",
            config=swing_config,
            visible_pivots=visible_pivots,
        )

    latest = structures.iloc[-1]
    status = str(latest["market_structure_status"])
    label = str(latest["swing_label"])
    score, context = _alignment_score_and_context(direction, status, label)
    return {
        "feature_available": True,
        "source": "observed_swing_structure_alignment",
        "context": context,
        "score": round(score, 6),
        "current_index": int(current_index),
        "direction": str(direction),
        "market_structure_status": status,
        "last_swing_label": label,
        "last_pivot_type": str(latest["pivot_type"]),
        "last_pivot_price": _json_float(latest["pivot_price"]),
        "last_change_rate": _json_float(latest["change_rate"]),
        "feature_window_pivots": int(len(visible_pivots)),
        "confirmation_rule": "confirmed_index <= current_index and pivot_index < current_index",
        "latest_confirmed_index": _latest_confirmed_index(visible_pivots),
        "confirmation_delay_bars": _confirmation_delay_bars(
            visible_pivots, current_index
        ),
        "structure_window": int(swing_config.structure_window),
    }


def classify_high(
    current_price: float,
    previous_price: float,
    atr: float | None,
    config: SwingStructureConfig,
) -> tuple[str, float]:
    """Classify a pivot high against the previous confirmed pivot high."""

    change = current_price - previous_price
    change_rate = _calculate_change_rate(current_price, previous_price)

    if config.use_atr_threshold and atr is None:
        return SwingLabel.UNKNOWN.value, change_rate

    if _is_below_configured_threshold(change, change_rate, atr, config):
        return SwingLabel.EQUAL_OR_NOISE.value, change_rate

    if change > 0:
        return SwingLabel.HH.value, change_rate
    if change < 0:
        return SwingLabel.LH.value, change_rate
    if config.ignore_equal_price:
        return SwingLabel.EQUAL_OR_NOISE.value, change_rate
    return SwingLabel.EQUAL_HIGH.value, change_rate


def classify_low(
    current_price: float,
    previous_price: float,
    atr: float | None,
    config: SwingStructureConfig,
) -> tuple[str, float]:
    """Classify a pivot low against the previous confirmed pivot low."""

    change = current_price - previous_price
    change_rate = _calculate_change_rate(current_price, previous_price)

    if config.use_atr_threshold and atr is None:
        return SwingLabel.UNKNOWN.value, change_rate

    if _is_below_configured_threshold(change, change_rate, atr, config):
        return SwingLabel.EQUAL_OR_NOISE.value, change_rate

    if change > 0:
        return SwingLabel.HL.value, change_rate
    if change < 0:
        return SwingLabel.LL.value, change_rate
    if config.ignore_equal_price:
        return SwingLabel.EQUAL_OR_NOISE.value, change_rate
    return SwingLabel.EQUAL_LOW.value, change_rate


def classify_market_status(
    high_labels: list[str],
    low_labels: list[str],
    previous_status: str,
) -> str:
    """Classify latest market status from recent high and low labels."""

    last_high = _get_last_non_unknown_label(high_labels)
    last_low = _get_last_non_unknown_label(low_labels)

    if last_high is None or last_low is None:
        return MarketStructureStatus.UNKNOWN.value

    if last_high == SwingLabel.HH.value and last_low == SwingLabel.HL.value:
        return MarketStructureStatus.UPTREND.value

    if last_high == SwingLabel.LH.value and last_low == SwingLabel.LL.value:
        return MarketStructureStatus.DOWNTREND.value

    if (
        previous_status == MarketStructureStatus.UPTREND.value
        and last_low == SwingLabel.LL.value
    ):
        return MarketStructureStatus.TRANSITION.value

    if (
        previous_status == MarketStructureStatus.DOWNTREND.value
        and last_high == SwingLabel.HH.value
    ):
        return MarketStructureStatus.TRANSITION.value

    return MarketStructureStatus.RANGE.value


def _validate_pivots(pivots: pd.DataFrame, config: SwingStructureConfig) -> None:
    missing_columns = [
        column for column in REQUIRED_SWING_STRUCTURE_COLUMNS if column not in pivots.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Pivot data is missing required columns: {missing}")

    for column in ("pivot_index", "confirmed_index"):
        try:
            pd.to_numeric(pivots[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"Pivot data contains non-numeric {column} values") from error

    if "atr" in pivots.columns:
        try:
            pd.to_numeric(pivots["atr"], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError("Pivot data contains non-numeric ATR values") from error

    price_without_missing = pivots["price"].dropna()
    try:
        numeric_price = pd.to_numeric(price_without_missing, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Pivot data contains non-numeric price values") from error

    if (numeric_price <= 0).any():
        raise ValueError("Pivot data contains non-positive price values")


def _visible_confirmed_pivots(pivots: pd.DataFrame, current_index: int) -> pd.DataFrame:
    visible = pivots.copy()
    if "is_confirmed" in visible:
        visible = visible[visible["is_confirmed"] == True]  # noqa: E712
    if "confirmed_index" in visible:
        visible = visible[pd.to_numeric(visible["confirmed_index"]) <= current_index]
    visible = visible[pd.to_numeric(visible["pivot_index"]) < current_index]
    if visible.empty:
        return visible
    return visible.sort_values(["pivot_index", "confirmed_index"]).reset_index(drop=True)


def _alignment_score_and_context(
    direction: str, status: str, label: str
) -> tuple[float, str]:
    normalized = str(direction).upper()
    if normalized in {"BULLISH", "LONG", "BUY"}:
        if status == MarketStructureStatus.UPTREND.value:
            return 1.0, "BULLISH_STRUCTURE_ALIGNED"
        if status == MarketStructureStatus.DOWNTREND.value:
            return 0.0, "BULLISH_STRUCTURE_OPPOSED"
        if label in {SwingLabel.HH.value, SwingLabel.HL.value}:
            return 0.7, "BULLISH_SWING_ALIGNED"
        if label in {SwingLabel.LH.value, SwingLabel.LL.value}:
            return 0.2, "BULLISH_SWING_OPPOSED"
        if status in {MarketStructureStatus.RANGE.value, MarketStructureStatus.TRANSITION.value}:
            return 0.5, "BULLISH_STRUCTURE_NEUTRAL"
        return 0.0, "MISSING_CONTEXT"

    if normalized in {"BEARISH", "SHORT", "SELL"}:
        if status == MarketStructureStatus.DOWNTREND.value:
            return 1.0, "BEARISH_STRUCTURE_ALIGNED"
        if status == MarketStructureStatus.UPTREND.value:
            return 0.0, "BEARISH_STRUCTURE_OPPOSED"
        if label in {SwingLabel.LH.value, SwingLabel.LL.value}:
            return 0.7, "BEARISH_SWING_ALIGNED"
        if label in {SwingLabel.HH.value, SwingLabel.HL.value}:
            return 0.2, "BEARISH_SWING_OPPOSED"
        if status in {MarketStructureStatus.RANGE.value, MarketStructureStatus.TRANSITION.value}:
            return 0.5, "BEARISH_STRUCTURE_NEUTRAL"
        return 0.0, "MISSING_CONTEXT"

    raise ValueError("direction must be bullish/long or bearish/short")


def _missing_alignment_feature(
    *,
    current_index: int,
    direction: str,
    reason: str,
    config: SwingStructureConfig,
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
        "structure_window": int(config.structure_window),
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


def _json_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _is_below_configured_threshold(
    change: float,
    change_rate: float,
    atr: float | None,
    config: SwingStructureConfig,
) -> bool:
    if config.use_atr_threshold:
        if atr is None:
            return False
        minimum_change = atr * float(config.minimum_price_change_atr_multiplier)
        return abs(change) < minimum_change

    return change_rate < config.minimum_price_change_rate


def _calculate_change_rate(current_price: float, previous_price: float) -> float:
    if previous_price <= 0:
        raise ValueError("previous pivot price must be positive")
    return abs(current_price - previous_price) / previous_price


def _append_recent_label(labels: list[str], label: str, window: int) -> None:
    if label != SwingLabel.UNKNOWN.value:
        labels.append(label)
    if len(labels) > window:
        del labels[:-window]


def _get_last_non_unknown_label(labels: list[str]) -> str | None:
    for label in reversed(labels):
        if label != SwingLabel.UNKNOWN.value:
            return label
    return None


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _empty_swing_structure_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=SWING_STRUCTURE_OUTPUT_COLUMNS)
