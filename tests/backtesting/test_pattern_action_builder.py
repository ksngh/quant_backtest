from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, IntrabarSequencingMode
from quant_bitcoin.backtesting.sizing import PositionSizingConfig, PositionSizingMode
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.patterns import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitPlanStatus,
    TrailingStopSettings,
    create_risk_exit_plan,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryTrigger
from quant_bitcoin.risk.exit_simulation import SoftInvalidationRule
from quant_bitcoin.strategies.actions import StrategyActionType, StrategyQuantityMode


class _Event:
    def __init__(self, direction: str = "BULLISH", **overrides) -> None:
        self.event_id = "evt-1"
        self.pattern_type = "FAIR_VALUE_GAP"
        self.direction = direction
        for key, value in overrides.items():
            setattr(self, key, value)


def _candles(rows: list[dict]) -> pd.DataFrame:
    base = []
    for i, row in enumerate(rows):
        candle = {"timestamp": i + 1, "high": 101.0, "low": 99.0, "close": 100.0}
        candle.update(row)
        base.append(candle)
    return pd.DataFrame(base)


def _plan(direction: str = "LONG", **cfg):
    base_cfg = {
        "atr_buffer_multiplier": 0.0,
        "break_even": BreakEvenSettings(enabled=False),
        "trailing_stop": TrailingStopSettings(enabled=False),
    }
    base_cfg.update(cfg)
    config = RiskExitConfig(**base_cfg)
    if direction == "LONG":
        return create_risk_exit_plan(direction="LONG", entry_price=100.0, structural_stop=95.0, atr=10.0, config=config)
    return create_risk_exit_plan(direction="SHORT", entry_price=100.0, structural_stop=105.0, atr=10.0, config=config)


def test_long_event_emits_entry_and_exit() -> None:
    actions = build_pattern_trade_actions(_Event("BULLISH"), _plan("LONG"), _candles([{"high": 116.0, "low": 100.0}]), entry_action_timestamp=0, position_side="LONG")

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].quantity is None
    assert actions[0].metadata["entry_quantity_source"] == "ENGINE_CONFIG"
    assert actions[0].metadata["engine_sizing_allowed"] is True
    assert actions[-1].action_type == StrategyActionType.EXIT_LONG
    assert actions[-1].metadata["exit_reason"] == "TAKE_PROFIT"


def test_entry_quantity_override_is_preserved() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"high": 116.0, "low": 100.0}]),
        entry_action_timestamp=0,
        position_side="LONG",
        entry_quantity=0.02,
    )

    assert actions[0].quantity == pytest.approx(0.02)
    assert actions[0].metadata["entry_quantity_source"] == "ACTION_OVERRIDE"
    assert actions[0].metadata["engine_sizing_allowed"] is False
    assert actions[0].metadata["raw_action_quantity"] == pytest.approx(0.02)
    assert actions[0].metadata["pattern_quantity_override"] == pytest.approx(0.02)
    assert actions[0].metadata["sizing_risk_source"] == "ACTION_OVERRIDE"


def test_market_confirmation_fill_uses_actual_confirmation_close() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=95.0),
        _plan("LONG"),
        _candles([]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 98.0, "high": 101.0, "low": 94.0, "close": 103.0},
        position_side="LONG",
    )

    assert actions[0].requested_price == pytest.approx(103.0)
    assert actions[0].metadata["fill_price"] == pytest.approx(103.0)
    assert actions[0].metadata["entry_reference"] == pytest.approx(100.0)
    assert actions[0].metadata["confirmation_close"] == pytest.approx(103.0)
    assert actions[0].metadata["fill_price_source"] == "CONFIRMATION_CLOSE"
    assert actions[0].metadata["fill_assumption"] == "MARKET"
    policy = actions[0].metadata["pattern_entry_policy"]
    assert policy["schema_version"] == "pattern_entry_policy_v1"
    assert policy["entry_mode"] == "MARKET_ON_CONFIRMATION_CLOSE"
    assert policy["requested_price"] == pytest.approx(103.0)
    assert policy["entry_reference"] == pytest.approx(100.0)
    assert policy["confirmation_close"] == pytest.approx(103.0)
    assert policy["bars_waited"] == 0
    assert "requested_price is the simulated fill price" in policy["contract"]


