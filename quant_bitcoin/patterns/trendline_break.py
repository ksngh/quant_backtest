"""Trendline Break pattern detection.

This module evaluates already-provided completed candle data and emits stable,
deterministic Trendline Break events. It is intentionally pure: it does not
fetch market data, read secrets, call exchange APIs, place orders, persist
records, or make trading decisions.

First-batch implementation notes:
- The initial implementation uses two-point trendlines from confirmed pivot
  highs/lows and deterministic best-candidate selection.
- Liquidity and bid-ask spread filters are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require pass/fail values once those filters are supplied.
- Pending events are not emitted in this first batch; candles that do not break
  the trendline with the configured ATR buffer are ignored.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` to preserve deterministic streaming behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from itertools import combinations
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, atr_timing_metadata, calculate_atr
from quant_bitcoin.indicators.displacement_candle import (
    DisplacementCandleConfig,
    DisplacementDirection,
    DisplacementStatus,
    detect_displacement_candles,
)
from quant_bitcoin.indicators.pivots import (
    PivotConfig,
    PivotType,
    detect_pivots,
    pivot_strength_diagnostics,
)
from quant_bitcoin.indicators.swing_structure import (
    SwingStructureConfig,
    swing_structure_alignment_feature,
)
from quant_bitcoin.indicators.volume_ratio import VolumeRatioConfig, calculate_volume_ratio
from quant_bitcoin.patterns.score_metadata import build_score_metadata

REQUIRED_TRENDLINE_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class TrendlineBreakDirection(Enum):
    """Supported Trendline Break directions."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NONE = "NONE"


