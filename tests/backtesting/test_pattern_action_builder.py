from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.patterns import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitPlanStatus,
    TrailingStopSettings,
    create_risk_exit_plan,
)
from quant_bitcoin.risk.exit_simulation import SoftInvalidationRule
from quant_bitcoin.strategies.actions import StrategyActionType


class _Event:
    def __init__(self, direction: str = "BULLISH") -> None:
        self.event_id = "evt-1"
        self.pattern_type = "FAIR_VALUE_GAP"
        self.direction = direction


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
    assert actions[-1].action_type == StrategyActionType.EXIT_LONG
    assert actions[-1].metadata["exit_reason"] == "TAKE_PROFIT"


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
    assert actions[2].quantity == pytest.approx(0.6)


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


def test_invalid_risk_plan_returns_entry_with_invalid_reason() -> None:
    invalid_plan = _plan("LONG")
    invalid_plan = invalid_plan.__class__(**{**invalid_plan.__dict__, "status": RiskExitPlanStatus.INVALID})
    actions = build_pattern_trade_actions(_Event(), invalid_plan, _candles([]), entry_action_timestamp=1, position_side="LONG")
    assert len(actions) == 1
    assert actions[0].reason == "RISK_PLAN_INVALID"


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
