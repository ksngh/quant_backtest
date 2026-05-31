# Project Status

## Current Overall Phase
Phase 362: Task 289 daily backtest blog template and handoff completed (2026-05-31).

## Current Step
Completed Task 289 `DAILY_BACKTEST_BLOG_TEMPLATE_AND_AGENT_HANDOFF`: created the daily Korean backtest report template, compact result data-saving rules, reusable agent handoff prompt, and owner-request workflow rules.

## Current Goal
Use the new `docs/blog/` workflow for future strategy-specific daily backtest write-ups; keep model development and backtest execution under separately assigned tasks.

## Current Active Task
No active implementation task. Last completed documentation task: Task 289 `DAILY_BACKTEST_BLOG_TEMPLATE_AND_AGENT_HANDOFF`.

## Last Completed Step (Short)
Created `docs/blog/template.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, and `docs/blog/daily_report_workflow.md`; verified the template excludes the forbidden metadata labels and banned expressions.

## Recommended Next Step
Recommended next step: wait for owner assignment. For future "`[전략명]` daily report" requests, follow `docs/blog/daily_report_workflow.md`; if no saved payload/run exists, create or assign the relevant backtest task first.

## Current Blockers (Short)
- Task 279 note: no tested BTCUSDT 1m candidate passed the robustness matrix; Task 278 run `155`/`156` remains a directional diagnostic only, and all Task 279 candidates remain `DIAGNOSTIC_ONLY`.
- Task 286 resolved the BTCUSDT 1m data blocker: local closed candles now cover `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z` with `55227` continuous rows and `0` duplicate open times.
- Task 282 note: Task 281 run `892` reproduces on the owner window but fails pre-owner validation and stress validation; keep it `LIKELY_OVERFIT_RESEARCH_ONLY`.
- Task 287 note: repaired-data locked validation persisted runs `1085`-`1159`; coverage guard passed with `55227` continuous BTCUSDT 1m closed candles from `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z`, `0` gaps, and `0` duplicate open-time groups. Primary `T285_R3_CORE_SHORT_ONLY_B2` failed full 0420+ return at `-13.0706pct`, pre-owner at `-17.4283pct`, independent weekly aggregate at `-8.2103pct`, 2x cost full at `-27.9587pct`, and 3x cost full at `-40.2970pct`. All 75 Task 287 runs had non-zero fee/spread/slippage and `0` formula/summary cost mismatches.
- Task 287 documentation note: the rejected strategy and failure analysis are documented in Korean at `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`.
- Task 288 note: new model-development task is created at `tasks/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md`; it has not been implemented or backtested yet.
- Task 289 note: daily blog template and agent handoff workflow is complete at `docs/blog/template.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, and `docs/blog/daily_report_workflow.md`.
- Task 283 note: target fixed-window gates passed historically, but Task 287 repaired-data replay rejected the locked comparator: full 0420+ return `-15.0301pct`, pre-owner `-18.8410pct`, and independent weekly aggregate `-10.0735pct`; keep it research-only.
- Task 284 note: locked validation rejected robustness despite owner-window replay passing; Task 287 repaired-data rerun confirmed the underlying Task 283/284 candidate remains rejected. Historical Task 284 cost audit mismatch count was `0` across runs `960`-`993`.
- Task 284 post-audit note: owner questioned whether the result was anomalous; read-only DB readback and in-memory reruns confirmed Task 283/284 paired runs match exactly, event-level short/long PnL formulas are consistent, and cost summaries match trade-level costs. The suspicious-looking result is driven by short-side concentration after 2026-05-20, cost-dominated pre-owner performance, overlapping owner windows, and missing April/May data, not by a detected persistence or fee-accounting mismatch.
- Task 285 note: multi-window repair selected `T285_R3_CORE_SHORT_ONLY_B2` as the best repaired diagnostic, but Task 287 repaired-data locked validation rejected it on full 0420+, pre-owner, independent weekly, outlier, and cost-stress gates. Cost formula and summary mismatch counts were `0` for all Task 285 and Task 287 runs.
- Task 280 hard data constraint: after 576 persisted Task 280 runs, the best combined owner-window result is only Window A `+0.2057pct` and Window B `+0.3001pct` at primary `cash_fraction=0.10`; a perfect-hindsight close-to-close switching diagnostic for Window B is approximately `+1.9146pct` at 10pct sizing after an approximate 38bps round-trip cost, below the owner +3pct threshold before implementable signal constraints.
- Task 279 note: the planned 154-run matrix persisted 135 runs before stopping the optional Order Block expansion because that branch was already strongly dominated, very slow, and fee-dominated; SRLBR, FVG inverse, and LSR validation groups were persisted broadly.
- Task 276 note: the owner-requested single baseline has 0 fills; broader LSR grid variants were not run in this task because the latest owner request was to run one 1m backtest from 2026-05-20 onward.
- Task 276 note: native DB-backed 1h/4h context is still Task 265; Task 276 used completed base-candle context only.
- Task 277 note: repeated tuning against the fixed 2026-05-20+ and 2026-05-25+ windows is data-snooping-prone; Task 277 is complete but results remain research-only until a future OOS/WFO task.
- Task 278 note: the selected `cash_fraction=0.75` simulated spot-short candidate exceeded +3pct on both fixed windows, but it was chosen after observing those windows and remains research-only/data-snooping-prone until a locked OOS/WFO task.
- Task 274/275 note: FVG historical-detector OB confluence timed out after 900 seconds on the 2026-05-25+ owner profile and should not be expanded without narrowing the range or optimizing that path.
- Live trading remains blocked pending explicit owner approval for Task 138, credential policy, allowed endpoint policy, and kill-switch design.
- Task 170 audit confirms live execution also needs max-notional guards, symbol filter checks, stale-data checks, duplicate-order idempotency, restart reconciliation, cancel/replace and partial-fill policy, monitoring/alerting, and secret-management policy before Task 138 can be unblocked.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Backend FastAPI route tests are not runnable in the current Python environment because `fastapi` is not installed; FastAPI-independent service/repository tests and frontend checks passed.
- In-app browser automation could not be used in this session because the required Node REPL browser-control tool was not exposed; local Next server HTML response was verified with `curl`.
- Full browser visual verification for the channel overlay was not run in this task because the local API was not reachable from this shell; frontend type/helper tests passed.
- `npm --prefix frontend run test` is unavailable because `frontend/package.json` has no `test` script; `npm --prefix frontend run test:helpers` passed.

