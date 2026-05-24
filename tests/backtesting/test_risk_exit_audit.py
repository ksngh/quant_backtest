import inspect

import pytest

from quant_bitcoin.backtesting.risk_exit_audit import calculate_risk_exit_audit


def _row(action_type, exit_reason, net_pnl, r, *, side="LONG", entry=100.0, stop=95.0, exit_price=105.0, target_name=None):
    return {
        "action_type": action_type,
        "exit_reason": exit_reason,
        "net_pnl": net_pnl,
        "gross_pnl": net_pnl,
        "realized_r_multiple": r,
        "metadata": {
            "position_side": side,
            "entry_price": entry,
            "fill_price": entry,
            "stop_price": stop,
            "exit_price": exit_price,
            "target_name": target_name,
            "risk_per_unit": abs(entry - stop),
        },
    }


def test_exit_reason_aggregation_and_partial_contribution() -> None:
    audit = calculate_risk_exit_audit(
        (
            _row("PARTIAL_EXIT_LONG", "TAKE_PROFIT", 3.0, 1.0, target_name="TP1"),
            _row("EXIT_LONG", "TIME_STOP", -1.0, -0.2),
        )
    )

    assert audit["exit_reason_distribution"]["TAKE_PROFIT"]["count"] == 1
    assert audit["exit_reason_distribution"]["TIME_STOP"]["average_net_pnl"] == pytest.approx(-1.0)
    assert audit["partial_exit"]["partial_exit_net_pnl"] == pytest.approx(3.0)
    assert audit["partial_exit"]["partial_exit_pnl_contribution_ratio"] == pytest.approx(1.5)
    assert audit["target_quality"]["first_target_hit_rate"] == pytest.approx(0.5)


def test_stop_and_soft_invalidation_dominance_flags_for_negative_expectancy() -> None:
    stop_audit = calculate_risk_exit_audit(
        (
            _row("EXIT_LONG", "HARD_STOP", -5.0, -1.0),
            _row("EXIT_LONG", "HARD_STOP", -4.0, -1.0),
            _row("EXIT_LONG", "TIME_STOP", 1.0, 0.2),
        ),
        {"trade_attribution": {"trade_metrics": {"expectancy": -2.0}}},
    )
    soft_audit = calculate_risk_exit_audit(
        (
            _row("EXIT_LONG", "SOFT_INVALIDATION", -2.0, -0.4),
            _row("EXIT_LONG", "SOFT_INVALIDATION", -1.0, -0.2),
        ),
        {"trade_attribution": {"trade_metrics": {"expectancy": -1.0}}},
    )

    assert "HARD_STOP_DOMINATES_NEGATIVE_EXPECTANCY" in {flag["code"] for flag in stop_audit["flags"]}
    assert "SOFT_INVALIDATION_DOMINATES_NEGATIVE_EXPECTANCY" in {flag["code"] for flag in soft_audit["flags"]}


def test_direction_validation_for_long_and_short_targets_and_stops() -> None:
    audit = calculate_risk_exit_audit(
        (
            _row("EXIT_LONG", "TAKE_PROFIT", 1.0, 0.5, side="LONG", entry=100.0, stop=101.0, exit_price=99.0),
            _row("EXIT_SHORT", "TAKE_PROFIT", 1.0, 0.5, side="SHORT", entry=100.0, stop=99.0, exit_price=101.0),
        )
    )

    codes = {warning["code"] for warning in audit["validation"]["warnings"]}
    assert {"LONG_STOP_NOT_BELOW_FILL", "LONG_TARGET_NOT_ABOVE_FILL", "SHORT_STOP_NOT_ABOVE_FILL", "SHORT_TARGET_NOT_BELOW_FILL"} <= codes
    assert audit["validation"]["critical_count"] == 4


def test_risk_exit_audit_module_has_no_live_execution_imports() -> None:
    import quant_bitcoin.backtesting.risk_exit_audit as risk_exit_audit

    source = inspect.getsource(risk_exit_audit)
    assert "Binance" not in source
    assert "PostgresCandleDataProvider" not in source
    assert "order endpoint" not in source
