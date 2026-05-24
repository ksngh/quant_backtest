from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortEconomicsConfig,
)
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.indicators import (
    PatternRegimeThresholdConfig,
    PatternRegimeThresholdOverride,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 102, "high": 103, "low": 101, "close": 102, "volume": 10},
            {"timestamp": 3, "open": 105, "high": 106, "low": 104, "close": 105, "volume": 10},
        ]
    )


def test_engine_buy_sell_and_equity_accounting() -> None:
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, metadata={"pattern_event_id": "e1", "risk_per_unit": 2.0}),
        StrategyAction(
            StrategyActionType.PARTIAL_EXIT_LONG,
            timestamp=2,
            quantity=0.4,
            metadata={
                "exit_reason": "TAKE_PROFIT",
                "target_source": "R_MULTIPLE",
                "exit_metadata": {"target_source": "R_MULTIPLE", "intrabar_policy": "CONSERVATIVE"},
            },
        ),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=3, quantity=0.6, metadata={"exit_reason": "TIME_STOP"}),
    ]

    result = run_strategy_backtest_engine(_candles(), actions, config=StrategyEngineConfig(starting_cash=10000, trade_quantity=1.0))

    assert result.summary.buy_count == 1
    assert result.summary.sell_count == 2
    assert result.summary.trade_count == 3
    assert result.summary.ending_position == 0
    assert result.summary.ending_cash == 10003.8
    assert result.summary.final_equity == 10003.8
    assert result.executions[0].side == "BUY"
    assert result.executions[0].execution_side == "BUY"
    assert result.executions[0].position_signal == "LONG_ENTRY"
    assert result.executions[0].position_side == "LONG"
    assert result.executions[1].side == "SELL"
    assert result.executions[1].execution_side == "SELL"
    assert result.executions[1].position_signal == "LONG_PARTIAL_EXIT"
    assert result.executions[1].position_side == "LONG"
    assert result.executions[1].quantity == 0.4
    assert result.executions[2].quantity == 0.6
    assert result.executions[1].exit_reason == "TAKE_PROFIT"
    assert result.equity_points[0].equity == 10000
    assert result.equity_points[1].equity == 10002
    attribution = result.summary.metadata["trade_attribution"]
    assert attribution["trade_metrics"]["completed_trade_count"] == 1
    assert attribution["trade_metrics"]["closing_execution_count"] == 2
    assert attribution["trade_metrics"]["partial_exit_execution_count"] == 1
    assert attribution["trade_metrics"]["expectancy"] == pytest.approx(3.8)
    assert attribution["attribution"]["by_position_side"]["LONG"]["completed_trade_count"] == 1
    assert attribution["attribution"]["by_exit_reason"]["TAKE_PROFIT+TIME_STOP"]["net_pnl"] == pytest.approx(3.8)
    timing = result.summary.metadata["timing_diagnostics"]
    assert timing["schema_version"] == "trade_timing_diagnostics_v1"
    assert timing["completed_trade_count"] == 1
    assert timing["trades"][0]["mfe_price"] == pytest.approx(6.0)
    assert timing["trades"][0]["mae_price"] == pytest.approx(1.0)
    audit = result.summary.metadata["risk_exit_audit"]
    assert audit["schema_version"] == "risk_exit_audit_v1"
    assert "outcome_attribution" in audit
    assert "path_attribution" in audit
    assert audit["target_quality"]["by_target_source"]["R_MULTIPLE"]["count"] == 1


def test_engine_summary_includes_pattern_score_lift_report() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 102, "high": 103, "low": 101, "close": 102, "volume": 10},
            {"timestamp": 3, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 4, "open": 104, "high": 105, "low": 103, "close": 104, "volume": 10},
        ]
    )
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
        StrategyAction(
            StrategyActionType.EXIT_LONG,
            timestamp=2,
            quantity=1.0,
            metadata={
                "pattern_score": 0.2,
                "pattern_type": "FAIR_VALUE_GAP",
                "pattern_direction": "BULLISH",
                "realized_r_multiple": -0.1,
            },
        ),
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=3, quantity=1.0),
        StrategyAction(
            StrategyActionType.EXIT_LONG,
            timestamp=4,
            quantity=1.0,
            metadata={
                "pattern_score": 0.9,
                "pattern_type": "FAIR_VALUE_GAP",
                "pattern_direction": "BULLISH",
                "realized_r_multiple": 0.4,
            },
        ),
    ]

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(starting_cash=10000, trade_quantity=1.0),
    )

    calibration = result.summary.metadata["score_calibration"]
    assert calibration["score_lift"]["interpretation"] == "POSITIVE_LIFT"
    assert calibration["pattern_direction_buckets"][0]["pattern_type"] == "FAIR_VALUE_GAP"
    assert calibration["pattern_direction_buckets"][0]["direction"] == "BULLISH"


