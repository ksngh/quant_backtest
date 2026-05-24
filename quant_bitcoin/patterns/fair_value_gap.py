"""Fair Value Gap pattern detection.

This module evaluates already-provided completed candle data and emits
stable, deterministic Fair Value Gap events. It is intentionally pure: it does
not fetch market data, read secrets, call exchange APIs, place orders, persist
records, or make trading decisions.

First-batch implementation notes:
- Liquidity and bid-ask spread filters are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require a pass/fail value once those filters are supplied.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` so streaming callers do not accidentally evaluate
  incomplete or reordered windows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, atr_timing_metadata, calculate_atr
from quant_bitcoin.indicators.displacement_candle import (
    DisplacementCandleConfig,
    DisplacementDirection,
    DisplacementStatus,
    detect_displacement_candles,
)
from quant_bitcoin.indicators.pivots import PivotConfig, detect_pivots
from quant_bitcoin.indicators.support_resistance_zone import (
    SupportResistanceZoneConfig,
    support_resistance_proximity_feature,
)
from quant_bitcoin.indicators.swing_structure import (
    SwingStructureConfig,
    swing_structure_alignment_feature,
)
from quant_bitcoin.indicators.volume_ratio import VolumeRatioConfig, calculate_volume_ratio
from quant_bitcoin.patterns.score_metadata import build_score_metadata

REQUIRED_PATTERN_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class PatternType(Enum):
    """Supported first-batch pattern types."""

    FAIR_VALUE_GAP = "FAIR_VALUE_GAP"


class PatternDirection(Enum):
    """Supported pattern directions."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NONE = "NONE"


class PatternStatus(Enum):
    """Supported pattern statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


class FairValueGapState(Enum):
    """Supported Fair Value Gap lifecycle states."""

    FRESH = "FRESH"
    TOUCHED = "TOUCHED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    BROKEN = "BROKEN"
    INVALID = "INVALID"


@dataclass(frozen=True)
class FairValueGapConfig:
    """Configuration for deterministic first-batch Fair Value Gap detection."""

    minimum_gap_size_atr_multiplier: float = 0.1
    maximum_gap_size_atr_multiplier: float = 2.0
    require_displacement_candle: bool = True
    minimum_volume_ratio: float = 1.3
    strong_volume_ratio: float = 1.5
    break_buffer_atr_multiplier: float = 0.2
    fill_threshold: float = 1.0
    partial_fill_threshold: float = 0.01
    # Liquidity and spread modules are not implemented yet. The first detector
    # therefore defaults these unavailable prerequisite filters to not required
    # instead of silently approximating them.
    require_liquidity_pass: bool = False
    require_spread_pass: bool = False
    liquidity_pass: bool | None = None
    spread_pass: bool | None = None
    minimum_pattern_score: float = 0.7
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None
    displacement_config: DisplacementCandleConfig | None = None
    pivot_config: PivotConfig | None = None
    support_resistance_config: SupportResistanceZoneConfig | None = None
    swing_structure_config: SwingStructureConfig | None = None
    retrospective_lifecycle: bool = False

    def __post_init__(self) -> None:
        if self.minimum_gap_size_atr_multiplier < 0:
            raise ValueError("minimum_gap_size_atr_multiplier must be non-negative")
        if self.maximum_gap_size_atr_multiplier < 0:
            raise ValueError("maximum_gap_size_atr_multiplier must be non-negative")
        if self.minimum_gap_size_atr_multiplier > self.maximum_gap_size_atr_multiplier:
            raise ValueError(
                "minimum_gap_size_atr_multiplier must be less than or equal to "
                "maximum_gap_size_atr_multiplier"
            )
        if self.minimum_volume_ratio < 0:
            raise ValueError("minimum_volume_ratio must be non-negative")
        if self.strong_volume_ratio < self.minimum_volume_ratio:
            raise ValueError(
                "strong_volume_ratio must be greater than or equal to minimum_volume_ratio"
            )
        if self.break_buffer_atr_multiplier < 0:
            raise ValueError("break_buffer_atr_multiplier must be non-negative")
        if not 0 <= self.partial_fill_threshold <= self.fill_threshold:
            raise ValueError(
                "partial_fill_threshold must be between 0 and fill_threshold"
            )
        if not 0 <= self.minimum_pattern_score <= 1:
            raise ValueError("minimum_pattern_score must be between 0 and 1")


@dataclass(frozen=True)
class PatternEvent:
    """Deterministic pattern event emitted by the first-batch detector."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    candle_1_index: int
    candle_2_index: int
    candle_3_index: int
    zone_low: float
    zone_high: float
    zone_mid: float
    gap_size: float
    gap_size_atr: float
    fill_ratio: float
    fvg_state: str
    displacement_confirmed: bool
    displacement_direction: str
    volume_ratio: float
    liquidity_pass: bool | None
    spread_pass: bool | None
    structure_context: str | None
    support_resistance_context: str | None
    pattern_score: float
    entry_reference: float
    stop_reference: float
    target_reference: float
    risk_reward: float | None
    reason: str
    score_components: dict[str, Any] = field(default_factory=dict)
    score_component_sources: dict[str, str] = field(default_factory=dict)
    score_limitations: tuple[str, ...] = ()
    score_calibration: dict[str, Any] = field(default_factory=dict)
    executable_pattern_score: float | None = None
    diagnostic_pattern_score: float | None = None
    atr_metadata: dict[str, Any] = field(default_factory=dict)


