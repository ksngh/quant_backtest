from fastapi.testclient import TestClient

from backend.quant_backtest_api.main import app


class FakeService:
    def db_reachable(self) -> bool:
        return True


def test_health_success_without_secrets(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@localhost/db")
    from backend.quant_backtest_api.dependencies import get_backtest_results_service

    app.dependency_overrides[get_backtest_results_service] = lambda: FakeService()
    client = TestClient(app)
    response = client.get("/api/health")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["database"]["configured"] is True
    assert "secret" not in str(body)
