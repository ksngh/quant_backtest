# Project Status

## Current Overall Phase
Phase 392: Daily report interpretation/style workflow revision completed (2026-06-01).

## Current Step
Completed Task 303 `DAILY_REPORT_INTERPRETATION_STYLE_WORKFLOW_REVISION` by updating reusable daily-report template, style, workflow, handoff prompt, data rules, and image prompt guidance for interpretation-centered Korean reports.

## Current Goal
Wait for the owner to assign the next bounded task. Recommended candidates are a separate `5m` candle backfill execution task for missing momentum comparison coverage, locked OOS/WFO diagnostics, or another explicitly assigned report workflow task.

## Current Active Task
None. Task 303 is completed; no next task has been started.

## Last Completed Step (Short)
Completed Task 303. Daily-report docs now require interpretation-centered Korean report writing, avoid absent pattern/filter/artifact mentions by default, move unavailable interval coverage such as missing `5m` local candles to limitations or next improvements, enrich representative trade descriptions with available market context, and replace generic final conclusions with an interpretation section covering experiment intent, observed result, likely causes, and next improvements. No report artifact rewrite, backtest, tuning/search, strategy/code change, candle backfill, DB mutation, image generation, frontend/backend/API change, live trading behavior, exchange endpoint behavior, secret, or `.env` change was performed.

## Recommended Next Step
Recommended next step: assign a separate bounded task such as `5m` candle backfill for missing momentum comparison coverage, locked OOS/WFO diagnostics, or a future reusable report-payload/image exporter task if desired.

