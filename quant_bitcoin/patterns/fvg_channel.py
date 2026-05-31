"""FVG v2 parallel-channel research helpers.

This module is deterministic, offline-only analysis code. It does not fetch
market data, persist data, or communicate with exchanges.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.risk.exit_simulation import PatternExitEvent, PatternExitReason


CHANNEL_SCHEMA_VERSION = "fvg_parallel_channel_v1"
CHANNEL_ENTRY_SCHEMA_VERSION = "fvg_parallel_channel_entry_v1"
CHANNEL_EXIT_SCHEMA_VERSION = "fvg_parallel_channel_exit_v1"
CHANNEL_BOUNDARY_DIRECTION_RULE = "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
CHANNEL_TARGET_POLICY = "PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1"
CHANNEL_RETEST_CONFIRMATION_BASIS = "CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1"


class ChannelBoundary(Enum):
    LOWER = "LOWER"
    UPPER = "UPPER"
    RETEST_STRUCTURE_LOW = "RETEST_STRUCTURE_LOW"
    CHANNEL_WIDTH_TARGET = "CHANNEL_WIDTH_TARGET"


class ChannelEntrySide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class ChannelTrendDirection(Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"


@dataclass(frozen=True)
class FvgChannelConfig:
    enabled: bool = False
    window: int = 20
    tolerance: float = 1e-8
    max_wait_bars: int | None = None
    allow_same_candle_exit: bool = False
    standalone_scan_enabled: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "fvg_parallel_channel_config_v1",
            "enabled": self.enabled,
            "window": self.window,
            "tolerance": self.tolerance,
            "max_wait_bars": self.max_wait_bars,
            "allow_same_candle_exit": self.allow_same_candle_exit,
            "standalone_scan_enabled": self.standalone_scan_enabled,
            "scan_semantics": (
                "fvg_event_expansion_plus_standalone_visible_prefix_scan"
                if self.standalone_scan_enabled
                else "fvg_event_expansion_only"
            ),
            "stop_target_policy": CHANNEL_TARGET_POLICY,
            "channel_boundary_direction_rule": CHANNEL_BOUNDARY_DIRECTION_RULE,
            "channel_target_policy": CHANNEL_TARGET_POLICY,
            "atr_used_for_stop_or_target": False,
        }


@dataclass(frozen=True)
class ChannelLine:
    slope: float
    intercept: float

    def value_at(self, candle_index: int | float) -> float:
        return self.slope * float(candle_index) + self.intercept

    def to_metadata(self) -> dict[str, float]:
        return {"slope": self.slope, "intercept": self.intercept}


@dataclass(frozen=True)
class FvgParallelChannel:
    window_start_index: int
    window_end_index: int
    lower_anchor_1_index: int | None
    lower_anchor_2_index: int | None
    upper_touch_index: int | None
    lower_line: ChannelLine
    upper_line: ChannelLine
    width: float
    tolerance: float
    lower_anchor_1_price: float | None
    lower_anchor_2_price: float | None
    upper_touch_price: float | None
    trend_direction: ChannelTrendDirection = ChannelTrendDirection.UPTREND
    upper_anchor_1_index: int | None = None
    upper_anchor_2_index: int | None = None
    lower_touch_index: int | None = None
    upper_anchor_1_price: float | None = None
    upper_anchor_2_price: float | None = None
    lower_touch_price: float | None = None

    def lower_at(self, candle_index: int | float) -> float:
        return self.lower_line.value_at(candle_index)

    def upper_at(self, candle_index: int | float) -> float:
        return self.upper_line.value_at(candle_index)

    def to_metadata(self) -> dict[str, Any]:
        identity = channel_identity(self)
        return {
            "schema_version": CHANNEL_SCHEMA_VERSION,
            "fit": "VALID",
            "selection_rule": "latest_second_anchor_then_narrowest_width_then_latest_opposite_boundary_touch",
            "channel_id": channel_id(self),
            "channel_identity": identity,
            "trend_direction": self.trend_direction.value,
            "channel_trend_direction": self.trend_direction.value,
            "channel_boundary_direction_rule": CHANNEL_BOUNDARY_DIRECTION_RULE,
            "window_start_index": self.window_start_index,
            "window_end_index": self.window_end_index,
            "lower_anchor_1_index": self.lower_anchor_1_index,
            "lower_anchor_2_index": self.lower_anchor_2_index,
            "upper_touch_index": self.upper_touch_index,
            "lower_anchor_1_price": self.lower_anchor_1_price,
            "lower_anchor_2_price": self.lower_anchor_2_price,
            "upper_touch_price": self.upper_touch_price,
            "upper_anchor_1_index": self.upper_anchor_1_index,
            "upper_anchor_2_index": self.upper_anchor_2_index,
            "lower_touch_index": self.lower_touch_index,
            "upper_anchor_1_price": self.upper_anchor_1_price,
            "upper_anchor_2_price": self.upper_anchor_2_price,
            "lower_touch_price": self.lower_touch_price,
            "lower_line": self.lower_line.to_metadata(),
            "upper_line": self.upper_line.to_metadata(),
            "slope": self.lower_line.slope,
            "width": self.width,
            "tolerance": self.tolerance,
            "all_candles_fit_inside_channel": True,
            "atr_used_for_stop_or_target": False,
        }


def channel_identity(channel: FvgParallelChannel) -> dict[str, Any]:
    """Return the stable geometry identity used to dedupe the same drawn channel."""

    return {
        "schema_version": "fvg_parallel_channel_identity_v1",
        "trend_direction": channel.trend_direction.value,
        "lower_anchor_1_index": channel.lower_anchor_1_index,
        "lower_anchor_2_index": channel.lower_anchor_2_index,
        "upper_touch_index": channel.upper_touch_index,
        "upper_anchor_1_index": channel.upper_anchor_1_index,
        "upper_anchor_2_index": channel.upper_anchor_2_index,
        "lower_touch_index": channel.lower_touch_index,
        "lower_line_slope": channel.lower_line.slope,
        "lower_line_intercept": channel.lower_line.intercept,
        "upper_line_intercept": channel.upper_line.intercept,
        "width": channel.width,
    }


def channel_id(channel: FvgParallelChannel) -> str:
    payload = json.dumps(channel_identity(channel), sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ChannelRetestEntry:
    side: ChannelEntrySide
    timestamp: Any
    fill_price: float
    candle_index: int
    touch_index: int
    confirmation_index: int
    entry_boundary: ChannelBoundary
    stop_price: float
    target_price: float
    metadata: dict[str, Any]
    stop_source: str = "CHANNEL_BOUNDARY"
    retest_structure_low: float | None = None


def detect_fvg_parallel_channel(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    config: FvgChannelConfig | None = None,
) -> FvgParallelChannel | None:
    """Detect the owner's parallel-channel geometry in completed candles."""

    cfg = config or FvgChannelConfig(enabled=True)
    frame = _normalize_candles(candles)
    if frame.empty or len(frame) < 3 or cfg.window < 3:
        return None

    window = frame.iloc[-cfg.window :].copy()
    candidates: list[FvgParallelChannel] = []
    tol = max(float(cfg.tolerance), 0.0)

    records = list(window.itertuples(index=False))
    candidates.extend(_detect_uptrend_channels(records, tol))
    candidates.extend(_detect_downtrend_channels(records, tol))

    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda item: (
            _second_anchor_index(item),
            -item.width,
            _opposite_touch_index(item),
        ),
        reverse=True,
    )[0]


