from __future__ import annotations

from quant_bitcoin.persistence.postgres import PostgresBacktestResultRepository

from backend.quant_backtest_api.services.backtest_results import BacktestResultsService
from backend.quant_backtest_api.settings import AppSettings, load_settings


def get_settings() -> AppSettings:
    return load_settings()


def get_backtest_results_service(settings: AppSettings | None = None) -> BacktestResultsService:
    resolved_settings = settings or load_settings()
    return BacktestResultsService(
        repository=(
            PostgresBacktestResultRepository(resolved_settings.database_url)
            if resolved_settings.database_url
            else None
        )
    )
