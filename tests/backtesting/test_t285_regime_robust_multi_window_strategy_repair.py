from __future__ import annotations

import inspect
from types import SimpleNamespace

import pandas as pd

from quant_bitcoin.backtesting import t285_regime_robust_multi_window_strategy_repair as t285
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def test_task285_window_parser_supports_multiple_formats() -> None:
    pipe = t285.parse_window_definition("w1|2026-05-20T00:00:00Z|2026-05-21T00:00:00Z")
    comma = t285.parse_window_definition("w2,2026-05-20T00:00:00Z,2026-05-21T00:00:00Z")
    colon = t285.parse_window_definition("w3:2026-05-20T00:00:00Z:2026-05-21T00:00:00Z")

    assert pipe.window_id == "w1"
    assert comma.window_id == "w2"
    assert colon.window_id == "w3"
    assert pipe.decision_role == "independent"


def test_task285_gap_detection_and_complete_split() -> None:
    candles = pd.DataFrame(
        {
            "timestamp": [
                "2026-05-20T00:00:00Z",
                "2026-05-20T00:01:00Z",
                "2026-05-20T00:04:00Z",
                "2026-05-20T00:05:00Z",
            ],
            "open": [1.0, 1.0, 1.0, 1.0],
            "high": [1.0, 1.0, 1.0, 1.0],
            "low": [1.0, 1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0, 1.0],
            "volume": [1.0, 1.0, 1.0, 1.0],
        }
    )

    gaps = t285.detect_candle_gaps(candles)
    ranges = t285.split_complete_ranges(candles)

    assert len(gaps) == 1
    assert gaps[0].missing_candles == 2
    assert len(ranges) == 2
    assert [item.candle_count for item in ranges] == [2, 2]


def test_task285_short_only_filter_removes_long_events_and_keeps_metadata() -> None:
    plan = [candidate for candidate in t285.build_candidate_plans() if candidate.repair_mode == "short_only"][0]
    actions = [
        _action("e1", StrategyActionType.ENTER_LONG, "LONG"),
        _action("e1", StrategyActionType.EXIT_LONG, "LONG"),
        _action("e2", StrategyActionType.ENTER_SHORT, "SHORT"),
        _action("e2", StrategyActionType.EXIT_SHORT, "SHORT"),
    ]

    filtered = t285.filter_actions_for_plan(actions, plan)

    assert [action.metadata["event_id"] for action in filtered] == ["e2", "e2"]
    assert all(action.metadata["task285_candidate_id"] == plan.candidate_id for action in filtered)
    assert filtered[0].metadata["task285_explicit_single_side"] == "SHORT"


def test_task285_cost_profiles_include_2x_and_3x_realistic_stress() -> None:
    profiles = t285.cost_profile_map()

    assert profiles["cost_2x"].config.taker_fee_bps == 20.0
    assert profiles["cost_2x"].config.spread_bps == 6.0
    assert profiles["cost_3x"].config.taker_fee_bps == 30.0
    assert profiles["cost_3x"].config.slippage_bps == 15.0


def test_task285_followup_specs_do_not_repeat_primary_matrix() -> None:
    windows = (
        t285.WindowDefinition(
            "independent_a",
            "test",
            t285._dt("2026-05-20T00:00:00Z"),
            t285._dt("2026-05-21T00:00:00Z"),
            "independent",
        ),
        t285.WindowDefinition(
            "owner_diag",
            "test",
            t285._dt("2026-05-20T00:00:00Z"),
            t285._dt("2026-05-22T00:00:00Z"),
            "diagnostic",
        ),
    )

    specs = t285.build_run_specs(
        windows=windows,
        selected_candidate_id="T285_R1_SHORT_ONLY_B2",
        include_stress=True,
        include_primary=False,
    )

    assert {spec.run_group for spec in specs} == {"owner_overlap_diagnostic", "cost_stress"}
    assert all(spec.candidate.candidate_id == "T285_R1_SHORT_ONLY_B2" for spec in specs)


def test_task285_classifier_rejects_overlapping_only_evidence() -> None:
    plan = [candidate for candidate in t285.build_candidate_plans() if candidate.repair_mode == "short_only"][0]
    records = [
        _record(plan, "owner_0520_full", "diagnostic", 0.05, 20),
        _record(plan, "owner_0525_full", "diagnostic", 0.03, 10),
    ]
    coverage = t285.DataCoverage(
        requested_start_time=t285._dt("2026-04-20T00:00:00Z"),
        available_start_time=t285._dt("2026-05-20T00:00:00Z"),
        available_end_time=t285._dt("2026-05-28T00:00:00Z"),
        candle_count=1_000,
        gaps=(),
        complete_ranges=(),
        april20_forward_complete=False,
    )

    gate = t285.classify_records(records, coverage)

    assert gate.status == "BLOCKED"
    assert gate.selected_candidate_id is None
    assert "Repair candidates" in gate.failed_gates


def test_task285_module_does_not_import_execution_clients() -> None:
    source = inspect.getsource(t285)

    assert "quant_bitcoin.execution" not in source
    assert "binance_spot_testnet" not in source
    assert "ENABLE_LIVE_TRADING" not in source


def _action(event_id: str, action_type: StrategyActionType, side: str) -> StrategyAction:
    return StrategyAction(
        action_type=action_type,
        timestamp=pd.Timestamp("2026-05-20T00:00:00Z"),
        quantity=1.0,
        metadata={
            "event_id": event_id,
            "position_side": side,
            "task283_layer": "core",
            "task283_factor_snapshot": {
                "mtf_15m_trend_bps": -10.0,
                "mtf_1h_trend_bps": -20.0,
                "volume_ratio_20": 1.0,
            },
        },
    )


def _record(
    plan: t285.CandidatePlan,
    window_id: str,
    decision_role: str,
    total_return: float,
    trips: int,
) -> t285.RunRecord:
    window = t285.WindowDefinition(
        window_id,
        "test",
        t285._dt("2026-05-20T00:00:00Z"),
        t285._dt("2026-05-21T00:00:00Z"),
        decision_role,
    )
    return t285.RunRecord(
        spec=t285.RunSpec(plan, window, "conservative_crypto_1m", "test", "test", decision_role != "independent"),
        run_id=1,
        status="COMPLETED_RESEARCH_ONLY",
        total_return=total_return,
        gross_pnl=total_return * t285.STARTING_CASH,
        net_pnl=total_return * t285.STARTING_CASH,
        completed_round_trips=trips,
        side_attribution=(
            SimpleNamespace(bucket="SHORT", net_pnl=total_return * t285.STARTING_CASH, completed_round_trips=trips),
        ),
        event_net_pnls=(total_return * t285.STARTING_CASH,),
    )
