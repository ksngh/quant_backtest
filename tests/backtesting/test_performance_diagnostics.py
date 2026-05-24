from __future__ import annotations

from quant_bitcoin.backtesting.performance_diagnostics import calculate_backtest_performance_diagnostics


def _codes(diagnostics: dict[str, object]) -> set[str]:
    return {str(flag["code"]) for flag in diagnostics["flags"]}


def _flag(diagnostics: dict[str, object], code: str) -> dict[str, object]:
    return next(flag for flag in diagnostics["flags"] if flag["code"] == code)


def test_negative_expectancy_low_hit_rate_and_poor_payoff_are_flagged() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(
        {
            "performance_metrics": {"max_drawdown": -0.05, "max_drawdown_duration_periods": 2},
            "trade_attribution": {
                "trade_metrics": {
                    "completed_trade_count": 12,
                    "expectancy": -4.0,
                    "hit_ratio": 0.25,
                    "payoff_ratio": 0.7,
                }
            },
            "cost_summary": {"zero_transaction_cost_assumption": False},
        }
    )

    assert {"NEGATIVE_EXPECTANCY", "LOW_HIT_RATE", "POOR_PAYOFF_RATIO"} <= _codes(diagnostics)


def test_high_gross_pnl_but_negative_net_pnl_is_critical_cost_drag() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(
        {
            "performance_metrics": {},
            "trade_attribution": {"trade_metrics": {"completed_trade_count": 8}},
            "cost_summary": {"gross_pnl": 10.0, "net_pnl": -2.0, "cost_to_gross_pnl_ratio": 1.2},
        }
    )

    cost_flag = _flag(diagnostics, "HIGH_COST_DRAG")
    assert cost_flag["severity"] == "CRITICAL"


def test_drawdown_exposure_turnover_and_zero_cost_flags() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(
        {
            "performance_metrics": {"max_drawdown": -0.25, "max_drawdown_duration_periods": 33},
            "trade_attribution": {
                "trade_metrics": {"completed_trade_count": 7},
                "exposure": {"exposure_fraction": 0.02},
                "turnover": {"turnover_ratio": 12.5},
            },
            "cost_summary": {"zero_transaction_cost_assumption": True},
        }
    )

    assert {
        "LARGE_OR_PERSISTENT_DRAWDOWN",
        "LOW_EXPOSURE",
        "HIGH_TURNOVER",
        "ZERO_COST_ASSUMPTION",
    } <= _codes(diagnostics)


def test_no_completed_trades_short_simulation_and_exit_reason_dominance_flags() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(
        {
            "performance_metrics": {"max_drawdown": 0.0},
            "trade_attribution": {
                "trade_metrics": {"completed_trade_count": 0},
                "attribution": {
                    "by_exit_reason": {
                        "SOFT_INVALIDATION+TIME_STOP+HARD_STOP": {"completed_trade_count": 3},
                    }
                },
            },
            "cost_summary": {"zero_transaction_cost_assumption": False},
            "short_performance": {"short_close_count": 1},
            "short_economics": {"scope": "backtest_only_simulation"},
        }
    )

    assert {
        "NO_COMPLETED_TRADES",
        "SHORT_SIMULATION_ONLY",
        "SOFT_INVALIDATION_DOMINANT",
        "TIME_STOP_DOMINANT",
        "STOP_LOSS_DOMINANT",
    } <= _codes(diagnostics)
    assert diagnostics["inference_strength"] == "WEAK"


def test_fill_reference_divergence_and_negative_take_profit_anomaly() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(
        {"performance_metrics": {}, "trade_attribution": {}, "cost_summary": {}},
        executions=[
            {
                "exit_reason": "TAKE_PROFIT",
                "gross_pnl": -1.0,
                "net_pnl": -1.2,
                "metadata": {
                    "fill_price": 110.0,
                    "entry_reference": 100.0,
                    "risk_plan_aligned_to_fill": True,
                },
            }
        ],
    )

    assert {"ENTRY_FILL_REFERENCE_DIVERGENCE", "TAKE_PROFIT_NEGATIVE_PNL_ANOMALY"} <= _codes(diagnostics)
    assert _flag(diagnostics, "TAKE_PROFIT_NEGATIVE_PNL_ANOMALY")["severity"] == "CRITICAL"


def test_missing_metadata_produces_partial_diagnostics_with_warnings() -> None:
    diagnostics = calculate_backtest_performance_diagnostics(None)

    assert diagnostics["schema_version"] == "backtest_performance_diagnostics_v1"
    assert diagnostics["flags"] == ()
    assert "performance_metrics metadata missing" in diagnostics["warnings"]
    assert diagnostics["inference_strength"] == "PARTIAL"
