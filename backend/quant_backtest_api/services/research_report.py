from __future__ import annotations

from typing import Any

SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "credential",
    "database_url",
    "db_url",
)


def build_backtest_research_report(
    *,
    run: dict[str, Any],
    strategy_config: dict[str, Any],
    summary: dict[str, Any],
    trades: list[dict[str, Any]],
    graph_points: list[dict[str, Any]],
    diagnostics: dict[str, Any] | None,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a portable read-only research report from already-loaded run data."""

    summary_metadata = summary.get("metadata") if isinstance(summary.get("metadata"), dict) else {}
    run_metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
    diagnostics_summary = diagnostics.get("summary") if isinstance(diagnostics, dict) and isinstance(diagnostics.get("summary"), dict) else {}
    report = {
        "schema_version": "backtest_research_report_v1",
        "run_identity": _redact(
            {
                "id": run.get("id"),
                "run_key": run.get("run_key"),
                "engine_name": run.get("engine_name"),
                "engine_version": run.get("engine_version"),
                "status": run.get("status"),
                "created_at": run.get("created_at"),
                "completed_at": run.get("completed_at"),
            }
        ),
        "market": _redact(run.get("market")),
        "strategy": _redact(
            {
                "key": strategy_config.get("key"),
                "name": strategy_config.get("name"),
                "version": strategy_config.get("version"),
                "parameters": strategy_config.get("parameters"),
                "parameters_hash": strategy_config.get("parameters_hash"),
                "explanation": (strategy_config.get("metadata") or {}).get("explanation") if isinstance(strategy_config.get("metadata"), dict) else None,
            }
        ),
        "reproducibility": _redact(run_metadata.get("reproducibility") if isinstance(run_metadata, dict) else None) or {"status": "missing"},
        "risk": _redact(
            {
                "position_sizing": summary_metadata.get("position_sizing"),
                "guardrails": summary_metadata.get("guardrails"),
                "short_exposure_policy": summary_metadata.get("short_exposure_policy"),
                "cost_profile": summary_metadata.get("cost_profile"),
                "cost_summary": summary_metadata.get("cost_summary"),
            }
        ),
        "performance": _redact(
            {
                "summary": {
                    "starting_cash": summary.get("starting_cash"),
                    "final_equity": summary.get("final_equity"),
                    "total_return": summary.get("total_return"),
                    "trade_count": summary.get("trade_count"),
                    "max_drawdown": summary.get("max_drawdown"),
                },
                "performance_metrics": summary_metadata.get("performance_metrics"),
                "trade_attribution": summary_metadata.get("trade_attribution") or diagnostics_summary.get("trade_attribution"),
            }
        ),
        "diagnostics": _redact(
            {
                "performance_diagnostics": summary_metadata.get("performance_diagnostics") or diagnostics_summary.get("performance_diagnostics"),
                "timing_diagnostics": summary_metadata.get("timing_diagnostics") or diagnostics_summary.get("timing_diagnostics"),
                "risk_exit_audit": summary_metadata.get("risk_exit_audit") or diagnostics_summary.get("risk_exit_audit"),
                "score_calibration": summary_metadata.get("score_calibration") or diagnostics_summary.get("score_calibration"),
            }
        ),
        "data_summary": {
            "trade_rows": len(trades),
            "graph_points": len(graph_points),
            "warnings": _redact(warnings),
        },
        "limitations": _limitations(summary_metadata),
        "safety_boundary": [
            "Read-only saved-run report.",
            "No backtest rerun was performed to generate this artifact.",
            "No live trading, order execution, exchange account access, or API key exposure.",
        ],
        "recommended_next_experiments": _recommended_next_experiments(summary_metadata, diagnostics_summary),
    }
    return {**report, "markdown": _to_markdown(report)}


def redact_sensitive(value: Any) -> Any:
    return _redact(value)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in SENSITIVE_KEY_PARTS):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact(item) for item in value)
    return value


def _limitations(summary_metadata: dict[str, Any]) -> list[str]:
    limitations = summary_metadata.get("limitations")
    result = [str(item) for item in limitations] if isinstance(limitations, (list, tuple)) else []
    result.extend(
        [
            "Historical simulation only; not live-trading approval.",
            "Diagnostics are explanatory and may be partial for legacy runs.",
        ]
    )
    return list(dict.fromkeys(result))


def _recommended_next_experiments(summary_metadata: dict[str, Any], diagnostics_summary: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    for section_name in ("performance_diagnostics", "timing_diagnostics", "risk_exit_audit", "score_calibration"):
        section = summary_metadata.get(section_name) or diagnostics_summary.get(section_name)
        if not isinstance(section, dict):
            continue
        flags = section.get("flags")
        if not isinstance(flags, (list, tuple)):
            continue
        for flag in flags:
            if isinstance(flag, dict) and flag.get("suggested_next_analysis"):
                recommendations.append(str(flag["suggested_next_analysis"]))
            elif isinstance(flag, dict) and flag.get("code"):
                recommendations.append(f"Inspect {flag['code']} evidence before changing parameters.")
    if not recommendations:
        recommendations.append("Run walk-forward validation and compare cost profiles before changing strategy parameters.")
    return list(dict.fromkeys(recommendations))[:8]


def _to_markdown(report: dict[str, Any]) -> str:
    identity = report["run_identity"]
    strategy = report["strategy"]
    market = report["market"] or {}
    performance = report["performance"]
    perf_summary = performance.get("summary") if isinstance(performance, dict) else {}
    lines = [
        f"# Backtest Research Report: Run {identity.get('id')}",
        "",
        "## Run",
        f"- Key: {identity.get('run_key')}",
        f"- Engine: {identity.get('engine_name')} {identity.get('engine_version')}",
        f"- Status: {identity.get('status')}",
        "",
        "## Market",
        f"- Symbol: {market.get('symbol')}",
        f"- Interval: {market.get('interval')}",
        f"- Source: {market.get('source')}",
        "",
        "## Strategy",
        f"- Name: {strategy.get('name')}",
        f"- Version: {strategy.get('version')}",
        f"- Parameters Hash: {strategy.get('parameters_hash')}",
        "",
        "## Performance",
        f"- Final Equity: {perf_summary.get('final_equity')}",
        f"- Total Return: {perf_summary.get('total_return')}",
        f"- Trade Count: {perf_summary.get('trade_count')}",
        f"- Max Drawdown: {perf_summary.get('max_drawdown')}",
        "",
        "## Recommended Next Experiments",
        *[f"- {item}" for item in report["recommended_next_experiments"]],
        "",
        "## Safety Boundary",
        *[f"- {item}" for item in report["safety_boundary"]],
    ]
    return "\n".join(lines)
