from pathlib import Path

import pytest

from quant_bitcoin.patterns import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitDirection,
    RiskExitPlanStatus,
    RiskExitTargetSource,
    TimeStopSettings,
    TrailingStopSettings,
    calculate_r_multiple_targets,
    create_risk_exit_plan,
)


def test_long_stop_with_atr_buffer() -> None:
    plan = create_risk_exit_plan(
        direction=RiskExitDirection.LONG,
        entry_price=100.0,
        structural_stop=95.0,
        atr=10.0,
        config=RiskExitConfig(atr_buffer_multiplier=0.2),
    )

    assert plan.status == RiskExitPlanStatus.VALID
    assert plan.atr_buffer == pytest.approx(2.0)
    assert plan.stop_price == pytest.approx(93.0)
    assert plan.risk_per_unit == pytest.approx(7.0)


def test_short_stop_with_atr_buffer() -> None:
    plan = create_risk_exit_plan(
        direction="SHORT",
        entry_price=100.0,
        structural_stop=105.0,
        atr=10.0,
        config=RiskExitConfig(atr_buffer_multiplier=0.2),
    )

    assert plan.status == RiskExitPlanStatus.VALID
    assert plan.atr_buffer == pytest.approx(2.0)
    assert plan.stop_price == pytest.approx(107.0)
    assert plan.risk_per_unit == pytest.approx(7.0)


def test_r_multiple_targets_for_long_and_short() -> None:
    long_targets = calculate_r_multiple_targets(
        direction=RiskExitDirection.LONG,
        entry_price=100.0,
        risk_per_unit=5.0,
    )
    short_targets = calculate_r_multiple_targets(
        direction=RiskExitDirection.SHORT,
        entry_price=100.0,
        risk_per_unit=5.0,
    )

    assert [target.name for target in long_targets] == ["TP1", "TP2", "TP3"]
    assert [target.price for target in long_targets] == pytest.approx([105.0, 110.0, 115.0])
    assert [target.r_multiple for target in long_targets] == pytest.approx([1.0, 2.0, 3.0])
    assert all(target.source == RiskExitTargetSource.R_MULTIPLE for target in long_targets)
    assert [target.price for target in short_targets] == pytest.approx([95.0, 90.0, 85.0])


def test_minimum_first_target_threshold_passes_with_default_one_r_target() -> None:
    plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=0.0,
        config=RiskExitConfig(minimum_first_target_r=0.8),
    )

    assert plan.status == RiskExitPlanStatus.VALID
    assert plan.reasons == ()
    assert plan.targets[0].r_multiple == pytest.approx(1.0)


def test_minimum_first_target_threshold_skips_when_first_target_is_too_close() -> None:
    plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=0.0,
        config=RiskExitConfig(r_multiples=(0.5, 2.0, 3.0), minimum_first_target_r=0.8),
    )

    assert plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.reasons[0]


def test_invalid_non_positive_risk_handling() -> None:
    plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=100.0,
        atr=0.0,
    )

    assert plan.status == RiskExitPlanStatus.INVALID
    assert plan.targets == ()
    assert "risk_per_unit must be positive after ATR buffer" in plan.reasons


def test_invalid_atr_or_missing_value_handling() -> None:
    missing_entry = create_risk_exit_plan(
        direction="LONG",
        entry_price=None,
        structural_stop=95.0,
        atr=1.0,
    )
    invalid_atr = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=float("nan"),
    )
    negative_atr = create_risk_exit_plan(
        direction="SHORT",
        entry_price=100.0,
        structural_stop=105.0,
        atr=-1.0,
    )

    assert missing_entry.status == RiskExitPlanStatus.INVALID
    assert "entry_price must be a finite positive number" in missing_entry.reasons
    assert invalid_atr.status == RiskExitPlanStatus.INVALID
    assert "atr must be a finite non-negative number" in invalid_atr.reasons
    assert negative_atr.status == RiskExitPlanStatus.INVALID
    assert "atr must be a finite non-negative number" in negative_atr.reasons


