from backend.quant_backtest_api.services.backtest_results import BacktestResultsService
from quant_bitcoin.persistence.postgres import (
    BacktestGraphPointReadModel,
    BacktestRunMetadataReadModel,
    BacktestRunReadModel,
    BacktestStrategyConfigReadModel,
    BacktestSummaryReadModel,
    BacktestTradeReadModel,
)
from datetime import datetime, timezone


class _Repo:
    def __init__(self, rows):
        self.rows = rows

    def list_completed_runs(self, **kwargs):
        return self.rows

    def load_run_for_graphs(self, backtest_run_id):
        return self.rows[0] if self.rows else None


def _row(metadata):
    return {
        "id": 1,
        "run_key": "rk",
        "strategy_config_id": 1,
        "strategy_key": "k",
        "strategy_name": "name",
        "strategy_version": "v",
        "strategy_parameters": {},
        "strategy_parameters_hash": "h",
        "candle_source": "csv",
        "symbol": "BTCUSDT",
        "interval": "1h",
        "actual_start_time": None,
        "actual_end_time": None,
        "candle_count": 10,
        "final_equity": 1.0,
        "total_return": 0.1,
        "trade_count": 2,
        "metadata": metadata,
        "created_at": "2026-05-23T00:00:00Z",
        "completed_at": "2026-05-23T00:01:00Z",
    }


def test_list_runtime_summary_present():
    svc = BacktestResultsService(_Repo([_row({"runtime": {"total_elapsed_ms": 1500, "engine_elapsed_ms": 500}})]))
    items = svc.list_completed_runs(limit=1)
    assert items[0]["runtime"] == {"total_elapsed_ms": 1500.0, "engine_elapsed_ms": 500.0}


def test_list_runtime_summary_absent():
    svc = BacktestResultsService(_Repo([_row(None)]))
    items = svc.list_completed_runs(limit=1)
    assert items[0]["runtime"] is None


def test_list_runtime_summary_malformed_safe_none():
    svc = BacktestResultsService(_Repo([_row({"runtime": {"total_elapsed_ms": "x"}})]))
    items = svc.list_completed_runs(limit=1)
    assert items[0]["runtime"] is None


