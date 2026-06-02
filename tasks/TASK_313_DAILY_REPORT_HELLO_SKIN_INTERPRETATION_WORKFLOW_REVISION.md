# Task 313: DAILY_REPORT_HELLO_SKIN_INTERPRETATION_WORKFLOW_REVISION

# Goal

Revise the reusable daily-report workflow, style rules, and HTML template so future Tistory reports:

- distinguish a failed tested strategy/version from rejecting the broader strategy family;
- explain why broad rejection is premature when the saved evidence only covers a bounded implementation, period, market, and parameter set;
- generate single-file HTML suitable for the Tistory hELLO skin with readable width, table alignment, and image sizing.

# Source Requirement

Owner request on 2026-06-02 after reviewing the Task 312 report interpretation:

> `Lookback Return Momentum V1은 현재 조건에서 비용 반영 후 유효한 전략으로 보기 어렵다. 다만 이 결과만으로 모멘텀 전략 일반을 기각하기는 이르다.`
>
> This is the kind of content needed in the report's `해석` section. The workflow should also explain why broad rejection is premature.
>
> Additionally, HTML reports should be written for the Tistory hELLO skin. The reusable template should be adjusted for a `1100px ~ 1200px` body width, default `1120px`, centered layout, single-file internal CSS, left-aligned tables, full-width images, and larger generated chart image sizes.

# Extracted Roles

- Owner role:
  - Provides report-interpretation and hELLO skin layout requirements.
- Supporting roles:
  - Workflow editor: update reusable `docs/blog` workflow/style/template/handoff/data/image rules.
  - HTML template maintainer: adjust the reusable HTML template for Tistory hELLO skin body width and responsive behavior.
  - Report interpretation rule writer: define how future reports should avoid overbroad conclusions from bounded backtests.
  - Image rule maintainer: update recommended chart export dimensions for readable Tistory display.
- Forbidden roles:
  - Backtest runner.
  - Strategy/code implementer.
  - Parameter optimizer.
  - Existing report artifact rewriter.
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend/API implementer.

# Context

Task 312 generated a Tistory-ready report from Task 311 saved results. Owner review identified a missing interpretation nuance:

- It is valid to say `Lookback Return Momentum V1` is not effective after costs under the tested conditions.
- It is too broad to say momentum strategies in general are meaningless.
- Future reports should explicitly explain the evidence boundary.

For the Task 311/312 case, the reason broad rejection is premature includes:

- the tested object was one simple V1 implementation, not all momentum strategies;
- the signal was close-to-close lookback return only;
- the result covered one symbol, one February-to-May 2026 window, and selected `1m`/`5m`/`15m` intervals;
- the tested grid did not include stronger regime, liquidity, continuation, higher-timeframe, or market-condition filters;
- negative net results after costs prove the current version did not clear costs, not that momentum cannot exist under other conditions;
- a stronger claim would require broader OOS/WFO validation, random/baseline comparisons, regime segmentation, and alternative momentum definitions.

The owner also clarified that future HTML reports should be optimized for Tistory hELLO skin rather than the previous wide desktop review target.

# Scope

- Read required state files and this task before implementation.
- Inspect and update only reusable report workflow/template/rule documents as needed:
  - `docs/blog/report_template.html`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/agent_handoff_prompt.md`
- Keep edits focused on:
  - interpretation-boundary rules for failed and successful strategy reports;
  - hELLO skin HTML layout and CSS rules;
  - table alignment rules;
  - image display and generated chart dimension rules;
  - final verification expectations for future `report-ko.html` artifacts.
- Update state files after execution.

# Out of Scope

- Regenerating or rewriting existing report artifacts, including Task 312's `report-ko.html`.
- Creating a new daily report.
- Creating or editing payloads/images under `reports/`.
- Running a new backtest.
- Parameter tuning/search.
- Strategy/code changes.
- Strategy document changes unless a wording inconsistency in docs/blog directly requires referencing strategy-doc expectations.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Future `해석` sections must separate:
  - what the tested strategy/version did or did not prove;
  - what cannot be concluded about the broader strategy family.
- For negative reports, require language similar in meaning to:

```text
현재 버전은 이 조건에서 비용 반영 후 유효한 전략으로 보기 어렵습니다.
다만 이 결과만으로 전략군 전체를 기각하기는 이릅니다.
```

- The report must then explain why broad rejection is premature using saved evidence boundaries, not generic disclaimers.
- The rule must generalize beyond momentum:
  - if a strategy fails, avoid rejecting the whole strategy family unless the task explicitly tested that breadth;
  - if a strategy succeeds, avoid claiming universal effectiveness unless broad validation supports it.
- For the Lookback Return Momentum example, future workflow guidance should mention that a bounded V1 failure does not reject momentum generally because tested scope may be limited by implementation, window, symbol, timeframe, cost assumptions, and missing filters/confirmations.
- Future HTML reports must target Tistory hELLO skin posting.
- HTML must be a single complete file with internal CSS and no external CSS dependency.
- The default report body container must follow:

```css
:root {
  --page-max-width: 1120px;
}