def test_market_next_open_requires_next_candle_and_records_policy() -> None:
    no_next = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.MARKET_ON_NEXT_OPEN,
    )
    assert no_next[0].action_type == StrategyActionType.SKIP
    assert no_next[0].reason == "ENTRY_NOT_FILLED"
    assert no_next[0].metadata["pattern_entry_policy"]["entry_status"] == "NOT_FILLED"

    filled = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"timestamp": 2, "open": 101.5, "high": 106.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.MARKET_ON_NEXT_OPEN,
    )
    assert filled[0].action_type == StrategyActionType.ENTER_LONG
    assert filled[0].requested_price == pytest.approx(101.5)
    assert filled[0].metadata["bars_waited"] == 1
    assert filled[0].metadata["pattern_entry_policy"]["fill_price_source"] == "NEXT_OPEN"
    assert filled[0].metadata["pattern_entry_policy"]["requested_price"] == pytest.approx(101.5)


def test_long_market_fill_rebuilds_targets_from_actual_fill_price() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    assert [action.action_type for action in actions] == [StrategyActionType.ENTER_LONG]
    assert actions[0].requested_price == pytest.approx(110.0)
    assert actions[0].metadata["entry_reference"] == pytest.approx(100.0)
    assert actions[0].metadata["entry_price"] == pytest.approx(110.0)
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(15.0)
    assert actions[0].metadata["original_risk_per_unit"] == pytest.approx(5.0)
    assert actions[0].metadata["fill_adjusted_risk_per_unit"] == pytest.approx(15.0)
    assert actions[0].metadata["sizing_risk_source"] == "FILL_ADJUSTED"
    assert actions[0].metadata["risk_plan_aligned_to_fill"] is True
    semantics = actions[0].metadata["target_semantics"]
    assert semantics["schema_version"] == "target_semantics_v1"
    assert [target["name"] for target in semantics["risk_targets"]] == ["TP1", "TP2", "TP3"]
    assert all(target["source"] == "R_MULTIPLE" for target in semantics["risk_targets"])