## Current Safety Boundary
- No live trading.
- No real Binance order execution.
- No API keys in code.
- No committed `.env` files.
- No signed exchange requests.
- No order/account endpoint usage.
- Testnet signed order request code exists only in the explicit execution client and is covered by fake-HTTP tests; live order execution remains disabled.

## Focused Context Pointers
- Historical/completed ledger: `PROJECT_HISTORY.md`
- Future/deferred candidate work: `BACKLOG.md`
- Backend area status: `backend/STATUS.md`
- Frontend area status: `frontend/STATUS.md`
- Last completed task: `tasks/TASK_258_FRONTEND_FVG_UPTREND_CHANNEL_L1_H1_L2_POINTS.md`
- Last completed task: `tasks/TASK_259_FVG_V2_CHANNEL_CLOSE_BASED_RETEST_AND_TRADE_BOUNDED_OVERLAY.md`
- Last completed task: `tasks/TASK_260_FVG_V2_CHANNEL_OWNER_PROFILE_DEFAULTS.md`
- Last completed task: `tasks/TASK_261_FVG_V2_CLOSE_VOLUME_ENTRY_FILTER.md`
- Last completed task: `tasks/TASK_262_FVG_V2_CLOSE_VOLUME_FILTER_ALL_ENTRY_SIDES.md`
- Last completed task: `tasks/TASK_263_BACKTEST_CASH_CURRENCY_DENOMINATION_GUARDRAIL.md`
- Last completed task: `tasks/TASK_264_FVG_V2_CHANNEL_PRE_RETEST_CANDLE_STRUCTURE_STOP.md`
- Last completed task: `tasks/TASK_266_FVG_ORDER_BLOCK_CONFLUENCE_ENTRY_FILTER.md`
- Last completed task: `tasks/TASK_267_FVG_ENTRY_LOCAL_ORDER_BLOCK_FILTER.md`
- Last completed task: `tasks/TASK_268_FVG_CLOSE_VOLUME_DEFAULT_THRESHOLDS.md`
- Last completed task: `tasks/TASK_269_PROJECT_REFACTOR_AND_LEDGER_RECONCILIATION.md`
- Last completed task: `tasks/TASK_270_ORDER_BLOCK_VOLUME_COST_AND_MTF_FILTERS.md`
- Last completed task: `tasks/TASK_271_ORDER_BLOCK_PREVIOUS_CANDLE_RISK_REWARD_EXIT.md`
- Last completed task: `tasks/TASK_273_ORDER_BLOCK_BACKTEST_CANDIDATE_SWEEP.md`
- Last completed task: `tasks/TASK_274_FVG_ORDER_BLOCK_MULTI_TIMEFRAME_BACKTEST_SWEEP.md`
- Last completed task: `tasks/TASK_275_EXPANDED_FVG_OB_MTF_BACKTEST_MATRIX.md`
- Last completed task: `tasks/TASK_276_LIQUIDITY_SWEEP_DISPLACEMENT_FVG_OB_BACKTEST.md`
- Last completed task: `tasks/TASK_277_ADAPTIVE_1M_STRATEGY_SEARCH_TARGET_5PCT.md`
- Last completed task: `tasks/TASK_278_LOW_TURNOVER_1M_EDGE_DEVELOPMENT.md`
- Last completed task: `tasks/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`
- Last completed task: `tasks/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md`
- Last completed task: `tasks/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`
- Last completed task: `tasks/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md`
- Last completed task: `tasks/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`
- Last completed task: `tasks/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md`
- Last completed task: `tasks/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`
- Last completed task: `tasks/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md`
- Last completed task: `tasks/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`
- Last completed task: `tasks/TASK_289_DAILY_BACKTEST_BLOG_TEMPLATE_AND_AGENT_HANDOFF.md`
- Current created task: `tasks/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md`
- Current created task: `tasks/TASK_265_HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT.md`
- Current created task: `tasks/TASK_272_ORDER_BLOCK_COST_AWARE_RR_ENTRY_GUARD.md`
