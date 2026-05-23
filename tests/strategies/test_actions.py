from quant_bitcoin.strategies.actions import (
    StrategyActionType,
    execution_side_for_action,
    is_entry_action,
    is_exit_action,
    position_signal_for_action,
    position_side_for_action,
)


def test_strategy_action_type_includes_long_and_short_actions() -> None:
    assert StrategyActionType.ENTER_LONG.value == "ENTER_LONG"
    assert StrategyActionType.EXIT_LONG.value == "EXIT_LONG"
    assert StrategyActionType.PARTIAL_EXIT_LONG.value == "PARTIAL_EXIT_LONG"
    assert StrategyActionType.ENTER_SHORT.value == "ENTER_SHORT"
    assert StrategyActionType.EXIT_SHORT.value == "EXIT_SHORT"
    assert StrategyActionType.PARTIAL_EXIT_SHORT.value == "PARTIAL_EXIT_SHORT"
    assert StrategyActionType.SKIP.value == "SKIP"


def test_entry_and_exit_classification() -> None:
    assert is_entry_action(StrategyActionType.ENTER_LONG)
    assert is_entry_action(StrategyActionType.ENTER_SHORT)
    assert not is_entry_action(StrategyActionType.SKIP)

    assert is_exit_action(StrategyActionType.EXIT_LONG)
    assert is_exit_action(StrategyActionType.PARTIAL_EXIT_LONG)
    assert is_exit_action(StrategyActionType.EXIT_SHORT)
    assert is_exit_action(StrategyActionType.PARTIAL_EXIT_SHORT)
    assert not is_exit_action(StrategyActionType.SKIP)


def test_position_and_execution_side_mappings() -> None:
    assert position_side_for_action(StrategyActionType.ENTER_LONG) == "LONG"
    assert position_side_for_action(StrategyActionType.EXIT_LONG) == "LONG"
    assert position_side_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "LONG"

    assert position_side_for_action(StrategyActionType.ENTER_SHORT) == "SHORT"
    assert position_side_for_action(StrategyActionType.EXIT_SHORT) == "SHORT"
    assert position_side_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "SHORT"

    assert execution_side_for_action(StrategyActionType.ENTER_LONG) == "BUY"
    assert execution_side_for_action(StrategyActionType.EXIT_LONG) == "SELL"
    assert execution_side_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "SELL"

    assert execution_side_for_action(StrategyActionType.ENTER_SHORT) == "SELL"
    assert execution_side_for_action(StrategyActionType.EXIT_SHORT) == "BUY"
    assert execution_side_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "BUY"

    assert position_side_for_action(StrategyActionType.SKIP) is None
    assert execution_side_for_action(StrategyActionType.SKIP) is None


def test_position_signal_mapping_long_short_and_partial_actions() -> None:
    assert position_signal_for_action(StrategyActionType.ENTER_LONG) == "LONG_ENTRY"
    assert position_signal_for_action(StrategyActionType.EXIT_LONG) == "LONG_EXIT"
    assert position_signal_for_action(StrategyActionType.PARTIAL_EXIT_LONG) == "LONG_PARTIAL_EXIT"
    assert position_signal_for_action(StrategyActionType.ENTER_SHORT) == "SHORT_ENTRY"
    assert position_signal_for_action(StrategyActionType.EXIT_SHORT) == "SHORT_EXIT"
    assert position_signal_for_action(StrategyActionType.PARTIAL_EXIT_SHORT) == "SHORT_PARTIAL_EXIT"
    assert position_signal_for_action(StrategyActionType.SKIP) is None
