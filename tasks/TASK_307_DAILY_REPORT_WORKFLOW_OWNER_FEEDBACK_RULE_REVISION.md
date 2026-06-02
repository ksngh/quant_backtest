# Task 307: Daily Report Workflow Owner Feedback Rule Revision

# Goal

Update the reusable daily-report workflow, template, style, handoff prompt, and report rules so future blog reports follow the owner's feedback by default.

This task must update workflow/docs/rules only. It must not rewrite an existing report artifact.

# Source Requirement

Owner correction:

```text
리포트를 고치지말고, 그 워크플로를 고쳐달라는 얘기야 나는. docs와 md등등과 rule 등..
```

Owner follow-up:

```text
리포트 산출물이 html파일이어야 겠지. md파일이아니라.
```

Clean requirement:

- Do not fix the already generated report body as the primary deliverable.
- Fix the reusable workflow and documentation that generate future reports.
- Update `docs`, markdown templates, handoff prompts, and rules so the owner's report feedback is encoded once and reused.
- The final report artifact for future full-report workflows must be an HTML file, not a Markdown file.
- Use `report-ko.html` as the default Korean report output name unless the workflow docs explicitly choose a more specific HTML naming convention.
- Treat Markdown as optional intermediate scratch only when explicitly assigned; it must not be the default final report deliverable.
- Keep this task documentation-only unless a future assigned task explicitly asks to regenerate a report.

# Extracted Roles

- Owner role:
  - Wants future reports to be generated correctly from the workflow, not manually patched one at a time.
  - Wants the previous report feedback generalized into reusable writing and artifact-generation rules.
  - Wants report authors/agents to write a real publishable report from saved data and images, not just a rough draft or internal analysis.
  - Wants the report artifact to be HTML, not Markdown.
- Supporting roles:
  - Workflow maintainer role: update daily-report process docs.
  - Template/style role: update section names, opening rules, prohibited wording, and interpretation style.
  - HTML artifact role: make the future full-report output contract produce `report-ko.html`.
  - Handoff prompt role: update prompts given to future report-writing agents.
  - Data-integrity role: preserve rules that prohibit invented metrics, unsupported causes, internal task IDs, and unsafe trading claims.
  - State-tracking role: update project status files after execution.
- Forbidden roles:
  - Do not rewrite `reports/**/report-ko.md`.
  - Do not edit existing `reports/**/payload.json` unless a later assigned report-artifact task explicitly allows it.
  - Do not run a new backtest.
  - Do not regenerate images.
  - Do not change strategy/backtest code.
  - Do not mutate candle data or saved backtest DB records.
  - Do not add live trading behavior, exchange order/account/private endpoints, signed requests, secrets, or `.env` changes.

# Context

- Tasks 300, 303, and 304 updated parts of the daily-report workflow and copy style.
- Task 306 incorrectly targeted the existing Lookback Return Momentum report artifact instead of the reusable workflow/rules.
- The owner clarified that the desired change is to update `docs`, `.md` templates, prompts, and rules so future reports automatically follow the feedback.
- The owner also clarified that the future report output should be HTML rather than Markdown.
- `docs/blog/report_template.html` exists and should be treated as a layout/reading-flow reference for future report structure.
- This task should not undo or further modify the current report artifact. If the owner wants Task 306 report edits reverted, that should be a separate explicit task.

# Scope