def test_equity_risk_sizing_uses_fill_adjusted_pattern_risk() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 116.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    result = run_strategy_backtest_engine(
        pd.DataFrame(
            [
                {"timestamp": 1, "open": 110, "high": 111, "low": 100, "close": 110, "volume": 10},
                {"timestamp": 2, "open": 104, "high": 116, "low": 100, "close": 104, "volume": 10},
            ]
        ),
        actions[:1],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    entry = result.executions[0]
    assert entry.quantity == pytest.approx(100.0 / 15.0)
    assert entry.metadata["risk_per_unit"] == pytest.approx(15.0)
    assert entry.metadata["sizing_risk_source"] == "FILL_ADJUSTED"
    assert entry.metadata["resolved_risk_amount"] == pytest.approx(100.0)


@pytest.mark.parametrize(
    "pattern_type",
    [
        "FAIR_VALUE_GAP",
        "ORDER_BLOCK",
        "TRENDLINE_BREAK",
        "CUP_AND_HANDLE",
        "DIAMOND",
        "ADAM_AND_EVE",
    ],
)
def test_canonical_builder_preserves_pattern_metadata_for_all_pattern_types(pattern_type: str) -> None:
    actions = build_pattern_trade_actions(
        _Event(
            "BULLISH",
            event_id=f"{pattern_type}-event",
            pattern_type=pattern_type,
            pattern_status="VALID",
            pattern_score=0.75,
            entry_reference=100.0,
            stop_reference=95.0,
            target_reference=115.0,
            score_components={"geometry": 0.8},
        ),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    entry = actions[0]
    assert entry.action_type == StrategyActionType.ENTER_LONG
    assert entry.metadata["pattern_execution_path"] == "CANONICAL_FILL_AWARE_ACTION_BUILDER"
    assert entry.metadata["canonical_pattern_action"] is True
    assert entry.metadata["canonical_expansion_required"] is False
    assert entry.metadata["pattern_event_id"] == f"{pattern_type}-event"
    assert entry.metadata["pattern_type"] == pattern_type
    assert entry.metadata["pattern_status"] == "VALID"
    assert entry.metadata["pattern_score"] == pytest.approx(0.75)
    assert entry.metadata["score_components"] == {"geometry": 0.8}
    assert entry.metadata["event_entry_reference"] == pytest.approx(100.0)
    assert entry.metadata["event_stop_reference"] == pytest.approx(95.0)
    assert entry.metadata["event_target_reference"] == pytest.approx(115.0)
    assert entry.metadata["fill_adjusted_risk_per_unit"] == pytest.approx(15.0)


def test_canonical_builder_preserves_fvg_trend_metadata() -> None:
    actions = build_pattern_trade_actions(
        _Event(
            "BULLISH",
            mtf_trend_score=0.42,
            mtf_trend_direction="BULLISH",
            mtf_trend_aligned=True,
            mtf_trend_metadata={"schema_version": "multitimeframe_trend_score_v1"},
        ),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    metadata = actions[0].metadata
    assert metadata["mtf_trend_score"] == pytest.approx(0.42)
    assert metadata["mtf_trend_direction"] == "BULLISH"
    assert metadata["mtf_trend_aligned"] is True
    assert metadata["mtf_trend_metadata"]["schema_version"] == "multitimeframe_trend_score_v1"


def test_canonical_builder_preserves_fvg_fibonacci_metadata() -> None:
    actions = build_pattern_trade_actions(
        _Event(
            "BULLISH",
            fib_confluence_pass=True,
            fib_retracement_level=0.5,
            fib_metadata={"schema_version": "fibonacci_retracement_confluence_v1"},
        ),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 100.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    metadata = actions[0].metadata
    assert metadata["fib_confluence_pass"] is True
    assert metadata["fib_retracement_level"] == pytest.approx(0.5)
    assert metadata["fib_metadata"]["schema_version"] == "fibonacci_retracement_confluence_v1"


def test_reaction_entry_metadata_and_fill_adjusted_risk_are_preserved() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", zone_mid=100.0),
        _plan("LONG"),
        _candles([
            {"timestamp": 2, "open": 101.0, "high": 101.2, "low": 99.8, "close": 99.9},
            {"timestamp": 3, "open": 99.9, "high": 111.0, "low": 99.7, "close": 108.0},
        ]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 102.0, "low": 100.0, "close": 101.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
        entry_config=PatternEntryConfig(max_wait_bars=3, entry_trigger=PatternEntryTrigger.TOUCH_AND_REACTION_CLOSE),
    )

    entry = actions[0]
    assert entry.action_type == StrategyActionType.ENTER_LONG
    assert entry.requested_price == pytest.approx(108.0)
    assert entry.metadata["entry_trigger"] == "TOUCH_AND_REACTION_CLOSE"
    assert entry.metadata["touch_candle_index"] == 0
    assert entry.metadata["reaction_candle_index"] == 1
    assert entry.metadata["fill_adjusted_risk_per_unit"] == pytest.approx(13.0)


def test_short_market_fill_rebuilds_targets_from_actual_fill_price() -> None:
    actions = build_pattern_trade_actions(
        _Event("BEARISH"),
        _plan("SHORT"),
        _candles([{"timestamp": 2, "high": 100.0, "low": 94.0, "close": 96.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 99.0, "high": 101.0, "low": 89.0, "close": 90.0},
        position_side="SHORT",
    )

    assert [action.action_type for action in actions] == [StrategyActionType.ENTER_SHORT]
    assert actions[0].requested_price == pytest.approx(90.0)
    assert actions[0].metadata["entry_reference"] == pytest.approx(100.0)
    assert actions[0].metadata["entry_price"] == pytest.approx(90.0)
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(15.0)
    assert actions[0].metadata["risk_plan_aligned_to_fill"] is True


def test_fill_adjusted_targets_are_directionally_sorted() -> None:
    long_actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 160.0, "low": 109.0, "close": 150.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )
    short_actions = build_pattern_trade_actions(
        _Event("BEARISH"),
        _plan("SHORT"),
        _candles([{"timestamp": 2, "high": 91.0, "low": 40.0, "close": 50.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 99.0, "high": 101.0, "low": 89.0, "close": 90.0},
        position_side="SHORT",
    )

    long_exit_prices = [action.requested_price for action in long_actions[1:]]
    short_exit_prices = [action.requested_price for action in short_actions[1:]]
    assert long_exit_prices == sorted(long_exit_prices)
    assert short_exit_prices == sorted(short_exit_prices, reverse=True)
    assert all(price > 110.0 for price in long_exit_prices)
    assert all(price < 90.0 for price in short_exit_prices)


def test_fill_adjusted_take_profit_is_profitable_when_replayed_by_engine() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 126.0, "low": 109.0, "close": 124.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0, "volume": 1.0},
            {"timestamp": 2, "open": 110.0, "high": 126.0, "low": 109.0, "close": 124.0, "volume": 1.0},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(starting_cash=10000.0, trade_quantity=1.0),
    )

    take_profit = next(execution for execution in result.executions if execution.exit_reason == "TAKE_PROFIT")
    entry = result.executions[0]
    assert entry.price == pytest.approx(110.0)
    assert entry.raw_price == pytest.approx(actions[0].requested_price)
    assert entry.metadata["requested_price"] == pytest.approx(actions[0].requested_price)
    assert entry.metadata["pattern_entry_policy"]["requested_price"] == pytest.approx(actions[0].requested_price)
    assert take_profit.raw_price > entry.price
    assert take_profit.gross_pnl is not None
    assert take_profit.gross_pnl >= 0
    assert take_profit.realized_r_multiple is not None
    assert take_profit.realized_r_multiple >= 0


def test_limit_entry_reference_fill_uses_reference_only_when_touched() -> None:
    risk_plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=95.0,
        structural_stop=90.0,
        atr=10.0,
        config=RiskExitConfig(
            atr_buffer_multiplier=0.0,
            break_even=BreakEvenSettings(enabled=False),
            trailing_stop=TrailingStopSettings(enabled=False),
        ),
    )
    actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=95.0),
        risk_plan,
        _candles([{"high": 96.0, "low": 94.0, "close": 95.5}]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].requested_price == pytest.approx(95.0)
    assert actions[0].metadata["fill_price_source"] == "ENTRY_REFERENCE"
    assert actions[0].metadata["fill_assumption"] == "REFERENCE_LIMIT"


def test_limit_midpoint_and_boundary_modes_require_touch() -> None:
    midpoint_actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=100.0, zone_mid=98.0, zone_low=96.0, zone_high=100.0),
        _plan("LONG"),
        _candles([{"high": 99.0, "low": 97.5, "close": 98.5}]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 100.0, "high": 104.0, "low": 99.0, "close": 103.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
    )
    boundary_actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=100.0, zone_mid=98.0, zone_low=96.0, zone_high=100.0),
        _plan("LONG"),
        _candles([{"high": 97.0, "low": 95.5, "close": 96.5}]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 100.0, "high": 104.0, "low": 99.0, "close": 103.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
    )

    assert midpoint_actions[0].action_type == StrategyActionType.ENTER_LONG
    assert midpoint_actions[0].requested_price == pytest.approx(98.0)
    assert midpoint_actions[0].metadata["fill_price_source"] == "PATTERN_MIDPOINT"
    assert boundary_actions[0].action_type == StrategyActionType.ENTER_LONG
    assert boundary_actions[0].requested_price == pytest.approx(96.0)
    assert boundary_actions[0].metadata["fill_price_source"] == "PATTERN_BOUNDARY"
    assert midpoint_actions[0].metadata["pattern_entry_policy"]["entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert midpoint_actions[0].metadata["pattern_entry_policy"]["requested_price"] == pytest.approx(98.0)
    assert boundary_actions[0].metadata["pattern_entry_policy"]["entry_mode"] == "LIMIT_AT_PATTERN_BOUNDARY"


def test_fvg_near_boundary_policy_metadata_marks_retest_variant() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0, zone_mid=100.0),
        _plan("LONG"),
        _candles([{"low": 101.0, "high": 101.2}]),
        entry_action_timestamp=0,
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY,
    )

    policy = actions[0].metadata["pattern_entry_policy"]
    assert actions[0].requested_price == pytest.approx(101.0)
    assert policy["entry_mode_hypothesis"] == "RETEST_NEAR_GAP_BOUNDARY"
    assert policy["entry_style"] == "RETEST_LIMIT"
    assert policy["zone_boundary_variant"] == "NEAR_BOUNDARY"
    assert policy["zone_distance"]["from_zone_mid"] == pytest.approx(1.0)


