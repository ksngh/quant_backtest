# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`
- `docs/ledger_archives/backlog_task_101_150.md`
- `docs/ledger_archives/backlog_task_151_200.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 201-250)
- Completed (2026-05-28): Task 250 `FRONTEND_FVG_V2_CHANNEL_OVERLAY_VISUALIZATION` (added saved-metadata FVG v2 channel line, anchor, touch, and entry/exit overlays on the price chart).
- Completed (2026-05-28): Task 249 `FVG_V2_CHANNEL_GEOMETRY_PERSISTENCE_AND_API` (exposed channel geometry, boundary, line-price, and ambiguity metadata through saved-run trade API fields without DB schema changes).
- Completed (2026-05-28): Task 248 `FVG_V2_CHANNEL_RETEST_ENTRY_AND_BOUNDARY_EXIT` (added opt-in FVG v2 channel retest entries with dynamic line stops/targets and no ATR stop/target basis).
- Completed (2026-05-28): Task 247 `FVG_V2_PARALLEL_CHANNEL_DETECTION_CONTRACT` (added deterministic upward parallel-channel detector from low anchors and intervening high touch).
- Completed (2026-05-28): Task 246 `TRADE_ROW_COST_DETAIL_DISCLOSURE` (added expandable per-trade fee/spread/slippage/cost detail UX without DB schema changes).
- Completed (2026-05-28): Task 245 `FRONTEND_BACKTEST_RUN_LIST_FILTER_UI` (added frontend left-side saved-run filter controls wired to backend query parameters).
- Completed (2026-05-28): Task 244 `BACKEND_BACKTEST_RUN_LIST_FILTERS` (added read-only backend/API/persistence filters for saved backtest run list).
- Completed (2026-05-28): Task 243 `DASHBOARD_COLLAPSIBLE_INDICATOR_DIAGNOSTICS` (added collapsible/progressive-disclosure indicator and diagnostics groups).
- Completed (2026-05-28): Task 242 `DASHBOARD_CHART_INTERACTION_AND_LAYOUT` (added chart-first layout with drag/pan/zoom/reset interactions).
- Completed (2026-05-28): Task 241 `REFACTOR_COST_SEMANTICS_LEDGER_RECONCILIATION` (reconciled price/cost semantics vocabulary across engine, persistence/API/frontend, docs, status, history, backlog, and tests).
- Completed (2026-05-28): Task 240 `TRADE_COST_BREAKDOWN_PERSISTENCE` (added structured per-execution `cost_breakdown` metadata through execution serialization, persistence payloads, API flattening, and frontend display/type coverage).
- Completed (2026-05-28): Task 239 `COST_AWARE_NET_RR_ENTRY_FILTER` (added opt-in deterministic cost-aware entry filter with net reward/RR gating, CLI parameters, metadata, and SKIP reason `COST_INFEASIBLE_NET_RR`).
- Completed (2026-05-28): Task 238 `BACKTEST_EXECUTION_PRICE_SEMANTICS_SPLIT` (made new execution `price`/persisted trade `price` raw fill price, kept `effective_price` diagnostic, and reconciled net PnL from raw gross movement minus explicit costs).
- Completed (2026-05-27): Task 237 `FVG_RETEST_V2_DOCUMENTATION_LEDGER_RECONCILIATION_AND_ARCHIVE_CHECK` (reconciled FVG v2 docs/status/history/backlog and confirmed no 201-250 archive is required yet).
- Completed (2026-05-27): Task 236 `FVG_RETEST_V2_WALK_FORWARD_AND_OOS_RESEARCH_PROTOCOL` (added FVG v2 parameter-declaration validation, WFO/OOS research protocol evidence packaging, FVG v2 WFO grouping dimensions, and docs).
- Completed (2026-05-27): Task 235 `FVG_RETEST_V2_BACKEND_FRONTEND_READONLY_DIAGNOSTICS` (exposed saved-run FVG v2 diagnostics through backend metadata/research reports, frontend read-only panel/helper, and API/README docs).
- Completed (2026-05-27): Task 234 `FVG_RETEST_V2_FIXTURE_AND_NO_LOOKAHEAD_TEST_EXPANSION` (added reusable FVG v2 synthetic fixtures and no-lookahead/metadata regression tests).
- Completed (2026-05-27): Task 233 `FVG_RETEST_V2_CLI_DIAGNOSTICS_AND_PARAMETER_GRID` (added FVG v2 CLI settings/diagnostics metadata, entry-trigger CLI support, parameter-grid axes, and API/README notes).
- Completed (2026-05-27): Task 232 `FVG_STOP_MODE_AND_REACTION_FAILURE_EXIT_POLICY` (added FVG stop modes, stop metadata, invalid swing-stop handling, reaction-failure action semantics, and docs).
- Completed (2026-05-27): Task 231 `FVG_LIQUIDITY_TARGET_RESOLVER_AND_TAKE_PROFIT_POLICY` (added confirmed-pivot FVG liquidity target resolver, opt-in structural-target injection, risk-plan metadata, and docs caveat).
- Completed (2026-05-27): Task 230 `FVG_RETEST_ENTRY_TRIGGER_AND_POLICY_PRESET` (added opt-in retest entry triggers, FVG retest policy preset, touch/reaction metadata propagation, CLI trigger metadata, and docs).
- Completed (2026-05-27): Task 229 `FVG_FIBONACCI_RETRACEMENT_CONFLUENCE_FILTER` (added deterministic Fibonacci retracement confluence, default-off FVG diagnostics/filtering, metadata propagation, and docs).
- Completed (2026-05-27): Task 228 `FVG_DETECTOR_TREND_SCORE_AND_EMA_FILTER_INTEGRATION` (added default-off FVG trend diagnostics/filtering, score metadata, action propagation, and docs).
- Completed (2026-05-27): Task 227 `EMA_MULTITIMEFRAME_TREND_SCORE_INDICATOR` (added EMA trend features, diagnostic multi-timeframe trend scoring, metadata timing docs, and alignment integration tests).
- Completed (2026-05-27): Task 226 `MULTITIMEFRAME_CANDLE_AGGREGATION_AND_ALIGNMENT_CONTRACT` (added completed-candle multi-timeframe aggregation/alignment, metadata contract docs, no-lookahead boundary tests, and offline safety checks).
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
- Next explicit task: Task 251 or ledger maintenance should archive the completed 201-250 window before adding a new root backlog range.
- Follow-up candidate: run the opt-in FVG v2 channel mode on the approved 2026-05-20 dataset and inspect saved channel overlays/end-to-end metadata.
- Follow-up candidate: `RAW_FILL_RANGE_VALIDATION_AND_FVG_FIXED_FIXTURE` (add deterministic fixture coverage and warning/error metadata when requested/raw simulated fills fall outside the source candle high-low range).
- Follow-up candidate: `RUN_FVG_RETEST_V2_WFO_OOS_ON_APPROVED_DATASET` (execute the Task 236 protocol on a fixed dataset with predeclared splits and realistic costs; keep strategy research-only unless a later task explicitly changes status).
- Follow-up candidate: `LIVE_EXECUTION_KILL_SWITCH_AND_MAX_NOTIONAL_GUARDS` (prerequisite before any future live execution task).
- Follow-up candidate: `LIVE_EXECUTION_SYMBOL_FILTER_AND_STALE_DATA_PRECHECKS` (exchange filter, stale candle, and clock-skew checks before live intent submission).
- Follow-up candidate: `LIVE_EXECUTION_IDEMPOTENCY_AND_RESTART_RECONCILIATION` (durable duplicate-order prevention and restart recovery).
- Follow-up candidate: `LIVE_EXECUTION_CANCEL_REPLACE_AND_PARTIAL_FILL_POLICY` (cancel/replace, timeout, orphan-order, and partial-fill handling).
- Follow-up candidate: `LIVE_EXECUTION_MONITORING_ALERTING_AND_SECRET_POLICY` (alerts, credential storage/rotation, redaction, and operational readiness).
- Follow-up candidate: add visual regression/UI tests for dashboard marker/table/channel-overlay rendering once a frontend test harness is assigned.
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
- Created (2026-05-28): Tasks 247-250 complete the active 201-250 root backlog window. Archive `backlog_task_201_250.md` when the next task beyond 250 is created or when ledger maintenance is explicitly assigned.