## Current Blockers (Short)
- Task 279 note: no tested BTCUSDT 1m candidate passed the robustness matrix; Task 278 run `155`/`156` remains a directional diagnostic only, and all Task 279 candidates remain `DIAGNOSTIC_ONLY`.
- Task 286 resolved the BTCUSDT 1m data blocker: local closed candles now cover `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z` with `55227` continuous rows and `0` duplicate open times.
- Task 282 note: Task 281 run `892` reproduces on the owner window but fails pre-owner validation and stress validation; keep it `LIKELY_OVERFIT_RESEARCH_ONLY`.
- Task 287 note: repaired-data locked validation persisted runs `1085`-`1159`; coverage guard passed with `55227` continuous BTCUSDT 1m closed candles from `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z`, `0` gaps, and `0` duplicate open-time groups. Primary `T285_R3_CORE_SHORT_ONLY_B2` failed full 0420+ return at `-13.0706pct`, pre-owner at `-17.4283pct`, independent weekly aggregate at `-8.2103pct`, 2x cost full at `-27.9587pct`, and 3x cost full at `-40.2970pct`. All 75 Task 287 runs had non-zero fee/spread/slippage and `0` formula/summary cost mismatches.
- Task 287 documentation note: the rejected strategy and failure analysis are documented in Korean at `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`.
- Task 288 note: new model-development task is created at `tasks/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md`; it has not been implemented or backtested yet.
- Task 289 note: daily blog template and agent handoff workflow is complete at `docs/blog/template.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, and `docs/blog/daily_report_workflow.md`.
- Task 290 note: payload-saving task is complete. It resolved latest completed persisted run `1159` (`T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`, `pre_owner_0420_0519`, `high_slippage_stress`) as the source, saved `reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json`, generated `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png` and `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png`, verified JSON/required keys/forbidden fields/non-empty PNGs, and did not run a new backtest or mutate DB records.
- Task 291 note: artifact-layout task is complete. It updated `docs/blog/backtest_report_data_rules.md`, `docs/blog/daily_report_workflow.md`, `docs/blog/agent_handoff_prompt.md`, and `docs/blog/template.md`; migrated/regenerated the Task 290 artifact to `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/`; generated `equity_curve.png`, `drawdown.png`, `price_with_trades.png`, `trade_pnl_distribution.png`, `cost_breakdown.png`, `side_attribution.png`, and `exit_reason_attribution.png`; removed legacy `reports/blog_payloads/images/`; verified JSON, filename-only image refs, forbidden field absence, non-empty PNGs, and `git diff --check`; no new backtest or DB mutation was performed.
- Task 292 note: report-facing naming task is complete. The current report artifact now uses `Priority Ensemble Activity Scout V1` title fields, `reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/`, and `priority_ensemble_activity_scout_v1_*` image filenames. The payload has no `T281`, `T287`, `TASK`, `Task`, `candidate_id`, or `run_id` markers; the old `t281...` folder was removed. No new backtest or DB mutation was performed.
- Task 293 note: daily report image asset rules v2 is complete. `docs/blog/backtest_report_data_rules.md`, `docs/blog/daily_report_workflow.md`, `docs/blog/agent_handoff_prompt.md`, `docs/blog/template.md`, and `docs/blog/image_generation_prompt.md` now define the owner's new future contract: `daily_report/YYYY-MM-DD-[strategy-slug]/images/`, required fixed images, combined equity/drawdown summary chart, cost-impact chart without `cost stress` chart labels, representative candlestick win/loss trade charts, variant image naming, image-plan-before-generation, and final checks. No image generation, artifact migration, backtest execution, or DB mutation was performed.
- Task 294 note: colocated daily report payload/image regeneration is complete. The docs now define the corrected payload/images-only workflow with no default report markdown, image-plan files, or `images/` subdirectory, and the regenerated `Priority Ensemble Activity Scout V1` artifact is stored at `reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/` with `payload.json` and colocated PNGs. Report-facing total return is corrected to `-35.5861%` from saved final equity/net PnL. No new backtest or DB mutation was performed.
- Task 295 note: report draft and pre-backtest strategy documentation rules are complete. `AGENTS.md` now requires relevant `docs/strategy/*.md` after the assigned task file and before any strategy/model/backtest implementation, tuning, validation, or reportable research run. `docs/strategy/README.md` and `docs/strategy/STRATEGY_TEMPLATE.md` define the strategy-document workflow. Blog/report docs now require full workflows to generate `payload.json`, colocated PNGs, and `report-ko.md` in the same folder.
- Task 296 note: documentation-only task is complete. `docs/strategy/lookback_return_momentum_v1.md` now documents the pure close-to-close momentum baseline, signal formula, long/short/no-trade rules, insufficient-lookback behavior, flat-only/no-reverse entry rule, stop/target/time exits, same-candle stop-first priority, fixed v1 `1R = entry_price * 0.002`, 1m/5m/15m defaults, owner-listed exclusions, and future tests. Implementation/backtest work still requires a separate task.
- Task 297 note: implementation task is complete. `LOOKBACK_RETURN_MOMENTUM` is implemented as an offline research strategy using only completed close-to-close return, flat-only/no-reverse entries, fixed percentage `1R`, side-specific stop/target, time exit, stop-first same-candle ambiguity handling, CLI parameter overrides, and 1m/5m/15m defaults. Focused tests passed (`13 passed`). Broader `pytest tests/strategies tests/backtesting` showed `613 passed, 2 failed`; the failures are existing `FAIR_VALUE_GAP` CLI expectation mismatches around owner-profile defaults and were not changed in Task 297.
- Task 298 note: implementation is complete. `quant_bitcoin.market_data` public Binance candle downloader/backfill now supports `1h` and `1d` in the REST backfill path, while preserving existing minute intervals and keeping WebSocket minute-only validation unchanged. Focused tests passed (`64 passed`), full market-data tests passed (`120 passed`), and `git diff --check` passed. No real DB backfill execution, DB mutation, strategy/backtest execution, report/image/payload generation, live trading behavior, exchange order/account/private endpoint behavior, secrets, or `.env` changes were added.
- Task 299 note: validation is complete. `BTCUSDT` `1m` and `15m` local candles are available and continuous for the bounded validation window; `5m` has `0` local closed candles and was skipped. Saved runs `1160` and `1161` under `research.task_id=TASK_299`; `1m` returned `-37.9957pct` over `1285` completed trades and `15m` returned `-6.8468pct` over `169` completed trades under `conservative_crypto_1m`. Both are cost-dominated research-only diagnostics, documented at `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`.
- Task 300 note: completed documentation workflow wiring. Active daily-report rules now require reading `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md` before drafting `report-ko.md`, while preserving `docs/blog/daily_report_workflow.md`, `docs/blog/image_generation_prompt.md`, `docs/blog/backtest_report_data_rules.md`, and `docs/blog/agent_handoff_prompt.md` as workflow/image/data/handoff sources. No report, payload, image, backtest, DB mutation, strategy/code change, live trading behavior, exchange endpoint behavior, secret, or `.env` change was added.
- Task 301 note: completed report-generation task `tasks/TASK_301_LOOKBACK_RETURN_MOMENTUM_DAILY_REPORT_GENERATION.md`. The colocated artifact is stored at `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/` with `payload.json`, `report-ko.md`, `summary_equity_curve.png`, `cost_impact.png`, `representative_win_trade.png`, and `representative_loss_trade.png`. The artifact uses same-folder image references, filename-only payload image references, no internal run/task identifiers, and no `images/` subfolder. No new backtest, parameter tuning/search, strategy/code change, candle backfill, saved-run DB mutation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.
- Task 302 note: completed report copy/readability revision task `tasks/TASK_302_LOOKBACK_RETURN_MOMENTUM_REPORT_COPY_READABILITY_REVISION.md`. Revised `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md` to replace vague "성과가 약하다" phrasing with concrete saved-result descriptions, use compact tables for dense metrics, remove awkward English micro-headings, and keep same-folder image references. Updated `payload.json` only for the matching cost-impact interpretation sentence. No image generation, backtest, parameter tuning/search, strategy/code change, candle backfill, saved-run DB mutation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.
- Task 303 note: created daily-report interpretation/style workflow revision task `tasks/TASK_303_DAILY_REPORT_INTERPRETATION_STYLE_WORKFLOW_REVISION.md`. The task is not implemented yet and should update daily-report docs/prompts/workflow so future Korean reports avoid awkward wording, omit absent pattern/filter/artifact mentions by default, enrich representative trade examples with available context, and make interpretation sections synthesize experiment intent, observed result, concrete causes, and next improvements.
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
- Last completed task: `tasks/TASK_290_SAVE_RECENT_BACKTEST_REPORT_PAYLOAD.md`
- Last completed task: `tasks/TASK_291_BLOG_PAYLOAD_ARTIFACT_LAYOUT_AND_MULTI_IMAGE_RULES.md`
- Last completed task: `tasks/TASK_292_REPORT_FACING_STRATEGY_VERSION_NAMING.md`
- Last completed task: `tasks/TASK_293_DAILY_REPORT_IMAGE_ASSET_RULES_V2.md`
- Last completed task: `tasks/TASK_294_COLOCATED_DAILY_REPORT_PAYLOAD_IMAGE_REGENERATION.md`
- Last completed task: `tasks/TASK_295_REPORT_DRAFT_AND_PRE_BACKTEST_STRATEGY_DOC_RULES.md`
- Last completed task: `tasks/TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC.md`
- Last completed task: `tasks/TASK_297_LOOKBACK_RETURN_MOMENTUM_IMPLEMENTATION.md`
- Last completed task: `tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md`
- Last completed task: `tasks/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`
- Last completed task: `tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md`
- Last completed task: `tasks/TASK_301_LOOKBACK_RETURN_MOMENTUM_DAILY_REPORT_GENERATION.md`
- Last completed task: `tasks/TASK_302_LOOKBACK_RETURN_MOMENTUM_REPORT_COPY_READABILITY_REVISION.md`
- Last completed task: `tasks/TASK_303_DAILY_REPORT_INTERPRETATION_STYLE_WORKFLOW_REVISION.md`
- Current created task: `tasks/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md`
- Current created task: `tasks/TASK_265_HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT.md`
- Current created task: `tasks/TASK_272_ORDER_BLOCK_COST_AWARE_RR_ENTRY_GUARD.md`
