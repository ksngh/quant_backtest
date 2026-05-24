# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`
- `docs/ledger_archives/backlog_task_101_150.md`
- `docs/ledger_archives/backlog_task_151_200.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 201-225)
- Completed (2026-05-24): Task 225 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION_AFTER_PATTERN_RESEARCH_BATCH` (archived Tasks 151-200, reconciled current ledgers/status, and verified task checklist state).
- Completed (2026-05-24): Task 224 `LIVE_READINESS_BOUNDARY_NON_EXECUTION_AUDIT_FOR_PATTERNS` (re-audited pattern strategy/backtesting live boundaries and added static safety tests).
- Completed (2026-05-24): Task 223 `PERFORMANCE_REPORT_PATTERN_RESEARCH_NOTE_AUTOGENERATION` (added structured pattern research note JSON/markdown generation and read-only frontend preview).
- Completed (2026-05-24): Task 222 `TEST_FIXTURE_EXPANSION_SYNTHETIC_PATTERNS` (added reusable deterministic pattern fixtures and fixture contract tests).
- Completed (2026-05-24): Task 221 `BACKEND_API_PATTERN_RISK_SCORE_SCHEMA_HARDENING` (added backend metadata schema index, sensitive metadata redaction, and enriched/legacy metadata service tests).
- Completed (2026-05-24): Task 220 `FRONTEND_PATTERN_GEOMETRY_AND_SCORE_COMPONENT_DISPLAY` (added read-only frontend pattern geometry, score component, and candidate-overfit diagnostics display).
- Completed (2026-05-24): Task 219 `FRONTEND_EXECUTION_RISK_ASSUMPTION_EXPLANATION` (added read-only frontend execution/risk assumption panel and metadata-path verification).
- Completed (2026-05-24): Task 218 `CHART_PATTERN_CANDIDATE_EXPLOSION_AND_OVERFIT_DIAGNOSTICS` (added opt-in Cup/Handle, Diamond, and Adam/Eve candidate diagnostics plus score overfit attribution).
- Completed (2026-05-24): Task 217 `TRENDLINE_FALSE_BREAKOUT_FORENSICS` (added Trendline false-breakout post-break path forensics and summary metadata wiring).
- Completed (2026-05-24): Task 216 `FVG_OB_RETEST_FILL_RATE_AND_OPPORTUNITY_COST_REPORT` (added FVG/Order Block retest fill-rate, missed-move, opportunity-cost, adverse-excursion, and grouping diagnostics).
- Completed (2026-05-24): Task 215 `PATTERN_WFO_REGIME_STRATIFIED_VALIDATION` (added opt-in fold and aggregate WFO stratification with sparse-strata warnings).
- Completed (2026-05-24): Task 214 `PATTERN_BACKTEST_PARAMETER_GRID_AND_SENSITIVITY_RUNNER` (added offline deterministic pattern parameter-grid runner and docs).
- Completed (2026-05-24): Task 213 `COMMON_INDICATOR_CACHE_FOR_ALL_PATTERNS` (generalized cached pattern indicator evaluation beyond FVG/Order Block).
- Completed (2026-05-24): Task 212 `RISK_EXIT_AUDIT_MFE_MAE_AND_INTRABAR_ATTRIBUTION` (expanded risk-exit audit grouping, MFE/MAE attribution, and intrabar diagnostics).
- Completed (2026-05-24): Task 211 `PATTERN_EXIT_TARGET_SEMANTICS_NORMALIZATION` (added `target_semantics_v1` and separated detector target references from executable risk targets).
- Completed (2026-05-24): Task 210 `RISK_SOFT_INVALIDATION_AUTOWIRING` (auto-wired supported pattern soft invalidation into canonical exit simulation).
- Completed (2026-05-24): Task 209 `GUARDRAIL_OPEN_POSITION_KILL_SWITCH_AND_EXPOSURE_CAPS` (added opt-in guardrail forced exits and entry exposure caps).
- Completed (2026-05-24): Task 208 `POSITION_SIZING_FILL_ADJUSTED_RISK_CONTRACT` (enforced fill-adjusted risk metadata for equity-risk-fraction pattern sizing).
- Completed (2026-05-24): Task 207 `SHORT_ECONOMICS_FUNDING_BORROW_LIQUIDATION_RESEARCH_MODEL` (added optional research-only short borrow/funding carrying-cost accounting and diagnostic liquidation metadata).
- Completed (2026-05-24): Task 206 `TRANSACTION_COST_DEFAULT_PRESETS_AND_FAILSAFE_WARNINGS` (added zero-cost metadata, strict zero-cost blocking option, and cost sensitivity reporting).
- Completed (2026-05-24): Task 205 `PIVOT_STRENGTH_ATR_AND_MULTITIMEFRAME_RESEARCH` (added pivot strength/density diagnostics and opt-in ATR-strength pivot filtering).
- Completed (2026-05-24): Task 204 `ATR_TIMING_AND_REGIME_THRESHOLD_CALIBRATION` (expanded ATR timing metadata and ATR multiplier sensitivity diagnostics).
- Completed (2026-05-24): Task 203 `VOLUME_RATIO_PRIOR_ONLY_AND_NOTIONAL_BASELINE` (added explicit volume-ratio baseline/input modes and notional-volume fallback).
- Completed (2026-05-24): Task 202 `INDICATOR_CURRENT_INCLUSION_AND_PRIOR_BASELINE_CONTRACT` (added indicator timing metadata helpers and prior-only baseline options).
- Completed (2026-05-24): Task 201 `MARKET_REGIME_CONDITIONED_PATTERN_THRESHOLDS` (added opt-in pattern-regime threshold config and low-liquidity/wide-spread blocking).

