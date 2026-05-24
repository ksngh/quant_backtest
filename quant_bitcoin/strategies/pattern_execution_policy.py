from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_bitcoin.patterns.entry_simulation import PatternEntryMode


@dataclass(frozen=True)
class PatternExecutionPolicy:
    pattern_key: str
    policy_key: str
    default_entry_mode: PatternEntryMode
    allowed_entry_modes: tuple[PatternEntryMode, ...]
    exit_assumptions: tuple[str, ...]
    economic_rationale: str
    research_hypothesis: str
    mode_hypotheses: dict[PatternEntryMode, str]

    def to_metadata(self, *, selected_entry_mode: PatternEntryMode | None = None) -> dict[str, Any]:
        selected = selected_entry_mode or self.default_entry_mode
        return {
            "schema_version": "pattern_execution_policy_v1",
            "pattern_key": self.pattern_key,
            "policy_key": self.policy_key,
            "selected_entry_mode": selected.value,
            "default_entry_mode": self.default_entry_mode.value,
            "allowed_entry_modes": tuple(mode.value for mode in self.allowed_entry_modes),
            "exit_assumptions": self.exit_assumptions,
            "economic_rationale": self.economic_rationale,
            "research_hypothesis": self.research_hypothesis,
            "selected_entry_hypothesis": self.mode_hypotheses.get(selected, "unspecified"),
            "entry_mode_hypotheses": {mode.value: self.mode_hypotheses.get(mode, "unspecified") for mode in self.allowed_entry_modes},
            "scope": "backtest_research_only",
        }


