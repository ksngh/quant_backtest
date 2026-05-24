from pydantic import BaseModel


class BacktestRunsListResponse(BaseModel):
    items: list[dict]
    limit: int


class BacktestRunDetailResponse(BaseModel):
    run: dict
    strategy_config: dict
    summary: dict
    trades: list[dict]
    graph_points: list[dict]
    diagnostics: dict | None = None
    warnings: list[dict]
