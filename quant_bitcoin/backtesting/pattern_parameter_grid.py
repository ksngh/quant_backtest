from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product
from typing import Any, Mapping, Sequence

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, cost_profile
from quant_bitcoin.backtesting.costs import TransactionCostConfig
from quant_bitcoin.backtesting.json_metadata import json_ready, metadata_hash
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.strategy_postgres_runner_core import _expand_raw_actions
from quant_bitcoin.backtesting.fvg_detection_cache import IndicatorCache, PatternEvaluationContext
from quant_bitcoin.backtesting.sizing import PositionSizingConfig, PositionSizingMode
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus
from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.strategies.pattern_execution_policy import validate_pattern_entry_mode
from quant_bitcoin.strategies.patterns import PatternEntryFilterConfig, strategy_for_pattern

PATTERN_PARAMETER_GRID_SCHEMA_VERSION = "pattern_parameter_grid_v1"


@dataclass(frozen=True)
class PatternParameterGridConfig:
    max_combinations: int = 100
    warning_combinations: int = 50
    dry_run: bool = False
    starting_cash: float = 10000.0
    trade_quantity: float = 1.0
    interval: str = "1m"

    def __post_init__(self) -> None:
        if self.max_combinations < 1:
            raise ValueError("max_combinations must be at least 1")
        if self.warning_combinations < 1:
            raise ValueError("warning_combinations must be at least 1")
        if self.starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        if self.trade_quantity <= 0:
            raise ValueError("trade_quantity must be positive")


@dataclass(frozen=True)
class PatternParameterSet:
    index: int
    parameters: dict[str, Any]

    @property
    def parameter_hash(self) -> str:
        return pattern_parameter_hash(self.parameters)


def pattern_parameter_hash(parameters: Mapping[str, Any]) -> str:
    return metadata_hash({"schema_version": "pattern_parameter_set_v1", "parameters": dict(parameters)})


def expand_parameter_grid(
    grid: Mapping[str, Sequence[Any]],
    *,
    max_combinations: int,
) -> tuple[PatternParameterSet, ...]:
    if max_combinations < 1:
        raise ValueError("max_combinations must be at least 1")
    normalized = {str(path): tuple(values) for path, values in grid.items()}
    empty_paths = [path for path, values in normalized.items() if not values]
    if empty_paths:
        raise ValueError(f"parameter path has no values: {', '.join(sorted(empty_paths))}")
    paths = tuple(sorted(normalized))
    total = 1
    for path in paths:
        total *= len(normalized[path])
    if total > max_combinations:
        raise ValueError(f"parameter grid has {total} combinations; max_combinations={max_combinations}")
    return tuple(
        PatternParameterSet(
            index=index,
            parameters={path: value for path, value in zip(paths, values)},
        )
        for index, values in enumerate(product(*(normalized[path] for path in paths)), start=1)
    )


def run_pattern_parameter_grid(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    pattern: str,
    grid: Mapping[str, Sequence[Any]],
    config: PatternParameterGridConfig | None = None,
) -> dict[str, Any]:
    runner_config = config or PatternParameterGridConfig()
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    parameter_sets = expand_parameter_grid(grid, max_combinations=runner_config.max_combinations)
    warnings: list[str] = []
    if len(parameter_sets) >= runner_config.warning_combinations:
        warnings.append(
            f"large parameter grid: {len(parameter_sets)} combinations; "
            f"warning_combinations={runner_config.warning_combinations}"
        )
    rows = [
        _dry_run_row(pattern, parameter_set)
        if runner_config.dry_run
        else _run_parameter_set(frame, pattern, parameter_set, runner_config)
        for parameter_set in parameter_sets
    ]
    return {
        "schema_version": PATTERN_PARAMETER_GRID_SCHEMA_VERSION,
        "pattern": pattern.upper(),
        "dry_run": runner_config.dry_run,
        "combination_count": len(parameter_sets),
        "max_combinations": runner_config.max_combinations,
        "warnings": warnings,
        "rows": rows,
    }


