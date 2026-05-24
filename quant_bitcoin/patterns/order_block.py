"""Order Block pattern detection.

This module evaluates already-provided completed candle data and emits stable,
deterministic Order Block events. It is intentionally pure: it does not fetch
market data, read secrets, call exchange APIs, place orders, persist records, or
make trading decisions.

First-batch implementation notes:
- The initial implementation uses the nearest single opposing source candle
  before a valid displacement candle and the FULL_RANGE zone definition.
- Liquidity and bid-ask spread filters are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require pass/fail values once those filters are supplied.
- Pending source-candidate events and persisted lifecycle updates are deferred.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` to preserve deterministic streaming behavior.
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

REQUIRED_ORDER_BLOCK_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class OrderBlockDirection(Enum):
    """Supported Order Block directions."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NONE = "NONE"


class OrderBlockStatus(Enum):
    """Supported Order Block pattern statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


class OrderBlockState(Enum):
    """Supported Order Block lifecycle states."""

    FRESH = "FRESH"
    TOUCHED = "TOUCHED"
    MITIGATED = "MITIGATED"
    BROKEN = "BROKEN"
    INVALID = "INVALID"


class OrderBlockZoneDefinition(Enum):
    """Supported first-batch zone definitions."""

    FULL_RANGE = "FULL_RANGE"
    BODY_ONLY = "BODY_ONLY"
    WICK_ADJUSTED = "WICK_ADJUSTED"


@dataclass(frozen=True)
class OrderBlockConfig:
    """Configuration for deterministic Order Block detection."""

    source_search_lookback: int = 5
    allow_single_candle_order_block: bool = True
    allow_multi_candle_order_block: bool = False
    maximum_source_cluster_size: int = 3
    emit_retest_events: bool = False
    retest_entry_max_wait_bars: int | None = None
    zone_definition: OrderBlockZoneDefinition | str = OrderBlockZoneDefinition.FULL_RANGE
    require_displacement: bool = True
    minimum_displacement_body_ratio: float = 0.6
    minimum_displacement_atr_multiplier: float = 1.5
    minimum_volume_ratio: float = 1.5
    weak_volume_ratio: float = 1.3
    close_extreme_threshold: float = 0.25
    # Liquidity and spread modules are not implemented yet. The first detector
    # defaults these unavailable prerequisite filters to not required instead of
    # silently approximating them.
    require_liquidity_pass: bool = False
    require_spread_pass: bool = False
    liquidity_pass: bool | None = None
    spread_pass: bool | None = None
    require_structure_confirmation: bool = False
    minimum_zone_size_atr_multiplier: float = 0.1
    maximum_zone_size_atr_multiplier: float = 2.0
    mitigation_threshold: float = 0.5
    broken_atr_buffer_multiplier: float = 0.2
    stop_atr_buffer_multiplier: float = 0.2
    minimum_pattern_score: float = 0.7
    weak_pattern_score: float = 0.5
    default_entry_reference: str = "ZONE_MID"
    default_risk_reward: float = 2.0
    emit_invalid: bool = False
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None
    displacement_config: DisplacementCandleConfig | None = None
    pivot_config: PivotConfig | None = None
    support_resistance_config: SupportResistanceZoneConfig | None = None
    swing_structure_config: SwingStructureConfig | None = None
    retrospective_lifecycle: bool = False

    def __post_init__(self) -> None:
        if self.source_search_lookback < 1:
            raise ValueError("source_search_lookback must be at least 1")
        if self.maximum_source_cluster_size < 1:
            raise ValueError("maximum_source_cluster_size must be at least 1")
        if self.retest_entry_max_wait_bars is not None and self.retest_entry_max_wait_bars < 1:
            raise ValueError("retest_entry_max_wait_bars must be at least 1 when supplied")
        _coerce_zone_definition(self.zone_definition)
        if not self.allow_single_candle_order_block:
            raise ValueError("single-candle order blocks must be enabled in this batch")
        if not 0 <= self.minimum_displacement_body_ratio <= 1:
            raise ValueError("minimum_displacement_body_ratio must be between 0 and 1")
        if self.minimum_displacement_atr_multiplier < 0:
            raise ValueError("minimum_displacement_atr_multiplier must be non-negative")
        if self.weak_volume_ratio < 0:
            raise ValueError("weak_volume_ratio must be non-negative")
        if self.minimum_volume_ratio < self.weak_volume_ratio:
            raise ValueError(
                "minimum_volume_ratio must be greater than or equal to weak_volume_ratio"
            )
        if not 0 <= self.close_extreme_threshold <= 1:
            raise ValueError("close_extreme_threshold must be between 0 and 1")
        if self.minimum_zone_size_atr_multiplier < 0:
            raise ValueError("minimum_zone_size_atr_multiplier must be non-negative")
        if self.maximum_zone_size_atr_multiplier < self.minimum_zone_size_atr_multiplier:
            raise ValueError(
                "maximum_zone_size_atr_multiplier must be greater than or equal to "
                "minimum_zone_size_atr_multiplier"
            )
        if not 0 <= self.mitigation_threshold <= 1:
            raise ValueError("mitigation_threshold must be between 0 and 1")
        if self.broken_atr_buffer_multiplier < 0:
            raise ValueError("broken_atr_buffer_multiplier must be non-negative")
        if self.stop_atr_buffer_multiplier < 0:
            raise ValueError("stop_atr_buffer_multiplier must be non-negative")
        if not 0 <= self.weak_pattern_score <= self.minimum_pattern_score <= 1:
            raise ValueError(
                "weak_pattern_score and minimum_pattern_score must be between 0 and 1 "
                "with weak_pattern_score <= minimum_pattern_score"
            )
        if self.default_risk_reward <= 0:
            raise ValueError("default_risk_reward must be positive")


@dataclass(frozen=True)
class OrderBlockEvent:
    """Deterministic Order Block event."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    order_block_state: str
    source_candle_index: int
    source_candle_timestamp: Any
    displacement_candle_index: int
    displacement_candle_timestamp: Any
    zone_low: float
    zone_high: float
    zone_mid: float
    zone_size: float
    zone_size_atr: float
    source_mode: str
    source_cluster_start_index: int
    source_cluster_end_index: int
    source_cluster_size: int
    zone_definition: str
    detector_input_type: str
    displacement_direction: str
    displacement_range_atr: float
    body_ratio: float
    volume_ratio: float
    liquidity_pass: bool | None
    spread_pass: bool | None
    structure_confirmed: bool | None
    structure_event: str | None
    support_resistance_context: str | None
    mitigation_depth: float
    retest_entry_eligible: bool
    retest_wait_bars: int | None
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


