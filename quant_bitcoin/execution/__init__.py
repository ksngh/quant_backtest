"""Execution-simulation components."""

from quant_bitcoin.execution.order_intent import (
    ExecutionFill,
    ExecutionReport,
    OrderIntent,
    order_intent_from_strategy_action,
)
from quant_bitcoin.execution.binance_spot_testnet import (
    BINANCE_SPOT_TESTNET_BASE_URL,
    BinanceSpotTestnetExecutionClient,
    BinanceTestnetExecutionError,
    sign_query_string,
)
from quant_bitcoin.execution.paper_execution import (
    PaperExecutionClient,
)
from quant_bitcoin.execution.paper_trader import PaperTrade, PaperTrader
from quant_bitcoin.execution.product_policy import (
    SHORT_NOT_SUPPORTED_FOR_SPOT,
    ProductMode,
    ProductPolicyDecision,
    evaluate_product_policy,
)
from quant_bitcoin.execution.reconciliation import (
    ExecutionQualityMetrics,
    calculate_fill_vwap,
    calculate_side_aware_slippage_bps,
    reconcile_execution_report,
)
from quant_bitcoin.execution.realtime_runner import (
    RealtimeCandleCloseRunner,
    RealtimeRunnerOutput,
)

__all__ = [
    "ExecutionFill",
    "ExecutionQualityMetrics",
    "ExecutionReport",
    "OrderIntent",
    "BINANCE_SPOT_TESTNET_BASE_URL",
    "BinanceSpotTestnetExecutionClient",
    "BinanceTestnetExecutionError",
    "PaperExecutionClient",
    "PaperTrade",
    "PaperTrader",
    "ProductMode",
    "ProductPolicyDecision",
    "RealtimeCandleCloseRunner",
    "RealtimeRunnerOutput",
    "SHORT_NOT_SUPPORTED_FOR_SPOT",
    "evaluate_product_policy",
    "calculate_fill_vwap",
    "calculate_side_aware_slippage_bps",
    "order_intent_from_strategy_action",
    "reconcile_execution_report",
    "sign_query_string",
]