- Read and update as needed:
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/template.md` if present. It is absent in the current tree and should not be created unless a future task asks for a separate legacy template file.
  - `docs/blog/image_generation_prompt.md` only if report-image wording creates conflicting public-report language.
  - `docs/blog/report_template.html` as read-only reference unless the task discovers the file itself needs documentation comments; default is no edit.
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

# Out of Scope

- Editing any existing `reports/blog_payloads/**/report-ko.md`.
- Editing any existing `reports/blog_payloads/**/payload.json`.
- Generating a new report artifact.
- Backtest execution or parameter search.
- Strategy document changes unless a workflow doc must point readers to the already existing strategy-doc requirement.
- Strategy/source/test code changes.
- Candle backfill or DB mutation.
- Image generation/regeneration.
- Frontend/backend/API changes.
- Live trading behavior, exchange order/account/private endpoints, signed requests, secrets, or `.env` changes.

# Requirements

- Encode the owner's feedback into reusable workflow docs, not a one-off report.
- Change the future full-report output contract from Markdown to HTML:
  - final Korean report artifact should be `report-ko.html`;
  - `report-ko.md` should not be generated as the default final report output;
  - if Markdown is ever used as an internal scratch/intermediate format, docs must clearly say it is not the deliverable;
  - generated HTML should use the reading flow and visual structure of `docs/blog/report_template.html`;
  - HTML image references should still point to same-folder PNG filenames unless a future task changes artifact layout.
- Future report generation rules must require:
  - The opening paragraph explains the strategy in plain language first.
  - The opening must not begin with a market/timeframe/cost-summary sentence such as `Binance BTCUSDT ...`.
  - Comparison labels should avoid awkward `기본값` wording unless the report is explicitly discussing defaults as a concept.
  - The report should not use `The kicker` framing.
  - The key-point section should explain the observed result at strategy level, not just repeat a narrow metric such as total transaction cost.
  - Interpretation must generalize correctly:
    - When results are positive, explain evidence-supported success drivers such as gross edge, win/loss structure, cost absorption, holding-period behavior, drawdown, and reward/risk.
    - When results are negative or cost-dominated, explain evidence-supported failure drivers such as gross-vs-net gap, churn, exit mix, cost drag, insufficient edge, and reward/risk geometry.
  - Report writers must not invent ATR, liquidation, delayed-exit, microstructure, behavioral, or regime explanations unless the saved data, strategy document, or cited source supports them.
  - `전략에 포함된 가정과 이론적 배경` must cover broader strategy-level theory and economic background, not only why a signal may occur.
  - Theory/background should explain:
    - why the strategy might have an edge;
    - what economic or behavioral mechanisms it assumes;
    - what market conditions make it work;
    - what conditions make it fail;
    - how signal speed, turnover, costs, and reward/risk interact.
  - Public-facing reports should not include obvious backtest disclaimers such as `연구용`, `가상 포지션`, or `실제 주문은 넣지 않았습니다`.
  - The reusable template should remove `주의해서 볼 점` as a default section.
  - The final interpretation section should be titled `해석`, not `해석과 다음 보완점`.
  - Avoid `첫째`, `둘째`, `셋째` enumeration in interpretation. Use `-` bullets.
  - Prefer closing wording like `보완점은 다음과 같다`, with a reason for each improvement.
  - Align report structure and visual flow with `docs/blog/report_template.html`, including clear lead text, compact tables, image placement, and readable section order.
  - Preserve existing rules that:
    - reports use saved payload values only;
    - missing values are not invented;
    - same-folder PNG references are used;
    - internal task/run IDs are not shown in public report text;
    - live trading or real order claims are not introduced.
- Update prompts and rule docs consistently so future agents do not receive conflicting instructions.
- If older docs intentionally mention draft behavior, clarify whether the full-report workflow should produce a publishable Korean report body rather than only a rough draft.
- Replace or supersede older `report-ko.md` references in workflow docs where they describe the final deliverable. Historical examples may remain only if clearly marked as legacy.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 307 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read relevant `docs/blog` workflow/template/style/rule files.
- [x] Read `docs/blog/report_template.html` as a layout/reading-flow reference.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 307 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Reusable daily-report docs encode the owner feedback without requiring manual one-off report rewrites.
- Reusable daily-report docs define `report-ko.html` as the final Korean report artifact for future full-report workflows.
- Reusable daily-report docs no longer define `report-ko.md` as the default final report deliverable.
- Future reports are instructed to open with a plain-language strategy explanation.
- Future reports are instructed to avoid awkward `기본값`, `The kicker`, `연구용`, `가상 포지션`, actual-order disclaimer, `주의해서 볼 점`, and `해석과 다음 보완점` wording.
- Future reports are instructed to write `해석` with evidence-supported success/failure drivers and `-` bullets.
- Future theory/background sections are instructed to cover broader strategy-level economic and behavioral assumptions, success conditions, failure conditions, and cost/reward-risk interactions.
- Workflow docs and handoff prompt no longer conflict with the owner feedback.
- `docs/blog/report_template.html` is used as the future HTML report layout/reading-flow reference.
- No existing report artifact or payload is modified by this task.
- No backtest, strategy/code change, DB mutation, image generation, live trading behavior, exchange endpoint behavior, secret, or `.env` change is performed.

# Required Tests

## Unit Tests

- Not required. This is a documentation workflow task.

## Integration Tests

- Not required unless the implementation adds an executable report-rendering utility, which is out of scope by default.

## Contract Tests

- Verify the expected docs mention the new report-writing requirements without keeping the old section labels:

```bash
rg -n "전략에 포함된 가정과 이론적 배경|해석|보완점은 다음과 같습니다|기본값|report-ko\\.html" docs/blog
! rg -n "The kicker|주의해서 볼 점|해석과 다음 보완점|실제 주문은 넣지 않았습니다|가상 포지션" docs/blog
```

- Verify the docs define HTML as the final report artifact and do not keep Markdown as the default final deliverable:

```bash
rg -n "report-ko\\.html|HTML|html" docs/blog
! rg -n "report-ko\\.md.*final|report-ko\\.md.*최종|최종.*report-ko\\.md|default.*report-ko\\.md|기본.*report-ko\\.md" docs/blog
```

- Verify existing report artifacts were not edited by this task:

```bash
git diff --name-only -- reports
```

The only acceptable output is unrelated pre-existing changes explicitly documented in the completion summary.

## Safety Tests

- Confirm no live-trading or secret-related workflow language was introduced:

```bash
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed order|order endpoint|account endpoint|real order execution" docs/blog
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- No report artifacts edited.
- No payload metrics changed.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.
- Workflow, template, style, and handoff docs are consistent with one another.
- Future full-report artifact is HTML, not Markdown.