class TrendlineBreakStatus(Enum):
    """Supported Trendline Break statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


class TrendlineType(Enum):
    """Supported first-batch trendline types."""

    DESCENDING_RESISTANCE = "DESCENDING_RESISTANCE"
    ASCENDING_SUPPORT = "ASCENDING_SUPPORT"
    INVALID = "INVALID"


@dataclass(frozen=True)
class TrendlineBreakConfig:
    """Configuration for deterministic Trendline Break detection."""

    minimum_touch_count: int = 2
    strong_touch_count: int = 3
    maximum_pivot_lookback: int = 50
    max_recent_pivots: int = 80
    max_trendline_pairs_per_bar: int = 200
    minimum_trendline_length: int = 10
    maximum_trendline_length: int = 200
    minimum_slope_abs: float = 0.0
    maximum_slope_abs: float | None = None
    maximum_allowed_touch_deviation_atr: float = 0.5
    breakout_atr_multiplier: float = 0.2
    minimum_volume_ratio: float = 1.5
    weak_volume_ratio: float = 1.3
    # Liquidity and spread modules are not implemented yet. The first detector
    # defaults these unavailable prerequisite filters to not required instead of
    # silently approximating them.
    require_liquidity_pass: bool = False
    require_spread_pass: bool = False
    liquidity_pass: bool | None = None
    spread_pass: bool | None = None
    require_confirmed_pivots: bool = True
    require_independent_third_touch: bool = False
    retest_entry_max_wait_bars: int | None = None
    follow_through_confirmation_bars: int = 0
    allow_displacement_bonus: bool = True
    minimum_pattern_score: float = 0.7
    emit_pending: bool = False
    pivot_config: PivotConfig | None = None
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None
    displacement_config: DisplacementCandleConfig | None = None
    swing_structure_config: SwingStructureConfig | None = None

    def __post_init__(self) -> None:
        if self.minimum_touch_count < 2:
            raise ValueError("minimum_touch_count must be at least 2")
        if self.strong_touch_count < self.minimum_touch_count:
            raise ValueError(
                "strong_touch_count must be greater than or equal to minimum_touch_count"
            )
        if self.maximum_pivot_lookback < 1:
            raise ValueError("maximum_pivot_lookback must be at least 1")
        if self.max_recent_pivots < 2:
            raise ValueError("max_recent_pivots must be at least 2")
        if self.max_trendline_pairs_per_bar < 1:
            raise ValueError("max_trendline_pairs_per_bar must be at least 1")
        if self.minimum_trendline_length < 1:
            raise ValueError("minimum_trendline_length must be at least 1")
        if self.maximum_trendline_length < self.minimum_trendline_length:
            raise ValueError(
                "maximum_trendline_length must be greater than or equal to "
                "minimum_trendline_length"
            )
        if self.minimum_slope_abs < 0:
            raise ValueError("minimum_slope_abs must be non-negative")
        if self.maximum_slope_abs is not None and self.maximum_slope_abs < 0:
            raise ValueError("maximum_slope_abs must be non-negative when supplied")
        if self.maximum_allowed_touch_deviation_atr < 0:
            raise ValueError("maximum_allowed_touch_deviation_atr must be non-negative")
        if self.retest_entry_max_wait_bars is not None and self.retest_entry_max_wait_bars < 1:
            raise ValueError("retest_entry_max_wait_bars must be at least 1 when supplied")
        if self.follow_through_confirmation_bars < 0:
            raise ValueError("follow_through_confirmation_bars must be non-negative")
        if self.breakout_atr_multiplier < 0:
            raise ValueError("breakout_atr_multiplier must be non-negative")
        if self.weak_volume_ratio < 0:
            raise ValueError("weak_volume_ratio must be non-negative")
        if self.minimum_volume_ratio < self.weak_volume_ratio:
            raise ValueError(
                "minimum_volume_ratio must be greater than or equal to weak_volume_ratio"
            )
        if not 0 <= self.minimum_pattern_score <= 1:
            raise ValueError("minimum_pattern_score must be between 0 and 1")


@dataclass(frozen=True)
class TrendlineBreakEvent:
    """Deterministic Trendline Break event."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    trendline_type: str
    trendline_slope: float
    trendline_intercept: float
    touch_count: int
    fit_pivot_count: int
    validation_touch_count: int
    source_pivot_indices: tuple[int, ...]
    fit_pivot_indices: tuple[int, ...]
    validation_touch_indices: tuple[int, ...]
    touch_deviations: tuple[float, ...]
    trendline_value: float
    break_price: float
    break_distance: float
    break_distance_atr: float
    atr: float
    volume_ratio: float
    liquidity_pass: bool | None
    spread_pass: bool | None
    displacement_confirmed: bool
    retest_entry_eligible: bool
    retest_wait_bars: int | None
    follow_through_bars: int
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
    pivot_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _TrendlineCandidate:
    trendline_type: TrendlineType
    source_pivot_indices: tuple[int, ...]
    fit_pivot_indices: tuple[int, int]
    validation_touch_indices: tuple[int, ...]
    touch_deviations: tuple[float, ...]
    slope: float
    intercept: float
    touch_count: int
    trendline_length: int


