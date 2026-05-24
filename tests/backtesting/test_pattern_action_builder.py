from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, IntrabarSequencingMode
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.patterns import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitPlanStatus,
    TrailingStopSettings,
    create_risk_exit_plan,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryMode
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
    assert actions[0].metadata["risk_plan_aligned_to_fill"] is True


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
    assert exit_action.metadata["entry_price"] == pytest.approx(100.0)
    assert "realized_r_multiple" in exit_action.metadata


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
