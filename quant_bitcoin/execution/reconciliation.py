from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from quant_bitcoin.execution.order_intent import ExecutionFill, ExecutionReport


@dataclass(frozen=True)
class ExecutionQualityMetrics:
    intent_id: str
    client_order_id: str
    execution_side: str
    executed_quantity: float
    fill_vwap: float | None
    reference_price: float | None
    slippage_bps: float | None
    commission_by_asset: dict[str, float]
    quote_commission: float | None
    quote_commission_available: bool
    simulated_fee_bps: float | None = None
    simulated_slippage_bps: float | None = None
    actual_vs_simulated_fee_bps_delta: float | None = None
    actual_vs_simulated_slippage_bps_delta: float | None = None
    warnings: tuple[str, ...] = ()

    def to_metadata(self) -> dict[str, object]:
        return asdict(self)


def calculate_fill_vwap(fills: Sequence[ExecutionFill]) -> float | None:
    total_quantity = sum(float(fill.quantity) for fill in fills)
    if total_quantity <= 0:
        return None
    return sum(float(fill.price) * float(fill.quantity) for fill in fills) / total_quantity


def calculate_side_aware_slippage_bps(
    *,
    execution_side: str,
    fill_vwap: float,
    reference_price: float,
) -> float:
    if reference_price <= 0:
        raise ValueError("reference_price must be positive")
    if execution_side == "BUY":
        return (fill_vwap - reference_price) / reference_price * 10000
    if execution_side == "SELL":
        return (reference_price - fill_vwap) / reference_price * 10000
    raise ValueError("execution_side must be BUY or SELL")


def reconcile_execution_report(
    report: ExecutionReport,
    *,
    reference_price: float | None,
    quote_asset: str = "USDT",
    simulated_fee_bps: float | None = None,
    simulated_slippage_bps: float | None = None,
) -> ExecutionQualityMetrics:
    warnings: list[str] = []
    fill_vwap = calculate_fill_vwap(report.fills)
    commission_by_asset = _commission_by_asset(report.fills)
    quote_commission = None
    quote_commission_available = False
    if commission_by_asset:
        if set(commission_by_asset) == {quote_asset}:
            quote_commission = commission_by_asset[quote_asset]
            quote_commission_available = True
        else:
            warnings.append("quote commission unavailable without asset conversion")

    slippage_bps = None
    if reference_price is None or reference_price <= 0:
        warnings.append("reference price unavailable; slippage not calculated")
    elif fill_vwap is not None:
        slippage_bps = calculate_side_aware_slippage_bps(
            execution_side=report.execution_side,
            fill_vwap=fill_vwap,
            reference_price=reference_price,
        )

    actual_fee_bps = None
    notional = (fill_vwap or 0.0) * report.executed_quantity
    if quote_commission is not None and notional > 0:
        actual_fee_bps = quote_commission / notional * 10000

    return ExecutionQualityMetrics(
        intent_id=report.intent_id,
        client_order_id=report.client_order_id,
        execution_side=report.execution_side,
        executed_quantity=report.executed_quantity,
        fill_vwap=fill_vwap,
        reference_price=reference_price,
        slippage_bps=slippage_bps,
        commission_by_asset=commission_by_asset,
        quote_commission=quote_commission,
        quote_commission_available=quote_commission_available,
        simulated_fee_bps=simulated_fee_bps,
        simulated_slippage_bps=simulated_slippage_bps,
        actual_vs_simulated_fee_bps_delta=(
            actual_fee_bps - simulated_fee_bps
            if actual_fee_bps is not None and simulated_fee_bps is not None
            else None
        ),
        actual_vs_simulated_slippage_bps_delta=(
            slippage_bps - simulated_slippage_bps
            if slippage_bps is not None and simulated_slippage_bps is not None
            else None
        ),
        warnings=tuple(warnings),
    )


def _commission_by_asset(fills: Sequence[ExecutionFill]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for fill in fills:
        if fill.commission is None or not fill.commission_asset:
            continue
        totals[fill.commission_asset] = totals.get(fill.commission_asset, 0.0) + float(fill.commission)
    return totals
