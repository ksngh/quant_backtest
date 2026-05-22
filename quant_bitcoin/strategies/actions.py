"""Canonical strategy semantic-action contracts.

This module defines research-semantic actions that strategies emit before
execution/accounting conversion. It does not perform trading, persistence, or
exchange communication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StrategyActionType(Enum):
    """Canonical strategy-level semantic actions."""

    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    PARTIAL_EXIT_LONG = "PARTIAL_EXIT_LONG"
    PARTIAL_EXIT_SHORT = "PARTIAL_EXIT_SHORT"
    SKIP = "SKIP"


def is_entry_action(action_type: StrategyActionType) -> bool:
    return action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT)


def is_exit_action(action_type: StrategyActionType) -> bool:
    return action_type in (
        StrategyActionType.EXIT_LONG,
        StrategyActionType.PARTIAL_EXIT_LONG,
        StrategyActionType.EXIT_SHORT,
        StrategyActionType.PARTIAL_EXIT_SHORT,
    )


def position_side_for_action(action_type: StrategyActionType) -> str | None:
    if action_type in (
        StrategyActionType.ENTER_LONG,
        StrategyActionType.EXIT_LONG,
        StrategyActionType.PARTIAL_EXIT_LONG,
    ):
        return "LONG"
    if action_type in (
        StrategyActionType.ENTER_SHORT,
        StrategyActionType.EXIT_SHORT,
        StrategyActionType.PARTIAL_EXIT_SHORT,
    ):
        return "SHORT"
    return None


def execution_side_for_action(action_type: StrategyActionType) -> str | None:
    if action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.EXIT_SHORT, StrategyActionType.PARTIAL_EXIT_SHORT):
        return "BUY"
    if action_type in (StrategyActionType.ENTER_SHORT, StrategyActionType.EXIT_LONG, StrategyActionType.PARTIAL_EXIT_LONG):
        return "SELL"
    return None


@dataclass(frozen=True)
class StrategyAction:
    """A semantic strategy action emitted by research logic."""

    action_type: StrategyActionType
    timestamp: Any
    quantity: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    requested_price: float | None = None
