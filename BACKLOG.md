# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`
- `docs/ledger_archives/backlog_task_101_150.md`
- `docs/ledger_archives/backlog_task_151_200.md`
- `docs/ledger_archives/backlog_task_201_250.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 251-300)

- Completed (2026-05-31): Task 289 `DAILY_BACKTEST_BLOG_TEMPLATE_AND_AGENT_HANDOFF` (created `docs/blog/template.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, and `docs/blog/daily_report_workflow.md` for concise daily Korean quant backtest write-ups, including required placeholders/examples, PR-only metadata, expectancy/cost/result/illusion/representative-trade sections, compact handoff payload rules, reusable agent prompt, and owner-request routing rules for "`[전략명]` daily report" prompts; no backtest execution, strategy implementation, DB schema change, frontend/backend/API change, live trading behavior, or exchange endpoint behavior was added).
- Created (2026-05-31): Task 288 `REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT` (future implementation task to develop a new deterministic BTCUSDT 1m model after Task 287 rejection, using repaired April-20-forward data, at least two principle-first candidate families, repeated in-task implementation/backtest/revision loops, DB persistence under `research.task_id=TASK_288`, realistic fee/spread/slippage cost audits, full 0420+/0520+/0525+ target gates, independent weekly/WFO validation, cost stress, outlier checks, and research-only final status). No implementation or backtest execution was performed in this task-creation step.
- Completed (2026-05-31): Task 287 `REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION` (implemented the locked no-retune repaired-data validation runner, persisted DB runs `1085`-`1159` with `research.task_id=TASK_287`, verified repaired BTCUSDT 1m coverage from `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z` with `55227` continuous candles and `0` duplicate open-time groups, saved `reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`, added Korean failure analysis at `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`, and rejected the primary `T285_R3_CORE_SHORT_ONLY_B2` as `LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY`; full 0420+ return was `-13.0706pct` with `50` trips, pre-owner return was `-17.4283pct`, independent weekly aggregate was `-8.2103pct`, and all 75 persisted runs had `0` formula/summary cost mismatches with non-zero fee/spread/slippage).
- Completed (2026-05-31): Task 286 `BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR` (added a focused market-data audit/repair runner, fetched and upserted `32200` missing closed BTCUSDT 1m candles from Binance public klines, repaired the `2026-04-20T00:00:00Z` through `2026-05-09T23:59:00Z` leading gap and `2026-05-17T15:20:00Z` through `2026-05-19T23:59:00Z` internal gap, verified `55227` continuous closed candles through `2026-05-28T08:26:00Z`, confirmed duplicate open-time count `0`, and saved `reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md`).
- Completed (2026-05-31): Task 285 `REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR` (added an offline configurable multi-window repair runner, focused tests, DB-persisted runs `1001`-`1020` and `1041`-`1052`, and `reports/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`; final status `ROBUSTNESS_REJECTED_RESEARCH_ONLY`; selected diagnostic repair `T285_R3_CORE_SHORT_ONLY_B2` reached independent aggregate `+3.1737pct`, but had only `19` trips, positive windows `60pct`, return without top-three winners `-2.2531pct`, earliest OOS cost domination, and `2x` cost stress `-3.6686pct`; all Task 285 cost formula and summary mismatch counts were `0`).
- Completed (2026-05-30): Task 284 `TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION` (added an offline locked Task 283 robustness runner, focused tests, DB-persisted validation runs `960`-`993`, and `reports/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md`; final status `ROBUSTNESS_REJECTED_RESEARCH_ONLY`; owner replay runs `960`/`961` reproduced `+5.7327pct` and `+3.5337pct` with cost mismatch count `0`, but pre-owner run `962` returned `-2.6638pct`, pre-owner high-slippage stress run `989` returned `-8.6028pct`, endpoint diagnostics were positive in only `15/16` cases, and April-20-forward OOS remains blocked by missing local candles).
- Post-audit (2026-05-30): Rechecked the suspicious-looking Task 284 result after owner challenge. DB readback, in-memory rerun, and event-level PnL/cost recomputation confirmed no detected persistence or fee-accounting mismatch; weakness remains structural: 0520 profit is short-side concentrated, pre-owner replay is cost-dominated, owner windows overlap, and April/May data is incomplete.
- Completed (2026-05-30): Task 283 `PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT` (implemented an offline principle-first BTCUSDT 1m microstructure research runner, factor snapshots, seven deterministic candidates, focused tests, and `reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`; persisted DB runs `917`, `919`-`929`, and `950`-`959`; best candidate `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` passed fixed target-window gates with run `950` at `+5.7327pct`/`62` trips from 2026-05-20 and run `951` at `+3.5337pct` from 2026-05-25, with cost-audit mismatch count `0`; result remains `TARGET_PASSED_RESEARCH_ONLY` because pre-owner run `959` was `-2.6638pct` and April-20-forward OOS is data-blocked).
- Completed (2026-05-30): Task 282 `TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420` (replayed Task 281 run `892` without retuning, persisted DB runs `900`-`909`, verified cost-audit mismatch count `0` for every persisted run, and saved `reports/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md`; local BTCUSDT 1m data starts at 2026-05-10 and has an internal 2026-05-17 to 2026-05-20 candle gap, owner replay reproduced `+5.7295pct`, pre-owner conservative validation failed at `-2.7997pct`, pre-owner high-slippage stress failed at `-8.9497pct`, and final interpretation is `LIKELY_OVERFIT_RESEARCH_ONLY`).
- Completed (2026-05-30): Task 281 `OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH` (implemented an offline deterministic high-activity BTCUSDT 1m owner-window search, persisted DB runs `890`-`894`, verified realistic non-zero fee/spread/slippage costs, and saved `reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`; best passing run `892` reached `+5.7295pct` net return with `62` completed round trips on the 2026-05-20+ window, so it is `PROMISING_RESEARCH_ONLY` pending locked OOS/walk-forward validation).
- Hard-data-constrained research-only (2026-05-29): Task 280 `COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT` (executed repeated in-task deterministic BTCUSDT 1m model batches `batch1`-`batch9`, persisted 576 Task 280 DB runs `296`-`889`, verified non-zero conservative 1m fee/spread/slippage costs, added focused Task 280 tests, and saved `reports/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md`; best combined owner-window candidate reached only Window A `+0.2057pct` and Window B `+0.3001pct` at primary `cash_fraction=0.10`, so no candidate is promoted under current assumptions).
- Completed (2026-05-29): Task 279 `STRATEGY_ROBUSTNESS_VALIDATION_MATRIX` (persisted 135 BTCUSDT 1m validation runs, IDs 159-295, across owner windows, sizing ladder, endpoint trims, OOS splits, cost stress, and one-candle entry-delay diagnostics; generated `reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`; no candidate passed the robustness gates, and Task 278 remains `DIAGNOSTIC_ONLY`).
- Completed (2026-05-29): Task 278 `LOW_TURNOVER_1M_EDGE_DEVELOPMENT` (audited Task 277's weak edge/cost profile, persisted runs 151-158 for inverse-trend hold sizing diagnostics, selected research-only `T278_V001_INVERSE_TREND_HOLD_CF_0P75` with runs 155/156 at +3.1738pct and +3.4440pct, verified conservative 1m fees/spread/slippage, and documented the strategy in `reports/TASK_278_LOW_TURNOVER_1M_EDGE_DEVELOPMENT.md`).
- Completed (2026-05-29): Task 277 `ADAPTIVE_1M_STRATEGY_SEARCH_TARGET_5PCT` (attempted 18 deterministic BTCUSDT 1m candidate variants, persisted target-qualification runs 115-148 and zero-cost diagnostics 149-150, implemented `SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL`, verified conservative 1m fees/spread/slippage on qualifying runs, and wrote `reports/TASK_277_ADAPTIVE_1M_STRATEGY_SEARCH.md`; no candidate met +5% on both owner windows, so results remain research-only).
- Completed (2026-05-29): Task 276 `LIQUIDITY_SWEEP_DISPLACEMENT_FVG_OB_BACKTEST` (`LIQUIDITY_SWEEP_REVERSAL` now supports stop-liquidity sweep, reclaim/displacement, FVG/OB confluence, retest entry, sweep-extreme stop, cost-aware RR gate, CLI wiring, and saved baseline run 114 for 1m BTCUSDT from 2026-05-20; run 114 produced 0 fills, with 11 cost-aware rejections and 9 unfilled retests).
- Completed (2026-05-28): Task 275 `EXPANDED_FVG_OB_MTF_BACKTEST_MATRIX` (executed initial staged Batch A/E saved runs 110-113 and reused exact Task 273/274 references for matching cells; remaining deeper Batch C/D/F/G sweeps should be a new follow-up if needed).
- Completed (2026-05-28): Task 274 `FVG_ORDER_BLOCK_MULTI_TIMEFRAME_BACKTEST_SWEEP` (saved OB MTF/FVG runs 103, 105-109; historical-detector FVG OB confluence timed out after 900 seconds).
- Completed (2026-05-28): Task 273 `ORDER_BLOCK_BACKTEST_CANDIDATE_SWEEP` (saved five practical `ORDER_BLOCK` candidate runs, IDs 98-102, comparing baseline, volume 1.5x, 15m MTF, relaxed cost-aware RR, and 61.8% retest wait-20 variants).
- Created (2026-05-28): Task 272 `ORDER_BLOCK_COST_AWARE_RR_ENTRY_GUARD` (future implementation task to make `ORDER_BLOCK` skip entries when fee/spread/slippage-adjusted reward/risk is insufficient).
- Completed (2026-05-28): Task 271 `ORDER_BLOCK_PREVIOUS_CANDLE_RISK_REWARD_EXIT` (`ORDER_BLOCK` now defaults to previous-candle high/low stop and symmetric 1R current-close target for confirmation-close entries, with `--ob-risk-exit-mode zone_structural_2r` preserving the prior zone/structural mode).
- Completed (2026-05-28): Task 270 `ORDER_BLOCK_VOLUME_COST_AND_MTF_FILTERS` (added optional Order Block detector/entry volume controls, default realistic costs for `ORDER_BLOCK`, and opt-in same-direction MTF OB filtering using completed resampled base candles).
- Completed (2026-05-28): Task 269 `PROJECT_REFACTOR_AND_LEDGER_RECONCILIATION` (split the FVG OB confluence implementation into default local mode and explicit historical compatibility mode, then reconciled `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`).
- Completed (2026-05-28): Task 268 `FVG_CLOSE_VOLUME_DEFAULT_THRESHOLDS` (changed FVG close-volume owner/default minimum ratio to 2.0x and low-volume diagnostic threshold to 0.5x while preserving explicit CLI overrides).
- Completed (2026-05-28): Task 267 `FVG_ENTRY_LOCAL_ORDER_BLOCK_FILTER` (changed default FVG OB confluence to local previous/current entry-candle validation and avoided repeated historical `detect_order_blocks()` calls unless compatibility mode is explicitly selected).
- Completed (2026-05-28): Task 266 `FVG_ORDER_BLOCK_CONFLUENCE_ENTRY_FILTER` (added a default-off FVG entry gate that requires same-direction Order Block confluence, with CLI flags, metadata, baseline/channel support, and tests).
- Created (2026-05-28): Task 265 `HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT` (future implementation task to backfill Binance `1h`/`4h` candles and wire completed higher-timeframe context into strategy backtests).
- Completed (2026-05-28): Task 264 `FVG_V2_CHANNEL_PRE_RETEST_CANDLE_STRUCTURE_STOP` (changed FVG v2 channel stops to the immediately previous retest candle low for LONG and high for SHORT, with invalid-stop skip metadata).
- Completed (2026-05-28): Task 263 `BACKTEST_CASH_CURRENCY_DENOMINATION_GUARDRAIL` (added explicit cash denomination metadata and manual KRW-to-USDT quote-cash conversion for strategy backtests; follow-up set default cash input to KRW with `krw_per_usdt=1500`).
- Completed (2026-05-28): Task 262 `FVG_V2_CLOSE_VOLUME_FILTER_ALL_ENTRY_SIDES` (applies the close-volume entry filter to both LONG and SHORT FVG v2 channel entries with all-side metadata).
- Completed (2026-05-28): Task 261 `FVG_V2_CLOSE_VOLUME_ENTRY_FILTER` (added a default owner-profile close-volume entry filter that skips low-volume completed-candle FVG v2 channel LONG entries with explicit metadata).
- Completed (2026-05-28): Task 260 `FVG_V2_CHANNEL_OWNER_PROFILE_DEFAULTS` (made the owner-approved FVG v2 channel settings the default Fair Value Gap strategy-backtest profile with explicit override flags and metadata).
- Completed (2026-05-28): Task 259 `FVG_V2_CHANNEL_CLOSE_BASED_RETEST_AND_TRADE_BOUNDED_OVERLAY` (changed channel retests to close-based confirmation and clipped frontend overlay lines to the saved trade/retest point).
- Completed (2026-05-28): Task 258 `FRONTEND_FVG_UPTREND_CHANNEL_L1_H1_L2_POINTS` (renders saved uptrend FVG channel construction points as `L1`, `H1`, and `L2` on the dashboard overlay).
- Completed (2026-05-28): Task 257 `COST_AWARE_TAKE_PROFIT_ENTRY_BLOCK` (changed FVG v2 channel targets to one channel-width projection from entry price, updated LONG/SHORT channel stops, and blocked cost-negative projected targets before entry).
- Completed (2026-05-28): Task 256 `FVG_V2_CHANNEL_BOUNDARY_DIRECTION_RULES` (changed FVG v2 channel retest mapping to upper-boundary LONG and lower-boundary SHORT, added downtrend channel geometry support, direction-rule metadata, tests, and API/frontend type exposure).
- Completed (2026-05-28): Task 255 `FVG_INVERSE_DIRECTION_RESEARCH_MODE` (added explicit default-off FVG contrarian/inverse buy-sell direction research mode, metadata, tests, and channel-mode unsupported skip).
- Completed (2026-05-28): Task 254 `FVG_V2_MULTI_CHANNEL_OVERLAY_AND_SCAN_SEMANTICS_REVIEW` (added multi-channel bounded frontend overlays, explicit standalone channel scan opt-in, channel source metadata, and unfilled-channel dedupe correction).
- Completed (2026-05-28): Task 253 `BACKTEST_RUN_STARTING_CASH_AND_CHANNEL_OVERLAY_VISIBILITY_FIX` (exposed configured starting cash in list/frontend display and made FVG channel overlay parsing robust to top-level, nested, and graph-point trade metadata).
- Completed (2026-05-28): Task 252 `FVG_V2_CHANNEL_TRADE_EACH_NEW_CHANNEL` (added stable channel identity/dedupe and visible-prefix channel scanning so each distinct newly visible FVG v2 channel can generate its own trade candidate).
- Completed (2026-05-28): Task 251 `FVG_V2_CHANNEL_RETEST_STRUCTURE_STOP` (updated LONG channel retest stops to use the retest structure low instead of the lower channel line, while LONG target remains the upper channel line).

## Important Blocked Work

- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` remains blocked pending explicit owner approval for live order execution and the live-readiness prerequisites documented in `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`.

## Current Candidates / Follow-ups

- Follow-up candidate: implement Task 288 `REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT` if the owner assigns it; it must predeclare model families/windows/costs, persist decision-driving runs, enforce minimum trade-count/cost-stress gates, and keep any passing result research-only pending future unseen data.
- Follow-up candidate: create a future report-payload exporter task if the owner wants saved backtest runs to automatically emit payloads matching `docs/blog/backtest_report_data_rules.md` and route directly through `docs/blog/daily_report_workflow.md`.
- Follow-up candidate: create a locked out-of-sample/walk-forward validation task before any promotion claim from Task 278, with untouched validation windows, unchanged realistic costs, and predeclared acceptance criteria.
- Follow-up candidate: create a short-bias regime-selector task so the Task 278 inverse-trend hold idea can enter only when completed-candle trend/regime evidence supports it, instead of relying on hindsight window selection.
- Follow-up candidate: create an LSR sensitivity task to run the remaining predeclared `LIQUIDITY_SWEEP_REVERSAL` comparison variants: MTF 15m, MTF 15m/1h, stricter 2.0x volume, both FVG+OB, FVG-only, OB-only, and zero-cost diagnostic against run 114.
- Follow-up candidate: implement Task 265 `HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT` if the owner assigns it.
- Follow-up candidate: create a continuation task for remaining Task 275 Batch C/D/F/G variants only if the owner wants deeper volume, cost, FVG volume/channel sensitivity, and final best-candidate confirmation sweeps.
- Follow-up candidate: inspect saved runs 103, 107, 109, and 113 in the dashboard or API before expanding the sweep further.
- Follow-up candidate: implement Task 272 `ORDER_BLOCK_COST_AWARE_RR_ENTRY_GUARD` to enforce fee-adjusted reward/risk before `ORDER_BLOCK` entries.
- Follow-up candidate: compare `ORDER_BLOCK` default `previous_candle_1r` exits against `--ob-risk-exit-mode zone_structural_2r` on the owner-selected dataset.
- Follow-up candidate: run `ORDER_BLOCK` backtests with `--enable-ob-entry-volume-filter` and/or `--enable-ob-mtf-filter` to compare trade count, skips, costs, and net results against the default Order Block run.
- Follow-up candidate: if the owner wants DB-backed higher-timeframe context instead of resampled base candles, implement Task 265 `HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT`.
- Follow-up candidate: run the owner FAIR_VALUE_GAP strategy command with `--fvg-require-order-block-confluence` and compare runtime, filled entries, `FVG_ORDER_BLOCK_CONFLUENCE_MISSING` skips, and net results against the Task 266 historical-detector compatibility mode.
- Follow-up candidate: run the owner FVG v2 channel command with default KRW/1500 cash conversion and inspect `LOW_CLOSE_VOLUME_ENTRY_FILTER`, `COST_INFEASIBLE_TAKE_PROFIT`, projected channel-width targets, total costs, and equity behavior.
- Follow-up candidate: create `FVG_V2_MULTI_TIMEFRAME_ENTRY_ALIGNMENT` if the owner wants 1m entries confirmed by completed 15m and 1h FVG/channel timing windows.
- Follow-up candidate: run the owner 2026-05-20+ FVG v2 channel command and inspect trade count, channel IDs, long/short side distribution, cost breakdowns, and equity curve under the Task 256 channel-boundary direction rule.
- Follow-up candidate: run normal versus `--fvg-inverse-direction` FVG backtests on the approved 2026-05-20+ dataset and compare gross PnL, total costs, trade count, and equity curve.
- Follow-up candidate: re-run the approved 2026-05-20+ FVG v2 channel backtests in FVG-event-only mode and with `--fvg-channel-standalone-scan`, then compare overlays, channel IDs, duplicate/no-fill skips, trade count, cost metadata, and equity behavior.
- Follow-up candidate: `FVG_V2_CHANNEL_SHORT_RETEST_STRUCTURE_HIGH_STOP` (if owner wants SHORT stops to mirror LONG by using the retest structure high instead of the upper channel line).
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
- Completed (2026-05-28): Created `docs/ledger_archives/backlog_task_201_250.md` and reduced root backlog to the Tasks 251-300 recent window when Task 251 was created.
