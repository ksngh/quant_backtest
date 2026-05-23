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
            metadata={},
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
            metadata={},
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
