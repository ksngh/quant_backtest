"""Diamond Pattern detection.

This module evaluates already-provided completed candle data and emits stable,
deterministic Diamond Pattern breakout or breakdown events. It is intentionally
pure: it does not fetch market data, read secrets, call exchange APIs, place
orders, persist records, or make trading decisions.

First-batch implementation notes:
- The detector emits completed ``VALID`` or ``WEAK`` breakout/breakdown events;
  pending watchlist events are deferred.
- Candidate pivot windows are contiguous confirmed-pivot windows between
  ``minimum_pivot_count`` and ``maximum_pivot_count``.
- Diamond center is represented by the deterministic expansion/contraction split
  with the largest pivot-local range, with earliest split used as a tie-breaker.
- Liquidity and bid-ask spread modules are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require pass/fail values once those filters are supplied.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` to preserve deterministic streaming behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.indicators.atr import AtrConfig, calculate_atr
from quant_bitcoin.indicators.displacement_candle import (
    DisplacementCandleConfig,
    DisplacementDirection,
    DisplacementStatus,
    detect_displacement_candles,
)
from quant_bitcoin.indicators.pivots import PivotConfig, PivotType, detect_pivots
from quant_bitcoin.indicators.volume_ratio import VolumeRatioConfig, calculate_volume_ratio

REQUIRED_DIAMOND_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class DiamondDirection(Enum):
    """Supported Diamond Pattern directions."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NONE = "NONE"


class DiamondStatus(Enum):
    """Supported Diamond Pattern statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


@dataclass(frozen=True)
class DiamondConfig:
    """Configuration for deterministic Diamond Pattern detection."""

    minimum_pivot_count: int = 6
    maximum_pivot_count: int = 10
    max_recent_pivots: int = 120
    max_candidate_windows_per_bar: int = 250
    minimum_pattern_duration: int = 20
    maximum_pattern_duration: int = 200
    minimum_expansion_range_change_atr: float = 1.0
    minimum_contraction_range_change_rate: float = 0.20
    minimum_pattern_height_atr: float = 1.0
    maximum_pattern_height_atr: float = 8.0
    maximum_boundary_touch_deviation_atr: float = 0.5
    breakout_atr_multiplier: float = 0.2
    minimum_breakout_volume_ratio: float = 1.5
    weak_breakout_volume_ratio: float = 1.3
    # Liquidity and spread modules are not implemented yet. The first detector
    # defaults these unavailable prerequisite filters to not required instead of
    # silently approximating them.
    require_liquidity_pass: bool = False
    require_spread_pass: bool = False
    liquidity_pass: bool | None = None
    spread_pass: bool | None = None
    require_displacement_breakout: bool = False
    minimum_pattern_score: float = 0.7
    pivot_config: PivotConfig | None = None
    atr_config: AtrConfig | None = None
    volume_ratio_config: VolumeRatioConfig | None = None
    displacement_config: DisplacementCandleConfig | None = None

    def __post_init__(self) -> None:
        if self.minimum_pivot_count < 6:
            raise ValueError("minimum_pivot_count must be at least 6")
        if self.maximum_pivot_count < self.minimum_pivot_count:
            raise ValueError(
                "maximum_pivot_count must be greater than or equal to minimum_pivot_count"
            )
        if self.max_recent_pivots < self.minimum_pivot_count:
            raise ValueError("max_recent_pivots must be >= minimum_pivot_count")
        if self.max_candidate_windows_per_bar < 1:
            raise ValueError("max_candidate_windows_per_bar must be at least 1")
        if self.minimum_pattern_duration < 1:
            raise ValueError("minimum_pattern_duration must be at least 1")
        if self.maximum_pattern_duration < self.minimum_pattern_duration:
            raise ValueError(
                "maximum_pattern_duration must be greater than or equal to minimum_pattern_duration"
            )
        if self.minimum_expansion_range_change_atr < 0:
            raise ValueError("minimum_expansion_range_change_atr must be non-negative")
        if not 0 <= self.minimum_contraction_range_change_rate <= 1:
            raise ValueError("minimum_contraction_range_change_rate must be between 0 and 1")
        if self.minimum_pattern_height_atr < 0:
            raise ValueError("minimum_pattern_height_atr must be non-negative")
        if self.maximum_pattern_height_atr < self.minimum_pattern_height_atr:
            raise ValueError(
                "maximum_pattern_height_atr must be greater than or equal to "
                "minimum_pattern_height_atr"
            )
        if self.maximum_boundary_touch_deviation_atr < 0:
            raise ValueError("maximum_boundary_touch_deviation_atr must be non-negative")
        if self.breakout_atr_multiplier < 0:
            raise ValueError("breakout_atr_multiplier must be non-negative")
        if self.weak_breakout_volume_ratio < 0:
            raise ValueError("weak_breakout_volume_ratio must be non-negative")
        if self.minimum_breakout_volume_ratio < self.weak_breakout_volume_ratio:
            raise ValueError(
                "minimum_breakout_volume_ratio must be greater than or equal to "
                "weak_breakout_volume_ratio"
            )
        if not 0 <= self.minimum_pattern_score <= 1:
            raise ValueError("minimum_pattern_score must be between 0 and 1")


@dataclass(frozen=True)
class DiamondEvent:
    """Deterministic Diamond Pattern breakout or breakdown event."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    expansion_start_index: int
    diamond_center_index: int
    contraction_end_index: int
    breakout_index: int
    source_pivot_indices: tuple[int, ...]
    upper_boundary_slope: float
    upper_boundary_intercept: float
    lower_boundary_slope: float
    lower_boundary_intercept: float
    upper_boundary_value: float
    lower_boundary_value: float
    expansion_high_slope: float
    expansion_low_slope: float
    contraction_high_slope: float
    contraction_low_slope: float
    expansion_range_change: float
    expansion_range_change_atr: float
    contraction_range_change: float
    contraction_range_change_rate: float
    pattern_height: float
    pattern_height_atr: float
    breakout_price: float
    breakout_distance: float
    breakout_distance_atr: float
    atr: float
    volume_ratio: float
    liquidity_pass: bool | None
    spread_pass: bool | None
    displacement_confirmed: bool
    pattern_score: float
    entry_reference: float
    stop_reference: float
    target_reference: float
    risk_reward: float | None
    reason: str