def test_detail_serialization_promotes_semantic_signal_and_account_state_metadata():
    now = datetime(2026, 5, 24, tzinfo=timezone.utc)
    model = BacktestRunReadModel(
        run=BacktestRunMetadataReadModel(
            id=1,
            run_key="rk",
            engine_name="strategy_engine",
            engine_version="v1",
            candle_source="csv",
            symbol="BTCUSDT",
            interval="1m",
            requested_start_time=None,
            requested_end_time=None,
            actual_start_time=None,
            actual_end_time=None,
            candle_count=1,
            starting_cash=10000.0,
            trade_quantity=1.0,
            status="completed",
            metadata={
                "reproducibility": {
                    "dataset_hash": "abc",
                    "database_url": "postgres://user:password@localhost/db",
                }
            },
            created_at=now,
            completed_at=now,
        ),
        strategy_config=BacktestStrategyConfigReadModel(
            id=1,
            strategy_key="stub",
            strategy_name="STUB",
            version="v1",
            parameters={},
            parameters_hash="h",
            metadata={},
        ),
        summary=BacktestSummaryReadModel(
            starting_cash=10000.0,
            ending_cash=20000.0,
            ending_position=-1.0,
            final_price=10000.0,
            final_equity=10000.0,
            total_return=0.0,
            trade_count=1,
            buy_count=0,
            sell_count=1,
            metadata={
                "performance_metrics": {"total_return": 0.0},
                "trade_attribution": {"trade_metrics": {"completed_trade_count": 1}},
                "cost_summary": {
                    "cost_to_gross_pnl_ratio": 0.12,
                    "zero_transaction_cost_assumption": False,
                },
            },
            created_at=now,
        ),
        trades=(
            BacktestTradeReadModel(
                id=1,
                sequence=1,
                candle_open_time=now,
                signal="SHORT_ENTRY",
                price=10000.0,
                quantity=1.0,
                cash_after=20000.0,
                position_after=-1.0,
                metadata={
                    "position_signal": "SHORT_ENTRY",
                    "execution_side": "SELL",
                    "cash_balance_after": 20000.0,
                    "free_cash_after": 0.0,
                    "short_proceeds_locked_after": 10000.0,
                    "short_collateral_locked_after": 10000.0,
                },
            ),
        ),
        graph_points=(
            BacktestGraphPointReadModel(
                id=1,
                sequence=1,
                candle_open_time=now,
                close_price=10000.0,
                cash=20000.0,
                position=-1.0,
                equity=10000.0,
                trade_id=1,
                signal="SHORT_ENTRY",
                metadata={
                    "free_cash": 0.0,
                    "short_proceeds_locked": 10000.0,
                    "short_collateral_locked": 10000.0,
                    "equity_semantics": "candle-close mark-to-market equity after applying actions at this timestamp",
                    "trades": [{"position_signal": "SHORT_ENTRY", "execution_side": "SELL"}],
                },
            ),
        ),
    )
    detail = BacktestResultsService(_Repo([model])).load_run_for_graphs(1)
    assert detail["trades"][0]["position_signal"] == "SHORT_ENTRY"
    assert detail["trades"][0]["execution_side"] == "SELL"
    assert detail["trades"][0]["free_cash_after"] == 0.0
    assert detail["trades"][0]["cash_balance_after"] == 20000.0
    assert detail["graph_points"][0]["position_signal"] == "SHORT_ENTRY"
    assert detail["graph_points"][0]["short_collateral_locked"] == 10000.0
    assert detail["diagnostics"]["summary"]["performance_metrics"] == {
        "total_return": 0.0
    }
    assert detail["diagnostics"]["summary"]["cost_summary"] == {
        "cost_to_gross_pnl_ratio": 0.12,
        "zero_transaction_cost_assumption": False,
    }
    assert detail["diagnostics"]["summary"]["performance_diagnostics"]["schema_version"] == "backtest_performance_diagnostics_v1"
    assert detail["diagnostics"]["summary"]["timing_diagnostics"]["schema_version"] == "trade_timing_diagnostics_v1"
    assert detail["diagnostics"]["summary"]["risk_exit_audit"]["schema_version"] == "risk_exit_audit_v1"
    assert detail["diagnostics"]["summary"]["score_calibration"]["schema_version"] == "pattern_score_calibration_v1"
    assert detail["research_report"]["schema_version"] == "backtest_research_report_v1"
    assert detail["research_report"]["data_summary"]["trade_rows"] == 1
    assert detail["research_report"]["reproducibility"]["database_url"] == "[REDACTED]"
    assert "postgres://user:password@localhost/db" not in str(detail["research_report"])
    assert "trades.metadata" in detail["diagnostics"]["available_sections"]
    assert "summary.cost_summary" in detail["diagnostics"]["available_sections"]
    assert "summary.performance_diagnostics" in detail["diagnostics"]["available_sections"]
    assert "summary.timing_diagnostics" in detail["diagnostics"]["available_sections"]
    assert "summary.risk_exit_audit" in detail["diagnostics"]["available_sections"]
    assert "summary.score_calibration" in detail["diagnostics"]["available_sections"]