def detect_patterns(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: FairValueGapConfig | None = None,
) -> list[PatternEvent]:
    """Return deterministic first-batch pattern events for completed candles.

    The first implementation batch supports only Fair Value Gap detection. The
    caller may pass a full historical batch or an overlapping rolling completed
    candle window. Stable ``event_id`` values allow the caller to suppress
    duplicates by tracking previously seen identifiers.

    Args:
        candles: Completed candles using the standard candle schema. A pandas
            ``DataFrame`` is preferred, but an iterable of dictionaries is also
            accepted and normalized at the boundary.
        symbol: Optional caller-supplied symbol used in event records and stable
            event identifiers. If omitted and a ``symbol`` candle column exists,
            the first candle's value is used.
        timeframe: Optional caller-supplied timeframe used in event records and
            stable event identifiers.
        config: Optional Fair Value Gap detector configuration.

    Raises:
        ValueError: If required candle columns are missing, numeric values are
            non-numeric, candles are not sorted ascending by timestamp, or a
            required unavailable filter is enabled without an explicit pass value.
    """

    return detect_fair_value_gaps(
        candles,
        symbol=symbol,
        timeframe=timeframe,
        config=config,
    )


def detect_fair_value_gaps(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: FairValueGapConfig | None = None,
) -> list[PatternEvent]:
    """Return Fair Value Gap events using signal-time no-lookahead semantics.

    By default lifecycle fields are evaluated only through the confirmation
    candle. Set ``FairValueGapConfig.retrospective_lifecycle=True`` only for
    event-study analysis that intentionally reclassifies events with later
    candles.
    """

    fvg_config = config or FairValueGapConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < 3:
        return []

    _validate_external_filters(fvg_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        fvg_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(candle_frame, fvg_config.volume_ratio_config)
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    displacement_rows = detect_displacement_candles(
        enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
        fvg_config.displacement_config,
    )

    events: list[PatternEvent] = []
    for candle_3_index in range(2, len(enriched)):
        candle_1_index = candle_3_index - 2
        candle_2_index = candle_3_index - 1
        candle_1 = enriched.iloc[candle_1_index]
        candle_3 = enriched.iloc[candle_3_index]

        if float(candle_1["high"]) < float(candle_3["low"]):
            event = _evaluate_fair_value_gap(
                PatternDirection.BULLISH,
                enriched,
                displacement_rows,
                candle_1_index,
                candle_2_index,
                candle_3_index,
                symbol=symbol or str(enriched.iloc[0]["symbol"]),
                timeframe=timeframe,
                config=fvg_config,
            )
            if event is not None:
                events.append(event)

        if float(candle_1["low"]) > float(candle_3["high"]):
            event = _evaluate_fair_value_gap(
                PatternDirection.BEARISH,
                enriched,
                displacement_rows,
                candle_1_index,
                candle_2_index,
                candle_3_index,
                symbol=symbol or str(enriched.iloc[0]["symbol"]),
                timeframe=timeframe,
                config=fvg_config,
            )
            if event is not None:
                events.append(event)

    return events


def detect_fair_value_gaps_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: FairValueGapConfig | None = None,
) -> list[PatternEvent]:
    """Return only events confirmed at ``current_index`` using visible candles."""

    if current_index < 0:
        return []
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if current_index >= len(frame):
        return []
    events = detect_fair_value_gaps(
        frame.iloc[: current_index + 1],
        symbol=symbol,
        timeframe=timeframe,
        config=config,
    )
    return [event for event in events if event.end_index == current_index]