def test_order_block_618_policy_metadata_marks_retracement_variant() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=100.0, zone_high=110.0, zone_mid=105.0),
        _plan("LONG"),
        _candles([{"low": 103.8, "high": 104.0}]),
        entry_action_timestamp=0,
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT,
    )

    policy = actions[0].metadata["pattern_entry_policy"]
    assert actions[0].requested_price == pytest.approx(103.82)
    assert policy["fill_price_source"] == "ORDER_BLOCK_618_RETRACEMENT"
    assert policy["entry_mode_hypothesis"] == "RETEST_ORDER_BLOCK_618_RETRACEMENT"


def test_boundary_mode_without_boundary_fields_returns_invalid_skip() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="TRENDLINE_BREAK", entry_reference=100.0),
        _plan("LONG"),
        _candles([{"high": 101.0, "low": 99.0, "close": 100.5}]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 100.0, "high": 104.0, "low": 99.0, "close": 103.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ENTRY_MODE_INVALID"
    policy = actions[0].metadata["pattern_entry_policy"]
    assert policy["schema_version"] == "pattern_entry_policy_v1"
    assert policy["entry_status"] == "INVALID"
    assert "zone_low" in policy["invalid_reason"]


def test_limit_entry_reference_no_fill_returns_skip_metadata() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=95.0),
        _plan("LONG"),
        _candles([{"high": 100.0, "low": 99.0, "close": 99.5}]),
        entry_action_timestamp=0,
        confirmation_candle={"timestamp": 0, "open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        max_wait_bars=1,
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ENTRY_NOT_FILLED"
    assert actions[0].metadata["entry_status"] == "NOT_FILLED"
    assert actions[0].metadata["reason"] == "limit price not touched within evaluated candles"


def test_long_event_emits_partial_and_final_exits() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG", partial_exits=(PartialExitSettings(1.0, 0.4), PartialExitSettings(2.0, 0.6))),
        _candles([{"high": 105.0, "low": 100.0}, {"high": 110.0, "low": 105.0}]),
        entry_action_timestamp=0,
        position_side="LONG",
    )

    assert [a.action_type for a in actions] == [
        StrategyActionType.ENTER_LONG,
        StrategyActionType.PARTIAL_EXIT_LONG,
        StrategyActionType.EXIT_LONG,
    ]
    assert actions[1].quantity == pytest.approx(0.4)
    assert actions[1].quantity_mode is StrategyQuantityMode.POSITION_RATIO
    assert actions[1].metadata["quantity_ratio"] == pytest.approx(0.4)
    assert actions[1].metadata["action_quantity_ratio"] == pytest.approx(0.4)
    assert actions[2].quantity == pytest.approx(1.0)
    assert actions[2].quantity_mode is StrategyQuantityMode.POSITION_RATIO
    assert actions[2].metadata["quantity_ratio"] == pytest.approx(0.6)
    assert actions[2].metadata["action_quantity_ratio"] == pytest.approx(1.0)


