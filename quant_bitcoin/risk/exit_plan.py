"""Pattern risk and exit planning contract.

This module turns already-supplied entry, invalidation, and volatility values
into deterministic risk/exit plan data for future pattern-specific planners. It
is intentionally pure: it does not fetch market data, read secrets, call
exchange APIs, place orders, persist records, or simulate candle-by-candle
exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Iterable


class RiskExitDirection(Enum):
    """Supported planning directions."""

    LONG = "LONG"
    SHORT = "SHORT"


class RiskExitPlanStatus(Enum):
    """Risk/exit plan validity statuses."""

    VALID = "VALID"
    SKIPPED = "SKIPPED"
    INVALID = "INVALID"


class RiskExitTargetSource(Enum):
    """Supported target origins."""

    R_MULTIPLE = "R_MULTIPLE"
    STRUCTURE = "STRUCTURE"
    MEASURED = "MEASURED"


@dataclass(frozen=True)
class TimeStopSettings:
    """Serialization-friendly time-stop settings for later simulators."""

    max_bars_in_trade: int | None = None
    required_r_multiple: float | None = None

    def __post_init__(self) -> None:
        if self.max_bars_in_trade is not None and self.max_bars_in_trade < 1:
            raise ValueError("max_bars_in_trade must be at least 1 when supplied")
        if self.required_r_multiple is not None and self.required_r_multiple < 0:
            raise ValueError("required_r_multiple must be non-negative when supplied")
        if self.required_r_multiple is not None and not isfinite(self.required_r_multiple):
            raise ValueError("required_r_multiple must be finite when supplied")


@dataclass(frozen=True)
class BreakEvenSettings:
    """Break-even movement condition data for later simulators."""

    enabled: bool = True
    trigger_r_multiple: float = 1.0
    stop_offset_r_multiple: float = 0.0

    def __post_init__(self) -> None:
        _require_finite_non_negative(
            self.trigger_r_multiple,
            "trigger_r_multiple",
            allow_zero=False,
        )
        _require_finite_non_negative(
            self.stop_offset_r_multiple,
            "stop_offset_r_multiple",
        )


@dataclass(frozen=True)
class TrailingStopSettings:
    """Trailing-stop settings for later simulators."""

    enabled: bool = False
    activation_r_multiple: float = 2.0
    trail_atr_multiplier: float = 1.0

    def __post_init__(self) -> None:
        _require_finite_non_negative(
            self.activation_r_multiple,
            "activation_r_multiple",
            allow_zero=False,
        )
        _require_finite_non_negative(
            self.trail_atr_multiplier,
            "trail_atr_multiplier",
        )


@dataclass(frozen=True)
class PartialExitSettings:
    """Partial-exit ratio planned at a target R multiple."""

    target_r_multiple: float
    exit_ratio: float

    def __post_init__(self) -> None:
        _require_finite_non_negative(
            self.target_r_multiple,
            "target_r_multiple",
            allow_zero=False,
        )
        _require_finite_non_negative(self.exit_ratio, "exit_ratio", allow_zero=False)
        if self.exit_ratio > 1:
            raise ValueError("exit_ratio must be less than or equal to 1")


@dataclass(frozen=True)
class RiskExitTarget:
    """One planned target with metadata explaining its origin."""

    name: str
    price: float
    source: RiskExitTargetSource | str
    r_multiple: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_finite_non_negative(self.price, "price", allow_zero=False)
        if self.r_multiple is not None:
            _require_finite_non_negative(self.r_multiple, "r_multiple")
        _coerce_target_source(self.source)


@dataclass(frozen=True)
class RiskExitConfig:
    """Configuration for deterministic risk/exit planning."""

    atr_buffer_multiplier: float = 0.2
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    time_stop: TimeStopSettings = field(default_factory=TimeStopSettings)
    break_even: BreakEvenSettings = field(default_factory=BreakEvenSettings)
    trailing_stop: TrailingStopSettings = field(default_factory=TrailingStopSettings)
    partial_exits: tuple[PartialExitSettings, ...] = field(
        default_factory=lambda: (
            PartialExitSettings(1.0, 0.33),
            PartialExitSettings(2.0, 0.33),
            PartialExitSettings(3.0, 0.34),
        )
    )

    def __post_init__(self) -> None:
        _require_finite_non_negative(self.atr_buffer_multiplier, "atr_buffer_multiplier")
        _validate_r_multiples(self.r_multiples)
        _require_finite_non_negative(self.minimum_first_target_r, "minimum_first_target_r")
        _validate_partial_exit_total(self.partial_exits)


@dataclass(frozen=True)
class RiskExitPlan:
    """Reusable pattern risk/exit plan data contract."""

    direction: RiskExitDirection | str
    entry_price: float | None
    structural_stop: float | None
    atr: float | None
    atr_buffer_multiplier: float
    atr_buffer: float | None
    stop_price: float | None
    risk_per_unit: float | None
    targets: tuple[RiskExitTarget, ...]
    status: RiskExitPlanStatus | str
    reasons: tuple[str, ...] = ()
    minimum_first_target_r: float = 0.8
    time_stop: TimeStopSettings = field(default_factory=TimeStopSettings)
    break_even: BreakEvenSettings = field(default_factory=BreakEvenSettings)
    trailing_stop: TrailingStopSettings = field(default_factory=TrailingStopSettings)
    partial_exits: tuple[PartialExitSettings, ...] = ()


def create_risk_exit_plan(
    *,
    direction: RiskExitDirection | str,
    entry_price: float | int | None,
    structural_stop: float | int | None,
    atr: float | int | None,
    config: RiskExitConfig | None = None,
    structural_targets: Iterable[float | int] | None = None,
    measured_targets: Iterable[float | int] | None = None,
) -> RiskExitPlan:
    """Create a deterministic reusable risk/exit plan.

    Pattern-specific callers are responsible for deriving ``entry_price``,
    ``structural_stop``, structural targets, and measured targets from their own
    events. This function only validates supplied values, applies the ATR stop
    buffer, calculates R-based targets, combines optional caller-supplied
    targets, and records skip/invalid reasons.
    """

    risk_config = config or RiskExitConfig()
    plan_direction = _coerce_direction(direction)
    reasons: list[str] = []

    entry = _optional_float(entry_price)
    stop_reference = _optional_float(structural_stop)
    atr_value = _optional_float(atr)

    if entry is None or entry <= 0:
        reasons.append("entry_price must be a finite positive number")
    if stop_reference is None or stop_reference <= 0:
        reasons.append("structural_stop must be a finite positive number")
    if atr_value is None or atr_value < 0:
        reasons.append("atr must be a finite non-negative number")

    if reasons:
        return _invalid_plan(
            plan_direction,
            entry,
            stop_reference,
            atr_value,
            risk_config,
            tuple(reasons),
        )

    assert entry is not None
    assert stop_reference is not None
    assert atr_value is not None

    atr_buffer = atr_value * risk_config.atr_buffer_multiplier
    if plan_direction == RiskExitDirection.LONG:
        stop_price = stop_reference - atr_buffer
        risk_per_unit = entry - stop_price
    else:
        stop_price = stop_reference + atr_buffer
        risk_per_unit = stop_price - entry

    if stop_price <= 0 or not isfinite(stop_price):
        reasons.append("stop_price must be a finite positive number")
    if risk_per_unit <= 0 or not isfinite(risk_per_unit):
        reasons.append("risk_per_unit must be positive after ATR buffer")

    if reasons:
        return RiskExitPlan(
            direction=plan_direction,
            entry_price=entry,
            structural_stop=stop_reference,
            atr=atr_value,
            atr_buffer_multiplier=risk_config.atr_buffer_multiplier,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            targets=(),
            status=RiskExitPlanStatus.INVALID,
            reasons=tuple(reasons),
            minimum_first_target_r=risk_config.minimum_first_target_r,
            time_stop=risk_config.time_stop,
            break_even=risk_config.break_even,
            trailing_stop=risk_config.trailing_stop,
            partial_exits=risk_config.partial_exits,
        )

    try:
        r_targets = calculate_r_multiple_targets(
            direction=plan_direction,
            entry_price=entry,
            risk_per_unit=risk_per_unit,
            r_multiples=risk_config.r_multiples,
        )
        targets = combine_targets(
            direction=plan_direction,
            entry_price=entry,
            risk_per_unit=risk_per_unit,
            r_targets=r_targets,
            structural_targets=structural_targets,
            measured_targets=measured_targets,
        )
    except ValueError as exc:
        return RiskExitPlan(
            direction=plan_direction,
            entry_price=entry,
            structural_stop=stop_reference,
            atr=atr_value,
            atr_buffer_multiplier=risk_config.atr_buffer_multiplier,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            targets=(),
            status=RiskExitPlanStatus.INVALID,
            reasons=(str(exc),),
            minimum_first_target_r=risk_config.minimum_first_target_r,
            time_stop=risk_config.time_stop,
            break_even=risk_config.break_even,
            trailing_stop=risk_config.trailing_stop,
            partial_exits=risk_config.partial_exits,
        )

    status = RiskExitPlanStatus.VALID
    if targets:
        first_target_r = targets[0].r_multiple
        if first_target_r is not None and first_target_r < risk_config.minimum_first_target_r:
            status = RiskExitPlanStatus.SKIPPED
            reasons.append(
                "first actionable target is below minimum_first_target_r "
                f"({first_target_r} < {risk_config.minimum_first_target_r})"
            )
    else:
        status = RiskExitPlanStatus.INVALID
        reasons.append("at least one actionable target is required")

    return RiskExitPlan(
        direction=plan_direction,
        entry_price=entry,
        structural_stop=stop_reference,
        atr=atr_value,
        atr_buffer_multiplier=risk_config.atr_buffer_multiplier,
        atr_buffer=atr_buffer,
        stop_price=stop_price,
        risk_per_unit=risk_per_unit,
        targets=targets,
        status=status,
        reasons=tuple(reasons),
        minimum_first_target_r=risk_config.minimum_first_target_r,
        time_stop=risk_config.time_stop,
        break_even=risk_config.break_even,
        trailing_stop=risk_config.trailing_stop,
        partial_exits=risk_config.partial_exits,
    )


def calculate_r_multiple_targets(
    *,
    direction: RiskExitDirection | str,
    entry_price: float,
    risk_per_unit: float,
    r_multiples: Iterable[float] = (1.0, 2.0, 3.0),
) -> tuple[RiskExitTarget, ...]:
    """Calculate deterministic R-multiple targets for long or short plans."""

    plan_direction = _coerce_direction(direction)
    _require_finite_non_negative(entry_price, "entry_price", allow_zero=False)
    _require_finite_non_negative(risk_per_unit, "risk_per_unit", allow_zero=False)
    multiples = tuple(r_multiples)
    _validate_r_multiples(multiples)

    targets: list[RiskExitTarget] = []
    for index, multiple in enumerate(multiples, start=1):
        if plan_direction == RiskExitDirection.LONG:
            price = entry_price + risk_per_unit * multiple
        else:
            price = entry_price - risk_per_unit * multiple
        targets.append(
            RiskExitTarget(
                name=f"TP{index}",
                price=price,
                source=RiskExitTargetSource.R_MULTIPLE,
                r_multiple=multiple,
                metadata={"rule": "r_multiple"},
            )
        )
    return tuple(targets)


def combine_targets(
    *,
    direction: RiskExitDirection | str,
    entry_price: float,
    risk_per_unit: float,
    r_targets: tuple[RiskExitTarget, ...],
    structural_targets: Iterable[float | int] | None = None,
    measured_targets: Iterable[float | int] | None = None,
) -> tuple[RiskExitTarget, ...]:
    """Combine R, structural, and measured targets deterministically.

    The reusable default is TP1 from the first R target, TP2 from the nearest
    actionable structural target when supplied, and TP3 from the nearest
    actionable measured target when supplied. Missing optional targets fall back
    to the matching R-multiple targets, preserving source metadata for every
    target.
    """

    if not r_targets:
        return ()
    plan_direction = _coerce_direction(direction)
    _require_finite_non_negative(entry_price, "entry_price", allow_zero=False)
    _require_finite_non_negative(risk_per_unit, "risk_per_unit", allow_zero=False)

    combined = list(r_targets[:3])
    structural_target = _nearest_actionable_target(
        plan_direction,
        entry_price,
        structural_targets,
    )
    if structural_target is not None and len(combined) >= 2:
        combined[1] = RiskExitTarget(
            name="TP2",
            price=structural_target,
            source=RiskExitTargetSource.STRUCTURE,
            r_multiple=_target_r_multiple(
                plan_direction,
                entry_price,
                structural_target,
                risk_per_unit,
            ),
            metadata={"rule": "nearest_actionable_structure"},
        )

    measured_target = _nearest_actionable_target(
        plan_direction,
        entry_price,
        measured_targets,
    )
    if measured_target is not None and len(combined) >= 3:
        combined[2] = RiskExitTarget(
            name="TP3",
            price=measured_target,
            source=RiskExitTargetSource.MEASURED,
            r_multiple=_target_r_multiple(
                plan_direction,
                entry_price,
                measured_target,
                risk_per_unit,
            ),
            metadata={"rule": "nearest_actionable_measured"},
        )

    return tuple(combined)


def _invalid_plan(
    direction: RiskExitDirection,
    entry_price: float | None,
    structural_stop: float | None,
    atr: float | None,
    config: RiskExitConfig,
    reasons: tuple[str, ...],
) -> RiskExitPlan:
    return RiskExitPlan(
        direction=direction,
        entry_price=entry_price,
        structural_stop=structural_stop,
        atr=atr,
        atr_buffer_multiplier=config.atr_buffer_multiplier,
        atr_buffer=None,
        stop_price=None,
        risk_per_unit=None,
        targets=(),
        status=RiskExitPlanStatus.INVALID,
        reasons=reasons,
        minimum_first_target_r=config.minimum_first_target_r,
        time_stop=config.time_stop,
        break_even=config.break_even,
        trailing_stop=config.trailing_stop,
        partial_exits=config.partial_exits,
    )


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    try:
        return RiskExitDirection(str(direction).upper())
    except ValueError as exc:
        raise ValueError("direction must be LONG or SHORT") from exc


def _coerce_target_source(
    source: RiskExitTargetSource | str,
) -> RiskExitTargetSource:
    if isinstance(source, RiskExitTargetSource):
        return source
    try:
        return RiskExitTargetSource(str(source).upper())
    except ValueError as exc:
        raise ValueError("source must be R_MULTIPLE, STRUCTURE, or MEASURED") from exc


def _optional_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result):
        return None
    return result


def _require_finite_non_negative(
    value: float,
    name: str,
    *,
    allow_zero: bool = True,
) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    elif value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_r_multiples(r_multiples: tuple[float, ...]) -> None:
    if not r_multiples:
        raise ValueError("r_multiples must include at least one target")
    for multiple in r_multiples:
        _require_finite_non_negative(multiple, "r_multiple", allow_zero=False)


def _validate_partial_exit_total(partial_exits: tuple[PartialExitSettings, ...]) -> None:
    total_ratio = sum(partial.exit_ratio for partial in partial_exits)
    if total_ratio > 1.0 + 1e-12:
        raise ValueError("partial exit ratios must sum to 1 or less")


def _nearest_actionable_target(
    direction: RiskExitDirection,
    entry_price: float,
    targets: Iterable[float | int] | None,
) -> float | None:
    if targets is None:
        return None

    actionable: list[float] = []
    for target in targets:
        target_price = _optional_float(target)
        if target_price is None or target_price <= 0:
            continue
        if direction == RiskExitDirection.LONG and target_price > entry_price:
            actionable.append(target_price)
        if direction == RiskExitDirection.SHORT and target_price < entry_price:
            actionable.append(target_price)

    if not actionable:
        return None
    if direction == RiskExitDirection.LONG:
        return min(actionable)
    return max(actionable)


def _target_r_multiple(
    direction: RiskExitDirection,
    entry_price: float,
    target_price: float,
    risk_per_unit: float,
) -> float:
    if direction == RiskExitDirection.LONG:
        return (target_price - entry_price) / risk_per_unit
    return (entry_price - target_price) / risk_per_unit
