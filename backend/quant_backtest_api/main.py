from fastapi import FastAPI

from backend.quant_backtest_api.routers.backtest_runs import router as backtest_runs_router
from backend.quant_backtest_api.routers.health import router as health_router

app = FastAPI(title="quant-backtest-api")
app.include_router(health_router)
app.include_router(backtest_runs_router)
