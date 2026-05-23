from __future__ import annotations

import pytest
import pandas as pd

from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
    SimulatedMarginConfig,
)
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame([
        {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
        {"timestamp": 2, "open": 110, "high": 110, "low": 110, "close": 110, "volume": 1},
        {"timestamp": 3, "open": 90, "high": 90, "low": 90, "close": 90, "volume": 1},
        {"timestamp": 4, "open": 95, "high": 95, "low": 95, "close": 95, "volume": 1},
    ])


def _high_price_candles() -> pd.DataFrame:
    return pd.DataFrame([
        {"timestamp": 1, "open": 80000, "high": 80000, "low": 80000, "close": 80000, "volume": 1},
        {"timestamp": 2, "open": 79000, "high": 79000, "low": 79000, "close": 79000, "volume": 1},
    ])


def test_position_sizing_config_accepts_valid_modes() -> None:
    assert PositionSizingConfig(PositionSizingMode.FIXED_QUANTITY, value=1).mode is PositionSizingMode.FIXED_QUANTITY
    assert PositionSizingConfig(PositionSizingMode.CASH_FRACTION, value=0.5).value == 0.5
    assert PositionSizingConfig(PositionSizingMode.TARGET_NOTIONAL, value=2500).value == 2500


@pytest.mark.parametrize(
    "config",
    [
        {"mode": PositionSizingMode.FIXED_QUANTITY, "value": -1},
        {"mode": PositionSizingMode.FIXED_QUANTITY, "value": 0},
        {"mode": PositionSizingMode.FIXED_QUANTITY, "value": float("inf")},
        {"mode": PositionSizingMode.CASH_FRACTION, "value": None},
        {"mode": PositionSizingMode.CASH_FRACTION, "value": 0},
        {"mode": PositionSizingMode.CASH_FRACTION, "value": 1.5},
        {"mode": PositionSizingMode.TARGET_NOTIONAL, "value": None},
        {"mode": PositionSizingMode.TARGET_NOTIONAL, "value": 0},
        {"mode": PositionSizingMode.TARGET_NOTIONAL, "value": float("nan")},
    ],
)
def test_position_sizing_config_rejects_invalid_values(config: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        PositionSizingConfig(**config)


def test_action_quantity_precedes_engine_sizing_config() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=2)],
        config=StrategyEngineConfig(
            position_sizing=PositionSizingConfig(PositionSizingMode.CASH_FRACTION, value=0.5),
        ),
    )
    assert result.executions[0].quantity == pytest.approx(2.0)
    assert result.executions[0].metadata["position_sizing_source"] == "ACTION_QUANTITY"


def test_default_config_preserves_fixed_trade_quantity_when_action_quantity_missing() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1)],
        config=StrategyEngineConfig(trade_quantity=3),
    )
    assert result.executions[0].quantity == pytest.approx(3.0)
    assert result.summary.metadata["position_sizing"]["mode"] == "FIXED_QUANTITY"


def test_long_and_short_zero_cost_accounting() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=3, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=4, quantity=1),
    ])
    assert [e.side for e in result.executions] == ["BUY", "SELL", "SELL", "BUY"]
    assert result.summary.ending_position == 0
    assert result.summary.net_pnl == pytest.approx(5.0)


def test_partial_long_and_short_exits() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=2),
        StrategyAction(StrategyActionType.PARTIAL_EXIT_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    qtys = [e.quantity for e in result.executions if e.gross_pnl is not None]
    assert qtys == [1, 1]
    assert result.summary.ending_position == 0


def test_opposite_entry_skip_deterministic() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
    ])
    assert len(result.executions) == 2
    assert result.executions[1].quantity == 0.0
    assert result.executions[1].reason == "OPPOSITE_ENTRY_BLOCKED"
    metrics = result.summary.metadata["execution_metrics"]
    assert result.summary.trade_count == 1
    assert metrics["filled_execution_count"] == 1
    assert metrics["blocked_action_count"] == 1


def test_cost_applied_once_fee_and_not_double_counted() -> None:
    cfg = StrategyEngineConfig(
        transaction_cost_config=TransactionCostConfig(taker_fee_bps=10, spread_bps=10, slippage_bps=10),
        default_liquidity_role=LiquidityRole.TAKER,
    )
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1),
    ], config=cfg)
    entry, exit_ = result.executions
    assert entry.effective_price > entry.raw_price
    assert exit_.effective_price < exit_.raw_price
    assert exit_.net_pnl < exit_.gross_pnl
    assert exit_.net_pnl == pytest.approx(exit_.gross_pnl - exit_.total_cost)


def test_high_price_long_is_resized_to_affordable_quantity() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(starting_cash=10000),
    )
    execution = result.executions[0]
    assert execution.quantity == pytest.approx(0.125)
    assert execution.cash_after == pytest.approx(0.0)
    assert execution.metadata["resize_reason"] == "INSUFFICIENT_CASH_FOR_LONG"


def test_high_price_long_can_be_blocked_by_policy() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(
                insufficient_funds_policy=InsufficientFundsPolicy.BLOCK,
            ),
        ),
    )
    execution = result.executions[0]
    assert execution.quantity == 0.0
    assert execution.reason == "INSUFFICIENT_CASH_FOR_LONG"
    assert result.summary.trade_count == 0


