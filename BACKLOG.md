# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`
- `docs/ledger_archives/backlog_task_101_150.md`
- `docs/ledger_archives/backlog_task_151_200.md`
- `docs/ledger_archives/backlog_task_201_250.md`
- `docs/ledger_archives/backlog_task_251_300.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 301-350)

- Completed (2026-05-31): Task 301 `LOOKBACK_RETURN_MOMENTUM_DAILY_REPORT_GENERATION` generated a publish-ready Korean daily report from the saved `LOOKBACK_RETURN_MOMENTUM` validation results. The colocated artifact is stored at `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/` with `payload.json`, `report-ko.md`, `summary_equity_curve.png`, `cost_impact.png`, `representative_win_trade.png`, and `representative_loss_trade.png`. The report states that `1m` and `15m` were negative and cost-dominated, that `5m` was skipped because local closed candles were missing, and that results are research-only. No new backtest execution, parameter tuning/search, strategy/code change, candle backfill, saved-run DB mutation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.
- Completed (2026-05-31): Task 302 `LOOKBACK_RETURN_MOMENTUM_REPORT_COPY_READABILITY_REVISION` revised the existing `Lookback Return Momentum V1` report under `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/`. `report-ko.md` now replaces vague "성과가 약하다" phrasing with concrete saved-result descriptions, uses compact tables for dense metrics, removes awkward English micro-headings, and keeps same-folder image references. `payload.json` was updated only for the matching cost-impact interpretation sentence. No new backtest execution, parameter tuning/search, strategy/code change, candle backfill, saved-run DB mutation, image generation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.
- Completed (2026-06-01): Task 303 `DAILY_REPORT_INTERPRETATION_STYLE_WORKFLOW_REVISION` updated the reusable daily-report template, style guide, workflow, agent handoff prompt, payload data rules, and image prompt so future Korean reports use interpretation-centered structure and natural wording. The docs now tell report writers to omit absent pattern/filter/artifact mentions by default, move unavailable interval coverage such as missing `5m` local candles to limitations or next improvements, enrich representative trade descriptions with available context, and replace generic final conclusions with an interpretation section that covers experiment intent, observed result, likely causes, and next improvements. No report artifact rewrite, backtest execution, parameter tuning/search, strategy/code change, candle backfill, DB mutation, image generation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.

## Important Blocked Work

- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` remains blocked pending explicit owner approval for live order execution and the live-readiness prerequisites documented in `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`.

## Current Candidates / Follow-ups

- Follow-up candidate: create a separate bounded data-backfill execution task if the owner wants Codex to populate PostgreSQL with actual `1h` and `1d` candles after Task 298's code support.
- Follow-up candidate: create a separate bounded `BTCUSDT` `5m` candle backfill execution task if the owner wants the missing `5m` momentum validation interval populated.
- Follow-up candidate: create a separate locked OOS/WFO diagnostic task before making any further claim about `LOOKBACK_RETURN_MOMENTUM`; Task 299 results are cost-dominated and research-only.
- Follow-up candidate: implement Task 288 `REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT` if the owner assigns it; it must predeclare model families/windows/costs, persist decision-driving runs, enforce minimum trade-count/cost-stress gates, and keep any passing result research-only pending future unseen data.
- Follow-up candidate: create a future reusable report-payload/image exporter task if the owner wants saved backtest runs to automatically emit colocated `payload.json` and required PNGs without report markdown, image-plan files, or an `images/` subdirectory.
- Follow-up candidate: implement Task 265 `HIGHER_TIMEFRAME_1H_4H_BACKFILL_AND_STRATEGY_CONTEXT` if the owner assigns it.
- Follow-up candidate: implement Task 272 `ORDER_BLOCK_COST_AWARE_RR_ENTRY_GUARD` to enforce fee-adjusted reward/risk before `ORDER_BLOCK` entries.
- Follow-up candidate: `LIVE_EXECUTION_KILL_SWITCH_AND_MAX_NOTIONAL_GUARDS` (prerequisite before any future live execution task).
- Follow-up candidate: `LIVE_EXECUTION_SYMBOL_FILTER_AND_STALE_DATA_PRECHECKS` (exchange filter, stale candle, and clock-skew checks before live intent submission).
- Follow-up candidate: `LIVE_EXECUTION_IDEMPOTENCY_AND_RESTART_RECONCILIATION` (durable duplicate-order prevention and restart recovery).
- Follow-up candidate: `LIVE_EXECUTION_CANCEL_REPLACE_AND_PARTIAL_FILL_POLICY` (cancel/replace, timeout, orphan-order, and partial-fill handling).
- Follow-up candidate: `LIVE_EXECUTION_MONITORING_ALERTING_AND_SECRET_POLICY` (alerts, credential storage/rotation, redaction, and operational readiness).
- Follow-up candidate: add visual regression/UI tests for dashboard marker/table/channel-overlay rendering once a frontend test harness is assigned.

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
- Completed (2026-05-31): Created `docs/ledger_archives/backlog_task_251_300.md` and reduced root backlog to the Tasks 301-350 recent window when Task 301 was created.

- Completed (2026-06-01): Task 304 `REWRITE_LOOKBACK_MOMENTUM_DAILY_REPORT_WITH_REVISED_PROMPT` rewrote the existing Lookback Return Momentum Korean daily report with the revised Task 303 prompt/workflow/style guidance, preserving saved metrics, same-folder image references, payload semantics, and research-only framing.
