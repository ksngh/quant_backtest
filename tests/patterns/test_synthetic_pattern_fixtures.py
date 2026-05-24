from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.patterns.entry_simulation import (
    PatternEntryStatus,
    create_entry_plan_from_event,
    simulate_pattern_entry,
)
from tests.fixtures.synthetic_patterns import (
    STANDARD_COLUMNS,
    SyntheticPatternFixture,
    all_pattern_fixtures,
)


@pytest.mark.parametrize("fixture", all_pattern_fixtures(), ids=lambda item: f"{item.pattern_type}-{item.direction}")
def test_fixture_builders_produce_sorted_standard_candles(fixture: SyntheticPatternFixture) -> None:
    for candles in _all_candle_frames(fixture):
        assert tuple(candles.columns) == STANDARD_COLUMNS
        assert candles["timestamp"].is_monotonic_increasing
        assert candles["timestamp"].is_unique
        assert (candles["low"] <= candles["open"]).all()
        assert (candles["low"] <= candles["close"]).all()
        assert (candles["high"] >= candles["open"]).all()
        assert (candles["high"] >= candles["close"]).all()
        assert (candles["volume"] >= 0).all()


@pytest.mark.parametrize("fixture", all_pattern_fixtures(), ids=lambda item: f"{item.pattern_type}-{item.direction}")
def test_valid_and_invalid_fixture_detection_cases(fixture: SyntheticPatternFixture) -> None:
    events = fixture.detect_all(
        fixture.valid_candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=fixture.config,
    )
    assert events, f"{fixture.pattern_type} {fixture.direction} fixture should detect at least one event"
    assert events[0].direction == fixture.direction

    invalid_events = fixture.detect_all(
        fixture.invalid_candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=fixture.config,
    )
    assert invalid_events == []

    if fixture.unsupported_inverse_candles is not None:
        inverse_events = fixture.detect_all(
            fixture.unsupported_inverse_candles,
            symbol="BTCUSDT",
            timeframe="1m",
            config=fixture.config,
        )
        assert inverse_events == []


@pytest.mark.parametrize("fixture", all_pattern_fixtures(), ids=lambda item: f"{item.pattern_type}-{item.direction}")
def test_fixture_at_index_detection_matches_rolling_prefix(fixture: SyntheticPatternFixture) -> None:
    prefix_events = fixture.detect_all(
        fixture.valid_candles.iloc[: fixture.current_index + 1],
        symbol="BTCUSDT",
        timeframe="1m",
        config=fixture.config,
    )
    expected = [event for event in prefix_events if event.end_index == fixture.current_index]
    actual = fixture.detect_at_index(
        fixture.valid_candles,
        fixture.current_index,
        symbol="BTCUSDT",
        timeframe="1m",
        config=fixture.config,
    )
    assert [event.event_id for event in actual] == [event.event_id for event in expected]


@pytest.mark.parametrize("fixture", all_pattern_fixtures(), ids=lambda item: f"{item.pattern_type}-{item.direction}")
def test_fixture_entry_cases_cover_market_limit_fill_and_no_fill(fixture: SyntheticPatternFixture) -> None:
    event = fixture.detect_all(
        fixture.valid_candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=fixture.config,
    )[0]
    confirmation = fixture.valid_candles.iloc[fixture.current_index]
    entry_reference = float(event.entry_reference)

    outcomes = {}
    for case in fixture.entry_cases:
        plan = create_entry_plan_from_event(
            event,
            case.mode,
            fixture.position_side,
            max_wait_bars=case.max_wait_bars,
        )
        future = _future_touching(entry_reference) if case.should_fill else _future_missing(entry_reference)
        result = simulate_pattern_entry(plan, confirmation, future)
        outcomes[case.name] = result.status

    assert outcomes["market_fill"] == PatternEntryStatus.FILLED
    assert outcomes["limit_fill"] == PatternEntryStatus.FILLED
    assert outcomes["limit_no_fill"] == PatternEntryStatus.NOT_FILLED


def test_fixture_exit_case_matrix_covers_required_outcomes() -> None:
    required = {"stop_first", "target_first", "ambiguous", "soft_invalidation", "time_stop"}
    for fixture in all_pattern_fixtures():
        assert required.issubset({case.name for case in fixture.exit_cases})


def test_fixture_direction_coverage_matches_current_pattern_support() -> None:
    directions_by_pattern: dict[str, set[str]] = {}
    for fixture in all_pattern_fixtures():
        directions_by_pattern.setdefault(fixture.pattern_type, set()).add(fixture.direction)

    assert {"BULLISH", "BEARISH"}.issubset(directions_by_pattern["FAIR_VALUE_GAP"])
    assert {"BULLISH", "BEARISH"}.issubset(directions_by_pattern["ORDER_BLOCK"])
    assert {"BULLISH", "BEARISH"}.issubset(directions_by_pattern["TRENDLINE_BREAK"])
    assert {"BULLISH", "BEARISH"}.issubset(directions_by_pattern["DIAMOND_PATTERN"])
    assert directions_by_pattern["CUP_AND_HANDLE"] == {"BULLISH"}
    assert directions_by_pattern["ADAM_AND_EVE"] == {"BULLISH"}


def _all_candle_frames(fixture: SyntheticPatternFixture) -> list[pd.DataFrame]:
    frames = [fixture.valid_candles, fixture.invalid_candles]
    if fixture.unsupported_inverse_candles is not None:
        frames.append(fixture.unsupported_inverse_candles)
    return frames


def _future_touching(price: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-05-16T01:00:00Z",
                "open": price,
                "high": price + 0.25,
                "low": price - 0.25,
                "close": price,
            }
        ]
    )


def _future_missing(price: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-05-16T01:00:00Z",
                "open": price + 2.0,
                "high": price + 3.0,
                "low": price + 1.5,
                "close": price + 2.5,
            }
        ]
    )