@dataclass(frozen=True)
class _DiamondCandidate:
    pivots: tuple[dict[str, Any], ...]
    split_position: int
    expansion_high_slope: float
    expansion_low_slope: float
    contraction_high_slope: float
    contraction_low_slope: float
    expansion_range_change: float
    expansion_range_change_atr: float
    contraction_range_change: float
    contraction_range_change_rate: float
    pattern_height: float
    pattern_height_atr: float
    upper_boundary_slope: float
    upper_boundary_intercept: float
    lower_boundary_slope: float
    lower_boundary_intercept: float


def detect_diamond_patterns(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: DiamondConfig | None = None,
) -> list[DiamondEvent]:
    """Return deterministic Diamond Pattern events from completed candles.

    The first implementation batch emits completed ``VALID`` or ``WEAK``
    breakout/breakdown events only. Invalid and pending candidates are not
    emitted; they deterministically return no event.
    """

    diamond_config = config or DiamondConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < diamond_config.minimum_pivot_count + 1:
        return []

    _validate_external_filters(diamond_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        diamond_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(
        candle_frame[["symbol", "timestamp", "volume"]],
        diamond_config.volume_ratio_config,
    )
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    pivot_rows = detect_pivots(
        enriched[["symbol", "timestamp", "open", "high", "low", "close"]],
        diamond_config.pivot_config,
    )
    pivot_rows = pivot_rows[pivot_rows["is_confirmed"] == True]
    displacement_rows = detect_displacement_candles(
        enriched[
            [
                "symbol",
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "atr",
                "volume_ratio",
            ]
        ],
        diamond_config.displacement_config,
    )

    symbol_value = symbol or str(enriched.iloc[0]["symbol"])
    events: list[DiamondEvent] = []
    for breakout_index in range(len(enriched)):
        atr = _optional_float(enriched.iloc[breakout_index]["atr"])
        volume_ratio = _optional_float(enriched.iloc[breakout_index]["volume_ratio"])
        if atr is None or atr <= 0 or volume_ratio is None:
            continue

        visible_pivots = pivot_rows[
            (pivot_rows["confirmed_index"] <= breakout_index)
            & (pivot_rows["pivot_index"] < breakout_index)
        ]
        if len(visible_pivots) > diamond_config.max_recent_pivots:
            visible_pivots = visible_pivots.nlargest(
                diamond_config.max_recent_pivots, "pivot_index"
            )
        candidates = _build_candidates(visible_pivots, enriched, breakout_index, diamond_config)
        evaluated = [
            event
            for candidate in candidates
            if (
                event := _evaluate_candidate(
                    candidate,
                    enriched,
                    displacement_rows,
                    breakout_index,
                    symbol=symbol_value,
                    timeframe=timeframe,
                    config=diamond_config,
                )
            )
            is not None
        ]
        if evaluated:
            events.append(_select_best_event(evaluated))

    return events


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]], symbol: str | None
) -> pd.DataFrame:
    frame = candles.copy() if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    missing = [column for column in REQUIRED_DIAMOND_CANDLE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"candles missing required columns: {missing}")

    if frame.empty:
        if "symbol" not in frame.columns:
            frame["symbol"] = symbol or ""
        return frame.reset_index(drop=True)

    frame = frame.copy()
    if "symbol" not in frame.columns:
        frame["symbol"] = symbol or ""
    elif symbol is not None:
        frame["symbol"] = frame["symbol"].fillna(symbol)

    timestamps = pd.to_datetime(frame["timestamp"], errors="raise")
    if not timestamps.is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError("candle numeric columns must not contain null values")
    if (frame["high"] < frame["low"]).any():
        raise ValueError("candle high must be greater than or equal to low")
    if (frame["volume"] < 0).any():
        raise ValueError("candle volume must be non-negative")

    return frame.reset_index(drop=True)


