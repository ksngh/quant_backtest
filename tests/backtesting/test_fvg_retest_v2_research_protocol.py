from __future__ import annotations

import pytest

from quant_bitcoin.backtesting.fvg_retest_v2_research_protocol import (
    FvgRetestV2ResearchProtocolConfig,
    default_fvg_retest_v2_parameter_grid,
    run_fvg_retest_v2_research_protocol,
    validate_fvg_retest_v2_parameter_declaration,
)
from quant_bitcoin.backtesting.walk_forward import WalkForwardConfig
from tests.fixtures.synthetic_fvg_v2 import bullish_retest_v2_scenario


def _bounded_grid() -> dict[str, tuple[object, ...]]:
    return {
        "detector.use_multitimeframe_trend_score": (False,),
        "detector.use_fibonacci_confluence": (False,),
        "risk.require_liquidity_target": (False,),
        "entry.mode": ("limit_at_pattern_midpoint",),
        "entry.trigger": ("touch",),
        "risk.stop_mode": ("fvg_boundary_atr_buffer",),
        "cost.profile": ("conservative_crypto_1m",),
    }


def test_default_fvg_v2_parameter_declaration_is_predeclared_and_realistic() -> None:
    declaration = validate_fvg_retest_v2_parameter_declaration(
        default_fvg_retest_v2_parameter_grid(),
        config=FvgRetestV2ResearchProtocolConfig(max_combinations=32),
    )

    assert declaration["schema_version"] == "fvg_retest_v2_parameter_declaration_v1"
    assert declaration["combination_count"] == 16
    assert "entry.trigger" in declaration["required_paths"]
    assert "cost.profile" in declaration["required_paths"]
    assert "regime_stratification.session_tag" in declaration["grouping_dimensions"]


def test_fvg_v2_parameter_declaration_rejects_missing_ranges() -> None:
    grid = _bounded_grid()
    grid.pop("entry.trigger")

    with pytest.raises(ValueError, match="missing required FVG v2 parameter paths"):
        validate_fvg_retest_v2_parameter_declaration(grid)


def test_fvg_v2_parameter_declaration_rejects_empty_and_excessive_ranges() -> None:
    grid = _bounded_grid()
    grid["entry.trigger"] = ()
    with pytest.raises(ValueError, match="parameter path has no values"):
        validate_fvg_retest_v2_parameter_declaration(grid)

    with pytest.raises(ValueError, match="parameter grid has"):
        validate_fvg_retest_v2_parameter_declaration(
            {
                **_bounded_grid(),
                "entry.trigger": ("touch", "touch_and_reaction_close"),
                "risk.stop_mode": ("fvg_boundary_atr_buffer", "swing_pivot"),
            },
            config=FvgRetestV2ResearchProtocolConfig(max_combinations=1),
        )


def test_fvg_v2_parameter_declaration_rejects_zero_cost_only_protocol() -> None:
    with pytest.raises(ValueError, match="non-zero cost.profile"):
        validate_fvg_retest_v2_parameter_declaration(
            {**_bounded_grid(), "cost.profile": ("zero",)}
        )


def test_fvg_v2_research_protocol_runs_bounded_wfo_smoke() -> None:
    payload = run_fvg_retest_v2_research_protocol(
        bullish_retest_v2_scenario().candles,
        walk_forward_config=WalkForwardConfig(
            "8min",
            "8min",
            "8min",
            regime_stratification_enabled=True,
            minimum_trades_per_stratum=1,
        ),
        parameter_grid=_bounded_grid(),
        config=FvgRetestV2ResearchProtocolConfig(max_combinations=2),
    )

    assert payload["schema_version"] == "fvg_retest_v2_research_protocol_v1"
    assert payload["research_scope"] == "offline_backtest_research_only"
    assert payload["parameter_declaration"]["combination_count"] == 1
    assert len(payload["parameter_grid_report"]["rows"]) == 1
    assert len(payload["variant_results"]) == 1
    variant = payload["variant_results"][0]
    assert variant["summary"]["schema_version"] == "fvg_retest_v2_variant_summary_v1"
    assert variant["summary"]["research_decision"]["promotion_allowed"] is False
    assert "timing" in variant["summary"]
    assert payload["research_note"]["promotion_allowed"] is False
    assert "FVG Retest V2 Research Protocol" in payload["markdown"]
    assert any("No live trading" in item for item in payload["safety_boundary"])
