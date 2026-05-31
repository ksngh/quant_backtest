from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.pattern_action_builder import (
    CloseVolumeEntryFilterConfig,
    CostAwareEntryFilterConfig,
    FvgOrderBlockConfluenceConfig,
    OrderBlockEntryVolumeFilterConfig,
    OrderBlockMtfFilterConfig,
    OrderBlockRiskExitConfig,
    _fvg_order_block_confluence_decision,
    build_fvg_channel_trade_actions,
    build_pattern_trade_actions,
)
from quant_bitcoin.backtesting.strategy_postgres_runner_core import _build_actions, _expand_raw_actions
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
from quant_bitcoin.patterns.fvg_channel import ChannelBoundary, ChannelEntrySide, ChannelRetestEntry, FvgChannelConfig
from quant_bitcoin.risk.exit_simulation import SoftInvalidationRule
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode


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


def _ohlcv(rows: list[dict]) -> pd.DataFrame:
    base = []
    for i, row in enumerate(rows):
        candle = {
            "timestamp": i,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        candle.update(row)
        base.append(candle)
    return pd.DataFrame(base)


def _order_block(direction: str, *, zone_low: float = 99.0, zone_high: float = 101.0, end_index: int = 0, state: str = "FRESH"):
    return SimpleNamespace(
        event_id=f"ob-{direction.lower()}-{end_index}",
        direction=direction,
        pattern_status="VALID",
        order_block_state=state,
        zone_low=zone_low,
        zone_high=zone_high,
        end_index=end_index,
        timestamp=end_index,
    )


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


def test_fvg_order_block_confluence_local_long_passes_without_detector(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: pytest.fail("default local FVG OB confluence must not call detect_order_blocks"),
    )

    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        position_side="LONG",
        candles=_ohlcv([
            {"open": 101.0, "high": 102.0, "low": 98.0, "close": 99.0},
            {"open": 99.0, "high": 104.0, "low": 98.5, "close": 103.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=103.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is True
    assert decision["blocked"] is False
    assert decision["source"] == "LOCAL_ENTRY_CANDLES"
    assert decision["required_order_block_direction"] == "BULLISH"
    assert decision["matched_order_block_direction"] == "BULLISH"
    assert decision["local_order_block_passed"] is True
    assert decision["local_ob_zone_low"] == pytest.approx(98.0)
    assert decision["local_ob_zone_high"] == pytest.approx(102.0)


def test_fvg_order_block_confluence_local_short_passes_without_detector(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: pytest.fail("default local FVG OB confluence must not call detect_order_blocks"),
    )

    decision = _fvg_order_block_confluence_decision(
        _Event("BEARISH", zone_low=99.0, zone_high=101.0),
        position_side="SHORT",
        candles=_ohlcv([
            {"open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0},
            {"open": 101.0, "high": 101.5, "low": 96.0, "close": 97.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=97.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is True
    assert decision["required_order_block_direction"] == "BEARISH"
    assert decision["matched_order_block_direction"] == "BEARISH"
    assert decision["local_order_block_passed"] is True


def test_fvg_order_block_confluence_local_long_fails_when_previous_not_bearish() -> None:
    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        position_side="LONG",
        candles=_ohlcv([
            {"open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0},
            {"open": 101.0, "high": 104.0, "low": 100.0, "close": 103.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=103.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is False
    assert decision["blocked"] is True
    assert decision["invalid_reason"] == "PREVIOUS_CANDLE_NOT_OPPOSING_SIDE"
    assert decision["block_reason"] == "FVG_ORDER_BLOCK_CONFLUENCE_MISSING"


def test_fvg_order_block_confluence_local_long_fails_when_current_not_bullish() -> None:
    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        position_side="LONG",
        candles=_ohlcv([
            {"open": 101.0, "high": 102.0, "low": 98.0, "close": 99.0},
            {"open": 103.0, "high": 104.0, "low": 100.0, "close": 101.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=100.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is False
    assert decision["blocked"] is True
    assert decision["invalid_reason"] == "CURRENT_CANDLE_NOT_CONFIRMING_SIDE"


def test_fvg_order_block_confluence_local_long_fails_when_break_not_confirmed() -> None:
    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        position_side="LONG",
        candles=_ohlcv([
            {"open": 101.0, "high": 102.0, "low": 98.0, "close": 99.0},
            {"open": 99.0, "high": 101.5, "low": 98.5, "close": 101.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=101.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is False
    assert decision["blocked"] is True
    assert decision["invalid_reason"] == "LOCAL_ORDER_BLOCK_BREAK_NOT_CONFIRMED"


def test_fvg_order_block_confluence_local_short_failures() -> None:
    previous_not_bullish = _fvg_order_block_confluence_decision(
        _Event("BEARISH", zone_low=99.0, zone_high=101.0),
        position_side="SHORT",
        candles=_ohlcv([
            {"open": 101.0, "high": 102.0, "low": 98.0, "close": 99.0},
            {"open": 99.0, "high": 100.0, "low": 96.0, "close": 97.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=97.0,
        entry_timestamp=1,
    )
    current_not_bearish = _fvg_order_block_confluence_decision(
        _Event("BEARISH", zone_low=99.0, zone_high=101.0),
        position_side="SHORT",
        candles=_ohlcv([
            {"open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0},
            {"open": 97.0, "high": 100.0, "low": 96.0, "close": 99.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=99.0,
        entry_timestamp=1,
    )
    break_not_confirmed = _fvg_order_block_confluence_decision(
        _Event("BEARISH", zone_low=99.0, zone_high=101.0),
        position_side="SHORT",
        candles=_ohlcv([
            {"open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0},
            {"open": 101.0, "high": 101.5, "low": 98.0, "close": 99.0},
        ]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=99.0,
        entry_timestamp=1,
    )

    assert previous_not_bullish["invalid_reason"] == "PREVIOUS_CANDLE_NOT_OPPOSING_SIDE"
    assert current_not_bearish["invalid_reason"] == "CURRENT_CANDLE_NOT_CONFIRMING_SIDE"
    assert break_not_confirmed["invalid_reason"] == "LOCAL_ORDER_BLOCK_BREAK_NOT_CONFIRMED"
    assert previous_not_bullish["blocked"] is True
    assert current_not_bearish["blocked"] is True
    assert break_not_confirmed["blocked"] is True


def test_fvg_order_block_confluence_local_missing_previous_fails() -> None:
    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        position_side="LONG",
        candles=_ohlcv([{"open": 99.0, "high": 104.0, "low": 98.5, "close": 103.0}]),
        config=FvgOrderBlockConfluenceConfig(enabled=True),
        entry_price=103.0,
        entry_timestamp=0,
    )

    assert decision["blocked"] is True
    assert decision["invalid_reason"] == "PREVIOUS_CANDLE_MISSING"


def test_fvg_order_block_confluence_historical_detector_compatibility(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: [_order_block("BULLISH", zone_low=99.5, zone_high=100.5, end_index=1)],
    )

    decision = _fvg_order_block_confluence_decision(
        _Event("BULLISH", zone_low=95.0, zone_high=96.0),
        position_side="LONG",
        candles=_ohlcv([{}, {}]),
        config=FvgOrderBlockConfluenceConfig(
            enabled=True,
            source="historical_detector",
            lookback_bars=5,
            mode="entry_price_inside_ob",
        ),
        entry_price=100.0,
        entry_timestamp=1,
    )

    assert decision["passed"] is True
    assert decision["source"] == "HISTORICAL_DETECTOR"
    assert decision["match_reason"] == "ENTRY_PRICE_INSIDE_OB"


def test_pattern_entry_skips_when_fvg_order_block_confluence_missing() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": 1, "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=0,
        confirmation_candle=_ohlcv([{"timestamp": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0}]).iloc[0],
        position_side="LONG",
        context_candles=_ohlcv([
            {"timestamp": -1, "open": 99.0, "high": 101.0, "low": 98.0, "close": 100.0},
            {"timestamp": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
        ]),
        fvg_order_block_confluence_config=FvgOrderBlockConfluenceConfig(enabled=True, lookback_bars=5),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "FVG_ORDER_BLOCK_CONFLUENCE_MISSING"
    assert actions[0].metadata["fvg_order_block_confluence"]["blocked"] is True


def test_pattern_entry_allows_when_fvg_order_block_confluence_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: pytest.fail("default local FVG OB confluence must not call detect_order_blocks"),
    )

    actions = build_pattern_trade_actions(
        _Event("BULLISH", zone_low=99.0, zone_high=101.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": 1, "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=0,
        confirmation_candle=_ohlcv([{"timestamp": 0, "open": 99.0, "high": 104.0, "low": 98.5, "close": 103.0}]).iloc[0],
        position_side="LONG",
        context_candles=_ohlcv([
            {"timestamp": -1, "open": 101.0, "high": 102.0, "low": 98.0, "close": 99.0},
            {"timestamp": 0, "open": 99.0, "high": 104.0, "low": 98.5, "close": 103.0},
        ]),
        fvg_order_block_confluence_config=FvgOrderBlockConfluenceConfig(enabled=True, lookback_bars=5),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].metadata["fvg_order_block_confluence"]["passed"] is True
    assert actions[0].metadata["fvg_order_block_confluence"]["matched_order_block_direction"] == "BULLISH"
    assert actions[0].metadata["fvg_order_block_confluence"]["previous_candle"]["timestamp"] == -1


def test_order_block_entry_volume_filter_blocks_low_volume() -> None:
    context = _ohlcv([
        {"timestamp": 0, "volume": 100.0},
        {"timestamp": 1, "volume": 100.0},
        {"timestamp": 2, "open": 99.0, "high": 104.0, "low": 98.0, "close": 100.0, "volume": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=98.0, zone_high=104.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": 3, "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=2,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_entry_volume_filter_config=OrderBlockEntryVolumeFilterConfig(
            enabled=True,
            window=2,
            minimum_volume_ratio=2.0,
        ),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ORDER_BLOCK_ENTRY_VOLUME_FILTER"
    metadata = actions[0].metadata["order_block_entry_volume_filter"]
    assert metadata["blocked"] is True
    assert metadata["volume_ratio"] == pytest.approx(1.0)


def test_order_block_entry_volume_filter_allows_high_volume() -> None:
    context = _ohlcv([
        {"timestamp": 0, "volume": 100.0},
        {"timestamp": 1, "volume": 100.0},
        {"timestamp": 2, "open": 99.0, "high": 104.0, "low": 98.0, "close": 100.0, "volume": 300.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=98.0, zone_high=104.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": 3, "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=2,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_entry_volume_filter_config=OrderBlockEntryVolumeFilterConfig(
            enabled=True,
            window=2,
            minimum_volume_ratio=2.0,
        ),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["order_block_entry_volume_filter"]
    assert metadata["blocked"] is False
    assert metadata["volume_ratio"] == pytest.approx(3.0)


def test_order_block_mtf_filter_allows_same_direction_completed_ob(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: [_order_block("BULLISH", zone_low=98.0, zone_high=104.0, end_index=0)],
    )
    context = _ohlcv([
        {"timestamp": pd.Timestamp("2026-05-18T00:00:00Z") + pd.Timedelta(minutes=i), "volume": 100.0}
        for i in range(16)
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=98.0, zone_high=104.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": pd.Timestamp("2026-05-18T00:16:00Z"), "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=context.iloc[-1]["timestamp"],
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_mtf_filter_config=OrderBlockMtfFilterConfig(enabled=True, timeframes=("15m",)),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["order_block_mtf_filter"]
    assert metadata["blocked"] is False
    assert metadata["timeframe_results"][0]["passed"] is True


def test_order_block_mtf_filter_blocks_opposite_direction(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: [_order_block("BEARISH", zone_low=98.0, zone_high=104.0, end_index=0)],
    )
    context = _ohlcv([
        {"timestamp": pd.Timestamp("2026-05-18T00:00:00Z") + pd.Timedelta(minutes=i), "volume": 100.0}
        for i in range(16)
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=98.0, zone_high=104.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": pd.Timestamp("2026-05-18T00:16:00Z"), "high": 116.0, "low": 100.0}]),
        entry_action_timestamp=context.iloc[-1]["timestamp"],
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_mtf_filter_config=OrderBlockMtfFilterConfig(enabled=True, timeframes=("15m",)),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ORDER_BLOCK_MTF_FILTER"
    metadata = actions[0].metadata["order_block_mtf_filter"]
    assert metadata["blocked"] is True
    assert metadata["timeframe_results"][0]["same_direction_order_block_count"] == 0


def test_order_block_previous_candle_risk_exit_long_uses_previous_low_and_1r_target() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 101.0, "high": 102.0, "low": 95.0, "close": 98.0},
        {"timestamp": 1, "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK", zone_low=95.0, zone_high=102.0),
        _plan("LONG"),
        _ohlcv([{"timestamp": 2, "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["applied"] is True
    assert metadata["stop_source"] == "PREVIOUS_CANDLE_LOW"
    assert metadata["stop_price"] == pytest.approx(95.0)
    assert metadata["risk_distance"] == pytest.approx(5.0)
    assert metadata["target_price"] == pytest.approx(105.0)
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(5.0)
    assert actions[-1].action_type == StrategyActionType.EXIT_LONG
    assert actions[-1].requested_price == pytest.approx(105.0)


def test_order_block_previous_candle_risk_exit_short_uses_previous_high_and_1r_target() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 99.0, "high": 105.0, "low": 98.0, "close": 102.0},
        {"timestamp": 1, "open": 102.0, "high": 103.0, "low": 99.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BEARISH", pattern_type="ORDER_BLOCK", zone_low=98.0, zone_high=105.0),
        _plan("SHORT"),
        _ohlcv([{"timestamp": 2, "open": 100.0, "high": 101.0, "low": 94.0, "close": 95.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="SHORT",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["applied"] is True
    assert metadata["stop_source"] == "PREVIOUS_CANDLE_HIGH"
    assert metadata["stop_price"] == pytest.approx(105.0)
    assert metadata["risk_distance"] == pytest.approx(5.0)
    assert metadata["target_price"] == pytest.approx(95.0)
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(5.0)
    assert actions[-1].action_type == StrategyActionType.EXIT_SHORT
    assert actions[-1].requested_price == pytest.approx(95.0)


def test_order_block_previous_candle_risk_exit_invalid_long_non_positive_risk() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0},
        {"timestamp": 1, "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK"),
        _plan("LONG"),
        _ohlcv([{"timestamp": 2, "high": 106.0, "low": 99.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID"
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["blocked"] is True
    assert metadata["invalid_reason"] == "NON_POSITIVE_PREVIOUS_CANDLE_RISK"


def test_order_block_previous_candle_risk_exit_invalid_short_non_positive_risk() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 99.0, "high": 100.0, "low": 97.0, "close": 98.0},
        {"timestamp": 1, "open": 102.0, "high": 103.0, "low": 99.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BEARISH", pattern_type="ORDER_BLOCK"),
        _plan("SHORT"),
        _ohlcv([{"timestamp": 2, "high": 101.0, "low": 94.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="SHORT",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "ORDER_BLOCK_PREVIOUS_CANDLE_RISK_INVALID"
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["blocked"] is True
    assert metadata["invalid_reason"] == "NON_POSITIVE_PREVIOUS_CANDLE_RISK"


def test_order_block_previous_candle_risk_exit_missing_previous_candle_fails_closed() -> None:
    context = _ohlcv([
        {"timestamp": 1, "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK"),
        _plan("LONG"),
        _ohlcv([{"timestamp": 2, "high": 106.0, "low": 99.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["invalid_reason"] == "PREVIOUS_CANDLE_MISSING"


def test_order_block_previous_candle_risk_exit_falls_back_for_non_confirmation_entry_mode() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 101.0, "high": 102.0, "low": 95.0, "close": 98.0},
        {"timestamp": 1, "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0},
    ])

    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK"),
        _plan("LONG"),
        _ohlcv([{"timestamp": 2, "open": 102.0, "high": 106.0, "low": 99.0, "close": 104.0}]),
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        entry_mode=PatternEntryMode.MARKET_ON_NEXT_OPEN,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["order_block_risk_exit"]
    assert metadata["applied"] is False
    assert metadata["fallback_to_existing_risk_plan"] is True
    assert metadata["fallback_reason"] == "UNSUPPORTED_ENTRY_MODE_FOR_PREVIOUS_CANDLE_1R"


def test_order_block_previous_candle_risk_exit_profitable_exits_are_reflected_in_engine_summary() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 101.0, "high": 102.0, "low": 95.0, "close": 98.0},
        {"timestamp": 1, "open": 98.0, "high": 101.0, "low": 97.0, "close": 100.0},
    ])
    future = _ohlcv([{"timestamp": 2, "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0}])
    actions = build_pattern_trade_actions(
        _Event("BULLISH", pattern_type="ORDER_BLOCK"),
        _plan("LONG"),
        future,
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="LONG",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    result = run_strategy_backtest_engine(
        pd.concat([context, future], ignore_index=True),
        actions,
        config=StrategyEngineConfig(starting_cash=10000.0, trade_quantity=1.0),
    )

    take_profit = next(execution for execution in result.executions if execution.exit_reason == "TAKE_PROFIT")
    assert take_profit.gross_pnl == pytest.approx(5.0)
    assert take_profit.net_pnl == pytest.approx(5.0)
    assert result.summary.metadata["gross_pnl"] == pytest.approx(5.0)
    assert result.summary.metadata["net_pnl"] == pytest.approx(5.0)


def test_order_block_previous_candle_risk_exit_profitable_short_is_reflected_in_engine_summary() -> None:
    context = _ohlcv([
        {"timestamp": 0, "open": 99.0, "high": 105.0, "low": 98.0, "close": 102.0},
        {"timestamp": 1, "open": 102.0, "high": 103.0, "low": 99.0, "close": 100.0},
    ])
    future = _ohlcv([{"timestamp": 2, "open": 100.0, "high": 101.0, "low": 94.0, "close": 95.0}])
    actions = build_pattern_trade_actions(
        _Event("BEARISH", pattern_type="ORDER_BLOCK"),
        _plan("SHORT"),
        future,
        entry_action_timestamp=1,
        confirmation_candle=context.iloc[-1],
        position_side="SHORT",
        context_candles=context,
        order_block_risk_exit_config=OrderBlockRiskExitConfig(mode="previous_candle_1r"),
    )

    result = run_strategy_backtest_engine(
        pd.concat([context, future], ignore_index=True),
        actions,
        config=StrategyEngineConfig(starting_cash=10000.0, trade_quantity=1.0),
    )

    take_profit = next(execution for execution in result.executions if execution.exit_reason == "TAKE_PROFIT")
    assert take_profit.gross_pnl == pytest.approx(5.0)
    assert take_profit.net_pnl == pytest.approx(5.0)
    assert result.summary.metadata["gross_pnl"] == pytest.approx(5.0)
    assert result.summary.metadata["net_pnl"] == pytest.approx(5.0)


def test_long_event_emits_entry_and_exit() -> None:
    actions = build_pattern_trade_actions(_Event("BULLISH"), _plan("LONG"), _candles([{"high": 116.0, "low": 100.0}]), entry_action_timestamp=0, position_side="LONG")

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].quantity is None
    assert actions[0].metadata["entry_quantity_source"] == "ENGINE_CONFIG"
    assert actions[0].metadata["engine_sizing_allowed"] is True
    assert actions[-1].action_type == StrategyActionType.EXIT_LONG
    assert actions[-1].metadata["exit_reason"] == "TAKE_PROFIT"


def test_fvg_inverse_direction_flips_bullish_long_to_short() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"timestamp": 1, "open": 100.0, "high": 101.0, "low": 94.0, "close": 96.0},
        ]
    )
    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=0,
        reason="PATTERN_CONFIRMED",
        metadata={
            "event_id": "fvg-bullish",
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": "BULLISH",
            "pattern_direction": "BULLISH",
            "pattern_status": "VALID",
            "position_side": "LONG",
            "risk_plan": _plan("LONG"),
        },
    )

    actions = _expand_raw_actions([raw], candles, 1, fvg_inverse_direction=True)

    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    assert actions[0].metadata["fvg_direction_mode"] == "INVERSE_CONTRARIAN"
    assert actions[0].metadata["fvg_inverse_direction_enabled"] is True
    assert actions[0].metadata["original_position_side"] == "LONG"
    assert actions[0].metadata["effective_position_side"] == "SHORT"
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(5.0)
    assert any(action.action_type in {StrategyActionType.PARTIAL_EXIT_SHORT, StrategyActionType.EXIT_SHORT} for action in actions)


def test_fvg_inverse_direction_flips_bearish_short_to_long() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"timestamp": 1, "open": 100.0, "high": 106.0, "low": 99.0, "close": 104.0},
        ]
    )
    raw = StrategyAction(
        StrategyActionType.ENTER_SHORT,
        timestamp=0,
        reason="PATTERN_CONFIRMED",
        metadata={
            "event_id": "fvg-bearish",
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": "BEARISH",
            "pattern_direction": "BEARISH",
            "pattern_status": "VALID",
            "position_side": "SHORT",
            "risk_plan": _plan("SHORT"),
        },
    )

    actions = _expand_raw_actions([raw], candles, 1, fvg_inverse_direction=True)

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].metadata["fvg_direction_mode"] == "INVERSE_CONTRARIAN"
    assert actions[0].metadata["original_position_side"] == "SHORT"
    assert actions[0].metadata["effective_position_side"] == "LONG"
    assert actions[0].metadata["risk_per_unit"] == pytest.approx(5.0)
    assert any(action.action_type in {StrategyActionType.PARTIAL_EXIT_LONG, StrategyActionType.EXIT_LONG} for action in actions)


def test_fvg_inverse_direction_is_default_off() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"timestamp": 1, "open": 100.0, "high": 116.0, "low": 99.0, "close": 114.0},
        ]
    )
    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=0,
        reason="PATTERN_CONFIRMED",
        metadata={
            "event_id": "fvg-normal",
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": "BULLISH",
            "pattern_direction": "BULLISH",
            "pattern_status": "VALID",
            "position_side": "LONG",
            "risk_plan": _plan("LONG"),
        },
    )

    actions = _expand_raw_actions([raw], candles, 1)

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].metadata["fvg_direction_mode"] == "NORMAL"
    assert actions[0].metadata["fvg_inverse_direction_enabled"] is False
    assert actions[0].metadata["original_position_side"] == "LONG"
    assert actions[0].metadata["effective_position_side"] == "LONG"


def test_fvg_inverse_direction_blocks_channel_mode_with_clear_skip() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 108.0, "low": 102.95, "close": 104.0},
        ]
    )
    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=2,
        reason="PATTERN_CONFIRMED",
        metadata={
            "event_id": "fvg-channel-inverse",
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": "BULLISH",
            "pattern_direction": "BULLISH",
            "pattern_status": "VALID",
            "position_side": "LONG",
            "risk_plan": _plan("LONG"),
        },
    )

    actions = _expand_raw_actions(
        [raw],
        candles,
        3,
        fvg_channel_config=FvgChannelConfig(enabled=True, window=3),
        fvg_inverse_direction=True,
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "FVG_INVERSE_DIRECTION_CHANNEL_UNSUPPORTED"
    assert actions[0].metadata["fvg_inverse_direction_enabled"] is True
    assert actions[0].metadata["original_position_side"] == "LONG"
    assert actions[0].metadata["effective_position_side"] == "SHORT"


def test_fvg_channel_upper_boundary_action_enters_long_with_projected_width_target() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
    )

    assert [action.action_type for action in actions] == [
        StrategyActionType.ENTER_LONG,
        StrategyActionType.EXIT_LONG,
    ]
    assert actions[0].requested_price == pytest.approx(113.2)
    assert actions[0].metadata["entry_boundary"] == "UPPER"
    assert actions[0].metadata["channel_boundary_direction_mode"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert actions[0].metadata["original_channel_entry_side"] == "SHORT"
    assert actions[0].metadata["effective_channel_entry_side"] == "LONG"
    assert actions[0].metadata["line_stop_price"] == pytest.approx(102.0)
    assert actions[0].metadata["line_target_price"] == pytest.approx(123.2)
    assert actions[0].metadata["stop_source"] == "PRE_RETEST_CANDLE_LOW"
    assert actions[0].metadata["retest_structure_low"] == pytest.approx(109.0)
    assert actions[0].metadata["pre_retest_stop_valid"] is True
    assert actions[0].metadata["pre_retest_candle_index"] == 2
    assert actions[0].metadata["pre_retest_candle_low"] == pytest.approx(102.0)
    assert actions[0].metadata["pre_retest_candle_high"] == pytest.approx(107.0)
    assert actions[0].metadata["line_stop_price_diagnostic"] == pytest.approx(103.0)
    assert actions[0].metadata["channel_width_at_entry"] == pytest.approx(10.0)
    assert actions[0].metadata["retest_confirmation_basis"] == "CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1"
    assert actions[0].metadata["entry_trigger"] == "UPPER_CLOSE_BASED_RETEST"
    assert actions[0].metadata["projected_channel_width_target"] == pytest.approx(123.2)
    assert actions[0].metadata["opposite_boundary_target_price"] == pytest.approx(113.0)
    assert actions[0].metadata["channel_lower_line_price_at_entry"] == pytest.approx(103.0)
    assert actions[0].metadata["atr_used_for_stop_or_target"] is False
    assert actions[1].requested_price == pytest.approx(123.2)
    assert actions[1].metadata["exit_reason"] == "TAKE_PROFIT"
    assert actions[1].metadata["target_boundary"] == "CHANNEL_WIDTH_TARGET"
    assert actions[1].metadata["target_source"] == "FVG_V2_CHANNEL_WIDTH_PROJECTION"
    assert actions[1].metadata["atr_used_for_stop_or_target"] is False


def test_fvg_channel_lower_boundary_action_enters_short_with_projected_width_target() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8},
            {"timestamp": 4, "high": 106.5, "low": 92.0, "close": 93.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
    )

    assert [action.action_type for action in actions] == [
        StrategyActionType.ENTER_SHORT,
        StrategyActionType.EXIT_SHORT,
    ]
    assert actions[0].requested_price == pytest.approx(102.8)
    assert actions[0].metadata["entry_boundary"] == "LOWER"
    assert actions[0].metadata["channel_boundary_direction_mode"] == "UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1"
    assert actions[0].metadata["original_channel_entry_side"] == "LONG"
    assert actions[0].metadata["effective_channel_entry_side"] == "SHORT"
    assert actions[0].metadata["line_stop_price"] == pytest.approx(107.0)
    assert actions[0].metadata["line_target_price"] == pytest.approx(92.8)
    assert actions[0].metadata["stop_source"] == "PRE_RETEST_CANDLE_HIGH"
    assert actions[0].metadata["pre_retest_stop_valid"] is True
    assert actions[0].metadata["pre_retest_candle_index"] == 2
    assert actions[0].metadata["pre_retest_candle_low"] == pytest.approx(102.0)
    assert actions[0].metadata["pre_retest_candle_high"] == pytest.approx(107.0)
    assert actions[0].metadata["line_stop_price_diagnostic"] == pytest.approx(113.0)
    assert actions[0].metadata["channel_width_at_entry"] == pytest.approx(10.0)
    assert actions[0].metadata["retest_confirmation_basis"] == "CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1"
    assert actions[0].metadata["entry_trigger"] == "LOWER_CLOSE_BASED_RETEST"
    assert actions[0].metadata["projected_channel_width_target"] == pytest.approx(92.8)
    assert actions[0].metadata["opposite_boundary_target_price"] == pytest.approx(103.0)
    assert actions[0].metadata["atr_used_for_stop_or_target"] is False
    assert actions[1].requested_price == pytest.approx(92.8)
    assert actions[1].metadata["exit_reason"] == "TAKE_PROFIT"
    assert actions[1].metadata["target_boundary"] == "CHANNEL_WIDTH_TARGET"
    assert actions[1].metadata["target_source"] == "FVG_V2_CHANNEL_WIDTH_PROJECTION"
    assert actions[1].metadata["atr_used_for_stop_or_target"] is False


def test_fvg_channel_invalid_pre_retest_stop_emits_skip(monkeypatch) -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
        ]
    )

    def invalid_entry(*args, **kwargs):
        return ChannelRetestEntry(
            side=ChannelEntrySide.LONG,
            timestamp=candles.iloc[3]["timestamp"],
            fill_price=113.2,
            candle_index=3,
            touch_index=3,
            confirmation_index=3,
            entry_boundary=ChannelBoundary.UPPER,
            stop_price=120.0,
            target_price=123.2,
            stop_source="PRE_RETEST_CANDLE_LOW",
            metadata={
                "entry_trigger": "UPPER_CLOSE_BASED_RETEST",
                "pre_retest_stop_valid": False,
                "pre_retest_stop_invalid_reason": "LONG_PRE_RETEST_LOW_NOT_BELOW_ENTRY",
                "stop_source": "PRE_RETEST_CANDLE_LOW",
            },
        )

    monkeypatch.setattr("quant_bitcoin.backtesting.pattern_action_builder.simulate_channel_retest_entry", invalid_entry)

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "FVG_CHANNEL_PRE_RETEST_STOP_INVALID"
    assert actions[0].metadata["pre_retest_stop_valid"] is False
    assert actions[0].metadata["pre_retest_stop_invalid_reason"] == "LONG_PRE_RETEST_LOW_NOT_BELOW_ENTRY"


def test_fvg_channel_skips_when_order_block_confluence_missing() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "open": 103.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "open": 105.0, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "open": 105.0, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 100.0},
            {"timestamp": 3, "open": 110.0, "high": 113.4, "low": 109.0, "close": 113.2, "volume": 100.0},
            {"timestamp": 4, "open": 114.0, "high": 124.0, "low": 110.0, "close": 123.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH", zone_low=109.0, zone_high=111.0),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        fvg_order_block_confluence_config=FvgOrderBlockConfluenceConfig(enabled=True, lookback_bars=5),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "FVG_ORDER_BLOCK_CONFLUENCE_MISSING"
    assert actions[0].metadata["fvg_order_block_confluence"]["blocked"] is True


def test_fvg_channel_allows_when_order_block_confluence_matches(monkeypatch) -> None:
    monkeypatch.setattr(
        "quant_bitcoin.backtesting.pattern_action_builder.detect_order_blocks",
        lambda *args, **kwargs: pytest.fail("default local FVG OB confluence must not call detect_order_blocks"),
    )
    candles = _candles(
        [
            {"timestamp": 0, "open": 103.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "open": 105.0, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "open": 106.0, "high": 107.0, "low": 102.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 3, "open": 110.0, "high": 113.4, "low": 109.0, "close": 113.2, "volume": 100.0},
            {"timestamp": 4, "open": 114.0, "high": 124.0, "low": 110.0, "close": 123.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH", zone_low=109.0, zone_high=111.0),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        fvg_order_block_confluence_config=FvgOrderBlockConfluenceConfig(enabled=True, lookback_bars=5),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].metadata["fvg_order_block_confluence"]["passed"] is True
    assert actions[0].metadata["fvg_order_block_confluence"]["matched_order_block_direction"] == "BULLISH"
    assert actions[0].metadata["fvg_order_block_confluence"]["current_candle"]["timestamp"] == 3


def test_fvg_channel_cost_negative_long_target_is_blocked() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=100.0, spread_bps=100.0, slippage_bps=300.0),
            liquidity_role=LiquidityRole.TAKER,
            cost_profile_name="high_cost_fixture",
        ),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "COST_INFEASIBLE_TAKE_PROFIT"
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["auto_enabled_by_nonzero_costs"] is True
    assert metadata["target_price"] == pytest.approx(123.2)
    assert metadata["channel_width_at_entry"] == pytest.approx(10.0)
    assert metadata["estimated_round_trip_cost_bps"] > metadata["gross_reward_bps"]
    assert metadata["net_reward_bps"] <= 0


def test_fvg_channel_cost_negative_short_target_is_blocked() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8},
            {"timestamp": 4, "high": 112.0, "low": 92.0, "close": 93.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=100.0, spread_bps=100.0, slippage_bps=300.0),
            liquidity_role=LiquidityRole.TAKER,
            cost_profile_name="high_cost_fixture",
        ),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "COST_INFEASIBLE_TAKE_PROFIT"
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["target_price"] == pytest.approx(92.8)
    assert metadata["projected_channel_width_target"] == pytest.approx(92.8)
    assert metadata["estimated_round_trip_cost_bps"] > metadata["gross_reward_bps"]
    assert metadata["net_reward_bps"] <= 0


def test_fvg_channel_cost_positive_target_is_allowed_and_records_filter() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=1.0, spread_bps=1.0, slippage_bps=1.0),
            liquidity_role=LiquidityRole.TAKER,
            cost_profile_name="low_cost_fixture",
        ),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["blocked"] is False
    assert metadata["net_reward_bps"] > 0
    assert metadata["target_price_source"] == "PROJECTED_CHANNEL_WIDTH_FROM_ENTRY_PRICE"


def test_fvg_channel_low_close_volume_blocks_long_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 100.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2, "volume": 40.0},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=True, window=3, minimum_volume_ratio=1.0),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LOW_CLOSE_VOLUME_ENTRY_FILTER"
    metadata = actions[0].metadata["close_volume_entry_filter"]
    assert metadata["blocked"] is True
    assert metadata["current_volume"] == pytest.approx(40.0)
    assert metadata["baseline_volume"] == pytest.approx(100.0)
    assert metadata["volume_ratio"] == pytest.approx(0.4)
    assert metadata["minimum_volume_ratio"] == pytest.approx(1.0)
    assert metadata["low_volume_ratio_threshold"] == pytest.approx(0.5)


def test_fvg_channel_adequate_close_volume_allows_long_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 100.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2, "volume": 150.0},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=True, window=3, minimum_volume_ratio=1.0),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["close_volume_entry_filter"]
    assert metadata["blocked"] is False
    assert metadata["passed"] is True
    assert metadata["volume_ratio"] == pytest.approx(1.5)


def test_fvg_channel_low_close_volume_blocks_short_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 100.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8, "volume": 40.0},
            {"timestamp": 4, "high": 112.0, "low": 92.0, "close": 93.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=True, window=3, minimum_volume_ratio=1.0),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LOW_CLOSE_VOLUME_ENTRY_FILTER"
    metadata = actions[0].metadata["close_volume_entry_filter"]
    assert metadata["entry_side"] == "SHORT"
    assert metadata["applies_to_side"] == "ALL"
    assert metadata["applies_to_sides"] == ["LONG", "SHORT"]
    assert metadata["blocked"] is True
    assert metadata["current_volume"] == pytest.approx(40.0)
    assert metadata["baseline_volume"] == pytest.approx(100.0)
    assert metadata["volume_ratio"] == pytest.approx(0.4)


def test_fvg_channel_adequate_close_volume_allows_short_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 100.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 100.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 100.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8, "volume": 150.0},
            {"timestamp": 4, "high": 112.0, "low": 92.0, "close": 93.0, "volume": 100.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=True, window=3, minimum_volume_ratio=1.0),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    metadata = actions[0].metadata["close_volume_entry_filter"]
    assert metadata["entry_side"] == "SHORT"
    assert metadata["applies_to_side"] == "ALL"
    assert metadata["blocked"] is False
    assert metadata["passed"] is True
    assert metadata["volume_ratio"] == pytest.approx(1.5)


def test_fvg_channel_missing_volume_fails_closed_for_long_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=True, window=3, minimum_volume_ratio=1.0),
    )

    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LOW_CLOSE_VOLUME_ENTRY_FILTER"
    assert actions[0].metadata["close_volume_entry_filter"]["invalid_reason"] == "VOLUME_COLUMN_MISSING"


def test_fvg_channel_close_volume_filter_can_be_disabled() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 113.4, "low": 109.0, "close": 113.2},
            {"timestamp": 4, "high": 124.0, "low": 110.0, "close": 123.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=False, window=3, minimum_volume_ratio=1.0),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_LONG
    assert actions[0].metadata["close_volume_entry_filter"]["enabled"] is False


def test_fvg_channel_close_volume_filter_disable_bypasses_short_entry() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8},
            {"timestamp": 4, "high": 112.0, "low": 92.0, "close": 93.0},
        ]
    )

    actions = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=FvgChannelConfig(enabled=True, window=3),
        close_volume_entry_filter_config=CloseVolumeEntryFilterConfig(enabled=False, window=3, minimum_volume_ratio=1.0),
    )

    assert actions[0].action_type == StrategyActionType.ENTER_SHORT
    assert actions[0].metadata["close_volume_entry_filter"]["enabled"] is False


def test_fvg_channel_duplicate_geometry_emits_skip_diagnostic() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 108.0, "low": 102.8, "close": 102.8},
            {"timestamp": 4, "high": 114.25, "low": 105.0, "close": 113.5},
        ]
    )
    seen_channel_ids: set[str] = set()
    config = FvgChannelConfig(enabled=True, window=3)

    first = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )
    duplicate = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )

    assert first[0].metadata["channel_duplicate"] is False
    assert len(seen_channel_ids) == 1
    assert duplicate[0].action_type == StrategyActionType.SKIP
    assert duplicate[0].reason == "FVG_CHANNEL_DUPLICATE"
    assert duplicate[0].metadata["channel_duplicate"] is True
    assert duplicate[0].metadata["channel_id"] == first[0].metadata["channel_id"]


def test_fvg_channel_retest_not_filled_does_not_mark_channel_seen() -> None:
    candles = _candles(
        [
            {"timestamp": 0, "high": 105.0, "low": 100.0, "close": 104.0},
            {"timestamp": 1, "high": 111.0, "low": 101.0, "close": 110.0},
            {"timestamp": 2, "high": 107.0, "low": 102.0, "close": 106.0},
            {"timestamp": 3, "high": 110.0, "low": 104.0, "close": 106.0},
        ]
    )
    seen_channel_ids: set[str] = set()
    config = FvgChannelConfig(enabled=True, window=3)

    first = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )
    second = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )

    assert first[0].action_type == StrategyActionType.SKIP
    assert first[0].reason == "FVG_CHANNEL_RETEST_NOT_FILLED"
    assert first[0].metadata["channel_seen_after_filled_candidate"] is False
    assert len(seen_channel_ids) == 0
    assert second[0].reason == "FVG_CHANNEL_RETEST_NOT_FILLED"


def test_fvg_channel_standalone_scan_is_opt_in() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 0, "open": 104.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 10.0},
            {"timestamp": 1, "open": 110.0, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 10.0},
            {"timestamp": 2, "open": 106.0, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 10.0},
            {"timestamp": 3, "open": 104.0, "high": 108.0, "low": 102.8, "close": 102.8, "volume": 10.0},
            {"timestamp": 4, "open": 113.5, "high": 114.25, "low": 105.0, "close": 113.5, "volume": 10.0},
        ]
    )

    _, actions = _build_actions(
        candles,
        "FAIR_VALUE_GAP",
        fvg_channel_config=FvgChannelConfig(enabled=True, window=3),
    )

    assert not [
        action
        for action in actions
        if (action.metadata or {}).get("channel_candidate_source") == "standalone_visible_prefix_scan"
    ]


def test_fvg_channel_scanner_trades_each_distinct_visible_channel() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 0, "open": 104.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 10.0},
            {"timestamp": 1, "open": 110.0, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 10.0},
            {"timestamp": 2, "open": 106.0, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 10.0},
            {"timestamp": 3, "open": 104.0, "high": 108.0, "low": 102.8, "close": 102.8, "volume": 10.0},
            {"timestamp": 4, "open": 113.5, "high": 114.25, "low": 105.0, "close": 113.5, "volume": 10.0},
            {"timestamp": 5, "open": 204.0, "high": 205.0, "low": 200.0, "close": 204.0, "volume": 10.0},
            {"timestamp": 6, "open": 210.0, "high": 211.0, "low": 201.0, "close": 210.0, "volume": 10.0},
            {"timestamp": 7, "open": 206.0, "high": 207.0, "low": 202.0, "close": 206.0, "volume": 10.0},
            {"timestamp": 8, "open": 204.0, "high": 208.0, "low": 202.8, "close": 202.8, "volume": 10.0},
            {"timestamp": 9, "open": 213.5, "high": 214.25, "low": 205.0, "close": 213.5, "volume": 10.0},
        ]
    )

    _, actions = _build_actions(
        candles,
        "FAIR_VALUE_GAP",
        fvg_channel_config=FvgChannelConfig(enabled=True, window=3, standalone_scan_enabled=True),
    )

    entry_actions = [
        action
        for action in actions
        if action.action_type in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}
    ]
    channel_ids = {action.metadata["channel_id"] for action in entry_actions}
    assert len(entry_actions) >= 2
    assert len(channel_ids) >= 2
    assert all(action.metadata["channel_duplicate"] is False for action in entry_actions)
    assert all(action.metadata["channel_candidate_source"] == "standalone_visible_prefix_scan" for action in entry_actions)


def test_fvg_channel_distinct_non_overlapping_channels_fill_two_trades() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 0, "open": 104.0, "high": 105.0, "low": 100.0, "close": 104.0, "volume": 10.0},
            {"timestamp": 1, "open": 110.0, "high": 111.0, "low": 101.0, "close": 110.0, "volume": 10.0},
            {"timestamp": 2, "open": 106.0, "high": 107.0, "low": 102.0, "close": 106.0, "volume": 10.0},
            {"timestamp": 3, "open": 104.0, "high": 108.0, "low": 102.8, "close": 102.8, "volume": 10.0},
            {"timestamp": 4, "open": 113.5, "high": 114.25, "low": 105.0, "close": 113.5, "volume": 10.0},
            {"timestamp": 5, "open": 204.0, "high": 205.0, "low": 200.0, "close": 204.0, "volume": 10.0},
            {"timestamp": 6, "open": 210.0, "high": 211.0, "low": 201.0, "close": 210.0, "volume": 10.0},
            {"timestamp": 7, "open": 206.0, "high": 207.0, "low": 202.0, "close": 206.0, "volume": 10.0},
            {"timestamp": 8, "open": 204.0, "high": 208.0, "low": 202.8, "close": 202.8, "volume": 10.0},
            {"timestamp": 9, "open": 213.5, "high": 214.25, "low": 205.0, "close": 213.5, "volume": 10.0},
        ]
    )
    seen_channel_ids: set[str] = set()
    config = FvgChannelConfig(enabled=True, window=3)
    first = build_fvg_channel_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        candles.iloc[:3],
        candles.iloc[3:],
        entry_action_timestamp=2,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )
    second = build_fvg_channel_trade_actions(
        _Event("BULLISH", event_id="evt-2"),
        _plan("LONG"),
        candles.iloc[:8],
        candles.iloc[8:],
        entry_action_timestamp=7,
        position_side="LONG",
        channel_config=config,
        seen_channel_ids=seen_channel_ids,
    )

    result = run_strategy_backtest_engine(
        candles,
        [*first, *second],
        config=StrategyEngineConfig(starting_cash=100000.0, trade_quantity=1.0),
    )

    assert [execution.action_type for execution in result.executions] == [
        "ENTER_SHORT",
        "EXIT_SHORT",
        "ENTER_SHORT",
        "EXIT_SHORT",
    ]
    assert result.summary.trade_count == 4
    assert len({first[0].metadata["channel_id"], second[0].metadata["channel_id"]}) == 2