def detect_order_blocks(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: OrderBlockConfig | None = None,
) -> list[OrderBlockEvent]:
    """Return Order Block events using signal-time no-lookahead semantics.

    By default mitigation/broken lifecycle fields are evaluated only through
    the displacement candle. Set ``OrderBlockConfig.retrospective_lifecycle=True``
    only for event-study analysis that intentionally reclassifies events with
    later candles.
    """

    order_block_config = config or OrderBlockConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < 2:
        return []

    _validate_external_filters(order_block_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        order_block_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(
        candle_frame,
        order_block_config.volume_ratio_config,
    )
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    displacement_rows = detect_displacement_candles(
        enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
        _displacement_config(order_block_config),
    )

    events: list[OrderBlockEvent] = []
    symbol_value = symbol or str(enriched.iloc[0]["symbol"])
    for displacement_index, displacement in displacement_rows.iterrows():
        if str(displacement["displacement_status"]) != DisplacementStatus.VALID.value:
            continue
        displacement_direction = str(displacement["displacement_direction"])
        if displacement_direction == DisplacementDirection.BULLISH.value:
            direction = OrderBlockDirection.BULLISH
            source_cluster = _find_source_cluster(enriched, displacement_index, direction, order_block_config)
        elif displacement_direction == DisplacementDirection.BEARISH.value:
            direction = OrderBlockDirection.BEARISH
            source_cluster = _find_source_cluster(enriched, displacement_index, direction, order_block_config)
        else:
            continue

        if source_cluster is None:
            continue

        event = _evaluate_order_block(
            direction,
            enriched,
            displacement,
            source_cluster,
            displacement_index,
            symbol=symbol_value,
            timeframe=timeframe,
            config=order_block_config,
        )
        if event is not None:
            events.append(event)

    return events


def detect_order_blocks_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: OrderBlockConfig | None = None,
) -> list[OrderBlockEvent]:
    """Return only events confirmed at ``current_index`` using visible candles."""

    if current_index < 0:
        return []
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if current_index >= len(frame):
        return []
    events = detect_order_blocks(
        frame.iloc[: current_index + 1],
        symbol=symbol,
        timeframe=timeframe,
        config=config,
    )
    return [event for event in events if event.end_index == current_index]


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]], symbol: str | None
) -> pd.DataFrame:
    if isinstance(candles, pd.DataFrame):
        frame = candles.copy(deep=True)
    else:
        frame = pd.DataFrame(list(candles)).copy(deep=True)

    missing_columns = [
        column
        for column in REQUIRED_ORDER_BLOCK_CANDLE_COLUMNS
        if column not in frame.columns
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


def _validate_external_filters(config: OrderBlockConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _displacement_config(config: OrderBlockConfig) -> DisplacementCandleConfig:
    if config.displacement_config is not None:
        return config.displacement_config
    return DisplacementCandleConfig(
        minimum_body_ratio=config.minimum_displacement_body_ratio,
        minimum_range_atr_multiplier=config.minimum_displacement_atr_multiplier,
        minimum_volume_ratio=config.weak_volume_ratio,
        minimum_close_position_ratio=1.0 - config.close_extreme_threshold,
    )


def _find_source_cluster(
    candles: pd.DataFrame,
    displacement_index: int,
    direction: OrderBlockDirection,
    config: OrderBlockConfig,
) -> tuple[int, int] | None:
    start_index = max(0, displacement_index - config.source_search_lookback)
    for source_index in range(displacement_index - 1, start_index - 1, -1):
        source = candles.iloc[source_index]
        if not _is_opposing_source_candle(source, direction):
            continue
        if not config.allow_multi_candle_order_block:
            return source_index, source_index
        cluster_start = source_index
        max_start = max(start_index, source_index - config.maximum_source_cluster_size + 1)
        for candidate_index in range(source_index - 1, max_start - 1, -1):
            if not _is_opposing_source_candle(candles.iloc[candidate_index], direction):
                break
            cluster_start = candidate_index
        return cluster_start, source_index
    return None


def _is_opposing_source_candle(source: pd.Series, direction: OrderBlockDirection) -> bool:
    if direction == OrderBlockDirection.BULLISH:
        return float(source["close"]) < float(source["open"])
    return float(source["close"]) > float(source["open"])


def _evaluate_order_block(
    direction: OrderBlockDirection,
    candles: pd.DataFrame,
    displacement: pd.Series,
    source_cluster: tuple[int, int],
    displacement_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: OrderBlockConfig,
) -> OrderBlockEvent | None:
    source_start_index, source_end_index = source_cluster
    source_index = source_end_index
    displacement_candle = candles.iloc[displacement_index]
    atr = _optional_float(displacement_candle["atr"])
    volume_ratio = _optional_float(displacement_candle["volume_ratio"])
    candle_range = _optional_float(displacement["candle_range"])
    body_ratio = _optional_float(displacement["body_ratio"])
    if atr is None or atr <= 0 or volume_ratio is None or candle_range is None or body_ratio is None:
        return None

    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    displacement_range_atr = candle_range / atr
    if displacement_range_atr < config.minimum_displacement_atr_multiplier:
        return None
    if volume_ratio < config.weak_volume_ratio:
        return None

    source_frame = candles.iloc[source_start_index : source_end_index + 1]
    zone = _zone_boundaries(source_frame, direction, config)
    if zone is None:
        return None
    zone_low, zone_high = zone
    zone_size = zone_high - zone_low
    if zone_size <= 0:
        return None
    zone_size_atr = zone_size / atr
    if zone_size_atr < config.minimum_zone_size_atr_multiplier:
        return None
    if zone_size_atr > config.maximum_zone_size_atr_multiplier:
        return None

    lifecycle_candles = candles if (config.retrospective_lifecycle or config.emit_retest_events) else candles.iloc[: displacement_index + 1]
    state, mitigation_depth, state_index = _classify_state(
        direction,
        lifecycle_candles,
        displacement_index,
        zone_low,
        zone_high,
        zone_size,
        atr,
        config,
    )
    if state == OrderBlockState.BROKEN:
        return None
    retest_entry_eligible = state in {OrderBlockState.TOUCHED, OrderBlockState.MITIGATED}
    retest_wait_bars = None if state_index is None else state_index - displacement_index
    if config.emit_retest_events:
        if config.retest_entry_max_wait_bars is not None:
            visible_wait_bars = len(candles) - displacement_index - 1
            if not retest_entry_eligible and visible_wait_bars >= config.retest_entry_max_wait_bars:
                return None
            if retest_wait_bars is not None and retest_wait_bars > config.retest_entry_max_wait_bars:
                return None
        if not retest_entry_eligible:
            return None

    zone_mid = (zone_low + zone_high) / 2
    context_pivots = _context_pivots(candles, displacement_index, config.pivot_config)
    support_resistance_feature = support_resistance_proximity_feature(
        context_pivots,
        current_index=displacement_index,
        price=zone_mid,
        direction=direction.value,
        atr=atr,
        config=config.support_resistance_config,
    )
    swing_structure_feature = swing_structure_alignment_feature(
        context_pivots,
        current_index=displacement_index,
        direction=direction.value,
        config=config.swing_structure_config,
    )

    score_metadata = _calculate_pattern_score_metadata(
        displacement_range_atr=displacement_range_atr,
        body_ratio=body_ratio,
        volume_ratio=volume_ratio,
        zone_size_atr=zone_size_atr,
        order_block_state=state,
        support_resistance_feature=support_resistance_feature,
        swing_structure_feature=swing_structure_feature,
        config=config,
    )
    pattern_score = float(score_metadata["pattern_score"])
    if volume_ratio < config.minimum_volume_ratio:
        pattern_status = OrderBlockStatus.WEAK
    elif pattern_score >= config.minimum_pattern_score:
        pattern_status = OrderBlockStatus.VALID
    elif pattern_score >= config.weak_pattern_score:
        pattern_status = OrderBlockStatus.WEAK
    else:
        return None

    entry_reference = _entry_reference(zone_low, zone_high, zone_mid, config)
    stop_reference = _stop_reference(direction, zone_low, zone_high, atr, config)
    target_reference, risk_reward = _target_and_risk_reward(
        direction,
        entry_reference,
        stop_reference,
        config,
    )
    if risk_reward is None:
        return None

    event_id = _build_event_id(
        pattern_type="ORDER_BLOCK",
        direction=direction.value,
        symbol=symbol,
        timeframe=timeframe,
        source_timestamp=candles.iloc[source_start_index]["timestamp"],
        displacement_timestamp=displacement_candle["timestamp"],
    )
    source_cluster_size = source_end_index - source_start_index + 1
    source_mode = "MULTI_CANDLE_CLUSTER" if source_cluster_size > 1 else "SINGLE_CANDLE"
    event_end_index = state_index if config.emit_retest_events and state_index is not None else displacement_index

    return OrderBlockEvent(
        event_id=event_id,
        pattern_type="ORDER_BLOCK",
        direction=direction.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=displacement_candle["timestamp"],
        start_index=source_start_index,
        end_index=event_end_index,
        order_block_state=state.value,
        source_candle_index=source_index,
        source_candle_timestamp=candles.iloc[source_index]["timestamp"],
        displacement_candle_index=displacement_index,
        displacement_candle_timestamp=displacement_candle["timestamp"],
        zone_low=zone_low,
        zone_high=zone_high,
        zone_mid=zone_mid,
        zone_size=zone_size,
        zone_size_atr=zone_size_atr,
        source_mode=source_mode,
        source_cluster_start_index=source_start_index,
        source_cluster_end_index=source_end_index,
        source_cluster_size=source_cluster_size,
        zone_definition=_coerce_zone_definition(config.zone_definition).value,
        detector_input_type="OHLCV_HEURISTIC",
        displacement_direction=direction.value,
        displacement_range_atr=displacement_range_atr,
        body_ratio=body_ratio,
        volume_ratio=volume_ratio,
        liquidity_pass=config.liquidity_pass,
        spread_pass=config.spread_pass,
        structure_confirmed=bool(swing_structure_feature.get("feature_available")),
        structure_event=str(swing_structure_feature.get("context")),
        support_resistance_context=str(support_resistance_feature.get("context")),
        mitigation_depth=mitigation_depth,
        retest_entry_eligible=retest_entry_eligible,
        retest_wait_bars=retest_wait_bars,
        pattern_score=pattern_score,
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        reason=(
            f"{direction.value.title()} Order Block detected from OHLCV heuristic "
            f"{source_mode.lower()} before valid displacement."
        ),
        score_components=score_metadata["score_components"],
        score_component_sources=score_metadata["score_component_sources"],
        score_limitations=score_metadata["score_limitations"],
        score_calibration=score_metadata["score_calibration"],
        executable_pattern_score=score_metadata["executable_pattern_score"],
        diagnostic_pattern_score=score_metadata["diagnostic_pattern_score"],
        atr_metadata=atr_timing_metadata(config.atr_config),
    )


def _zone_boundaries(
    source: pd.DataFrame,
    direction: OrderBlockDirection,
    config: OrderBlockConfig,
) -> tuple[float, float] | None:
    zone_definition = _coerce_zone_definition(config.zone_definition)
    high = float(source["high"].max())
    low = float(source["low"].min())

    if zone_definition == OrderBlockZoneDefinition.FULL_RANGE:
        return low, high
    if zone_definition == OrderBlockZoneDefinition.BODY_ONLY:
        if direction == OrderBlockDirection.BULLISH:
            open_price = float(source["open"].max())
            return low, open_price
        close = float(source["close"].min())
        return close, high
    if zone_definition == OrderBlockZoneDefinition.WICK_ADJUSTED:
        if direction == OrderBlockDirection.BULLISH:
            body_top = float(source[["open", "close"]].max(axis=1).max())
            return low, body_top
        body_bottom = float(source[["open", "close"]].min(axis=1).min())
        return body_bottom, high
    return None


def _classify_state(
    direction: OrderBlockDirection,
    candles: pd.DataFrame,
    displacement_index: int,
    zone_low: float,
    zone_high: float,
    zone_size: float,
    atr: float,
    config: OrderBlockConfig,
) -> tuple[OrderBlockState, float, int | None]:
    later_candles = candles.iloc[displacement_index + 1 :]
    if later_candles.empty:
        return OrderBlockState.FRESH, 0.0, None

    if direction == OrderBlockDirection.BULLISH:
        broken = (later_candles["close"] < zone_low - config.broken_atr_buffer_multiplier * atr).any()
        touched_rows = later_candles[(later_candles["low"] <= zone_high) & (later_candles["close"] >= zone_low)]
        if broken:
            lowest_low = float(later_candles["low"].min())
            broken_index = int(later_candles[later_candles["close"] < zone_low - config.broken_atr_buffer_multiplier * atr].index[0])
            return OrderBlockState.BROKEN, _clamp((zone_high - lowest_low) / zone_size), broken_index
        if touched_rows.empty:
            return OrderBlockState.FRESH, 0.0, None
        lowest_low = float(touched_rows["low"].min())
        mitigation_depth = _clamp((zone_high - lowest_low) / zone_size)
        state_index = int(touched_rows.index[0])
    else:
        broken = (later_candles["close"] > zone_high + config.broken_atr_buffer_multiplier * atr).any()
        touched_rows = later_candles[(later_candles["high"] >= zone_low) & (later_candles["close"] <= zone_high)]
        if broken:
            highest_high = float(later_candles["high"].max())
            broken_index = int(later_candles[later_candles["close"] > zone_high + config.broken_atr_buffer_multiplier * atr].index[0])
            return OrderBlockState.BROKEN, _clamp((highest_high - zone_low) / zone_size), broken_index
        if touched_rows.empty:
            return OrderBlockState.FRESH, 0.0, None
        highest_high = float(touched_rows["high"].max())
        mitigation_depth = _clamp((highest_high - zone_low) / zone_size)
        state_index = int(touched_rows.index[0])

    if mitigation_depth >= config.mitigation_threshold:
        return OrderBlockState.MITIGATED, mitigation_depth, state_index
    return OrderBlockState.TOUCHED, mitigation_depth, state_index


def _calculate_pattern_score(
    *,
    displacement_range_atr: float,
    body_ratio: float,
    volume_ratio: float,
    zone_size_atr: float,
    order_block_state: OrderBlockState,
    config: OrderBlockConfig,
    support_resistance_feature: dict[str, Any] | None = None,
    swing_structure_feature: dict[str, Any] | None = None,
) -> float:
    return float(
        _calculate_pattern_score_metadata(
            displacement_range_atr=displacement_range_atr,
            body_ratio=body_ratio,
            volume_ratio=volume_ratio,
            zone_size_atr=zone_size_atr,
            order_block_state=order_block_state,
            support_resistance_feature=support_resistance_feature,
            swing_structure_feature=swing_structure_feature,
            config=config,
        )["pattern_score"]
    )


def _calculate_pattern_score_metadata(
    *,
    displacement_range_atr: float,
    body_ratio: float,
    volume_ratio: float,
    zone_size_atr: float,
    order_block_state: OrderBlockState,
    config: OrderBlockConfig,
    support_resistance_feature: dict[str, Any] | None = None,
    swing_structure_feature: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if displacement_range_atr >= 2.0 and body_ratio >= 0.7:
        displacement_score = 1.0
    elif (
        displacement_range_atr >= config.minimum_displacement_atr_multiplier
        and body_ratio >= config.minimum_displacement_body_ratio
    ):
        displacement_score = 0.8
    else:
        displacement_score = 0.0

    if volume_ratio >= 2.0:
        volume_confirmation_score = 1.0
    elif volume_ratio >= config.minimum_volume_ratio:
        volume_confirmation_score = 0.8
    elif volume_ratio >= config.weak_volume_ratio:
        volume_confirmation_score = 0.5
    else:
        volume_confirmation_score = 0.0

    structure_feature = swing_structure_feature or _missing_score_feature(
        reason="feature_not_computed"
    )
    if 0.25 <= zone_size_atr <= 1.0:
        zone_quality_score = 1.0
    elif config.minimum_zone_size_atr_multiplier <= zone_size_atr <= config.maximum_zone_size_atr_multiplier:
        zone_quality_score = 0.7
    else:
        zone_quality_score = 0.0

    liquidity_score = 0.8 if not config.require_liquidity_pass else 1.0
    support_feature = support_resistance_feature or _missing_score_feature(
        reason="feature_not_computed"
    )
    if order_block_state == OrderBlockState.FRESH:
        freshness_score = 1.0
    elif order_block_state == OrderBlockState.TOUCHED:
        freshness_score = 0.7
    elif order_block_state == OrderBlockState.MITIGATED:
        freshness_score = 0.4
    else:
        freshness_score = 0.0

    return build_score_metadata(
        "ORDER_BLOCK",
        [
            {"name": "displacement", "raw_score": displacement_score, "weight": 0.25, "source": "observed_displacement_candle", "description": "Displacement range/body ratio confirmation."},
            {"name": "volume_confirmation", "raw_score": volume_confirmation_score, "weight": 0.15, "source": "observed_volume_ratio", "description": "Relative volume on displacement candle."},
            {"name": "structure_confirmation", "raw_score": structure_feature["score"], "weight": 0.15, "source": structure_feature["source"], "description": "No-lookahead swing-structure alignment at the Order Block displacement candle.", "metadata": structure_feature},
            {"name": "zone_quality", "raw_score": zone_quality_score, "weight": 0.15, "source": "observed_zone_size_atr", "description": "Order block zone size normalized by ATR."},
            {"name": "liquidity", "raw_score": liquidity_score, "weight": 0.10, "source": "placeholder_policy" if not config.require_liquidity_pass else "required_external_liquidity_flag", "is_placeholder": not config.require_liquidity_pass, "description": "Liquidity is a policy prior unless required externally by the caller."},
            {"name": "support_resistance_context", "raw_score": support_feature["score"], "weight": 0.10, "source": support_feature["source"], "description": "No-lookahead proximity to confirmed support/resistance zones at the Order Block zone midpoint.", "metadata": support_feature},
            {"name": "freshness", "raw_score": freshness_score, "weight": 0.10, "source": "observed_lifecycle_state", "description": "Fresh/touched/mitigated order-block lifecycle state."},
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


def _entry_reference(
    zone_low: float,
    zone_high: float,
    zone_mid: float,
    config: OrderBlockConfig,
) -> float:
    reference = config.default_entry_reference.upper()
    if reference == "ZONE_HIGH":
        return zone_high
    if reference == "ZONE_LOW":
        return zone_low
    return zone_mid


def _stop_reference(
    direction: OrderBlockDirection,
    zone_low: float,
    zone_high: float,
    atr: float,
    config: OrderBlockConfig,
) -> float:
    if direction == OrderBlockDirection.BULLISH:
        return zone_low - config.stop_atr_buffer_multiplier * atr
    return zone_high + config.stop_atr_buffer_multiplier * atr


def _target_and_risk_reward(
    direction: OrderBlockDirection,
    entry_reference: float,
    stop_reference: float,
    config: OrderBlockConfig,
) -> tuple[float, float | None]:
    if direction == OrderBlockDirection.BULLISH:
        risk = entry_reference - stop_reference
        if risk <= 0:
            return entry_reference, None
        target_reference = entry_reference + config.default_risk_reward * risk
        reward = target_reference - entry_reference
    else:
        risk = stop_reference - entry_reference
        if risk <= 0:
            return entry_reference, None
        target_reference = entry_reference - config.default_risk_reward * risk
        reward = entry_reference - target_reference
    return target_reference, reward / risk


def _build_event_id(
    *,
    pattern_type: str,
    direction: str,
    symbol: str | None,
    timeframe: str | None,
    source_timestamp: Any,
    displacement_timestamp: Any,
) -> str:
    raw = "|".join(
        [
            pattern_type,
            direction,
            str(symbol or ""),
            str(timeframe or ""),
            str(source_timestamp),
            str(displacement_timestamp),
        ]
    )
    digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{pattern_type}:{direction}:{digest}"


def _coerce_zone_definition(
    zone_definition: OrderBlockZoneDefinition | str,
) -> OrderBlockZoneDefinition:
    if isinstance(zone_definition, OrderBlockZoneDefinition):
        return zone_definition
    try:
        return OrderBlockZoneDefinition(str(zone_definition).upper())
    except ValueError as exc:
        allowed = ", ".join(definition.value for definition in OrderBlockZoneDefinition)
        raise ValueError(f"zone_definition must be one of: {allowed}") from exc


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))