def simulate_channel_retest_entry(
    channel: FvgParallelChannel,
    future_candles: pd.DataFrame | Iterable[dict[str, Any]],
    config: FvgChannelConfig | None = None,
    *,
    context_candles: pd.DataFrame | Iterable[dict[str, Any]] | None = None,
) -> ChannelRetestEntry | None:
    """Return the first valid channel-boundary retest entry after channel fit."""

    cfg = config or FvgChannelConfig(enabled=True)
    frame = _normalize_candles(future_candles)
    if frame.empty:
        return None
    max_wait = cfg.max_wait_bars
    rows = list(frame.itertuples(index=False))
    if max_wait is not None:
        rows = rows[: max(0, int(max_wait))]
    context_rows: list[Any] = []
    if context_candles is not None:
        context_rows = list(_normalize_candles(context_candles).itertuples(index=False))

    seen_rows: list[Any] = []
    for row in rows:
        index = int(row.candle_index)
        prior_rows = [
            prior_row
            for prior_row in [*context_rows, *seen_rows]
            if int(prior_row.candle_index) < index
        ]
        pre_retest_candle = _latest_prior_candle(prior_rows)
        seen_rows.append(row)
        upper = channel.upper_at(index)
        lower = channel.lower_at(index)
        close = float(row.close)
        confirmed_upper_retest = close >= upper - channel.tolerance
        confirmed_lower_retest = close <= lower + channel.tolerance
        if confirmed_upper_retest and confirmed_lower_retest:
            return None
        if confirmed_upper_retest:
            return _entry_result(
                side=ChannelEntrySide.LONG,
                boundary=ChannelBoundary.UPPER,
                row=row,
                channel=channel,
                retest_rows=seen_rows,
                pre_retest_candle=pre_retest_candle,
            )
        if confirmed_lower_retest:
            return _entry_result(
                side=ChannelEntrySide.SHORT,
                boundary=ChannelBoundary.LOWER,
                row=row,
                channel=channel,
                retest_rows=seen_rows,
                pre_retest_candle=pre_retest_candle,
            )
    return None


