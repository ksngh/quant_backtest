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
    strategy_key: str | None = None,
    actual_start_time: datetime | None = None,
    actual_end_time: datetime | None = None,
    created_start_time: datetime | None = None,
    created_end_time: datetime | None = None,
    min_total_return: float | None = None,
    max_total_return: float | None = None,
    cost_profile: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    service: BacktestResultsService = Depends(get_backtest_results_service),
) -> BacktestRunsListResponse:
    if (
        actual_start_time is not None
        and actual_end_time is not None
        and actual_start_time > actual_end_time
    ):
        raise HTTPException(status_code=400, detail="actual_start_time must be <= actual_end_time")
    if (
        created_start_time is not None
        and created_end_time is not None
        and created_start_time > created_end_time
    ):
        raise HTTPException(status_code=400, detail="created_start_time must be <= created_end_time")
    if (
        min_total_return is not None
        and max_total_return is not None
        and min_total_return > max_total_return
    ):
        raise HTTPException(status_code=400, detail="min_total_return must be <= max_total_return")
    items = service.list_completed_runs(
        source=source,
        symbol=symbol,
        interval=interval,
        strategy_key=strategy_key,
        actual_start_time=actual_start_time,
        actual_end_time=actual_end_time,
        created_start_time=created_start_time,
        created_end_time=created_end_time,
        min_total_return=min_total_return,
        max_total_return=max_total_return,
        cost_profile=cost_profile,
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
