# Goal

Lower the `LOOKBACK_RETURN_MOMENTUM` `entry_threshold` relative to the current configured values, run bounded cost-aware backtests, interpret whether lower thresholds restore acceptable entries and whether those entries have a usable net edge, then generate a daily-report artifact from the selected result set.

# Source Requirement

Owner request:

> 내생각엔 entry_threshold를 조절해보는게 좋을 거 같아. 더 낮추는 방향으로하고 백테스트해주고, 결과 해석해서 daily_report 만드는거까지 task로 만들어줘.

Clean requirement:

- Create an execution task that tests lower `entry_threshold` values for `LOOKBACK_RETURN_MOMENTUM`.
- Preserve Task 305's cost-aware reward/risk gate unless evidence shows a separate implementation bug.
- Compare the current threshold configuration against strictly lower threshold candidates.
- Run the backtest over the same Task 305 validation window unless the owner assigns a different window before execution:
  - `BTCUSDT`
  - `1m`, `5m`, `15m`
  - `2026-02-01T00:00:00Z` inclusive through `2026-05-01T00:00:00Z` exclusive
- Interpret results in terms of signal frequency, accepted-entry count, rejected-entry count, net reward/risk feasibility, total cost drag, expectancy, drawdown, and whether lowering the threshold improved or degraded the strategy.
- Produce a daily report as `report-ko.html`, not Markdown, using the current `docs/blog` workflow and `docs/blog/report_template.html`.

# Extracted Roles

- Owner role: Decide whether the resulting threshold behavior is worth further strategy development after reviewing the backtest and report.
- Supporting roles:
  - Strategy researcher: predeclare the lowered threshold grid, run bounded cost-aware backtests, and interpret the result.
  - Report producer: create the colocated payload, images, and final `report-ko.html`.
  - Documentation maintainer: update strategy/report docs only where this task changes declared assumptions or reusable report artifacts require state pointers.
- Forbidden roles:
  - Live trader.
  - Real Binance order executor.
  - Dashboard/backend/frontend feature implementer.
  - Open-ended optimizer that keeps changing thresholds after seeing results.

# Context

- Task 305 added `cost_aware_entry_filter_v1` and validated `1m`/`5m`/`15m` over the three-month window.
- Task 305 persisted runs `1162`, `1163`, and `1164`; all candidates were blocked by `COST_INFEASIBLE_NET_RR`, so no fills occurred.
- The current owner hypothesis is that lowering `entry_threshold` may restore usable entries.
- This task must distinguish:
  - lower threshold creates more raw signals but they are still rejected by the cost-aware net reward/risk gate;
  - lower threshold creates accepted entries but net expectancy remains weak;
  - lower threshold creates accepted entries and improves cost-adjusted behavior;
  - current no-entry behavior is caused by an implementation/configuration bug rather than threshold level.
- The report workflow was revised by Task 307, so the final daily-report artifact must be HTML.

# Scope

- Read required project state files before execution:
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `STATUS.md`
- Read this task before execution.
- Read the relevant strategy document before any parameter selection, backtest, code change, or reportable research run:
  - `docs/strategy/lookback_return_momentum_v1.md`
- Read the relevant prior result:
  - `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md`
