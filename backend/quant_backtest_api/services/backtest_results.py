from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from quant_bitcoin.backtesting.performance_diagnostics import calculate_backtest_performance_diagnostics
from quant_bitcoin.backtesting.timing_diagnostics import calculate_trade_timing_diagnostics
from quant_bitcoin.backtesting.risk_exit_audit import calculate_risk_exit_audit
from quant_bitcoin.backtesting.score_calibration import calculate_score_calibration_diagnostics
from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    PostgresBacktestResultRepository,
)
from backend.quant_backtest_api.services.research_report import build_backtest_research_report


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
        trades = [self._serialize_trade(trade) for trade in row.trades]
        graph_points = [self._serialize_graph_point(point) for point in row.graph_points]
        diagnostics = self._extract_research_diagnostics(
            run=run,
            summary=summary,
            trades=trades,
            graph_points=graph_points,
        )
        response = {
            "run": run,
            "strategy_config": strategy_config,
            "summary": summary,
            "trades": trades,
            "graph_points": graph_points,
            "diagnostics": diagnostics,
            "warnings": warnings,
        }
        response["research_report"] = build_backtest_research_report(
            run=run,
            strategy_config=strategy_config,
            summary=summary,
            trades=trades,
            graph_points=graph_points,
            diagnostics=diagnostics,
            warnings=warnings,
        )
        return response

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
        runtime_summary = self._extract_runtime_summary(data.get("metadata"))
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
            "runtime": runtime_summary,
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

    def _serialize_trade(self, trade: Any) -> dict[str, Any]:
        data = self._serialize_dataclass(trade)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        for key in (
            "position_signal",
            "side",
            "execution_side",
            "position_side",
            "cash_balance_after",
            "execution_equity_after",
            "mark_to_market_equity_after",
            "free_cash_after",
            "margin_used_after",
            "short_proceeds_locked_after",
            "short_collateral_locked_after",
            "available_buying_power_after",
            "cash_after_semantics",
        ):
            if key in metadata and key not in data:
                data[key] = metadata[key]
        if "position_signal" not in data:
            data["position_signal"] = metadata.get("position_signal") or data.get("signal")
        if "cash_balance_after" not in data:
            data["cash_balance_after"] = metadata.get("cash_balance_after", data.get("cash_after"))
        return data

    def _serialize_graph_point(self, point: Any) -> dict[str, Any]:
        data = self._serialize_dataclass(point)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        for source_key, target_key in (
            ("free_cash", "free_cash"),
            ("margin_used", "margin_used"),
            ("short_proceeds_locked", "short_proceeds_locked"),
            ("short_collateral_locked", "short_collateral_locked"),
            ("available_buying_power", "available_buying_power"),
            ("cash_semantics", "cash_semantics"),
            ("equity_semantics", "equity_semantics"),
        ):
            if source_key in metadata and target_key not in data:
                data[target_key] = metadata[source_key]
        trades = metadata.get("trades")
        if isinstance(trades, list) and trades:
            first_trade = trades[0] if isinstance(trades[0], dict) else {}
            data.setdefault("position_signal", first_trade.get("position_signal") or data.get("signal"))
            data.setdefault("execution_side", first_trade.get("execution_side"))
        return data

    def _warnings_for(self, model: BacktestRunReadModel) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []
        graph_points = list(model.graph_points)
        if graph_points and all(point.equity == 0 for point in graph_points):
            warnings.append(
                {
                    "code": "PATTERN_PLACEHOLDER_EQUITY",
                    "message": "Older persisted pattern runs may contain placeholder-neutral cash/equity values from pre-canonical compatibility history; treat those runs as non-financial diagnostics.",
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
                    "message": "Older persisted pattern runs may contain placeholder-neutral cash/equity values from pre-canonical compatibility history; treat those runs as non-financial diagnostics.",
                }
            )
        return warnings

    def _extract_runtime_summary(self, metadata: Any) -> dict[str, float] | None:
        if not isinstance(metadata, dict):
            return None
        runtime = metadata.get("runtime")
        if not isinstance(runtime, dict):
            return None

        summary: dict[str, float] = {}
        for key in ("total_elapsed_ms", "action_build_elapsed_ms", "engine_elapsed_ms"):
            value = runtime.get(key)
            if isinstance(value, (int, float)):
                summary[key] = float(value)
        return summary or None

    def _extract_research_diagnostics(
        self,
        *,
        run: dict[str, Any],
        summary: dict[str, Any],
        trades: list[dict[str, Any]],
        graph_points: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        diagnostics: dict[str, Any] = {
            "schema_version": "research_diagnostics_api_v1"
        }
        available_sections: list[str] = []

        run_metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        run_sections = self._metadata_subset(run_metadata, ("runtime",))
        if run_sections:
            diagnostics["run"] = run_sections
            available_sections.extend(f"run.{key}" for key in run_sections)

        summary_metadata = (
            summary.get("metadata") if isinstance(summary.get("metadata"), dict) else {}
        )
        summary_sections = self._metadata_subset(
            summary_metadata,
            (
                "account_state",
                "cost_summary",
                "performance_diagnostics",
                "performance_metrics",
                "pattern_execution_policy",
                "position_sizing",
                "risk_exit_audit",
                "score_calibration",
                "short_economics",
                "short_exposure_policy",
                "timing_diagnostics",
                "trade_attribution",
                "transaction_cost",
            ),
        )
        if "timing_diagnostics" not in summary_sections:
            summary_sections["timing_diagnostics"] = calculate_trade_timing_diagnostics(
                trades,
                graph_points,
            )
        if "risk_exit_audit" not in summary_sections:
            summary_sections["risk_exit_audit"] = calculate_risk_exit_audit(
                trades,
                summary_metadata,
            )
        if "score_calibration" not in summary_sections:
            summary_sections["score_calibration"] = calculate_score_calibration_diagnostics(
                trades,
                summary_metadata,
            )
        if "performance_diagnostics" not in summary_sections:
            summary_sections["performance_diagnostics"] = calculate_backtest_performance_diagnostics(
                summary_metadata,
                trades,
                graph_points,
            )
        if summary_sections:
            diagnostics["summary"] = summary_sections
            available_sections.extend(f"summary.{key}" for key in summary_sections)

        trade_metadata_keys = self._metadata_keys(trades)
        if trade_metadata_keys:
            diagnostics["trade_metadata_keys"] = trade_metadata_keys
            available_sections.append("trades.metadata")

        graph_metadata_keys = self._metadata_keys(graph_points)
        if graph_metadata_keys:
            diagnostics["graph_metadata_keys"] = graph_metadata_keys
            available_sections.append("graph_points.metadata")

        if not available_sections:
            return None
        diagnostics["available_sections"] = sorted(available_sections)
        return diagnostics

    def _metadata_subset(
        self, metadata: dict[str, Any], keys: tuple[str, ...]
    ) -> dict[str, Any]:
        return {
            key: metadata[key]
            for key in keys
            if key in metadata and metadata[key] is not None
        }

    def _metadata_keys(self, rows: list[dict[str, Any]]) -> list[str]:
        keys: set[str] = set()
        for row in rows:
            metadata = row.get("metadata")
            if isinstance(metadata, dict):
                keys.update(str(key) for key in metadata)
        return sorted(keys)

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
