"""Backtesting components."""

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
from quant_bitcoin.backtesting.walk_forward import (
    WalkForwardConfig,
    WalkForwardFold,
    aggregate_fold_metrics,
    build_rsi_action_builder,
    generate_walk_forward_folds,
    monte_carlo_trade_return_bootstrap,
    run_walk_forward_validation,
)

from quant_bitcoin.backtesting.pattern_event_study import (
    PatternEventStudyDataset,
    PatternEventStudyRecord,
    PatternForwardLabel,
    PatternForwardLabelConfig,
    extract_fair_value_gap_event_study_records,
    pattern_event_to_study_record,
    records_to_dataframe,
)

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
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
    "WalkForwardConfig",
    "WalkForwardFold",
    "aggregate_fold_metrics",
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
    "ShortExposureMode",
    "SimulatedMarginConfig",
    "run_strategy_backtest_engine",
    "StrategyBacktestResult",
    "StrategyBacktestSummary",
    "StrategyEquityPoint",
    "StrategyExecution",
]