def simulate_channel_boundary_exit(
    channel: FvgParallelChannel,
    entry: ChannelRetestEntry,
    future_candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    allow_same_candle_exit: bool = False,
) -> PatternExitEvent | None:
    """Simulate dynamic line stop/target exits after a channel entry."""

    frame = _normalize_candles(future_candles)
    if frame.empty:
        return None
    for row in frame.itertuples(index=False):
        candle_index = int(row.candle_index)
        if candle_index < entry.candle_index:
            continue
        if candle_index == entry.candle_index and not allow_same_candle_exit:
            continue
        upper = channel.upper_at(candle_index)
        lower = channel.lower_at(candle_index)
        if entry.side is ChannelEntrySide.LONG:
            stop_hit = float(row.low) <= entry.stop_price + channel.tolerance
            target_hit = float(row.high) >= entry.target_price - channel.tolerance
            stop_price = entry.stop_price
            target_price = entry.target_price
            stop_boundary = ChannelBoundary.LOWER
            target_boundary = ChannelBoundary.CHANNEL_WIDTH_TARGET
        else:
            stop_hit = float(row.high) >= entry.stop_price - channel.tolerance
            target_hit = float(row.low) <= entry.target_price + channel.tolerance
            stop_price = entry.stop_price
            target_price = entry.target_price
            stop_boundary = ChannelBoundary.UPPER
            target_boundary = ChannelBoundary.CHANNEL_WIDTH_TARGET

        ambiguous = stop_hit and target_hit
        if stop_hit:
            return _exit_event(
                row=row,
                reason=PatternExitReason.HARD_STOP,
                price=stop_price,
                target_name=f"CHANNEL_{stop_boundary.value}_STOP",
                stop_price=stop_price,
                target_price=target_price,
                channel=channel,
                entry=entry,
                stop_boundary=stop_boundary,
                target_boundary=target_boundary,
                ambiguous=ambiguous,
            )
        if target_hit:
            return _exit_event(
                row=row,
                reason=PatternExitReason.TAKE_PROFIT,
                price=target_price,
                target_name=f"CHANNEL_{target_boundary.value}_TARGET",
                stop_price=stop_price,
                target_price=target_price,
                channel=channel,
                entry=entry,
                stop_boundary=stop_boundary,
                target_boundary=target_boundary,
                ambiguous=False,
            )
    return None


