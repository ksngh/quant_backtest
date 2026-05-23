from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quant_bitcoin.indicators.atr import calculate_atr
from quant_bitcoin.indicators.displacement_candle import detect_displacement_candles
from quant_bitcoin.indicators.volume_ratio import calculate_volume_ratio
from quant_bitcoin.patterns.fair_value_gap import (
    FairValueGapConfig,
    PatternDirection,
    PatternEvent,
    _evaluate_fair_value_gap,
    _normalize_candles,
    _validate_external_filters,
)


@dataclass
class IndicatorCache:
    candles: pd.DataFrame
    atr: pd.Series
    volume_ratio: pd.Series
    displacement_rows: pd.DataFrame

    @classmethod
    def for_fvg(
        cls,
        candles: pd.DataFrame | list[dict[str, Any]],
        config: FairValueGapConfig | None = None,
    ) -> "IndicatorCache":
        fvg_config = config or FairValueGapConfig()
        normalized = _normalize_candles(candles, None)
        atr_rows = calculate_atr(
            normalized[["symbol", "timestamp", "high", "low", "close"]],
            fvg_config.atr_config,
        )
        volume_rows = calculate_volume_ratio(
            normalized[["symbol", "timestamp", "volume"]],
            fvg_config.volume_ratio_config,
        )
        enriched = normalized.copy()
        enriched["atr"] = atr_rows["atr"]
        enriched["volume_ratio"] = volume_rows["volume_ratio"]
        displacement_rows = detect_displacement_candles(
            enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
            fvg_config.displacement_config,
        )
        return cls(
            candles=enriched,
            atr=atr_rows["atr"],
            volume_ratio=volume_rows["volume_ratio"],
            displacement_rows=displacement_rows,
        )


@dataclass
class PatternEvaluationContext:
    candles: pd.DataFrame
    current_index: int
    indicator_cache: IndicatorCache
    seen_event_ids: set[str] = field(default_factory=set)
    portfolio_state: dict[str, Any] | None = None


def detect_fair_value_gap_at_index(
    context: PatternEvaluationContext,
    *,
    config: FairValueGapConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[PatternEvent]:
    fvg_config = config or FairValueGapConfig()
    _validate_external_filters(fvg_config)

    if context.current_index < 2 or context.current_index >= len(context.indicator_cache.candles):
        return []

    enriched = context.indicator_cache.candles
    candle_3_index = context.current_index
    candle_1_index = candle_3_index - 2
    candle_2_index = candle_3_index - 1

    candle_1 = enriched.iloc[candle_1_index]
    candle_3 = enriched.iloc[candle_3_index]

    visible_enriched = enriched.iloc[: candle_3_index + 1].reset_index(drop=True)
    visible_displacement_rows = (
        context.indicator_cache.displacement_rows.iloc[: candle_3_index + 1].reset_index(drop=True)
    )

    events: list[PatternEvent] = []
    if float(candle_1["high"]) < float(candle_3["low"]):
        event = _evaluate_fair_value_gap(
            PatternDirection.BULLISH,
            visible_enriched,
            visible_displacement_rows,
            candle_1_index,
            candle_2_index,
            candle_3_index,
            symbol=symbol or str(enriched.iloc[0]["symbol"]),
            timeframe=timeframe,
            config=fvg_config,
        )
        if event is not None and event.event_id not in context.seen_event_ids:
            events.append(event)
    if float(candle_1["low"]) > float(candle_3["high"]):
        event = _evaluate_fair_value_gap(
            PatternDirection.BEARISH,
            visible_enriched,
            visible_displacement_rows,
            candle_1_index,
            candle_2_index,
            candle_3_index,
            symbol=symbol or str(enriched.iloc[0]["symbol"]),
            timeframe=timeframe,
            config=fvg_config,
        )
        if event is not None and event.event_id not in context.seen_event_ids:
            events.append(event)

    for ev in events:
        context.seen_event_ids.add(ev.event_id)
    return events