def test_engine_rejects_unsorted_candles() -> None:
    candles = _candles().iloc[::-1]
    try:
        run_strategy_backtest_engine(candles, [])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "sorted" in str(exc)


def test_engine_rejects_duplicate_timestamps_before_actions_execute() -> None:
    candles = _candles()
    candles.loc[1, "timestamp"] = candles.loc[0, "timestamp"]
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)]

    with pytest.raises(ValueError, match="duplicate timestamp"):
        run_strategy_backtest_engine(candles, actions)


def test_engine_rejects_invalid_ohlc_before_actions_execute() -> None:
    candles = _candles()
    candles.loc[0, "high"] = 99
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)]

    with pytest.raises(ValueError, match="high below open/close"):
        run_strategy_backtest_engine(candles, actions)


def test_engine_detects_interval_gap_when_configured() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 102, "high": 103, "low": 101, "close": 102, "volume": 10},
        ]
    )

    with pytest.raises(ValueError, match="interval gap for 1m"):
        run_strategy_backtest_engine(
            candles,
            [],
            config=StrategyEngineConfig(enforce_candle_continuity=True),
        )


def test_engine_uses_explicit_requested_price_and_fallback_close() -> None:
    candles = _candles()
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, requested_price=99.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]
    result = run_strategy_backtest_engine(candles, actions)
    assert result.executions[0].raw_price == 99.0
    assert result.executions[1].raw_price == 102.0
    assert result.executions[0].execution_equity_after == 10000.0
    assert result.executions[0].mark_to_market_equity_after == 10001.0
    assert result.equity_points[0].equity == 10000.0
    assert result.equity_points[0].equity_valuation_price == 99.0
    assert "entry-candle execution-price equity" in (result.equity_points[0].equity_semantics or "")


def test_entry_candle_equity_uses_execution_price_then_next_close() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 105, "high": 106, "low": 104, "close": 105, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, requested_price=99.0)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(PositionSizingMode.CASH_FRACTION, value=1.0),
        ),
    )

    entry = result.executions[0]
    assert entry.quantity == pytest.approx(100.0)
    assert entry.cash_after == pytest.approx(100.0)
    assert entry.execution_equity_after == pytest.approx(10000.0)
    assert entry.mark_to_market_equity_after == pytest.approx(10100.0)
    assert entry.metadata["entry_sizing_valuation_price"] == pytest.approx(100.0)
    assert entry.metadata["conservative_entry_sizing_applied"] is True
    assert result.equity_points[0].equity == pytest.approx(10000.0)
    assert result.equity_points[0].equity_valuation_price == pytest.approx(99.0)
    assert result.equity_points[1].equity == pytest.approx(10600.0)
    assert result.equity_points[1].equity_valuation_price == pytest.approx(105.0)
    assert result.summary.final_equity == pytest.approx(10600.0)
    assert result.summary.metadata["performance_metrics"]["total_return"] == pytest.approx(0.06)


def test_engine_skips_invalid_explicit_price() -> None:
    candles = _candles()
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, requested_price=0.0)]
    result = run_strategy_backtest_engine(candles, actions)
    assert result.summary.trade_count == 0


