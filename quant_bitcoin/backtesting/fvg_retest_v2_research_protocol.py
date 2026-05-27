from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, cost_profile
from quant_bitcoin.backtesting.costs import TransactionCostConfig
from quant_bitcoin.backtesting.json_metadata import json_ready, metadata_hash
from quant_bitcoin.backtesting.pattern_parameter_grid import (
    PatternParameterGridConfig,
    expand_parameter_grid,
    run_pattern_parameter_grid,
)
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig
from quant_bitcoin.backtesting.walk_forward import (
    WalkForwardConfig,
    build_pattern_action_builder,
    run_walk_forward_validation,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus, PatternEntryTrigger
from quant_bitcoin.strategies.patterns import PatternEntryFilterConfig

FVG_RETEST_V2_PARAMETER_DECLARATION_SCHEMA_VERSION = "fvg_retest_v2_parameter_declaration_v1"
FVG_RETEST_V2_RESEARCH_PROTOCOL_SCHEMA_VERSION = "fvg_retest_v2_research_protocol_v1"

FVG_RETEST_V2_REQUIRED_PARAMETER_PATHS: tuple[str, ...] = (
    "entry.mode",
    "entry.trigger",
    "risk.stop_mode",
    "cost.profile",
)

FVG_RETEST_V2_GROUPING_DIMENSIONS: tuple[str, ...] = (
    "detector.use_multitimeframe_trend_score",
    "detector.use_fibonacci_confluence",
    "risk.require_liquidity_target",
    "entry.trigger",
    "risk.stop_mode",
    "cost.profile",
    "regime_stratification.market_regime",
    "regime_stratification.session_tag",
)


@dataclass(frozen=True)
class FvgRetestV2ResearchProtocolConfig:
    max_combinations: int = 32
    warning_combinations: int = 16
    require_realistic_cost_profile: bool = True
    starting_cash: float = 10000.0
    trade_quantity: float = 1.0
    interval: str = "1m"
    minimum_folds_for_promotion: int = 3
    minimum_positive_fold_ratio: float = 0.55
    maximum_no_fill_fold_ratio: float = 0.5

    def __post_init__(self) -> None:
        if self.max_combinations < 1:
            raise ValueError("max_combinations must be at least 1")
        if self.warning_combinations < 1:
            raise ValueError("warning_combinations must be at least 1")
        if self.starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        if self.trade_quantity <= 0:
            raise ValueError("trade_quantity must be positive")
        if self.minimum_folds_for_promotion < 1:
            raise ValueError("minimum_folds_for_promotion must be at least 1")
        if not 0 <= self.minimum_positive_fold_ratio <= 1:
            raise ValueError("minimum_positive_fold_ratio must be between 0 and 1")
        if not 0 <= self.maximum_no_fill_fold_ratio <= 1:
            raise ValueError("maximum_no_fill_fold_ratio must be between 0 and 1")


def default_fvg_retest_v2_parameter_grid() -> dict[str, tuple[Any, ...]]:
    return {
        "detector.use_multitimeframe_trend_score": (False, True),
        "detector.use_fibonacci_confluence": (False, True),
        "risk.require_liquidity_target": (False,),
        "entry.mode": ("limit_at_pattern_midpoint",),
        "entry.trigger": ("touch", "touch_and_reaction_close"),
        "risk.stop_mode": ("fvg_boundary_atr_buffer", "wider_of_fvg_and_swing"),
        "cost.profile": ("conservative_crypto_1m",),
    }


def validate_fvg_retest_v2_parameter_declaration(
    grid: Mapping[str, Sequence[Any]],
    *,
    config: FvgRetestV2ResearchProtocolConfig | None = None,
) -> dict[str, Any]:
    protocol_config = config or FvgRetestV2ResearchProtocolConfig()
    missing = sorted(set(FVG_RETEST_V2_REQUIRED_PARAMETER_PATHS) - set(grid))
    if missing:
        raise ValueError(f"missing required FVG v2 parameter paths: {', '.join(missing)}")

    parameter_sets = expand_parameter_grid(grid, max_combinations=protocol_config.max_combinations)
    run_pattern_parameter_grid(
        _minimal_validation_candles(),
        pattern="FAIR_VALUE_GAP",
        grid=grid,
        config=PatternParameterGridConfig(
            max_combinations=protocol_config.max_combinations,
            warning_combinations=protocol_config.warning_combinations,
            dry_run=True,
        ),
    )
    cost_profiles = tuple(str(value).lower() for value in grid.get("cost.profile", ()))
    if protocol_config.require_realistic_cost_profile and not any(profile != "zero" for profile in cost_profiles):
        raise ValueError("FVG v2 protocol requires at least one non-zero cost.profile; zero-cost rows are debugging-only")

    warnings: list[str] = []
    if "zero" in cost_profiles:
        warnings.append("zero cost.profile rows are debugging-only and cannot support promotion evidence")
    if len(parameter_sets) >= protocol_config.warning_combinations:
        warnings.append(
            f"large FVG v2 declaration: {len(parameter_sets)} combinations; "
            f"warning_combinations={protocol_config.warning_combinations}"
        )
    return {
        "schema_version": FVG_RETEST_V2_PARAMETER_DECLARATION_SCHEMA_VERSION,
        "required_paths": FVG_RETEST_V2_REQUIRED_PARAMETER_PATHS,
        "grouping_dimensions": FVG_RETEST_V2_GROUPING_DIMENSIONS,
        "combination_count": len(parameter_sets),
        "max_combinations": protocol_config.max_combinations,
        "parameter_hashes": tuple(parameter_set.parameter_hash for parameter_set in parameter_sets),
        "grid": json_ready(dict(grid)),
        "warnings": tuple(warnings),
    }


def run_fvg_retest_v2_research_protocol(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    walk_forward_config: WalkForwardConfig,
    parameter_grid: Mapping[str, Sequence[Any]] | None = None,
    config: FvgRetestV2ResearchProtocolConfig | None = None,
) -> dict[str, Any]:
    protocol_config = config or FvgRetestV2ResearchProtocolConfig()
    grid = dict(parameter_grid or default_fvg_retest_v2_parameter_grid())
    declaration = validate_fvg_retest_v2_parameter_declaration(grid, config=protocol_config)
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    parameter_sets = expand_parameter_grid(grid, max_combinations=protocol_config.max_combinations)
    grid_report = run_pattern_parameter_grid(
        frame,
        pattern="FAIR_VALUE_GAP",
        grid=grid,
        config=PatternParameterGridConfig(
            max_combinations=protocol_config.max_combinations,
            warning_combinations=protocol_config.warning_combinations,
            starting_cash=protocol_config.starting_cash,
            trade_quantity=protocol_config.trade_quantity,
            interval=protocol_config.interval,
        ),
    )

    variant_rows = []
    for parameter_set in parameter_sets:
        components = _parameter_components(parameter_set.parameters)
        wfo_payload = run_walk_forward_validation(
            frame,
            config=walk_forward_config,
            action_builder=build_pattern_action_builder(
                pattern="FAIR_VALUE_GAP",
                entry_filter_config=components["entry_filter_config"],
                entry_mode=components["entry_mode"],
                entry_config=components["entry_config"],
                detector_config_updates=components["detector_updates"],
                risk_config_updates=components["risk_updates"],
            ),
            engine_config=StrategyEngineConfig(
                starting_cash=protocol_config.starting_cash,
                trade_quantity=protocol_config.trade_quantity,
                interval=protocol_config.interval,
                transaction_cost_config=components["transaction_cost_config"],
            ),
            strategy_parameters={
                "strategy": "pattern",
                "pattern": "FAIR_VALUE_GAP",
                **json_ready(parameter_set.parameters),
            },
        )
        variant_rows.append(
            {
                "parameter_set_index": parameter_set.index,
                "parameter_hash": parameter_set.parameter_hash,
                "parameters": json_ready(parameter_set.parameters),
                "walk_forward": wfo_payload,
                "summary": _variant_summary(wfo_payload, parameter_set.parameters, protocol_config),
            }
        )

    research_note = _research_note(declaration, grid_report, variant_rows, protocol_config)
    payload = {
        "schema_version": FVG_RETEST_V2_RESEARCH_PROTOCOL_SCHEMA_VERSION,
        "research_scope": "offline_backtest_research_only",
        "dataset_identity": _dataset_identity(frame),
        "config_hash": metadata_hash(
            {
                "schema_version": FVG_RETEST_V2_RESEARCH_PROTOCOL_SCHEMA_VERSION,
                "declaration": declaration,
                "walk_forward_config": _walk_forward_config_metadata(walk_forward_config),
            }
        ),
        "parameter_declaration": declaration,
        "parameter_grid_report": grid_report,
        "variant_results": variant_rows,
        "research_note": research_note,
        "markdown": _markdown(research_note),
        "safety_boundary": (
            "No live trading approval.",
            "No paper/testnet promotion.",
            "No exchange order/account endpoints, signed requests, API keys, or .env behavior.",
            "All variants, including weak and losing variants, remain in the output.",
        ),
    }
    return json_ready(payload)


def _parameter_components(parameters: Mapping[str, Any]) -> dict[str, Any]:
    detector_updates: dict[str, Any] = {}
    risk_updates: dict[str, Any] = {}
    filter_kwargs: dict[str, Any] = {}
    entry_mode = PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT
    entry_config_kwargs: dict[str, Any] = {}
    cost_profile_name = "conservative_crypto_1m"

    for path, value in parameters.items():
        if path.startswith("detector."):
            detector_updates[path.removeprefix("detector.")] = value
        elif path.startswith("risk."):
            risk_updates[path.removeprefix("risk.")] = value
        elif path == "entry.mode":
            entry_mode = PatternEntryMode(str(value).upper().replace("-", "_"))
        elif path == "entry.trigger":
            entry_config_kwargs["entry_trigger"] = PatternEntryTrigger(str(value).upper().replace("-", "_"))
        elif path == "entry.max_wait_bars":
            entry_config_kwargs["max_wait_bars"] = None if value is None else int(value)
        elif path == "entry.expire_status":
            entry_config_kwargs["expire_status"] = PatternEntryStatus(str(value).upper().replace("-", "_"))
        elif path == "cost.profile":
            cost_profile_name = str(value).lower()
        elif path == "filter.minimum_pattern_score":
            filter_kwargs["minimum_pattern_score"] = None if value is None else float(value)
        elif path == "filter.minimum_risk_reward":
            filter_kwargs["minimum_risk_reward"] = None if value is None else float(value)

    return {
        "detector_updates": detector_updates,
        "risk_updates": risk_updates,
        "entry_mode": entry_mode,
        "entry_config": PatternEntryConfig(**entry_config_kwargs),
        "entry_filter_config": PatternEntryFilterConfig(**filter_kwargs),
        "transaction_cost_config": _cost_config(cost_profile_name),
    }


def _cost_config(profile_name: str) -> TransactionCostConfig:
    if profile_name == "zero":
        return TransactionCostConfig()
    if profile_name not in COST_PROFILES:
        raise ValueError(f"unsupported cost profile: {profile_name}")
    return cost_profile(profile_name).config


def _variant_summary(
    wfo_payload: Mapping[str, Any],
    parameters: Mapping[str, Any],
    config: FvgRetestV2ResearchProtocolConfig,
) -> dict[str, Any]:
    folds = tuple(row for row in wfo_payload.get("folds", ()) if isinstance(row, Mapping))
    aggregate = wfo_payload.get("aggregate") if isinstance(wfo_payload.get("aggregate"), Mapping) else {}
    fold_count = int(aggregate.get("fold_count") or len(folds))
    no_fill = int(aggregate.get("no_fill_fold_count") or 0)
    failures = int(aggregate.get("failure_count") or 0)
    positive_ratio = aggregate.get("positive_fold_ratio")
    no_fill_ratio = 0.0 if fold_count == 0 else no_fill / fold_count
    timing = _aggregate_timing(folds)
    weakness = _weakness_labels(aggregate, timing, parameters)
    decision = _decision(
        fold_count=fold_count,
        failures=failures,
        no_fill_ratio=no_fill_ratio,
        positive_ratio=positive_ratio,
        config=config,
    )
    return {
        "schema_version": "fvg_retest_v2_variant_summary_v1",
        "fold_count": fold_count,
        "failure_count": failures,
        "no_fill_fold_count": no_fill,
        "no_fill_fold_ratio": no_fill_ratio,
        "positive_fold_ratio": positive_ratio,
        "total_return": aggregate.get("total_return"),
        "expectancy": aggregate.get("expectancy"),
        "trade_count": aggregate.get("trade_count"),
        "max_drawdown": aggregate.get("max_drawdown"),
        "timing": timing,
        "weakness_labels": weakness,
        "research_decision": decision,
    }


def _aggregate_timing(folds: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed = 0
    mfe_values: list[float] = []
    mae_values: list[float] = []
    for fold in folds:
        diagnostics = fold.get("diagnostics")
        if not isinstance(diagnostics, Mapping):
            continue
        timing = diagnostics.get("timing_diagnostics")
        if not isinstance(timing, Mapping):
            continue
        completed += int(timing.get("completed_trade_count") or 0)
        aggregate = timing.get("aggregate")
        if not isinstance(aggregate, Mapping):
            continue
        if aggregate.get("average_mfe_r") is not None:
            mfe_values.append(float(aggregate["average_mfe_r"]))
        if aggregate.get("average_mae_r") is not None:
            mae_values.append(float(aggregate["average_mae_r"]))
    return {
        "completed_trade_count": completed,
        "average_mfe_r": _mean(mfe_values),
        "average_mae_r": _mean(mae_values),
    }


def _weakness_labels(aggregate: Mapping[str, Any], timing: Mapping[str, Any], parameters: Mapping[str, Any]) -> tuple[str, ...]:
    labels: list[str] = []
    trade_count = _distribution_mean(aggregate.get("trade_count"))
    expectancy = _distribution_mean(aggregate.get("expectancy"))
    max_drawdown = _distribution_min(aggregate.get("max_drawdown"))
    if trade_count == 0:
        labels.append("NO_FILL_RETESTS_OR_NO_COMPLETED_TRADES")
    if expectancy is not None and expectancy < 0:
        labels.append("NEGATIVE_EXPECTANCY_OR_POOR_FOLLOW_THROUGH")
    if bool(parameters.get("detector.use_multitimeframe_trend_score")) and trade_count == 0:
        labels.append("TREND_FILTER_OVERBLOCKING")
    if bool(parameters.get("risk.require_liquidity_target")) and trade_count == 0:
        labels.append("LIQUIDITY_TARGET_SCARCITY")
    if str(parameters.get("cost.profile", "")).lower() != "zero" and expectancy is not None and expectancy <= 0:
        labels.append("COST_DRAG")
    if max_drawdown is not None and max_drawdown < -0.05:
        labels.append("DRAWDOWN_PRESSURE")
    if timing.get("average_mfe_r") is not None and timing.get("average_mae_r") is not None and float(timing["average_mfe_r"]) <= abs(float(timing["average_mae_r"])):
        labels.append("ADVERSE_EXCURSION_DOMINATES_MFE")
    return tuple(labels or ("NO_DETERMINISTIC_WEAKNESS_LABEL",))


def _decision(
    *,
    fold_count: int,
    failures: int,
    no_fill_ratio: float,
    positive_ratio: Any,
    config: FvgRetestV2ResearchProtocolConfig,
) -> dict[str, Any]:
    reasons: list[str] = []
    if fold_count < config.minimum_folds_for_promotion:
        reasons.append("insufficient fold count for promotion-grade evidence")
    if failures > 0:
        reasons.append("one or more folds failed")
    if no_fill_ratio > config.maximum_no_fill_fold_ratio:
        reasons.append("no-fill fold ratio exceeds threshold")
    if positive_ratio is None or float(positive_ratio) < config.minimum_positive_fold_ratio:
        reasons.append("positive fold ratio below threshold")
    status = "RESEARCH_REJECT_OR_RETEST" if reasons else "RESEARCH_CANDIDATE_NEEDS_LOCKED_HOLDOUT"
    return {
        "status": status,
        "promotion_allowed": False,
        "reasons": tuple(reasons or ("passes preliminary WFO thresholds but remains research-only pending locked holdout",)),
    }


def _research_note(
    declaration: Mapping[str, Any],
    grid_report: Mapping[str, Any],
    variants: Sequence[Mapping[str, Any]],
    config: FvgRetestV2ResearchProtocolConfig,
) -> dict[str, Any]:
    decisions = [variant["summary"]["research_decision"]["status"] for variant in variants]
    rejected = sum(1 for status in decisions if status == "RESEARCH_REJECT_OR_RETEST")
    return {
        "schema_version": "fvg_retest_v2_research_note_v1",
        "status": "research_only",
        "promotion_allowed": False,
        "parameter_combination_count": declaration.get("combination_count"),
        "attempted_variant_count": len(variants),
        "grid_row_count": len(grid_report.get("rows", ())) if isinstance(grid_report.get("rows"), Sequence) else None,
        "rejected_or_retest_variant_count": rejected,
        "promotion_criteria": {
            "minimum_folds_for_promotion": config.minimum_folds_for_promotion,
            "minimum_positive_fold_ratio": config.minimum_positive_fold_ratio,
            "maximum_no_fill_fold_ratio": config.maximum_no_fill_fold_ratio,
            "locked_holdout_required": True,
            "realistic_cost_profile_required": config.require_realistic_cost_profile,
        },
        "rejection_criteria": (
            "repeated OOS failures",
            "no-fill retest dominance",
            "negative expectancy after realistic costs",
            "trend filter overblocking",
            "liquidity target scarcity",
            "drawdown pressure",
        ),
        "limitations": (
            "Protocol output is not paper or live approval.",
            "Holdout outcomes must not be used for post-hoc retuning.",
            "All losing and no-fill variants are retained in the report.",
        ),
    }


def _markdown(note: Mapping[str, Any]) -> str:
    lines = [
        "# FVG Retest V2 Research Protocol",
        "",
        f"- Status: {note.get('status')}",
        f"- Promotion Allowed: {note.get('promotion_allowed')}",
        f"- Attempted Variants: {note.get('attempted_variant_count')}",
        f"- Rejected/Retest Variants: {note.get('rejected_or_retest_variant_count')}",
        "",
        "## Limitations",
        *[f"- {item}" for item in note.get("limitations", ())],
    ]
    return "\n".join(lines)


def _dataset_identity(frame: pd.DataFrame) -> dict[str, Any]:
    normalized = frame.copy(deep=True)
    if "timestamp" in normalized.columns:
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
        normalized = normalized.sort_values("timestamp").reset_index(drop=True)
    columns = [column for column in ("timestamp", "open", "high", "low", "close", "volume") if column in normalized.columns]
    records = json_ready(normalized[columns].to_dict(orient="records")) if columns else ()
    return {
        "schema_version": "fvg_retest_v2_dataset_identity_v1",
        "row_count": len(normalized),
        "first_timestamp": str(normalized.iloc[0]["timestamp"]) if len(normalized) and "timestamp" in normalized.columns else None,
        "last_timestamp": str(normalized.iloc[-1]["timestamp"]) if len(normalized) and "timestamp" in normalized.columns else None,
        "content_hash": metadata_hash({"columns": columns, "records": records}),
    }


def _walk_forward_config_metadata(config: WalkForwardConfig) -> dict[str, Any]:
    return {
        "train_window": str(config.train_window),
        "test_window": str(config.test_window),
        "step_size": str(config.step_size),
        "regime_stratification_enabled": config.regime_stratification_enabled,
        "minimum_trades_per_stratum": config.minimum_trades_per_stratum,
    }


def _minimal_validation_candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01T00:00:00Z", periods=6, freq="min"),
            "open": [100.0, 100.5, 101.0, 101.5, 102.0, 102.5],
            "high": [101.0, 101.5, 102.0, 102.5, 103.0, 103.5],
            "low": [99.0, 99.5, 100.0, 100.5, 101.0, 101.5],
            "close": [100.5, 101.0, 101.5, 102.0, 102.5, 103.0],
            "volume": [100.0] * 6,
        }
    )


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _distribution_mean(value: Any) -> float | None:
    if not isinstance(value, Mapping):
        return None
    mean = value.get("mean")
    return None if mean is None else float(mean)


def _distribution_min(value: Any) -> float | None:
    if not isinstance(value, Mapping):
        return None
    minimum = value.get("min")
    return None if minimum is None else float(minimum)
