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
        "pattern_research_note": _redact(
            _pattern_research_note(
                strategy_config=strategy_config,
                summary_metadata=summary_metadata,
                diagnostics_summary=diagnostics_summary,
                trades=trades,
            )
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


def _pattern_research_note(
    *,
    strategy_config: dict[str, Any],
    summary_metadata: dict[str, Any],
    diagnostics_summary: dict[str, Any],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    params = strategy_config.get("parameters") if isinstance(strategy_config.get("parameters"), dict) else {}
    strategy_metadata = strategy_config.get("metadata") if isinstance(strategy_config.get("metadata"), dict) else {}
    explanation = strategy_metadata.get("explanation") if isinstance(strategy_metadata.get("explanation"), dict) else {}
    policy = _first_record(
        params.get("pattern_execution_policy"),
        summary_metadata.get("pattern_execution_policy"),
        diagnostics_summary.get("pattern_execution_policy"),
    )
    entry_trade = _first_trade(trades, contains="ENTRY")
    entry_metadata = entry_trade.get("metadata") if isinstance(entry_trade.get("metadata"), dict) else {}
    first_trade_metadata = _first_trade_metadata(trades)
    pattern_type = (
        _text(first_trade_metadata.get("pattern_type"))
        or _text(params.get("pattern"))
        or _text(params.get("pattern_key"))
        or _text(strategy_config.get("key"))
        or "UNAVAILABLE"
    )
    score_calibration = _first_record(summary_metadata.get("score_calibration"), diagnostics_summary.get("score_calibration"))
    risk_exit_audit = _first_record(summary_metadata.get("risk_exit_audit"), diagnostics_summary.get("risk_exit_audit"))
    timing_diagnostics = _first_record(summary_metadata.get("timing_diagnostics"), diagnostics_summary.get("timing_diagnostics"))
    performance_diagnostics = _first_record(summary_metadata.get("performance_diagnostics"), diagnostics_summary.get("performance_diagnostics"))
    trade_attribution = _first_record(summary_metadata.get("trade_attribution"), diagnostics_summary.get("trade_attribution"))
    cost_profile = _first_record(summary_metadata.get("cost_profile"), diagnostics_summary.get("cost_profile"))
    cost_summary = _first_record(summary_metadata.get("cost_summary"), diagnostics_summary.get("cost_summary"))
    metadata_schema_index = _first_record(diagnostics_summary.get("metadata_schema_index"))
    score_lift = _first_record(score_calibration.get("score_lift") if score_calibration else None)
    regime_attribution = _regime_attribution(trade_attribution)
    top_failure_reasons = _top_failure_reasons(performance_diagnostics, timing_diagnostics, risk_exit_audit, score_calibration)
    recommendations = _recommended_next_experiments(summary_metadata, diagnostics_summary)

    return {
        "schema_version": "pattern_research_note_v1",
        "status": "available" if first_trade_metadata or policy or _text(params.get("pattern")) or _text(params.get("pattern_key")) else "partial",
        "pattern_type": pattern_type,
        "hypothesis": {
            "algorithm_name": explanation.get("algorithm_name") or pattern_type,
            "economic_rationale": _list(policy.get("economic_rationale") if policy else None)
            or _list(policy.get("research_hypothesis") if policy else None)
            or _list(explanation.get("design_rationale")),
            "score_warning": "pattern_score is heuristic unless out-of-sample score lift is demonstrated.",
        },
        "detector_conditions": {
            "detection_rules": _list(explanation.get("detection_rules")),
            "pattern_status": first_trade_metadata.get("pattern_status"),
            "pattern_direction": first_trade_metadata.get("pattern_direction") or first_trade_metadata.get("direction"),
            "score_components_available": isinstance(first_trade_metadata.get("score_components"), dict),
            "candidate_diagnostics_available": isinstance(first_trade_metadata.get("candidate_diagnostics"), dict),
        },
        "windows_candles_observed": {
            "market_interval": _text((strategy_config.get("market") or {}).get("interval")) if isinstance(strategy_config.get("market"), dict) else None,
            "bars_waited": entry_metadata.get("bars_waited"),
            "timing_path_mode": timing_diagnostics.get("path_mode") if timing_diagnostics else None,
            "completed_trade_count": timing_diagnostics.get("completed_trade_count") if timing_diagnostics else None,
        },
        "entry_mode": {
            "selected_entry_mode": entry_metadata.get("entry_mode") or (policy or {}).get("selected_entry_mode"),
            "fill_assumption": entry_metadata.get("fill_assumption"),
            "fill_price_source": entry_metadata.get("fill_price_source"),
            "entry_reference": entry_metadata.get("entry_reference"),
            "requested_price": entry_metadata.get("requested_price"),
        },
        "risk_plan": {
            "position_sizing": summary_metadata.get("position_sizing"),
            "risk_per_unit": entry_metadata.get("risk_per_unit"),
            "fill_adjusted_risk_per_unit": entry_metadata.get("fill_adjusted_risk_per_unit"),
            "risk_plan_aligned_to_fill": entry_metadata.get("risk_plan_aligned_to_fill"),
            "target_semantics": first_trade_metadata.get("target_semantics"),
            "risk_exit_audit_schema": risk_exit_audit.get("schema_version") if risk_exit_audit else None,
        },
        "cost_profile": {
            "profile": cost_profile,
            "summary": cost_summary,
        },
        "score_reliability": {
            "score_contract": score_calibration.get("score_contract") if score_calibration else None,
            "inference_strength": score_calibration.get("inference_strength") if score_calibration else None,
            "score_lift": score_lift,
            "warnings": _list(score_calibration.get("warnings") if score_calibration else None),
        },
        "no_lookahead_status": {
            "metadata_schema_index": metadata_schema_index,
            "timing_note": "Report uses already-saved run metadata and does not rerun detection.",
        },
        "regime_dependence": regime_attribution,
        "top_failure_reasons": top_failure_reasons,
        "limitations": [
            "Research-grade saved-run summary; not production or live-trading readiness.",
            "Pattern scores are heuristic unless independent OOS calibration supports them.",
            "Legacy rows may have unavailable fields.",
        ],
        "recommended_next_analyses": recommendations,
    }


def _first_record(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _first_trade(trades: list[dict[str, Any]], *, contains: str) -> dict[str, Any]:
    marker = contains.upper()
    for trade in trades:
        signal = str(trade.get("position_signal") or trade.get("signal") or "").upper()
        if marker in signal:
            return trade
    return {}


def _first_trade_metadata(trades: list[dict[str, Any]]) -> dict[str, Any]:
    for trade in trades:
        metadata = trade.get("metadata")
        if isinstance(metadata, dict):
            return metadata
    return {}


def _top_failure_reasons(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    for section in sections:
        flags = section.get("flags") if isinstance(section, dict) else None
        if not isinstance(flags, (list, tuple)):
            continue
        for flag in flags:
            if isinstance(flag, dict):
                reasons.append(
                    {
                        "code": flag.get("code"),
                        "severity": flag.get("severity"),
                        "message": flag.get("message") or flag.get("description"),
                    }
                )
    return reasons[:8]


def _regime_attribution(trade_attribution: dict[str, Any]) -> dict[str, Any]:
    attribution = trade_attribution.get("attribution") if isinstance(trade_attribution, dict) else None
    if not isinstance(attribution, dict):
        return {"status": "unavailable"}
    return {
        "by_market_regime": attribution.get("by_market_regime"),
        "by_volatility_regime": attribution.get("by_volatility_regime"),
        "by_liquidity_regime": attribution.get("by_liquidity_regime"),
        "by_spread_regime": attribution.get("by_spread_regime"),
        "by_session": attribution.get("by_session"),
    }


def _list(value: Any) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item]
    return []


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


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
        "## Pattern Research Note",
        f"- Pattern: {report.get('pattern_research_note', {}).get('pattern_type')}",
        f"- Status: {report.get('pattern_research_note', {}).get('status')}",
        f"- Entry Mode: {report.get('pattern_research_note', {}).get('entry_mode', {}).get('selected_entry_mode')}",
        f"- Score Reliability: {report.get('pattern_research_note', {}).get('score_reliability', {}).get('inference_strength')}",
        "",
        "## Recommended Next Experiments",
        *[f"- {item}" for item in report["recommended_next_experiments"]],
        "",
        "## Safety Boundary",
        *[f"- {item}" for item in report["safety_boundary"]],
    ]
    return "\n".join(lines)