def test_short_event_emits_entry_and_exit() -> None:
    actions = build_pattern_trade_actions(_Event("BEARISH"), _plan("SHORT"), _candles([{"high": 100.0, "low": 84.0}]), entry_action_timestamp=0, position_side="SHORT")

    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    assert actions[-1].action_type == StrategyActionType.EXIT_SHORT


def test_exit_metadata_preserved() -> None:
    actions = build_pattern_trade_actions(_Event(), _plan("LONG"), _candles([{"high": 106.0, "low": 100.0}]), entry_action_timestamp=123, position_side="LONG")
    exit_action = actions[1]
    assert exit_action.metadata["pattern_event_id"] == "evt-1"
    assert exit_action.metadata["pattern_type"] == "FAIR_VALUE_GAP"
    assert exit_action.metadata["target_name"] == "TP1"
    assert exit_action.metadata["target_source"] == "R_MULTIPLE"
    assert exit_action.metadata["entry_price"] == pytest.approx(100.0)
    assert "realized_r_multiple" in exit_action.metadata


def test_fill_aligned_targets_preserve_target_semantics_sources() -> None:
    risk_plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=10.0,
        config=RiskExitConfig(
            atr_buffer_multiplier=0.0,
            break_even=BreakEvenSettings(enabled=False),
            trailing_stop=TrailingStopSettings(enabled=False),
        ),
        structural_targets=[130.0],
        measured_targets=[140.0],
        detector_target_reference=125.0,
    )
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="CUP_AND_HANDLE", neckline=99.0, target_reference=125.0),
        risk_plan,
        _candles([{"timestamp": 2, "high": 126.0, "low": 100.0, "close": 124.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 101.0, "high": 111.0, "low": 100.0, "close": 110.0},
        position_side="LONG",
    )

    semantics = actions[0].metadata["target_semantics"]
    assert semantics["detector_target_reference"] == pytest.approx(125.0)
    assert semantics["structural_targets"][0]["price"] == pytest.approx(130.0)
    assert semantics["measured_targets"][0]["price"] == pytest.approx(140.0)
    assert {target["source"] for target in semantics["risk_targets"]} >= {"R_MULTIPLE", "STRUCTURE", "MEASURED"}
    assert actions[1].metadata["target_source"] == "R_MULTIPLE"


def test_no_exit_behavior_returns_entry_only() -> None:
    actions = build_pattern_trade_actions(_Event(), _plan("LONG"), _candles([{"high": 101.0, "low": 99.5, "close": 100.2}]), entry_action_timestamp=1, position_side="LONG")
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.ENTER_LONG


def test_invalid_risk_plan_returns_skip_with_diagnostics() -> None:
    invalid_plan = _plan("LONG")
    invalid_plan = invalid_plan.__class__(**{**invalid_plan.__dict__, "status": RiskExitPlanStatus.INVALID, "reasons": ("bad stop",)})
    actions = build_pattern_trade_actions(_Event(), invalid_plan, _candles([]), entry_action_timestamp=1, position_side="LONG")
    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "RISK_PLAN_INVALID"
    assert actions[0].quantity == 0.0
    assert actions[0].metadata["risk_plan_status"] == "INVALID"
    assert actions[0].metadata["risk_plan_reasons"] == ("bad stop",)


def test_skipped_risk_plan_returns_skip_with_diagnostics() -> None:
    skipped_plan = _plan("LONG")
    skipped_plan = skipped_plan.__class__(**{**skipped_plan.__dict__, "status": RiskExitPlanStatus.SKIPPED, "reasons": ("weak setup",)})
    actions = build_pattern_trade_actions(_Event(), skipped_plan, _candles([]), entry_action_timestamp=1, position_side="LONG")

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "RISK_PLAN_INVALID"
    assert actions[0].metadata["risk_plan_status"] == "SKIPPED"
    assert actions[0].metadata["risk_plan_reasons"] == ("weak setup",)


def test_invalid_position_side_rejected() -> None:
    with pytest.raises(ValueError):
        build_pattern_trade_actions(_Event(), _plan("LONG"), _candles([]), entry_action_timestamp=1, position_side="FLAT")


def test_soft_invalidation_metadata_flow() -> None:
    actions = build_pattern_trade_actions(
        _Event(),
        _plan("LONG"),
        _candles([{"high": 102.0, "low": 96.0, "close": 98.0}]),
        entry_action_timestamp=1,
        position_side="LONG",
        soft_invalidation=SoftInvalidationRule("close < neckline", reference_price=99.0),
    )
    assert actions[-1].metadata["exit_reason"] == "SOFT_INVALIDATION"


@pytest.mark.parametrize(
    ("pattern_type", "event_fields", "expected_source"),
    [
        ("TRENDLINE_BREAK", {"trendline_value": 99.0}, "trendline_break.soft_invalidation"),
        ("CUP_AND_HANDLE", {"neckline": 99.0}, "cup_and_handle.neckline_soft_exit"),
        (
            "DIAMOND",
            {"upper_boundary_value": 99.0, "lower_boundary_value": 90.0},
            "diamond.soft_invalidation",
        ),
        ("ADAM_AND_EVE", {"neckline": 99.0}, "adam_and_eve.neckline_soft_exit"),
    ],
)
def test_builder_auto_wires_pattern_soft_invalidation(
    pattern_type: str,
    event_fields: dict,
    expected_source: str,
) -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type=pattern_type, **event_fields),
        _plan("LONG"),
        _candles([{"high": 102.0, "low": 96.0, "close": 98.0}]),
        entry_action_timestamp=1,
        position_side="LONG",
    )

    assert actions[-1].metadata["exit_reason"] == "SOFT_INVALIDATION"
    assert actions[0].metadata["pattern_soft_invalidation"]["schema_version"] == "pattern_soft_invalidation_v1"
    assert actions[0].metadata["pattern_soft_invalidation"]["source"] == expected_source
    assert actions[-1].metadata["exit_metadata"]["pattern_soft_invalidation_source"] == expected_source
    assert actions[-1].metadata["exit_metadata"]["reference_price"] == pytest.approx(99.0)