def _entry_result(
    *,
    side: ChannelEntrySide,
    boundary: ChannelBoundary,
    row: Any,
    channel: FvgParallelChannel,
    retest_rows: list[Any],
    pre_retest_candle: Any | None,
) -> ChannelRetestEntry | None:
    candle_index = int(row.candle_index)
    lower = channel.lower_at(candle_index)
    upper = channel.upper_at(candle_index)
    channel_width = upper - lower
    if channel_width <= 0 or not isfinite(channel_width):
        return None
    stop_boundary = ChannelBoundary.LOWER if side is ChannelEntrySide.LONG else ChannelBoundary.UPPER
    target_boundary = ChannelBoundary.CHANNEL_WIDTH_TARGET
    retest_structure_low = _retest_structure_low(retest_rows) if side is ChannelEntrySide.LONG else None
    line_stop_price_diagnostic = lower if side is ChannelEntrySide.LONG else upper
    stop_source = "PRE_RETEST_CANDLE_LOW" if side is ChannelEntrySide.LONG else "PRE_RETEST_CANDLE_HIGH"
    fill_price = float(row.close)
    if pre_retest_candle is None:
        stop_price = fill_price
        stop_valid = False
        invalid_reason = "PRE_RETEST_CANDLE_MISSING"
        pre_retest_index = None
        pre_retest_timestamp = None
        pre_retest_low = None
        pre_retest_high = None
    else:
        pre_retest_index = int(pre_retest_candle.candle_index)
        pre_retest_timestamp = pre_retest_candle.timestamp
        pre_retest_low = float(pre_retest_candle.low)
        pre_retest_high = float(pre_retest_candle.high)
        stop_price = pre_retest_low if side is ChannelEntrySide.LONG else pre_retest_high
        if side is ChannelEntrySide.LONG:
            stop_valid = _positive_finite(stop_price) and stop_price < fill_price
            invalid_reason = None if stop_valid else "LONG_PRE_RETEST_LOW_NOT_BELOW_ENTRY"
        else:
            stop_valid = _positive_finite(stop_price) and stop_price > fill_price
            invalid_reason = None if stop_valid else "SHORT_PRE_RETEST_HIGH_NOT_ABOVE_ENTRY"
    target_price = fill_price + channel_width if side is ChannelEntrySide.LONG else fill_price - channel_width
    opposite_boundary_target = upper if side is ChannelEntrySide.LONG else lower
    metadata = {
        "schema_version": CHANNEL_ENTRY_SCHEMA_VERSION,
        "channel_mode": "FVG_V2_PARALLEL_CHANNEL",
        "position_side": side.value,
        "channel_trend_direction": channel.trend_direction.value,
        "channel_direction_rule": CHANNEL_BOUNDARY_DIRECTION_RULE,
        "channel_boundary_direction_mode": CHANNEL_BOUNDARY_DIRECTION_RULE,
        "original_channel_entry_side": _legacy_entry_side_for_boundary(boundary).value,
        "effective_channel_entry_side": side.value,
        "entry_boundary": boundary.value,
        "retest_confirmation_basis": CHANNEL_RETEST_CONFIRMATION_BASIS,
        "retest_confirmation_price_source": "close",
        "retest_close_price": float(row.close),
        "retest_close_rule": (
            "close >= upper_channel_line"
            if boundary is ChannelBoundary.UPPER
            else "close <= lower_channel_line"
        ),
        "touch_candle_index": candle_index,
        "reaction_candle_index": candle_index,
        "confirmation_candle_index": candle_index,
        "fill_candle_index": candle_index,
        "fill_price": float(row.close),
        "fill_price_source": "channel_retest_confirmation_close",
        "entry_trigger": f"{boundary.value}_CLOSE_BASED_RETEST",
        "stop_boundary": stop_boundary.value,
        "target_boundary": target_boundary.value,
        "stop_source": stop_source,
        "retest_structure_low": retest_structure_low,
        "pre_retest_stop_valid": stop_valid,
        "pre_retest_stop_invalid_reason": invalid_reason,
        "pre_retest_candle_index": pre_retest_index,
        "pre_retest_candle_timestamp": pre_retest_timestamp,
        "pre_retest_candle_low": pre_retest_low,
        "pre_retest_candle_high": pre_retest_high,
        "channel_lower_line_price_at_entry": lower,
        "channel_upper_line_price_at_entry": upper,
        "channel_width_at_entry": channel_width,
        "target_price_source": "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE",
        "target_source": "FVG_V2_CHANNEL_WIDTH_PROJECTION",
        "channel_target_policy": CHANNEL_TARGET_POLICY,
        "projected_channel_width_target": target_price,
        "opposite_boundary_target_price": opposite_boundary_target,
        "line_stop_price": stop_price,
        "line_stop_price_diagnostic": line_stop_price_diagnostic,
        "line_target_price": target_price,
        "atr_used_for_stop_or_target": False,
        "same_candle_entry_exit_ambiguity": False,
        "channel_geometry": channel.to_metadata(),
        "fvg_channel": channel.to_metadata(),
    }
    return ChannelRetestEntry(
        side=side,
        timestamp=row.timestamp,
        fill_price=fill_price,
        candle_index=candle_index,
        touch_index=candle_index,
        confirmation_index=candle_index,
        entry_boundary=boundary,
        stop_price=stop_price,
        target_price=target_price,
        metadata=metadata,
        stop_source=stop_source,
        retest_structure_low=retest_structure_low,
    )


