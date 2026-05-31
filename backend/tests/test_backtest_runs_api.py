from fastapi.testclient import TestClient

from backend.quant_backtest_api.dependencies import get_backtest_results_service
from backend.quant_backtest_api.main import app


class FakeService:
    last_kwargs = None

    def list_completed_runs(self, **kwargs):
        FakeService.last_kwargs = kwargs
        return ({"id": 1, "run_key": "abc", "strategy": {}, "market": {}, "summary": {}, "created_at": "2026-05-21T00:00:00Z", "completed_at": "2026-05-21T00:00:01Z"},)

    def load_run_for_graphs(self, backtest_run_id: int):
        if backtest_run_id == 404:
            return None
        return {
            "run": {"id": backtest_run_id},
            "strategy_config": {"name": "PATTERN_STRATEGY"},
            "summary": {},
            "trades": [{"id": 1}],
            "graph_points": [{"equity": 0, "cash": 0}],
            "warnings": [{"code": "PATTERN_PLACEHOLDER_EQUITY", "message": "x"}],
        }


def test_list_runs_success():
    FakeService.last_kwargs = None
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get(
        "/api/backtest-runs?limit=10&source=binance_spot&symbol=BTCUSDT&interval=1m"
        "&strategy_key=pattern_strategy&actual_start_time=2026-05-20T00:00:00Z"
        "&actual_end_time=2026-05-21T00:00:00Z&created_start_time=2026-05-20T00:00:00Z"
        "&created_end_time=2026-05-28T00:00:00Z&min_total_return=-0.05"
        "&max_total_return=0.1&cost_profile=conservative_crypto_1m"
    )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["limit"] == 10
    assert FakeService.last_kwargs is not None
    assert FakeService.last_kwargs["source"] == "binance_spot"
    assert FakeService.last_kwargs["symbol"] == "BTCUSDT"
    assert FakeService.last_kwargs["interval"] == "1m"
    assert FakeService.last_kwargs["strategy_key"] == "pattern_strategy"
    assert FakeService.last_kwargs["min_total_return"] == -0.05
    assert FakeService.last_kwargs["max_total_return"] == 0.1
    assert FakeService.last_kwargs["cost_profile"] == "conservative_crypto_1m"


def test_limit_validation():
    client = TestClient(app)
    response = client.get("/api/backtest-runs?limit=101")
    assert response.status_code == 422


def test_detail_success():
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs/1")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["trades"]
    assert data["graph_points"]
    assert data["warnings"]


def test_detail_not_found():
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs/404")
    app.dependency_overrides.clear()
    assert response.status_code == 404
