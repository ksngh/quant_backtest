"""Backtesting components."""

import importlib

from quant_bitcoin.backtesting.equity_curve import (
    EquityCurveConfig,
    EquityCurvePoint,
    EquityCurveResult,
    build_equity_curve_from_trades,
    calculate_drawdown_series,
)
from quant_bitcoin.backtesting.costs import (
    ExecutionSide,
    LiquidityRole,
    TransactionCostBreakdown,
    TransactionCostConfig,
    basis_points_to_decimal,
    calculate_transaction_cost,
    effective_execution_price,
)
from quant_bitcoin.backtesting.multiple_testing import (
    benjamini_hochberg_thresholds,
    bonferroni_threshold,
    count_strategy_variants,
)
from quant_bitcoin.backtesting.performance_metrics import calculate_trade_attribution_metrics
from quant_bitcoin.backtesting.performance_diagnostics import calculate_backtest_performance_diagnostics
from quant_bitcoin.backtesting.timing_diagnostics import calculate_trade_timing_diagnostics
from quant_bitcoin.backtesting.risk_exit_audit import calculate_risk_exit_audit
from quant_bitcoin.backtesting.pattern_event_study import (
    PatternEventStudyDataset,
    PatternEventStudyRecord,
    PatternForwardLabel,
    PatternForwardLabelConfig,
    extract_fair_value_gap_event_study_records,
    pattern_event_to_study_record,
    records_to_dataframe,
)

_LAZY_WALK_FORWARD_EXPORTS = {
    "WalkForwardConfig",
    "WalkForwardFold",
    "aggregate_fold_metrics",
    "build_pattern_action_builder",
    "build_rsi_action_builder",
    "generate_walk_forward_folds",
    "monte_carlo_trade_return_bootstrap",
    "run_walk_forward_validation",
}


def __getattr__(name: str):
    if name in _LAZY_WALK_FORWARD_EXPORTS:
        walk_forward = importlib.import_module("quant_bitcoin.backtesting.walk_forward")
        value = getattr(walk_forward, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    SizingRiskSource,
    ShortEconomicsConfig,
    ShortExposureMode,
    SimulatedMarginConfig,
)
from quant_bitcoin.backtesting.strategy_models import (
    StrategyBacktestResult,
    StrategyBacktestSummary,
    StrategyEquityPoint,
    StrategyExecution,
)


__all__ = [
    "calculate_drawdown_series",
    "build_equity_curve_from_trades",
    "EquityCurveResult",
    "EquityCurvePoint",
    "EquityCurveConfig",
    "PatternEventStudyDataset",
    "PatternEventStudyRecord",
    "PatternForwardLabel",
    "PatternForwardLabelConfig",
    "ExecutionSide",
    "LiquidityRole",
    "TransactionCostBreakdown",
    "TransactionCostConfig",
    "benjamini_hochberg_thresholds",
    "bonferroni_threshold",
    "count_strategy_variants",
    "basis_points_to_decimal",
    "calculate_transaction_cost",
    "effective_execution_price",
    "calculate_trade_attribution_metrics",
    "calculate_backtest_performance_diagnostics",
    "calculate_trade_timing_diagnostics",
    "calculate_risk_exit_audit",
    "WalkForwardConfig",
    "WalkForwardFold",
    "aggregate_fold_metrics",
    "build_pattern_action_builder",
    "build_rsi_action_builder",
    "generate_walk_forward_folds",
    "monte_carlo_trade_return_bootstrap",
    "run_walk_forward_validation",
    "extract_fair_value_gap_event_study_records",
    "pattern_event_to_study_record",
    "records_to_dataframe",
    "StrategyEngineConfig",
    "BacktestGuardrailConfig",
    "InsufficientFundsPolicy",
    "PositionSizingConfig",
    "PositionSizingMode",
    "SizingRiskSource",
    "ShortEconomicsConfig",
    "ShortExposureMode",
    "SimulatedMarginConfig",
    "run_strategy_backtest_engine",
    "StrategyBacktestResult",
    "StrategyBacktestSummary",
    "StrategyEquityPoint",
    "StrategyExecution",
]
