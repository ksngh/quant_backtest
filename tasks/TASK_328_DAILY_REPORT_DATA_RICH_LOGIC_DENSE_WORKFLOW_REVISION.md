# Task 328: DAILY_REPORT_DATA_RICH_LOGIC_DENSE_WORKFLOW_REVISION

# Goal

Revise the reusable daily-report workflow so future `report-ko.html` artifacts
combine:

- V2-style format and data display:
  - Tistory hELLO HTML layout.
  - rich but purposeful tables.
  - colocated PNG charts.
  - data coverage, result comparison, cost impact, exit mix, side attribution,
    yearly/regime attribution, and representative-trade visuals when available.
- V1-style reasoning density:
  - tight result-to-driver-to-limitation-to-next-action logic.
  - evidence-supported success and failure interpretation.
  - clear explanation of why each major table or image matters.

Also revise the writing rules so future report-facing Korean copy does not end
sentences with the vague `봅니다.` construction.

# Source Requirement

Owner request:

> v2처럼 형식과 데이터 표시를 하고, v1처럼 논리를 촘촘히 할 수 있도록
> 워크플로우를 바꿔봐. 그리고 글에서 '~~봅니다.' 는 제거해줘.
> task로 만들어줘

Interpreted requirement:

- Create a future workflow-revision task, not a one-off report rewrite.
- The target is reusable `docs/blog` report-generation rules and prompts.
- Future report artifacts should preserve the improved V2 report presentation
  contract while recovering the tighter explanatory logic of the V1
  `20260201-20260501-atr-reward-cost` report.
- Do not regenerate current reports as part of this task creation.

# Extracted Roles

- Owner role:
  - Defines the desired report-writing standard.
  - Identifies V2 as better for format/data display.
  - Identifies V1 as better for dense interpretation logic.
  - Prohibits report-facing `~~봅니다.` wording.
- Supporting roles:
  - Workflow maintainer: update reusable daily-report workflow/style/template
    docs.
  - Report-structure maintainer: encode V2-style table/image/data-display
    requirements without making reports table-heavy without interpretation.
  - Copy-rule maintainer: add a report-facing Korean wording rule banning
    sentence-final `봅니다.` and related vague observational phrasing.
  - Interpretation-rule maintainer: require every major metric/table/image to
    be reclaimed in narrative interpretation.
  - Verification role: grep updated docs for required guidance and forbidden
    wording.
- Forbidden roles:
  - Backtest runner.
  - Strategy implementer.
  - Report artifact rewriter.
  - PNG/image generator.
  - Payload generator.
  - Database mutator.
  - Frontend/backend/API implementer.
  - Live trader.
  - Real Binance order executor.
  - Exchange order/account/private endpoint caller.
  - Secret or `.env` user.

# Context

The latest comparison found:

- The V2 HTF report has stronger artifact form and data display:
  - `report-ko.html`
  - same-folder PNGs
  - broader tables and charts, including data coverage, result comparison,
    exit mix, side attribution, yearly attribution, cost impact, and
    representative trades.
- The V1 ATR reward/cost report has stronger interpretation logic:
  - it clearly states the experiment change;
  - explains what the result proves and does not prove;
  - connects cost, ATR geometry, entry count, win rate, exit mix, turnover, and
    representative trades to a bounded conclusion;
  - gives next improvements with reasons.
- The current V2 report is readable but too close to "showing the result" rather
  than "reasoning through the result."

Reference reports for future execution:

- V1 logic-density reference:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
- V2 data-display reference:
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`

# Scope

- Create or update reusable workflow guidance in:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html` only if the HTML template text/guidance
    needs a narrow rule update.
- Encode a future report standard that requires:
  - V2-like data inventory and visual richness.
  - V1-like interpretation chain.
  - no raw table or chart without an explanatory takeaway.
  - no metric dump that is not used in `핵심 요약`, `결과`, `대표 거래`, or
    `해석`.
  - no report-facing sentence-final `봅니다.`.
- Add verification instructions that can be run on workflow docs and future
  report artifacts.
- Update state files after execution.

# Out of Scope