def _exit_event(
    *,
    row: Any,
    reason: PatternExitReason,
    price: float,
    target_name: str,
    stop_price: float,
    target_price: float,
    channel: FvgParallelChannel,
    entry: ChannelRetestEntry,
    stop_boundary: ChannelBoundary,
    target_boundary: ChannelBoundary,
    ambiguous: bool,
) -> PatternExitEvent:
    return PatternExitEvent(
        timestamp=row.timestamp,
        candle_index=int(row.candle_index),
        reason=reason,
        price=price,
        quantity_ratio=1.0,
        remaining_quantity_ratio=0.0,
        target_name=target_name,
        stop_price=stop_price,
        metadata={
            "schema_version": CHANNEL_EXIT_SCHEMA_VERSION,
            "channel_mode": "FVG_V2_PARALLEL_CHANNEL",
            "exit_candle_index": int(row.candle_index),
            "stop_boundary": stop_boundary.value,
            "target_boundary": target_boundary.value,
            "stop_source": entry.stop_source,
            "retest_structure_low": entry.retest_structure_low,
            "pre_retest_stop_valid": entry.metadata.get("pre_retest_stop_valid"),
            "pre_retest_stop_invalid_reason": entry.metadata.get("pre_retest_stop_invalid_reason"),
            "pre_retest_candle_index": entry.metadata.get("pre_retest_candle_index"),
            "pre_retest_candle_timestamp": entry.metadata.get("pre_retest_candle_timestamp"),
            "pre_retest_candle_low": entry.metadata.get("pre_retest_candle_low"),
            "pre_retest_candle_high": entry.metadata.get("pre_retest_candle_high"),
            "channel_width_at_entry": entry.metadata.get("channel_width_at_entry"),
            "target_price_source": entry.metadata.get("target_price_source"),
            "target_source": "FVG_V2_CHANNEL_WIDTH_PROJECTION",
            "channel_target_policy": CHANNEL_TARGET_POLICY,
            "projected_channel_width_target": entry.metadata.get("projected_channel_width_target"),
            "opposite_boundary_target_price": entry.metadata.get("opposite_boundary_target_price"),
            "line_stop_price": stop_price,
            "line_stop_price_diagnostic": entry.metadata.get("line_stop_price_diagnostic"),
            "line_target_price": target_price,
            "exit_line_price": price,
            "channel_geometry": channel.to_metadata(),
            "same_candle_entry_exit_ambiguity": ambiguous and int(row.candle_index) == entry.candle_index,
            "ambiguous_stop_target": ambiguous,
            "atr_used_for_stop_or_target": False,
            "channel_trend_direction": channel.trend_direction.value,
            "channel_direction_rule": CHANNEL_BOUNDARY_DIRECTION_RULE,
            "channel_boundary_direction_mode": CHANNEL_BOUNDARY_DIRECTION_RULE,
        },
    )