def test_engine_attaches_market_regime_metadata_without_changing_fills() -> None:
    candles = _candles()
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]
    baseline = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(starting_cash=10000),
    )
    tagged = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            starting_cash=10000,
            market_regime_by_timestamp={
                1: {
                    "market_regime": "LOW_VOL_UPTREND",
                    "trend_regime": "UPTREND",
                    "liquidity_regime": "LOW",
                    "spread_regime": "WIDE",
                    "session_tag": "EU_US_OVERLAP",
                    "weekday_tag": "WEEKDAY",
                    "trading_value_percentile": 0.2,
                    "range_spread_proxy_percentile": 0.9,
                },
                2: {
                    "market_regime": "LOW_VOL_UPTREND",
                    "trend_regime": "UPTREND",
                    "liquidity_regime": "LOW",
                    "spread_regime": "WIDE",
                    "session_tag": "EU_US_OVERLAP",
                    "weekday_tag": "WEEKDAY",
                },
            },
        ),
    )

    assert [execution.price for execution in tagged.executions] == [execution.price for execution in baseline.executions]
    assert [execution.quantity for execution in tagged.executions] == [execution.quantity for execution in baseline.executions]
    assert tagged.executions[0].metadata["market_regime"] == "LOW_VOL_UPTREND"
    assert tagged.executions[0].metadata["market_regime_context"]["trend_regime"] == "UPTREND"
    assert tagged.executions[0].metadata["session"] == "EU_US_OVERLAP"
    assert tagged.executions[0].metadata["trading_value_percentile"] == 0.2
    assert tagged.summary.metadata["trade_attribution"]["attribution"]["by_market_regime"]["LOW_VOL_UPTREND"]["completed_trade_count"] == 1
    assert tagged.summary.metadata["trade_attribution"]["attribution"]["by_session"]["EU_US_OVERLAP"]["completed_trade_count"] == 1
    assert tagged.summary.metadata["trade_attribution"]["attribution"]["by_liquidity_regime"]["LOW"]["completed_trade_count"] == 1
    assert tagged.summary.metadata["trade_attribution"]["attribution"]["by_spread_regime"]["WIDE"]["completed_trade_count"] == 1


def test_engine_preserves_applied_pattern_regime_threshold_metadata() -> None:
    candles = _candles()
    actions = [
        StrategyAction(
            StrategyActionType.ENTER_LONG,
            timestamp=1,
            quantity=1.0,
            metadata={
                "pattern_type": "TRENDLINE_BREAK",
                "pattern_score": 0.9,
                "volume_ratio": 2.0,
                "break_distance_atr": 0.7,
            },
        )
    ]

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            starting_cash=10000,
            market_regime_by_timestamp={
                1: {
                    "market_regime": "HIGH_VOL_UPTREND",
                    "volatility_regime": "HIGH",
                }
            },
            pattern_regime_thresholds=PatternRegimeThresholdConfig(
                enabled=True,
                volatility_regime_overrides={
                    "HIGH": PatternRegimeThresholdOverride(
                        breakout_atr_multiplier=0.6
                    )
                },
            ),
        ),
    )

    metadata = result.executions[0].metadata["pattern_regime_thresholds"]
    assert result.executions[0].quantity == 1.0
    assert metadata["enabled"] is True
    assert metadata["blocked"] is False
    assert metadata["applied_thresholds"]["breakout_atr_multiplier"] == 0.6
    assert metadata["matched_overrides"] == ("volatility_regime:HIGH",)
    assert result.summary.metadata["pattern_regime_thresholds"]["enabled"] is True


def test_engine_blocks_entry_when_regime_threshold_fails() -> None:
    candles = _candles()
    actions = [
        StrategyAction(
            StrategyActionType.ENTER_LONG,
            timestamp=1,
            quantity=1.0,
            metadata={
                "pattern_type": "TRENDLINE_BREAK",
                "pattern_score": 0.9,
                "volume_ratio": 2.0,
                "break_distance_atr": 0.3,
            },
        )
    ]

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            starting_cash=10000,
            market_regime_by_timestamp={1: {"volatility_regime": "HIGH"}},
            pattern_regime_thresholds=PatternRegimeThresholdConfig(
                enabled=True,
                volatility_regime_overrides={
                    "HIGH": PatternRegimeThresholdOverride(
                        breakout_atr_multiplier=0.8
                    )
                },
            ),
        ),
    )

    assert result.summary.trade_count == 0
    assert result.executions[0].quantity == 0.0
    assert result.executions[0].reason == "REGIME_BREAKOUT_ATR_BELOW_MINIMUM"
    assert result.executions[0].metadata["pattern_regime_thresholds"]["blocked"] is True


def test_engine_records_cost_summary_and_volatility_slippage() -> None:
    from quant_bitcoin.backtesting.costs import TransactionCostConfig

    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 110, "low": 90, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 110, "high": 121, "low": 99, "close": 110, "volume": 10},
        ]
    )
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            transaction_cost_config=TransactionCostConfig(
                taker_fee_bps=10.0,
                spread_bps=5.0,
                slippage_bps=1.0,
                volatility_slippage_multiplier=0.01,
            )
        ),
    )

    entry, exit_ = result.executions
    assert entry.effective_price > 100.0
    assert exit_.effective_price < 110.0
    assert entry.metadata["volatility_bps"] == pytest.approx(2000.0)
    assert entry.metadata["effective_slippage_bps"] == pytest.approx(21.0)
    assert result.summary.gross_pnl > result.summary.net_pnl
    assert result.summary.metadata["cost_summary"]["total_cost"] == pytest.approx(entry.total_cost + exit_.total_cost)
    assert result.summary.metadata["cost_summary"]["zero_transaction_cost_assumption"] is False
    assert result.summary.metadata["transaction_cost"]["zero_transaction_cost_assumption"] is False


