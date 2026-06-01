# Task 302: Lookback Return Momentum Report Copy Readability Revision

# Goal

Revise the existing `Lookback Return Momentum V1` Korean daily report so the wording is more concrete and the Markdown is easier to read.

The owner specifically called out that the phrase around "성과가 약하다" feels odd, and that the current Markdown layout is uncomfortable to read. This task should improve the finished report body, not rerun research.

# Source Requirement

Owner request:

```text
성과가 약하다는 내용도 조금 이상해. 그리고 마크다운 양식을 조금만 수정해줘 보기가 불편해. 이거 task 로만들어줘
```

Clean requirement:

- Create a task to revise the existing Task 301 `report-ko.md`.
- Replace vague performance language such as "성과가 약하다" with more concrete language grounded in the saved numbers.
- Improve Markdown readability with small formatting changes.
- Keep the report factual, publication-oriented, and consistent with the existing daily-report template/style rules.
- Do not execute the revision in this task-creation step.

# Extracted Roles

- Owner role:
  - Wants the report wording corrected where the interpretation sounds awkward.
  - Wants the Markdown layout adjusted because it is hard to read.
- Supporting roles:
  - Report editing role: revise the Korean report body for clarity and readability.
  - Data integrity role: keep all numeric claims tied to the existing payload/report data.
  - Style role: follow `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md`.
  - Status-tracking role: update state files after execution.
- Forbidden roles:
  - No new backtest execution.
  - No parameter tuning or search.
  - No strategy/model/code change.
  - No candle backfill.
  - No DB mutation.
  - No image regeneration unless a broken Markdown image reference requires a filename-only correction.
  - No frontend/backend/API change.
  - No live trading.
  - No exchange order/account/private endpoint behavior.
  - No secrets or `.env` changes.

# Context

- Task 301 generated the report artifact at:

```text
reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/
```

- Main files in that artifact:
  - `payload.json`
  - `report-ko.md`
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- The report currently includes several broad phrases such as:
  - "성과가 약했습니다."
  - "비용을 빼고 봐도 성과가 약했고..."
  - "현재 조건에서 우위가 있다고 보기는 어렵습니다."
- The first two phrases are especially likely to feel vague. Prefer language such as:
  - "비용 차감 전 손익도 거의 없거나 음수였고, 비용 반영 후에는 손실이 크게 커졌습니다."
  - "1분봉은 총 거래비용이 순손실의 대부분을 차지했습니다."
  - "15분봉은 거래 수를 줄였지만 비용 반영 후 기대값이 여전히 음수였습니다."
- The current report uses English labels (`The setup`, `The numbers`, `The kicker`) and repeated bullet lists that may reduce readability in a Korean blog post.

# Scope

- Read required state files and this task file before execution.
- Read:
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
- Revise only:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
- Optional, only if needed for consistency:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
- Allowed content changes:
  - Replace vague wording with concrete performance/cost descriptions.
  - Make section structure easier to scan.
  - Convert awkward English micro-headings to Korean headings or compact Markdown tables.
  - Reduce duplicated metric lists where the same numbers are repeated too often.
  - Keep all image references as same-folder `./[filename].png`.
  - Keep the same required 10-section report structure unless a template-allowed subsection is condensed for readability.
- Update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.

# Out of Scope

- No new backtest execution.
- No parameter tuning/search.
- No strategy/code change.
- No candle backfill.
- No saved-run DB mutation.
- No PNG chart regeneration unless a Markdown reference is broken and filename-only correction is insufficient.
- No payload schema redesign.
- No English report.
- No `images/` subfolder.
- No `image_plan.md` or `image_plan.json`.
- No frontend/backend/API changes.
- No live trading behavior.
- No real exchange order/account/private endpoint behavior.
- No secrets or `.env` changes.

# Requirements

- The revised `report-ko.md` must remain a publish-ready Korean report body.
- Replace "성과가 약하다/약했습니다" style wording with concrete claims based on the saved results.
- Preserve the core factual conclusions:
  - `1m` result was negative after costs.
  - `15m` result was negative after costs.
  - Costs materially widened the losses.
  - `5m` was skipped because local closed candles were missing.
  - Results remain research-only and do not imply live-trading readiness.
- Improve Markdown readability with small, targeted changes:
  - Prefer Korean subheadings over mixed English labels where they interrupt reading.
  - Prefer compact tables for dense metric comparisons.
  - Avoid repeating the same metric block in multiple sections unless it serves a clear purpose.
  - Keep paragraphs short.
