from types import SimpleNamespace

import pandas as pd
import pytest

from quant_bitcoin.patterns.entry_simulation import (
    PatternEntryConfig,
    PatternEntryMode,
    PatternEntrySimulationResult,
    PatternEntryStatus,
    create_entry_plan_from_event,
    simulate_pattern_entry,
)


def _confirmation() -> dict:
    return {"timestamp": "2026-05-20T00:00:00Z", "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0}


def _future(rows: list[dict]) -> pd.DataFrame:
    candles = []
    for index, row in enumerate(rows):
        candle = {"timestamp": f"2026-05-20T00:{index+1:02d}:00Z", "open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0}
        candle.update(row)
        candles.append(candle)
    return pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close"])


def _event(**overrides):
    base = {
        "event_id": "evt-1",
        "pattern_type": "FAIR_VALUE_GAP",
        "entry_reference": 101.5,
        "zone_mid": 101.25,
        "zone_low": 100.5,
        "zone_high": 102.0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_market_on_confirmation_close_fills_at_confirmation_close() -> None:
    plan = create_entry_plan_from_event(_event(), PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, "LONG")

    result = simulate_pattern_entry(plan, _confirmation(), _future([]))

    assert result.status == PatternEntryStatus.FILLED
    assert result.fill_price == pytest.approx(101.0)
    assert result.bars_waited == 0


def test_market_on_next_open_fills_at_next_open() -> None:
    plan = create_entry_plan_from_event(_event(), PatternEntryMode.MARKET_ON_NEXT_OPEN, "LONG")

    result = simulate_pattern_entry(plan, _confirmation(), _future([{"open": 99.5}]))

    assert result.status == PatternEntryStatus.FILLED
    assert result.fill_price == pytest.approx(99.5)
    assert result.bars_waited == 1


def test_limit_entry_reference_fills_when_touched() -> None:
    plan = create_entry_plan_from_event(_event(entry_reference=100.25), PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE, "LONG")

    result = simulate_pattern_entry(plan, _confirmation(), _future([{"low": 100.0, "high": 100.5}]))

    assert result.status == PatternEntryStatus.FILLED
    assert result.fill_price == pytest.approx(100.25)


def test_limit_midpoint_and_boundary_modes() -> None:
    midpoint_plan = create_entry_plan_from_event(_event(zone_mid=100.9), PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT, "LONG")
    boundary_plan = create_entry_plan_from_event(_event(zone_low=100.4), PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY, "LONG")

    midpoint_result = simulate_pattern_entry(midpoint_plan, _confirmation(), _future([{"low": 100.8, "high": 101.0}]))
    boundary_result = simulate_pattern_entry(boundary_plan, _confirmation(), _future([{"low": 100.4, "high": 100.7}]))

    assert midpoint_result.fill_price == pytest.approx(100.9)
    assert boundary_result.fill_price == pytest.approx(100.4)


def test_limit_custom_price_and_max_wait_bars_not_filled() -> None:
    event = _event()
    plan = create_entry_plan_from_event(event, PatternEntryMode.LIMIT_AT_CUSTOM_PRICE, "LONG", custom_price=99.0, max_wait_bars=2)

    result = simulate_pattern_entry(
        plan,
        _confirmation(),
        _future([
            {"low": 100.0, "high": 101.0},
            {"low": 100.1, "high": 101.1},
            {"low": 98.9, "high": 99.1},
        ]),
    )

    assert result.status == PatternEntryStatus.NOT_FILLED
    assert result.bars_waited == 2


def test_cancelled_status_on_expiry_when_configured() -> None:
    plan = create_entry_plan_from_event(_event(entry_reference=90.0), PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE, "LONG")
    cancelled_plan = plan.__class__(
        mode=plan.mode,
        direction=plan.direction,
        limit_price=plan.limit_price,
        config=PatternEntryConfig(max_wait_bars=1, expire_status=PatternEntryStatus.CANCELLED),
        event_id=plan.event_id,
        pattern_type=plan.pattern_type,
        metadata=plan.metadata,
    )

    result = simulate_pattern_entry(cancelled_plan, _confirmation(), _future([{"low": 100.0, "high": 101.0}]))

    assert result.status == PatternEntryStatus.CANCELLED


def test_missing_columns_raise_clear_error() -> None:
    plan = create_entry_plan_from_event(_event(), PatternEntryMode.MARKET_ON_NEXT_OPEN, "LONG")

    with pytest.raises(ValueError, match="missing required future_candles columns"):
        simulate_pattern_entry(plan, _confirmation(), pd.DataFrame([{"timestamp": "x", "high": 1, "low": 1, "close": 1}]))


def test_unsorted_future_candles_raise_error() -> None:
    plan = create_entry_plan_from_event(_event(), PatternEntryMode.MARKET_ON_NEXT_OPEN, "LONG")
    rows = _future([{}, {}])
    unsorted_rows = rows.iloc[::-1].reset_index(drop=True)

    with pytest.raises(ValueError, match="sorted ascending"):
        simulate_pattern_entry(plan, _confirmation(), unsorted_rows)


def test_missing_event_fields_return_invalid_result() -> None:
    plan = create_entry_plan_from_event(_event(zone_mid=None), PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT, "LONG")

    result = simulate_pattern_entry(plan, _confirmation(), _future([{}]))

    assert isinstance(result, PatternEntrySimulationResult)
    assert result.status == PatternEntryStatus.INVALID
    assert "zone_mid" in str(result.reason)


def test_simulation_does_not_mutate_input_data() -> None:
    confirmation = _confirmation()
    future = _future([{}])
    confirmation_original = dict(confirmation)
    future_original = future.copy(deep=True)

    plan = create_entry_plan_from_event(_event(), PatternEntryMode.MARKET_ON_NEXT_OPEN, "LONG")
    simulate_pattern_entry(plan, confirmation, future)

    assert confirmation == confirmation_original
    pd.testing.assert_frame_equal(future, future_original)
