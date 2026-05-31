from __future__ import annotations

from typing import Any

_REQUIRED_KEYS = (
    "algorithm_key","algorithm_name","direction_support","detection_rules","entry_rules","stop_loss_rules",
    "take_profit_rules","partial_exit_rules","soft_invalidation_rules","time_stop_rules","design_rationale","known_limitations",
)


def build_pattern_strategy_explanation(pattern_key: str) -> dict[str, Any]:
    key = str(pattern_key).upper()
    common = {
        "direction_support": ["LONG", "SHORT"],
        "partial_exit_rules": ["Partial exits are active only when risk-plan targets define quantity_ratio metadata."],
        "known_limitations": [
            "No live trading; historical simulation only.",
            "Execution uses canonical engine requested_price/close fallback semantics.",
            "pattern_score is a heuristic quality filter, not a calibrated probability of profitable alpha.",
            "Some score components may be placeholder context until validated indicator inputs or out-of-sample calibration are assigned.",
        ],
    }
    mapping: dict[str, dict[str, Any]] = {
        "FAIR_VALUE_GAP": {
            **common,
            "algorithm_key": key, "algorithm_name": "Fair Value Gap",
            "detection_rules": ["Three-candle imbalance with displacement/volume checks."],
            "entry_rules": ["Entry when confirmed FVG event passes status/score/risk-reward filters."],
            "stop_loss_rules": ["Stop references FVG boundary from risk plan."],
            "take_profit_rules": ["Targets use configured R-multiple levels from risk plan."],
            "soft_invalidation_rules": ["Soft invalidation can close position when post-entry invalidation triggers."],
            "time_stop_rules": ["Time-stop may trigger no-reaction exit per risk plan."],
            "design_rationale": ["Capture displacement imbalance fills with explicit, deterministic risk planning."],
        },
        "LIQUIDITY_SWEEP_REVERSAL": {
            **common,
            "algorithm_key": key,
            "algorithm_name": "Liquidity Sweep Reversal",
            "detection_rules": [
                "Prior swing liquidity is swept, price reclaims the level, and a same-direction displacement candle confirms.",
                "A same-direction FVG or local Order Block confluence zone must be present before an event is emitted.",
            ],
            "entry_rules": [
                "Default entry is the selected FVG midpoint or Order Block 61.8% retest reference, not a chase entry."
            ],
            "stop_loss_rules": ["Stop anchors beyond the sweep extreme with an ATR buffer."],
            "take_profit_rules": ["Targets use the nearest opposite liquidity reference when available, otherwise fixed R multiple."],
            "soft_invalidation_rules": ["Unsupported as a separate adapter in the first version; pre-entry invalidation is handled by no-fill/skip metadata."],
            "time_stop_rules": ["Entry retest expires after the configured wait window."],
            "design_rationale": [
                "Filter noisy FVG/OB signals through stop-run, reclaim, displacement, and cost-aware reward/risk constraints."
            ],
        },
        "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL": {
            **common,
            "algorithm_key": key,
            "algorithm_name": "Session Range Liquidity Breakout Reversal",
            "detection_rules": [
                "Use only the completed prior range window before the confirmation candle.",
                "Detect failed upside liquidity breaks, failed downside liquidity breaks, or configured downside breakdown continuations.",
                "Require confirmation candle body and prior-only volume-ratio thresholds.",
            ],
            "entry_rules": ["Enter on the confirmation close or next open per selected entry mode."],
            "stop_loss_rules": ["Stop anchors beyond the swept range boundary with an ATR buffer."],
            "take_profit_rules": ["Target uses a configured fixed R multiple from the entry and buffered stop."],
            "soft_invalidation_rules": ["No separate soft invalidation adapter in the first research version."],
            "time_stop_rules": ["Risk plan may exit after the configured maximum bars in trade."],
            "design_rationale": [
                "Exploit intraday liquidity failure or breakdown behavior while keeping every assumption deterministic and cost-auditable."
            ],
        },
        "ORDER_BLOCK": {**common, "algorithm_key": key, "algorithm_name": "Order Block", "detection_rules": ["Opposing source candle and displacement to define zone."], "entry_rules": ["Entry when confirmed order-block event passes filters."], "stop_loss_rules": ["Stop near zone boundary per risk plan."], "take_profit_rules": ["Target references opposing move objective from risk plan."], "soft_invalidation_rules": ["Exit if zone thesis invalidates."], "time_stop_rules": ["No-reaction timeout may force exit."], "design_rationale": ["Trade institutional-style reaction zones with bounded risk."]},
        "TRENDLINE_BREAK": {**common, "algorithm_key": key, "algorithm_name": "Trendline Break", "detection_rules": ["Pivot-based trendline with ATR-buffered breakout confirmation."], "entry_rules": ["Entry on confirmed breakout event when filters pass."], "stop_loss_rules": ["Stop from breakout/retest risk plan level."], "take_profit_rules": ["Target from breakout extension objective."], "soft_invalidation_rules": ["Close on trendline re-entry invalidation conditions."], "time_stop_rules": ["Event timeout may force exit if no progress."], "design_rationale": ["Exploit structural regime shift via confirmed trendline breaks."]},
        "CUP_AND_HANDLE": {**common, "algorithm_key": key, "algorithm_name": "Cup and Handle", "detection_rules": ["Bullish rim-bottom-rim and handle structure with breakout validation."], "entry_rules": ["Entry on validated breakout events only."], "stop_loss_rules": ["Handle low acts as primary stop anchor."], "take_profit_rules": ["Measured move target from cup depth."], "soft_invalidation_rules": ["Neckline/structure failure can trigger soft exit."], "time_stop_rules": ["Timeout exit when expected continuation fails."], "design_rationale": ["Model continuation accumulation and breakout follow-through."]},
        "DIAMOND": {**common, "algorithm_key": key, "algorithm_name": "Diamond", "detection_rules": ["Expansion then contraction pivot geometry with boundary break."], "entry_rules": ["Enter after breakout/breakdown confirmation and filter checks."], "stop_loss_rules": ["Stop around opposite diamond boundary."], "take_profit_rules": ["Measured move from pattern height."], "soft_invalidation_rules": ["Close back inside structure can invalidate thesis."], "time_stop_rules": ["Optional timeout exits inactive setups."], "design_rationale": ["Capture post-consolidation volatility resolution directionally."]},
        "ADAM_AND_EVE": {**common, "algorithm_key": key, "algorithm_name": "Adam and Eve", "detection_rules": ["Adam spike low + Eve rounded retest + neckline breakout."], "entry_rules": ["Enter on validated neckline breakout events."], "stop_loss_rules": ["Stop below Eve or broader Adam/Eve low per plan."], "take_profit_rules": ["Measured move from neckline to base depth."], "soft_invalidation_rules": ["Neckline failure may trigger soft exit."], "time_stop_rules": ["No-follow-through timeout can close trade."], "design_rationale": ["Trade reversal confirmation with explicit structural invalidation."]},
    }
    if key not in mapping:
        raise ValueError(f"unsupported pattern: {pattern_key}")
    payload = mapping[key]
    missing = [k for k in _REQUIRED_KEYS if k not in payload]
    if missing:
        raise ValueError(f"missing explanation keys: {missing}")
    return payload