def test_engine_marks_zero_cost_assumption() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)],
    )

    assert result.summary.metadata["cost_summary"]["zero_transaction_cost_assumption"] is True
    assert result.summary.metadata["cost_profile"]["profile_key"] == "zero"
    assert result.summary.metadata["cost_profile"]["zero_cost_profile"] is True


def test_strict_cost_mode_blocks_zero_cost_1m_pattern_run() -> None:
    with pytest.raises(ValueError, match="strict cost mode blocks zero-cost 1m pattern runs"):
        run_strategy_backtest_engine(
            _candles(),
            [
                StrategyAction(
                    StrategyActionType.ENTER_LONG,
                    timestamp=1,
                    quantity=1.0,
                    metadata={"pattern_type": "FAIR_VALUE_GAP"},
                )
            ],
            config=StrategyEngineConfig(strict_zero_cost_1m_pattern_runs=True),
        )


def test_zero_cost_1m_pattern_run_emits_high_severity_warning() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                quantity=1.0,
                metadata={"pattern_type": "FAIR_VALUE_GAP"},
            )
        ],
    )

    cost_summary = result.summary.metadata["cost_summary"]
    assert cost_summary["zero_transaction_cost_assumption"] is True
    assert cost_summary["diagnostic_severity"] == "HIGH"
    assert "zero fees" in cost_summary["zero_cost_warning"]


def test_cost_sensitivity_report_is_deterministic() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(include_cost_sensitivity_report=True),
    )

    report = result.summary.metadata["cost_sensitivity_report"]
    assert report["schema_version"] == "transaction_cost_sensitivity_report_v1"
    assert [row["profile_key"] for row in report["profiles"]] == [
        "zero",
        "binance_spot_taker_baseline",
        "conservative_crypto_1m",
        "high_slippage_stress",
    ]
    assert report["profiles"][0]["estimated_total_cost"] == pytest.approx(0.0)
    assert report["profiles"][1]["static_cost_bps"] == pytest.approx(12.0)


def test_disabled_short_economics_preserves_short_results() -> None:
    actions = [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1.0),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1.0),
    ]

    baseline = run_strategy_backtest_engine(_candles(), actions)
    disabled = run_strategy_backtest_engine(
        _candles(),
        actions,
        config=StrategyEngineConfig(
            short_economics=ShortEconomicsConfig(
                enabled=False,
                borrow_fee_bps_per_day=100.0,
                funding_bps_per_interval=50.0,
                maintenance_margin_rate=0.05,
            )
        ),
    )

    assert disabled.summary.ending_cash == pytest.approx(baseline.summary.ending_cash)
    assert disabled.summary.net_pnl == pytest.approx(baseline.summary.net_pnl)
    assert disabled.summary.metadata["short_economics"]["enabled"] is False
    assert disabled.summary.metadata["short_economics"]["scope"] == "backtest_only_simulation"
    assert disabled.summary.metadata["short_economics"]["borrow_fees_modeled"] is False
    assert disabled.summary.metadata["limitations"] == [
        "No borrow fees modeled",
        "No futures funding modeled",
        "No maintenance margin or liquidation model",
    ]


def test_short_borrow_fee_accrues_over_multiple_candles() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2026-01-01T00:00:00Z", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": "2026-01-02T00:00:00Z", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": "2026-01-03T00:00:00Z", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=candles.iloc[2]["timestamp"], quantity=1.0),
        ],
        config=StrategyEngineConfig(
            short_economics=ShortEconomicsConfig(
                enabled=True,
                borrow_fee_bps_per_day=100.0,
            )
        ),
    )

    economics = result.summary.metadata["short_economics"]
    assert economics["total_borrow_cost"] == pytest.approx(2.0)
    assert economics["total_carrying_cost"] == pytest.approx(2.0)
    assert result.summary.ending_cash == pytest.approx(9998.0)
    assert result.summary.net_pnl == pytest.approx(-2.0)
    assert result.equity_points[-1].short_carrying_cost_cumulative == pytest.approx(2.0)


