from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.quant_backtest_api.dependencies import get_backtest_results_service
from backend.quant_backtest_api.schemas.backtest import BacktestRunDetailResponse, BacktestRunsListResponse
from backend.quant_backtest_api.services.backtest_results import BacktestResultsService

router = APIRouter(prefix="/api", tags=["backtest-runs"])


@router.get("/backtest-runs", response_model=BacktestRunsListResponse)
def list_backtest_runs(
    source: str | None = None,
    symbol: str | None = None,
    interval: str | None = None,
    actual_start_time: datetime | None = None,
    actual_end_time: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    service: BacktestResultsService = Depends(get_backtest_results_service),
) -> BacktestRunsListResponse:
    items = service.list_completed_runs(
        source=source,
        symbol=symbol,
        interval=interval,
        actual_start_time=actual_start_time,
        actual_end_time=actual_end_time,
        limit=limit,
    )
    return BacktestRunsListResponse(items=list(items), limit=limit)


@router.get("/backtest-runs/{backtest_run_id}", response_model=BacktestRunDetailResponse)
def get_backtest_run_detail(
    backtest_run_id: int,
    service: BacktestResultsService = Depends(get_backtest_results_service),
) -> BacktestRunDetailResponse:
    if backtest_run_id <= 0:
        raise HTTPException(status_code=400, detail="backtest_run_id must be positive")
    detail = service.load_run_for_graphs(backtest_run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="backtest run not found")
    return BacktestRunDetailResponse(**detail)
