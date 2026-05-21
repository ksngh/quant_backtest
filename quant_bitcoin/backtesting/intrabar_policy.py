"""Deterministic intrabar sequencing policy helpers.

OHLC candles do not encode whether high or low occurred first intrabar. These
helpers provide reusable pure policy resolution for same-candle touch ambiguity
across entry/stop/target simulation use cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite


class IntrabarSequencingMode(Enum):
    """Supported deterministic sequencing policies."""

    CONSERVATIVE = "CONSERVATIVE"
    OPTIMISTIC = "OPTIMISTIC"
    STOP_FIRST = "STOP_FIRST"
    TARGET_FIRST = "TARGET_FIRST"
    ENTRY_FIRST_THEN_STOP = "ENTRY_FIRST_THEN_STOP"
    ENTRY_FIRST_THEN_TARGET = "ENTRY_FIRST_THEN_TARGET"
    SKIP_AMBIGUOUS = "SKIP_AMBIGUOUS"


@dataclass(frozen=True)
class IntrabarTouch:
    """Whether each relevant level is touched by candle range."""

    entry_touched: bool
    stop_touched: bool
    target_touched: bool
    ambiguous_stop_target: bool
    ambiguous_entry_stop_target: bool


@dataclass(frozen=True)
class IntrabarDecision:
    """Resolved deterministic intrabar outcome."""

    outcome: str
    reason: str
    is_ambiguous: bool
    skipped: bool = False


@dataclass(frozen=True)
class IntrabarPolicyConfig:
    """Intrabar policy configuration."""

    mode: IntrabarSequencingMode = IntrabarSequencingMode.CONSERVATIVE


def detect_intrabar_touches(
    *,
    high: float,
    low: float,
    entry_price: float,
    stop_price: float,
    target_price: float,
) -> IntrabarTouch:
    """Return deterministic candle touch flags for entry/stop/target levels."""

    high_value = _coerce_finite_number(high, "high")
    low_value = _coerce_finite_number(low, "low")
    if high_value < low_value:
        raise ValueError("high must be greater than or equal to low")

    entry_value = _coerce_finite_number(entry_price, "entry_price")
    stop_value = _coerce_finite_number(stop_price, "stop_price")
    target_value = _coerce_finite_number(target_price, "target_price")

    entry_touched = low_value <= entry_value <= high_value
    stop_touched = low_value <= stop_value <= high_value
    target_touched = low_value <= target_value <= high_value

    ambiguous_stop_target = stop_touched and target_touched
    ambiguous_entry_stop_target = entry_touched and stop_touched and target_touched

    return IntrabarTouch(
        entry_touched=entry_touched,
        stop_touched=stop_touched,
        target_touched=target_touched,
        ambiguous_stop_target=ambiguous_stop_target,
        ambiguous_entry_stop_target=ambiguous_entry_stop_target,
    )


def resolve_intrabar_decision(
    *,
    direction: str,
    touches: IntrabarTouch,
    config: IntrabarPolicyConfig | None = None,
) -> IntrabarDecision:
    """Resolve deterministic outcome for intrabar entry/stop/target ambiguity."""

    normalized_direction = _normalize_direction(direction)
    _ = normalized_direction
    mode = IntrabarSequencingMode.CONSERVATIVE if config is None else config.mode

    if not (touches.entry_touched or touches.stop_touched or touches.target_touched):
        return IntrabarDecision("NONE", "no levels touched", is_ambiguous=False)

    if touches.ambiguous_entry_stop_target:
        return _resolve_all_three_touched(mode)

    if touches.ambiguous_stop_target:
        return _resolve_stop_target_ambiguous(mode)

    if touches.entry_touched and not (touches.stop_touched or touches.target_touched):
        return IntrabarDecision("ENTRY", "entry touched", is_ambiguous=False)
    if touches.stop_touched and not (touches.entry_touched or touches.target_touched):
        return IntrabarDecision("STOP", "stop touched", is_ambiguous=False)
    if touches.target_touched and not (touches.entry_touched or touches.stop_touched):
        return IntrabarDecision("TARGET", "target touched", is_ambiguous=False)

    if touches.entry_touched and touches.stop_touched:
        if mode in (IntrabarSequencingMode.OPTIMISTIC, IntrabarSequencingMode.ENTRY_FIRST_THEN_TARGET):
            return IntrabarDecision("ENTRY", "entry+stop touched; optimistic keeps position open", is_ambiguous=True)
        return IntrabarDecision("STOP", "entry+stop touched; stop-priority resolution", is_ambiguous=True)

    if touches.entry_touched and touches.target_touched:
        if mode in (IntrabarSequencingMode.CONSERVATIVE, IntrabarSequencingMode.STOP_FIRST, IntrabarSequencingMode.ENTRY_FIRST_THEN_STOP):
            return IntrabarDecision("ENTRY", "entry+target touched; conservative leaves target unresolved", is_ambiguous=True)
        return IntrabarDecision("TARGET", "entry+target touched; target-priority resolution", is_ambiguous=True)

    return IntrabarDecision("NONE", "unhandled touch combination", is_ambiguous=False)


def _resolve_stop_target_ambiguous(mode: IntrabarSequencingMode) -> IntrabarDecision:
    if mode in (
        IntrabarSequencingMode.CONSERVATIVE,
        IntrabarSequencingMode.STOP_FIRST,
        IntrabarSequencingMode.ENTRY_FIRST_THEN_STOP,
    ):
        return IntrabarDecision("STOP", "ambiguous stop/target resolved to stop", is_ambiguous=True)
    if mode in (
        IntrabarSequencingMode.OPTIMISTIC,
        IntrabarSequencingMode.TARGET_FIRST,
        IntrabarSequencingMode.ENTRY_FIRST_THEN_TARGET,
    ):
        return IntrabarDecision("TARGET", "ambiguous stop/target resolved to target", is_ambiguous=True)
    return IntrabarDecision("SKIP", "ambiguous stop/target skipped by policy", is_ambiguous=True, skipped=True)


def _resolve_all_three_touched(mode: IntrabarSequencingMode) -> IntrabarDecision:
    if mode == IntrabarSequencingMode.SKIP_AMBIGUOUS:
        return IntrabarDecision("SKIP", "entry/stop/target all touched; skipped by policy", is_ambiguous=True, skipped=True)
    if mode in (
        IntrabarSequencingMode.CONSERVATIVE,
        IntrabarSequencingMode.STOP_FIRST,
        IntrabarSequencingMode.ENTRY_FIRST_THEN_STOP,
    ):
        return IntrabarDecision("STOP", "entry/stop/target all touched; conservative stop-first resolution", is_ambiguous=True)
    if mode == IntrabarSequencingMode.ENTRY_FIRST_THEN_TARGET:
        return IntrabarDecision("TARGET", "entry/stop/target all touched; entry-then-target resolution", is_ambiguous=True)
    if mode in (IntrabarSequencingMode.OPTIMISTIC, IntrabarSequencingMode.TARGET_FIRST):
        return IntrabarDecision("TARGET", "entry/stop/target all touched; optimistic target-first resolution", is_ambiguous=True)
    return IntrabarDecision("STOP", "fallback stop-first resolution", is_ambiguous=True)


def _coerce_finite_number(value: float, field_name: str) -> float:
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{field_name} must be finite")
    return numeric


def _normalize_direction(direction: str) -> str:
    normalized = str(direction).upper()
    if normalized not in ("LONG", "SHORT"):
        raise ValueError("direction must be LONG or SHORT")
    return normalized