def filter_new_events(
    events: Iterable[PatternEvent], seen_event_ids: set[str]
) -> list[PatternEvent]:
    """Return events whose stable identifiers are not present in ``seen_event_ids``.

    The helper is optional and does not keep global mutable state. It mutates
    only the caller-provided ``seen_event_ids`` set to document the streaming
    duplicate-prevention pattern.
    """

    new_events: list[PatternEvent] = []
    for event in events:
        if event.event_id in seen_event_ids:
            continue
        new_events.append(event)
        seen_event_ids.add(event.event_id)
    return new_events


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]], symbol: str | None
) -> pd.DataFrame:
    if isinstance(candles, pd.DataFrame):
        frame = candles.copy(deep=True)
    else:
        frame = pd.DataFrame(list(candles)).copy(deep=True)

    missing_columns = [
        column for column in REQUIRED_PATTERN_CANDLE_COLUMNS if column not in frame.columns
    ]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(f"missing required candle columns: {joined}")

    if frame.empty:
        if "symbol" not in frame.columns:
            frame["symbol"] = symbol or "UNKNOWN"
        return frame

    if "symbol" not in frame.columns:
        frame["symbol"] = symbol or "UNKNOWN"
    elif symbol is not None:
        frame["symbol"] = symbol

    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[column].isna().any():
            raise ValueError(f"candle column contains missing values: {column}")

    if (frame["high"] < frame["low"]).any():
        raise ValueError("candle high must be greater than or equal to low")
    if (frame["volume"] < 0).any():
        raise ValueError("candle volume must be non-negative")

    return frame.reset_index(drop=True)


