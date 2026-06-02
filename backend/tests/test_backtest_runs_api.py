from fastapi.testclient import TestClient

from backend.quant_backtest_api.dependencies import get_backtest_results_service
from backend.quant_backtest_api.main import app


class FakeService:
    last_kwargs = None
    last_detail_kwargs = None

    def list_completed_runs(self, **kwargs):
        FakeService.last_kwargs = kwargs
        return ({"id": 1, "run_key": "abc", "strategy": {}, "market": {}, "summary": {}, "created_at": "2026-05-21T00:00:00Z", "completed_at": "2026-05-21T00:00:01Z"},)

    def load_run_for_graphs(self, backtest_run_id: int, **kwargs):
        FakeService.last_detail_kwargs = kwargs
        if backtest_run_id == 404:
            return None
        graph_max_points = kwargs.get("graph_max_points")
        returned_count = graph_max_points or 1
        return {
            "run": {"id": backtest_run_id},
            "strategy_config": {"name": "PATTERN_STRATEGY"},
            "summary": {},
            "trades": [{"id": 1}],
            "graph_points": [
                {"id": index, "sequence": index, "equity": 0, "cash": 0}
                for index in range(returned_count)
            ],
            "chart_metadata": {
                "schema_version": "chart_payload_metadata_v1",
                "graph_points": {
                    "schema_version": "graph_sampling_v1",
                    "sampled": bool(graph_max_points),
                    "original_point_count": 1000 if graph_max_points else returned_count,
                    "returned_point_count": returned_count,
                    "max_points": graph_max_points,
                    "sampling_mode": kwargs.get("graph_sampling_mode", "preserve_markers"),
                    "marker_point_count": 1,
                    "preserved_marker_point_count": 1,
                    "marker_points_preserved": True,
                },
            },
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
    FakeService.last_detail_kwargs = None
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs/1")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["trades"]
    assert data["graph_points"]
    assert data["warnings"]
    assert data["chart_metadata"]["graph_points"]["sampled"] is False
    assert FakeService.last_detail_kwargs == {
        "graph_max_points": None,
        "graph_sampling_mode": "preserve_markers",
    }


def test_detail_passes_bounded_graph_query_params():
    FakeService.last_detail_kwargs = None
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get(
        "/api/backtest-runs/1?graph_max_points=100&graph_sampling_mode=preserve_markers"
    )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert len(data["graph_points"]) == 100
    assert data["chart_metadata"]["graph_points"]["sampled"] is True
    assert data["chart_metadata"]["graph_points"]["original_point_count"] == 1000
    assert data["chart_metadata"]["graph_points"]["returned_point_count"] == 100
    assert FakeService.last_detail_kwargs == {
        "graph_max_points": 100,
        "graph_sampling_mode": "preserve_markers",
    }


def test_detail_rejects_unsupported_sampling_mode():
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs/1?graph_sampling_mode=unknown")
    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_detail_not_found():
    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/backtest-runs/404")
    app.dependency_overrides.clear()
    assert response.status_code == 404
