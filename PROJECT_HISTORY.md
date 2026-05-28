# Project History (Recent Window)

This file keeps recent completion context only.
Older history is preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/project_history_task_001_050.md`
- `docs/ledger_archives/project_history_task_051_100.md`
- `docs/ledger_archives/project_history_task_101_150.md`
- `docs/ledger_archives/project_history_task_151_200.md`

## Recent Completion Window (Tasks 201-246)
- 2026-05-24: Completed Task 201 `MARKET_REGIME_CONDITIONED_PATTERN_THRESHOLDS`; added opt-in pattern-regime threshold config, high-vol threshold overrides, low-liquidity/wide-spread entry blocking, strategy-level SKIP behavior, engine-level blocked-entry execution metadata, and CLI workflow/parameter reporting.
- 2026-05-24: Completed Task 202 `INDICATOR_CURRENT_INCLUSION_AND_PRIOR_BASELINE_CONTRACT`; added `indicator_timing_metadata_v1` helpers for ATR, Volume Ratio, Market Regime, and Pivots, prior-only volume/regime baseline options, and timing contract documentation.
- 2026-05-24: Completed Task 203 `VOLUME_RATIO_PRIOR_ONLY_AND_NOTIONAL_BASELINE`; added explicit `VolumeRatioBaselineMode`, `VolumeInputMode`, quote-volume fallback, trading-value input, and detector config propagation.
- 2026-05-24: Completed Task 204 `ATR_TIMING_AND_REGIME_THRESHOLD_CALIBRATION`; expanded ATR timing metadata, attached ATR metadata to pattern events/risk plans, and added ATR multiplier sensitivity diagnostics.
- 2026-05-24: Completed Task 205 `PIVOT_STRENGTH_ATR_AND_MULTITIMEFRAME_RESEARCH`; added pivot strength/density diagnostics, ATR-filter settings, and no-lookahead pivot metadata.
- 2026-05-24: Completed Task 206 `TRANSACTION_COST_DEFAULT_PRESETS_AND_FAILSAFE_WARNINGS`; added zero-cost profile helpers, high-severity zero-cost warnings, strict zero-cost blocking option, and deterministic cost sensitivity reporting.
- 2026-05-24: Completed Task 207 `SHORT_ECONOMICS_FUNDING_BORROW_LIQUIDATION_RESEARCH_MODEL`; added optional research-only borrow/funding carrying-cost accounting and diagnostic-only short liquidation metadata.
- 2026-05-24: Completed Task 208 `POSITION_SIZING_FILL_ADJUSTED_RISK_CONTRACT`; added fill-adjusted risk metadata and blocked stale/missing/non-positive pattern risk for equity-risk-fraction sizing.
- 2026-05-24: Completed Task 209 `GUARDRAIL_OPEN_POSITION_KILL_SWITCH_AND_EXPOSURE_CAPS`; added opt-in guardrail forced exits, entry exposure caps, and forced-exit metadata.
- 2026-05-24: Completed Task 210 `RISK_SOFT_INVALIDATION_AUTOWIRING`; added `pattern_soft_invalidation_v1` adapter metadata and auto-wired supported soft invalidation rules into canonical exit simulation.
- 2026-05-24: Completed Task 211 `PATTERN_EXIT_TARGET_SEMANTICS_NORMALIZATION`; added `target_semantics_v1`, separated detector references from executable risk targets, and exposed target-source metadata.
- 2026-05-24: Completed Task 212 `RISK_EXIT_AUDIT_MFE_MAE_AND_INTRABAR_ATTRIBUTION`; expanded risk-exit audit grouping, target-source quality, MFE/MAE path attribution, intrabar ambiguity counts, stop movement, and cost-dominance diagnostics.
- 2026-05-24: Completed Task 213 `COMMON_INDICATOR_CACHE_FOR_ALL_PATTERNS`; generalized the offline pattern indicator cache and shared strategy/runner context across all six supported patterns.
- 2026-05-24: Completed Task 214 `PATTERN_BACKTEST_PARAMETER_GRID_AND_SENSITIVITY_RUNNER`; added deterministic parameter-grid expansion, dry-run validation, max-combination guardrails, CLI output, docs, and metrics rows.
- 2026-05-24: Completed Task 215 `PATTERN_WFO_REGIME_STRATIFIED_VALIDATION`; extended offline WFO validation with opt-in fold and aggregate stratification plus sparse-strata warnings.
- 2026-05-24: Completed Task 216 `FVG_OB_RETEST_FILL_RATE_AND_OPPORTUNITY_COST_REPORT`; added retest fill-rate, missed-move, opportunity-cost, adverse-excursion, and grouping diagnostics for FVG/Order Block retest entries.
- 2026-05-24: Completed Task 217 `TRENDLINE_FALSE_BREAKOUT_FORENSICS`; added Trendline false-breakout post-break outcome diagnostics and grouping metadata.
- 2026-05-24: Completed Task 218 `CHART_PATTERN_CANDIDATE_EXPLOSION_AND_OVERFIT_DIAGNOSTICS`; added opt-in candidate diagnostics for Cup/Handle, Diamond, and Adam/Eve plus score overfit attribution.
- 2026-05-24: Completed Task 219 `FRONTEND_EXECUTION_RISK_ASSUMPTION_EXPLANATION`; added a read-only frontend Execution Assumptions panel and backend metadata-path coverage.
- 2026-05-24: Completed Task 220 `FRONTEND_PATTERN_GEOMETRY_AND_SCORE_COMPONENT_DISPLAY`; added read-only frontend Pattern Geometry, score-component, and candidate-overfit diagnostics display.
- 2026-05-24: Completed Task 221 `BACKEND_API_PATTERN_RISK_SCORE_SCHEMA_HARDENING`; added backend response redaction for sensitive metadata keys and `diagnostics.summary.metadata_schema_index` schema discovery.
- 2026-05-24: Completed Task 222 `TEST_FIXTURE_EXPANSION_SYNTHETIC_PATTERNS`; added reusable deterministic synthetic fixtures for six patterns with entry/exit/no-lookahead coverage.
- 2026-05-24: Completed Task 223 `PERFORMANCE_REPORT_PATTERN_RESEARCH_NOTE_AUTOGENERATION`; added `pattern_research_note_v1` JSON/markdown sections and read-only frontend preview support.
- 2026-05-24: Completed Task 224 `LIVE_READINESS_BOUNDARY_NON_EXECUTION_AUDIT_FOR_PATTERNS`; re-audited pattern strategy/backtesting modules for execution-client coupling, updated the safety audit, and added static safety tests.
- 2026-05-24: Completed Task 225 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION_AFTER_PATTERN_RESEARCH_BATCH`; archived Tasks 151-200 into fixed ledger files, reduced root ledgers to Tasks 201-225, reconciled Task 188/189 checklist state, updated final status/backlog/history, and verified the final pattern research batch.
- 2026-05-27: Completed Task 226 `MULTITIMEFRAME_CANDLE_AGGREGATION_AND_ALIGNMENT_CONTRACT`; added deterministic completed-candle multi-timeframe aggregation/alignment, metadata contract documentation, no-lookahead boundary coverage, validation tests, and offline safety checks.
- 2026-05-27: Completed Task 227 `EMA_MULTITIMEFRAME_TREND_SCORE_INDICATOR`; added deterministic EMA trend features, diagnostic-only multi-timeframe trend scoring, metadata timing contracts, alignment integration tests, and offline safety checks without changing pattern strategy behavior.
- 2026-05-27: Completed Task 228 `FVG_DETECTOR_TREND_SCORE_AND_EMA_FILTER_INTEGRATION`; added default-off FVG multi-timeframe trend diagnostics/filtering, trend score metadata, canonical action metadata propagation, and default-off FVG strategy documentation.
- 2026-05-27: Completed Task 229 `FVG_FIBONACCI_RETRACEMENT_CONFLUENCE_FILTER`; added deterministic Fibonacci retracement confluence, default-off FVG diagnostics/hard-filtering, metadata propagation, and no-lookahead anchor documentation.
- 2026-05-27: Completed Task 230 `FVG_RETEST_ENTRY_TRIGGER_AND_POLICY_PRESET`; added opt-in retest entry triggers, FVG retest policy preset, touch/reaction metadata propagation, CLI trigger metadata, and default-preserving documentation.
- 2026-05-27: Completed Task 231 `FVG_LIQUIDITY_TARGET_RESOLVER_AND_TAKE_PROFIT_POLICY`; added confirmed-pivot FVG liquidity target resolver, opt-in strategy structural-target injection, risk-plan metadata, and OHLCV-liquidity caveat documentation.
- 2026-05-27: Completed Task 232 `FVG_STOP_MODE_AND_REACTION_FAILURE_EXIT_POLICY`; added FVG stop modes, stop metadata, invalid swing-stop handling, explicit reaction-failure action semantics, and documentation.
- 2026-05-27: Completed Task 233 `FVG_RETEST_V2_CLI_DIAGNOSTICS_AND_PARAMETER_GRID`; added FVG v2 CLI settings/diagnostics metadata, entry-trigger CLI support, parameter-grid axes, and API/README research-only notes.
- 2026-05-27: Completed Task 234 `FVG_RETEST_V2_FIXTURE_AND_NO_LOOKAHEAD_TEST_EXPANSION`; added reusable FVG v2 synthetic fixtures and no-lookahead/metadata regression tests for multi-timeframe, pivot, and reaction-entry behavior.
- 2026-05-27: Completed Task 235 `FVG_RETEST_V2_BACKEND_FRONTEND_READONLY_DIAGNOSTICS`; exposed saved-run FVG v2 trend/Fibonacci/liquidity/entry/stop diagnostics through backend metadata, research reports, frontend helper/UI presentation, and read-only API/README documentation.
- 2026-05-27: Completed Task 236 `FVG_RETEST_V2_WALK_FORWARD_AND_OOS_RESEARCH_PROTOCOL`; added FVG v2 parameter-declaration validation, WFO/OOS research protocol JSON/markdown evidence packaging, FVG v2 WFO grouping dimensions, and protocol documentation.
- 2026-05-27: Completed Task 237 `FVG_RETEST_V2_DOCUMENTATION_LEDGER_RECONCILIATION_AND_ARCHIVE_CHECK`; reconciled FVG v2 README/API/FVG/protocol docs, root status/history/backlog, and confirmed the active Tasks 201-237 window does not yet require a 201-250 archive.
- 2026-05-28: Completed Task 238 `BACKTEST_EXECUTION_PRICE_SEMANTICS_SPLIT`; changed new strategy-engine executions so `price`/persisted trade `price` are raw fill prices, retained `effective_price` as spread/slippage-adjusted diagnostics, and reconciled summary net PnL from raw gross PnL minus explicit transaction costs.
- 2026-05-28: Completed Task 239 `COST_AWARE_NET_RR_ENTRY_FILTER`; added an opt-in pattern entry gate using fee/spread/effective-slippage estimates, net reward bps, and net R/R, with CLI flags and `COST_INFEASIBLE_NET_RR` SKIP metadata.
- 2026-05-28: Completed Task 240 `TRADE_COST_BREAKDOWN_PERSISTENCE`; added structured `execution_cost_breakdown_v1` metadata to executions, CLI JSON, persistence payloads, API trade serialization, and frontend trade table/type coverage.
- 2026-05-28: Completed Task 241 `REFACTOR_COST_SEMANTICS_LEDGER_RECONCILIATION`; documented raw/effective price and cost-breakdown semantics in API/architecture docs, updated root status/backlog/history, and confirmed no 201-250 archive is required yet.
- 2026-05-28: Created Tasks 242-246 from owner dashboard feedback: chart-first drag/zoom UX, collapsible indicator diagnostics, backend run-list filters, frontend filter controls, and per-trade cost detail disclosure. No implementation was executed in this task-creation step.

## Active Historical Notes
- Live trading approval/credential policy/endpoint allowlist/kill-switch design remains unresolved and blocks Task 138.
- Docker runtime verification remains environment-dependent where Docker is unavailable.
- Backend FastAPI route tests require a Python environment with `fastapi` installed.
- 2026-05-24: Ledger range cleanup reconciled root `BACKLOG.md` and `PROJECT_HISTORY.md` with the fixed 50-task archive rule by replacing partial archives with `*_task_051_100.md` archives and keeping root ledgers focused on Tasks 101-148.
- 2026-05-24: Task 171 archived Tasks 101-150 into `docs/ledger_archives/backlog_task_101_150.md` and `docs/ledger_archives/project_history_task_101_150.md`.
- 2026-05-24: Task 225 archived Tasks 151-200 into `docs/ledger_archives/backlog_task_151_200.md` and `docs/ledger_archives/project_history_task_151_200.md`.
- 2026-05-28: Tasks 242-246 were added to the active root ledger window; Tasks 201-246 remain below the 201-250 archive boundary, so 201-250 archive files were not created.
