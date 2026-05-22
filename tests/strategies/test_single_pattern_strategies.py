from __future__ import annotations

import pandas as pd

from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.strategies.patterns import DiamondStrategy


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1},
            {"timestamp": 2, "open": 100.5, "high": 102, "low": 100, "close": 101.5, "volume": 1},
        ]
    )


def test_diamond_no_event_returns_no_action(monkeypatch) -> None:
    strategy = DiamondStrategy()
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [])

    assert strategy.evaluate(_candles(), {}) == []


def test_diamond_weak_event_returns_risk_plan_invalid_skip(monkeypatch) -> None:
    strategy = DiamondStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "diamond-weak"
        pattern_type = "DIAMOND"

    class Plan:
        status = RiskExitPlanStatus.INVALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "RISK_PLAN_INVALID"


def test_diamond_bullish_event_enters_long(monkeypatch) -> None:
    strategy = DiamondStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "diamond-bull"
        pattern_type = "DIAMOND"
        entry_reference = 101
        stop_reference = 99
        target_reference = 104

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].reason == "PATTERN_CONFIRMED"


def test_diamond_bearish_event_short_disabled_skip(monkeypatch) -> None:
    strategy = DiamondStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BEARISH"
        event_id = "diamond-bear"
        pattern_type = "DIAMOND"

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])

    actions = strategy.evaluate(_candles(), {})
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "SHORT_DISABLED"