def test_builder_records_order_block_soft_invalidation_limitation_without_fake_exit() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK"),
        _plan("LONG"),
        _candles([{"high": 102.0, "low": 96.0, "close": 100.2}]),
        entry_action_timestamp=1,
        position_side="LONG",
    )

    assert [action.action_type for action in actions] == [StrategyActionType.ENTER_LONG]
    metadata = actions[0].metadata["pattern_soft_invalidation"]
    assert metadata["schema_version"] == "pattern_soft_invalidation_v1"
    assert metadata["supported"] is False
    assert metadata["source"] == "order_block.no_reaction_stop"
    assert "not expressible as a simple close rule" in metadata["limitation"]


def test_actions_include_requested_prices_for_entry_and_exit() -> None:
    actions = build_pattern_trade_actions(_Event(), _plan("LONG"), _candles([{"high": 106.0, "low": 100.0}]), entry_action_timestamp=123, position_side="LONG")
    assert actions[0].requested_price == pytest.approx(actions[0].metadata["fill_price"])
    assert actions[1].requested_price == pytest.approx(actions[1].metadata["exit_price"])


def test_ambiguous_same_candle_exit_metadata_contains_precedence_policy() -> None:
    actions = build_pattern_trade_actions(
        _Event(),
        _plan("LONG"),
        _candles([{"high": 106.0, "low": 94.0, "close": 101.0}]),
        entry_action_timestamp=123,
        position_side="LONG",
    )
    exit_metadata = actions[-1].metadata["exit_metadata"]
    assert exit_metadata["precedence"] == "stop_before_target"
    assert exit_metadata["intrabar_precedence_policy"] == "stop_before_target"
    assert exit_metadata["ambiguous_stop_target"] is True


