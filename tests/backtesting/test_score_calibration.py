from types import SimpleNamespace

from quant_bitcoin.backtesting.score_calibration import calculate_score_calibration_diagnostics


def _execution(score, pnl, r, *, components=None, pattern_type="FAIR_VALUE_GAP"):
    return SimpleNamespace(
        net_pnl=pnl,
        realized_r_multiple=r,
        position_side="LONG",
        metadata={
            "pattern_score": score,
            "pattern_type": pattern_type,
            "score_components": components or {
                "gap_quality": {
                    "weighted_score": score or 0.0,
                    "source": "observed_gap_size",
                    "is_placeholder": False,
                }
            },
        },
    )


def test_score_calibration_warns_when_higher_scores_perform_worse() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(0.2, 100.0, 1.0),
            _execution(0.3, 50.0, 0.5),
            _execution(0.8, -100.0, -1.0),
            _execution(0.9, -50.0, -0.5),
        ),
        min_trades_per_bucket=1,
    )

    codes = {flag["code"] for flag in diagnostics["flags"]}
    assert "NO_MONOTONIC_SCORE_IMPROVEMENT" in codes
    assert "HIGH_SCORE_NEGATIVE_EXPECTANCY" in codes
    high_bucket = diagnostics["buckets"][-1]
    assert high_bucket["average_r"] == -0.75


def test_score_calibration_missing_score_metadata_returns_partial_report() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            SimpleNamespace(
                net_pnl=25.0,
                realized_r_multiple=0.25,
                metadata={"pattern_type": "FAIR_VALUE_GAP"},
            ),
        )
    )

    assert diagnostics["schema_version"] == "pattern_score_calibration_v1"
    assert diagnostics["scored_trade_count"] == 0
    assert diagnostics["inference_strength"] == "PARTIAL"
    assert diagnostics["flags"][0]["code"] == "MISSING_SCORE_METADATA"


def test_score_calibration_warns_when_placeholder_components_dominate() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(
                0.8,
                10.0,
                0.1,
                components={
                    "liquidity": {
                        "weighted_score": 0.2,
                        "source": "placeholder_liquidity_context",
                        "is_placeholder": True,
                    }
                },
            ),
            _execution(
                0.7,
                12.0,
                0.2,
                components={
                    "liquidity": {
                        "weighted_score": 0.2,
                        "source": "placeholder_liquidity_context",
                        "is_placeholder": True,
                    }
                },
            ),
        ),
        min_trades_per_bucket=1,
    )

    codes = {flag["code"] for flag in diagnostics["flags"]}
    assert "PLACEHOLDER_COMPONENT_DOMINATES_SCORE" in codes
    assert diagnostics["component_analysis"]["placeholder_component_rate"] == 1.0


def test_threshold_sensitivity_does_not_mutate_thresholds() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(0.4, -10.0, -0.1),
            _execution(0.6, 20.0, 0.2),
            _execution(0.8, 30.0, 0.3),
        ),
        {"strategy_parameters": {"minimum_pattern_score": 0.6}},
        min_trades_per_bucket=1,
    )

    thresholds = diagnostics["threshold_sensitivity"]
    assert [row["minimum_pattern_score"] for row in thresholds] == [0.0, 0.2, 0.4, 0.6, 0.8]
    assert diagnostics["minimum_pattern_score"] == 0.6
    assert thresholds[3]["trade_count"] == 2
