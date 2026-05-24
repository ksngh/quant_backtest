"""Deterministic transaction-cost helpers for historical backtests.

This module is pure and side-effect free. It models a small reusable execution
cost contract (fees, spread, and slippage) for simulation-only backtest paths.
It does not call exchanges, place orders, load data, or mutate caller inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class ExecutionSide(Enum):
    """Execution side for a simulated trade."""

    BUY = "BUY"
    SELL = "SELL"


class LiquidityRole(Enum):
    """Liquidity role used for fee selection."""

    MAKER = "MAKER"
    TAKER = "TAKER"


@dataclass(frozen=True)
class TransactionCostConfig:
    """Configuration values expressed in basis points."""

    maker_fee_bps: float = 0.0
    taker_fee_bps: float = 0.0
    spread_bps: float = 0.0
    slippage_bps: float = 0.0
    volatility_slippage_multiplier: float = 0.0
    minimum_slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        _validate_non_negative_finite(self.maker_fee_bps, "maker_fee_bps")
        _validate_non_negative_finite(self.taker_fee_bps, "taker_fee_bps")
        _validate_non_negative_finite(self.spread_bps, "spread_bps")
        _validate_non_negative_finite(self.slippage_bps, "slippage_bps")
        _validate_non_negative_finite(
            self.volatility_slippage_multiplier,
            "volatility_slippage_multiplier",
        )
        _validate_non_negative_finite(self.minimum_slippage_bps, "minimum_slippage_bps")


@dataclass(frozen=True)
class TransactionCostBreakdown:
    """Gross and cost components for one deterministic simulated execution."""

    gross_notional: float
    fee_cost: float
    spread_cost: float
    slippage_cost: float
    total_cost: float
    effective_price: float
    effective_slippage_bps: float = 0.0
    volatility_bps: float | None = None


def basis_points_to_decimal(value_bps: float) -> float:
    """Convert basis points to decimal fraction.

    Example: 10 bps -> 0.001.
    """

    if not isinstance(value_bps, (int, float)) or not math.isfinite(float(value_bps)):
        raise ValueError("basis points value must be a finite number")
    return float(value_bps) / 10_000.0


def effective_execution_price(
    price: float,
    side: ExecutionSide,
    liquidity_role: LiquidityRole,
    config: TransactionCostConfig,
    volatility_bps: float | None = None,
) -> float:
    """Return side-aware effective execution price including spread and slippage."""

    _validate_positive_finite(price, "price")
    _validate_inputs(side, liquidity_role, config, volatility_bps)

    spread_decimal = basis_points_to_decimal(config.spread_bps)
    slippage_decimal = basis_points_to_decimal(
        _effective_slippage_bps(config, volatility_bps)
    )
    price_multiplier = 1.0 + spread_decimal + slippage_decimal

    if side is ExecutionSide.BUY:
        return float(price) * price_multiplier
    return float(price) * (1.0 - spread_decimal - slippage_decimal)


def calculate_transaction_cost(
    price: float,
    quantity: float,
    side: ExecutionSide,
    liquidity_role: LiquidityRole,
    config: TransactionCostConfig,
    volatility_bps: float | None = None,
) -> TransactionCostBreakdown:
    """Calculate deterministic execution-cost components for one simulated trade."""

    _validate_positive_finite(price, "price")
    _validate_positive_finite(quantity, "quantity")
    _validate_inputs(side, liquidity_role, config, volatility_bps)

    gross_notional = float(price) * float(quantity)
    effective_slippage_bps = _effective_slippage_bps(config, volatility_bps)
    spread_cost = gross_notional * basis_points_to_decimal(config.spread_bps)
    slippage_cost = gross_notional * basis_points_to_decimal(effective_slippage_bps)

    fee_bps = config.maker_fee_bps if liquidity_role is LiquidityRole.MAKER else config.taker_fee_bps
    fee_cost = gross_notional * basis_points_to_decimal(fee_bps)

    total_cost = fee_cost + spread_cost + slippage_cost
    effective_price = effective_execution_price(
        price=float(price),
        side=side,
        liquidity_role=liquidity_role,
        config=config,
        volatility_bps=volatility_bps,
    )

    return TransactionCostBreakdown(
        gross_notional=gross_notional,
        fee_cost=fee_cost,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        total_cost=total_cost,
        effective_price=effective_price,
        effective_slippage_bps=effective_slippage_bps,
        volatility_bps=volatility_bps,
    )


def _effective_slippage_bps(
    config: TransactionCostConfig,
    volatility_bps: float | None,
) -> float:
    if volatility_bps is None:
        return max(config.slippage_bps, config.minimum_slippage_bps)

    adjusted = config.slippage_bps + (
        float(volatility_bps) * config.volatility_slippage_multiplier
    )
    return max(config.minimum_slippage_bps, adjusted)


def _validate_non_negative_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    if float(value) < 0:
        raise ValueError(f"{name} must be non-negative")


def _validate_positive_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    if float(value) <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_inputs(
    side: ExecutionSide,
    liquidity_role: LiquidityRole,
    config: TransactionCostConfig,
    volatility_bps: float | None,
) -> None:
    if not isinstance(side, ExecutionSide):
        raise ValueError("side must be an ExecutionSide")
    if not isinstance(liquidity_role, LiquidityRole):
        raise ValueError("liquidity_role must be a LiquidityRole")
    if not isinstance(config, TransactionCostConfig):
        raise ValueError("config must be a TransactionCostConfig")
    if volatility_bps is not None:
        _validate_non_negative_finite(volatility_bps, "volatility_bps")
