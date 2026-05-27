import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    PatternRegimeThresholdConfig,
    PatternRegimeThresholdOverride,
)
from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.patterns import (
    AdamAndEveStrategy,
    CupAndHandleStrategy,
    DiamondStrategy,
    FairValueGapStrategy,
    OrderBlockStrategy,
    PatternEntryFilterConfig,
    TrendlineBreakStrategy,
    pattern_direction_to_position_side,
    strategy_for_pattern,
)


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
        pattern_status = "VALID"

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())

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
        pattern_status = "VALID"
        entry_reference = 101.0
        stop_reference = 99.0
        target_reference = 104.0

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].reason == "PATTERN_CONFIRMED"


def test_pattern_direction_to_position_side_mapping():
    assert pattern_direction_to_position_side("BULLISH") == "LONG"
    assert pattern_direction_to_position_side("BEARISH") == "SHORT"
    assert pattern_direction_to_position_side("SIDEWAYS") is None


def test_weak_event_skipped_by_default(monkeypatch):
    strategy = DiamondStrategy()

    class Event:
        end_index = 1; timestamp = 2; direction = "BULLISH"; event_id = "d3"; pattern_type = "DIAMOND"; pattern_status = "WEAK"
    class Plan: status = RiskExitPlanStatus.VALID
    class Wrapper: risk_plan = Plan()
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())
    actions = strategy.evaluate(_candles(), {})
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "PATTERN_STATUS_NOT_ALLOWED"


def test_weak_event_allowed_when_configured(monkeypatch):
    strategy = DiamondStrategy(entry_filter_config=PatternEntryFilterConfig(allowed_statuses=("VALID", "WEAK")))

    class Event:
        end_index = 1; timestamp = 2; direction = "BULLISH"; event_id = "d4"; pattern_type = "DIAMOND"; pattern_status = "WEAK"
    class Plan: status = RiskExitPlanStatus.VALID
    class Wrapper: risk_plan = Plan()
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())
    actions = strategy.evaluate(_candles(), {})
    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].quantity is None


def test_entry_filter_uses_executable_pattern_score_when_available(monkeypatch):
    strategy = DiamondStrategy(
        entry_filter_config=PatternEntryFilterConfig(minimum_pattern_score=0.5)
    )

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "d-score"
        pattern_type = "DIAMOND"
        pattern_status = "VALID"
        pattern_score = 0.9
        executable_pattern_score = 0.2
        diagnostic_pattern_score = 0.9

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "PATTERN_SCORE_BELOW_MINIMUM"
    assert actions[0].metadata["pattern_score"] == 0.2
    assert actions[0].metadata["executable_pattern_score"] == 0.2
    assert actions[0].metadata["diagnostic_pattern_score"] == 0.9


def test_pattern_quantity_override(monkeypatch):
    strategy = DiamondStrategy(entry_filter_config=PatternEntryFilterConfig(quantity_override=2.5))

    class Event:
        end_index = 1; timestamp = 2; direction = "BULLISH"; event_id = "d5"; pattern_type = "DIAMOND"; pattern_status = "VALID"
    class Plan: status = RiskExitPlanStatus.VALID
    class Wrapper: risk_plan = Plan()
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())
    actions = strategy.evaluate(_candles(), {})
    assert actions[0].quantity == 2.5
    assert actions[0].metadata["quantity_override"] == 2.5


