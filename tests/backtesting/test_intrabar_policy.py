from __future__ import annotations

import pytest

from quant_bitcoin.backtesting.intrabar_policy import (
    IntrabarPolicyConfig,
    IntrabarSequencingMode,
    detect_intrabar_touches,
    resolve_intrabar_decision,
)


def test_detect_touches_marks_all_three_ambiguous() -> None:
    touches = detect_intrabar_touches(
        high=110.0,
        low=90.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    assert touches.entry_touched is True
    assert touches.stop_touched is True
    assert touches.target_touched is True
    assert touches.ambiguous_stop_target is True
    assert touches.ambiguous_entry_stop_target is True


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_conservative_mode_prefers_stop_when_stop_and_target_reachable(direction: str) -> None:
    touches = detect_intrabar_touches(
        high=110.0,
        low=90.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    decision = resolve_intrabar_decision(
        direction=direction,
        touches=touches,
        config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.CONSERVATIVE),
    )

    assert decision.outcome == "STOP"
    assert decision.is_ambiguous is True
    assert decision.skipped is False


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (IntrabarSequencingMode.OPTIMISTIC, "TARGET"),
        (IntrabarSequencingMode.STOP_FIRST, "STOP"),
        (IntrabarSequencingMode.TARGET_FIRST, "TARGET"),
        (IntrabarSequencingMode.ENTRY_FIRST_THEN_STOP, "STOP"),
        (IntrabarSequencingMode.ENTRY_FIRST_THEN_TARGET, "TARGET"),
    ],
)
def test_modes_resolve_all_three_touched_as_expected(mode: IntrabarSequencingMode, expected: str) -> None:
    touches = detect_intrabar_touches(
        high=110.0,
        low=90.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    decision = resolve_intrabar_decision(
        direction="LONG",
        touches=touches,
        config=IntrabarPolicyConfig(mode=mode),
    )

    assert decision.outcome == expected
    assert decision.is_ambiguous is True


def test_skip_ambiguous_mode_returns_explicit_skip() -> None:
    touches = detect_intrabar_touches(
        high=110.0,
        low=90.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    decision = resolve_intrabar_decision(
        direction="SHORT",
        touches=touches,
        config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.SKIP_AMBIGUOUS),
    )

    assert decision.outcome == "SKIP"
    assert decision.skipped is True
    assert decision.is_ambiguous is True


def test_non_ambiguous_touches_return_direct_outcome() -> None:
    touches = detect_intrabar_touches(
        high=101.0,
        low=99.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    decision = resolve_intrabar_decision(direction="LONG", touches=touches)

    assert decision.outcome == "ENTRY"
    assert decision.is_ambiguous is False


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"high": 90.0, "low": 100.0, "entry_price": 95.0, "stop_price": 94.0, "target_price": 96.0},
            "high must be greater than or equal to low",
        ),
        (
            {"high": float("nan"), "low": 90.0, "entry_price": 95.0, "stop_price": 94.0, "target_price": 96.0},
            "high must be finite",
        ),
    ],
)
def test_detect_touches_validates_numeric_ranges(kwargs: dict[str, float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        detect_intrabar_touches(**kwargs)


def test_resolve_validates_direction() -> None:
    touches = detect_intrabar_touches(
        high=110.0,
        low=90.0,
        entry_price=100.0,
        stop_price=95.0,
        target_price=105.0,
    )

    with pytest.raises(ValueError, match="direction must be LONG or SHORT"):
        resolve_intrabar_decision(direction="SIDEWAYS", touches=touches)
