"""Deterministic multi-timeframe candle aggregation and alignment helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.market_data.candle_validation import (
    CandleValidationConfig,
    STANDARD_CANDLE_COLUMNS,
    SUPPORTED_INTERVAL_DELTAS,
    validate_standard_candles,
)


ALIGNMENT_CONTRACT_VERSION = "multitimeframe_candle_alignment_v1"

ALIGNED_CANDLE_FIELDS: tuple[str, ...] = (
    "open_time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


@dataclass(frozen=True)
class MultitimeframeAlignmentResult:
    """Aligned base candles plus derived higher-timeframe candle metadata."""

    candles: pd.DataFrame
    higher_timeframe_candles: dict[str, pd.DataFrame]
    metadata: dict[str, Any]


def align_completed_higher_timeframe_candles(
    candles: pd.DataFrame,
    *,
    source_interval: str = "1m",
    target_intervals: Iterable[str] = ("5m", "15m"),
) -> MultitimeframeAlignmentResult:
    """Return base candles with the latest completed higher-timeframe context.

    The input ``timestamp`` is treated as candle open time. A derived 5m candle
    opened at 00:00 and closed at 00:05 is first visible to the 00:05 base
    candle, never to the 00:04 base candle.
    """

    targets = tuple(target_intervals)
    if not targets:
        raise ValueError("target_intervals must include at least one interval")

    source_delta = _interval_delta(source_interval, context="source_interval")
    target_deltas = {
        target: _validate_target_interval(source_interval, source_delta, target)
        for target in targets
    }

    validate_standard_candles(
        candles,
        CandleValidationConfig(interval=source_interval, enforce_continuity=False, context="Base candle data"),
    )

    base = _normalized_base_candles(candles)
    aligned = base.copy()
    aligned["base_open_time"] = aligned["timestamp"]

    higher_by_interval: dict[str, pd.DataFrame] = {}
    target_metadata: dict[str, dict[str, Any]] = {}

    for target, target_delta in target_deltas.items():
        aggregate = _aggregate_completed_windows(base, source_delta, target_delta)
        higher_by_interval[target] = aggregate
        target_metadata[target] = _target_metadata(
            target,
            source_interval,
            target_delta,
            aggregate,
        )
        aligned = _merge_latest_completed(aligned, aggregate, target)

    metadata = {
        "contract_version": ALIGNMENT_CONTRACT_VERSION,
        "source_interval": source_interval,
        "target_intervals": list(targets),
        "timestamp_semantics": "timestamp is the base candle open time",
        "availability_semantics": (
            "higher-timeframe candles are visible only when their close_time "
            "is less than or equal to the base candle timestamp"
        ),
        "no_lookahead_guarantee": True,
        "base_row_count": int(len(base)),
        "targets": target_metadata,
    }
    return MultitimeframeAlignmentResult(
        candles=aligned.reset_index(drop=True),
        higher_timeframe_candles=higher_by_interval,
        metadata=metadata,
    )


def _normalized_base_candles(candles: pd.DataFrame) -> pd.DataFrame:
    frame = candles.loc[:, list(STANDARD_CANDLE_COLUMNS)].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise", utc=True, format="mixed")
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame.reset_index(drop=True)


def _interval_delta(interval: str, *, context: str) -> pd.Timedelta:
    delta = SUPPORTED_INTERVAL_DELTAS.get(str(interval))
    if delta is None:
        supported = ", ".join(sorted(SUPPORTED_INTERVAL_DELTAS))
        raise ValueError(f"unsupported {context}: {interval}; supported: {supported}")
    return delta


def _validate_target_interval(
    source_interval: str,
    source_delta: pd.Timedelta,
    target_interval: str,
) -> pd.Timedelta:
    target_delta = _interval_delta(target_interval, context="target_interval")
    if target_delta <= source_delta:
        raise ValueError(
            f"target interval {target_interval} must be greater than source interval {source_interval}"
        )
    if target_delta % source_delta != pd.Timedelta(0):
        raise ValueError(
            f"target interval {target_interval} must be divisible by source interval {source_interval}"
        )
    return target_delta


def _aggregate_completed_windows(
    base: pd.DataFrame,
    source_delta: pd.Timedelta,
    target_delta: pd.Timedelta,
) -> pd.DataFrame:
    if base.empty:
        return _empty_aggregate()

    window_size = int(target_delta / source_delta)
    work = base.copy()
    work["open_time"] = work["timestamp"].dt.floor(target_delta)
    work["expected_close_time"] = work["open_time"] + target_delta
    work["expected_index"] = ((work["timestamp"] - work["open_time"]) / source_delta).astype(int)

    rows: list[dict[str, Any]] = []
    for open_time, group in work.groupby("open_time", sort=True):
        expected_indices = set(range(window_size))
        actual_indices = set(int(value) for value in group["expected_index"].tolist())
        close_time = pd.Timestamp(open_time) + target_delta
        is_complete = (
            len(group) == window_size
            and actual_indices == expected_indices
            and pd.Timestamp(group["timestamp"].max()) == close_time - source_delta
        )
        if not is_complete:
            continue
        ordered = group.sort_values("timestamp")
        rows.append(
            {
                "open_time": pd.Timestamp(open_time),
                "close_time": close_time,
                "open": ordered.iloc[0]["open"],
                "high": ordered["high"].max(),
                "low": ordered["low"].min(),
                "close": ordered.iloc[-1]["close"],
                "volume": ordered["volume"].sum(),
                "source_row_count": int(len(ordered)),
                "complete": True,
            }
        )

    if not rows:
        return _empty_aggregate()
    return pd.DataFrame(rows).reset_index(drop=True)


def _empty_aggregate() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "open_time",
            "close_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "source_row_count",
            "complete",
        ]
    )


def _merge_latest_completed(aligned: pd.DataFrame, aggregate: pd.DataFrame, target: str) -> pd.DataFrame:
    prefix = f"mtf_{target}_"

    if aggregate.empty:
        for field in ALIGNED_CANDLE_FIELDS:
            aligned[f"{prefix}{field}"] = pd.NA
        aligned[f"{prefix}available"] = False
        return aligned

    right = aggregate.loc[:, list(ALIGNED_CANDLE_FIELDS)].copy()
    right[f"{prefix}available_from"] = right["close_time"]
    right = right.rename(columns={field: f"{prefix}{field}" for field in ALIGNED_CANDLE_FIELDS})

    merged = pd.merge_asof(
        aligned.sort_values("timestamp"),
        right.sort_values(f"{prefix}available_from"),
        left_on="timestamp",
        right_on=f"{prefix}available_from",
        direction="backward",
    )
    merged[f"{prefix}available"] = merged[f"{prefix}open_time"].notna()
    merged = merged.drop(columns=[f"{prefix}available_from"])
    return merged


def _target_metadata(
    target: str,
    source_interval: str,
    target_delta: pd.Timedelta,
    aggregate: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "target_interval": target,
        "source_interval": source_interval,
        "target_duration_seconds": int(target_delta.total_seconds()),
        "completed_window_count": int(len(aggregate)),
        "availability_column": f"mtf_{target}_available",
        "field_prefix": f"mtf_{target}_",
        "close_availability_semantics": "visible when close_time <= base timestamp",
        "partial_or_incomplete_windows": "excluded from aligned OHLCV and left unavailable",
        "no_lookahead": True,
    }
