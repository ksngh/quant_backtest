from __future__ import annotations

from dataclasses import dataclass

from quant_bitcoin.backtesting.pattern_event_study import (
    PatternEventStudyRecord,
    pattern_event_to_study_record,
    records_to_dataframe,
)
from quant_bitcoin.patterns.fair_value_gap import PatternEvent


def test_pattern_event_to_study_record_from_fvg_event() -> None:
    event = PatternEvent(
        event_id="fvg-1",
        pattern_type="FAIR_VALUE_GAP",
        direction="BULLISH",
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2024-01-01T00:02:00Z",
        start_index=0,
        end_index=2,
        candle_1_index=0,
        candle_2_index=1,
        candle_3_index=2,
        zone_low=100.0,
        zone_high=101.0,
        zone_mid=100.5,
        gap_size=1.0,
        gap_size_atr=0.4,
        fill_ratio=0.0,
        fvg_state="FRESH",
        displacement_confirmed=True,
        displacement_direction="BULLISH",
        volume_ratio=1.8,
        liquidity_pass=None,
        spread_pass=None,
        structure_context=None,
        support_resistance_context=None,
        pattern_score=0.85,
        entry_reference=100.5,
        stop_reference=99.9,
        target_reference=101.7,
        risk_reward=2.0,
        reason="valid",
    )

    record = pattern_event_to_study_record(event, source_metadata={"dataset": "unit"})

    assert record.event_id == "fvg-1"
    assert record.pattern_type == "FAIR_VALUE_GAP"
    assert record.displacement_confirmed is True
    assert record.volume_ratio == 1.8
    assert record.metadata["dataset"] == "unit"
    assert record.metadata["candle_1_index"] == 0
    assert record.metadata["reason"] == "valid"


@dataclass(frozen=True)
class GenericPatternEvent:
    event_id: str
    pattern_type: str
    direction: str
    pattern_status: str
    symbol: str | None
    timeframe: str | None
    timestamp: str
    start_index: int
    end_index: int


def test_pattern_event_to_study_record_handles_missing_optional_fields() -> None:
    event = GenericPatternEvent(
        event_id="generic-1",
        pattern_type="GENERIC",
        direction="BEARISH",
        pattern_status="PENDING",
        symbol=None,
        timeframe=None,
        timestamp="2024-01-01T01:00:00Z",
        start_index=10,
        end_index=11,
    )

    record = pattern_event_to_study_record(event)

    assert record.entry_reference is None
    assert record.stop_reference is None
    assert record.target_reference is None
    assert record.pattern_score is None
    assert record.metadata == {}


def test_records_to_dataframe_is_deterministic() -> None:
    records = [
        PatternEventStudyRecord(
            event_id="a",
            pattern_type="X",
            direction="BULLISH",
            pattern_status="VALID",
            symbol="BTCUSDT",
            timeframe="1m",
            timestamp="2024-01-01T00:00:00Z",
            start_index=1,
            end_index=2,
            metadata={"k": 1},
        ),
        PatternEventStudyRecord(
            event_id="b",
            pattern_type="Y",
            direction="BEARISH",
            pattern_status="WEAK",
            symbol="BTCUSDT",
            timeframe="1m",
            timestamp="2024-01-01T00:01:00Z",
            start_index=3,
            end_index=4,
            metadata={"k": 2},
        ),
    ]

    frame = records_to_dataframe(records)

    assert frame.columns.tolist() == [
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
    ]
    assert frame["event_id"].tolist() == ["a", "b"]
    assert frame.iloc[1]["metadata"] == {"k": 2}


def test_pattern_event_to_study_record_from_mapping_includes_optional_metadata() -> None:
    event = {
        "event_id": "map-1",
        "pattern_type": "ORDER_BLOCK",
        "direction": "BULLISH",
        "pattern_status": "VALID",
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "timestamp": "2024-01-01T00:00:00Z",
        "start_index": 1,
        "end_index": 5,
        "pattern_score": 0.9,
        "displacement_confirmed": False,
        "extra_context": "context",
    }

    record = pattern_event_to_study_record(event)

    assert record.pattern_score == 0.9
    assert record.displacement_confirmed is False
    assert record.metadata["extra_context"] == "context"