def test_partial_exit_ratio_validation() -> None:
    RiskExitConfig(
        partial_exits=(
            PartialExitSettings(target_r_multiple=1.0, exit_ratio=0.5),
            PartialExitSettings(target_r_multiple=2.0, exit_ratio=0.5),
        )
    )

    with pytest.raises(ValueError, match="exit_ratio must be less than or equal to 1"):
        PartialExitSettings(target_r_multiple=1.0, exit_ratio=1.1)
    with pytest.raises(ValueError, match="partial exit ratios must sum to 1 or less"):
        RiskExitConfig(
            partial_exits=(
                PartialExitSettings(target_r_multiple=1.0, exit_ratio=0.6),
                PartialExitSettings(target_r_multiple=2.0, exit_ratio=0.5),
            )
        )


def test_combines_optional_structural_and_measured_targets_with_metadata() -> None:
    plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=0.0,
        structural_targets=[103.0, 111.0, 99.0],
        measured_targets=[112.0, 118.0],
    )

    assert [target.name for target in plan.targets] == ["TP1", "TP2", "TP3"]
    assert plan.targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert plan.targets[1].source == RiskExitTargetSource.STRUCTURE
    assert plan.targets[1].price == pytest.approx(103.0)
    assert plan.targets[1].r_multiple == pytest.approx(0.6)
    assert plan.targets[1].metadata["rule"] == "nearest_actionable_structure"
    assert plan.targets[1].metadata["target_source"] == "STRUCTURE"
    assert plan.targets[2].source == RiskExitTargetSource.MEASURED
    assert plan.targets[2].price == pytest.approx(112.0)
    assert plan.targets[2].r_multiple == pytest.approx(2.4)
    assert plan.targets[2].metadata["target_source"] == "MEASURED"
    semantics = plan.target_semantics
    assert semantics["schema_version"] == "target_semantics_v1"
    assert semantics["risk_targets"][1]["source"] == "STRUCTURE"
    assert semantics["risk_targets"][2]["source"] == "MEASURED"
    assert semantics["structural_targets"][0]["price"] == pytest.approx(103.0)
    assert semantics["measured_targets"][0]["price"] == pytest.approx(112.0)


def test_detector_target_reference_is_separate_from_measured_target_semantics() -> None:
    plan = create_risk_exit_plan(
        direction="LONG",
        entry_price=100.0,
        structural_stop=95.0,
        atr=0.0,
        detector_target_reference=123.0,
        measured_targets=[120.0],
    )

    semantics = plan.target_semantics
    assert semantics["detector_target_reference"] == pytest.approx(123.0)
    assert semantics["measured_targets"][0]["price"] == pytest.approx(120.0)
    assert semantics["risk_targets"][2]["source"] == "MEASURED"
    assert semantics["risk_targets"][2]["price"] == pytest.approx(120.0)


def test_represents_time_stop_break_even_trailing_stop_and_partial_exit_settings() -> None:
    config = RiskExitConfig(
        time_stop=TimeStopSettings(max_bars_in_trade=12, required_r_multiple=1.0),
        break_even=BreakEvenSettings(enabled=True, trigger_r_multiple=1.5, stop_offset_r_multiple=0.1),
        trailing_stop=TrailingStopSettings(enabled=True, activation_r_multiple=2.0, trail_atr_multiplier=1.2),
        partial_exits=(
            PartialExitSettings(target_r_multiple=1.0, exit_ratio=0.5),
            PartialExitSettings(target_r_multiple=2.0, exit_ratio=0.25),
        ),
    )

    plan = create_risk_exit_plan(
        direction="SHORT",
        entry_price=100.0,
        structural_stop=105.0,
        atr=0.0,
        config=config,
    )

    assert plan.time_stop.max_bars_in_trade == 12
    assert plan.break_even.trigger_r_multiple == pytest.approx(1.5)
    assert plan.trailing_stop.enabled is True
    assert [partial.exit_ratio for partial in plan.partial_exits] == pytest.approx([0.5, 0.25])


def test_risk_exit_module_does_not_import_exchange_clients_or_execution_dependencies() -> None:
    source = Path("quant_bitcoin/patterns/risk_exit.py").read_text()

    forbidden_terms = [
        "binance",
        "create_order",
        "order_endpoint",
        "api_key",
        "api_secret",
        "ENABLE_LIVE_TRADING",
        "quant_bitcoin.execution",
    ]
    assert all(term not in source for term in forbidden_terms)