POLICIES: dict[str, PatternExecutionPolicy] = {
    "FAIR_VALUE_GAP": PatternExecutionPolicy(
        pattern_key="FAIR_VALUE_GAP",
        policy_key="FVG_RETEST_OR_MOMENTUM",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
            PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
            PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY,
            PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY,
            PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
            PatternEntryMode.LIMIT_AT_CUSTOM_PRICE,
        ),
        exit_assumptions=("ATR-buffered FVG structural stop", "R-multiple targets", "midpoint soft invalidation"),
        economic_rationale="FVG can be tested either as momentum continuation after displacement or as a retest/rebalancing entry into the gap.",
        research_hypothesis="Poor results may separate into late momentum fills, no-fill retest variants, or weak follow-through after retest fill.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "CHASE_MOMENTUM_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "CHASE_MOMENTUM_NEXT_OPEN",
            PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT: "RETEST_GAP_MIDPOINT",
            PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY: "RETEST_NEAR_GAP_BOUNDARY",
            PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY: "RETEST_DEEP_GAP_BOUNDARY",
            PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY: "LEGACY_RETEST_DEEP_GAP_BOUNDARY",
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE: "LEGACY_EVENT_ENTRY_REFERENCE",
            PatternEntryMode.LIMIT_AT_CUSTOM_PRICE: "CUSTOM_RESEARCH_PRICE",
        },
    ),
    "ORDER_BLOCK": PatternExecutionPolicy(
        pattern_key="ORDER_BLOCK",
        policy_key="ORDER_BLOCK_ZONE_RETEST",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
            PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
            PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT,
            PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
            PatternEntryMode.LIMIT_AT_CUSTOM_PRICE,
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        ),
        exit_assumptions=("zone structural stop", "R-multiple targets"),
        economic_rationale="Order Block logic is usually a defended-zone retest thesis, while confirmation entries model momentum continuation away from the zone.",
        research_hypothesis="Retest entries should improve reward-to-risk if the zone is actually defended; no-fill rates expose unavailable retests.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "CHASE_MOMENTUM_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "CHASE_MOMENTUM_NEXT_OPEN",
            PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT: "RETEST_ORDER_BLOCK_MIDPOINT",
            PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT: "RETEST_ORDER_BLOCK_618_RETRACEMENT",
            PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY: "RETEST_ORDER_BLOCK_STOP_SIDE_BOUNDARY",
            PatternEntryMode.LIMIT_AT_CUSTOM_PRICE: "CUSTOM_RESEARCH_PRICE",
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE: "LEGACY_EVENT_ENTRY_REFERENCE",
        },
    ),
    "TRENDLINE_BREAK": PatternExecutionPolicy(
        pattern_key="TRENDLINE_BREAK",
        policy_key="TRENDLINE_BREAKOUT_CONFIRMATION",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
            PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST,
        ),
        exit_assumptions=("trendline-break structural stop", "R-multiple targets"),
        economic_rationale="Trendline breaks are primarily breakout-confirmation patterns; optional retests model failed-break or pullback entries.",
        research_hypothesis="Momentum entries should benefit from continuation; retest variants should reduce chasing but may miss fast breaks.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "BREAKOUT_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "BREAKOUT_NEXT_OPEN",
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE: "TRENDLINE_RETEST_REFERENCE",
            PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST: "BROKEN_TRENDLINE_RETEST",
        },
    ),
    "CUP_AND_HANDLE": PatternExecutionPolicy(
        pattern_key="CUP_AND_HANDLE",
        policy_key="CUP_HANDLE_NECKLINE_BREAKOUT",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
            PatternEntryMode.LIMIT_AT_NECKLINE_RETEST,
        ),
        exit_assumptions=("handle or neckline structural stop", "measured-move/R-multiple targets"),
        economic_rationale="Cup and Handle usually enters on neckline breakout or a controlled neckline retest.",
        research_hypothesis="Breakout entries test immediate demand; retest entries test whether the neckline becomes support.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "BREAKOUT_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "BREAKOUT_NEXT_OPEN",
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE: "NECKLINE_RETEST_REFERENCE",
            PatternEntryMode.LIMIT_AT_NECKLINE_RETEST: "BROKEN_NECKLINE_RETEST",
        },
    ),
    "DIAMOND": PatternExecutionPolicy(
        pattern_key="DIAMOND",
        policy_key="DIAMOND_BOUNDARY_BREAKOUT",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
        ),
        exit_assumptions=("diamond boundary invalidation", "measured-move/R-multiple targets"),
        economic_rationale="Diamond patterns are treated as boundary resolution patterns, so confirmation close or next open is the supported timing assumption.",
        research_hypothesis="Boundary resolution should show continuation after compression; retest variants need separate future specification.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "BOUNDARY_RESOLUTION_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "BOUNDARY_RESOLUTION_NEXT_OPEN",
        },
    ),
    "ADAM_AND_EVE": PatternExecutionPolicy(
        pattern_key="ADAM_AND_EVE",
        policy_key="ADAM_EVE_NECKLINE_BREAKOUT",
        default_entry_mode=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        allowed_entry_modes=(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryMode.MARKET_ON_NEXT_OPEN,
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
            PatternEntryMode.LIMIT_AT_NECKLINE_RETEST,
        ),
        exit_assumptions=("neckline or structure invalidation", "measured-move/R-multiple targets"),
        economic_rationale="Adam and Eve reversal patterns usually confirm on neckline recovery, with optional neckline retest entries.",
        research_hypothesis="Neckline breakout entries test reversal confirmation; retests test whether recovered neckline support holds.",
        mode_hypotheses={
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE: "REVERSAL_CONFIRMATION_CLOSE",
            PatternEntryMode.MARKET_ON_NEXT_OPEN: "REVERSAL_NEXT_OPEN",
            PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE: "NECKLINE_RETEST_REFERENCE",
            PatternEntryMode.LIMIT_AT_NECKLINE_RETEST: "BROKEN_NECKLINE_RETEST",
        },
    ),
}


def policy_for_pattern(pattern_key: str) -> PatternExecutionPolicy:
    normalized = str(pattern_key).upper()
    if normalized not in POLICIES:
        raise ValueError(f"unsupported pattern execution policy: {pattern_key}")
    return POLICIES[normalized]


def validate_pattern_entry_mode(pattern_key: str, mode: PatternEntryMode) -> PatternExecutionPolicy:
    policy = policy_for_pattern(pattern_key)
    if mode not in policy.allowed_entry_modes:
        allowed = ", ".join(entry_mode.value.lower() for entry_mode in policy.allowed_entry_modes)
        raise ValueError(f"{mode.value.lower()} is not supported for {policy.pattern_key}; allowed modes: {allowed}")
    return policy