def _validate_external_filters(config: FairValueGapConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _evaluate_fair_value_gap(
    direction: PatternDirection,
    candles: pd.DataFrame,
    displacement_rows: pd.DataFrame,
    candle_1_index: int,
    candle_2_index: int,
    candle_3_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: FairValueGapConfig,
) -> PatternEvent | None:
    candle_1 = candles.iloc[candle_1_index]
    candle_2 = candles.iloc[candle_2_index]
    candle_3 = candles.iloc[candle_3_index]

    if direction == PatternDirection.BULLISH:
        zone_low = float(candle_1["high"])
        zone_high = float(candle_3["low"])
        expected_displacement_direction = DisplacementDirection.BULLISH.value
    else:
        zone_low = float(candle_3["high"])
        zone_high = float(candle_1["low"])
        expected_displacement_direction = DisplacementDirection.BEARISH.value

    gap_size = zone_high - zone_low
    if gap_size <= 0:
        return None

    atr = _optional_float(candle_3["atr"])
    if atr is None or atr <= 0:
        return None

    gap_size_atr = gap_size / atr
    if gap_size_atr < config.minimum_gap_size_atr_multiplier:
        return None

    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    displacement = displacement_rows.iloc[candle_2_index]
    displacement_direction = str(displacement["displacement_direction"])
    displacement_confirmed = (
        displacement_direction == expected_displacement_direction
        and str(displacement["displacement_status"]) == DisplacementStatus.VALID.value
    )
    if config.require_displacement_candle and not displacement_confirmed:
        return None

    volume_ratio = _optional_float(candle_2["volume_ratio"])
    if volume_ratio is None:
        return None

    lifecycle_candles = candles if config.retrospective_lifecycle else candles.iloc[: candle_3_index + 1]
    fvg_state, fill_ratio = _classify_fvg_state(
        direction,
        lifecycle_candles,
        candle_3_index,
        zone_low,
        zone_high,
        gap_size,
        atr,
        config,
    )
    if fvg_state in (FairValueGapState.FILLED, FairValueGapState.BROKEN):
        return None

    zone_mid = (zone_low + zone_high) / 2
    context_pivots = _context_pivots(candles, candle_3_index, config.pivot_config)
    support_resistance_feature = support_resistance_proximity_feature(
        context_pivots,
        current_index=candle_3_index,
        price=zone_mid,
        direction=direction.value,
        atr=atr,
        config=config.support_resistance_config,
    )
    swing_structure_feature = swing_structure_alignment_feature(
        context_pivots,
        current_index=candle_3_index,
        direction=direction.value,
        config=config.swing_structure_config,
    )

    score_metadata = _calculate_pattern_score_metadata(
        gap_size_atr=gap_size_atr,
        displacement_confirmed=displacement_confirmed,
        volume_ratio=volume_ratio,
        fvg_state=fvg_state,
        support_resistance_feature=support_resistance_feature,
        swing_structure_feature=swing_structure_feature,
        config=config,
    )
    pattern_score = float(score_metadata["pattern_score"])
    pattern_status = _classify_pattern_status(
        gap_size_atr=gap_size_atr,
        volume_ratio=volume_ratio,
        pattern_score=pattern_score,
        config=config,
    )

    entry_reference = zone_mid
    if direction == PatternDirection.BULLISH:
        stop_reference = zone_low - config.break_buffer_atr_multiplier * atr
        target_reference = entry_reference + 2 * abs(entry_reference - stop_reference)
        risk = entry_reference - stop_reference
        reward = target_reference - entry_reference
    else:
        stop_reference = zone_high + config.break_buffer_atr_multiplier * atr
        target_reference = entry_reference - 2 * abs(stop_reference - entry_reference)
        risk = stop_reference - entry_reference
        reward = entry_reference - target_reference
    risk_reward = reward / risk if risk > 0 else None

    timestamp = candle_3["timestamp"]
    event_id = _build_event_id(
        pattern_type=PatternType.FAIR_VALUE_GAP.value,
        direction=direction.value,
        symbol=symbol,
        timeframe=timeframe,
        candle_1_timestamp=candle_1["timestamp"],
        candle_2_timestamp=candle_2["timestamp"],
        candle_3_timestamp=timestamp,
    )

    return PatternEvent(
        event_id=event_id,
        pattern_type=PatternType.FAIR_VALUE_GAP.value,
        direction=direction.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=timestamp,
        start_index=candle_1_index,
        end_index=candle_3_index,
        candle_1_index=candle_1_index,
        candle_2_index=candle_2_index,
        candle_3_index=candle_3_index,
        zone_low=zone_low,
        zone_high=zone_high,
        zone_mid=zone_mid,
        gap_size=gap_size,
        gap_size_atr=gap_size_atr,
        fill_ratio=fill_ratio,
        fvg_state=fvg_state.value,
        displacement_confirmed=displacement_confirmed,
        displacement_direction=displacement_direction,
        volume_ratio=volume_ratio,
        liquidity_pass=config.liquidity_pass,
        spread_pass=config.spread_pass,
        structure_context=str(swing_structure_feature.get("context")),
        support_resistance_context=str(support_resistance_feature.get("context")),
        pattern_score=pattern_score,
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        reason=(
            f"{direction.value.title()} Fair Value Gap detected with "
            "three-candle imbalance, displacement evaluation, and volume confirmation."
        ),
        score_components=score_metadata["score_components"],
        score_component_sources=score_metadata["score_component_sources"],
        score_limitations=score_metadata["score_limitations"],
        score_calibration=score_metadata["score_calibration"],
        executable_pattern_score=score_metadata["executable_pattern_score"],
        diagnostic_pattern_score=score_metadata["diagnostic_pattern_score"],
        atr_metadata=atr_timing_metadata(config.atr_config),
    )


def _classify_fvg_state(
    direction: PatternDirection,
    candles: pd.DataFrame,
    candle_3_index: int,
    zone_low: float,
    zone_high: float,
    gap_size: float,
    atr: float,
    config: FairValueGapConfig,
) -> tuple[FairValueGapState, float]:
    later_candles = candles.iloc[candle_3_index + 1 :]
    if later_candles.empty:
        return FairValueGapState.FRESH, 0.0

    if direction == PatternDirection.BULLISH:
        lowest_price = float(later_candles["low"].min())
        fill_ratio = _clamp((zone_high - lowest_price) / gap_size)
        broken = (later_candles["close"] < zone_low - config.break_buffer_atr_multiplier * atr).any()
    else:
        highest_price = float(later_candles["high"].max())
        fill_ratio = _clamp((highest_price - zone_low) / gap_size)
        broken = (later_candles["close"] > zone_high + config.break_buffer_atr_multiplier * atr).any()

    if broken:
        return FairValueGapState.BROKEN, fill_ratio
    if fill_ratio >= config.fill_threshold:
        return FairValueGapState.FILLED, fill_ratio
    if fill_ratio >= config.partial_fill_threshold:
        return FairValueGapState.PARTIALLY_FILLED, fill_ratio
    return FairValueGapState.FRESH, 0.0


def _calculate_pattern_score(
    *,
    gap_size_atr: float,
    displacement_confirmed: bool,
    volume_ratio: float,
    fvg_state: FairValueGapState,
    config: FairValueGapConfig,
    support_resistance_feature: dict[str, Any] | None = None,
    swing_structure_feature: dict[str, Any] | None = None,
) -> float:
    return float(
        _calculate_pattern_score_metadata(
            gap_size_atr=gap_size_atr,
            displacement_confirmed=displacement_confirmed,
            volume_ratio=volume_ratio,
            fvg_state=fvg_state,
            support_resistance_feature=support_resistance_feature,
            swing_structure_feature=swing_structure_feature,
            config=config,
        )["pattern_score"]
    )


def _calculate_pattern_score_metadata(
    *,
    gap_size_atr: float,
    displacement_confirmed: bool,
    volume_ratio: float,
    fvg_state: FairValueGapState,
    config: FairValueGapConfig,
    support_resistance_feature: dict[str, Any] | None = None,
    swing_structure_feature: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if 0.2 <= gap_size_atr <= 1.0:
        gap_quality_score = 1.0
    elif 0.1 <= gap_size_atr < 0.2:
        gap_quality_score = 0.6
    elif 1.0 < gap_size_atr <= config.maximum_gap_size_atr_multiplier:
        gap_quality_score = 0.7
    else:
        gap_quality_score = 0.0

    displacement_score = 1.0 if displacement_confirmed else 0.4
    if config.require_displacement_candle and not displacement_confirmed:
        displacement_score = 0.0

    if volume_ratio >= 2.0:
        volume_confirmation_score = 1.0
    elif volume_ratio >= config.strong_volume_ratio:
        volume_confirmation_score = 0.8
    elif volume_ratio >= config.minimum_volume_ratio:
        volume_confirmation_score = 0.5
    else:
        volume_confirmation_score = 0.0

    structure_feature = swing_structure_feature or _missing_score_feature(
        reason="feature_not_computed"
    )
    support_feature = support_resistance_feature or _missing_score_feature(
        reason="feature_not_computed"
    )
    liquidity_score = 0.8 if not config.require_liquidity_pass else 1.0

    if fvg_state == FairValueGapState.FRESH:
        freshness_score = 1.0
    elif fvg_state == FairValueGapState.PARTIALLY_FILLED:
        freshness_score = 0.5
    else:
        freshness_score = 0.0

    return build_score_metadata(
        PatternType.FAIR_VALUE_GAP.value,
        [
            {
                "name": "gap_quality",
                "raw_score": gap_quality_score,
                "weight": 0.20,
                "source": "observed_gap_size_atr",
                "description": "Gap size normalized by ATR against configured mechanical bounds.",
            },
            {
                "name": "displacement",
                "raw_score": displacement_score,
                "weight": 0.25,
                "source": "observed_displacement_candle",
                "description": "Whether displacement candle confirmation was observed.",
            },
            {
                "name": "volume_confirmation",
                "raw_score": volume_confirmation_score,
                "weight": 0.15,
                "source": "observed_volume_ratio",
                "description": "Relative volume confirmation at the pattern candle.",
            },
            {
                "name": "structure_alignment",
                "raw_score": structure_feature["score"],
                "weight": 0.15,
                "source": structure_feature["source"],
                "description": "No-lookahead swing-structure alignment at the FVG confirmation candle.",
                "metadata": structure_feature,
            },
            {
                "name": "support_resistance_context",
                "raw_score": support_feature["score"],
                "weight": 0.10,
                "source": support_feature["source"],
                "description": "No-lookahead proximity to confirmed support/resistance zones at the FVG reference price.",
                "metadata": support_feature,
            },
            {
                "name": "liquidity",
                "raw_score": liquidity_score,
                "weight": 0.10,
                "source": "placeholder_policy" if not config.require_liquidity_pass else "required_external_liquidity_flag",
                "is_placeholder": not config.require_liquidity_pass,
                "description": "Liquidity is a policy prior unless a caller explicitly requires an external liquidity pass flag.",
            },
            {
                "name": "freshness",
                "raw_score": freshness_score,
                "weight": 0.05,
                "source": "observed_lifecycle_state",
                "description": "Fresh or partially filled lifecycle state at signal time.",
            },
        ],
    )


def _context_pivots(
    candles: pd.DataFrame, current_index: int, config: PivotConfig | None
) -> pd.DataFrame:
    if current_index < 0:
        return pd.DataFrame()
    visible = candles.iloc[: current_index + 1]
    return detect_pivots(
        visible[["symbol", "timestamp", "open", "high", "low", "close"]],
        config,
    )


def _missing_score_feature(reason: str) -> dict[str, Any]:
    return {
        "feature_available": False,
        "source": "missing_context",
        "context": "MISSING_CONTEXT",
        "score": 0.0,
        "missing_context_reason": reason,
    }


def _classify_pattern_status(
    *,
    gap_size_atr: float,
    volume_ratio: float,
    pattern_score: float,
    config: FairValueGapConfig,
) -> PatternStatus:
    if gap_size_atr > config.maximum_gap_size_atr_multiplier:
        return PatternStatus.WEAK
    if volume_ratio < config.minimum_volume_ratio:
        return PatternStatus.WEAK
    if pattern_score < config.minimum_pattern_score:
        return PatternStatus.WEAK
    return PatternStatus.VALID


def _build_event_id(
    *,
    pattern_type: str,
    direction: str,
    symbol: str | None,
    timeframe: str | None,
    candle_1_timestamp: Any,
    candle_2_timestamp: Any,
    candle_3_timestamp: Any,
) -> str:
    raw = "|".join(
        [
            pattern_type,
            direction,
            str(symbol or ""),
            str(timeframe or ""),
            str(candle_1_timestamp),
            str(candle_2_timestamp),
            str(candle_3_timestamp),
        ]
    )
    digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{pattern_type}:{direction}:{digest}"


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))