def _detect_uptrend_channels(records: list[Any], tol: float) -> list[FvgParallelChannel]:
    candidates: list[FvgParallelChannel] = []
    for first_pos in range(0, len(records) - 2):
        first = records[first_pos]
        x1 = int(first.candle_index)
        y1 = float(first.low)
        for second_pos in range(first_pos + 2, len(records)):
            second = records[second_pos]
            x2 = int(second.candle_index)
            y2 = float(second.low)
            if x2 == x1:
                continue
            slope = (y2 - y1) / (x2 - x1)
            if slope <= 0 or not isfinite(slope):
                continue
            intercept = y1 - slope * x1
            lower = ChannelLine(slope=slope, intercept=intercept)
            if any(float(row.low) < lower.value_at(int(row.candle_index)) - tol for row in records):
                continue

            high_offsets = [
                float(row.high) - lower.value_at(int(row.candle_index))
                for row in records
            ]
            width = max(high_offsets)
            if width <= 0 or not isfinite(width):
                continue
            upper = ChannelLine(slope=slope, intercept=intercept + width)
            touch_positions = [
                pos
                for pos, offset in enumerate(high_offsets)
                if abs(offset - width) <= tol and first_pos < pos < second_pos
            ]
            if not touch_positions:
                continue
            if any(float(row.high) > upper.value_at(int(row.candle_index)) + tol for row in records):
                continue
            touch_pos = touch_positions[-1]
            touch = records[touch_pos]
            candidates.append(
                FvgParallelChannel(
                    window_start_index=int(records[0].candle_index),
                    window_end_index=int(records[-1].candle_index),
                    lower_anchor_1_index=x1,
                    lower_anchor_2_index=x2,
                    upper_touch_index=int(touch.candle_index),
                    lower_line=lower,
                    upper_line=upper,
                    width=width,
                    tolerance=tol,
                    lower_anchor_1_price=y1,
                    lower_anchor_2_price=y2,
                    upper_touch_price=float(touch.high),
                    trend_direction=ChannelTrendDirection.UPTREND,
                )
            )
    return candidates


