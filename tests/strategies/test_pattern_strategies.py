import pandas as pd

from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.patterns import DiamondStrategy, pattern_direction_to_position_side, strategy_for_pattern


def _candles():
    return pd.DataFrame([
        {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1},
        {"timestamp": 2, "open": 100.5, "high": 102, "low": 100, "close": 101.5, "volume": 1},
    ])


def test_strategy_for_pattern_factory():
    strat = strategy_for_pattern("FAIR_VALUE_GAP")
    assert strat.strategy_key == "FAIR_VALUE_GAP"


def test_diamond_bearish_emits_enter_short(monkeypatch):
    strategy = DiamondStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BEARISH"
        event_id = "d1"
        pattern_type = "DIAMOND"

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    assert actions[0].reason == "PATTERN_CONFIRMED"


def test_diamond_bullish_emits_enter_long(monkeypatch):
    strategy = DiamondStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "d2"
        pattern_type = "DIAMOND"
        entry_reference = 101.0
        stop_reference = 99.0
        target_reference = 104.0

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


def test_pattern_direction_to_position_side_mapping():
    assert pattern_direction_to_position_side("BULLISH") == "LONG"
    assert pattern_direction_to_position_side("BEARISH") == "SHORT"
    assert pattern_direction_to_position_side("SIDEWAYS") is None
