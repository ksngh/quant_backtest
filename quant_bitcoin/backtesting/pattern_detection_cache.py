"""Compatibility re-export for FVG cache utilities.

Canonical module: ``quant_bitcoin.backtesting.fvg_detection_cache``.
"""

from quant_bitcoin.backtesting.fvg_detection_cache import (  # noqa: F401
    IndicatorCache,
    PatternIndicatorCache,
    PatternEvaluationContext,
    SharedPatternEvaluationContext,
    detect_adam_and_eve_at_index,
    detect_cup_and_handle_at_index,
    detect_diamond_at_index,
    detect_fair_value_gap_at_index,
    detect_order_block_at_index,
    detect_trendline_break_at_index,
)
