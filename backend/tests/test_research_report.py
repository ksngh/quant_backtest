from backend.quant_backtest_api.services.research_report import (
    build_backtest_research_report,
    redact_sensitive,
)


def test_research_report_builder_redacts_sensitive_metadata() -> None:
    report = build_backtest_research_report(
        run={
            "id": 7,
            "run_key": "run-7",
            "engine_name": "strategy_engine",
            "engine_version": "v1",
            "status": "completed",
            "market": {"source": "csv", "symbol": "BTCUSDT", "interval": "1m"},
            "metadata": {
                "reproducibility": {
                    "dataset_hash": "abc",
                    "database_url": "postgres://user:password@localhost/db",
                    "api_key": "secret-api-key",
                }
            },
        },
        strategy_config={
            "key": "pattern",
            "name": "Pattern Strategy",
            "version": "v1",
            "parameters": {
                "pattern": "FAIR_VALUE_GAP",
                "password": "strategy-password",
            },
            "parameters_hash": "hash-1",
            "metadata": {"explanation": {"algorithm_name": "Fair Value Gap"}},
        },
        summary={
            "starting_cash": 10000.0,
            "final_equity": 10100.0,
            "total_return": 0.01,
            "trade_count": 1,
            "max_drawdown": -0.02,
            "metadata": {
                "cost_summary": {"zero_transaction_cost_assumption": False},
                "cost_profile": {"profile_key": "conservative_crypto_1m"},
                "position_sizing": {"mode": "EQUITY_RISK_FRACTION", "value": 0.01},
                "pattern_execution_policy": {
                    "schema_version": "pattern_execution_policy_v1",
                    "selected_entry_mode": "LIMIT_AT_PATTERN_MIDPOINT",
                    "economic_rationale": "Retest imbalance before continuation.",
                },
                "score_calibration": {
                    "schema_version": "pattern_score_calibration_v1",
                    "score_contract": "pattern_score is a heuristic quality score, not a calibrated probability.",
                    "inference_strength": "PARTIAL",
                    "score_lift": {"interpretation": "POSITIVE_LIFT"},
                    "warnings": ["small sample"],
                },
                "performance_diagnostics": {
                    "flags": [
                        {
                            "code": "LOW_HIT_RATE",
                            "suggested_next_analysis": "Check entry filters.",
                        }
                    ]
                },
            },
        },
        trades=[
            {
                "id": 1,
                "signal": "LONG_ENTRY",
                "position_signal": "LONG_ENTRY",
                "metadata": {
                    "secret": "trade-secret",
                    "pattern_type": "FAIR_VALUE_GAP",
                    "pattern_status": "VALID",
                    "pattern_direction": "BULLISH",
                    "entry_mode": "LIMIT_AT_PATTERN_MIDPOINT",
                    "fill_assumption": "historical_limit_fill",
                    "fill_price_source": "limit_touch",
                    "entry_reference": 101.0,
                    "requested_price": 101.0,
                    "risk_per_unit": 2.0,
                    "fill_adjusted_risk_per_unit": 2.2,
                    "risk_plan_aligned_to_fill": True,
                    "score_components": {"gap_quality": {"raw_score": 0.8}},
                    "target_semantics": {"schema_version": "target_semantics_v1"},
                },
            }
        ],
        graph_points=[{"sequence": 1}],
        diagnostics={"summary": {"trade_attribution": {"trade_metrics": {"expectancy": 1.0}}}},
        warnings=[{"code": "W", "message": "warning"}],
    )

    payload_text = str(report)
    assert report["schema_version"] == "backtest_research_report_v1"
    assert report["reproducibility"]["database_url"] == "[REDACTED]"
    assert report["reproducibility"]["api_key"] == "[REDACTED]"
    assert report["strategy"]["parameters"]["password"] == "[REDACTED]"
    note = report["pattern_research_note"]
    assert note["schema_version"] == "pattern_research_note_v1"
    assert note["pattern_type"] == "FAIR_VALUE_GAP"
    assert note["entry_mode"]["selected_entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert note["risk_plan"]["risk_plan_aligned_to_fill"] is True
    assert note["score_reliability"]["inference_strength"] == "PARTIAL"
    assert note["score_reliability"]["score_lift"]["interpretation"] == "POSITIVE_LIFT"
    assert note["top_failure_reasons"][0]["code"] == "LOW_HIT_RATE"
    assert "not production or live-trading readiness" in note["limitations"][0]
    assert "Check entry filters." in report["recommended_next_experiments"]
    assert "postgres://user:password@localhost/db" not in payload_text
    assert "secret-api-key" not in payload_text
    assert "strategy-password" not in payload_text
    assert "Backtest Research Report: Run 7" in report["markdown"]
    assert "## Pattern Research Note" in report["markdown"]


def test_research_report_builder_handles_minimal_legacy_metadata() -> None:
    report = build_backtest_research_report(
        run={"id": 1, "run_key": "legacy", "market": None, "metadata": None},
        strategy_config={"key": "legacy", "name": "Legacy", "version": "v0"},
        summary={"metadata": None, "final_equity": 10000.0, "total_return": 0.0, "trade_count": 0},
        trades=[],
        graph_points=[],
        diagnostics=None,
        warnings=[],
    )

    assert report["reproducibility"] == {"status": "missing"}
    assert report["pattern_research_note"]["status"] == "partial"
    assert report["pattern_research_note"]["entry_mode"]["selected_entry_mode"] is None
    assert report["data_summary"] == {"trade_rows": 0, "graph_points": 0, "warnings": []}
    assert "Diagnostics are explanatory and may be partial for legacy runs." in report["limitations"]
    assert report["recommended_next_experiments"] == [
        "Run walk-forward validation and compare cost profiles before changing strategy parameters."
    ]


def test_redact_sensitive_masks_nested_credentials() -> None:
    assert redact_sensitive(
        {
            "safe": "value",
            "nested": {
                "db_url": "postgres://example",
                "access_token": "token-value",
            },
        }
    ) == {
        "safe": "value",
        "nested": {
            "db_url": "[REDACTED]",
            "access_token": "[REDACTED]",
        },
    }