## Important Blocked Work
- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` remains blocked pending explicit owner approval for live order execution and the live-readiness prerequisites documented in `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`.

## Current Candidates / Follow-ups
- Next explicit task: none assigned.
- Follow-up candidate: `LIVE_EXECUTION_KILL_SWITCH_AND_MAX_NOTIONAL_GUARDS` (prerequisite before any future live execution task).
- Follow-up candidate: `LIVE_EXECUTION_SYMBOL_FILTER_AND_STALE_DATA_PRECHECKS` (exchange filter, stale candle, and clock-skew checks before live intent submission).
- Follow-up candidate: `LIVE_EXECUTION_IDEMPOTENCY_AND_RESTART_RECONCILIATION` (durable duplicate-order prevention and restart recovery).
- Follow-up candidate: `LIVE_EXECUTION_CANCEL_REPLACE_AND_PARTIAL_FILL_POLICY` (cancel/replace, timeout, orphan-order, and partial-fill handling).
- Follow-up candidate: `LIVE_EXECUTION_MONITORING_ALERTING_AND_SECRET_POLICY` (alerts, credential storage/rotation, redaction, and operational readiness).
- Follow-up candidate: add visual regression/UI tests for dashboard marker/table rendering once a frontend test harness is assigned.
- Candidate: `PATTERN_STRATEGY_OUTPUT_CONTRACT_DOCUMENTATION_AND_FIXTURE_EXPANSION` (document enriched stdout schema and broaden deterministic fixtures for short-side/no-fill cases).
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema if owner requires richer financial outputs.
- Follow-up candidate: align pattern persistence graph-point cash/position/equity to candle-timed fills for richer dashboard trace fidelity.
- Liquidity indicator implementation.
- Bid-Ask spread indicator implementation.

## Backend/Frontend Candidates
- Follow-up candidate: add a dedicated frontend unit/component test harness for dashboard helper/rendering behavior if future UI work continues.
- API contract evolution for any future backend/frontend coordination beyond the current read-only dashboard.
- Backend API extensions only when assigned by a future backend task.
- Frontend dashboard extensions only when assigned by a future frontend task.

## Deferred Verification
- Local Docker runtime verification for previously completed Docker-related tasks in a Docker-capable environment.
- Backend FastAPI route tests require a Python environment with `fastapi` installed.

## Ledger Maintenance
- Completed (2026-05-24): Reconciled root backlog archive pointers to fixed 50-task ranges and moved Tasks 088-100 entries into `docs/ledger_archives/backlog_task_051_100.md`.
- Completed (2026-05-24): Task 171 created `docs/ledger_archives/backlog_task_101_150.md` and reduced root backlog to the Tasks 151-171 recent window.
- Completed (2026-05-24): Task 225 created `docs/ledger_archives/backlog_task_151_200.md` and reduced root backlog to the Tasks 201-225 recent window.
