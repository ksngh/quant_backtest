# Task 301: Lookback Return Momentum Daily Report Generation

# Goal

Generate a publish-ready Korean daily report from the completed Task 299 `LOOKBACK_RETURN_MOMENTUM` validation results.

The owner explicitly wants a real blog/report body, not a draft-only workflow. The final artifact should be `report-ko.md` written for publication using the data and generated graphs that belong in the report.

# Source Requirement

Owner requests:

```text
task를 하나 만들어줘. 블로그 초안을 작성하는게 아니라. 본문을 바로 작성할거야. docs/blog에 있는 파일들 중 daily_report_template 과 daily_report_style을 읽고 블로그에 투고할 글을 작성해주는 workflow를 정의하는 task. 현재는 지금 daily_report_workflow가 초안을 쓰는데에 집중하게 되어있는데, 그게 아니라 내가 리포트 만들어줘~ 하면 리포트에 들어가야할 데이터 과, 생성된 그래프 그림들로 아예 리얼 리포트를 만들 수 있도록 나머지 작업들을 해줘
```

```text
모멘텀 백테스트한 내용으로 데일리 리포트 만드는 task 진행해줘
```

```text
리포트 만드는 task 만들어줘
리포트 만드는 task 진행해줘
```

Clean requirement:

- Create and execute a task that produces a real daily report for the momentum backtest results.
- Use the completed Task 299 `LOOKBACK_RETURN_MOMENTUM` validation results as the data source.
- Read `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md` before writing the report.
- Use `docs/blog/daily_report_workflow.md`, `docs/blog/image_generation_prompt.md`, `docs/blog/backtest_report_data_rules.md`, and `docs/blog/agent_handoff_prompt.md` as supporting workflow/data/image guidance.
- If active workflow docs still describe the output as only a draft, update the wording so future owner requests for “리포트 만들어줘” produce a publication-ready `report-ko.md` body, not a draft-only handoff.

# Extracted Roles

- Owner role:
  - Wants a publish-ready daily report from the momentum validation results.
  - Wants `DAILY_REPORT_TEMPLATE.md` and `DAILY_REPORT_STYLE.md` to govern the written body.
  - Wants the workflow to use report data and generated graphs to create the actual article body.
- Supporting roles:
  - Report data role: derive a compact report payload from Task 299 saved results and report notes.
  - Image role: generate required report PNGs when source data is available.
  - Writing role: write `report-ko.md` as final publication-oriented Korean markdown.
  - Workflow documentation role: adjust active daily-report wording only if needed to remove draft-only semantics.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No new strategy/model implementation.
  - No parameter tuning or search.
  - No new backtest execution unless explicitly required by a later task.
  - No candle backfill or candle DB mutation.
  - No mutation of saved backtest run records.
  - No frontend/backend/API change.
  - No live trading.
  - No exchange order/account/private endpoint behavior.
  - No secrets or `.env` changes.

# Context

- Task 296 documented `LOOKBACK_RETURN_MOMENTUM` in `docs/strategy/lookback_return_momentum_v1.md`.
- Task 297 implemented the research-only strategy and focused tests passed.
- Task 299 validated default parameters on available local `BTCUSDT` candles:
  - `1m` saved run `1160`: `2026-05-20T00:00:00Z` to `2026-05-28T08:15:00Z`, `12016` candles, `1285` completed trades, `-37.9957pct`.
  - `15m` saved run `1161`: same date window, `802` candles, `169` completed trades, `-6.8468pct`.
  - `5m` was skipped because local closed candles were missing.
- Task 299 saved the validation summary at `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`.
- Task 300 wired daily-report writing to `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md`.
- Current daily-report docs may still use the word “초안” in some active guidance. This task may update only that wording where it conflicts with the owner’s request for a real publish-ready report body.

# Scope

- Read required state files and this task file before execution.
- Read:
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
- Create a report artifact folder under:

```text
reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/
```

- Generate or save:
  - `payload.json`
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
  - optional PNGs only if source data supports them and they improve the report
  - `report-ko.md`
- Use same-folder image references in `report-ko.md`, such as `./summary_equity_curve.png`.
- Keep payload image references filename-only.
- Use saved run IDs only as internal source references; do not expose run IDs, task IDs, or internal candidate IDs in public report-facing payload fields, chart titles, image filenames, or `report-ko.md` body.
- Make the report honest:
  - `1m` and `15m` were both cost-dominated and negative.
  - `5m` was unavailable because local candles were missing.
  - Results are research-only and not suitable for live trading.
- If data needed for exact trade charts is unavailable, create clear fallback images and document the limitation in payload/report wording without inventing candles or trade paths.
- Update active daily-report docs only if necessary to replace draft-only semantics with publish-ready report semantics.

# Out of Scope

- No new backtest execution.
- No parameter tuning/search.
- No strategy code change.
- No strategy promotion.
- No candle backfill.
- No saved-run DB mutation.
- No frontend/backend/API changes.
- No English report unless separately requested.
- No `images/` subfolder.
- No `image_plan.md` or `image_plan.json`.
- No live trading behavior.
- No real exchange order/account/private endpoint behavior.
- No secrets or `.env` changes.

# Requirements