def test_short_funding_fee_applies_by_interval() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 3, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(
            interval="1d",
            short_economics=ShortEconomicsConfig(
                enabled=True,
                funding_bps_per_interval=50.0,
            ),
        ),
    )

    economics = result.summary.metadata["short_economics"]
    assert economics["total_funding_cost"] == pytest.approx(1.0)
    assert economics["funding_event_count"] == 2
    assert result.summary.ending_cash == pytest.approx(9999.0)
    assert result.summary.net_pnl == pytest.approx(-1.0)


def test_short_liquidation_diagnostic_flags_adverse_move_without_execution() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 190, "high": 200, "low": 190, "close": 190, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1.0)],
        config=StrategyEngineConfig(
            starting_cash=100.0,
            short_economics=ShortEconomicsConfig(
                enabled=True,
                maintenance_margin_rate=0.05,
            ),
        ),
    )

    diagnostics = result.summary.metadata["short_economics"]["liquidation_diagnostics"]
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["would_liquidate"] is True
    assert diagnostics["event_count"] == 1
    assert diagnostics["events"][0]["adverse_high"] == pytest.approx(200.0)
    assert diagnostics["events"][0]["estimated_liquidation_price"] == pytest.approx(200.0 / 1.05)
    assert result.summary.ending_position == pytest.approx(-1.0)
    assert result.equity_points[-1].short_would_liquidate is True


def test_engine_sizes_entry_by_equity_risk_fraction() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                metadata={"risk_per_unit": 100.0},
            )
        ],
        config=StrategyEngineConfig(
            starting_cash=10000.0,
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    assert result.executions[0].quantity == pytest.approx(1.0)
    assert result.executions[0].metadata["position_sizing_mode"] == "EQUITY_RISK_FRACTION"
    assert result.executions[0].metadata["resolved_risk_amount"] == pytest.approx(100.0)
    assert result.executions[0].metadata["sizing_risk_source"] == "ACTION_OVERRIDE"


def test_engine_blocks_risk_fraction_without_risk_per_unit() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1)],
        config=StrategyEngineConfig(
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    assert result.summary.trade_count == 0
    assert result.executions[0].quantity == 0.0
    assert result.executions[0].reason == "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"
    assert result.executions[0].metadata["block_reason"] == "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"
    assert result.executions[0].metadata["sizing_risk_source"] == "MISSING"


def test_pattern_risk_fraction_blocks_stale_reference_risk() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                requested_price=110.0,
                metadata={
                    "canonical_pattern_action": True,
                    "pattern_type": "FAIR_VALUE_GAP",
                    "risk_per_unit": 5.0,
                    "original_risk_per_unit": 5.0,
                    "fill_adjusted_risk_per_unit": 15.0,
                    "sizing_risk_source": "ORIGINAL_REFERENCE",
                },
            )
        ],
        config=StrategyEngineConfig(
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    execution = result.executions[0]
    assert execution.quantity == 0.0
    assert execution.reason == "STALE_RISK_PER_UNIT_FOR_RISK_SIZING"
    assert execution.metadata["sizing_risk_source"] == "ORIGINAL_REFERENCE"
    assert execution.metadata["stale_risk_per_unit"] == pytest.approx(5.0)
    assert execution.metadata["fill_adjusted_risk_per_unit"] == pytest.approx(15.0)


def test_action_quantity_override_bypasses_pattern_risk_sizing() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                quantity=2.0,
                requested_price=110.0,
                metadata={
                    "canonical_pattern_action": True,
                    "pattern_type": "FAIR_VALUE_GAP",
                    "risk_per_unit": 5.0,
                    "original_risk_per_unit": 5.0,
                    "fill_adjusted_risk_per_unit": 15.0,
                },
            )
        ],
        config=StrategyEngineConfig(
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    execution = result.executions[0]
    assert execution.quantity == pytest.approx(2.0)
    assert execution.metadata["position_sizing_source"] == "ACTION_QUANTITY"
    assert execution.metadata["sizing_risk_source"] == "ACTION_OVERRIDE"


def test_engine_blocks_entries_after_consecutive_loss_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
            {"timestamp": 3, "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_consecutive_losses=1)),
    )

    assert result.summary.trade_count == 2
    assert result.executions[-1].quantity == 0.0
    assert result.executions[-1].reason == "RISK_GUARD_MAX_CONSECUTIVE_LOSSES"
    assert result.executions[-1].metadata["guardrail_scope"] == "backtest_only"


def test_engine_blocks_entries_after_drawdown_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 80, "high": 81, "low": 79, "close": 80, "volume": 10},
            {"timestamp": 3, "open": 80, "high": 81, "low": 79, "close": 80, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_account_drawdown=0.001)),
    )

    assert result.executions[-1].reason == "RISK_GUARD_MAX_DRAWDOWN"