- Editing current report artifacts, including:
  - V1 ATR reward/cost report.
  - V2 HTF no-cost report.
- Regenerating `payload.json`.
- Regenerating PNG images.
- Creating new report artifacts.
- Running backtests.
- Parameter tuning or strategy validation.
- Strategy document changes unless a narrow report-workflow reference to
  strategy docs is required.
- Strategy/code changes.
- DB mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Exchange order/account/private endpoints.
- Secrets or `.env` changes.

# Requirements

- Data-display requirements:
  - Future reports should keep the V2 artifact contract:
    - single `report-ko.html`;
    - internal CSS;
    - Tistory hELLO `1120px` centered `.report-page`;
    - colocated `payload.json`;
    - colocated PNGs referenced by same-folder paths;
    - no default Markdown final artifact.
  - Future reports should prefer the V2-style data surfaces when relevant:
    - data coverage table/chart;
    - compact setup table;
    - result comparison table;
    - cost impact chart/table;
    - exit mix;
    - side attribution;
    - yearly or regime attribution;
    - representative win/loss trades.
  - Each table or chart must have a clear analytic role:
    - what it shows;
    - why it matters;
    - how it changes the interpretation.
  - Avoid table inflation:
    - large tables should be split, reduced, or moved to payload/report
      metadata;
    - reader-facing tables should answer a question, not merely display all
      available columns.

- Logic-density requirements:
  - Future reports must use this narrative chain:
    1. Strategy idea.
    2. What changed in this version or experiment.
    3. What the main result was.
    4. Which evidence explains the result.
    5. Which evidence weakens or limits the result.
    6. What the result can conclude.
    7. What the result cannot conclude.
    8. What the next improvement is and why.
  - `핵심 요약` must state the main result and the main driver, not only list
    settings.
  - `결과` must connect tables/charts to drivers:
    - cost drag;
    - gross vs net;
    - turnover;
    - ATR geometry;
    - exit mix;
    - side attribution;
    - year/regime concentration;
    - data coverage/blockers;
    - signal horizon alignment;
    - representative trade recurrence.
  - `대표 거래` must not be isolated anecdotes:
    - explain why the trade happened;
    - whether the entry and exit matched strategy logic;
    - whether it represents a recurring pattern or an outlier;
    - whether it suggests strategy behavior, volatility behavior, or engine
      issues.
  - `해석` must reclaim the most important evidence from earlier sections and
    produce a bounded conclusion.
  - Success cases and failure cases both require driver analysis:
    - If positive: explain likely success drivers and why the conclusion is
      still bounded.
    - If negative: explain likely failure drivers and why broader strategy-family
      rejection may still be premature.
    - If mixed: separate which intervals, sides, years, exits, or variants drove
      the result.

- Copy/style requirements:
  - Future report-facing Korean prose must not use sentence-final `봅니다.`.
  - Avoid vague forms such as:
    - `~라고 봅니다.`
    - `~로 봅니다.`
    - `~해 봅니다.`
  - Replace them with direct evidence-based wording, for example:
    - `...로 해석합니다.`
    - `...로 판단합니다.`
    - `...를 확인했습니다.`
    - `...를 비교했습니다.`
    - `...가 핵심입니다.`
    - `...가 필요합니다.`
  - Continue existing style bans:
    - no awkward `그것은`;
    - no `강한 결론` / `더 강한 결론`;
    - no unnecessary `기본값`;
    - no standalone `가설` section by default;
    - no obvious backtest-order disclaimers.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read the relevant reusable daily-report workflow docs.
- [x] Read the V1 and V2 reference reports listed in Context.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open
  question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and
  verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- Reusable daily-report workflow docs are updated so future reports combine:
  - V2-style HTML/data/image/table richness;
  - V1-style evidence-backed interpretation density.
- The workflow explicitly requires each table/image to be connected to an
  interpretive takeaway.
- The workflow explicitly requires success/failure/mixed-result driver analysis.
- The workflow explicitly requires `해석` to reclaim major evidence rather than
  only restate the headline result.
