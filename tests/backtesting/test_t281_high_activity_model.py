import inspect

import pandas as pd

from quant_bitcoin.backtesting import t281_high_activity_model as t281
from quant_bitcoin.strategies.actions import StrategyActionType


def test_task281_candidate_grid_is_deterministic_and_bounded():
    first = t281.build_candidates("batch1")
    second = t281.build_candidates("batch1")

    assert first == second
    assert len(first) == 5
    assert {candidate.family for candidate in first} >= {
        "ACTIVITY_TREND_SCOUT",
        "LIQUIDITY_RANGE_FADE_CORE",
        "PRIORITY_CORE_ACTIVITY_SCOUT",
    }
    assert all(candidate.variant_id.startswith("T281_B1_") for candidate in first)


def test_task281_selected_candidate_records_sizing_and_cost_metadata():
    selected = [
        candidate
        for candidate in t281.build_candidates()
        if candidate.variant_id == "T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002"
    ][0]

    assert selected.params["core_fraction"] == 1.0
    assert selected.params["scout_fraction"] == 0.02
    assert selected.params["preempt_scout_on_core"] is True
    assert selected.params["same_candle_core_after_preempt"] is True


def test_task281_preempt_exit_allows_same_candle_core_entry():
    candles = _synthetic_preempt_candles()
    candidate = t281.CandidateSpec(
        variant_id="T281_TEST_PREEMPT",
        family="PRIORITY_CORE_ACTIVITY_SCOUT",
        description="test",
        params={
            "core_enabled": True,
            "core_fraction": 1.0,
            "core_target_bps": 260.0,
            "core_stop_bps": 130.0,
            "core_hold_bars": 480,
            "core_skip_incomplete_hold": True,
            "core_skip_sunday_hours_utc": [],
            "scout_enabled": True,
            "scout_fraction": 0.02,
            "scout_hold_bars": 120,
            "scout_target_bps": 1000.0,
            "scout_stop_bps": 1000.0,
            "preempt_scout_on_core": True,
            "same_candle_core_after_preempt": True,
        },
    )

    actions, metadata = t281.generate_actions(candles, candidate)
    preempt_index = next(
        index
        for index, action in enumerate(actions)
        if action.reason == "T281_SCOUT_PREEMPT_CORE_SIGNAL"
    )
    preempt_exit = actions[preempt_index]
    same_candle_core_entry = actions[preempt_index + 1]

    assert metadata["completed_candle_only"] is True
    assert metadata["preempt_exits"] >= 1
    assert preempt_exit.action_type == StrategyActionType.EXIT_SHORT
    assert same_candle_core_entry.action_type == StrategyActionType.ENTER_SHORT
    assert same_candle_core_entry.timestamp == preempt_exit.timestamp
    assert preempt_exit.metadata["task281_layer"] == "scout"
    assert same_candle_core_entry.metadata["task281_layer"] == "core"


def test_task281_module_does_not_import_execution_clients():
    source = inspect.getsource(t281)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _synthetic_preempt_candles() -> pd.DataFrame:
    periods = 1_600
    timestamps = pd.date_range("2026-05-20T00:00:00Z", periods=periods, freq="min")
    close = [100.0 - (index * 0.006) for index in range(periods)]
    open_ = [value + 0.01 for value in close]
    high = [value + 0.03 for value in close]
    low = [value - 0.03 for value in close]

    prior_high = max(high[940:1000])
    high[1000] = prior_high + 2.0
    close[1000] = prior_high - 0.5
    open_[1000] = prior_high + 0.2
    low[1000] = close[1000] - 0.5

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": [1.0] * periods,
        }
    )