def test_guardrail_default_does_not_force_close_open_position() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 80, "high": 80, "low": 80, "close": 80, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)],
        config=StrategyEngineConfig(
            starting_cash=100.0,
            guardrails=BacktestGuardrailConfig(max_account_drawdown=0.1),
        ),
    )

    assert result.summary.ending_position == pytest.approx(1.0)
    assert len(result.executions) == 1


def test_guardrail_forced_exit_closes_open_long_on_drawdown_breach() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 80, "high": 80, "low": 80, "close": 80, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)],
        config=StrategyEngineConfig(
            starting_cash=100.0,
            guardrails=BacktestGuardrailConfig(
                max_account_drawdown=0.1,
                close_open_position_on_breach=True,
            ),
        ),
    )

    forced_exit = result.executions[-1]
    assert forced_exit.side == "SELL"
    assert forced_exit.action_type == "EXIT_LONG"
    assert forced_exit.reason == "RISK_GUARD_MAX_DRAWDOWN"
    assert forced_exit.exit_reason == "GUARDRAIL_FORCED_EXIT"
    assert forced_exit.metadata["guardrail_forced_exit"] is True
    assert forced_exit.metadata["forced_exit_price_source"] == "CURRENT_CANDLE_CLOSE"
    assert result.summary.ending_position == pytest.approx(0.0)
    assert result.summary.ending_cash == pytest.approx(80.0)


def test_guardrail_forced_exit_closes_open_short_with_buy_side() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 120, "high": 120, "low": 120, "close": 120, "volume": 10},
        ]
    )

    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1.0)],
        config=StrategyEngineConfig(
            starting_cash=100.0,
            guardrails=BacktestGuardrailConfig(
                max_account_drawdown=0.1,
                close_open_position_on_breach=True,
            ),
        ),
    )

    forced_exit = result.executions[-1]
    assert forced_exit.side == "BUY"
    assert forced_exit.action_type == "EXIT_SHORT"
    assert forced_exit.reason == "RISK_GUARD_MAX_DRAWDOWN"
    assert forced_exit.metadata["guardrail_forced_exit"] is True
    assert result.summary.ending_position == pytest.approx(0.0)
    assert result.summary.ending_cash == pytest.approx(80.0)


def test_max_position_notional_cap_blocks_oversized_entry() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=2.0)],
        config=StrategyEngineConfig(
            guardrails=BacktestGuardrailConfig(max_position_notional=100.0),
            position_sizing=PositionSizingConfig(
                insufficient_funds_policy=InsufficientFundsPolicy.BLOCK,
            ),
        ),
    )

    execution = result.executions[0]
    assert execution.quantity == 0.0
    assert execution.reason == "RISK_GUARD_MAX_POSITION_NOTIONAL"
    assert execution.metadata["entry_exposure_cap_applied"] is True
    assert execution.metadata["entry_exposure_requested_notional"] == pytest.approx(200.0)
    assert execution.metadata["entry_exposure_cap_notional"] == pytest.approx(100.0)


def test_max_symbol_notional_cap_resizes_entry() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=2.0)],
        config=StrategyEngineConfig(
            guardrails=BacktestGuardrailConfig(max_symbol_notional=100.0),
        ),
    )

    execution = result.executions[0]
    assert execution.quantity == pytest.approx(1.0)
    assert execution.metadata["resize_reason"] == "RISK_GUARD_MAX_SYMBOL_NOTIONAL"
    assert execution.metadata["entry_exposure_cap_name"] == "max_symbol_notional"


def test_engine_blocks_entries_after_daily_loss_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-01-01T00:00:00Z"), "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": pd.Timestamp("2026-01-01T00:01:00Z"), "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
            {"timestamp": pd.Timestamp("2026-01-01T00:02:00Z"), "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[2]["timestamp"], quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_daily_loss=5.0)),
    )

    assert result.executions[-1].reason == "RISK_GUARD_MAX_DAILY_LOSS"