def _validate_external_filters(config: DiamondConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _build_candidates(
    visible_pivots: pd.DataFrame,
    candles: pd.DataFrame,
    breakout_index: int,
    config: DiamondConfig,
) -> list[_DiamondCandidate]:
    if len(visible_pivots) < config.minimum_pivot_count:
        return []

    records = list(visible_pivots.sort_values("pivot_index").to_dict("records"))
    candidates: list[_DiamondCandidate] = []
    window_count = 0
    for end in range(config.minimum_pivot_count, len(records) + 1):
        for count in range(config.minimum_pivot_count, config.maximum_pivot_count + 1):
            window_count += 1
            if window_count > config.max_candidate_windows_per_bar:
                return candidates
            start = end - count
            if start < 0:
                continue
            window = tuple(records[start:end])
            candidate = _evaluate_pivot_window(window, candles, breakout_index, config)
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def _evaluate_pivot_window(
    pivots: tuple[dict[str, Any], ...],
    candles: pd.DataFrame,
    breakout_index: int,
    config: DiamondConfig,
) -> _DiamondCandidate | None:
    pivot_indices = tuple(int(pivot["pivot_index"]) for pivot in pivots)
    pattern_duration = pivot_indices[-1] - pivot_indices[0]
    if not config.minimum_pattern_duration <= pattern_duration <= config.maximum_pattern_duration:
        return None
    if pivot_indices[-1] >= breakout_index:
        return None

    highs = _filter_pivots(pivots, {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value})
    lows = _filter_pivots(pivots, {PivotType.PIVOT_LOW.value, PivotType.BOTH.value})
    if len(highs) < 3 or len(lows) < 3:
        return None

    atr = _optional_float(candles.iloc[pivot_indices[-1]]["atr"])
    if atr is None or atr <= 0:
        return None

    pattern_height = max(float(pivot["price"]) for pivot in highs) - min(
        float(pivot["price"]) for pivot in lows
    )
    pattern_height_atr = pattern_height / atr
    if not config.minimum_pattern_height_atr <= pattern_height_atr <= config.maximum_pattern_height_atr:
        return None

    split_candidates: list[_DiamondCandidate] = []
    for split_position in range(4, len(pivots) - 3):
        expansion = pivots[:split_position]
        contraction = pivots[split_position:]
        expansion_highs = _filter_pivots(
            expansion, {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value}
        )
        expansion_lows = _filter_pivots(
            expansion, {PivotType.PIVOT_LOW.value, PivotType.BOTH.value}
        )
        contraction_highs = _filter_pivots(
            contraction, {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value}
        )
        contraction_lows = _filter_pivots(
            contraction, {PivotType.PIVOT_LOW.value, PivotType.BOTH.value}
        )
        if (
            len(expansion_highs) < 2
            or len(expansion_lows) < 2
            or len(contraction_highs) < 2
            or len(contraction_lows) < 2
        ):
            continue

        expansion_high_slope, _ = _fit_line(expansion_highs)
        expansion_low_slope, _ = _fit_line(expansion_lows)
        contraction_high_slope, upper_intercept = _fit_line(contraction_highs)
        contraction_low_slope, lower_intercept = _fit_line(contraction_lows)
        if expansion_high_slope <= 0 or expansion_low_slope >= 0:
            continue
        if contraction_high_slope >= 0 or contraction_low_slope <= 0:
            continue

        expansion_start_range = _paired_range(expansion_highs[0], expansion_lows[0])
        expansion_end_range = _segment_range(expansion)
        expansion_range_change = expansion_end_range - expansion_start_range
        expansion_range_change_atr = expansion_range_change / atr
        if expansion_range_change_atr < config.minimum_expansion_range_change_atr:
            continue

        contraction_start_range = _paired_range(contraction_highs[0], contraction_lows[0])
        contraction_end_range = _paired_range(contraction_highs[-1], contraction_lows[-1])
        if contraction_start_range <= 0:
            continue
        contraction_range_change = contraction_start_range - contraction_end_range
        contraction_range_change_rate = contraction_range_change / contraction_start_range
        if contraction_range_change_rate < config.minimum_contraction_range_change_rate:
            continue

        split_candidates.append(
            _DiamondCandidate(
                pivots=pivots,
                split_position=split_position,
                expansion_high_slope=expansion_high_slope,
                expansion_low_slope=expansion_low_slope,
                contraction_high_slope=contraction_high_slope,
                contraction_low_slope=contraction_low_slope,
                expansion_range_change=expansion_range_change,
                expansion_range_change_atr=expansion_range_change_atr,
                contraction_range_change=contraction_range_change,
                contraction_range_change_rate=contraction_range_change_rate,
                pattern_height=pattern_height,
                pattern_height_atr=pattern_height_atr,
                upper_boundary_slope=contraction_high_slope,
                upper_boundary_intercept=upper_intercept,
                lower_boundary_slope=contraction_low_slope,
                lower_boundary_intercept=lower_intercept,
            )
        )

    if not split_candidates:
        return None
    return sorted(
        split_candidates,
        key=lambda candidate: (
            _segment_range(candidate.pivots[: candidate.split_position]),
            -candidate.split_position,
        ),
        reverse=True,
    )[0]


def _evaluate_candidate(
    candidate: _DiamondCandidate,
    candles: pd.DataFrame,
    displacement_rows: pd.DataFrame,
    breakout_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: DiamondConfig,
) -> DiamondEvent | None:
    current = candles.iloc[breakout_index]
    atr = _optional_float(current["atr"])
    volume_ratio = _optional_float(current["volume_ratio"])
    if atr is None or atr <= 0 or volume_ratio is None:
        return None
    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    breakout_price = float(current["close"])
    upper_boundary_value = _line_value(
        candidate.upper_boundary_slope, candidate.upper_boundary_intercept, breakout_index
    )
    lower_boundary_value = _line_value(
        candidate.lower_boundary_slope, candidate.lower_boundary_intercept, breakout_index
    )
    bullish_distance = breakout_price - upper_boundary_value
    bearish_distance = lower_boundary_value - breakout_price
    if bullish_distance > bearish_distance and bullish_distance / atr >= config.breakout_atr_multiplier:
        direction = DiamondDirection.BULLISH
        breakout_distance = bullish_distance
        expected_displacement = DisplacementDirection.BULLISH.value
        stop_reference = lower_boundary_value
        target_reference = breakout_price + candidate.pattern_height
    elif bearish_distance / atr >= config.breakout_atr_multiplier:
        direction = DiamondDirection.BEARISH
        breakout_distance = bearish_distance
        expected_displacement = DisplacementDirection.BEARISH.value
        stop_reference = upper_boundary_value
        target_reference = breakout_price - candidate.pattern_height
    else:
        return None

    breakout_distance_atr = breakout_distance / atr
    if volume_ratio < config.weak_breakout_volume_ratio:
        return None
    pattern_status = (
        DiamondStatus.VALID
        if volume_ratio >= config.minimum_breakout_volume_ratio
        else DiamondStatus.WEAK
    )

    displacement_confirmed = _displacement_confirmed(
        displacement_rows, breakout_index, expected_displacement
    )
    if config.require_displacement_breakout and not displacement_confirmed:
        return None

    pattern_score = _calculate_pattern_score(
        candidate=candidate,
        breakout_distance_atr=breakout_distance_atr,
        volume_ratio=volume_ratio,
        displacement_confirmed=displacement_confirmed,
        config=config,
    )
    if pattern_status == DiamondStatus.VALID and pattern_score < config.minimum_pattern_score:
        pattern_status = DiamondStatus.WEAK

    entry_reference = breakout_price
    risk_reward = _risk_reward(direction, entry_reference, stop_reference, target_reference)
    if risk_reward is None:
        return None

    source_pivot_indices = tuple(int(pivot["pivot_index"]) for pivot in candidate.pivots)
    expansion_start_index = source_pivot_indices[0]
    diamond_center_index = int(candidate.pivots[candidate.split_position - 1]["pivot_index"])
    contraction_end_index = source_pivot_indices[-1]
    event_id = _build_event_id(
        pattern_type="DIAMOND_PATTERN",
        direction=direction.value,
        symbol=symbol,
        timeframe=timeframe,
        pivot_timestamps=tuple(
            candles.iloc[pivot_index]["timestamp"] for pivot_index in source_pivot_indices
        ),
        breakout_timestamp=current["timestamp"],
    )

    return DiamondEvent(
        event_id=event_id,
        pattern_type="DIAMOND_PATTERN",
        direction=direction.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=current["timestamp"],
        start_index=expansion_start_index,
        end_index=breakout_index,
        expansion_start_index=expansion_start_index,
        diamond_center_index=diamond_center_index,
        contraction_end_index=contraction_end_index,
        breakout_index=breakout_index,
        source_pivot_indices=source_pivot_indices,
        upper_boundary_slope=candidate.upper_boundary_slope,
        upper_boundary_intercept=candidate.upper_boundary_intercept,
        lower_boundary_slope=candidate.lower_boundary_slope,
        lower_boundary_intercept=candidate.lower_boundary_intercept,
        upper_boundary_value=upper_boundary_value,
        lower_boundary_value=lower_boundary_value,
        expansion_high_slope=candidate.expansion_high_slope,
        expansion_low_slope=candidate.expansion_low_slope,
        contraction_high_slope=candidate.contraction_high_slope,
        contraction_low_slope=candidate.contraction_low_slope,
        expansion_range_change=candidate.expansion_range_change,
        expansion_range_change_atr=candidate.expansion_range_change_atr,
        contraction_range_change=candidate.contraction_range_change,
        contraction_range_change_rate=candidate.contraction_range_change_rate,
        pattern_height=candidate.pattern_height,
        pattern_height_atr=candidate.pattern_height_atr,
        breakout_price=breakout_price,
        breakout_distance=breakout_distance,
        breakout_distance_atr=breakout_distance_atr,
        atr=atr,
        volume_ratio=volume_ratio,
        liquidity_pass=config.liquidity_pass,
        spread_pass=config.spread_pass,
        displacement_confirmed=displacement_confirmed,
        pattern_score=pattern_score,
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        reason=f"{direction.value.title()} Diamond Pattern breakout confirmed.",
    )


def _select_best_event(events: list[DiamondEvent]) -> DiamondEvent:
    status_rank = {DiamondStatus.VALID.value: 2, DiamondStatus.WEAK.value: 1}
    return sorted(
        events,
        key=lambda event: (
            status_rank.get(event.pattern_status, -1),
            event.pattern_score,
            event.pattern_height_atr,
            event.breakout_distance_atr,
            event.volume_ratio,
            event.source_pivot_indices,
        ),
        reverse=True,
    )[0]


def _calculate_pattern_score(
    *,
    candidate: _DiamondCandidate,
    breakout_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: DiamondConfig,
) -> float:
    expansion_score = min(
        1.0,
        candidate.expansion_range_change_atr
        / max(config.minimum_expansion_range_change_atr, 1e-9),
    )
    contraction_score = min(
        1.0,
        candidate.contraction_range_change_rate
        / max(config.minimum_contraction_range_change_rate, 1e-9),
    )
    height_midpoint = (config.minimum_pattern_height_atr + config.maximum_pattern_height_atr) / 2
    height_range = max(config.maximum_pattern_height_atr - config.minimum_pattern_height_atr, 1e-9)
    height_score = max(0.0, 1.0 - abs(candidate.pattern_height_atr - height_midpoint) / height_range)
    breakout_score = 1.0 if breakout_distance_atr >= 0.5 else 0.7
    volume_score = 1.0 if volume_ratio >= config.minimum_breakout_volume_ratio else 0.6
    displacement_score = 1.0 if displacement_confirmed else 0.0
    liquidity_score = 0.8 if not config.require_liquidity_pass else 1.0

    score = (
        expansion_score * 0.20
        + contraction_score * 0.20
        + height_score * 0.15
        + breakout_score * 0.20
        + volume_score * 0.15
        + liquidity_score * 0.05
        + displacement_score * 0.05
    )
    return round(max(0.0, min(score, 1.0)), 6)


def _risk_reward(
    direction: DiamondDirection,
    entry_reference: float,
    stop_reference: float,
    target_reference: float,
) -> float | None:
    if direction == DiamondDirection.BULLISH:
        risk = entry_reference - stop_reference
        reward = target_reference - entry_reference
    else:
        risk = stop_reference - entry_reference
        reward = entry_reference - target_reference
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def _filter_pivots(
    pivots: Iterable[dict[str, Any]], pivot_types: set[str]
) -> list[dict[str, Any]]:
    return [pivot for pivot in pivots if str(pivot["pivot_type"]) in pivot_types]


def _fit_line(pivots: list[dict[str, Any]]) -> tuple[float, float]:
    if len(pivots) < 2:
        raise ValueError("at least two pivots are required to fit a line")
    x_values = [float(pivot["pivot_index"]) for pivot in pivots]
    y_values = [float(pivot["price"]) for pivot in pivots]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    if denominator == 0:
        return 0.0, y_mean
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / denominator
    intercept = y_mean - slope * x_mean
    return slope, intercept


def _line_value(slope: float, intercept: float, index: int) -> float:
    return slope * index + intercept


def _segment_range(pivots: Iterable[dict[str, Any]]) -> float:
    pivot_list = list(pivots)
    highs = _filter_pivots(pivot_list, {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value})
    lows = _filter_pivots(pivot_list, {PivotType.PIVOT_LOW.value, PivotType.BOTH.value})
    if not highs or not lows:
        return 0.0
    return max(float(pivot["price"]) for pivot in highs) - min(
        float(pivot["price"]) for pivot in lows
    )


def _paired_range(high_pivot: dict[str, Any], low_pivot: dict[str, Any]) -> float:
    return float(high_pivot["price"]) - float(low_pivot["price"])


def _displacement_confirmed(
    displacement_rows: pd.DataFrame,
    breakout_index: int,
    expected_displacement: str,
) -> bool:
    displacement = displacement_rows.iloc[breakout_index]
    return (
        str(displacement["displacement_direction"]) == expected_displacement
        and str(displacement["displacement_status"]) == DisplacementStatus.VALID.value
    )


def _build_event_id(
    *,
    pattern_type: str,
    direction: str,
    symbol: str | None,
    timeframe: str | None,
    pivot_timestamps: tuple[Any, ...],
    breakout_timestamp: Any,
) -> str:
    raw = "|".join(
        [
            pattern_type,
            direction,
            str(symbol or ""),
            str(timeframe or ""),
            ",".join(str(timestamp) for timestamp in pivot_timestamps),
            str(breakout_timestamp),
        ]
    )
    digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{pattern_type}:{direction}:{digest}"


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
