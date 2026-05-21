from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    PostgresBacktestResultRepository,
)


class BacktestResultsService:
    def __init__(self, repository: PostgresBacktestResultRepository | None) -> None:
        self.repository = repository

    def list_completed_runs(self, **kwargs: Any) -> tuple[dict[str, Any], ...]:
        if self.repository is None:
            return tuple()
        return tuple(
            self._serialize_list_item(item)
            for item in self.repository.list_completed_runs(**kwargs)
        )

    def load_run_for_graphs(self, backtest_run_id: int) -> dict[str, Any] | None:
        if self.repository is None:
            return None
        row = self.repository.load_run_for_graphs(backtest_run_id)
        if row is None:
            return None
        warnings = self._warnings_for(row)
        run = self._serialize_run(row.run)
        strategy_config = self._serialize_strategy_config(row.strategy_config)
        summary = self._serialize_dataclass(row.summary)
        trades = [self._serialize_dataclass(trade) for trade in row.trades]
        graph_points = [self._serialize_dataclass(point) for point in row.graph_points]
        return {
            "run": run,
            "strategy_config": strategy_config,
            "summary": summary,
            "trades": trades,
            "graph_points": graph_points,
            "warnings": warnings,
        }

    def db_reachable(self) -> bool:
        if self.repository is None:
            return False
        try:
            self.repository.list_completed_runs(limit=1)
            return True
        except Exception:
            return False

    def _serialize_list_item(self, item: Any) -> dict[str, Any]:
        data = self._serialize_dataclass(item)
        return {
            "id": data["id"],
            "run_key": data["run_key"],
            "strategy": {
                "config_id": data["strategy_config_id"],
                "key": data["strategy_key"],
                "name": data["strategy_name"],
                "version": data["strategy_version"],
                "parameters": data["strategy_parameters"],
                "parameters_hash": data["strategy_parameters_hash"],
            },
            "market": {
                "source": data["candle_source"],
                "symbol": data["symbol"],
                "interval": data["interval"],
                "actual_start_time": data["actual_start_time"],
                "actual_end_time": data["actual_end_time"],
                "candle_count": data["candle_count"],
            },
            "summary": {
                "final_equity": data["final_equity"],
                "total_return": data["total_return"],
                "trade_count": data["trade_count"],
            },
            "created_at": data["created_at"],
            "completed_at": data["completed_at"],
        }

    def _serialize_run(self, run: Any) -> dict[str, Any]:
        data = self._serialize_dataclass(run)
        return {
            "id": data["id"],
            "run_key": data["run_key"],
            "engine_name": data["engine_name"],
            "engine_version": data["engine_version"],
            "status": data["status"],
            "market": {
                "source": data["candle_source"],
                "symbol": data["symbol"],
                "interval": data["interval"],
                "requested_start_time": data["requested_start_time"],
                "requested_end_time": data["requested_end_time"],
                "actual_start_time": data["actual_start_time"],
                "actual_end_time": data["actual_end_time"],
                "candle_count": data["candle_count"],
            },
            "starting_cash": data["starting_cash"],
            "trade_quantity": data["trade_quantity"],
            "created_at": data["created_at"],
            "completed_at": data["completed_at"],
            "metadata": data["metadata"],
        }

    def _serialize_strategy_config(self, strategy: Any) -> dict[str, Any]:
        data = self._serialize_dataclass(strategy)
        return {
            "id": data["id"],
            "key": data["strategy_key"],
            "name": data["strategy_name"],
            "version": data["version"],
            "parameters": data["parameters"],
            "parameters_hash": data["parameters_hash"],
            "metadata": data["metadata"],
        }

    def _warnings_for(self, model: BacktestRunReadModel) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []
        graph_points = list(model.graph_points)
        if graph_points and all(point.equity == 0 for point in graph_points):
            warnings.append(
                {
                    "code": "PATTERN_PLACEHOLDER_EQUITY",
                    "message": "Some persisted pattern runs may contain placeholder-neutral cash/equity values until richer financial persistence is implemented.",
                }
            )
        if graph_points and all(point.cash == 0 for point in graph_points):
            warnings.append(
                {
                    "code": "PATTERN_PLACEHOLDER_CASH",
                    "message": "Persisted cash values appear placeholder-like (all zero).",
                }
            )
        if (
            "pattern" in model.strategy_config.strategy_name.lower()
            and not model.summary.metadata
        ):
            warnings.append(
                {
                    "code": "PATTERN_PLACEHOLDER_EQUITY",
                    "message": "Some persisted pattern runs may contain placeholder-neutral cash/equity values until richer financial persistence is implemented.",
                }
            )
        return warnings

    def _serialize_dataclass(self, value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            return {
                key: self._serialize_dataclass(getattr(value, key))
                for key in value.__dataclass_fields__
            }
        if isinstance(value, datetime):
            normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return normalized.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (tuple, list)):
            return [self._serialize_dataclass(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_dataclass(v) for k, v in value.items()}
        return value
