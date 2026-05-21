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
    EXIT_LONG = "EXIT_LONG"
    PARTIAL_EXIT_LONG = "PARTIAL_EXIT_LONG"
    SKIP = "SKIP"


@dataclass(frozen=True)
class StrategyAction:
    """A semantic strategy action emitted by research logic."""

    action_type: StrategyActionType
    timestamp: Any
    quantity: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
