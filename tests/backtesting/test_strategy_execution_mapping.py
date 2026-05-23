from quant_bitcoin.strategies.actions import (
    StrategyActionType,
    execution_side_for_action,
    position_signal_for_action,
    position_side_for_action,
)


def test_execution_side_mapping_long_actions() -> None:
    assert execution_side_for_action(StrategyActionType.ENTER_LONG) == "BUY"
    assert execution_side_for_action(StrategyActionType.EXIT_LONG) == "SELL"
    assert execution_side_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "SELL"


def test_execution_side_mapping_short_actions() -> None:
    assert execution_side_for_action(StrategyActionType.ENTER_SHORT) == "SELL"
    assert execution_side_for_action(StrategyActionType.EXIT_SHORT) == "BUY"
    assert execution_side_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "BUY"


def test_execution_side_mapping_skip_maps_to_none() -> None:
    assert execution_side_for_action(StrategyActionType.SKIP) is None


def test_position_side_mapping_long_short_and_skip() -> None:
    assert position_side_for_action(StrategyActionType.ENTER_LONG) == "LONG"
    assert position_side_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "LONG"
    assert position_side_for_action(StrategyActionType.ENTER_SHORT) == "SHORT"
    assert position_side_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "SHORT"
    assert position_side_for_action(StrategyActionType.SKIP) is None


def test_position_signal_mapping_distinguishes_position_lifecycle() -> None:
    assert position_signal_for_action(StrategyActionType.ENTER_LONG) == "LONG_ENTRY"
    assert position_signal_for_action(StrategyActionType.EXIT_LONG) == "LONG_EXIT"
    assert position_signal_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "LONG_PARTIAL_EXIT"
    assert position_signal_for_action(StrategyActionType.ENTER_SHORT) == "SHORT_ENTRY"
    assert position_signal_for_action(StrategyActionType.EXIT_SHORT) == "SHORT_EXIT"
    assert position_signal_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "SHORT_PARTIAL_EXIT"
    assert position_signal_for_action(StrategyActionType.SKIP) is None