def test_detail_serialization_exposes_legacy_timing_diagnostics_from_saved_rows():
    now = datetime(2026, 5, 24, tzinfo=timezone.utc)
    later = datetime(2026, 5, 24, 0, 1, tzinfo=timezone.utc)
    model = BacktestRunReadModel(
        run=BacktestRunMetadataReadModel(
            id=1,
            run_key="rk",
            engine_name="strategy_engine",
            engine_version="v1",
            candle_source="csv",
            symbol="BTCUSDT",
            interval="1m",
            requested_start_time=None,
            requested_end_time=None,
            actual_start_time=None,
            actual_end_time=None,
            candle_count=2,
            starting_cash=10000.0,
            trade_quantity=1.0,
            status="completed",
            metadata={},
            created_at=now,
            completed_at=later,
        ),
        strategy_config=BacktestStrategyConfigReadModel(
            id=1,
            strategy_key="stub",
            strategy_name="STUB",
            version="v1",
            parameters={},
            parameters_hash="h",
            metadata={},
        ),
        summary=BacktestSummaryReadModel(
            starting_cash=10000.0,
            ending_cash=10005.0,
            ending_position=0.0,
            final_price=105.0,
            final_equity=10005.0,
            total_return=0.0005,
            trade_count=2,
            buy_count=1,
            sell_count=1,
            metadata={},
            created_at=later,
        ),
        trades=(
            BacktestTradeReadModel(
                id=1,
                sequence=1,
                candle_open_time=now,
                signal="LONG_ENTRY",
                price=100.0,
                quantity=1.0,
                cash_after=9900.0,
                position_after=1.0,
                metadata={"action_type": "ENTER_LONG", "position_side": "LONG", "risk_per_unit": 5.0, "entry_reference": 100.0},
            ),
            BacktestTradeReadModel(
                id=2,
                sequence=2,
                candle_open_time=later,
                signal="LONG_EXIT",
                price=105.0,
                quantity=1.0,
                cash_after=10005.0,
                position_after=0.0,
                metadata={"action_type": "EXIT_LONG", "position_side": "LONG", "realized_r_multiple": 1.0, "exit_reason": "TIME_STOP"},
            ),
        ),
        graph_points=(
            BacktestGraphPointReadModel(
                id=1,
                sequence=1,
                candle_open_time=now,
                close_price=100.0,
                cash=9900.0,
                position=1.0,
                equity=10000.0,
                trade_id=1,
                signal="LONG_ENTRY",
                metadata={},
            ),
            BacktestGraphPointReadModel(
                id=2,
                sequence=2,
                candle_open_time=later,
                close_price=105.0,
                cash=10005.0,
                position=0.0,
                equity=10005.0,
                trade_id=2,
                signal="LONG_EXIT",
                metadata={},
            ),
        ),
    )

    detail = BacktestResultsService(_Repo([model])).load_run_for_graphs(1)

    timing = detail["diagnostics"]["summary"]["timing_diagnostics"]
    assert timing["schema_version"] == "trade_timing_diagnostics_v1"
    assert timing["completed_trade_count"] == 1
    assert timing["trades"][0]["mfe_r"] == 1.0
    assert "high/low path unavailable; MFE/MAE uses close-only approximation" in timing["warnings"]


def test_detail_serialization_returns_partial_legacy_performance_diagnostics():
    now = datetime(2026, 5, 24, tzinfo=timezone.utc)
    model = BacktestRunReadModel(
        run=BacktestRunMetadataReadModel(
            id=1,
            run_key="rk",
            engine_name="strategy_engine",
            engine_version="v1",
            candle_source="csv",
            symbol="BTCUSDT",
            interval="1m",
            requested_start_time=None,
            requested_end_time=None,
            actual_start_time=None,
            actual_end_time=None,
            candle_count=1,
            starting_cash=10000.0,
            trade_quantity=1.0,
            status="completed",
            metadata=None,
            created_at=now,
            completed_at=now,
        ),
        strategy_config=BacktestStrategyConfigReadModel(
            id=1,
            strategy_key="stub",
            strategy_name="STUB",
            version="v1",
            parameters={},
            parameters_hash="h",
            metadata=None,
        ),
        summary=BacktestSummaryReadModel(
            starting_cash=10000.0,
            ending_cash=10000.0,
            ending_position=0.0,
            final_price=10000.0,
            final_equity=10000.0,
            total_return=0.0,
            trade_count=0,
            buy_count=0,
            sell_count=0,
            metadata=None,
            created_at=now,
        ),
        trades=(),
        graph_points=(),
    )

    detail = BacktestResultsService(_Repo([model])).load_run_for_graphs(1)

    assert detail["diagnostics"]["summary"]["performance_diagnostics"]["schema_version"] == "backtest_performance_diagnostics_v1"
    assert "performance_metrics metadata missing" in detail["diagnostics"]["summary"]["performance_diagnostics"]["warnings"]
    assert detail["diagnostics"]["summary"]["performance_diagnostics"]["inference_strength"] == "PARTIAL"
