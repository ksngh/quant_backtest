from types import SimpleNamespace

from quant_bitcoin.backtesting.score_calibration import calculate_score_calibration_diagnostics


def _execution(
    score,
    pnl,
    r,
    *,
    components=None,
    pattern_type="FAIR_VALUE_GAP",
    direction="BULLISH",
    fold_id=None,
    atr_multiplier=None,
    market_regime=None,
    volatility_regime=None,
    candidate_diagnostics=None,
):
    metadata = {
        "pattern_score": score,
        "pattern_type": pattern_type,
        "pattern_direction": direction,
        "fold_id": fold_id,
        "score_components": components
        or {
            "gap_quality": {
                "weighted_score": score or 0.0,
                "source": "observed_gap_size",
                "is_placeholder": False,
                "included_in_executable_score": True,
            }
        },
    }
    if atr_multiplier is not None:
        metadata["atr_buffer_multiplier"] = atr_multiplier
    if market_regime is not None:
        metadata["market_regime"] = market_regime
    if volatility_regime is not None:
        metadata["volatility_regime"] = volatility_regime
    if candidate_diagnostics is not None:
        metadata["candidate_diagnostics"] = candidate_diagnostics
    return SimpleNamespace(
        net_pnl=pnl,
        realized_r_multiple=r,
        position_side="LONG",
        metadata=metadata,
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


def test_score_lift_reports_positive_and_pattern_direction_buckets() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(0.2, -20.0, -0.2, pattern_type="FAIR_VALUE_GAP", direction="BULLISH"),
            _execution(0.3, -10.0, -0.1, pattern_type="FAIR_VALUE_GAP", direction="BULLISH"),
            _execution(0.8, 30.0, 0.3, pattern_type="FAIR_VALUE_GAP", direction="BULLISH"),
            _execution(0.9, 40.0, 0.4, pattern_type="FAIR_VALUE_GAP", direction="BULLISH"),
        ),
        min_trades_per_bucket=1,
    )

    assert diagnostics["score_lift"]["interpretation"] == "POSITIVE_LIFT"
    assert diagnostics["score_lift"]["high_minus_low_outcome"] == 0.5
    grouped = diagnostics["pattern_direction_buckets"][0]
    assert grouped["pattern_type"] == "FAIR_VALUE_GAP"
    assert grouped["direction"] == "BULLISH"
    assert grouped["score_lift"]["interpretation"] == "POSITIVE_LIFT"


def test_inverted_score_lift_emits_negative_lift_warning() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(0.2, 30.0, 0.3),
            _execution(0.3, 40.0, 0.4),
            _execution(0.8, -20.0, -0.2),
            _execution(0.9, -10.0, -0.1),
        ),
        min_trades_per_bucket=1,
    )

    assert diagnostics["score_lift"]["interpretation"] == "NEGATIVE_LIFT"
    assert "NEGATIVE_SCORE_LIFT" in {flag["code"] for flag in diagnostics["flags"]}


def test_placeholder_components_are_excluded_from_observed_ablation() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(
                0.8,
                20.0,
                0.2,
                components={
                    "observed_quality": {
                        "weighted_score": 0.2,
                        "source": "observed_quality",
                        "is_placeholder": False,
                        "included_in_executable_score": True,
                    },
                    "liquidity": {
                        "weighted_score": 0.1,
                        "source": "placeholder_policy",
                        "is_placeholder": True,
                        "included_in_executable_score": False,
                    },
                },
            ),
            _execution(0.2, -10.0, -0.1, components={}),
        ),
        min_trades_per_bucket=1,
    )

    observed = {
        row["component"]: row
        for row in diagnostics["component_analysis"]["observed_components"]
    }
    placeholders = {
        row["component"]: row
        for row in diagnostics["component_analysis"]["placeholder_components"]
    }
    assert "observed_quality" in observed
    assert "liquidity" not in observed
    assert "liquidity" in placeholders
    assert placeholders["liquidity"]["observed_ablation_delta_r"] is None


def test_fold_analysis_groups_oos_fold_metadata() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(0.2, -10.0, -0.1, fold_id="fold-1"),
            _execution(0.8, 30.0, 0.3, fold_id="fold-1"),
            _execution(0.9, 40.0, 0.4, fold_id="fold-2"),
        ),
        min_trades_per_bucket=1,
    )

    assert diagnostics["fold_analysis"]["has_oos_folds"] is True
    assert diagnostics["fold_analysis"]["fold_count"] == 2
    assert diagnostics["fold_analysis"]["folds"][0]["fold_id"] == "fold-1"


def test_atr_multiplier_sensitivity_groups_by_pattern_and_regime() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(
                0.8,
                30.0,
                0.3,
                atr_multiplier=0.2,
                market_regime="LOW_VOL_UPTREND",
                volatility_regime="LOW",
            ),
            _execution(
                0.8,
                -10.0,
                -0.1,
                atr_multiplier=0.4,
                market_regime="LOW_VOL_UPTREND",
                volatility_regime="LOW",
            ),
        ),
        min_trades_per_bucket=1,
    )

    sensitivity = diagnostics["atr_multiplier_sensitivity"]
    assert sensitivity["schema_version"] == "atr_multiplier_sensitivity_v1"
    assert sensitivity["has_comparable_settings"] is True
    assert [row["atr_buffer_multiplier"] for row in sensitivity["groups"]] == [0.2, 0.4]
    assert sensitivity["groups"][0]["pattern_type"] == "FAIR_VALUE_GAP"
    assert sensitivity["groups"][0]["market_regime"] == "LOW_VOL_UPTREND"
    assert sensitivity["groups"][0]["volatility_regime"] == "LOW"


def test_candidate_diagnostics_feed_score_overfit_warning() -> None:
    diagnostics = calculate_score_calibration_diagnostics(
        (
            _execution(
                0.8,
                -10.0,
                -0.1,
                pattern_type="DIAMOND_PATTERN",
                candidate_diagnostics={
                    "schema_version": "chart_pattern_candidate_diagnostics_v1",
                    "pattern_type": "DIAMOND_PATTERN",
                    "candidate_count": 25,
                    "evaluated_candidate_count": 10,
                    "candidate_to_pivot_ratio": 2.5,
                    "candidate_to_bar_ratio": 1.2,
                    "max_guard_hit": True,
                    "overfit_warnings": ("max_candidate_guard_hit",),
                    "rejected_by_reason": {
                        "pivot_window_rule_rejected": 15,
                        "max_candidate_guard_hit": 1,
                    },
                },
            ),
        ),
        min_trades_per_bucket=1,
    )

    candidate_report = diagnostics["candidate_diagnostics"]
    assert candidate_report["schema_version"] == "chart_pattern_candidate_overfit_attribution_v1"
    assert candidate_report["has_guard_hit"] is True
    assert candidate_report["has_overfit_warning"] is True
    group = candidate_report["groups"][0]
    assert group["pattern_type"] == "DIAMOND_PATTERN"
    assert group["max_candidate_count"] == 25.0
    assert group["rejected_by_reason"]["pivot_window_rule_rejected"] == 15
    assert "CHART_PATTERN_CANDIDATE_OVERFIT_RISK" in {
        flag["code"] for flag in diagnostics["flags"]
    }
