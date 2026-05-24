"""Backtest-only position sizing and simulated-margin policy models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class PositionSizingMode(Enum):
    FIXED_QUANTITY = "FIXED_QUANTITY"
    CASH_FRACTION = "CASH_FRACTION"
    TARGET_NOTIONAL = "TARGET_NOTIONAL"
    EQUITY_RISK_FRACTION = "EQUITY_RISK_FRACTION"


class InsufficientFundsPolicy(Enum):
    RESIZE = "RESIZE"
    BLOCK = "BLOCK"


class ShortExposureMode(Enum):
    CASH_BOUNDED = "CASH_BOUNDED"
    SIMULATED_MARGIN = "SIMULATED_MARGIN"


@dataclass(frozen=True)
class PositionSizingConfig:
    mode: PositionSizingMode = PositionSizingMode.FIXED_QUANTITY
    value: float | None = None
    insufficient_funds_policy: InsufficientFundsPolicy = InsufficientFundsPolicy.RESIZE

    def __post_init__(self) -> None:
        mode = _coerce_enum(self.mode, PositionSizingMode, "mode")
        policy = _coerce_enum(
            self.insufficient_funds_policy,
            InsufficientFundsPolicy,
            "insufficient_funds_policy",
        )
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "insufficient_funds_policy", policy)
        if mode is PositionSizingMode.FIXED_QUANTITY:
            if self.value is not None:
                _validate_positive_finite(self.value, "fixed quantity sizing value")
            return
        if self.value is None:
            raise ValueError(f"{mode.value} sizing requires value")
        if mode in (PositionSizingMode.CASH_FRACTION, PositionSizingMode.EQUITY_RISK_FRACTION):
            _validate_positive_finite(self.value, mode.value.lower())
            if float(self.value) > 1.0:
                raise ValueError(f"{mode.value} value must be <= 1.0")
            return
        if mode is PositionSizingMode.TARGET_NOTIONAL:
            _validate_positive_finite(self.value, "target notional")

    def to_metadata(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "value": self.value,
            "insufficient_funds_policy": self.insufficient_funds_policy.value,
            "action_quantity_precedence": "action.quantity overrides engine sizing when provided",
        }


@dataclass(frozen=True)
class BacktestGuardrailConfig:
    """Backtest-only portfolio guardrails checked before new entries."""

    max_account_drawdown: float | None = None
    max_consecutive_losses: int | None = None
    max_daily_loss: float | None = None

    def __post_init__(self) -> None:
        if self.max_account_drawdown is not None:
            _validate_positive_finite(self.max_account_drawdown, "max_account_drawdown")
            if float(self.max_account_drawdown) > 1.0:
                raise ValueError("max_account_drawdown must be <= 1.0")
        if self.max_consecutive_losses is not None:
            if not isinstance(self.max_consecutive_losses, int) or self.max_consecutive_losses < 1:
                raise ValueError("max_consecutive_losses must be a positive integer")
        if self.max_daily_loss is not None:
            _validate_positive_finite(self.max_daily_loss, "max_daily_loss")

    def to_metadata(self) -> dict[str, object]:
        return {
            "scope": "backtest_only",
            "max_account_drawdown": self.max_account_drawdown,
            "max_consecutive_losses": self.max_consecutive_losses,
            "max_daily_loss": self.max_daily_loss,
        }


@dataclass(frozen=True)
class SimulatedMarginConfig:
    enabled: bool = False
    leverage: float = 1.0
    insufficient_margin_policy: InsufficientFundsPolicy = InsufficientFundsPolicy.BLOCK

    def __post_init__(self) -> None:
        policy = _coerce_enum(
            self.insufficient_margin_policy,
            InsufficientFundsPolicy,
            "insufficient_margin_policy",
        )
        object.__setattr__(self, "insufficient_margin_policy", policy)
        _validate_positive_finite(self.leverage, "leverage")
        if float(self.leverage) < 1.0:
            raise ValueError("leverage must be >= 1.0")

    def required_initial_margin(self, notional: float) -> float:
        _validate_non_negative_finite(notional, "notional")
        return float(notional) / float(self.leverage)

    def to_metadata(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "leverage": float(self.leverage),
            "insufficient_margin_policy": self.insufficient_margin_policy.value,
            "scope": "backtest_only",
            "unsupported_economics": [
                "No borrow fees modeled",
                "No futures funding modeled",
                "No maintenance margin or liquidation model",
            ],
        }


def _coerce_enum(value, enum_type, name: str):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value).upper())
    except ValueError as exc:
        valid = ", ".join(member.value for member in enum_type)
        raise ValueError(f"{name} must be one of: {valid}") from exc


def _validate_positive_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    if float(value) <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_non_negative_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    if float(value) < 0:
        raise ValueError(f"{name} must be non-negative")
