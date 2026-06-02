from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.quant_backtest_api.services.backtest_results import BacktestResultsService


@dataclass(frozen=True)
class TradeRow:
    id: int
    sequence: int
    candle_open_time: str
    signal: str
    price: float
    quantity: float
    cash_after: float
    position_after: float
    metadata: dict[str, Any] | None


@dataclass(frozen=True)
class RunListRow:
    id: int
    run_key: str
    strategy_config_id: int
    strategy_key: str
    strategy_name: str
    strategy_version: str
    strategy_parameters: dict[str, Any]
    strategy_parameters_hash: str
    candle_source: str
    symbol: str
    interval: str
    actual_start_time: str | None
    actual_end_time: str | None
    candle_count: int
    starting_cash: float
    final_equity: float
    total_return: float
    trade_count: int
    metadata: dict[str, Any] | None
    created_at: str
    completed_at: str | None


def _graph_point(sequence: int, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": sequence,
        "sequence": sequence,
        "candle_open_time": f"2026-02-01T{sequence // 60:02d}:{sequence % 60:02d}:00Z",
        "close_price": 100.0 + sequence,
        "cash": 10_000.0,
        "position": 0.0,
        "equity": 10_000.0 + sequence,
        "trade_id": None,
        "signal": None,
        "metadata": {},
    }
    row.update(overrides)
    return row


def test_serialize_list_item_exposes_configured_starting_cash() -> None:
    service = BacktestResultsService(None)

    row = service._serialize_list_item(
        RunListRow(
            id=7,
            run_key="run-key",
            strategy_config_id=1,
            strategy_key="fair_value_gap",
            strategy_name="FAIR_VALUE_GAP_PATTERN_STRATEGY",
            strategy_version="strategy_engine_v1",
            strategy_parameters={},
            strategy_parameters_hash="hash",
            candle_source="binance_spot",
            symbol="BTCUSDT",
            interval="1m",
            actual_start_time="2026-05-20T00:00:00Z",
            actual_end_time="2026-05-21T00:00:00Z",
            candle_count=1440,
            starting_cash=1_000_000.0,
            final_equity=1_010_000.0,
            total_return=0.01,
            trade_count=4,
            metadata={},
            created_at="2026-05-28T00:00:00Z",
            completed_at="2026-05-28T00:00:01Z",
        )
    )

    assert row["summary"]["starting_cash"] == 1_000_000.0


