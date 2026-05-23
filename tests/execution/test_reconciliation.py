from __future__ import annotations

import pytest

from quant_bitcoin.execution import (
    ExecutionFill,
    ExecutionReport,
    calculate_fill_vwap,
    calculate_side_aware_slippage_bps,
    reconcile_execution_report,
)


def _report(side: str = "BUY", fills=()):
    return ExecutionReport(
        intent_id="intent-1",
        client_order_id="client-1",
        symbol="BTCUSDT",
        status="FILLED",
        action_type="ENTER_LONG" if side == "BUY" else "EXIT_LONG",
        position_side="LONG",
        execution_side=side,
        requested_quantity=1.0,
        executed_quantity=sum(fill.quantity for fill in fills),
        fills=tuple(fills),
    )


def test_vwap_for_one_fill() -> None:
    assert calculate_fill_vwap([ExecutionFill(price=100, quantity=2)]) == 100


def test_vwap_for_multiple_fills() -> None:
    fills = [ExecutionFill(price=100, quantity=1), ExecutionFill(price=110, quantity=3)]

    assert calculate_fill_vwap(fills) == pytest.approx(107.5)


def test_buy_slippage_bps() -> None:
    assert calculate_side_aware_slippage_bps(
        execution_side="BUY",
        fill_vwap=101,
        reference_price=100,
    ) == pytest.approx(100)


def test_sell_slippage_bps() -> None:
    assert calculate_side_aware_slippage_bps(
        execution_side="SELL",
        fill_vwap=99,
        reference_price=100,
    ) == pytest.approx(100)


def test_zero_reference_price_fails_safely() -> None:
    metrics = reconcile_execution_report(
        _report(fills=[ExecutionFill(price=100, quantity=1)]),
        reference_price=0,
    )

    assert metrics.slippage_bps is None
    assert "reference price unavailable; slippage not calculated" in metrics.warnings


def test_commission_asset_is_preserved() -> None:
    metrics = reconcile_execution_report(
        _report(fills=[ExecutionFill(price=100, quantity=1, commission=0.01, commission_asset="BNB")]),
        reference_price=100,
    )

    assert metrics.commission_by_asset == {"BNB": 0.01}


def test_missing_commission_conversion_is_explicitly_unavailable() -> None:
    metrics = reconcile_execution_report(
        _report(fills=[ExecutionFill(price=100, quantity=1, commission=0.01, commission_asset="BNB")]),
        reference_price=100,
        quote_asset="USDT",
    )

    assert metrics.quote_commission is None
    assert metrics.quote_commission_available is False
    assert "quote commission unavailable without asset conversion" in metrics.warnings


def test_simulated_vs_actual_fee_and_slippage_comparison() -> None:
    metrics = reconcile_execution_report(
        _report(fills=[ExecutionFill(price=101, quantity=1, commission=0.101, commission_asset="USDT")]),
        reference_price=100,
        simulated_fee_bps=5,
        simulated_slippage_bps=50,
    )

    assert metrics.quote_commission == pytest.approx(0.101)
    assert metrics.actual_vs_simulated_fee_bps_delta == pytest.approx(5)
    assert metrics.actual_vs_simulated_slippage_bps_delta == pytest.approx(50)
