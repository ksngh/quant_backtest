"""Strategy semantic-to-execution side mapping helpers.

This module defines the explicit boundary between strategy semantics and
execution/accounting sides for deterministic backtest cashflow processing.
"""

from __future__ import annotations

from enum import Enum

from quant_bitcoin.strategies.actions import StrategyActionType


class ExecutionSide(Enum):
    """Execution/accounting-side directions for portfolio cashflow."""

    BUY = "BUY"
    SELL = "SELL"


def map_long_only_action_to_execution_side(
    action_type: StrategyActionType,
) -> ExecutionSide | None:
    """Map strategy semantic actions to long-only execution sides.

    Returns ``None`` for semantic actions that do not create an execution fill,
    such as ``SKIP``.
    """

    if action_type == StrategyActionType.ENTER_LONG:
        return ExecutionSide.BUY
    if action_type in (
        StrategyActionType.EXIT_LONG,
        StrategyActionType.PARTIAL_EXIT_LONG,
    ):
        return ExecutionSide.SELL
    if action_type == StrategyActionType.SKIP:
        return None
    raise ValueError(f"unsupported action_type: {action_type}")
