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
from backend.quant_backtest_api.services.research_report import (
    build_backtest_research_report,
    redact_sensitive,
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
        trades = [self._serialize_trade(trade) for trade in row.trades]
        graph_points = [self._serialize_graph_point(point) for point in row.graph_points]
        diagnostics = self._extract_research_diagnostics(
            run=run,
            summary=summary,
            trades=trades,
            graph_points=graph_points,
        )
        response = redact_sensitive({
            "run": run,
            "strategy_config": strategy_config,
            "summary": summary,
            "trades": trades,
            "graph_points": graph_points,
            "diagnostics": diagnostics,
            "warnings": warnings,
        })
        response["research_report"] = build_backtest_research_report(
            run=response["run"],
            strategy_config=response["strategy_config"],
            summary=response["summary"],
            trades=response["trades"],
            graph_points=response["graph_points"],
            diagnostics=response["diagnostics"],
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
        return redact_sensitive({
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
                "starting_cash": data["starting_cash"],
                "final_equity": data["final_equity"],
                "total_return": data["total_return"],
                "trade_count": data["trade_count"],
            },
            "runtime": runtime_summary,
            "created_at": data["created_at"],
            "completed_at": data["completed_at"],
        })

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
            "raw_price",
            "effective_price",
            "price_semantics",
            "effective_price_semantics",
            "cost_breakdown",
            "channel_geometry",
            "channel_id",
            "channel_candidate_source",
            "channel_scan_source",
            "channel_trend_direction",
            "channel_direction_rule",
            "channel_boundary_direction_mode",
            "channel_identity",
            "fvg_channel",
            "channel_mode",
            "entry_boundary",
            "original_channel_entry_side",
            "effective_channel_entry_side",
            "stop_boundary",
            "target_boundary",
            "stop_source",
            "retest_structure_low",
            "channel_lower_line_price_at_entry",
            "channel_upper_line_price_at_entry",
            "channel_width_at_entry",
            "target_price_source",
            "target_source",
            "channel_target_policy",
            "projected_channel_width_target",
            "opposite_boundary_target_price",
            "line_stop_price",
            "line_target_price",
            "same_candle_entry_exit_ambiguity",
            "cost_aware_entry_filter",
        ):
            if key in metadata and key not in data:
                data[key] = metadata[key]
        if "position_signal" not in data:
            data["position_signal"] = metadata.get("position_signal") or data.get("signal")
        if "cash_balance_after" not in data:
            data["cash_balance_after"] = metadata.get("cash_balance_after", data.get("cash_after"))
        exit_metadata = metadata.get("exit_metadata") if isinstance(metadata.get("exit_metadata"), dict) else {}
        for key in (
            "channel_geometry",
            "fvg_channel",
            "channel_id",
            "channel_candidate_source",
            "channel_scan_source",
            "channel_trend_direction",
            "channel_direction_rule",
            "channel_boundary_direction_mode",
            "channel_identity",
            "target_price_source",
            "target_source",
            "channel_target_policy",
            "projected_channel_width_target",
        ):
            if key not in data and key in exit_metadata:
                data[key] = exit_metadata[key]
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
                "fvg_retest_v2",
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
        metadata_schema_index = self._metadata_schema_index(summary_metadata, trades)
        if metadata_schema_index:
            summary_sections["metadata_schema_index"] = metadata_schema_index
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

    def _metadata_schema_index(
        self,
        summary_metadata: dict[str, Any],
        trades: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        contracts = {
            "pattern_execution_policy": self._schema_contract(
                expected_schema="pattern_execution_policy_v1",
                location="summary.metadata.pattern_execution_policy",
                value=summary_metadata.get("pattern_execution_policy"),
            ),
            "target_semantics": self._schema_contract(
                expected_schema="target_semantics_v1",
                location="trades.metadata.target_semantics",
                value=self._first_trade_metadata_record(trades, "target_semantics"),
            ),
            "score_components": self._score_components_contract(trades),
            "risk_exit_audit": self._schema_contract(
                expected_schema="risk_exit_audit_v2",
                location="summary.metadata.risk_exit_audit",
                value=summary_metadata.get("risk_exit_audit"),
                compatible_saved_schemas=("risk_exit_audit_v1",),
            ),
            "fvg_retest_v2": self._schema_contract(
                expected_schema="fvg_retest_v2_diagnostics_v1",
                location="summary.metadata.fvg_retest_v2",
                value=summary_metadata.get("fvg_retest_v2"),
            ),
            "intrabar_policy": self._intrabar_policy_contract(trades),
        }
        warnings = [
            f"{name} metadata unavailable"
            for name, contract in contracts.items()
            if contract["status"] == "missing"
        ]
        return {
            "schema_version": "backtest_metadata_schema_index_v1",
            "contracts": contracts,
            "warnings": warnings,
        }

    def _schema_contract(
        self,
        *,
        expected_schema: str,
        location: str,
        value: Any,
        compatible_saved_schemas: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        record = value if isinstance(value, dict) else None
        observed_schema = record.get("schema_version") if record else None
        status = "missing"
        if record:
            status = "present"
            if observed_schema and observed_schema not in (expected_schema, *compatible_saved_schemas):
                status = "schema_mismatch"
        return {
            "expected_schema": expected_schema,
            "compatible_saved_schemas": list(compatible_saved_schemas),
            "observed_schema": observed_schema,
            "location": location,
            "status": status,
        }

    def _score_components_contract(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        components = self._first_trade_metadata_record(trades, "score_components")
        component_values = list(components.values()) if isinstance(components, dict) else []
        component_records = [component for component in component_values if isinstance(component, dict)]
        invalid_component_count = len(component_values) - len(component_records)
        placeholder_count = sum(1 for component in component_records if component.get("is_placeholder") is True)
        return {
            "expected_schema": "score_components_v1",
            "observed_schema": "score_components_v1" if components else None,
            "location": "trades.metadata.score_components",
            "status": "present" if components else "missing",
            "component_count": len(component_values),
            "placeholder_component_count": placeholder_count,
            "invalid_component_count": invalid_component_count,
            "required_component_fields": [
                "raw_score",
                "weight",
                "source",
                "is_placeholder",
                "included_in_executable_score",
            ],
        }

    def _intrabar_policy_contract(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        policy = None
        ambiguous = None
        for trade in trades:
            metadata = trade.get("metadata")
            if not isinstance(metadata, dict):
                continue
            exit_metadata = metadata.get("exit_metadata")
            if isinstance(exit_metadata, dict):
                policy = policy or exit_metadata.get("intrabar_policy")
                ambiguous = ambiguous if ambiguous is not None else exit_metadata.get("ambiguous_stop_target")
            policy = policy or metadata.get("intrabar_policy")
            ambiguous = ambiguous if ambiguous is not None else metadata.get("ambiguous_stop_target")
            if policy is not None or ambiguous is not None:
                break
        return {
            "expected_schema": "intrabar_policy_v1",
            "observed_schema": "intrabar_policy_v1" if policy is not None or ambiguous is not None else None,
            "location": "trades.metadata.exit_metadata.intrabar_policy",
            "status": "present" if policy is not None or ambiguous is not None else "missing",
            "policy": policy,
            "ambiguous_stop_target": ambiguous,
        }

    def _first_trade_metadata_record(
        self,
        trades: list[dict[str, Any]],
        key: str,
    ) -> dict[str, Any] | None:
        for trade in trades:
            metadata = trade.get("metadata")
            if not isinstance(metadata, dict):
                continue
            value = metadata.get(key)
            if isinstance(value, dict):
                return value
        return None

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