.report-page {
  max-width: var(--page-max-width);
  width: calc(100% - 32px);
  margin: 0 auto;
}
```

- The allowed page max-width range is `1100px` to `1200px`; default is `1120px`.
- Mobile layout must preserve side padding and avoid horizontal overflow.
- Tables must default to left alignment.
- Numeric columns may be right-aligned only when it improves readability; do not center numeric columns by default.
- Tables should read as one aligned block rather than scattered centered cells.
- Images must use full report body width:

```css
.report-figure img {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
}
```

- Generated chart image dimension guidance:
  - general graph images: at least `1600px x 900px`;
  - wide charts or equity curves: around `1800px x 1000px`;
  - table-heavy or complex charts: around `1800px x 1200px`.
- HTML must not force images into small fixed dimensions; images should scale to body width.
- The reusable style should prioritize readability, width, alignment, and restrained writing over decorative design.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read current `docs/blog` workflow/style/template/data/image/handoff docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- `docs/blog/report_template.html` defines a hELLO-skin-friendly single-file HTML template with:
  - `--page-max-width: 1120px`;
  - centered `.report-page`;
  - responsive `width: calc(100% - 32px)`;
  - image rules that scale images to full body width;
  - table alignment rules matching the owner request.
- Daily-report workflow/style/template docs require final `해석` sections to state the bounded conclusion and explain why broader strategy-family rejection is premature when evidence is bounded.
- Daily-report workflow/style/template docs also prevent overclaiming positive results beyond the tested evidence.
- Image generation docs recommend the new larger chart export dimensions.
- Existing report artifacts under `reports/` are not modified.
- No new backtest, DB mutation, strategy/code change, live trading behavior, order/account/private endpoint usage, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless implementation adds reusable code.

## Integration Tests

- Not required unless implementation adds reusable code.

## Contract Tests

- Verify hELLO skin layout tokens exist:

```bash
rg -n -- "--page-max-width: 1120px|\\.report-page|width: calc\\(100% - 32px\\)|max-width: var\\(--page-max-width\\)" docs/blog/report_template.html
```

- Verify interpretation-boundary rules exist:

```bash
rg -n "전략군 전체|기각하기|현재 버전|조건에서|유효한 전략으로 보기 어렵|성공.*과장|보편" docs/blog
```

- Verify image dimension guidance exists:

```bash
rg -n "1600px x 900px|1800px x 1000px|1800px x 1200px" docs/blog
```

- Verify no report artifacts changed:

```bash
git diff --name-only -- reports
```

- Run:

```bash
git diff --check
```

## Safety Tests

- Confirm no code/report workflow added by this task calls exchange order/account/private endpoints.
- Confirm no API keys, secrets, or `.env` files are added or modified.
- Run a focused diff grep for:

```bash
rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" docs/blog tasks/TASK_313_DAILY_REPORT_HELLO_SKIN_INTERPRETATION_WORKFLOW_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Existing reports not rewritten.
- hELLO skin width and table/image layout rules encoded.
- Interpretation-boundary rules are generalized, not overfit to one momentum report.

# Verification

Default:

```bash
rg -n -- "--page-max-width: 1120px|\\.report-page|width: calc\\(100% - 32px\\)|max-width: var\\(--page-max-width\\)" docs/blog/report_template.html
rg -n "전략군 전체|기각하기|현재 버전|조건에서|유효한 전략으로 보기 어렵|성공.*과장|보편" docs/blog
rg -n "1600px x 900px|1800px x 1000px|1800px x 1200px" docs/blog
git diff --check
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

# Completion Summary

- Files changed:
  - `docs/blog/report_template.html`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_313_DAILY_REPORT_HELLO_SKIN_INTERPRETATION_WORKFLOW_REVISION.md`
- Implementation summary:
  - Revised the reusable Tistory hELLO HTML template to use `.report-page`, `--page-max-width: 1120px`, centered body width, mobile-safe width, full-width image display, and left-first table alignment with numeric right alignment only when useful.
  - Updated daily-report style/template/workflow/handoff/data/image docs so future `report-ko.html` outputs distinguish a bounded tested version result from claims about the broader strategy family.
  - Added reusable interpretation rules for negative and positive reports: do not reject a whole strategy family from a bounded failure, and do not overclaim universal success from a narrow pass.
  - Added chart export guidance for `1600px x 900px`, `1800px x 1000px`, and `1800px x 1200px` source images.
- Tests added or updated:
  - None. This task changed documentation and an HTML template only.
- Tests run:
  - `rg -n -- "--page-max-width: 1120px|\\.report-page|width: calc\\(100% - 32px\\)|max-width: var\\(--page-max-width\\)" docs/blog/report_template.html`
  - `rg -n "전략군 전체|기각하기|현재 버전|조건에서|유효한 전략으로 보기 어렵|성공.*과장|보편" docs/blog`
  - `rg -n "1600px x 900px|1800px x 1000px|1800px x 1200px" docs/blog`
  - `rg -n "1392|report-shell|--max" docs/blog`
  - `git diff --name-only -- reports`
  - `git diff --check`
  - `rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" docs/blog tasks/TASK_313_DAILY_REPORT_HELLO_SKIN_INTERPRETATION_WORKFLOW_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md`
  - `rg -n "[ \\t]+$" docs/blog/report_template.html docs/blog/DAILY_REPORT_STYLE.md docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/daily_report_workflow.md docs/blog/backtest_report_data_rules.md docs/blog/image_generation_prompt.md docs/blog/agent_handoff_prompt.md tasks/TASK_313_DAILY_REPORT_HELLO_SKIN_INTERPRETATION_WORKFLOW_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md`
- Codex self-review result:
  - Passed. Scope stayed within the assigned docs/blog template/workflow/rule changes plus mandatory state files. No strategy/backtest/code/report artifact rewrite was introduced.
- Known limitations:
  - `git diff --name-only -- reports` is non-empty because pre-existing dirty report artifacts from earlier tasks remain in the worktree. Task 313 did not edit report artifacts.
  - Safety grep matches only declarative safety-policy/task text such as `.env` and endpoint prohibitions, not executable order/account/private endpoint code.
- Recommended next task:
  - Create a separate bounded report-regeneration task if the owner wants the existing Task 312 `report-ko.html` regenerated with the revised hELLO skin and interpretation-boundary rules.
