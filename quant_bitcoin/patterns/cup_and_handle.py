"""Cup and Handle pattern detection.

This module evaluates already-provided completed candle data and emits stable,
deterministic bullish Cup and Handle breakout events. It is intentionally pure:
it does not fetch market data, read secrets, call exchange APIs, place orders,
persist records, or make trading decisions.

First-batch implementation notes:
- Only bullish completed breakout events are emitted.
- The neckline is ``max(left_rim.price, right_rim.price)``.
- Liquidity and bid-ask spread modules are not implemented elsewhere in the
  project yet, so the default configuration does not require them. Callers can
  explicitly require pass/fail values once those filters are supplied.
- Input candles must already be sorted by ascending ``timestamp``. Unsorted
  input raises ``ValueError`` to preserve deterministic streaming behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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
from quant_bitcoin.indicators.pivots import (
    PivotConfig,
    PivotType,
    detect_pivots,
    pivot_strength_diagnostics,
)
from quant_bitcoin.indicators.volume_ratio import VolumeRatioConfig, calculate_volume_ratio
from quant_bitcoin.patterns.score_metadata import build_score_metadata

REQUIRED_CUP_AND_HANDLE_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class CupAndHandleDirection(Enum):
    """Supported first-batch Cup and Handle directions."""

    BULLISH = "BULLISH"
    NONE = "NONE"


class CupAndHandleStatus(Enum):
    """Supported Cup and Handle statuses."""

    VALID = "VALID"
    WEAK = "WEAK"
    INVALID = "INVALID"
    PENDING = "PENDING"


@dataclass(frozen=True)
class CupAndHandleConfig:
    """Configuration for deterministic bullish Cup and Handle detection."""

    minimum_cup_duration: int = 20
    maximum_cup_duration: int = 200
    minimum_handle_duration: int = 3
    maximum_handle_duration: int = 40
    max_recent_pivots: int = 120
    max_candidates_per_bar: int = 300
    maximum_rim_difference_rate: float = 0.05
    minimum_cup_depth_rate: float = 0.10
    maximum_cup_depth_rate: float = 0.40
    maximum_handle_depth_ratio: float = 0.35
    minimum_bottom_zone_duration: int = 3
    bottom_zone_atr_multiplier: float = 0.5
    breakout_atr_multiplier: float = 0.2
    minimum_breakout_volume_ratio: float = 1.5
    weak_breakout_volume_ratio: float = 1.3
    require_prior_uptrend: bool = True
    prior_uptrend_method: str = "LOCAL"
    local_uptrend_lookback: int = 5
    local_uptrend_minimum_return_rate: float = 0.02
    local_uptrend_require_higher_high: bool = True
    neckline_retest_max_wait_bars: int | None = None
    breakout_follow_through_bars: int = 0
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
    enable_candidate_diagnostics: bool = False

    def __post_init__(self) -> None:
        if self.minimum_cup_duration < 1:
            raise ValueError("minimum_cup_duration must be at least 1")
        if self.maximum_cup_duration < self.minimum_cup_duration:
            raise ValueError(
                "maximum_cup_duration must be greater than or equal to minimum_cup_duration"
            )
        if self.minimum_handle_duration < 1:
            raise ValueError("minimum_handle_duration must be at least 1")
        if self.maximum_handle_duration < self.minimum_handle_duration:
            raise ValueError(
                "maximum_handle_duration must be greater than or equal to minimum_handle_duration"
            )
        if self.max_recent_pivots < 4:
            raise ValueError("max_recent_pivots must be at least 4")
        if self.max_candidates_per_bar < 1:
            raise ValueError("max_candidates_per_bar must be at least 1")
        if self.maximum_rim_difference_rate < 0:
            raise ValueError("maximum_rim_difference_rate must be non-negative")
        if self.minimum_cup_depth_rate < 0:
            raise ValueError("minimum_cup_depth_rate must be non-negative")
        if self.maximum_cup_depth_rate < self.minimum_cup_depth_rate:
            raise ValueError(
                "maximum_cup_depth_rate must be greater than or equal to minimum_cup_depth_rate"
            )
        if self.maximum_handle_depth_ratio < 0:
            raise ValueError("maximum_handle_depth_ratio must be non-negative")
        if self.minimum_bottom_zone_duration < 1:
            raise ValueError("minimum_bottom_zone_duration must be at least 1")
        if self.bottom_zone_atr_multiplier < 0:
            raise ValueError("bottom_zone_atr_multiplier must be non-negative")
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
        if self.prior_uptrend_method.upper() not in {"LOCAL", "LEGACY_GLOBAL"}:
            raise ValueError("prior_uptrend_method must be LOCAL or LEGACY_GLOBAL")
        if self.local_uptrend_lookback < 1:
            raise ValueError("local_uptrend_lookback must be at least 1")
        if self.local_uptrend_minimum_return_rate < 0:
            raise ValueError("local_uptrend_minimum_return_rate must be non-negative")
        if self.neckline_retest_max_wait_bars is not None and self.neckline_retest_max_wait_bars < 1:
            raise ValueError("neckline_retest_max_wait_bars must be at least 1 when supplied")
        if self.breakout_follow_through_bars < 0:
            raise ValueError("breakout_follow_through_bars must be non-negative")


@dataclass(frozen=True)
class CupAndHandleEvent:
    """Deterministic bullish Cup and Handle breakout event."""

    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    left_rim_index: int
    cup_bottom_index: int
    right_rim_index: int
    handle_low_index: int
    breakout_index: int
    left_rim_price: float
    cup_bottom_price: float
    right_rim_price: float
    handle_low_price: float
    neckline: float
    cup_depth: float
    cup_depth_rate: float
    cup_duration: int
    bottom_zone_duration: int
    duration_ratio: float
    handle_depth: float
    handle_depth_ratio: float
    handle_duration: int
    breakout_price: float
    breakout_distance: float
    breakout_distance_atr: float
    atr: float
    volume_ratio: float
    liquidity_pass: bool | None
    spread_pass: bool | None
    displacement_confirmed: bool
    prior_uptrend_method: str
    prior_uptrend_strength: float | None
    neckline_retest_status: str
    neckline_retest_wait_bars: int | None
    breakout_follow_through_bars: int
    handle_quality: dict[str, float]
    detector_target_reference_semantics: str
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
    atr_metadata: dict[str, Any] = field(default_factory=dict)
    pivot_metadata: dict[str, Any] = field(default_factory=dict)
    candidate_diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _CupCandidate:
    left_rim: dict[str, Any]
    cup_bottom: dict[str, Any]
    right_rim: dict[str, Any]
    handle_low: dict[str, Any]


@dataclass(frozen=True)
class _CupCandidateBuildResult:
    candidates: list[_CupCandidate]
    candidate_count: int
    max_guard_hit: bool


def detect_cup_and_handle_patterns(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: CupAndHandleConfig | None = None,
) -> list[CupAndHandleEvent]:
    """Return deterministic bullish Cup and Handle events from completed candles.

    The first implementation batch emits completed ``VALID`` or ``WEAK``
    breakout events only. Invalid and pending candidates are not emitted; they
    deterministically return no event.
    """

    cup_config = config or CupAndHandleConfig()
    candle_frame = _normalize_candles(candles, symbol)

    if len(candle_frame) < 5:
        return []

    _validate_external_filters(cup_config)

    atr_rows = calculate_atr(
        candle_frame[["symbol", "timestamp", "high", "low", "close"]],
        cup_config.atr_config,
    )
    volume_rows = calculate_volume_ratio(candle_frame, cup_config.volume_ratio_config)
    enriched = candle_frame.copy()
    enriched["atr"] = atr_rows["atr"]
    enriched["volume_ratio"] = volume_rows["volume_ratio"]

    pivot_rows = detect_pivots(
        enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr"]],
        cup_config.pivot_config,
    )
    pivot_rows = pivot_rows[pivot_rows["is_confirmed"] == True]
    displacement_rows = _detect_displacements(enriched, cup_config)

    symbol_value = symbol or str(enriched.iloc[0]["symbol"])
    events: list[CupAndHandleEvent] = []

    for breakout_index in range(len(enriched)):
        atr = _optional_float(enriched.iloc[breakout_index]["atr"])
        volume_ratio = _optional_float(enriched.iloc[breakout_index]["volume_ratio"])
        if atr is None or atr <= 0 or volume_ratio is None:
            continue

        visible_pivots = pivot_rows[
            (pivot_rows["confirmed_index"] <= breakout_index)
            & (pivot_rows["pivot_index"] < breakout_index)
        ]
        if len(visible_pivots) > cup_config.max_recent_pivots:
            visible_pivots = visible_pivots.nlargest(cup_config.max_recent_pivots, "pivot_index")
        build_result = _build_candidates(visible_pivots, cup_config)
        evaluated = [
            event
            for candidate in build_result.candidates
            if (
                event := _evaluate_candidate(
                    candidate,
                    enriched,
                    displacement_rows,
                    breakout_index,
                    symbol=symbol_value,
                    timeframe=timeframe,
                    config=cup_config,
                )
            )
            is not None
        ]
        if evaluated:
            selected = _select_best_event(evaluated)
            if cup_config.enable_candidate_diagnostics:
                selected = replace(
                    selected,
                    candidate_diagnostics=_candidate_diagnostics(
                        pattern_type="CUP_AND_HANDLE",
                        visible_pivot_count=len(visible_pivots),
                        bars_observed=breakout_index + 1,
                        candidate_count=build_result.candidate_count,
                        evaluated_candidate_count=len(build_result.candidates),
                        accepted_candidate_count=len(evaluated),
                        selected_rank=1,
                        max_guard_hit=build_result.max_guard_hit,
                    ),
                )
            events.append(selected)

    return events


def detect_cup_and_handle_patterns_at_index(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    current_index: int,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: CupAndHandleConfig | None = None,
) -> list[CupAndHandleEvent]:
    """Return only cup-and-handle events confirmed at ``current_index``."""

    if current_index < 0:
        return []
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if current_index >= len(frame):
        return []
    events = detect_cup_and_handle_patterns(
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
        column
        for column in REQUIRED_CUP_AND_HANDLE_CANDLE_COLUMNS
        if column not in frame.columns
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


def _validate_external_filters(config: CupAndHandleConfig) -> None:
    if config.require_liquidity_pass and config.liquidity_pass is None:
        raise ValueError(
            "liquidity_pass must be supplied when require_liquidity_pass is true"
        )
    if config.require_spread_pass and config.spread_pass is None:
        raise ValueError("spread_pass must be supplied when require_spread_pass is true")


def _detect_displacements(
    candles: pd.DataFrame, config: CupAndHandleConfig
) -> pd.DataFrame | None:
    if not config.require_displacement_breakout:
        # Still report confirmation using the optional module when enough ATR and
        # volume-ratio context is available, matching the first-batch task.
        pass
    return detect_displacement_candles(
        candles[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
        config.displacement_config,
    )


def _build_candidates(visible_pivots: pd.DataFrame, config: CupAndHandleConfig) -> _CupCandidateBuildResult:
    if len(visible_pivots) < 4:
        return _CupCandidateBuildResult([], 0, False)

    records = list(visible_pivots.sort_values("pivot_index").to_dict("records"))
    highs = [
        record
        for record in records
        if record["pivot_type"] in {PivotType.PIVOT_HIGH.value, PivotType.BOTH.value}
    ]
    lows = [
        record
        for record in records
        if record["pivot_type"] in {PivotType.PIVOT_LOW.value, PivotType.BOTH.value}
    ]

    candidates: list[_CupCandidate] = []
    candidate_count = 0
    for left_rim in highs:
        left_index = int(left_rim["pivot_index"])
        for cup_bottom in lows:
            bottom_index = int(cup_bottom["pivot_index"])
            if bottom_index <= left_index:
                continue
            for right_rim in highs:
                right_index = int(right_rim["pivot_index"])
                if right_index <= bottom_index:
                    continue
                for handle_low in lows:
                    handle_index = int(handle_low["pivot_index"])
                    if handle_index <= right_index:
                        continue
                    candidates.append(_CupCandidate(left_rim, cup_bottom, right_rim, handle_low))
                    candidate_count += 1
                    if candidate_count >= config.max_candidates_per_bar:
                        return _CupCandidateBuildResult(candidates, candidate_count, True)
    return _CupCandidateBuildResult(candidates, candidate_count, False)


def _candidate_diagnostics(
    *,
    pattern_type: str,
    visible_pivot_count: int,
    bars_observed: int,
    candidate_count: int,
    evaluated_candidate_count: int,
    accepted_candidate_count: int,
    selected_rank: int | None,
    max_guard_hit: bool,
) -> dict[str, Any]:
    pivot_density = candidate_count / max(visible_pivot_count, 1)
    bar_density = candidate_count / max(bars_observed, 1)
    rejected_by_reason: dict[str, int] = {}
    rejected_by_rule = max(evaluated_candidate_count - accepted_candidate_count, 0)
    if rejected_by_rule:
        rejected_by_reason["candidate_rule_rejected"] = rejected_by_rule
    if max_guard_hit:
        rejected_by_reason["max_candidate_guard_hit"] = 1

    warnings: list[str] = []
    if max_guard_hit:
        warnings.append("max_candidate_guard_hit")
    if pivot_density >= 2.0 and candidate_count >= 10:
        warnings.append("high_candidate_to_pivot_density")
    if bar_density >= 1.0 and candidate_count >= 10:
        warnings.append("high_candidate_to_bar_density")

    return {
        "schema_version": "chart_pattern_candidate_diagnostics_v1",
        "pattern_type": pattern_type,
        "candidate_count": candidate_count,
        "evaluated_candidate_count": evaluated_candidate_count,
        "rejected_by_reason": rejected_by_reason,
        "selected_rank": selected_rank,
        "max_guard_hit": max_guard_hit,
        "visible_pivot_count": visible_pivot_count,
        "bars_observed": bars_observed,
        "candidate_to_pivot_ratio": pivot_density,
        "candidate_to_bar_ratio": bar_density,
        "overfit_warnings": warnings,
    }


def _evaluate_candidate(
    candidate: _CupCandidate,
    candles: pd.DataFrame,
    displacement_rows: pd.DataFrame | None,
    breakout_index: int,
    *,
    symbol: str | None,
    timeframe: str | None,
    config: CupAndHandleConfig,
) -> CupAndHandleEvent | None:
    left_index = int(candidate.left_rim["pivot_index"])
    bottom_index = int(candidate.cup_bottom["pivot_index"])
    right_index = int(candidate.right_rim["pivot_index"])
    handle_index = int(candidate.handle_low["pivot_index"])
    if not left_index < bottom_index < right_index < handle_index < breakout_index:
        return None

    uptrend_ok, prior_uptrend_strength = _has_prior_uptrend(candles, left_index, config)
    if config.require_prior_uptrend and not uptrend_ok:
        return None
    if config.require_liquidity_pass and config.liquidity_pass is not True:
        return None
    if config.require_spread_pass and config.spread_pass is not True:
        return None

    left_price = float(candidate.left_rim["price"])
    bottom_price = float(candidate.cup_bottom["price"])
    right_price = float(candidate.right_rim["price"])
    handle_price = float(candidate.handle_low["price"])
    if left_price <= 0 or right_price <= 0:
        return None

    rim_difference_rate = abs(left_price - right_price) / left_price
    if rim_difference_rate > config.maximum_rim_difference_rate:
        return None

    neckline = max(left_price, right_price)
    cup_reference_price = min(left_price, right_price)
    cup_depth = cup_reference_price - bottom_price
    cup_depth_rate = cup_depth / cup_reference_price if cup_reference_price > 0 else 0.0
    if not config.minimum_cup_depth_rate <= cup_depth_rate <= config.maximum_cup_depth_rate:
        return None

    cup_duration = right_index - left_index
    if not config.minimum_cup_duration <= cup_duration <= config.maximum_cup_duration:
        return None

    atr_at_bottom = _optional_float(candles.iloc[bottom_index]["atr"])
    if atr_at_bottom is None or atr_at_bottom <= 0:
        return None
    bottom_zone_duration = _bottom_zone_duration(
        candles, left_index, right_index, bottom_price, atr_at_bottom, config
    )
    if bottom_zone_duration < config.minimum_bottom_zone_duration:
        return None

    left_decline_duration = bottom_index - left_index
    right_recovery_duration = right_index - bottom_index
    duration_ratio = min(left_decline_duration, right_recovery_duration) / max(
        left_decline_duration, right_recovery_duration
    )
    if duration_ratio <= 0:
        return None

    handle_depth = neckline - handle_price
    handle_depth_ratio = handle_depth / cup_depth if cup_depth > 0 else 0.0
    handle_duration = breakout_index - right_index
    cup_midpoint = bottom_price + (cup_depth * 0.5)
    if handle_depth <= 0:
        return None
    if handle_depth_ratio > config.maximum_handle_depth_ratio:
        return None
    if handle_price < cup_midpoint:
        return None
    if not config.minimum_handle_duration <= handle_duration <= config.maximum_handle_duration:
        return None

    breakout = candles.iloc[breakout_index]
    atr = _optional_float(breakout["atr"])
    volume_ratio = _optional_float(breakout["volume_ratio"])
    if atr is None or atr <= 0 or volume_ratio is None:
        return None

    breakout_price = float(breakout["close"])
    breakout_distance = breakout_price - neckline
    breakout_distance_atr = breakout_distance / atr
    if breakout_distance <= 0 or breakout_distance_atr < config.breakout_atr_multiplier:
        return None
    if volume_ratio < config.weak_breakout_volume_ratio:
        return None
    pattern_status = (
        CupAndHandleStatus.VALID
        if volume_ratio >= config.minimum_breakout_volume_ratio
        else CupAndHandleStatus.WEAK
    )

    displacement_confirmed = _displacement_confirmed(displacement_rows, breakout_index)
    if config.require_displacement_breakout and not displacement_confirmed:
        return None
    follow_through_end_index = _follow_through_end_index(
        candles,
        breakout_index,
        neckline,
        config.breakout_follow_through_bars,
    )
    if follow_through_end_index is None:
        return None
    neckline_retest_status, neckline_retest_wait_bars = _neckline_retest_status(
        candles,
        breakout_index,
        neckline,
        config.neckline_retest_max_wait_bars,
    )

    score_metadata = _calculate_pattern_score_metadata(
        rim_difference_rate=rim_difference_rate,
        cup_depth_rate=cup_depth_rate,
        bottom_zone_duration=bottom_zone_duration,
        duration_ratio=duration_ratio,
        handle_depth_ratio=handle_depth_ratio,
        breakout_distance_atr=breakout_distance_atr,
        volume_ratio=volume_ratio,
        displacement_confirmed=displacement_confirmed,
        config=config,
    )
    pattern_score = float(score_metadata["pattern_score"])
    if pattern_status == CupAndHandleStatus.VALID and pattern_score < config.minimum_pattern_score:
        pattern_status = CupAndHandleStatus.WEAK

    entry_reference = breakout_price
    stop_reference = handle_price
    target_reference, risk_reward = _target_and_risk_reward(
        entry_reference, stop_reference, cup_depth
    )
    if risk_reward is None:
        return None

    event_id = _build_event_id(
        pattern_type="CUP_AND_HANDLE",
        direction=CupAndHandleDirection.BULLISH.value,
        symbol=symbol,
        timeframe=timeframe,
        pivot_timestamps=(
            candles.iloc[left_index]["timestamp"],
            candles.iloc[bottom_index]["timestamp"],
            candles.iloc[right_index]["timestamp"],
            candles.iloc[handle_index]["timestamp"],
        ),
        breakout_timestamp=breakout["timestamp"],
    )

    return CupAndHandleEvent(
        event_id=event_id,
        pattern_type="CUP_AND_HANDLE",
        direction=CupAndHandleDirection.BULLISH.value,
        pattern_status=pattern_status.value,
        symbol=symbol,
        timeframe=timeframe,
        timestamp=candles.iloc[follow_through_end_index]["timestamp"],
        start_index=left_index,
        end_index=follow_through_end_index,
        left_rim_index=left_index,
        cup_bottom_index=bottom_index,
        right_rim_index=right_index,
        handle_low_index=handle_index,
        breakout_index=breakout_index,
        left_rim_price=left_price,
        cup_bottom_price=bottom_price,
        right_rim_price=right_price,
        handle_low_price=handle_price,
        neckline=neckline,
        cup_depth=cup_depth,
        cup_depth_rate=cup_depth_rate,
        cup_duration=cup_duration,
        bottom_zone_duration=bottom_zone_duration,
        duration_ratio=duration_ratio,
        handle_depth=handle_depth,
        handle_depth_ratio=handle_depth_ratio,
        handle_duration=handle_duration,
        breakout_price=breakout_price,
        breakout_distance=breakout_distance,
        breakout_distance_atr=breakout_distance_atr,
        atr=atr,
        volume_ratio=volume_ratio,
        liquidity_pass=config.liquidity_pass,
        spread_pass=config.spread_pass,
        displacement_confirmed=displacement_confirmed,
        prior_uptrend_method=config.prior_uptrend_method.upper(),
        prior_uptrend_strength=prior_uptrend_strength,
        neckline_retest_status=neckline_retest_status,
        neckline_retest_wait_bars=neckline_retest_wait_bars,
        breakout_follow_through_bars=config.breakout_follow_through_bars,
        handle_quality={
            "handle_depth_ratio": handle_depth_ratio,
            "handle_duration": float(handle_duration),
            "handle_low_above_cup_midpoint": 1.0 if handle_price >= cup_midpoint else 0.0,
        },
        detector_target_reference_semantics="detector target_reference = breakout entry_reference + cup_depth; risk planner may rebuild measured targets from neckline/cup_depth.",
        pattern_score=pattern_score,
        entry_reference=entry_reference,
        stop_reference=stop_reference,
        target_reference=target_reference,
        risk_reward=risk_reward,
        reason="Bullish Cup and Handle detected with ATR-buffered neckline breakout.",
        score_components=score_metadata["score_components"],
        score_component_sources=score_metadata["score_component_sources"],
        score_limitations=score_metadata["score_limitations"],
        score_calibration=score_metadata["score_calibration"],
        atr_metadata=atr_timing_metadata(config.atr_config),
        pivot_metadata=pivot_strength_diagnostics(
            (
                candidate.left_rim,
                candidate.cup_bottom,
                candidate.right_rim,
                candidate.handle_low,
            ),
            config.pivot_config,
            current_index=breakout_index,
            candle_count=len(candles),
        ),
    )


def _has_prior_uptrend(candles: pd.DataFrame, left_index: int, config: CupAndHandleConfig) -> tuple[bool, float | None]:
    if left_index < 1:
        return False, None
    method = config.prior_uptrend_method.upper()
    start_index = 0 if method == "LEGACY_GLOBAL" else max(0, left_index - config.local_uptrend_lookback)
    prior = candles.iloc[start_index : left_index + 1]
    if len(prior) < 2:
        return False, None
    first_close = float(prior.iloc[0]["close"])
    left_close = float(candles.iloc[left_index]["close"])
    if first_close <= 0:
        return False, None
    strength = (left_close - first_close) / first_close
    higher_high_ok = True
    if config.local_uptrend_require_higher_high or method == "LEGACY_GLOBAL":
        higher_high_ok = float(candles.iloc[left_index]["high"]) > float(prior.iloc[:-1]["high"].max())
    return strength >= config.local_uptrend_minimum_return_rate and higher_high_ok, strength


def _follow_through_end_index(
    candles: pd.DataFrame,
    breakout_index: int,
    neckline: float,
    required_bars: int,
) -> int | None:
    if required_bars == 0:
        return breakout_index
    end_index = breakout_index + required_bars
    if end_index >= len(candles):
        return None
    for index in range(breakout_index + 1, end_index + 1):
        if float(candles.iloc[index]["close"]) <= neckline:
            return None
    return end_index


def _neckline_retest_status(
    candles: pd.DataFrame,
    breakout_index: int,
    neckline: float,
    max_wait_bars: int | None,
) -> tuple[str, int | None]:
    if max_wait_bars is None:
        return "NOT_REQUESTED", None
    last_index = min(len(candles) - 1, breakout_index + max_wait_bars)
    for index in range(breakout_index + 1, last_index + 1):
        candle = candles.iloc[index]
        if float(candle["close"]) < neckline:
            return "FAILED_BELOW_NECKLINE", index - breakout_index
        if float(candle["low"]) <= neckline <= float(candle["high"]):
            return "RETESTED", index - breakout_index
    return "NOT_RETESTED", None


def _bottom_zone_duration(
    candles: pd.DataFrame,
    left_index: int,
    right_index: int,
    bottom_price: float,
    atr: float,
    config: CupAndHandleConfig,
) -> int:
    zone_low = bottom_price - config.bottom_zone_atr_multiplier * atr
    zone_high = bottom_price + config.bottom_zone_atr_multiplier * atr
    count = 0
    for index in range(left_index + 1, right_index):
        candle = candles.iloc[index]
        if float(candle["low"]) >= zone_low and float(candle["high"]) <= zone_high:
            count += 1
    return count


def _displacement_confirmed(
    displacement_rows: pd.DataFrame | None,
    breakout_index: int,
) -> bool:
    if displacement_rows is None:
        return False
    displacement = displacement_rows.iloc[breakout_index]
    return (
        str(displacement["displacement_direction"]) == DisplacementDirection.BULLISH.value
        and str(displacement["displacement_status"]) == DisplacementStatus.VALID.value
    )


def _calculate_pattern_score(
    *,
    rim_difference_rate: float,
    cup_depth_rate: float,
    bottom_zone_duration: int,
    duration_ratio: float,
    handle_depth_ratio: float,
    breakout_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: CupAndHandleConfig,
) -> float:
    return float(
        _calculate_pattern_score_metadata(
            rim_difference_rate=rim_difference_rate,
            cup_depth_rate=cup_depth_rate,
            bottom_zone_duration=bottom_zone_duration,
            duration_ratio=duration_ratio,
            handle_depth_ratio=handle_depth_ratio,
            breakout_distance_atr=breakout_distance_atr,
            volume_ratio=volume_ratio,
            displacement_confirmed=displacement_confirmed,
            config=config,
        )["pattern_score"]
    )


def _calculate_pattern_score_metadata(
    *,
    rim_difference_rate: float,
    cup_depth_rate: float,
    bottom_zone_duration: int,
    duration_ratio: float,
    handle_depth_ratio: float,
    breakout_distance_atr: float,
    volume_ratio: float,
    displacement_confirmed: bool,
    config: CupAndHandleConfig,
) -> dict[str, Any]:
    rim_score = max(0.0, 1.0 - rim_difference_rate / max(config.maximum_rim_difference_rate, 1e-9))
    depth_midpoint = (config.minimum_cup_depth_rate + config.maximum_cup_depth_rate) / 2
    depth_range = max(config.maximum_cup_depth_rate - config.minimum_cup_depth_rate, 1e-9)
    depth_score = max(0.0, 1.0 - abs(cup_depth_rate - depth_midpoint) / depth_range)
    roundness_score = min(1.0, bottom_zone_duration / config.minimum_bottom_zone_duration) * 0.6 + min(1.0, duration_ratio) * 0.4
    handle_score = max(0.0, 1.0 - handle_depth_ratio / max(config.maximum_handle_depth_ratio, 1e-9))
    breakout_score = 1.0 if breakout_distance_atr >= 0.5 else 0.7
    volume_score = 1.0 if volume_ratio >= config.minimum_breakout_volume_ratio else 0.6
    displacement_score = 1.0 if displacement_confirmed else 0.0

    return build_score_metadata(
        "CUP_AND_HANDLE",
        [
            {"name": "rim_symmetry", "raw_score": rim_score, "weight": 0.15, "source": "observed_rim_difference_rate", "description": "Similarity between left and right rim prices."},
            {"name": "cup_depth", "raw_score": depth_score, "weight": 0.15, "source": "observed_cup_depth_rate", "description": "Cup depth within configured minimum/maximum depth range."},
            {"name": "roundness", "raw_score": roundness_score, "weight": 0.20, "source": "observed_bottom_duration", "description": "Bottom-zone duration and cup duration balance."},
            {"name": "handle_quality", "raw_score": handle_score, "weight": 0.15, "source": "observed_handle_depth_ratio", "description": "Handle pullback depth relative to configured maximum."},
            {"name": "breakout_strength", "raw_score": breakout_score, "weight": 0.15, "source": "observed_breakout_distance_atr", "description": "ATR-normalized neckline breakout distance."},
            {"name": "volume_confirmation", "raw_score": volume_score, "weight": 0.15, "source": "observed_volume_ratio", "description": "Breakout candle relative volume."},
            {"name": "displacement", "raw_score": displacement_score, "weight": 0.05, "source": "observed_displacement_candle", "description": "Directional displacement confirmation at breakout."},
        ],
    )


def _select_best_event(events: list[CupAndHandleEvent]) -> CupAndHandleEvent:
    status_rank = {CupAndHandleStatus.VALID.value: 2, CupAndHandleStatus.WEAK.value: 1}
    return sorted(
        events,
        key=lambda event: (
            status_rank.get(event.pattern_status, -1),
            event.pattern_score,
            event.cup_duration,
            event.volume_ratio,
            event.breakout_distance_atr,
        ),
        reverse=True,
    )[0]


def _target_and_risk_reward(
    entry_reference: float, stop_reference: float, cup_depth: float
) -> tuple[float, float | None]:
    risk = entry_reference - stop_reference
    if risk <= 0:
        return entry_reference, None
    target_reference = entry_reference + cup_depth
    reward = target_reference - entry_reference
    return target_reference, reward / risk


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
