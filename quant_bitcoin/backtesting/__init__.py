"""Backtesting components."""

from quant_bitcoin.backtesting.basic import (
    BasicBacktester,
    BacktestResult,
    BacktestSummary,
    BacktestTrade,
)
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
from quant_bitcoin.backtesting.pattern_event_study import (
    PatternEventStudyDataset,
    PatternEventStudyRecord,
    PatternForwardLabel,
    PatternForwardLabelConfig,
    extract_fair_value_gap_event_study_records,
    pattern_event_to_study_record,
    records_to_dataframe,
)

from quant_bitcoin.backtesting.pattern_strategy import (
    DEFAULT_PATTERN,
    SUPPORTED_PATTERNS,
    PatternName,
    PatternStrategyBacktestConfig,
    PatternStrategyBacktestResult,
    PatternStrategyBacktestTrade,
    run_pattern_strategy_backtest,
    strategy_name_for_patterns,
    validate_pattern_selection,
)

__all__ = [
    "calculate_drawdown_series",
    "build_equity_curve_from_trades",
    "EquityCurveResult",
    "EquityCurvePoint",
    "EquityCurveConfig",
    "DEFAULT_PATTERN",
    "PatternEventStudyDataset",
    "PatternEventStudyRecord",
    "PatternForwardLabel",
    "PatternForwardLabelConfig",
    "ExecutionSide",
    "LiquidityRole",
    "TransactionCostBreakdown",
    "TransactionCostConfig",
    "SUPPORTED_PATTERNS",
    "BasicBacktester",
    "BacktestResult",
    "BacktestSummary",
    "BacktestTrade",
    "PatternName",
    "PatternStrategyBacktestConfig",
    "PatternStrategyBacktestResult",
    "PatternStrategyBacktestTrade",
    "basis_points_to_decimal",
    "calculate_transaction_cost",
    "effective_execution_price",
    "extract_fair_value_gap_event_study_records",
    "pattern_event_to_study_record",
    "records_to_dataframe",
    "run_pattern_strategy_backtest",
    "strategy_name_for_patterns",
    "validate_pattern_selection",
]