def _dry_run_row(pattern: str, parameter_set: PatternParameterSet) -> dict[str, Any]:
    _validate_parameter_set(pattern, parameter_set.parameters)
    return {
        "parameter_set_index": parameter_set.index,
        "parameter_hash": parameter_set.parameter_hash,
        "parameters": json_ready(parameter_set.parameters),
        "status": "DRY_RUN",
        "metrics": None,
        "error": None,
    }


def _run_parameter_set(
    candles: pd.DataFrame,
    pattern: str,
    parameter_set: PatternParameterSet,
    config: PatternParameterGridConfig,
) -> dict[str, Any]:
    try:
        strategy, entry_filter, entry_mode, entry_config, cost_config, sizing = _configured_strategy(
            pattern,
            parameter_set.parameters,
        )
        policy_metadata = validate_pattern_entry_mode(strategy.strategy_key, entry_mode).to_metadata(
            selected_entry_mode=entry_mode
        )
        actions = _build_actions(
            candles,
            strategy,
            entry_mode=entry_mode,
            entry_config=entry_config,
            pattern_policy_metadata=policy_metadata,
        )
        result = run_strategy_backtest_engine(
            candles,
            actions,
            config=StrategyEngineConfig(
                starting_cash=config.starting_cash,
                trade_quantity=config.trade_quantity,
                interval=config.interval,
                transaction_cost_config=cost_config,
                position_sizing=sizing,
            ),
        )
        metrics = _result_metrics(actions, result)
        return {
            "parameter_set_index": parameter_set.index,
            "parameter_hash": parameter_set.parameter_hash,
            "parameters": json_ready(parameter_set.parameters),
            "status": "NO_FILLS" if result.summary.trade_count == 0 else "OK",
            "metrics": json_ready(metrics),
            "error": None,
            "strategy_filter": json_ready(entry_filter),
        }
    except Exception as exc:
        return {
            "parameter_set_index": parameter_set.index,
            "parameter_hash": parameter_set.parameter_hash,
            "parameters": json_ready(parameter_set.parameters),
            "status": "FAILED",
            "metrics": None,
            "error": str(exc),
        }


def _validate_parameter_set(pattern: str, parameters: Mapping[str, Any]) -> None:
    _configured_strategy(pattern, parameters)


def _configured_strategy(
    pattern: str,
    parameters: Mapping[str, Any],
):
    filter_kwargs: dict[str, Any] = {}
    entry_mode = PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE
    entry_config_kwargs: dict[str, Any] = {}
    cost_profile_name = "zero"
    sizing_mode = PositionSizingMode.FIXED_QUANTITY
    sizing_value = None

    strategy = strategy_for_pattern(pattern)
    detector_updates: dict[str, Any] = {}
    risk_updates: dict[str, Any] = {}

    for path, value in parameters.items():
        if path.startswith("detector."):
            detector_updates[path.removeprefix("detector.")] = value
        elif path.startswith("risk."):
            risk_updates[path.removeprefix("risk.")] = value
        elif path == "entry.mode":
            entry_mode = _entry_mode(value)
        elif path == "entry.max_wait_bars":
            entry_config_kwargs["max_wait_bars"] = None if value is None else int(value)
        elif path == "entry.expire_status":
            entry_config_kwargs["expire_status"] = PatternEntryStatus(str(value).upper().replace("-", "_"))
        elif path == "cost.profile":
            cost_profile_name = str(value).lower()
        elif path == "sizing.mode":
            sizing_mode = PositionSizingMode(str(value).upper())
        elif path == "sizing.value":
            sizing_value = None if value is None else float(value)
        elif path == "filter.minimum_pattern_score":
            filter_kwargs["minimum_pattern_score"] = None if value is None else float(value)
        elif path == "filter.minimum_risk_reward":
            filter_kwargs["minimum_risk_reward"] = None if value is None else float(value)
        else:
            raise ValueError(f"unsupported parameter path: {path}")

    if detector_updates:
        _validate_dataclass_fields(strategy.detector_config, detector_updates, "detector")
        object.__setattr__(strategy, "detector_config", replace(strategy.detector_config, **detector_updates))
    if risk_updates:
        _validate_dataclass_fields(strategy.risk_config, risk_updates, "risk")
        object.__setattr__(strategy, "risk_config", replace(strategy.risk_config, **risk_updates))
    if cost_profile_name not in COST_PROFILES:
        raise ValueError(f"unsupported cost profile: {cost_profile_name}")

    entry_filter = PatternEntryFilterConfig(**filter_kwargs)
    object.__setattr__(strategy, "entry_filter_config", entry_filter)
    entry_config = PatternEntryConfig(**entry_config_kwargs)
    cost_config = (
        TransactionCostConfig()
        if cost_profile_name == "zero"
        else cost_profile(cost_profile_name).config
    )
    sizing = PositionSizingConfig(mode=sizing_mode, value=sizing_value)
    return strategy, entry_filter, entry_mode, entry_config, cost_config, sizing


