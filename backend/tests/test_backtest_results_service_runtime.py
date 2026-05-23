from backend.quant_backtest_api.services.backtest_results import BacktestResultsService


class _Repo:
    def __init__(self, rows):
        self.rows = rows

    def list_completed_runs(self, **kwargs):
        return self.rows


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
