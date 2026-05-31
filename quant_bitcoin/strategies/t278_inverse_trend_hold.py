"""Task 278 inverse trend-hold research action builder.

This module is intentionally small and offline-only. It creates a deterministic
cash-bounded simulated short from the first available candle to the final
available candle for a fixed research window. It does not fetch market data,
place orders, call exchange APIs, or persist records.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)

STRATEGY_KEY = "T278_INVERSE_TREND_HOLD"
STRATEGY_NAME = "T278_INVERSE_TREND_HOLD_RESEARCH_STRATEGY"


def build_inverse_trend_hold_actions(
    candles: pd.DataFrame | list[dict[str, Any]],
    *,
    variant_id: str,
) -> list[StrategyAction]:
    """Return first-candle short entry and final-candle short exit actions."""

    frame = candles.copy(deep=False) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    if frame.empty:
        return []
    missing = [column for column in ("timestamp", "close") if column not in frame.columns]
    if missing:
        raise ValueError(f"candles missing required columns: {missing}")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")

    first = frame.iloc[0]
    last = frame.iloc[-1]
    metadata = {
        "pattern_type": STRATEGY_KEY,
        "variant_id": variant_id,
        "strategy_scope": "offline_backtest_research_only",
        "cash_bounded_short": True,
        "known_limitation": "Directional inverse buy-and-hold baseline; not validated OOS.",
    }
    return [
        StrategyAction(
            StrategyActionType.ENTER_SHORT,
            first["timestamp"],
            reason="T278_CASH_BOUNDED_INVERSE_TREND_HOLD_ENTRY",
            requested_price=float(first["close"]),
            metadata={
                **metadata,
                "entry_rule": "enter_short_first_available_window_candle_close",
            },
        ),
        StrategyAction(
            StrategyActionType.EXIT_SHORT,
            last["timestamp"],
            quantity=1.0,
            quantity_mode=StrategyQuantityMode.POSITION_RATIO,
            reason="T278_FINAL_WINDOW_EXIT",
            requested_price=float(last["close"]),
            metadata={
                **metadata,
                "exit_rule": "exit_short_final_available_window_candle_close",
            },
        ),
    ]