def _detect_downtrend_channels(records: list[Any], tol: float) -> list[FvgParallelChannel]:
    candidates: list[FvgParallelChannel] = []
    for first_pos in range(0, len(records) - 2):
        first = records[first_pos]
        x1 = int(first.candle_index)
        y1 = float(first.high)
        for second_pos in range(first_pos + 2, len(records)):
            second = records[second_pos]
            x2 = int(second.candle_index)
            y2 = float(second.high)
            if x2 == x1:
                continue
            slope = (y2 - y1) / (x2 - x1)
            if slope >= 0 or not isfinite(slope):
                continue
            intercept = y1 - slope * x1
            upper = ChannelLine(slope=slope, intercept=intercept)
            if any(float(row.high) > upper.value_at(int(row.candle_index)) + tol for row in records):
                continue

            low_offsets = [
                upper.value_at(int(row.candle_index)) - float(row.low)
                for row in records
            ]
            width = max(low_offsets)
            if width <= 0 or not isfinite(width):
                continue
            lower = ChannelLine(slope=slope, intercept=intercept - width)
            touch_positions = [
                pos
                for pos, offset in enumerate(low_offsets)
                if abs(offset - width) <= tol and first_pos < pos < second_pos
            ]
            if not touch_positions:
                continue
            if any(float(row.low) < lower.value_at(int(row.candle_index)) - tol for row in records):
                continue
            touch_pos = touch_positions[-1]
            touch = records[touch_pos]
            candidates.append(
                FvgParallelChannel(
                    window_start_index=int(records[0].candle_index),
                    window_end_index=int(records[-1].candle_index),
                    lower_anchor_1_index=None,
                    lower_anchor_2_index=None,
                    upper_touch_index=None,
                    lower_line=lower,
                    upper_line=upper,
                    width=width,
                    tolerance=tol,
                    lower_anchor_1_price=None,
                    lower_anchor_2_price=None,
                    upper_touch_price=None,
                    trend_direction=ChannelTrendDirection.DOWNTREND,
                    upper_anchor_1_index=x1,
                    upper_anchor_2_index=x2,
                    lower_touch_index=int(touch.candle_index),
                    upper_anchor_1_price=y1,
                    upper_anchor_2_price=y2,
                    lower_touch_price=float(touch.low),
                )
            )
    return candidates


def _second_anchor_index(channel: FvgParallelChannel) -> int:
    if channel.trend_direction is ChannelTrendDirection.DOWNTREND:
        return int(channel.upper_anchor_2_index if channel.upper_anchor_2_index is not None else -1)
    return int(channel.lower_anchor_2_index if channel.lower_anchor_2_index is not None else -1)


def _opposite_touch_index(channel: FvgParallelChannel) -> int:
    if channel.trend_direction is ChannelTrendDirection.DOWNTREND:
        return int(channel.lower_touch_index if channel.lower_touch_index is not None else -1)
    return int(channel.upper_touch_index if channel.upper_touch_index is not None else -1)


def _legacy_entry_side_for_boundary(boundary: ChannelBoundary) -> ChannelEntrySide:
    return ChannelEntrySide.SHORT if boundary is ChannelBoundary.UPPER else ChannelEntrySide.LONG


def _retest_structure_low(rows: list[Any]) -> float | None:
    lows = [float(row.low) for row in rows if _positive_finite(float(row.low))]
    if not lows:
        return None
    return min(lows)


def _latest_prior_candle(rows: list[Any]) -> Any | None:
    if not rows:
        return None
    return max(rows, key=lambda row: int(row.candle_index))


def _positive_finite(value: float) -> bool:
    return isfinite(value) and value > 0


def _normalize_candles(candles: pd.DataFrame | Iterable[dict[str, Any]]) -> pd.DataFrame:
    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if frame.empty:
        return pd.DataFrame(columns=["candle_index", "timestamp", "open", "high", "low", "close"])
    records = frame.reset_index(drop=False).rename(columns={"index": "_source_index"})
    if "open" not in records.columns and "close" in records.columns:
        records["open"] = records["close"]
    required = ("timestamp", "open", "high", "low", "close")
    missing = [column for column in required if column not in records.columns]
    if missing:
        raise ValueError(f"channel candles missing required columns: {', '.join(missing)}")
    source_index = records["_source_index"]
    if source_index.map(lambda value: isinstance(value, int)).all():
        records["candle_index"] = source_index.astype(int)
    else:
        records["candle_index"] = range(len(records))
    normalized = records[["candle_index", "timestamp", "open", "high", "low", "close"]].copy()
    for column in ("open", "high", "low", "close"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    if normalized[["open", "high", "low", "close"]].isna().any().any():
        raise ValueError("channel candles contain non-numeric OHLC values")
    return normalized.sort_values("candle_index").reset_index(drop=True)