# Verification

Recommended:

```bash
test -s docs/blog/report_template.html
rg -n "report-ko\\.html|HTML|html" docs/blog
! rg -n "report-ko\\.md.*final|report-ko\\.md.*최종|최종.*report-ko\\.md|default.*report-ko\\.md|기본.*report-ko\\.md" docs/blog
rg -n "Lookback Return Momentum|전략에 포함된 가정과 이론적 배경|보완점은 다음과 같|해석" docs/blog
! rg -n "The kicker|주의해서 볼 점|해석과 다음 보완점|실제 주문은 넣지 않았습니다|가상 포지션" docs/blog
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed order|order endpoint|account endpoint|real order execution" docs/blog
git diff --check -- docs/blog tasks/TASK_307_DAILY_REPORT_WORKFLOW_OWNER_FEEDBACK_RULE_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
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
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `tasks/TASK_307_DAILY_REPORT_WORKFLOW_OWNER_FEEDBACK_RULE_REVISION.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Updated the reusable daily-report workflow so future full-report output is `report-ko.html`, not Markdown.
  - Rewrote the template/style/handoff/data/image rules around `docs/blog/report_template.html` HTML structure.
  - Encoded owner feedback: strategy-first opening, no awkward default-value labels, no old English micro-headings, no default caution section, final `해석` section, evidence-supported success/failure interpretation, and stronger strategy-level theory/economic background.
  - Preserved rules against invented metrics, unsupported causes, internal task/run IDs, and unsafe trading claims.
- Tests added or updated:
  - None. This was a documentation workflow task.
- Tests run:
  - `test -s docs/blog/report_template.html`
  - `rg -n "report-ko\\.html|HTML|html" docs/blog`
  - `! rg -n "report-ko\\.md.*final|report-ko\\.md.*최종|최종.*report-ko\\.md|default.*report-ko\\.md|기본.*report-ko\\.md" docs/blog`
  - `rg -n "Lookback Return Momentum|전략에 포함된 가정과 이론적 배경|보완점은 다음과 같|해석" docs/blog`
  - `! rg -n "The kicker|주의해서 볼 점|해석과 다음 보완점|실제 주문은 넣지 않았습니다|가상 포지션" docs/blog`
  - `! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed order|order endpoint|account endpoint|real order execution" docs/blog`
  - `git diff --name-only -- reports`
  - `git diff --check -- docs/blog tasks/TASK_307_DAILY_REPORT_WORKFLOW_OWNER_FEEDBACK_RULE_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md`
- Codex self-review result:
  - Scope respected. No existing report artifact or payload was edited during Task 307.
  - No backtest, strategy/source/test code, DB, candle data, image generation, live-trading behavior, exchange endpoint behavior, secret, or `.env` change was introduced.
- Known limitations:
  - `docs/blog/template.md` is absent in the current tree, so it was not edited or recreated.
  - `git diff --name-only -- reports` still lists pre-existing report changes from prior tasks; Task 307 did not modify `reports/`.
- Recommended next task:
  - Create a separate task if the owner wants the existing Lookback report artifact converted from Markdown to `report-ko.html` using the revised workflow.