def test_intrabar_target_first_policy_flows_through_builder() -> None:
    actions = build_pattern_trade_actions(
        _Event(),
        _plan("LONG"),
        _candles([{"high": 106.0, "low": 94.0, "close": 101.0}]),
        entry_action_timestamp=123,
        position_side="LONG",
        intrabar_policy_config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.TARGET_FIRST),
    )
    exit_action = actions[-1]

    assert exit_action.metadata["exit_reason"] == "TAKE_PROFIT"
    assert exit_action.metadata["exit_metadata"]["intrabar_policy"] == "TARGET_FIRST"
    assert exit_action.metadata["exit_metadata"]["decision_outcome"] == "TARGET"


def test_combined_entry_target_conservative_records_entry_without_same_candle_exit() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=100.0),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 99.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 105.0, "high": 106.0, "low": 99.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
    )

    assert [action.action_type for action in actions] == [StrategyActionType.ENTER_LONG]
    decision = actions[0].metadata["combined_intrabar_decision"]
    assert decision["intrabar_policy"] == "CONSERVATIVE"
    assert decision["decision_outcome"] == "ENTRY"
    assert decision["is_ambiguous"] is True


def test_combined_entry_stop_target_skip_ambiguous_skips_entry() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", entry_reference=100.0),
        _plan("LONG"),
        _candles([{"timestamp": 2, "high": 106.0, "low": 94.0, "close": 101.0}]),
        entry_action_timestamp=1,
        confirmation_candle={"timestamp": 1, "open": 105.0, "high": 106.0, "low": 94.0, "close": 102.0},
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        intrabar_policy_config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.SKIP_AMBIGUOUS),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ENTRY_EXIT_AMBIGUOUS"
    decision = actions[0].metadata["combined_intrabar_decision"]
    assert decision["skipped"] is True
    assert decision["decision_outcome"] == "SKIP"


def test_builder_does_not_mutate_future_candles_input() -> None:
    future = _candles([{"high": 106.0, "low": 100.0}])
    original = future.copy(deep=True)

    build_pattern_trade_actions(
        _Event(),
        _plan("LONG"),
        future,
        entry_action_timestamp=123,
        position_side="LONG",
    )

    pd.testing.assert_frame_equal(future, original)
