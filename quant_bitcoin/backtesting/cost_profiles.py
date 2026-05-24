from __future__ import annotations

from dataclasses import dataclass

from quant_bitcoin.backtesting.costs import TransactionCostConfig


@dataclass(frozen=True)
class CostProfile:
    key: str
    description: str
    config: TransactionCostConfig

    def to_metadata(self) -> dict[str, object]:
        return {
            "schema_version": "transaction_cost_profile_v1",
            "profile_key": self.key,
            "description": self.description,
            "maker_fee_bps": self.config.maker_fee_bps,
            "taker_fee_bps": self.config.taker_fee_bps,
            "spread_bps": self.config.spread_bps,
            "slippage_bps": self.config.slippage_bps,
            "minimum_slippage_bps": self.config.minimum_slippage_bps,
            "volatility_slippage_multiplier": self.config.volatility_slippage_multiplier,
            "zero_cost_profile": self.key == "zero",
            "source": "offline_static_preset",
        }


COST_PROFILES: dict[str, CostProfile] = {
    "zero": CostProfile("zero", "No fees, spread, or slippage; useful only as a debugging baseline.", TransactionCostConfig()),
    "binance_spot_taker_baseline": CostProfile(
        "binance_spot_taker_baseline",
        "Static spot taker-style baseline; not fetched from an exchange account.",
        TransactionCostConfig(taker_fee_bps=10.0, spread_bps=1.0, slippage_bps=1.0),
    ),
    "conservative_crypto_1m": CostProfile(
        "conservative_crypto_1m",
        "Conservative 1m crypto assumptions with spread, slippage, and volatility adjustment.",
        TransactionCostConfig(taker_fee_bps=10.0, spread_bps=3.0, slippage_bps=5.0, minimum_slippage_bps=1.0, volatility_slippage_multiplier=0.1),
    ),
    "high_slippage_stress": CostProfile(
        "high_slippage_stress",
        "Stress profile for high turnover or thin liquidity simulations.",
        TransactionCostConfig(taker_fee_bps=10.0, spread_bps=10.0, slippage_bps=20.0, minimum_slippage_bps=5.0, volatility_slippage_multiplier=0.5),
    ),
}


def cost_profile(key: str) -> CostProfile:
    normalized = str(key).lower()
    if normalized not in COST_PROFILES:
        raise ValueError(f"unsupported cost profile: {key}")
    return COST_PROFILES[normalized]


def manual_cost_overrides_present(values: dict[str, float]) -> bool:
    return any(float(value) != 0.0 for value in values.values())


def break_even_cost_bps(gross_pnl: float | None, notional: float | None) -> float | None:
    if gross_pnl is None or notional is None or notional <= 0:
        return None
    return (gross_pnl / notional) * 10_000.0
