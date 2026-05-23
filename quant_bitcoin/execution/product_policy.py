from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from quant_bitcoin.execution.order_intent import OrderIntent

SHORT_NOT_SUPPORTED_FOR_SPOT = "SHORT_NOT_SUPPORTED_FOR_SPOT"
SHORT_MODEL_LIMITATIONS = (
    "No borrow fees modeled",
    "No futures funding modeled",
    "No maintenance margin or liquidation model",
)


class ProductMode(Enum):
    BACKTEST_SIMULATION = "BACKTEST_SIMULATION"
    SPOT_PAPER = "SPOT_PAPER"
    SPOT_TESTNET = "SPOT_TESTNET"
    SPOT_LIVE = "SPOT_LIVE"
    MARGIN_DEFERRED = "MARGIN_DEFERRED"
    FUTURES_DEFERRED = "FUTURES_DEFERRED"


@dataclass(frozen=True)
class ProductPolicyDecision:
    allowed: bool
    product_mode: ProductMode
    reason: str | None = None
    metadata: dict[str, object] | None = None


def evaluate_product_policy(
    intent: OrderIntent,
    *,
    product_mode: ProductMode,
) -> ProductPolicyDecision:
    metadata = {
        "product_mode": product_mode.value,
        "short_model_limitations": list(SHORT_MODEL_LIMITATIONS),
    }
    if product_mode in {
        ProductMode.SPOT_PAPER,
        ProductMode.SPOT_TESTNET,
        ProductMode.SPOT_LIVE,
    } and intent.position_side == "SHORT":
        return ProductPolicyDecision(
            allowed=False,
            product_mode=product_mode,
            reason=SHORT_NOT_SUPPORTED_FOR_SPOT,
            metadata=metadata,
        )
    if product_mode in {ProductMode.MARGIN_DEFERRED, ProductMode.FUTURES_DEFERRED}:
        return ProductPolicyDecision(
            allowed=False,
            product_mode=product_mode,
            reason=f"{product_mode.value}_NOT_IMPLEMENTED",
            metadata=metadata,
        )
    return ProductPolicyDecision(
        allowed=True,
        product_mode=product_mode,
        metadata=metadata,
    )
