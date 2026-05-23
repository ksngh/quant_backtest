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
from quant_bitcoin.patterns.order_block import (
    OrderBlockConfig,
    OrderBlockDirection,
    OrderBlockEvent,
    _displacement_config as _ob_displacement_config,
    _evaluate_order_block as _evaluate_order_block_event,
    _find_source_candle as _find_order_block_source_candle,
    _validate_external_filters as _validate_order_block_external_filters,
)


@dataclass
class IndicatorCache:
    candles: pd.DataFrame
    atr: pd.Series
    volume_ratio: pd.Series
    displacement_rows: pd.DataFrame

    @classmethod
    def for_pattern(
        cls,
        candles: pd.DataFrame | list[dict[str, Any]],
        config: FairValueGapConfig | OrderBlockConfig | None = None,
    ) -> "IndicatorCache":
        detector_config = config or FairValueGapConfig()
        normalized = _normalize_candles(candles, None)
        atr_rows = calculate_atr(
            normalized[["symbol", "timestamp", "high", "low", "close"]],
            detector_config.atr_config,
        )
        volume_rows = calculate_volume_ratio(
            normalized[["symbol", "timestamp", "volume"]],
            detector_config.volume_ratio_config,
        )
        enriched = normalized.copy()
        enriched["atr"] = atr_rows["atr"]
        enriched["volume_ratio"] = volume_rows["volume_ratio"]
        displacement_config = getattr(detector_config, "displacement_config", None)
        if displacement_config is None and isinstance(detector_config, OrderBlockConfig):
            displacement_config = _ob_displacement_config(detector_config)
        displacement_rows = detect_displacement_candles(
            enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
            displacement_config,
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



def detect_order_block_at_index(
    context: PatternEvaluationContext,
    *,
    config: OrderBlockConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[OrderBlockEvent]:
    order_block_config = config or OrderBlockConfig()
    _validate_order_block_external_filters(order_block_config)
    if context.current_index < 1 or context.current_index >= len(context.indicator_cache.candles):
        return []
    displacement = context.indicator_cache.displacement_rows.iloc[context.current_index]
    if str(displacement.get("displacement_status", "")) != "VALID":
        return []
    displacement_direction = str(displacement.get("displacement_direction", ""))
    if displacement_direction == "BULLISH":
        direction = OrderBlockDirection.BULLISH
    elif displacement_direction == "BEARISH":
        direction = OrderBlockDirection.BEARISH
    else:
        return []
    source_index = _find_order_block_source_candle(
        context.indicator_cache.candles,
        context.current_index,
        direction,
        order_block_config,
    )
    if source_index is None:
        return []
    event = _evaluate_order_block_event(
        direction,
        context.indicator_cache.candles.iloc[: context.current_index + 1].reset_index(drop=True),
        displacement,
        source_index,
        context.current_index,
        symbol=symbol or str(context.indicator_cache.candles.iloc[0]["symbol"]),
        timeframe=timeframe,
        config=order_block_config,
    )
    if event is None or event.event_id in context.seen_event_ids:
        return []
    context.seen_event_ids.add(event.event_id)
    return [event]


IndicatorCache.for_fvg = IndicatorCache.for_pattern
