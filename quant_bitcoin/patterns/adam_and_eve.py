"""Adam and Eve Pattern detection.

This module evaluates already-provided completed candle data and emits stable,
deterministic bullish Adam and Eve breakout events. It is intentionally pure: it
does not fetch market data, read secrets, call exchange APIs, place orders,
persist records, or make trading decisions.

First-batch implementation notes:
- Only bullish completed breakout events are emitted.
- The neckline is ``neckline_pivot.price``.
- Adam sharpness uses a deterministic local window around the Adam pivot low.
- Eve roundness uses bottom-zone candle counts between the neckline pivot and
  breakout.
- Liquidity and bid-ask spread modules are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require pass/fail values once those filters are supplied.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` to preserve deterministic streaming behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
from quant_bitcoin.patterns.score_metadata import build_score_metadata

REQUIRED_ADAM_AND_EVE_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class AdamAndEveDirection(Enum):
    """Supported first-batch Adam and Eve directions."""

    BULLISH = "BULLISH"
    NONE = "NONE"


class AdamAndEveStatus(Enum):
    """Supported Adam and Eve statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


@dataclass(frozen=True)
class AdamAndEveConfig:
    """Configuration for deterministic bullish Adam and Eve detection."""

    maximum_bottom_difference_rate: float = 0.05
    minimum_pattern_duration: int = 20
    maximum_pattern_duration: int = 200
    max_recent_pivots: int = 120
    max_candidates_per_bar: int = 250
    maximum_adam_bottom_duration: int = 5
    adam_left_window: int = 2
    adam_right_window: int = 2
    minimum_eve_bottom_duration: int = 5
    minimum_eve_bottom_zone_duration: int = 3
    bottom_zone_atr_multiplier: float = 0.5
    minimum_adam_range_atr: float = 1.0
    minimum_eve_to_adam_duration_ratio: float = 1.5
    minimum_pattern_height_atr: float = 1.0
    maximum_pattern_height_atr: float = 8.0
    breakout_atr_multiplier: float = 0.2
    minimum_breakout_volume_ratio: float = 1.5
    weak_breakout_volume_ratio: float = 1.3
    require_prior_downtrend: bool = True
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
        if self.maximum_bottom_difference_rate < 0:
            raise ValueError("maximum_bottom_difference_rate must be non-negative")
        if self.minimum_pattern_duration < 1:
            raise ValueError("minimum_pattern_duration must be at least 1")
        if self.maximum_pattern_duration < self.minimum_pattern_duration:
            raise ValueError(
                "maximum_pattern_duration must be greater than or equal to "
                "minimum_pattern_duration"
            )
        if self.max_recent_pivots < 3:
            raise ValueError("max_recent_pivots must be at least 3")
        if self.max_candidates_per_bar < 1:
            raise ValueError("max_candidates_per_bar must be at least 1")
        if self.maximum_adam_bottom_duration < 1:
            raise ValueError("maximum_adam_bottom_duration must be at least 1")
        if self.adam_left_window < 0 or self.adam_right_window < 0:
            raise ValueError("adam local windows must be non-negative")
        if self.minimum_eve_bottom_duration < 1:
            raise ValueError("minimum_eve_bottom_duration must be at least 1")
        if self.minimum_eve_bottom_zone_duration < 1:
            raise ValueError("minimum_eve_bottom_zone_duration must be at least 1")
        if self.bottom_zone_atr_multiplier < 0:
            raise ValueError("bottom_zone_atr_multiplier must be non-negative")
        if self.minimum_adam_range_atr < 0:
            raise ValueError("minimum_adam_range_atr must be non-negative")
        if self.minimum_eve_to_adam_duration_ratio < 0:
            raise ValueError("minimum_eve_to_adam_duration_ratio must be non-negative")
        if self.minimum_pattern_height_atr < 0:
            raise ValueError("minimum_pattern_height_atr must be non-negative")
        if self.maximum_pattern_height_atr < self.minimum_pattern_height_atr:
            raise ValueError(
                "maximum_pattern_height_atr must be greater than or equal to "
                "minimum_pattern_height_atr"
            )
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
class AdamAndEveEvent:
    """Deterministic bullish Adam and Eve breakout event."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    adam_low_index: int
    neckline_pivot_index: int
    eve_low_index: int
    breakout_index: int
    adam_low_price: float
    neckline: float
    eve_low_price: float
    bottom_difference_rate: float
    adam_bottom_duration: int
    eve_bottom_duration: int
    eve_bottom_zone_duration: int
    adam_local_range_atr: float
    eve_local_range_atr: float
    eve_to_adam_duration_ratio: float
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
    score_components: dict[str, Any] = field(default_factory=dict)
    score_component_sources: dict[str, str] = field(default_factory=dict)
    score_limitations: tuple[str, ...] = ()
    score_calibration: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _AdamAndEveCandidate:
    adam_low: dict[str, Any]
    neckline_pivot: dict[str, Any]
    eve_low: dict[str, Any]


def detect_adam_and_eve_patterns(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: AdamAndEveConfig | None = None,
) -> list[AdamAndEveEvent]:
    """Return deterministic bullish Adam and Eve events from completed candles.

    The first implementation batch emits completed ``VALID`` or ``WEAK``
    breakout events only. Invalid and pending candidates are not emitted; they
    deterministically return no event.
    """

    ae_config = config or AdamAndEveConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < 4:
        return []

    _validate_external_filters(ae_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        ae_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(
        candle_frame[["symbol", "timestamp", "volume"]],
        ae_config.volume_ratio_config,
    )
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    pivot_rows = detect_pivots(
        enriched[["symbol", "timestamp", "open", "high", "low", "close"]],
        ae_config.pivot_config,
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
        ae_config.displacement_config,
    )

    symbol_value = symbol or str(enriched.iloc[0]["symbol"])
    events: list[AdamAndEveEvent] = []
    for breakout_index in range(len(enriched)):
        atr = _optional_float(enriched.iloc[breakout_index]["atr"])
        volume_ratio = _optional_float(enriched.iloc[breakout_index]["volume_ratio"])
        if atr is None or atr <= 0 or volume_ratio is None:
            continue

        visible_pivots = pivot_rows[
            (pivot_rows["confirmed_index"] <= breakout_index)
            & (pivot_rows["pivot_index"] < breakout_index)
        ]
        if len(visible_pivots) > ae_config.max_recent_pivots:
            visible_pivots = visible_pivots.nlargest(ae_config.max_recent_pivots, "pivot_index")
        evaluated = [
            event
            for candidate in _build_candidates(visible_pivots, ae_config)
            if (
                event := _evaluate_candidate(
                    candidate,
                    enriched,
                    displacement_rows,
                    breakout_index,
                    symbol=symbol_value,
                    timeframe=timeframe,
                    config=ae_config,
                )
            )
            is not None
        ]
        if evaluated:
            events.append(_select_best_event(evaluated))

    return events


def detect_adam_and_eve_patterns_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: AdamAndEveConfig | None = None,
) -> list[AdamAndEveEvent]:
    """Return only Adam-and-Eve events confirmed at ``current_index``."""

    if current_index < 0:
        return []
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if current_index >= len(frame):
        return []
    events = detect_adam_and_eve_patterns(
        frame.iloc[: current_index + 1],
        symbol=symbol,
        timeframe=timeframe,
        config=config,
    )
    return [event for event in events if event.end_index == current_index]


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]], symbol: str | None
) -> pd.DataFrame:
    frame = candles.copy() if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    missing = [
        column for column in REQUIRED_ADAM_AND_EVE_CANDLE_COLUMNS if column not in frame.columns
    ]
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


def _validate_external_filters(config: AdamAndEveConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _build_candidates(
    visible_pivots: pd.DataFrame, config: AdamAndEveConfig
) -> list[_AdamAndEveCandidate]:
    if len(visible_pivots) < 3:
        return []
    records = list(visible_pivots.sort_values("pivot_index").to_dict("records"))
    lows = [
        record
        for record in records
        if record["pivot_type"] in {PivotType.PIVOT_LOW.value, PivotType.BOTH.value}
    ]
    highs = [
        record
        for record in records
        if record["pivot_type"] in {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value}
    ]
    candidates: list[_AdamAndEveCandidate] = []
    candidate_count = 0
    for adam_low in lows:
        adam_index = int(adam_low["pivot_index"])
        for neckline_pivot in highs:
            neckline_index = int(neckline_pivot["pivot_index"])
            if neckline_index <= adam_index:
                continue
            for eve_low in lows:
                eve_index = int(eve_low["pivot_index"])
                if eve_index <= neckline_index:
                    continue
                candidates.append(_AdamAndEveCandidate(adam_low, neckline_pivot, eve_low))
                candidate_count += 1
                if candidate_count >= config.max_candidates_per_bar:
                    return candidates
    return candidates


def _evaluate_candidate(
    candidate: _AdamAndEveCandidate,
    candles: pd.DataFrame,
    displacement_rows: pd.DataFrame,
    breakout_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: AdamAndEveConfig,
) -> AdamAndEveEvent | None:
    adam_index = int(candidate.adam_low["pivot_index"])
    neckline_index = int(candidate.neckline_pivot["pivot_index"])
    eve_index = int(candidate.eve_low["pivot_index"])
    if not adam_index < neckline_index < eve_index < breakout_index:
        return None

    if config.require_prior_downtrend and not _has_prior_downtrend(candles, adam_index):
        return None
    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    adam_price = float(candidate.adam_low["price"])
    neckline = float(candidate.neckline_pivot["price"])
    eve_price = float(candidate.eve_low["price"])
    if adam_price <= 0 or neckline <= max(adam_price, eve_price):
        return None

    pattern_duration = breakout_index - adam_index
    if not config.minimum_pattern_duration <= pattern_duration <= config.maximum_pattern_duration:
        return None

    bottom_difference_rate = abs(adam_price - eve_price) / adam_price
    if bottom_difference_rate > config.maximum_bottom_difference_rate:
        return None

    atr_at_eve = _optional_float(candles.iloc[eve_index]["atr"])
    atr_at_adam = _optional_float(candles.iloc[adam_index]["atr"])
    if atr_at_eve is None or atr_at_eve <= 0 or atr_at_adam is None or atr_at_adam <= 0:
        return None

    pattern_bottom = min(adam_price, eve_price)
    pattern_height = neckline - pattern_bottom
    pattern_height_atr = pattern_height / atr_at_eve
    if pattern_height_atr < config.minimum_pattern_height_atr:
        return None
    height_too_large = pattern_height_atr > config.maximum_pattern_height_atr

    adam_bottom_duration = _adam_bottom_duration(adam_index, len(candles), config)
    if adam_bottom_duration > config.maximum_adam_bottom_duration:
        return None
    adam_local_range_atr = _adam_local_range_atr(candles, adam_index, adam_price, atr_at_adam, config)
    if adam_local_range_atr < config.minimum_adam_range_atr:
        return None

    eve_bottom_zone_duration = _eve_bottom_zone_duration(
        candles, neckline_index, breakout_index, eve_price, atr_at_eve, config
    )
    if eve_bottom_zone_duration < config.minimum_eve_bottom_zone_duration:
        return None
    eve_bottom_duration = max(eve_bottom_zone_duration, breakout_index - neckline_index)
    if eve_bottom_duration < config.minimum_eve_bottom_duration:
        return None

    eve_to_adam_duration_ratio = eve_bottom_duration / adam_bottom_duration
    if eve_to_adam_duration_ratio < config.minimum_eve_to_adam_duration_ratio:
        return None

    eve_local_range_atr = _eve_local_range_atr(
        candles, neckline_index, breakout_index, eve_price, atr_at_eve
    )

    current = candles.iloc[breakout_index]
    atr = _optional_float(current["atr"])
    volume_ratio = _optional_float(current["volume_ratio"])
    if atr is None or atr <= 0 or volume_ratio is None:
        return None

    breakout_price = float(current["close"])
    breakout_distance = breakout_price - neckline
    breakout_distance_atr = breakout_distance / atr
    if breakout_distance <= 0 or breakout_distance_atr < config.breakout_atr_multiplier:
        return None
    if volume_ratio < config.weak_breakout_volume_ratio:
        return None

    pattern_status = (
        AdamAndEveStatus.VALID
        if volume_ratio >= config.minimum_breakout_volume_ratio and not height_too_large
        else AdamAndEveStatus.WEAK
    )

    displacement_confirmed = _displacement_confirmed(displacement_rows, breakout_index)
    if config.require_displacement_breakout and not displacement_confirmed:
        return None

    score_metadata = _calculate_pattern_score_metadata(
        bottom_difference_rate=bottom_difference_rate,
        adam_local_range_atr=adam_local_range_atr,
        eve_bottom_zone_duration=eve_bottom_zone_duration,
        eve_to_adam_duration_ratio=eve_to_adam_duration_ratio,
        pattern_height_atr=pattern_height_atr,
        breakout_distance_atr=breakout_distance_atr,
        volume_ratio=volume_ratio,
        displacement_confirmed=displacement_confirmed,
        config=config,
    )
    pattern_score = float(score_metadata["pattern_score"])
    if pattern_status == AdamAndEveStatus.VALID and pattern_score < config.minimum_pattern_score:
        pattern_status = AdamAndEveStatus.WEAK

    entry_reference = breakout_price
    stop_reference = min(adam_price, eve_price)
    target_reference = breakout_price + pattern_height
    risk_reward = _risk_reward(entry_reference, stop_reference, target_reference)
    if risk_reward is None:
        return None

    event_id = _build_event_id(
        pattern_type="ADAM_AND_EVE_PATTERN",
        direction=AdamAndEveDirection.BULLISH.value,
        symbol=symbol,
        timeframe=timeframe,
        pivot_timestamps=(
            candles.iloc[adam_index]["timestamp"],
            candles.iloc[neckline_index]["timestamp"],
            candles.iloc[eve_index]["timestamp"],
        ),
        breakout_timestamp=current["timestamp"],
    )

    return AdamAndEveEvent(
        event_id=event_id,
        pattern_type="ADAM_AND_EVE_PATTERN",
        direction=AdamAndEveDirection.BULLISH.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=current["timestamp"],
        start_index=adam_index,
        end_index=breakout_index,
        adam_low_index=adam_index,
        neckline_pivot_index=neckline_index,
        eve_low_index=eve_index,
        breakout_index=breakout_index,
        adam_low_price=adam_price,
        neckline=neckline,
        eve_low_price=eve_price,
        bottom_difference_rate=bottom_difference_rate,
        adam_bottom_duration=adam_bottom_duration,
        eve_bottom_duration=eve_bottom_duration,
        eve_bottom_zone_duration=eve_bottom_zone_duration,
        adam_local_range_atr=adam_local_range_atr,
        eve_local_range_atr=eve_local_range_atr,
        eve_to_adam_duration_ratio=eve_to_adam_duration_ratio,
        pattern_height=pattern_height,
        pattern_height_atr=pattern_height_atr,
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
        reason="Bullish Adam and Eve breakout confirmed.",
        score_components=score_metadata["score_components"],
        score_component_sources=score_metadata["score_component_sources"],
        score_limitations=score_metadata["score_limitations"],
        score_calibration=score_metadata["score_calibration"],
    )


def _select_best_event(events: list[AdamAndEveEvent]) -> AdamAndEveEvent:
    status_rank = {AdamAndEveStatus.VALID.value: 2, AdamAndEveStatus.WEAK.value: 1}
    return sorted(
        events,
        key=lambda event: (
            status_rank.get(event.pattern_status, -1),
            event.pattern_score,
            event.eve_to_adam_duration_ratio,
            event.breakout_distance_atr,
            event.volume_ratio,
            -event.bottom_difference_rate,
        ),
        reverse=True,
    )[0]


def _has_prior_downtrend(candles: pd.DataFrame, adam_index: int) -> bool:
    if adam_index < 1:
        return False
    prior = candles.iloc[: adam_index + 1]
    first_close = float(prior.iloc[0]["close"])
    adam_close = float(candles.iloc[adam_index]["close"])
    return adam_close < first_close and float(candles.iloc[adam_index]["low"]) < float(
        prior.iloc[:-1]["low"].min()
    )


def _adam_bottom_duration(index: int, candle_count: int, config: AdamAndEveConfig) -> int:
    start = max(0, index - config.adam_left_window)
    end = min(candle_count - 1, index + config.adam_right_window)
    return end - start + 1


def _adam_local_range_atr(
    candles: pd.DataFrame,
    adam_index: int,
    adam_price: float,
    atr: float,
    config: AdamAndEveConfig,
) -> float:
    start = max(0, adam_index - config.adam_left_window)
    end = min(len(candles) - 1, adam_index + config.adam_right_window)
    local_high = float(candles.iloc[start : end + 1]["high"].max())
    return (local_high - adam_price) / atr


def _eve_bottom_zone_duration(
    candles: pd.DataFrame,
    neckline_index: int,
    breakout_index: int,
    eve_price: float,
    atr: float,
    config: AdamAndEveConfig,
) -> int:
    zone_low = eve_price - config.bottom_zone_atr_multiplier * atr
    zone_high = eve_price + config.bottom_zone_atr_multiplier * atr
    count = 0
    for index in range(neckline_index + 1, breakout_index):
        candle = candles.iloc[index]
        if float(candle["low"]) >= zone_low and float(candle["high"]) <= zone_high:
            count += 1
    return count


def _eve_local_range_atr(
    candles: pd.DataFrame,
    neckline_index: int,
    breakout_index: int,
    eve_price: float,
    atr: float,
) -> float:
    local_high = float(candles.iloc[neckline_index + 1 : breakout_index]["high"].max())
    return (local_high - eve_price) / atr


def _displacement_confirmed(
    displacement_rows: pd.DataFrame,
    breakout_index: int,
) -> bool:
    displacement = displacement_rows.iloc[breakout_index]
    return (
        str(displacement["displacement_direction"]) == DisplacementDirection.BULLISH.value
        and str(displacement["displacement_status"]) == DisplacementStatus.VALID.value
    )


def _calculate_pattern_score(
    *,
    bottom_difference_rate: float,
    adam_local_range_atr: float,
    eve_bottom_zone_duration: int,
    eve_to_adam_duration_ratio: float,
    pattern_height_atr: float,
    breakout_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: AdamAndEveConfig,
) -> float:
    return float(
        _calculate_pattern_score_metadata(
            bottom_difference_rate=bottom_difference_rate,
            adam_local_range_atr=adam_local_range_atr,
            eve_bottom_zone_duration=eve_bottom_zone_duration,
            eve_to_adam_duration_ratio=eve_to_adam_duration_ratio,
            pattern_height_atr=pattern_height_atr,
            breakout_distance_atr=breakout_distance_atr,
            volume_ratio=volume_ratio,
            displacement_confirmed=displacement_confirmed,
            config=config,
        )["pattern_score"]
    )


def _calculate_pattern_score_metadata(
    *,
    bottom_difference_rate: float,
    adam_local_range_atr: float,
    eve_bottom_zone_duration: int,
    eve_to_adam_duration_ratio: float,
    pattern_height_atr: float,
    breakout_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: AdamAndEveConfig,
) -> dict[str, Any]:
    bottom_score = max(
        0.0,
        1.0 - bottom_difference_rate / max(config.maximum_bottom_difference_rate, 1e-9),
    )
    adam_score = min(1.0, adam_local_range_atr / max(config.minimum_adam_range_atr, 1e-9))
    eve_score = min(1.0, eve_bottom_zone_duration / config.minimum_eve_bottom_zone_duration)
    ratio_score = min(
        1.0,
        eve_to_adam_duration_ratio / max(config.minimum_eve_to_adam_duration_ratio, 1e-9),
    )
    height_midpoint = (config.minimum_pattern_height_atr + config.maximum_pattern_height_atr) / 2
    height_range = max(config.maximum_pattern_height_atr - config.minimum_pattern_height_atr, 1e-9)
    height_score = max(0.0, 1.0 - abs(pattern_height_atr - height_midpoint) / height_range)
    breakout_score = 1.0 if breakout_distance_atr >= 0.5 else 0.7
    volume_score = 1.0 if volume_ratio >= config.minimum_breakout_volume_ratio else 0.6
    displacement_score = 1.0 if displacement_confirmed else 0.0

    return build_score_metadata(
        "ADAM_AND_EVE_PATTERN",
        [
            {"name": "bottom_similarity", "raw_score": bottom_score, "weight": 0.15, "source": "observed_bottom_difference_rate", "description": "Similarity between Adam and Eve lows."},
            {"name": "adam_sharpness", "raw_score": adam_score, "weight": 0.15, "source": "observed_adam_local_range_atr", "description": "Adam local range normalized by ATR."},
            {"name": "eve_roundness", "raw_score": eve_score, "weight": 0.15, "source": "observed_eve_bottom_zone_duration", "description": "Duration in Eve bottom zone."},
            {"name": "duration_ratio", "raw_score": ratio_score, "weight": 0.15, "source": "observed_eve_to_adam_duration_ratio", "description": "Relative duration between Eve and Adam structures."},
            {"name": "height_quality", "raw_score": height_score, "weight": 0.10, "source": "observed_pattern_height_atr", "description": "Pattern height within configured ATR-normalized bounds."},
            {"name": "breakout_strength", "raw_score": breakout_score, "weight": 0.15, "source": "observed_breakout_distance_atr", "description": "ATR-normalized neckline breakout distance."},
            {"name": "volume_confirmation", "raw_score": volume_score, "weight": 0.10, "source": "observed_volume_ratio", "description": "Breakout candle relative volume."},
            {"name": "displacement", "raw_score": displacement_score, "weight": 0.05, "source": "observed_displacement_candle", "description": "Directional displacement confirmation at breakout."},
        ],
    )


def _risk_reward(
    entry_reference: float, stop_reference: float, target_reference: float
) -> float | None:
    risk = entry_reference - stop_reference
    reward = target_reference - entry_reference
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


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
