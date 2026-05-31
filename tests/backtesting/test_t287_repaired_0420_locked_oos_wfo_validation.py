from __future__ import annotations

import inspect

from quant_bitcoin.backtesting import t284_task283_multi_axis_robustness_revalidation as t284
from quant_bitcoin.backtesting import t285_regime_robust_multi_window_strategy_repair as t285
from quant_bitcoin.backtesting import t287_repaired_0420_locked_oos_wfo_validation as t287


def test_task287_registry_contains_locked_candidates_without_retune() -> None:
    candidates = t287.candidate_registry()

    assert [candidate.candidate_id for candidate in candidates] == [
        "T285_R3_CORE_SHORT_ONLY_B2",
        "T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002",
        "T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002",
    ]
    assert candidates[0].role == "primary_locked_candidate"
    assert all(candidate.replay_kind in {"task285_plan", "task281_candidate"} for candidate in candidates)


def test_task287_windows_cover_repaired_0420_and_required_diagnostics() -> None:
    latest = t285._dt("2026-05-28T08:26:00Z")
    windows = t287.build_validation_windows(latest)
    by_id = {window.window_id: window for window in windows}

    assert by_id["full_0420_latest"].start_time == t287.REQUESTED_START
    assert by_id["full_0420_latest"].end_time == latest
    assert by_id["pre_owner_0420_0519"].end_time == t285._dt("2026-05-19T23:59:00Z")
    assert by_id["owner_replay_0520_latest"].decision_role == "owner_replay"
    assert [window.window_id for window in windows if window.decision_role == "independent"] == [
        "w1_0420_0426",
        "w2_0427_0503",
        "w3_0504_0510",
        "w4_0511_0517",
        "w5_0518_0524",
        "w6_0525_latest",
    ]
    assert len([window for window in windows if window.decision_role == "endpoint"]) == 6


def test_task287_run_specs_include_base_endpoint_and_cost_stress() -> None:
    latest = t285._dt("2026-05-28T08:26:00Z")
    specs = t287.build_run_specs(latest=latest)

    assert len(specs) == 75
    assert {spec.cost_profile_key for spec in specs if spec.run_group == "cost_stress"} == {
        "cost_2x",
        "cost_3x",
        "high_slippage_stress",
    }
    assert all(spec.diagnostic_only for spec in specs if spec.run_group == "endpoint_diagnostic")
    assert any(
        spec.candidate.candidate_id == "T285_R3_CORE_SHORT_ONLY_B2"
        and spec.window.window_id == "full_0420_latest"
        and spec.cost_profile_key == "conservative_crypto_1m"
        for spec in specs
    )


def test_task287_coverage_guard_requires_exact_continuity(monkeypatch) -> None:
    monkeypatch.setattr(t287, "duplicate_open_time_count", lambda _database_url: 0)
    coverage = t285.DataCoverage(
        requested_start_time=t287.REQUESTED_START,
        available_start_time=t287.REQUESTED_START,
        available_end_time=t285._dt("2026-04-20T00:02:00Z"),
        candle_count=3,
        gaps=(),
        complete_ranges=(),
        april20_forward_complete=True,
    )

    guard = t287.coverage_guard("postgresql://unused", coverage)

    assert guard.ok is True
    assert guard.expected_candle_count == 3
    assert guard.failed_reasons == ()


def test_task287_classifier_can_pass_only_when_all_locked_gates_pass() -> None:
    candidate = t287.candidate_registry()[0]
    records = [
        _record(candidate, "full_0420_latest", "full", "conservative_crypto_1m", 0.05, 60, gross=70_000, net=50_000, total_cost=14_000),
        _record(candidate, "pre_owner_0420_0519", "pre_owner", "conservative_crypto_1m", 0.01, 25, gross=20_000, net=10_000, total_cost=4_000),
        _record(candidate, "full_0420_latest", "full", "cost_2x", 0.02, 60, gross=60_000, net=20_000, total_cost=30_000),
        _record(candidate, "full_0420_latest", "full", "cost_3x", 0.01, 60, gross=60_000, net=10_000, total_cost=42_000),
        _record(candidate, "full_0420_latest", "full", "high_slippage_stress", 0.0, 60, gross=60_000, net=0, total_cost=50_000),
    ]
    for index in range(6):
        records.append(
            _record(
                candidate,
                f"w{index + 1}",
                "independent",
                "conservative_crypto_1m",
                0.007,
                12,
                gross=10_000,
                net=7_000,
                total_cost=3_000,
            )
        )

    guard = t287.CoverageGuard(True, 0, 10, ())
    coverage = t285.DataCoverage(t287.REQUESTED_START, t287.REQUESTED_START, t285._dt("2026-04-20T00:09:00Z"), 10, (), (), True)
    gate = t287.classify_records(records, coverage, guard)
    primary = gate.decisions[0]

    assert gate.status == "LOCKED_PRIMARY_SUPPORTED_RESEARCH_ONLY"
    assert primary.status == "OOS_SUPPORTED_RESEARCH_ONLY"
    assert primary.failed_gates == ()


def test_task287_classifier_rejects_low_trade_count_even_if_return_is_positive() -> None:
    candidate = t287.candidate_registry()[0]
    records = [
        _record(candidate, "full_0420_latest", "full", "conservative_crypto_1m", 0.05, 1, gross=70_000, net=50_000, total_cost=14_000),
    ]
    guard = t287.CoverageGuard(True, 0, 10, ())
    coverage = t285.DataCoverage(t287.REQUESTED_START, t287.REQUESTED_START, t285._dt("2026-04-20T00:09:00Z"), 10, (), (), True)

    gate = t287.classify_records(records, coverage, guard)
    primary = gate.decisions[0]

    assert gate.status == "LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY"
    assert "Full 0420 latest round trips" in primary.failed_gates
    assert primary.classification == "SAMPLE_SIZE_INSUFFICIENT"


def test_task287_module_does_not_import_execution_clients() -> None:
    source = inspect.getsource(t287)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _record(
    candidate: t287.LockedCandidate,
    window_id: str,
    decision_role: str,
    cost_profile_key: str,
    total_return: float,
    trips: int,
    *,
    gross: float,
    net: float,
    total_cost: float,
) -> t287.RunRecord:
    window = t285.WindowDefinition(
        window_id,
        "test",
        t287.REQUESTED_START,
        t287.REQUESTED_START,
        decision_role,
    )
    return t287.RunRecord(
        spec=t287.RunSpec(candidate, window, cost_profile_key, "test", "test"),
        run_id=1,
        status="COMPLETED_RESEARCH_ONLY",
        total_return=total_return,
        completed_round_trips=trips,
        gross_pnl=gross,
        net_pnl=net,
        total_cost=total_cost,
        total_fee_cost=total_cost / 3.0,
        total_spread_cost=total_cost / 3.0,
        total_slippage_cost=total_cost / 3.0,
        cost_to_gross_pnl_ratio=None if gross <= 0 else total_cost / gross,
        cost_formula_mismatch_count=0,
        summary_cost_mismatch_count=0,
        readback_ok=True,
        candle_continuity_ok=True,
        candle_gap_count=0,
        outlier_audit=t284.OutlierAudit(
            event_count=trips,
            net_pnl=net,
            top_three_winner_contribution=0.30,
            return_without_top_three_winners=0.02,
        ),
        event_net_pnls=(net / max(1, trips),) * max(1, trips),
    )