def test_cost_aware_entry_filter_blocks_infeasible_net_reward() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"high": 116.0, "low": 100.0, "close": 100.0}]),
        entry_action_timestamp=0,
        position_side="LONG",
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            enabled=True,
            min_net_reward_bps=20.0,
            min_net_rr=0.9,
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=200.0, spread_bps=200.0, slippage_bps=200.0),
            liquidity_role=LiquidityRole.TAKER,
        ),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "COST_INFEASIBLE_NET_RR"
    filter_metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert filter_metadata["blocked"] is True
    assert filter_metadata["estimated_round_trip_cost_bps"] == pytest.approx(1200.0)
    assert filter_metadata["net_reward_bps"] < 20.0


def test_cost_aware_entry_filter_metadata_is_attached_to_accepted_trade() -> None:
    actions = build_pattern_trade_actions(
        _Event("BULLISH"),
        _plan("LONG"),
        _candles([{"high": 116.0, "low": 100.0, "close": 100.0}]),
        entry_action_timestamp=0,
        position_side="LONG",
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            enabled=True,
            min_net_reward_bps=20.0,
            min_net_rr=0.9,
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=1.0, spread_bps=1.0, slippage_bps=1.0),
            liquidity_role=LiquidityRole.TAKER,
        ),
    )

    entry = actions[0]
    filter_metadata = entry.metadata["cost_aware_entry_filter"]
    assert entry.action_type == StrategyActionType.ENTER_LONG
    assert filter_metadata["blocked"] is False
    assert filter_metadata["net_reward_bps"] > 20.0
    assert filter_metadata["net_rr"] > 0.9


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