- Do not invent missing data.
- Keep `[확인 필요]` where a value is genuinely missing.
- Do not expose task IDs, run IDs, internal candidate IDs, source paths, DB dumps, config dumps, git commits, secrets, or `.env` values in `report-ko.md` or report-facing payload fields.
- Do not use forbidden expressions from `docs/blog/DAILY_REPORT_STYLE.md`.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 302 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read the relevant strategy document.
- [x] Read `DAILY_REPORT_TEMPLATE.md`.
- [x] Read `DAILY_REPORT_STYLE.md`.
- [x] Read the existing artifact `payload.json`.
- [x] Read the existing artifact `report-ko.md`.
- [x] Record assumptions, blockers, or unclear status items before implementation.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 302 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `report-ko.md` is revised for readability.
- The report no longer uses vague "성과가 약하다/약했습니다" phrasing.
- The report explains the weak/negative result in concrete terms using saved metrics, especially gross PnL, net PnL, cost totals, return, expectancy, and drawdown where appropriate.
- Markdown is easier to scan than Task 301 output.
- Image references remain same-folder references, such as `./summary_equity_curve.png`.
- Payload image references, if touched, remain filename-only.
- Required PNG files remain in the same folder and non-empty.
- No task IDs, run IDs, internal candidate IDs, source paths, DB dumps, config dumps, git commits, secrets, or `.env` values are exposed in the report-facing files.
- No new backtest, parameter tuning, strategy/code change, candle backfill, DB mutation, frontend/backend/API change, live trading behavior, or exchange order/account/private endpoint behavior is performed.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Not applicable unless reusable helper code is introduced. Avoid helper code for this editing task.

## Integration Tests

- Not applicable unless reusable report-generation code is introduced. Avoid new reusable code for this editing task.

## Contract Tests

Recommended:

```bash
test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/summary_equity_curve.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/cost_impact.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_loss_trade.png
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null
rg -n "\./[A-Za-z0-9_\\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
! rg -n "\./images/|images/" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
! rg -n "성과가 약|성과가 좋지|성과가 지속적으로 악화" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
```

## Safety Tests

Recommended:

```bash
! rg -n "TASK_299|Task 299|task 299|TASK_301|Task 301|task 301|TASK_302|Task 302|task 302|run 1160|run 1161|1160|1161|candidate_id|source file|DB dump|config dump|git commit" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
! rg -n "단순히|질문에서 출발한다|비용 스트레스|보수적 거래비용 가정에서 유효성이 약해진 사례|고비용 시나리오|거래비용 민감도 검증 구간|기대값이 음수로 고정되었습니다|검증 사례로 기록하는 것이 적절합니다|확실히 먹힌다|무조건 작동한다|실전 투입 가능하다|놀라운 결과|인상적인 결과|매우 유의미하다" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed|order endpoint|account endpoint" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Blog/data/image contract respected.
- Strategy document read before report editing.
- No new backtest execution.
- No parameter tuning/search.
- No strategy/code change.
- No candle backfill or DB mutation.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.

# Verification

Default:

```bash
git diff --check -- reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json tasks/TASK_302_LOOKBACK_RETURN_MOMENTUM_REPORT_COPY_READABILITY_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
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
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Revised the existing `Lookback Return Momentum V1` Korean report body for readability.
  - Replaced vague "성과가 약하다" wording with concrete saved-result descriptions around gross PnL, net PnL, total costs, return, expectancy, and drawdown.
  - Converted the most repetitive metric lists into compact Markdown tables.
  - Removed awkward English micro-headings from the report body.
  - Updated the matching payload cost interpretation sentence for consistency.
  - Did not rerun a backtest, regenerate images, change strategy/code, backfill candles, or mutate saved run records.
- Tests added or updated:
  - None. This was an artifact editing task and no reusable helper code was introduced.
- Tests run:
  - `test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `test -f reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/summary_equity_curve.png`
  - `test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/cost_impact.png`
  - `test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`
  - `test -s reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_loss_trade.png`
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null`
  - `rg -n "\./[A-Za-z0-9_\\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - Negative checks for `./images/`, `images/`, vague performance wording, English micro-headings, task IDs, run IDs, internal candidate IDs, source/config dump wording, git commit wording, forbidden style expressions, and secret/live-order markers in report-facing files.
  - `git diff --check -- reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json tasks/TASK_302_LOOKBACK_RETURN_MOMENTUM_REPORT_COPY_READABILITY_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md`
- Codex self-review result:
  - Passed. Scope stayed within Task 302; no strategy logic, backtest, candle data, DB, frontend/backend/API, live trading, exchange endpoint, secret, or `.env` behavior was changed.
- Known limitations:
  - The report still reflects the same saved diagnostic results; no new validation was performed.
  - `5m` remains unavailable because local closed candles are missing.
- Recommended next task:
  - Review the revised `report-ko.md`; if continuing research, create a separate bounded `BTCUSDT` `5m` candle backfill task or a locked OOS/WFO diagnostic task for `LOOKBACK_RETURN_MOMENTUM`.
