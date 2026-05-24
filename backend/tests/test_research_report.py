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
        trades=[{"id": 1, "metadata": {"secret": "trade-secret"}}],
        graph_points=[{"sequence": 1}],
        diagnostics={"summary": {"trade_attribution": {"trade_metrics": {"expectancy": 1.0}}}},
        warnings=[{"code": "W", "message": "warning"}],
    )

    payload_text = str(report)
    assert report["schema_version"] == "backtest_research_report_v1"
    assert report["reproducibility"]["database_url"] == "[REDACTED]"
    assert report["reproducibility"]["api_key"] == "[REDACTED]"
    assert report["strategy"]["parameters"]["password"] == "[REDACTED]"
    assert "Check entry filters." in report["recommended_next_experiments"]
    assert "postgres://user:password@localhost/db" not in payload_text
    assert "secret-api-key" not in payload_text
    assert "strategy-password" not in payload_text
    assert "Backtest Research Report: Run 7" in report["markdown"]


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
