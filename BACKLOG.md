# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`
- `docs/ledger_archives/backlog_task_101_150.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 151-187)
- Completed (2026-05-24): Task 187 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION_AFTER_BACKTEST_ANALYTICS` (final docs/status/backlog/history reconciliation, low-risk frontend helper refactor, and verification after Tasks 173-186).
- Completed (2026-05-24): Task 186 `SAVED_RUN_RESEARCH_REPORT_ARTIFACT` (add read-only saved-run research report JSON/markdown artifact, redaction, frontend preview, and API schema docs).
- Completed (2026-05-24): Task 185 `LIQUIDITY_SPREAD_AND_SESSION_FILTER_RESEARCH_FEATURES` (add OHLCV liquidity/spread/session proxies, attribution groups, and frontend tradability diagnostics).
- Completed (2026-05-24): Task 184 `BAD_RUN_EXPLAINER_AND_RECOMMENDED_NEXT_ANALYSIS_FRONTEND` (add read-only Run Conclusion panel mapping diagnostics to likely failure reasons and next analyses).
- Completed (2026-05-24): Task 183 `FRONTEND_STRATEGY_RISK_ENTRY_EXIT_DEEP_EXPLANATION` (upgrade read-only strategy explanation panels using actual run metadata and diagnostics).
- Completed (2026-05-24): Task 182 `PATTERN_WALK_FORWARD_OOS_VALIDATION_RUNNER` (extend offline walk-forward validation CLI/framework to pattern strategies with fold diagnostics).
- Completed (2026-05-24): Task 181 `PATTERN_SCORE_CALIBRATION_ABLATION_AND_THRESHOLDS` (add score bucket calibration, placeholder/component warnings, threshold sensitivity, and frontend score reliability display).
- Completed (2026-05-24): Task 180 `COST_PROFILE_PRESETS_AND_SENSITIVITY_REPORTING` (add named cost profiles, conflict handling, and cost-profile display).
- Completed (2026-05-24): Task 179 `CANONICAL_REGIME_GUARDRAIL_AND_CONTINUITY_CLI_WIRING` (wire continuity, market-regime, and guardrail controls into canonical CLI).
- Completed (2026-05-24): Task 178 `RISK_REWARD_TARGET_STOP_VALIDITY_AND_DOMINANCE_AUDIT` (add risk/exit audit diagnostics and frontend risk panel).
- Completed (2026-05-24): Task 177 `PATTERN_SPECIFIC_ENTRY_EXIT_POLICY_MATRIX` (add pattern-specific policy compatibility matrix, metadata, and frontend display).
- Completed (2026-05-24): Task 176 `FVG_ENTRY_MODE_RETEST_VERSUS_MOMENTUM_EXPERIMENTS` (add FVG entry-mode CLI controls and comparison diagnostics).
- Completed (2026-05-24): Task 175 `ENTRY_EXIT_TIMING_FORENSICS_AND_MFE_MAE_METRICS` (add entry/exit timing diagnostics, MFE/MAE path metrics, and frontend timing diagnosis).
- Completed (2026-05-24): Task 174 `BACKTEST_POOR_PERFORMANCE_FORENSIC_DIAGNOSTICS` (classify saved-run poor-performance causes and render run diagnosis).
- Completed (2026-05-24): Task 173 `BACKTEST_METRIC_FRONTEND_REPORTING_AND_INTERPRETATION` (surface saved-run performance diagnostics and interpretation in the read-only dashboard).
- Completed (2026-05-24): Task 172 `FVG_ACTUAL_FILL_RISK_PLAN_ALIGNMENT` (align FVG actual fill price with risk/target simulation so take-profit cannot be a realized loss).
- Completed (2026-05-24): Task 171 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION` (final remediation cleanup, docs, and ledgers).
- Completed (2026-05-24): Task 170 `EXECUTION_READINESS_SAFETY_BOUNDARY_AUDIT` (audit execution readiness and live-trading blockers).
- Completed (2026-05-24): Task 169 `BACKTEST_REPRODUCIBILITY_RUN_METADATA` (record reproducibility metadata for saved runs).
- Completed (2026-05-24): Task 168 `RESEARCH_DIAGNOSTICS_PERSISTENCE_AND_API_REPORTING` (persist and expose research diagnostics).
- Completed (2026-05-24): Task 167 `RSI_AND_MEAN_REVERSION_SIGNAL_CONTRACT_REVIEW` (review RSI/mean-reversion signal semantics).
- Completed (2026-05-24): Task 166 `WALK_FORWARD_OOS_MONTE_CARLO_VALIDATION` (add walk-forward/OOS/Monte Carlo validation utilities).
- Completed (2026-05-24): Task 165 `PATTERN_SCORE_FEATURE_AUDIT_AND_CALIBRATION` (audit pattern scoring features and calibration metadata).
- Completed (2026-05-24): Task 164 `MARKET_REGIME_AND_INDICATOR_EXPANSION` (add market-regime and richer indicator research inputs).
- Completed (2026-05-24): Task 163 `PERFORMANCE_ATTRIBUTION_METRICS_CUBE` (add richer performance attribution metrics).
- Completed (2026-05-24): Task 162 `SHORT_ECONOMICS_MARGIN_FUNDING_LIMITATIONS` (make short economics limitations explicit).
- Completed (2026-05-24): Task 161 `RISK_PER_TRADE_SIZING_AND_GUARDRAILS` (add risk-per-trade sizing controls and guardrails).
- Completed (2026-05-24): Task 160 `TRANSACTION_COST_AND_SLIPPAGE_REALISM` (improve cost/slippage realism without live execution behavior).
- Completed (2026-05-24): Task 159 `NO_LOOKAHEAD_PATTERN_DETECTION_CONTRACT` (audit pattern detection boundaries for no-lookahead behavior).
- Completed (2026-05-24): Task 158 `CANDLE_DATA_INTEGRITY_AND_GAP_VALIDATION` (validate candle continuity/gaps before research/backtest assumptions).
- Completed (2026-05-24): Task 157 `INTRABAR_SEQUENCING_POLICY_INTEGRATION` (use reusable intrabar sequencing policy for ambiguous stop/target exits).
- Completed (2026-05-24): Task 156 `CANONICAL_SOFT_INVALIDATION_INTEGRATION` (wire supported close-based soft invalidation into canonical pattern action expansion).
- Completed (2026-05-24): Task 155 `RISK_PLAN_INVALID_ACTION_SAFETY` (invalid/skipped risk plans must emit non-executable SKIP diagnostics only).
- Completed (2026-05-24): Task 154 `ENTRY_FILL_PRICE_MODEL_SEPARATION` (use actual confirmation candle for market fills and keep reference/limit fills explicit).
- Completed (2026-05-24): Task 153 `PARTIAL_EXIT_QUANTITY_RATIO_CONTRACT` (interpret pattern partial-exit quantities as position ratios, not absolute BTC units).
- Completed (2026-05-24): Task 152 `PATTERN_SIZING_PROPAGATION_CONTRACT` (propagate pattern quantity override while preserving engine-owned sizing by default).
- Completed (2026-05-24): Task 151 `ENTRY_FILL_EQUITY_AND_CONSERVATIVE_SIZING_SEMANTICS` (prevent same-candle favorable entry equity jumps from fill/close mismatch and make entry sizing conservative).

## Important Blocked Work
- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` remains blocked pending explicit owner approval for live order execution and the live-readiness prerequisites documented in `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`.

