from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quant_bitcoin.indicators.atr import calculate_atr
from quant_bitcoin.indicators.displacement_candle import detect_displacement_candles
from quant_bitcoin.indicators.market_regime import MarketRegimeConfig, calculate_market_regime
from quant_bitcoin.indicators.pivots import PivotConfig, detect_pivots
from quant_bitcoin.indicators.volume_ratio import calculate_volume_ratio
from quant_bitcoin.patterns.adam_and_eve import (
    AdamAndEveConfig,
    AdamAndEveEvent,
    detect_adam_and_eve_patterns_at_index as _detect_adam_and_eve_patterns_at_index,
)
from quant_bitcoin.patterns.cup_and_handle import (
    CupAndHandleConfig,
    CupAndHandleEvent,
    detect_cup_and_handle_patterns_at_index as _detect_cup_and_handle_patterns_at_index,
)
from quant_bitcoin.patterns.diamond import (
    DiamondConfig,
    DiamondEvent,
    detect_diamond_patterns_at_index as _detect_diamond_patterns_at_index,
)
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
    _find_source_cluster as _find_order_block_source_cluster,
    _validate_external_filters as _validate_order_block_external_filters,
)
from quant_bitcoin.patterns.liquidity_sweep_reversal import (
    LiquiditySweepReversalConfig,
    LiquiditySweepReversalEvent,
    evaluate_liquidity_sweep_reversal_at_index as _evaluate_liquidity_sweep_reversal_at_index,
)
from quant_bitcoin.patterns.trendline_break import (
    TrendlineBreakConfig,
    TrendlineBreakEvent,
    detect_trendline_breaks_at_index as _detect_trendline_breaks_at_index,
)


@dataclass
class PatternIndicatorCache:
    candles: pd.DataFrame
    atr: pd.Series
    volume_ratio: pd.Series
    displacement_rows: pd.DataFrame
    pivot_rows: pd.DataFrame
    market_regime_rows: pd.DataFrame | None = None
    calculation_counts: dict[str, int] = field(default_factory=dict)

    @classmethod
    def for_pattern(
        cls,
        candles: pd.DataFrame | list[dict[str, Any]],
        config: Any = None,
        *,
        market_regime_config: MarketRegimeConfig | None = None,
    ) -> "PatternIndicatorCache":
        detector_config = config or FairValueGapConfig()
        normalized = _normalize_candles(candles, None)
        atr_rows = calculate_atr(
            normalized[["symbol", "timestamp", "high", "low", "close"]],
            getattr(detector_config, "atr_config", None),
        )
        volume_rows = calculate_volume_ratio(
            normalized[["symbol", "timestamp", "volume"]],
            getattr(detector_config, "volume_ratio_config", None),
        )
        enriched = normalized.copy()
        enriched["atr"] = atr_rows["atr"]
        enriched["volume_ratio"] = volume_rows["volume_ratio"]
        pivot_config = getattr(detector_config, "pivot_config", None)
        pivot_rows = detect_pivots(
            enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr"]],
            pivot_config if isinstance(pivot_config, PivotConfig) else None,
        )
        displacement_config = getattr(detector_config, "displacement_config", None)
        if displacement_config is None and isinstance(detector_config, OrderBlockConfig):
            displacement_config = _ob_displacement_config(detector_config)
        displacement_rows = detect_displacement_candles(
            enriched[["symbol", "timestamp", "open", "high", "low", "close", "atr", "volume_ratio"]],
            displacement_config,
        )
        market_regime_rows = (
            calculate_market_regime(enriched, market_regime_config)
            if market_regime_config is not None
            else None
        )
        return cls(
            candles=enriched,
            atr=atr_rows["atr"],
            volume_ratio=volume_rows["volume_ratio"],
            displacement_rows=displacement_rows,
            pivot_rows=pivot_rows,
            market_regime_rows=market_regime_rows,
            calculation_counts={
                "atr": 1,
                "volume_ratio": 1,
                "displacement_rows": 1,
                "pivot_rows": 1,
                "market_regime_rows": 1 if market_regime_rows is not None else 0,
            },
        )

    def visible_candles(self, current_index: int) -> pd.DataFrame:
        return self.candles.iloc[: current_index + 1].reset_index(drop=True)

    def visible_displacement_rows(self, current_index: int) -> pd.DataFrame:
        return self.displacement_rows.iloc[: current_index + 1].reset_index(drop=True)

    def visible_pivot_rows(self, current_index: int) -> pd.DataFrame:
        if self.pivot_rows.empty or "confirmed_index" not in self.pivot_rows.columns:
            return self.pivot_rows.copy()
        visible = self.pivot_rows[
            pd.to_numeric(self.pivot_rows["confirmed_index"], errors="coerce") <= current_index
        ]
        return visible.reset_index(drop=True)

    def visible_market_regime_rows(self, current_index: int) -> pd.DataFrame | None:
        if self.market_regime_rows is None:
            return None
        return self.market_regime_rows.iloc[: current_index + 1].reset_index(drop=True)


