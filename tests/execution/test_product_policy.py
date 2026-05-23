from __future__ import annotations

from quant_bitcoin.execution import (
    SHORT_NOT_SUPPORTED_FOR_SPOT,
    ProductMode,
    evaluate_product_policy,
    order_intent_from_strategy_action,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _intent(action_type: StrategyActionType):
    return order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(action_type, timestamp=1, quantity=1, requested_price=100),
    )


def test_spot_product_policy_blocks_enter_short() -> None:
    decision = evaluate_product_policy(
        _intent(StrategyActionType.ENTER_SHORT),
        product_mode=ProductMode.SPOT_PAPER,
    )

    assert decision.allowed is False
    assert decision.reason == SHORT_NOT_SUPPORTED_FOR_SPOT


def test_spot_product_policy_blocks_exit_short_without_simulation_context() -> None:
    decision = evaluate_product_policy(
        _intent(StrategyActionType.EXIT_SHORT),
        product_mode=ProductMode.SPOT_TESTNET,
    )

    assert decision.allowed is False
    assert decision.reason == SHORT_NOT_SUPPORTED_FOR_SPOT


def test_backtest_simulation_policy_allows_enter_short() -> None:
    decision = evaluate_product_policy(
        _intent(StrategyActionType.ENTER_SHORT),
        product_mode=ProductMode.BACKTEST_SIMULATION,
    )

    assert decision.allowed is True
    assert decision.reason is None


def test_policy_metadata_includes_short_model_limitations() -> None:
    decision = evaluate_product_policy(
        _intent(StrategyActionType.ENTER_SHORT),
        product_mode=ProductMode.BACKTEST_SIMULATION,
    )

    assert decision.metadata is not None
    assert decision.metadata["short_model_limitations"] == [
        "No borrow fees modeled",
        "No futures funding modeled",
        "No maintenance margin or liquidation model",
    ]