- Read the current report workflow and style docs before report generation:
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html`
- Identify the current interval-specific `entry_threshold` values from the strategy document and implementation/CLI defaults.
- Predeclare a lower-threshold grid before looking at new result performance.
- Include the current threshold configuration as the comparator.
- Use a strictly lower threshold grid with at least three lower levels per tested interval unless the current implementation supports fewer distinct levels.
- Keep all non-threshold strategy assumptions fixed unless a verified bug blocks execution.
- Preserve cost-aware entry filtering, fee/spread/slippage assumptions, stop/target geometry, lookback length, holding bars, cash fraction, and same-candle ambiguity handling from Task 305 unless this task explicitly documents a narrow bug fix.
- Run bounded backtests for `1m`, `5m`, and `15m` over the Task 305 three-month window.
- Persist decision-driving runs with metadata that records:
  - task id `TASK_308`
  - interval
  - threshold candidate
  - current comparator flag
  - cost profile
  - entry-gate version
  - raw candidate count
  - accepted-entry count
  - blocked-entry count by reason
  - completed trade count
  - gross PnL, net PnL, total costs, total return, expectancy, max drawdown, win rate, profit factor, and exit-reason distribution where available
- Produce a task research report under `reports/` that records the full grid, selected comparison result, and interpretation.
- Produce a colocated daily-report artifact under `reports/blog_payloads/lookback-return-momentum/v1/` or another existing convention-compatible slug/date folder, containing:
  - `payload.json`
  - required colocated PNG images
  - `report-ko.html`
- Follow Task 307 report-writing rules:
  - open with a plain-language explanation of Lookback Return Momentum;
  - avoid awkward "기본값" phrasing unless technically unavoidable;
  - no default "주의해서 볼 점" section;
  - final section title `해석`;
  - explain success drivers if the threshold change works, and failure drivers if it does not;
  - include strategy-level theoretical/economic background;
  - do not include obvious backtest disclaimers such as "actual orders were not placed."

# Out of Scope

- Do not place real orders.
- Do not call exchange order/account/private endpoints.
- Do not add live trading behavior.
- Do not add dashboard, backend API, frontend UI, scheduler, database schema, Docker, ML, futures, leverage, or portfolio optimization features.
- Do not backfill new candle data unless the exact Task 305 window coverage check unexpectedly fails and the owner explicitly approves a separate data task.
- Do not change strategy logic beyond threshold parameter usage unless a narrow verified bug prevents the requested threshold test.
- Do not tune threshold values adaptively after inspecting performance.
- Do not promote any result to live trading readiness.
- Do not rewrite unrelated historical reports.

# Requirements

- Before the first new run, record the exact threshold grid and the current comparator values in the task notes or research report.
- The lowered threshold values must be strictly lower than the current configured threshold for each interval.
- The result interpretation must separate raw signal generation from accepted cost-aware entries.
- If no accepted entries occur, explain whether the blocker is the threshold condition, the cost-aware reward/risk gate, cost assumptions, stop/target geometry, or a code/configuration issue.
- If accepted entries occur, compare net performance to the current comparator and to the prior Task 305 no-fill result.
- The daily report must be based on the saved result data and generated graphs, not a draft-only narrative.
- The daily report output must be `report-ko.html`.
- The payload must use filename-only image references where required by the current blog data rules.
- Update `STATUS.md`, append `PROJECT_HISTORY.md`, and update `BACKLOG.md` after execution.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Read `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md`.
- [x] Read the required `docs/blog` workflow/style/template/data/image/handoff files before report generation.
- [x] Record the exact lower-threshold grid before running the first new backtest.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Execution summary:

- Predeclared threshold grid was recorded in `reports/TASK_308_LOOKBACK_RETURN_MOMENTUM_LOWER_ENTRY_THRESHOLD_BACKTEST_DAILY_REPORT.md` before new runs.
- Persisted 12 Task 308 runs for `1m`, `5m`, and `15m` over the assigned February-to-May window.
- Lowering `entry_threshold` increased raw candidates but accepted entries remained `0` for every comparison.
- Daily report artifact was generated at `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-lower-threshold/report-ko.html`.
- Focused strategy/runner/persistence verification passed; broad persistence test command still has two unrelated `FAIR_VALUE_GAP` expectation failures.

# Acceptance Criteria

- Current comparator and lowered `entry_threshold` candidates are explicitly recorded before result interpretation.
- Bounded cost-aware backtests are run for `1m`, `5m`, and `15m` over `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`, or any skipped interval is justified with a concrete data/coverage reason.
- The task report identifies whether lowering `entry_threshold` restores accepted entries.
- The task report explains the observed result using raw candidates, accepted entries, blocked reasons, cost-adjusted reward/risk, net expectancy, total costs, drawdown, and exit behavior.
- A daily-report artifact is generated as `report-ko.html` with colocated `payload.json` and required PNGs.
- The HTML report follows the current `docs/blog` workflow and `docs/blog/report_template.html` reading flow.
- State files are updated after execution.
- No live trading behavior, real order endpoint usage, secrets, or `.env` changes are introduced.

# Required Tests

## Unit Tests

- Run focused `LOOKBACK_RETURN_MOMENTUM` strategy tests if threshold handling, metadata, or entry-gate code is touched.

Suggested command:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py -q
```

## Integration Tests

- Run focused backtest runner/persistence tests if runner CLI wiring, saved metadata, or reportable persisted-run behavior is touched.

Suggested command:

```bash
python -m pytest tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py -q
```

## Contract Tests

- Verify generated `payload.json` follows the current blog data rules.
- Verify image references are filename-only where required.
- Verify `report-ko.html` exists and references only colocated/expected image files.

## Safety Tests

- Confirm no `.env` files are added.
- Confirm no exchange order/account/private endpoints are introduced or called.
- Confirm strategy/backtest code remains offline and research-only.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Threshold grid was predeclared before performance inspection.
- Cost-aware gate remained enabled unless a documented bug fix required a narrow change.
- Daily-report output is HTML, not Markdown.

# Verification

Default focused verification for this task:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py -q
git diff --check
```

Add any report/payload validation command used during execution to the completion summary.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