@dataclass
class SharedPatternEvaluationContext:
    candles: pd.DataFrame
    current_index: int
    indicator_cache: PatternIndicatorCache
    seen_event_ids: set[str] = field(default_factory=set)
    portfolio_state: dict[str, Any] | None = None


def detect_fair_value_gap_at_index(
    context: SharedPatternEvaluationContext,
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

    visible_enriched = context.indicator_cache.visible_candles(candle_3_index)
    visible_displacement_rows = context.indicator_cache.visible_displacement_rows(candle_3_index)

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
    context: SharedPatternEvaluationContext,
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
    source_cluster = _find_order_block_source_cluster(
        context.indicator_cache.candles,
        context.current_index,
        direction,
        order_block_config,
    )
    if source_cluster is None:
        return []
    event = _evaluate_order_block_event(
        direction,
        context.indicator_cache.candles.iloc[: context.current_index + 1].reset_index(drop=True),
        displacement,
        source_cluster,
        context.current_index,
        symbol=symbol or str(context.indicator_cache.candles.iloc[0]["symbol"]),
        timeframe=timeframe,
        config=order_block_config,
    )
    if event is None or event.event_id in context.seen_event_ids:
        return []
    context.seen_event_ids.add(event.event_id)
    return [event]


def detect_liquidity_sweep_reversal_at_index(
    context: SharedPatternEvaluationContext,
    *,
    config: LiquiditySweepReversalConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[LiquiditySweepReversalEvent]:
    sweep_config = config or LiquiditySweepReversalConfig()
    if context.current_index < 1 or context.current_index >= len(context.indicator_cache.candles):
        return []
    events = _evaluate_liquidity_sweep_reversal_at_index(
        context.indicator_cache.candles,
        context.indicator_cache.displacement_rows,
        context.current_index,
        symbol=symbol or _symbol_from_cache(context),
        timeframe=timeframe,
        config=sweep_config,
    )
    return _deduped_cached_events(context, events)


def detect_trendline_break_at_index(
    context: SharedPatternEvaluationContext,
    *,
    config: TrendlineBreakConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[TrendlineBreakEvent]:
    return _deduped_cached_events(
        context,
        _detect_trendline_breaks_at_index(
            context.indicator_cache.visible_candles(context.current_index),
            context.current_index,
            symbol=symbol or _symbol_from_cache(context),
            timeframe=timeframe,
            config=config,
        ),
    )


def detect_cup_and_handle_at_index(
    context: SharedPatternEvaluationContext,
    *,
    config: CupAndHandleConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[CupAndHandleEvent]:
    return _deduped_cached_events(
        context,
        _detect_cup_and_handle_patterns_at_index(
            context.indicator_cache.visible_candles(context.current_index),
            context.current_index,
            symbol=symbol or _symbol_from_cache(context),
            timeframe=timeframe,
            config=config,
        ),
    )


def detect_diamond_at_index(
    context: SharedPatternEvaluationContext,
    *,
    config: DiamondConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[DiamondEvent]:
    return _deduped_cached_events(
        context,
        _detect_diamond_patterns_at_index(
            context.indicator_cache.visible_candles(context.current_index),
            context.current_index,
            symbol=symbol or _symbol_from_cache(context),
            timeframe=timeframe,
            config=config,
        ),
    )


def detect_adam_and_eve_at_index(
    context: SharedPatternEvaluationContext,
    *,
    config: AdamAndEveConfig | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> list[AdamAndEveEvent]:
    return _deduped_cached_events(
        context,
        _detect_adam_and_eve_patterns_at_index(
            context.indicator_cache.visible_candles(context.current_index),
            context.current_index,
            symbol=symbol or _symbol_from_cache(context),
            timeframe=timeframe,
            config=config,
        ),
    )


def _deduped_cached_events(
    context: SharedPatternEvaluationContext,
    events: list[Any],
) -> list[Any]:
    deduped = [
        event
        for event in events
        if getattr(event, "event_id", None) not in context.seen_event_ids
    ]
    for event in deduped:
        event_id = getattr(event, "event_id", None)
        if event_id is not None:
            context.seen_event_ids.add(event_id)
    return deduped


def _symbol_from_cache(context: SharedPatternEvaluationContext) -> str | None:
    if context.indicator_cache.candles.empty or "symbol" not in context.indicator_cache.candles:
        return None
    return str(context.indicator_cache.candles.iloc[0]["symbol"])


IndicatorCache = PatternIndicatorCache
PatternEvaluationContext = SharedPatternEvaluationContext
IndicatorCache.for_fvg = IndicatorCache.for_pattern
