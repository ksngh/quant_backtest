from __future__ import annotations

import inspect
from types import SimpleNamespace

import pandas as pd

from quant_bitcoin.backtesting import t283_principle_first_microstructure_strategy as t283
from quant_bitcoin.strategies.actions import StrategyActionType


def test_task283_candidate_grid_is_principle_first_and_bounded() -> None:
    first = t283.build_candidates()
    second = t283.build_candidates()

    assert first == second
    assert len(first) == 7
    assert [candidate.family for candidate in first[:3]] == [
        "LIQUIDITY_SWEEP_REVERSAL_V2",
        "VOLATILITY_COMPRESSION_BREAKOUT",
        "MTF_TREND_PULLBACK_CONTINUATION",
    ]
    assert all(candidate.variant_id.startswith(("T283_B1_", "T283_B2_")) for candidate in first)
    assert all(candidate.thesis for candidate in first)


def test_task283_factor_snapshots_do_not_change_when_future_candles_mutate() -> None:
    candles = _trend_candles(periods=700)
    base = t283.build_factor_snapshots(candles)

    mutated = candles.copy(deep=True)
    mutated.loc[520:, "close"] = mutated.loc[520:, "close"] * 1.25
    mutated.loc[520:, "high"] = mutated.loc[520:, "high"] * 1.25
    mutated.loc[520:, "low"] = mutated.loc[520:, "low"] * 1.25
    changed = t283.build_factor_snapshots(mutated)

    columns = [
        "return_bps_prior_60",
        "atr_bps",
        "range_high_prior_60",
        "range_low_prior_60",
        "volume_ratio_20",
        "mtf_15m_trend_bps",
        "mtf_1h_trend_bps",
    ]
    pd.testing.assert_series_equal(base.loc[480, columns], changed.loc[480, columns], check_names=False)


def test_task283_stop_first_when_stop_and_target_same_candle() -> None:
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-20T00:00:00Z", periods=3, freq="min"),
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 103.0, 100.0],
            "low": [100.0, 97.0, 100.0],
            "close": [100.0, 101.0, 100.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )

    exit_index, exit_price, reason = t283.resolve_intrabar_exit(
        candles,
        entry_index=1,
        side="LONG",
        entry_price=100.0,
        stop_price=98.0,
        target_price=102.0,
        max_hold_bars=2,
    )

    assert exit_index == 1
    assert exit_price == 98.0
    assert reason == "TASK283_CONSERVATIVE_STOP_FIRST"


def test_task283_cost_audit_detects_formula_mismatch() -> None:
    good = _trade(10_000.0, fee=10.0, spread=3.0, slippage=5.0, total=18.0)
    bad = _trade(10_000.0, fee=9.0, spread=3.0, slippage=5.0, total=17.0)

    assert t283.audit_persisted_trade_costs([good]).mismatch_count == 0
    bad_audit = t283.audit_persisted_trade_costs([bad])

    assert bad_audit.mismatch_count == 1
    assert bad_audit.max_abs_mismatch == 1.0


def test_task283_priority_ensemble_separates_signal_and_execution_candles() -> None:
    candidate = [
        candidate
        for candidate in t283.build_candidates()
        if candidate.variant_id == "T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002"
    ][0]
    actions, metadata = t283.generate_actions(_ensemble_fixture(), candidate)

    entries = [action for action in actions if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}]

    assert metadata.generated_entries >= 1
    assert entries
    assert entries[0].metadata["signal_execution_separated"] is True
    assert entries[0].metadata["execution_timestamp"] != entries[0].metadata["signal_timestamp"]
    assert entries[0].metadata["entry_execution_model"] == "next_candle_open"
    assert entries[0].metadata["task283_factor_snapshot"]["schema_version"] == "task283_factor_snapshot_v1"


def test_task283_shifted_exit_variant_records_exit_condition_metadata() -> None:
    candidate = [
        candidate
        for candidate in t283.build_candidates()
        if candidate.variant_id == "T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002"
    ][0]
    actions, metadata = t283.generate_actions(_ensemble_fixture(), candidate)

    exits = [action for action in actions if action.action_type in {StrategyActionType.EXIT_LONG, StrategyActionType.EXIT_SHORT}]

    assert metadata.generated_entries >= 1
    assert exits
    assert exits[0].metadata["task283_cost_edge_gate"]["exit_execution_model"] == "next_candle_open_after_exit_condition"
    assert exits[0].metadata["intrabar_ambiguity_policy"] == "stop_first_when_stop_and_target_hit_same_candle"


def test_task283_module_does_not_import_execution_clients() -> None:
    source = inspect.getsource(t283)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _trade(gross_notional: float, *, fee: float, spread: float, slippage: float, total: float) -> SimpleNamespace:
    return SimpleNamespace(
        price=100.0,
        quantity=gross_notional / 100.0,
        metadata={
            "fee_cost": fee,
            "spread_cost": spread,
            "slippage_cost": slippage,
            "total_cost": total,
            "cost_breakdown": {
                "gross_notional": gross_notional,
                "fee_bps": 10.0,
                "spread_bps": 3.0,
                "effective_slippage_bps": 5.0,
            },
        },
    )


def _trend_candles(*, periods: int) -> pd.DataFrame:
    timestamps = pd.date_range("2026-05-20T00:00:00Z", periods=periods, freq="min")
    close = [1000.0 + index * 0.05 for index in range(periods)]
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [value - 0.02 for value in close],
            "high": [value + 0.10 for value in close],
            "low": [value - 0.10 for value in close],
            "close": close,
            "volume": [10.0 + (index % 7) for index in range(periods)],
        }
    )


def _ensemble_fixture() -> pd.DataFrame:
    periods = 1_600
    timestamps = pd.date_range("2026-05-20T00:00:00Z", periods=periods, freq="min")
    close = [1000.0 - (index * 0.20) for index in range(periods)]
    open_ = [value + 0.05 for value in close]
    high = [value + 0.10 for value in close]
    low = [value - 0.10 for value in close]

    prior_high = max(high[940:1000])
    high[1000] = prior_high + 5.0
    close[1000] = prior_high - 2.0
    open_[1000] = prior_high + 1.0
    low[1000] = close[1000] - 1.0

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": [20.0] * periods,
        }
    )
