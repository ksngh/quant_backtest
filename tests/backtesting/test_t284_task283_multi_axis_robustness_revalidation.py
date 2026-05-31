from __future__ import annotations

import inspect
from types import SimpleNamespace

import pandas as pd

from quant_bitcoin.backtesting import t284_task283_multi_axis_robustness_revalidation as t284


def test_task284_validation_specs_are_locked_and_cover_required_axes() -> None:
    specs = t284.build_validation_specs(pd.Timestamp("2026-05-28T08:26:00Z").to_pydatetime())
    axes = {spec.validation_axis for spec in specs}
    locked = [spec for spec in specs if not spec.diagnostic_only]

    assert {"owner_replay", "pre_owner", "endpoint_trim", "endpoint_split", "cost_sensitivity"}.issubset(axes)
    assert all(spec.candidate_id == t284.LOCKED_CANDIDATE_ID for spec in locked)
    assert all(spec.action_mode == "locked_b2" for spec in locked)
    assert any(spec.action_mode == "one_candle_delayed_entry" for spec in specs)
    assert any(spec.action_mode == "b1_same_candle_exit" for spec in specs)


def test_task284_cost_profile_stress_keys_are_deterministic() -> None:
    profiles = t284.cost_profile_map()

    assert profiles["fee_2x"].config.taker_fee_bps == 20.0
    assert profiles["slippage_2x"].config.slippage_bps == 10.0
    assert profiles["fee_slippage_2x"].config.taker_fee_bps == 20.0
    assert profiles["fee_slippage_2x"].config.slippage_bps == 10.0
    assert profiles["zero"].config.taker_fee_bps == 0.0


def test_task284_summary_cost_audit_detects_summary_mismatch() -> None:
    audit = SimpleNamespace(
        total_fee_cost=10.0,
        total_spread_cost=3.0,
        total_slippage_cost=5.0,
        total_cost=18.0,
    )

    assert t284.audit_summary_costs(
        {"total_fee_cost": 10.0, "total_spread_cost": 3.0, "total_slippage_cost": 5.0, "total_cost": 18.0},
        audit,
    ).mismatch_count == 0
    mismatch = t284.audit_summary_costs(
        {"total_fee_cost": 10.0, "total_spread_cost": 3.0, "total_slippage_cost": 5.0, "total_cost": 17.0},
        audit,
    )
    assert mismatch.mismatch_count == 1
    assert mismatch.max_abs_mismatch == 1.0


def test_task284_event_bucket_attribution_uses_entry_factor_snapshot() -> None:
    trades = [
        _trade(
            "event-1",
            "ENTER_SHORT",
            side="SHORT",
            cost=2.0,
            snapshot={
                "session_tag": "US",
                "realized_vol_percentile_240": 0.8,
                "mtf_15m_trend_bps": -10.0,
                "mtf_1h_trend_bps": -5.0,
                "volume_ratio_20": 1.2,
            },
        ),
        _trade("event-1", "EXIT_SHORT", side="SHORT", cost=3.0, gross=20.0),
        _trade(
            "event-2",
            "ENTER_LONG",
            side="LONG",
            cost=1.0,
            snapshot={
                "session_tag": "ASIA",
                "realized_vol_percentile_240": 0.2,
                "mtf_15m_trend_bps": -10.0,
                "mtf_1h_trend_bps": -5.0,
                "volume_ratio_20": 0.8,
            },
        ),
        _trade("event-2", "EXIT_LONG", side="LONG", cost=1.0, gross=-10.0),
    ]

    rows = t284.event_trade_rows(trades)
    side = {row.bucket: row for row in t284.bucket_attribution(rows, key="side")}
    sessions = {row.bucket: row for row in t284.bucket_attribution(rows, key="session")}
    regimes = {row.bucket: row for row in t284.bucket_attribution(rows, key="trend_alignment")}

    assert side["SHORT"].net_pnl == 15.0
    assert side["LONG"].net_pnl == -12.0
    assert sessions["US"].completed_round_trips == 1
    assert regimes["trend_ALIGNED"].completed_round_trips == 1
    assert regimes["trend_COUNTER"].completed_round_trips == 1


def test_task284_one_candle_delay_keeps_actions_separated() -> None:
    candidate = t284.candidate_by_id(t284.LOCKED_CANDIDATE_ID)
    actions, metadata = t284.generate_one_candle_delayed_entry_actions(_ensemble_fixture(), candidate)

    entries = [action for action in actions if action.action_type.name.startswith("ENTER")]

    assert metadata.generated_entries >= 1
    assert entries
    assert entries[0].metadata["entry_execution_model"] == "one_candle_delayed_next_open_diagnostic"
    assert entries[0].metadata["task284_execution_diagnostic"] == "one_candle_delayed_entry"
    assert entries[0].metadata["signal_timestamp"] != entries[0].metadata["execution_timestamp"]


def test_task284_module_does_not_import_execution_clients() -> None:
    source = inspect.getsource(t284)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _trade(
    event_id: str,
    action_type: str,
    *,
    side: str,
    cost: float,
    gross: float | None = None,
    snapshot: dict[str, object] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        metadata={
            "event_id": event_id,
            "pattern_event_id": event_id,
            "action_type": action_type,
            "position_side": side,
            "total_cost": cost,
            "gross_pnl": gross,
            "task283_factor_snapshot": snapshot or {},
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
