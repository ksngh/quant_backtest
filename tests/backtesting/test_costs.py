import math

import pytest

from quant_bitcoin.backtesting.costs import (
    ExecutionSide,
    LiquidityRole,
    TransactionCostConfig,
    basis_points_to_decimal,
    calculate_transaction_cost,
    effective_execution_price,
    is_zero_transaction_cost_config,
    transaction_cost_profile_metadata,
)


def test_basis_points_to_decimal_converts() -> None:
    assert basis_points_to_decimal(10.0) == pytest.approx(0.001)


def test_zero_cost_assumption_and_profile_metadata() -> None:
    assert is_zero_transaction_cost_config(None) is True
    assert is_zero_transaction_cost_config(TransactionCostConfig()) is True
    assert is_zero_transaction_cost_config(TransactionCostConfig(taker_fee_bps=1.0)) is False

    metadata = transaction_cost_profile_metadata(None)

    assert metadata["schema_version"] == "transaction_cost_profile_v1"
    assert metadata["profile_key"] == "zero"
    assert metadata["zero_cost_profile"] is True
    assert metadata["source"] == "implicit_zero_default"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"maker_fee_bps": -0.1},
        {"taker_fee_bps": -0.1},
        {"spread_bps": -0.1},
        {"slippage_bps": -0.1},
        {"volatility_slippage_multiplier": -0.1},
        {"minimum_slippage_bps": -0.1},
        {"maker_fee_bps": math.inf},
        {"taker_fee_bps": math.nan},
    ],
)
def test_transaction_cost_config_rejects_negative_or_non_finite(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        TransactionCostConfig(**kwargs)


def test_effective_price_buy_increases_and_sell_decreases() -> None:
    config = TransactionCostConfig(spread_bps=5.0, slippage_bps=7.0)

    buy = effective_execution_price(
        price=100.0,
        side=ExecutionSide.BUY,
        liquidity_role=LiquidityRole.TAKER,
        config=config,
    )
    sell = effective_execution_price(
        price=100.0,
        side=ExecutionSide.SELL,
        liquidity_role=LiquidityRole.TAKER,
        config=config,
    )

    assert buy > 100.0
    assert sell < 100.0
    assert buy == pytest.approx(100.12)
    assert sell == pytest.approx(99.88)


def test_calculate_transaction_cost_breakdown_and_maker_taker_fees() -> None:
    config = TransactionCostConfig(
        maker_fee_bps=5.0,
        taker_fee_bps=10.0,
        spread_bps=2.0,
        slippage_bps=3.0,
    )

    maker = calculate_transaction_cost(
        price=200.0,
        quantity=2.0,
        side=ExecutionSide.BUY,
        liquidity_role=LiquidityRole.MAKER,
        config=config,
    )
    taker = calculate_transaction_cost(
        price=200.0,
        quantity=2.0,
        side=ExecutionSide.BUY,
        liquidity_role=LiquidityRole.TAKER,
        config=config,
    )

    assert maker.gross_notional == pytest.approx(400.0)
    assert maker.fee_cost == pytest.approx(0.2)
    assert maker.spread_cost == pytest.approx(0.08)
    assert maker.slippage_cost == pytest.approx(0.12)
    assert maker.total_cost == pytest.approx(0.4)
    assert maker.effective_price == pytest.approx(200.1)

    assert taker.fee_cost == pytest.approx(0.4)
    assert taker.total_cost > maker.total_cost


def test_volatility_adjusted_slippage_and_floor() -> None:
    config = TransactionCostConfig(
        slippage_bps=2.0,
        volatility_slippage_multiplier=0.5,
        minimum_slippage_bps=4.0,
    )

    base = calculate_transaction_cost(
        price=100.0,
        quantity=1.0,
        side=ExecutionSide.SELL,
        liquidity_role=LiquidityRole.MAKER,
        config=config,
    )
    adjusted = calculate_transaction_cost(
        price=100.0,
        quantity=1.0,
        side=ExecutionSide.SELL,
        liquidity_role=LiquidityRole.MAKER,
        config=config,
        volatility_bps=10.0,
    )

    assert base.slippage_cost == pytest.approx(0.04)
    assert adjusted.slippage_cost == pytest.approx(0.07)
    assert adjusted.effective_slippage_bps == pytest.approx(7.0)
    assert adjusted.volatility_bps == pytest.approx(10.0)


def test_positive_price_and_quantity_required() -> None:
    config = TransactionCostConfig()

    with pytest.raises(ValueError):
        calculate_transaction_cost(
            price=0.0,
            quantity=1.0,
            side=ExecutionSide.BUY,
            liquidity_role=LiquidityRole.MAKER,
            config=config,
        )

    with pytest.raises(ValueError):
        calculate_transaction_cost(
            price=100.0,
            quantity=0.0,
            side=ExecutionSide.BUY,
            liquidity_role=LiquidityRole.MAKER,
            config=config,
        )