def test_serialize_trade_flattens_fvg_channel_metadata() -> None:
    service = BacktestResultsService(None)
    geometry = {
        "schema_version": "fvg_parallel_channel_v1",
        "lower_line": {"slope": 1.0, "intercept": 100.0},
        "upper_line": {"slope": 1.0, "intercept": 110.0},
    }

    row = service._serialize_trade(
        TradeRow(
            id=1,
            sequence=1,
            candle_open_time="2026-05-20T00:03:00Z",
            signal="LONG_ENTRY",
            price=104.0,
            quantity=1.0,
            cash_after=9896.0,
            position_after=1.0,
            metadata={
                "channel_mode": "FVG_V2_PARALLEL_CHANNEL",
                "channel_geometry": geometry,
                "channel_candidate_source": "standalone_visible_prefix_scan",
                "channel_scan_source": "rolling_visible_prefix",
                "channel_trend_direction": "UPTREND",
                "channel_direction_rule": "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1",
                "channel_boundary_direction_mode": "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1",
                "entry_boundary": "UPPER",
                "original_channel_entry_side": "SHORT",
                "effective_channel_entry_side": "LONG",
                "stop_boundary": "LOWER",
                "target_boundary": "CHANNEL_WIDTH_TARGET",
                "stop_source": "CHANNEL_LOWER_LINE",
                "retest_structure_low": 102.95,
                "channel_lower_line_price_at_entry": 103.0,
                "channel_upper_line_price_at_entry": 113.0,
                "channel_width_at_entry": 10.0,
                "target_price_source": "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE",
                "target_source": "FVG_V2_CHANNEL_WIDTH_PROJECTION",
                "channel_target_policy": "PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1",
                "projected_channel_width_target": 122.5,
                "opposite_boundary_target_price": 113.0,
                "line_stop_price": 103.0,
                "line_target_price": 122.5,
                "cost_aware_entry_filter": {"blocked": False, "net_reward_bps": 800.0},
                "same_candle_entry_exit_ambiguity": False,
            },
        )
    )

    assert row["channel_mode"] == "FVG_V2_PARALLEL_CHANNEL"
    assert row["channel_geometry"] == geometry
    assert row["channel_candidate_source"] == "standalone_visible_prefix_scan"
    assert row["channel_scan_source"] == "rolling_visible_prefix"
    assert row["channel_trend_direction"] == "UPTREND"
    assert row["channel_direction_rule"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert row["channel_boundary_direction_mode"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert row["entry_boundary"] == "UPPER"
    assert row["original_channel_entry_side"] == "SHORT"
    assert row["effective_channel_entry_side"] == "LONG"
    assert row["stop_boundary"] == "LOWER"
    assert row["target_boundary"] == "CHANNEL_WIDTH_TARGET"
    assert row["stop_source"] == "CHANNEL_LOWER_LINE"
    assert row["retest_structure_low"] == 102.95
    assert row["channel_lower_line_price_at_entry"] == 103.0
    assert row["channel_width_at_entry"] == 10.0
    assert row["target_price_source"] == "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE"
    assert row["target_source"] == "FVG_V2_CHANNEL_WIDTH_PROJECTION"
    assert row["channel_target_policy"] == "PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1"
    assert row["projected_channel_width_target"] == 122.5
    assert row["opposite_boundary_target_price"] == 113.0
    assert row["line_stop_price"] == 103.0
    assert row["line_target_price"] == 122.5
    assert row["cost_aware_entry_filter"]["blocked"] is False
    assert row["same_candle_entry_exit_ambiguity"] is False


def test_serialize_trade_flattens_nested_exit_channel_metadata() -> None:
    service = BacktestResultsService(None)
    geometry = {
        "schema_version": "fvg_parallel_channel_v1",
        "window_start_index": 0,
        "window_end_index": 2,
        "lower_line": {"slope": 1.0, "intercept": 100.0},
        "upper_line": {"slope": 1.0, "intercept": 110.0},
        "width": 10.0,
    }

    row = service._serialize_trade(
        TradeRow(
            id=2,
            sequence=2,
            candle_open_time="2026-05-20T00:04:00Z",
            signal="LONG_EXIT",
            price=114.0,
            quantity=1.0,
            cash_after=10010.0,
            position_after=0.0,
            metadata={
                "exit_metadata": {
                    "channel_id": "abc123",
                    "channel_geometry": geometry,
                },
            },
        )
    )

    assert row["channel_id"] == "abc123"
    assert row["channel_geometry"] == geometry


def test_serialize_trade_allows_missing_channel_metadata_for_legacy_rows() -> None:
    service = BacktestResultsService(None)

    row = service._serialize_trade(
        TradeRow(
            id=1,
            sequence=1,
            candle_open_time="2026-05-20T00:03:00Z",
            signal="LONG_ENTRY",
            price=104.0,
            quantity=1.0,
            cash_after=9896.0,
            position_after=1.0,
            metadata={},
        )
    )

    assert "channel_geometry" not in row
    assert row["position_signal"] == "LONG_ENTRY"


def test_sample_graph_points_preserves_boundaries_markers_and_order() -> None:
    service = BacktestResultsService(None)
    graph_points = [_graph_point(sequence) for sequence in range(1000)]
    graph_points[10]["signal"] = "LONG_ENTRY"
    graph_points[500]["position_signal"] = "LONG_EXIT"
    graph_points[990]["metadata"] = {"trades": [{"position_signal": "SHORT_ENTRY"}]}
    trades = [
        {"candle_open_time": graph_points[10]["candle_open_time"]},
        {"candle_open_time": graph_points[500]["candle_open_time"]},
        {"candle_open_time": graph_points[990]["candle_open_time"]},
    ]

    sampled, metadata = service._sample_graph_points(
        graph_points,
        trades,
        graph_max_points=100,
        graph_sampling_mode="preserve_markers",
    )

    sampled_sequences = [point["sequence"] for point in sampled]
    assert len(sampled) == 100
    assert sampled_sequences[0] == 0
    assert sampled_sequences[-1] == 999
    assert 10 in sampled_sequences
    assert 500 in sampled_sequences
    assert 990 in sampled_sequences
    assert sampled_sequences == sorted(sampled_sequences)
    assert metadata == {
        "schema_version": "graph_sampling_v1",
        "sampled": True,
        "original_point_count": 1000,
        "returned_point_count": 100,
        "max_points": 100,
        "sampling_mode": "preserve_markers",
        "marker_point_count": 3,
        "preserved_marker_point_count": 3,
        "marker_points_preserved": True,
    }


def test_sample_graph_points_is_deterministic() -> None:
    service = BacktestResultsService(None)
    graph_points = [_graph_point(sequence) for sequence in range(250)]
    graph_points[125]["execution_side"] = "BUY"
    trades = [{"candle_open_time": graph_points[125]["candle_open_time"]}]

    first_sample, first_metadata = service._sample_graph_points(
        graph_points,
        trades,
        graph_max_points=120,
        graph_sampling_mode="preserve_markers",
    )
    second_sample, second_metadata = service._sample_graph_points(
        graph_points,
        trades,
        graph_max_points=120,
        graph_sampling_mode="preserve_markers",
    )

    assert first_sample == second_sample
    assert first_metadata == second_metadata
