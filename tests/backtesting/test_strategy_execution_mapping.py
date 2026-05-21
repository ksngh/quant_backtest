from quant_bitcoin.backtesting.strategy_execution_mapping import (
    ExecutionSide,
    map_long_only_action_to_execution_side,
)
from quant_bitcoin.strategies.actions import StrategyActionType


def test_long_only_mapping_enter_maps_to_buy() -> None:
    assert map_long_only_action_to_execution_side(StrategyActionType.ENTER_LONG) == ExecutionSide.BUY


def test_long_only_mapping_exit_maps_to_sell() -> None:
    assert map_long_only_action_to_execution_side(StrategyActionType.EXIT_LONG) == ExecutionSide.SELL


def test_long_only_mapping_partial_exit_maps_to_sell() -> None:
    assert (
        map_long_only_action_to_execution_side(StrategyActionType.PARTIAL_EXIT_LONG)
        == ExecutionSide.SELL
    )


def test_long_only_mapping_skip_maps_to_none() -> None:
    assert map_long_only_action_to_execution_side(StrategyActionType.SKIP) is None
