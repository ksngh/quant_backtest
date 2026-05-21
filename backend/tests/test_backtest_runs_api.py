from fastapi.testclient import TestClient

from backend.quant_backtest_api.dependencies import get_backtest_results_service
from backend.quant_backtest_api.main import app


class FakeService:
    def list_completed_runs(self, **kwargs):
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
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs?limit=10")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["limit"] == 10


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
