from __future__ import annotations

import socket

import pytest

from quant_bitcoin.execution import (
    SHORT_NOT_SUPPORTED_FOR_SPOT,
    PaperExecutionClient,
    order_intent_from_strategy_action,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


@pytest.mark.parametrize(
    ("action_type", "position_side", "execution_side"),
    [
        (StrategyActionType.ENTER_LONG, "LONG", "BUY"),
        (StrategyActionType.EXIT_LONG, "LONG", "SELL"),
        (StrategyActionType.ENTER_SHORT, "SHORT", "SELL"),
        (StrategyActionType.EXIT_SHORT, "SHORT", "BUY"),
    ],
)
def test_strategy_action_maps_to_order_intent(action_type, position_side, execution_side) -> None:
    action = StrategyAction(
        action_type,
        timestamp=123,
        quantity=0.5,
        requested_price=100.0,
        metadata={"pattern_event_id": "event-1"},
    )

    intent = order_intent_from_strategy_action(symbol=" btcusdt ", action=action)

    assert intent.symbol == "BTCUSDT"
    assert intent.action_type == action_type.value
    assert intent.position_side == position_side
    assert intent.execution_side == execution_side
    assert intent.quantity == 0.5
    assert intent.reference_price == 100.0
    assert intent.client_order_id is not None


def test_order_intent_client_order_id_is_deterministic() -> None:
    action = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=123,
        quantity=1.0,
        requested_price=100.0,
    )

    first = order_intent_from_strategy_action(symbol="BTCUSDT", action=action)
    second = order_intent_from_strategy_action(symbol="BTCUSDT", action=action)

    assert first.intent_id == second.intent_id
    assert first.client_order_id == second.client_order_id


def test_paper_execution_long_entry_and_exit() -> None:
    client = PaperExecutionClient(cash_balance=1000)
    entry = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=2, requested_price=100),
    )
    exit_ = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=2, requested_price=110),
    )

    entry_report = client.execute_order_intent(entry)
    exit_report = client.execute_order_intent(exit_)

    assert entry_report.status == "FILLED"
    assert exit_report.status == "FILLED"
    assert client.cash_balance == 1020
    assert client.positions == {}
    assert [report.action_type for report in client.reports] == ["ENTER_LONG", "EXIT_LONG"]


def test_paper_execution_short_entry_and_exit_in_simulation_mode() -> None:
    client = PaperExecutionClient(cash_balance=1000, allow_simulated_shorts=True)
    entry = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1, requested_price=100),
    )
    exit_ = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=2, quantity=1, requested_price=90),
    )

    assert client.execute_order_intent(entry).status == "FILLED"
    assert client.positions == {"BTCUSDT": -1.0}
    assert client.execute_order_intent(exit_).status == "FILLED"
    assert client.cash_balance == 1010
    assert client.positions == {}


def test_spot_like_paper_mode_blocks_short_entry() -> None:
    client = PaperExecutionClient(cash_balance=1000)
    intent = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1, requested_price=100),
    )

    report = client.execute_order_intent(intent)

    assert report.status == "REJECTED"
    assert report.reason == SHORT_NOT_SUPPORTED_FOR_SPOT
    assert report.metadata["short_model_limitations"] == [
        "No borrow fees modeled",
        "No futures funding modeled",
        "No maintenance margin or liquidation model",
    ]
    assert client.positions == {}
    assert client.cash_balance == 1000


def test_spot_like_paper_mode_blocks_short_exit() -> None:
    client = PaperExecutionClient(cash_balance=1000)
    intent = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=1, quantity=1, requested_price=100),
    )

    report = client.execute_order_intent(intent)

    assert report.status == "REJECTED"
    assert report.reason == SHORT_NOT_SUPPORTED_FOR_SPOT
    assert report.execution_side == "BUY"


def test_dry_run_returns_report_without_mutating_balances() -> None:
    client = PaperExecutionClient(cash_balance=1000)
    intent = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1, requested_price=100),
    )

    report = client.execute_order_intent(intent, dry_run=True)

    assert report.status == "DRY_RUN"
    assert client.cash_balance == 1000
    assert client.positions == {}
    assert client.reports == []


def test_paper_execution_does_not_open_network_connections(monkeypatch) -> None:
    def fail_socket(*args, **kwargs):
        raise AssertionError("paper execution must not create network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket)
    client = PaperExecutionClient(cash_balance=1000)
    intent = order_intent_from_strategy_action(
        symbol="BTCUSDT",
        action=StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1, requested_price=100),
    )

    assert client.execute_order_intent(intent).status == "FILLED"