def test_pattern_regime_threshold_low_liquidity_block_emits_skip(monkeypatch):
    strategy = DiamondStrategy(
        entry_filter_config=PatternEntryFilterConfig(
            regime_threshold_config=PatternRegimeThresholdConfig(
                enabled=True,
                liquidity_regime_overrides={
                    "LOW": PatternRegimeThresholdOverride(
                        block_entry=True,
                        block_reason="LOW_LIQUIDITY_REGIME_BLOCK",
                    )
                },
            )
        )
    )

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "regime-block"
        pattern_type = "DIAMOND"
        pattern_status = "VALID"
        pattern_score = 0.9
        volume_ratio = 2.0

    class Plan:
        status = RiskExitPlanStatus.VALID

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", lambda event, candles=None, config=None: Wrapper())

    actions = strategy.evaluate(
        _candles(),
        {"market_regime_context": {"liquidity_regime": "LOW"}},
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LOW_LIQUIDITY_REGIME_BLOCK"
    assert actions[0].metadata["pattern_regime_thresholds"]["blocked"] is True
    assert actions[0].metadata["pattern_regime_thresholds"]["matched_overrides"] == (
        "liquidity_regime:LOW",
    )


def test_diamond_strategy_passes_candles_to_internal_pivot_risk_planner(monkeypatch):
    strategy = DiamondStrategy()
    captured = {}

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "d6"
        pattern_type = "DIAMOND"
        pattern_status = "VALID"

    class Plan:
        status = RiskExitPlanStatus.VALID
        reasons = ()

    class Wrapper:
        risk_plan = Plan()

    def fake_plan(event, candles=None, config=None):
        captured["candles"] = candles
        return Wrapper()

    frame = _candles()
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_diamond_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_diamond_risk_exit_plan", fake_plan)

    actions = strategy.evaluate(frame, {})

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert captured["candles"] is frame


def test_adam_and_eve_strategy_exposes_stop_mode_in_action_metadata(monkeypatch):
    strategy = AdamAndEveStrategy()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = "ae1"
        pattern_type = "ADAM_AND_EVE_PATTERN"
        pattern_status = "VALID"
        adam_low_price = 80.0
        eve_low_price = 81.0
        stop_reference_mode = "EVE_LOW"
        detector_reference_stop = 80.0
        detector_reference_risk_reward = 20.0 / 24.0

    class Plan:
        status = RiskExitPlanStatus.VALID
        reasons = ()
        structural_stop = 81.0

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr("quant_bitcoin.strategies.patterns.detect_adam_and_eve_patterns", lambda frame, config=None: [Event()])
    monkeypatch.setattr("quant_bitcoin.strategies.patterns.create_adam_and_eve_risk_exit_plan", lambda event, config=None: Wrapper())

    actions = strategy.evaluate(_candles(), {})

    assert actions[0].metadata["risk_stop_mode"] == "EVE_LOW"
    assert actions[0].metadata["detector_reference_stop"] == 80.0
    assert actions[0].metadata["detector_reference_risk_reward"] == pytest.approx(20.0 / 24.0)


@pytest.mark.parametrize(
    ("pattern_key", "strategy_cls", "detector_name", "planner_name"),
    [
        ("FAIR_VALUE_GAP", FairValueGapStrategy, "detect_fair_value_gaps", "create_fair_value_gap_risk_exit_plan"),
        ("ORDER_BLOCK", OrderBlockStrategy, "detect_order_blocks", "create_order_block_risk_exit_plan"),
        ("TRENDLINE_BREAK", TrendlineBreakStrategy, "detect_trendline_breaks", "create_trendline_break_risk_exit_plan"),
        ("CUP_AND_HANDLE", CupAndHandleStrategy, "detect_cup_and_handle_patterns", "create_cup_and_handle_risk_exit_plan"),
        ("DIAMOND", DiamondStrategy, "detect_diamond_patterns", "create_diamond_risk_exit_plan"),
        ("ADAM_AND_EVE", AdamAndEveStrategy, "detect_adam_and_eve_patterns", "create_adam_and_eve_risk_exit_plan"),
    ],
)
def test_pattern_strategy_raw_signal_is_explicit_legacy_input_for_canonical_expansion(
    monkeypatch,
    pattern_key,
    strategy_cls,
    detector_name,
    planner_name,
):
    strategy = strategy_cls()

    class Event:
        end_index = 1
        timestamp = 2
        direction = "BULLISH"
        event_id = f"{pattern_key}-1"
        pattern_type = pattern_key
        pattern_status = "VALID"
        pattern_score = 0.8
        entry_reference = 101.0
        stop_reference = 99.0
        target_reference = 104.0

    class Plan:
        status = RiskExitPlanStatus.VALID
        reasons = ()

    class Wrapper:
        risk_plan = Plan()

    monkeypatch.setattr(f"quant_bitcoin.strategies.patterns.{detector_name}", lambda frame, config=None: [Event()])
    if pattern_key in {"TRENDLINE_BREAK", "DIAMOND"}:
        monkeypatch.setattr(f"quant_bitcoin.strategies.patterns.{planner_name}", lambda event, candles=None, config=None: Wrapper())
    else:
        monkeypatch.setattr(f"quant_bitcoin.strategies.patterns.{planner_name}", lambda event, config=None, **kwargs: Wrapper())

    actions = strategy.evaluate(_candles(), {})

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].requested_price is None
    assert actions[0].metadata["pattern_execution_path"] == "LEGACY_SIMPLE_ENTRY_SIGNAL"
    assert actions[0].metadata["canonical_expansion_required"] is True
    assert actions[0].metadata["pattern_event_id"] == f"{pattern_key}-1"
    assert actions[0].metadata["pattern_type"] == pattern_key
    assert actions[0].metadata["pattern_score"] == 0.8
