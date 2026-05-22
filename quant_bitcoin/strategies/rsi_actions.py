from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.rsi import calculate_rsi


@dataclass(frozen=True)
class RsiActionStrategy:
    window: int = 14
    buy_threshold: float = 30.0
    sell_threshold: float = 70.0

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError("RSI window must be at least 1")
        if not 0 <= self.buy_threshold <= 100:
            raise ValueError("RSI buy threshold must be between 0 and 100")
        if not 0 <= self.sell_threshold <= 100:
            raise ValueError("RSI sell threshold must be between 0 and 100")
        if self.buy_threshold >= self.sell_threshold:
            raise ValueError("RSI buy threshold must be below sell threshold")

    def evaluate(
        self,
        candles_so_far: pd.DataFrame,
        portfolio_state: dict[str, float] | None = None,
    ) -> list[StrategyAction]:
        if candles_so_far.empty:
            return []
        rsi = calculate_rsi(candles_so_far, window=self.window)
        latest_rsi = rsi.iloc[-1] if not rsi.empty else pd.NA
        if pd.isna(latest_rsi):
            return []

        ts = candles_so_far.iloc[-1]["timestamp"]
        position = float((portfolio_state or {}).get("position", 0.0))
        if latest_rsi <= self.buy_threshold and position <= 0:
            return [StrategyAction(action_type=StrategyActionType.ENTER_LONG, timestamp=ts)]
        if latest_rsi >= self.sell_threshold and position > 0:
            return [StrategyAction(action_type=StrategyActionType.EXIT_LONG, timestamp=ts)]
        return []