def _validate_dataclass_fields(instance: Any, updates: Mapping[str, Any], prefix: str) -> None:
    available = set(getattr(instance, "__dataclass_fields__", {}))
    invalid = sorted(set(updates) - available)
    if invalid:
        raise ValueError(f"unsupported {prefix} parameter field: {', '.join(invalid)}")


def _entry_mode(value: Any) -> PatternEntryMode:
    return PatternEntryMode(str(value).upper().replace("-", "_"))


def _build_actions(
    candles: pd.DataFrame,
    strategy: Any,
    *,
    entry_mode: PatternEntryMode,
    entry_config: PatternEntryConfig,
    pattern_policy_metadata: dict[str, Any],
) -> list[Any]:
    actions: list[Any] = []
    cache = IndicatorCache.for_pattern(candles, strategy.detector_config)
    seen_event_ids: set[str] = set()
    for index in range(1, len(candles) + 1):
        raw_actions = strategy.evaluate_at(
            PatternEvaluationContext(
                candles=candles,
                current_index=index - 1,
                indicator_cache=cache,
                seen_event_ids=seen_event_ids,
            )
        )
        actions.extend(
            _expand_raw_actions(
                raw_actions,
                candles,
                index,
                pattern_entry_mode=entry_mode,
                fvg_entry_config=entry_config,
                pattern_policy_metadata=pattern_policy_metadata,
            )
        )
    return actions


def _result_metrics(actions: Sequence[Any], result: Any) -> dict[str, Any]:
    entry_actions = [
        action
        for action in actions
        if action.action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT)
    ]
    no_fill_actions = [
        action
        for action in actions
        if action.action_type == StrategyActionType.SKIP and getattr(action, "reason", None) == "ENTRY_NOT_FILLED"
    ]
    evaluated_count = len(entry_actions) + len(no_fill_actions)
    metadata = result.summary.metadata or {}
    trade_metrics = ((metadata.get("trade_attribution") or {}).get("trade_metrics") or {})
    cost_summary = metadata.get("cost_summary") or {}
    return {
        "trade_count": result.summary.trade_count,
        "candidate_count": evaluated_count,
        "filled_entry_count": len(entry_actions),
        "fill_rate": None if evaluated_count == 0 else len(entry_actions) / evaluated_count,
        "expectancy": trade_metrics.get("expectancy"),
        "average_r": trade_metrics.get("average_r"),
        "hit_rate": trade_metrics.get("hit_ratio"),
        "profit_factor": trade_metrics.get("profit_factor"),
        "profit_factor_is_infinite": trade_metrics.get("profit_factor_is_infinite"),
        "max_drawdown": result.summary.max_drawdown,
        "cost_ratio": cost_summary.get("cost_to_gross_pnl_ratio"),
        "no_fill_count": len(no_fill_actions),
    }
