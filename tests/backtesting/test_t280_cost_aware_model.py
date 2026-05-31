from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES
from quant_bitcoin.backtesting.t280_cost_aware_model import (
    build_candidates,
    cost_edge_decision,
)


def test_task280_cost_edge_gate_rejects_reward_below_cost_budget():
    decision = cost_edge_decision(
        side="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=100.5,
        volatility_bps=10.0,
        cost_config=COST_PROFILES["conservative_crypto_1m"].config,
    )

    assert decision["blocked"] is True
    assert decision["block_reason"] == "TASK280_COST_EDGE_GATE_REJECTED"
    assert decision["estimated_round_trip_cost_bps"] > 0.0
    assert decision["reward_cost_multiple"] < decision["min_reward_cost_multiple"]


def test_task280_cost_edge_gate_accepts_wide_net_reward():
    decision = cost_edge_decision(
        side="SHORT",
        entry_price=100.0,
        stop_price=101.0,
        target_price=96.0,
        volatility_bps=10.0,
        cost_config=COST_PROFILES["conservative_crypto_1m"].config,
    )

    assert decision["blocked"] is False
    assert decision["block_reason"] is None
    assert decision["estimated_round_trip_cost_bps"] > 0.0
    assert decision["net_reward_bps"] >= decision["min_net_reward_bps"]


def test_task280_later_batches_are_predeclared_and_short_only_where_expected():
    batch9 = build_candidates("batch9")

    assert batch9
    assert all(candidate.variant_id.startswith("T280_B9_") for candidate in batch9)
    assert {candidate.params["direction_mode"] for candidate in batch9} == {"short_only"}
    assert {candidate.params["track"] for candidate in batch9} == {"regime_fixed_target"}