@pytest.mark.parametrize("fraction,expected_quantity", [(0.25, 25), (0.5, 50), (1.0, 100)])
def test_cash_fraction_long_sizing(fraction: float, expected_quantity: float) -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(PositionSizingMode.CASH_FRACTION, value=fraction),
        ),
    )
    assert result.executions[0].quantity == pytest.approx(expected_quantity)


def test_target_notional_long_sizing_respects_cash() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(PositionSizingMode.TARGET_NOTIONAL, value=2500),
        ),
    )
    assert result.executions[0].quantity == pytest.approx(25.0)


def test_default_high_price_short_is_cash_bounded() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(starting_cash=10000),
    )
    execution = result.executions[0]
    assert execution.quantity == pytest.approx(0.125)
    assert execution.position_after == pytest.approx(-0.125)
    assert execution.metadata["resize_reason"] == "INSUFFICIENT_BUYING_POWER_FOR_SHORT"
    assert execution.short_proceeds_locked_after == pytest.approx(10000)
    assert execution.free_cash_after == pytest.approx(10000)


def test_blocked_high_price_short_does_not_count_as_filled_trade() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(
                insufficient_funds_policy=InsufficientFundsPolicy.BLOCK,
            ),
        ),
    )
    assert result.executions[0].reason == "INSUFFICIENT_BUYING_POWER_FOR_SHORT"
    assert result.executions[0].quantity == 0.0
    assert result.summary.trade_count == 0
    assert result.summary.metadata["execution_metrics"]["blocked_action_count"] == 1


def test_invalid_simulated_margin_leverage_rejected() -> None:
    with pytest.raises(ValueError):
        SimulatedMarginConfig(enabled=True, leverage=0)


def test_simulated_margin_initial_margin_blocks_when_insufficient() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            short_exposure_mode=ShortExposureMode.SIMULATED_MARGIN,
            simulated_margin=SimulatedMarginConfig(enabled=True, leverage=5),
        ),
    )
    execution = result.executions[0]
    assert execution.reason == "INSUFFICIENT_INITIAL_MARGIN"
    assert execution.quantity == 0.0
    assert execution.metadata["required_initial_margin"] == pytest.approx(16000)


def test_simulated_margin_allows_explicit_sufficient_leverage() -> None:
    result = run_strategy_backtest_engine(
        _high_price_candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            short_exposure_mode=ShortExposureMode.SIMULATED_MARGIN,
            simulated_margin=SimulatedMarginConfig(enabled=True, leverage=10),
        ),
    )
    execution = result.executions[0]
    assert execution.quantity == pytest.approx(1.0)
    assert execution.metadata["required_initial_margin"] == pytest.approx(8000)
    assert execution.margin_used_after == pytest.approx(8000)
    assert execution.free_cash_after == pytest.approx(2000)


def test_short_drawdown_tracked() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=4, quantity=1),
    ])
    assert result.summary.max_drawdown < 0


def test_profitable_short_realized_pnl_and_win_count() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    close_execution = result.executions[-1]
    assert close_execution.side == "BUY"
    assert close_execution.gross_pnl == pytest.approx(20.0)
    assert close_execution.net_pnl == pytest.approx(20.0)
    assert result.equity_points[-1].realized_pnl == pytest.approx(20.0)
    assert result.summary.win_count == 1
    assert result.summary.loss_count == 0


def test_losing_short_realized_pnl_and_loss_count() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=2, quantity=1),
    ])
    close_execution = result.executions[-1]
    assert close_execution.side == "BUY"
    assert close_execution.gross_pnl == pytest.approx(-10.0)
    assert close_execution.net_pnl == pytest.approx(-10.0)
    assert result.equity_points[-1].realized_pnl == pytest.approx(-10.0)
    assert result.summary.win_count == 0
    assert result.summary.loss_count == 1


def test_allow_short_false_blocks_short_entries_deterministically() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(allow_short=False),
    )
    assert result.summary.trade_count == 0
    assert result.summary.ending_position == 0
    assert result.summary.ending_cash == pytest.approx(10000.0)


def test_summary_includes_short_model_limitations_and_short_performance_metadata() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    metadata = result.summary.metadata
    assert metadata["limitations"] == [
        "No borrow fees modeled",
        "No futures funding modeled",
        "No maintenance margin or liquidation model",
    ]
    assert metadata["short_performance"] == {
        "short_close_count": 1,
        "short_win_count": 1,
        "short_loss_count": 0,
    }


def test_summary_includes_skip_and_partial_exit_metrics() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.SKIP, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=2, quantity=2),
        StrategyAction(StrategyActionType.PARTIAL_EXIT_LONG, timestamp=3, quantity=1),
    ])
    metrics = result.summary.metadata["execution_metrics"]
    assert metrics["skipped_action_count"] == 1
    assert metrics["entry_count"] == 1
    assert metrics["exit_count"] == 1
    assert metrics["partial_exit_count"] == 1
    assert metrics["full_exit_count"] == 0
    assert metrics["open_ending_position"] == pytest.approx(1.0)