def detect_trendline_breaks(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: TrendlineBreakConfig | None = None,
) -> list[TrendlineBreakEvent]:
    """Return deterministic Trendline Break events from completed candles.

    The first Trendline Break batch emits completed ``VALID`` or ``WEAK`` break
    events. ``PENDING`` events are supported by configuration but disabled by
    default to avoid noisy repeated rolling-window emissions before a break.
    """

    trendline_config = config or TrendlineBreakConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < 3:
        return []

    _validate_external_filters(trendline_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        trendline_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(
        candle_frame,
        trendline_config.volume_ratio_config,
    )
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    pivot_rows = detect_pivots(
        enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr"]],
        trendline_config.pivot_config,
    )
    if trendline_config.require_confirmed_pivots:
        pivot_rows = pivot_rows[pivot_rows["is_confirmed"] == True]

    displacement_rows = _detect_displacements(enriched, trendline_config)

    events: list[TrendlineBreakEvent] = []
    symbol_value = symbol or str(enriched.iloc[0]["symbol"])
    for current_index in range(len(enriched)):
        atr = _optional_float(enriched.iloc[current_index]["atr"])
        volume_ratio = _optional_float(enriched.iloc[current_index]["volume_ratio"])
        if atr is None or atr <= 0 or volume_ratio is None:
            continue

        visible_pivots = pivot_rows[
            (pivot_rows["confirmed_index"] <= current_index)
            & (pivot_rows["pivot_index"] < current_index)
            & (current_index - pivot_rows["pivot_index"] <= trendline_config.maximum_pivot_lookback)
        ]
        if len(visible_pivots) > trendline_config.max_recent_pivots:
            visible_pivots = visible_pivots.nlargest(
                trendline_config.max_recent_pivots, "pivot_index", keep="last"
            )
        if visible_pivots.empty:
            continue

        candidates = _build_candidates(
            visible_pivots,
            enriched,
            current_index,
            trendline_config,
        )
        evaluated = [
            event
            for candidate in candidates
            if (
                event := _evaluate_candidate(
                    candidate,
                    enriched,
                    pivot_rows,
                    displacement_rows,
                    current_index,
                    symbol=symbol_value,
                    timeframe=timeframe,
                    config=trendline_config,
                )
            )
            is not None
        ]
        if evaluated:
            events.append(_select_best_event(evaluated))

    return events


def detect_trendline_breaks_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: TrendlineBreakConfig | None = None,
) -> list[TrendlineBreakEvent]:
    """Return only trendline-break events confirmed at ``current_index``."""

    if current_index < 0:
        return []
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if current_index >= len(frame):
        return []
    events = detect_trendline_breaks(
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
        for column in REQUIRED_TRENDLINE_CANDLE_COLUMNS
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


def _validate_external_filters(config: TrendlineBreakConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _detect_displacements(
    candles: pd.DataFrame, config: TrendlineBreakConfig
) -> pd.DataFrame | None:
    if not config.allow_displacement_bonus:
        return None
    return detect_displacement_candles(
        candles[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
        config.displacement_config,
    )


def _build_candidates(
    visible_pivots: pd.DataFrame,
    candles: pd.DataFrame,
    current_index: int,
    config: TrendlineBreakConfig,
) -> list[_TrendlineCandidate]:
    candidates: list[_TrendlineCandidate] = []
    candidates.extend(
        _build_direction_candidates(
            visible_pivots,
            candles,
            current_index,
            config,
            pivot_types={PivotType.PIVOT_HIGH.value, PivotType.BOTH.value},
            trendline_type=TrendlineType.DESCENDING_RESISTANCE,
        )
    )
    candidates.extend(
        _build_direction_candidates(
            visible_pivots,
            candles,
            current_index,
            config,
            pivot_types={PivotType.PIVOT_LOW.value, PivotType.BOTH.value},
            trendline_type=TrendlineType.ASCENDING_SUPPORT,
        )
    )
    return candidates


def _build_direction_candidates(
    visible_pivots: pd.DataFrame,
    candles: pd.DataFrame,
    current_index: int,
    config: TrendlineBreakConfig,
    *,
    pivot_types: set[str],
    trendline_type: TrendlineType,
) -> list[_TrendlineCandidate]:
    direction_pivots = visible_pivots[visible_pivots["pivot_type"].isin(pivot_types)]
    if len(direction_pivots) < config.minimum_touch_count:
        return []

    records = list(direction_pivots.sort_values("pivot_index").to_dict("records"))
    candidates: list[_TrendlineCandidate] = []
    pair_count = 0
    for older, newer in combinations(records, 2):
        pair_count += 1
        if pair_count > config.max_trendline_pairs_per_bar:
            break
        older_index = int(older["pivot_index"])
        newer_index = int(newer["pivot_index"])
        trendline_length = newer_index - older_index
        if trendline_length < config.minimum_trendline_length:
            continue
        if trendline_length > config.maximum_trendline_length:
            continue

        slope = (float(newer["price"]) - float(older["price"])) / trendline_length
        if not _valid_slope(slope, trendline_type, config):
            continue
        intercept = float(older["price"]) - slope * older_index
        touches = _touching_pivots(records, candles, slope, intercept, config)
        touch_indices = tuple(index for index, _ in touches)
        validation_touch_indices = tuple(index for index in touch_indices if index not in {older_index, newer_index})
        if len(touch_indices) < config.minimum_touch_count:
            continue
        if config.require_independent_third_touch and not validation_touch_indices:
            continue

        candidates.append(
            _TrendlineCandidate(
                trendline_type=trendline_type,
                source_pivot_indices=touch_indices,
                fit_pivot_indices=(older_index, newer_index),
                validation_touch_indices=validation_touch_indices,
                touch_deviations=tuple(deviation for _, deviation in touches),
                slope=slope,
                intercept=intercept,
                touch_count=len(touch_indices),
                trendline_length=trendline_length,
            )
        )

    return candidates


def _valid_slope(
    slope: float, trendline_type: TrendlineType, config: TrendlineBreakConfig
) -> bool:
    if abs(slope) <= config.minimum_slope_abs:
        return False
    if config.maximum_slope_abs is not None and abs(slope) > config.maximum_slope_abs:
        return False
    if trendline_type == TrendlineType.DESCENDING_RESISTANCE:
        return slope < 0
    if trendline_type == TrendlineType.ASCENDING_SUPPORT:
        return slope > 0
    return False


def _touching_pivots(
    pivot_records: list[dict[str, Any]],
    candles: pd.DataFrame,
    slope: float,
    intercept: float,
    config: TrendlineBreakConfig,
) -> list[tuple[int, float]]:
    touches: list[tuple[int, float]] = []
    for pivot in pivot_records:
        pivot_index = int(pivot["pivot_index"])
        trendline_value = _trendline_value(slope, intercept, pivot_index)
        deviation = abs(float(pivot["price"]) - trendline_value)
        atr = _optional_float(candles.iloc[pivot_index]["atr"])
        max_deviation = 0.0
        if atr is not None:
            max_deviation = config.maximum_allowed_touch_deviation_atr * atr
        if deviation <= max_deviation:
            touches.append((pivot_index, deviation))
    return touches


def _evaluate_candidate(
    candidate: _TrendlineCandidate,
    candles: pd.DataFrame,
    all_pivots: pd.DataFrame,
    displacement_rows: pd.DataFrame | None,
    current_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: TrendlineBreakConfig,
) -> TrendlineBreakEvent | None:
    current = candles.iloc[current_index]
    atr = _optional_float(current["atr"])
    volume_ratio = _optional_float(current["volume_ratio"])
    if atr is None or atr <= 0 or volume_ratio is None:
        return None

    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    trendline_value = _trendline_value(candidate.slope, candidate.intercept, current_index)
    break_price = float(current["close"])
    if candidate.trendline_type == TrendlineType.DESCENDING_RESISTANCE:
        direction = TrendlineBreakDirection.BULLISH
        break_distance = break_price - trendline_value
        expected_displacement = DisplacementDirection.BULLISH.value
    else:
        direction = TrendlineBreakDirection.BEARISH
        break_distance = trendline_value - break_price
        expected_displacement = DisplacementDirection.BEARISH.value

    break_distance_atr = break_distance / atr
    if break_distance <= 0 or break_distance_atr < config.breakout_atr_multiplier:
        if not config.emit_pending:
            return None
        pattern_status = TrendlineBreakStatus.PENDING
    elif volume_ratio < config.weak_volume_ratio:
        return None
    elif volume_ratio < config.minimum_volume_ratio:
        pattern_status = TrendlineBreakStatus.WEAK
    else:
        pattern_status = TrendlineBreakStatus.VALID

    follow_through_end_index = _follow_through_end_index(
        candidate,
        candles,
        current_index,
        direction,
        config.follow_through_confirmation_bars,
    )
    if follow_through_end_index is None:
        return None
    retest_wait_bars = _trendline_retest_wait_bars(
        candidate,
        candles,
        current_index,
        direction,
        config.retest_entry_max_wait_bars,
    )
    retest_entry_eligible = retest_wait_bars is not None

    displacement_confirmed = _displacement_confirmed(
        displacement_rows,
        current_index,
        expected_displacement,
    )
    swing_structure_feature = swing_structure_alignment_feature(
        all_pivots,
        current_index=current_index,
        direction=direction.value,
        config=config.swing_structure_config,
    )
    source_pivots = all_pivots[
        all_pivots["pivot_index"].isin(candidate.source_pivot_indices)
    ]
    score_metadata = _calculate_pattern_score_metadata(
        candidate=candidate,
        break_distance_atr=max(break_distance_atr, 0.0),
        volume_ratio=volume_ratio,
        displacement_confirmed=displacement_confirmed,
        swing_structure_feature=swing_structure_feature,
        config=config,
    )
    pattern_score = float(score_metadata["pattern_score"])
    if (
        pattern_status == TrendlineBreakStatus.VALID
        and pattern_score < config.minimum_pattern_score
    ):
        pattern_status = TrendlineBreakStatus.WEAK

    entry_reference = break_price
    stop_reference = _stop_reference(
        direction,
        all_pivots,
        current_index,
        trendline_value,
        atr,
    )
    target_reference, risk_reward = _target_and_risk_reward(
        direction,
        entry_reference,
        stop_reference,
    )
    if risk_reward is None:
        return None

    event_id = _build_event_id(
        pattern_type="TRENDLINE_BREAK",
        direction=direction.value,
        symbol=symbol,
        timeframe=timeframe,
        source_pivot_timestamps=tuple(
            candles.iloc[pivot_index]["timestamp"]
            for pivot_index in candidate.source_pivot_indices
        ),
        breakout_timestamp=current["timestamp"],
    )

    return TrendlineBreakEvent(
        event_id=event_id,
        pattern_type="TRENDLINE_BREAK",
        direction=direction.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=candles.iloc[follow_through_end_index]["timestamp"],
        start_index=min(candidate.source_pivot_indices),
        end_index=follow_through_end_index,
        trendline_type=candidate.trendline_type.value,
        trendline_slope=candidate.slope,
        trendline_intercept=candidate.intercept,
        touch_count=candidate.touch_count,
        fit_pivot_count=len(candidate.fit_pivot_indices),
        validation_touch_count=len(candidate.validation_touch_indices),
        source_pivot_indices=candidate.source_pivot_indices,
        fit_pivot_indices=candidate.fit_pivot_indices,
        validation_touch_indices=candidate.validation_touch_indices,
        touch_deviations=candidate.touch_deviations,
        trendline_value=trendline_value,
        break_price=break_price,
        break_distance=break_distance,
        break_distance_atr=break_distance_atr,
        atr=atr,
        volume_ratio=volume_ratio,
        liquidity_pass=config.liquidity_pass,
        spread_pass=config.spread_pass,
        displacement_confirmed=displacement_confirmed,
        retest_entry_eligible=retest_entry_eligible,
        retest_wait_bars=retest_wait_bars,
        follow_through_bars=config.follow_through_confirmation_bars,
        pattern_score=pattern_score,
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        reason=(
            f"{direction.value.title()} Trendline Break detected with "
            f"{candidate.trendline_type.value} and ATR-buffered close."
        ),
        score_components=score_metadata["score_components"],
        score_component_sources=score_metadata["score_component_sources"],
        score_limitations=score_metadata["score_limitations"],
        score_calibration=score_metadata["score_calibration"],
        executable_pattern_score=score_metadata["executable_pattern_score"],
        diagnostic_pattern_score=score_metadata["diagnostic_pattern_score"],
        atr_metadata=atr_timing_metadata(config.atr_config),
        pivot_metadata=pivot_strength_diagnostics(
            source_pivots,
            config.pivot_config,
            current_index=current_index,
            candle_count=len(candles),
        ),
    )


def _follow_through_end_index(
    candidate: _TrendlineCandidate,
    candles: pd.DataFrame,
    breakout_index: int,
    direction: TrendlineBreakDirection,
    required_bars: int,
) -> int | None:
    if required_bars == 0:
        return breakout_index
    end_index = breakout_index + required_bars
    if end_index >= len(candles):
        return None
    for index in range(breakout_index + 1, end_index + 1):
        close = float(candles.iloc[index]["close"])
        value = _trendline_value(candidate.slope, candidate.intercept, index)
        if direction == TrendlineBreakDirection.BULLISH and close <= value:
            return None
        if direction == TrendlineBreakDirection.BEARISH and close >= value:
            return None
    return end_index


def _trendline_retest_wait_bars(
    candidate: _TrendlineCandidate,
    candles: pd.DataFrame,
    breakout_index: int,
    direction: TrendlineBreakDirection,
    max_wait_bars: int | None,
) -> int | None:
    if max_wait_bars is None:
        return None
    last_index = min(len(candles) - 1, breakout_index + max_wait_bars)
    for index in range(breakout_index + 1, last_index + 1):
        value = _trendline_value(candidate.slope, candidate.intercept, index)
        high = float(candles.iloc[index]["high"])
        low = float(candles.iloc[index]["low"])
        if low <= value <= high:
            return index - breakout_index
    return None


def _select_best_event(events: list[TrendlineBreakEvent]) -> TrendlineBreakEvent:
    status_rank = {
        TrendlineBreakStatus.VALID.value: 2,
        TrendlineBreakStatus.WEAK.value: 1,
        TrendlineBreakStatus.PENDING.value: 0,
    }
    return sorted(
        events,
        key=lambda event: (
            status_rank.get(event.pattern_status, -1),
            event.pattern_score,
            event.touch_count,
            event.end_index - event.start_index,
            event.volume_ratio,
            event.break_distance_atr,
            event.source_pivot_indices,
        ),
        reverse=True,
    )[0]


def _calculate_pattern_score(
    *,
    candidate: _TrendlineCandidate,
    break_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: TrendlineBreakConfig,
    swing_structure_feature: dict[str, Any] | None = None,
) -> float:
    return float(
        _calculate_pattern_score_metadata(
            candidate=candidate,
            break_distance_atr=break_distance_atr,
            volume_ratio=volume_ratio,
            displacement_confirmed=displacement_confirmed,
            swing_structure_feature=swing_structure_feature,
            config=config,
        )["pattern_score"]
    )


def _calculate_pattern_score_metadata(
    *,
    candidate: _TrendlineCandidate,
    break_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: TrendlineBreakConfig,
    swing_structure_feature: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if candidate.touch_count >= config.strong_touch_count:
        trendline_quality_score = 1.0
    elif candidate.touch_count >= config.minimum_touch_count:
        trendline_quality_score = 0.7
    else:
        trendline_quality_score = 0.0

    if break_distance_atr >= 0.5:
        breakout_strength_score = 1.0
    elif break_distance_atr >= config.breakout_atr_multiplier:
        breakout_strength_score = 0.7
    else:
        breakout_strength_score = 0.0

    if volume_ratio >= 2.0:
        volume_confirmation_score = 1.0
    elif volume_ratio >= config.minimum_volume_ratio:
        volume_confirmation_score = 0.8
    elif volume_ratio >= config.weak_volume_ratio:
        volume_confirmation_score = 0.5
    else:
        volume_confirmation_score = 0.0

    liquidity_score = 0.8 if not config.require_liquidity_pass else 1.0
    structure_feature = swing_structure_feature or _missing_score_feature(
        reason="feature_not_computed"
    )
    displacement_score = 1.0 if displacement_confirmed else 0.0

    return build_score_metadata(
        "TRENDLINE_BREAK",
        [
            {"name": "trendline_quality", "raw_score": trendline_quality_score, "weight": 0.30, "source": "observed_touch_count", "description": "Number of confirmed touches supporting the trendline."},
            {"name": "breakout_strength", "raw_score": breakout_strength_score, "weight": 0.25, "source": "observed_break_distance_atr", "description": "ATR-normalized break distance beyond the trendline."},
            {"name": "volume_confirmation", "raw_score": volume_confirmation_score, "weight": 0.20, "source": "observed_volume_ratio", "description": "Relative volume at the break candle."},
            {"name": "liquidity", "raw_score": liquidity_score, "weight": 0.10, "source": "placeholder_policy" if not config.require_liquidity_pass else "required_external_liquidity_flag", "is_placeholder": not config.require_liquidity_pass, "description": "Liquidity is a policy prior unless required externally by the caller."},
            {"name": "structure_alignment", "raw_score": structure_feature["score"], "weight": 0.10, "source": structure_feature["source"], "description": "No-lookahead swing-structure alignment at the trendline break candle.", "metadata": structure_feature},
            {"name": "displacement", "raw_score": displacement_score, "weight": 0.05, "source": "observed_displacement_candle", "description": "Directional displacement confirmation on the breakout candle."},
        ],
    )


def _missing_score_feature(reason: str) -> dict[str, Any]:
    return {
        "feature_available": False,
        "source": "missing_context",
        "context": "MISSING_CONTEXT",
        "score": 0.0,
        "missing_context_reason": reason,
    }


def _displacement_confirmed(
    displacement_rows: pd.DataFrame | None,
    current_index: int,
    expected_displacement: str,
) -> bool:
    if displacement_rows is None:
        return False
    displacement = displacement_rows.iloc[current_index]
    return (
        str(displacement["displacement_direction"]) == expected_displacement
        and str(displacement["displacement_status"]) == DisplacementStatus.VALID.value
    )


def _stop_reference(
    direction: TrendlineBreakDirection,
    pivots: pd.DataFrame,
    current_index: int,
    trendline_value: float,
    atr: float,
) -> float:
    visible_pivots = pivots[pivots["pivot_index"] < current_index]
    if direction == TrendlineBreakDirection.BULLISH:
        lows = visible_pivots[
            visible_pivots["pivot_type"].isin({PivotType.PIVOT_LOW.value, PivotType.BOTH.value})
        ]
        if not lows.empty:
            return float(lows.sort_values("pivot_index").iloc[-1]["price"])
        return trendline_value - atr

    highs = visible_pivots[
        visible_pivots["pivot_type"].isin({PivotType.PIVOT_HIGH.value, PivotType.BOTH.value})
    ]
    if not highs.empty:
        return float(highs.sort_values("pivot_index").iloc[-1]["price"])
    return trendline_value + atr


def _target_and_risk_reward(
    direction: TrendlineBreakDirection,
    entry_reference: float,
    stop_reference: float,
) -> tuple[float, float | None]:
    if direction == TrendlineBreakDirection.BULLISH:
        risk = entry_reference - stop_reference
        if risk <= 0:
            return entry_reference, None
        target_reference = entry_reference + 2 * risk
        reward = target_reference - entry_reference
    else:
        risk = stop_reference - entry_reference
        if risk <= 0:
            return entry_reference, None
        target_reference = entry_reference - 2 * risk
        reward = entry_reference - target_reference
    return target_reference, reward / risk


def _trendline_value(slope: float, intercept: float, index: int) -> float:
    return slope * index + intercept


def _build_event_id(
    *,
    pattern_type: str,
    direction: str,
    symbol: str | None,
    timeframe: str | None,
    source_pivot_timestamps: tuple[Any, ...],
    breakout_timestamp: Any,
) -> str:
    raw = "|".join(
        [
            pattern_type,
            direction,
            str(symbol or ""),
            str(timeframe or ""),
            ",".join(str(timestamp) for timestamp in source_pivot_timestamps),
            str(breakout_timestamp),
        ]
    )
    digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{pattern_type}:{direction}:{digest}"


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
