from datetime import datetime, timezone
import inspect
from types import SimpleNamespace

from quant_bitcoin.backtesting import t282_task281_locked_validation as t282


def test_task282_validation_windows_are_deterministic_and_bounded():
    latest = datetime(2026, 5, 28, 8, 26, tzinfo=timezone.utc)
    first = t282.build_validation_windows(latest)
    second = t282.build_validation_windows(latest)

    assert first == second
    assert [window.window_id for window in first] == [
        "full_0420_latest",
        "pre_owner_0420_0519",
        "owner_replay_0520_latest",
        "w1_0420_0426",
        "w2_0427_0503",
        "w3_0504_0510",
        "w4_0511_0517",
        "w5_0518_0524",
        "w6_0525_latest",
        "full_0420_latest_drop_first_day",
        "full_0420_latest_drop_last_day",
        "owner_0520_latest_drop_last_12h",
        "owner_0520_latest_drop_last_24h",
    ]
    assert all(window.end_time >= window.start_time for window in first)


def test_task282_locked_candidate_resolves_only_task281_run892_variant():
    candidate = t282.locked_candidate()

    assert candidate.variant_id == t282.LOCKED_VARIANT_ID
    assert candidate.params["core_fraction"] == 1.0
    assert candidate.params["scout_fraction"] == 0.02
    assert candidate.params["preempt_scout_on_core"] is True
    assert candidate.params["same_candle_core_after_preempt"] is True


def test_task282_cost_audit_detects_cost_formula_mismatch():
    good = _trade(
        gross_notional=10_000.0,
        fee_bps=10.0,
        spread_bps=3.0,
        slippage_bps=5.0,
        fee_cost=10.0,
        spread_cost=3.0,
        slippage_cost=5.0,
        total_cost=18.0,
    )
    bad = _trade(
        gross_notional=10_000.0,
        fee_bps=10.0,
        spread_bps=3.0,
        slippage_bps=5.0,
        fee_cost=9.0,
        spread_cost=3.0,
        slippage_cost=5.0,
        total_cost=17.0,
    )

    good_audit = t282.audit_persisted_trade_costs([good])
    bad_audit = t282.audit_persisted_trade_costs([bad])

    assert good_audit.mismatch_count == 0
    assert good_audit.total_cost == 18.0
    assert good_audit.effective_total_cost_bps == 18.0
    assert bad_audit.mismatch_count == 1
    assert bad_audit.max_abs_mismatch == 1.0


def test_task282_classification_is_deterministic_for_passing_records():
    availability = t282.DataAvailability(
        requested_start_time=t282._dt("2026-04-20T00:00:00Z"),
        available_start_time=t282._dt("2026-05-10T00:00:00Z"),
        available_end_time=t282._dt("2026-05-28T08:26:00Z"),
        candle_count=23_027,
    )
    records = [
        _record("full_0420_latest", total_return=0.04, trips=80, top1=0.20, top3=0.45, cost_ratio=0.40),
        _record("pre_owner_0420_0519", total_return=0.01, trips=30, top1=0.20, top3=0.45, cost_ratio=0.40),
        _record("owner_replay_0520_latest", total_return=t282.SOURCE_RUN_RETURN, trips=t282.SOURCE_RUN_TRIPS, top1=0.20, top3=0.45, cost_ratio=0.40),
        _record("w4_0511_0517", group="weekly", total_return=0.01, trips=12),
        _record("w5_0518_0524", group="weekly", total_return=-0.01, trips=14),
        _record("w6_0525_latest", group="weekly", total_return=0.01, trips=11),
        _record("full_0420_latest", cost="high_slippage_stress", total_return=0.01, trips=80),
        _record("pre_owner_0420_0519", cost="high_slippage_stress", total_return=-0.01, trips=30),
    ]

    first = t282.classify_validation(records, availability)
    second = t282.classify_validation(records, availability)

    assert first == second
    assert first.status == "OOS_SUPPORTED_RESEARCH_ONLY"
    assert all(ok for _, _, _, ok in first.gate_results)


def test_task282_module_does_not_import_execution_clients():
    source = inspect.getsource(t282)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _trade(
    *,
    gross_notional: float,
    fee_bps: float,
    spread_bps: float,
    slippage_bps: float,
    fee_cost: float,
    spread_cost: float,
    slippage_cost: float,
    total_cost: float,
) -> SimpleNamespace:
    return SimpleNamespace(
        price=100.0,
        quantity=gross_notional / 100.0,
        metadata={
            "fee_cost": fee_cost,
            "spread_cost": spread_cost,
            "slippage_cost": slippage_cost,
            "total_cost": total_cost,
            "cost_breakdown": {
                "gross_notional": gross_notional,
                "fee_bps": fee_bps,
                "spread_bps": spread_bps,
                "effective_slippage_bps": slippage_bps,
            },
        },
    )


def _record(
    window_id: str,
    *,
    group: str = "primary",
    cost: str = "conservative_crypto_1m",
    total_return: float,
    trips: int,
    top1: float = 0.20,
    top3: float = 0.45,
    cost_ratio: float = 0.40,
) -> t282.ValidationRecord:
    return t282.ValidationRecord(
        window_id=window_id,
        validation_group=group,
        cost_profile=cost,
        requested_start_time=t282._dt("2026-04-20T00:00:00Z"),
        requested_end_time=t282._dt("2026-05-28T08:26:00Z"),
        run_id=1,
        status="COMPLETED_VALIDATION_RESEARCH_ONLY",
        total_return=total_return,
        completed_round_trips=trips,
        largest_winner_contribution=top1,
        top_three_winner_contribution=top3,
        cost_to_gross_pnl_ratio=cost_ratio,
        readback_ok=True,
    )