- The workflow explicitly bans report-facing sentence-final `봅니다.`.
- The workflow includes replacement wording examples for `봅니다.` constructions.
- Existing report artifacts are not edited.
- No backtest, strategy/code change, DB mutation, candle backfill, frontend/backend
  change, live trading behavior, exchange endpoint behavior, secret, or `.env`
  change is introduced.

# Required Tests

## Unit Tests

- Not required unless reusable code is added.

## Integration Tests

- Not required unless a report-generation script is changed.

## Contract Tests

- Verify updated docs contain the core rule concepts:

```bash
rg -n "V2|data display|데이터|table|chart|해석|driver|success|failure|봅니다|그것은|강한 결론" docs/blog
```

- Verify the report-facing copy-ban rule is encoded:

```bash
rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다" docs/blog
```

Expected:

- Matches are allowed only where the docs describe the banned phrase or a
  verification rule.
- Future report examples, templates, or sample prose must not use `봅니다.` as
  valid output wording.

- Verify existing report artifacts are not modified by this task:

```bash
git diff --name-only -- reports
```

Expected:

- No new report artifact edits from this task.
- Pre-existing dirty report files, if any, must be identified as pre-existing
  and not modified by this task.

## Safety Tests

- Confirm no live trading, order/account/private endpoint, secret, or `.env`
  behavior was added:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_328_DAILY_REPORT_DATA_RICH_LOGIC_DENSE_WORKFLOW_REVISION.md
```

Expected:

- No new unsafe behavior.
- Declarative safety text is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Existing report artifacts preserved.
- V2 data-display strengths encoded.
- V1 reasoning-density strengths encoded.
- `봅니다.` copy rule encoded.

# Verification

Default:

```bash
git diff --check
rg -n "봅니다\\." docs/blog
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the
result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before
merge if this task is included in a PR.

# Completion Summary Required

- files changed
- implementation summary
- workflow docs updated
- report artifacts preserved
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary

- Files changed:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_328_DAILY_REPORT_DATA_RICH_LOGIC_DENSE_WORKFLOW_REVISION.md`
- Implementation summary:
  - Encoded the future report standard that combines V2-style HTML/data/image/table presentation with V1-style evidence-backed interpretation density.
  - Added table/image purpose and interpretation-reclaim requirements across workflow, template, style, payload, handoff, and image-generation docs.
  - Added success/failure/mixed-result driver-analysis rules and direct wording replacements for sentence-final `봅니다.`.
- Workflow docs updated:
  - `daily_report_workflow.md`, `DAILY_REPORT_TEMPLATE.md`, `DAILY_REPORT_STYLE.md`, `backtest_report_data_rules.md`, `agent_handoff_prompt.md`, and `image_generation_prompt.md`.
- Report artifacts preserved:
  - No `reports/` artifact, payload, PNG, or existing `report-ko.html` was edited by Task 328.
- Tests added or updated:
  - No unit/integration tests were required because no executable code changed.
- Tests run:
  - `rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다|함께 봅니다|같이 봅니다|볼 수 있다고 보는" docs/blog`
  - `rg -n "V2|V1|data display|데이터 표시|logic|논리|driver|success|failure|혼합|회수|chart_purposes|required_interpretive_takeaways|logic_chain" docs/blog/daily_report_workflow.md docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md docs/blog/backtest_report_data_rules.md docs/blog/agent_handoff_prompt.md docs/blog/image_generation_prompt.md`
  - `git diff --name-only -- reports`
  - `git diff --check`
  - `rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_328_DAILY_REPORT_DATA_RICH_LOGIC_DENSE_WORKFLOW_REVISION.md`
- Codex self-review result:
  - Scope respected. Only reusable report workflow docs and state/task files were changed.
  - No backtest, strategy/code change, DB mutation, report-artifact edit, frontend/backend change, live trading behavior, order/account/private endpoint behavior, secret, or `.env` change was introduced.
- Known limitations:
  - The current V2 report artifact was not regenerated. This task changes the future workflow only.
  - Existing dirty worktree items from earlier tasks remain outside this task's scope.
- Recommended next task:
  - If the owner wants the existing V2 report to reflect the revised standard, create a bounded task to regenerate or revise `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html` from the saved Task 326/327 payload and images using the Task 328 workflow.