- The report must be publication-oriented Korean markdown, not a draft handoff.
- `report-ko.md` must follow `DAILY_REPORT_TEMPLATE.md` section structure unless a section has no data and should be clearly marked `[확인 필요]` or omitted only where the template allows omission.
- `report-ko.md` must follow `DAILY_REPORT_STYLE.md` tone, forbidden expressions, internal-term conversions, and interpretation style.
- The artifact folder must be colocated: `payload.json`, PNGs, and `report-ko.md` in the same directory.
- The report must use generated PNGs from the same directory.
- The report must not include task IDs, run IDs, internal candidate IDs, source paths, DB dumps, config dumps, git commits, secrets, or `.env` values.
- Missing values must not be invented.
- Any fallback chart must be clearly labeled as a fallback and must not invent unavailable price paths.
- Any workflow wording change must be limited to daily-report publish-ready semantics.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 301 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read the relevant strategy document.
- [x] Read Task 299 report.
- [x] Read relevant daily-report docs.
- [x] Record assumptions, blockers, or unclear status items before implementation.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 301 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json` exists.
- Required PNGs exist in the same folder and are non-empty.
- `report-ko.md` exists in the same folder and is written as a publish-ready Korean report body.
- `report-ko.md` uses same-folder image references only.
- Payload image references are filename-only.
- The report accurately states that the `1m` and `15m` validations were negative and cost-dominated.
- The report accurately states that `5m` was skipped because local candles were missing.
- The report does not imply live-trading readiness.
- The report does not expose task IDs, run IDs, internal candidate IDs, source paths, DB dumps, config dumps, git commits, secrets, or `.env` values.
- No new backtest, parameter tuning, strategy code change, candle backfill, saved-run mutation, frontend/backend/API change, live trading behavior, or exchange order/account/private endpoint behavior is performed.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Not applicable unless helper code is introduced. Avoid helper code unless clearly necessary.

## Integration Tests

- Not applicable unless reusable report generation code is introduced. Avoid new reusable code unless clearly necessary.

## Contract Tests

Recommended:

```bash
test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/summary_equity_curve.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/cost_impact.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_loss_trade.png
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null
rg -n "\./[A-Za-z0-9_\\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
! rg -n "\./images/|images/" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
```

## Safety Tests

Recommended:

```bash
! rg -n "TASK_299|Task 299|task 299|run 1160|run 1161|1160|1161|candidate_id|source file|DB dump|config dump|git commit" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed|order endpoint|account endpoint" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json docs/blog
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Blog/data/image contract respected.
- Strategy document read before report generation.
- No new backtest execution.
- No parameter tuning/search.
- No strategy/code change unless explicitly justified and in scope.
- No DB mutation.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.

# Verification

Default:

```bash
git diff --check -- docs/blog reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528 tasks/TASK_301_LOOKBACK_RETURN_MOMENTUM_DAILY_REPORT_GENERATION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
```

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

## Completion Summary

- Files changed:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/summary_equity_curve.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/cost_impact.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_loss_trade.png`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Generated a colocated publish-ready daily-report artifact for `Lookback Return Momentum V1` under `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/`.
  - Used the saved `1m` and `15m` validation results as read-only sources; no new backtest, tuning, strategy/code change, candle backfill, or saved-run mutation was performed.
  - Generated four required PNGs: summary equity/drawdown, cost impact, representative winning trade, and representative losing trade.
  - Wrote `report-ko.md` as the final Korean report body with same-folder image references.
  - Updated active daily-report workflow wording so future report requests target a publication-ready report body instead of a draft-only handoff.
- Tests added or updated:
  - None. No reusable production helper code was introduced.
- Tests run:
  - `test -f` / `test -s` artifact existence checks for `payload.json`, `report-ko.md`, and required PNGs.
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null`
  - `rg -n "\./[A-Za-z0-9_\\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - Negative checks for `./images/`, `images/`, task IDs, run IDs, internal candidate IDs, source/config dump wording, git commit wording, and secret/live-order markers in the artifact files.
  - Negative checks for forbidden cost-impact wording in `report-ko.md`, `payload.json`, and `cost_impact.png` raster strings.
  - `rg -n "초안|draft|Draft" docs/blog`
  - `git diff --check -- docs/blog reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528 tasks/TASK_301_LOOKBACK_RETURN_MOMENTUM_DAILY_REPORT_GENERATION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md docs/ledger_archives/backlog_task_251_300.md docs/ledger_archives/project_history_task_251_300.md`
- Codex self-review result:
  - Passed. Scope stayed within Task 301; no unrelated implementation, strategy logic, DB mutation, live trading behavior, exchange order/account/private endpoint behavior, hardcoded secret, or `.env` change was added.
- Known limitations:
  - `5m` remains absent because local closed candles are missing.
  - The report uses saved diagnostic results only; it is not a new OOS/WFO validation.
  - Representative trade charts use saved candle windows and trade records from the available runs; they do not imply the strategy is profitable overall.
- Recommended next task:
  - Create a separate bounded `BTCUSDT` `5m` candle backfill execution task if the owner wants the missing middle timeframe populated, or create a locked OOS/WFO diagnostic task before making further claims about `LOOKBACK_RETURN_MOMENTUM`.
