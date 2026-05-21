from fastapi import APIRouter, Depends

from backend.quant_backtest_api.dependencies import get_backtest_results_service, get_settings
from backend.quant_backtest_api.schemas.health import HealthDatabase, HealthResponse
from backend.quant_backtest_api.services.backtest_results import BacktestResultsService
from backend.quant_backtest_api.settings import AppSettings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(
    settings: AppSettings = Depends(get_settings),
    service: BacktestResultsService = Depends(get_backtest_results_service),
) -> HealthResponse:
    configured = settings.db_configured
    return HealthResponse(
        status="ok",
        service="quant-backtest-api",
        database=HealthDatabase(configured=configured, reachable=service.db_reachable() if configured else False),
    )