## Current Candidates / Follow-ups
- Next explicit task: undecided.
- Follow-up candidate: `LIVE_EXECUTION_KILL_SWITCH_AND_MAX_NOTIONAL_GUARDS` (prerequisite before any future live execution task).
- Follow-up candidate: `LIVE_EXECUTION_SYMBOL_FILTER_AND_STALE_DATA_PRECHECKS` (exchange filter, stale candle, and clock-skew checks before live intent submission).
- Follow-up candidate: `LIVE_EXECUTION_IDEMPOTENCY_AND_RESTART_RECONCILIATION` (durable duplicate-order prevention and restart recovery).
- Follow-up candidate: `LIVE_EXECUTION_CANCEL_REPLACE_AND_PARTIAL_FILL_POLICY` (cancel/replace, timeout, orphan-order, and partial-fill handling).
- Follow-up candidate: `LIVE_EXECUTION_MONITORING_ALERTING_AND_SECRET_POLICY` (alerts, credential storage/rotation, redaction, and operational readiness).
- Follow-up candidate: add visual regression/UI tests for dashboard marker/table rendering once a frontend test harness is assigned.
- Candidate: `PATTERN_STRATEGY_OUTPUT_CONTRACT_DOCUMENTATION_AND_FIXTURE_EXPANSION` (document enriched stdout schema and broaden deterministic fixtures for short-side/no-fill cases).
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema if owner requires richer financial outputs.
- Follow-up candidate: align pattern persistence graph-point cash/position/equity to candle-timed fills for richer dashboard trace fidelity.
- Non-FVG deterministic synthetic entry fixtures for broader pattern backtest determinism.
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
