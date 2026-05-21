"""Pattern event-study schema and serialization helpers.

This module intentionally separates pattern-event recording from strategy
simulation. It defines a deterministic record format that can be used for
research datasets before any entry/exit rule promotion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class PatternEventStudyRecord:
    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: Any
    start_index: int
    end_index: int
    entry_reference: float | None = None
    stop_reference: float | None = None
    target_reference: float | None = None
    risk_reward: float | None = None
    pattern_score: float | None = None
    volume_ratio: float | None = None
    displacement_confirmed: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PatternForwardLabelConfig:
    horizons: tuple[int, ...] = (1, 3, 5, 15, 60)
    mfe_mae_horizons: tuple[int, ...] = (5, 15, 60)
    r_multiples: tuple[float, ...] = (1.0, 2.0)


@dataclass(frozen=True)
class PatternForwardLabel:
    forward_return_1: float | None = None
    forward_return_3: float | None = None
    forward_return_5: float | None = None
    forward_return_15: float | None = None
    forward_return_60: float | None = None
    mfe_5: float | None = None
    mae_5: float | None = None
    mfe_15: float | None = None
    mae_15: float | None = None
    mfe_60: float | None = None
    mae_60: float | None = None
    hit_1r_before_minus_1r: bool | None = None
    hit_2r_before_minus_1r: bool | None = None
    time_to_invalidation: int | None = None


@dataclass(frozen=True)
class PatternEventStudyDataset:
    records: tuple[PatternEventStudyRecord, ...]
    labels: tuple[PatternForwardLabel | None, ...] = ()


def pattern_event_to_study_record(
    event: Any,
    source_metadata: Mapping[str, Any] | None = None,
) -> PatternEventStudyRecord:
    payload = _event_payload(event)

    metadata: dict[str, Any] = dict(source_metadata or {})
    for key, value in payload.items():
        if key not in _STUDY_FIELDS:
            metadata[key] = value

    return PatternEventStudyRecord(
        event_id=str(payload["event_id"]),
        pattern_type=str(payload["pattern_type"]),
        direction=str(payload["direction"]),
        pattern_status=str(payload["pattern_status"]),
        symbol=_optional_str(payload.get("symbol")),
        timeframe=_optional_str(payload.get("timeframe")),
        timestamp=payload["timestamp"],
        start_index=int(payload["start_index"]),
        end_index=int(payload["end_index"]),
        entry_reference=_optional_float(payload.get("entry_reference")),
        stop_reference=_optional_float(payload.get("stop_reference")),
        target_reference=_optional_float(payload.get("target_reference")),
        risk_reward=_optional_float(payload.get("risk_reward")),
        pattern_score=_optional_float(payload.get("pattern_score")),
        volume_ratio=_optional_float(payload.get("volume_ratio")),
        displacement_confirmed=_optional_bool(payload.get("displacement_confirmed")),
        metadata=metadata,
    )


def records_to_dataframe(records: Iterable[PatternEventStudyRecord]) -> pd.DataFrame:
    rows = [asdict(record) for record in records]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=list(_DATAFRAME_COLUMNS))
    return frame.reindex(columns=list(_DATAFRAME_COLUMNS))


def extract_fair_value_gap_event_study_records(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    config: Any = None,
) -> PatternEventStudyDataset:
    """Extract deterministic Fair Value Gap event-study records with no look-ahead."""

    from quant_bitcoin.backtesting.basic import NUMERIC_CANDLE_COLUMNS, STANDARD_CANDLE_COLUMNS
    from quant_bitcoin.patterns import detect_fair_value_gaps

    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    missing = [column for column in STANDARD_CANDLE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required candle columns: {', '.join(missing)}")

    normalized = frame.loc[:, STANDARD_CANDLE_COLUMNS].copy(deep=True)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
    for column in NUMERIC_CANDLE_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="raise")
    if normalized["timestamp"].isnull().any():
        raise ValueError("timestamp contains null or invalid values")
    if not normalized["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted by ascending timestamp")

    if len(normalized) < 3:
        return PatternEventStudyDataset(records=())

    records: list[PatternEventStudyRecord] = []
    seen_event_ids: set[str] = set()

    for current_index in range(len(normalized)):
        prefix = normalized.iloc[: current_index + 1].copy(deep=True)
        current_events = detect_fair_value_gaps(
            prefix,
            symbol=symbol,
            timeframe=timeframe,
            config=config,
        )
        for event in current_events:
            if int(event.end_index) != current_index:
                continue
            if event.event_id in seen_event_ids:
                continue
            seen_event_ids.add(event.event_id)
            records.append(pattern_event_to_study_record(event))

    return PatternEventStudyDataset(records=tuple(records))


_STUDY_FIELDS: frozenset[str] = frozenset(
    {
        "event_id",
        "pattern_type",
        "direction",
        "pattern_status",
        "symbol",
        "timeframe",
        "timestamp",
        "start_index",
        "end_index",
        "entry_reference",
        "stop_reference",
        "target_reference",
        "risk_reward",
        "pattern_score",
        "volume_ratio",
        "displacement_confirmed",
    }
)

_DATAFRAME_COLUMNS: tuple[str, ...] = (
    "event_id",
    "pattern_type",
    "direction",
    "pattern_status",
    "symbol",
    "timeframe",
    "timestamp",
    "start_index",
    "end_index",
    "entry_reference",
    "stop_reference",
    "target_reference",
    "risk_reward",
    "pattern_score",
    "volume_ratio",
    "displacement_confirmed",
    "metadata",
)


def _event_payload(event: Any) -> dict[str, Any]:
    if is_dataclass(event):
        payload = asdict(event)
    elif isinstance(event, Mapping):
        payload = dict(event)
    elif hasattr(event, "__dict__"):
        payload = dict(vars(event))
    else:
        raise TypeError("event must be a dataclass, mapping, or object with __dict__")

    required = (
        "event_id",
        "pattern_type",
        "direction",
        "pattern_status",
        "timestamp",
        "start_index",
        "end_index",
    )
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"event missing required field(s): {', '.join(missing)}")
    return payload


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
