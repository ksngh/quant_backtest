# Task 295: Report Draft and Pre-Backtest Strategy Doc Rules

# Goal

Update project rules so daily-report generation includes a Korean report draft, and require a strategy information document before any future strategy/model backtest execution.

This task exists because the owner clarified that payload and chart images alone are not enough: Codex should also draft the report, and every model/backtest request should first have a strategy markdown file under a dedicated docs strategy directory.

# Source Requirement

Owner request:

```text
이거보니까 느낀게... report의 초안을 너가 작성하긴 해야겠다.
다시 report 초안 만드는걸로 rule좀 바꿔줘.
그리고 어떤 작업하기전에, model에대해서 정보를 미리 작성해야하는 것도 rule에 추가해줘.
그러니까, docs에다가 strategy 디렉토리 만들고 어떤 백테스트를 해달라는 시행 전에 strategy md파일을 강제해야하는 rule을 agents.md에 추가하라는 소리야.
```

Clean requirement:

- Change the report workflow again so report generation creates a Korean draft report, not only `payload.json` and PNG files.
- Keep payload and PNG images as required inputs/artifacts, but add a draft markdown report step.
- Add a strategy documentation rule before any strategy/model backtest run.
- Create a dedicated strategy-doc directory under `docs/`.
- Define a required strategy markdown format for model/strategy information.
- Update `AGENTS.md` so agents must create/read the relevant strategy markdown file before implementing, running, or modifying a backtest strategy/model.
- Do not execute a new backtest in this task.
- Do not mutate saved backtest DB records.
- Do not create live-trading behavior.

# Extracted Roles

- Owner role:
  - Decides that daily reports need a readable draft, not only data payloads and images.
  - Decides that strategy/model information must be documented before a backtest is run.
- Supporting roles:
  - Workflow-rule updater: update blog/report docs to include draft report generation.
  - Strategy-doc contract updater: add a required strategy markdown format and directory.
  - Project-rule updater: update `AGENTS.md` with the pre-backtest strategy-doc gate.
  - Validator: verify docs and rules agree.
- Forbidden roles:
  - No new strategy development.
  - No new backtest execution.
  - No payload/image regeneration unless explicitly included by a later task.
  - No DB mutation.
  - No live trading.
  - No exchange order/account/private endpoint usage.
  - No secrets, API keys, `.env`, frontend, backend, dashboard, or scheduler changes.

# Context

Task 294 changed the daily-report artifact workflow so the generated artifact folder contains only:

```text
payload.json
*.png
```

The owner has now corrected the workflow again. The payload and image files remain useful, but the report workflow should also produce a Korean report draft. The draft should use the saved payload and colocated image files, and should be clearly treated as a draft that a human can edit.

The owner also wants a stronger pre-backtest discipline: before any model/strategy backtest is requested or executed, Codex must document the model's logic, market rationale, risk assumptions, cost assumptions, expected failure modes, and validation plan in a strategy markdown file under `docs/strategy/`.

# Scope

Allowed files:

- `AGENTS.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/template.md`
- `docs/blog/image_generation_prompt.md` if its role needs clarification.
- New `docs/strategy/` directory.
- New strategy document template, for example `docs/strategy/STRATEGY_TEMPLATE.md`.
- Optional strategy workflow document, for example `docs/strategy/README.md`.
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

Allowed actions:

- Update report rules so a Korean draft markdown report is generated from payload/images.
- Define where the draft report should live.
- Define whether generated image references remain colocated.
- Define that `payload.json`, generated PNGs, and report draft must remain consistent.
- Add `docs/strategy/` and a reusable strategy markdown template.
- Add an `AGENTS.md` rule requiring the relevant strategy markdown file before any backtest/model implementation or execution.
- Add validation checks for the new docs/rules.

# Out of Scope

- Do not execute a new backtest.
- Do not regenerate the Task 294 payload or images unless a later task explicitly requests it.
- Do not write a full report draft for the Task 294 artifact unless a later task explicitly requests it.
- Do not implement a new model or strategy.
- Do not modify strategy/backtest engine code.
- Do not mutate DB records.
- Do not add frontend/backend/API/dashboard behavior.
- Do not add live trading, real order execution, signed exchange requests, API keys, secrets, or `.env` files.

# Requirements

## Report Draft Workflow

- Update the daily-report rules so the normal report workflow produces:

```text
[report-folder]/
  payload.json
  report-ko.md
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
  [optional additional PNGs]
```

- `report-ko.md` must be a Korean draft report, written in honorific tone.
- The draft should be generated from `payload.json` and colocated image filenames only.
- Markdown image references should use same-folder relative paths:

```text
./summary_equity_curve.png
./cost_impact.png
./representative_win_trade.png
./representative_loss_trade.png
```

- Do not require `report-en.md` unless explicitly requested by a later task.
- Do not require `image_plan.md` or `image_plan.json` unless a later task explicitly reinstates it.
- Do not require an `images/` subdirectory for this workflow.
- The draft must not expose task number, run id, internal candidate id, DB dump, source file paths, git commit, secrets, or config dumps.
- The draft must mark missing payload values as `[확인 필요]` instead of inventing them.
- The draft must avoid overstating research-only or failed strategies as deployable.

## Pre-Backtest Strategy Documentation Gate

- Create `docs/strategy/`.
- Add a strategy markdown template under `docs/strategy/`.
- The template must require at least:
  - strategy name.
  - strategy version.
  - market/symbol/timeframe.
  - market phenomenon and economic/microstructure rationale.
  - hypothesis.
  - factors and indicators.
  - entry logic.
  - exit logic.
  - stop loss logic.
  - take profit logic.
  - position sizing.
  - fee/spread/slippage assumptions.
  - intrabar execution assumptions.
  - look-ahead prevention rules.
  - expected win rate / expected R / break-even logic.
  - expected failure regimes.
  - overfitting risks.
  - validation windows.
  - minimum trade-count expectations.
  - required saved-run/report artifacts.
  - research-only/live-trading boundary.

- Update `AGENTS.md` so backtest/research tasks must:
  - find and read the relevant strategy markdown file before implementation or execution.
  - create/update the relevant strategy markdown file first and stop if it does not exist.
  - not run a backtest, implement a model, or tune parameters until the strategy document exists.
  - keep strategy docs under `docs/strategy/`.
  - update the strategy document if implementation changes the model logic, risk logic, cost logic, execution assumptions, or validation plan.

## Consistency Requirements

- Blog/report docs must agree with `AGENTS.md`.
- The strategy-doc gate must not bypass the existing `task.md` gate.
- The required order should be:

```text
state files -> relevant task.md -> relevant docs/strategy/*.md -> implementation/backtest/report generation
```

- If no task exists, agents still create/update only the task first and stop.
- If a task exists but no strategy document exists for a requested backtest/model, agents create/update only the strategy document and stop.
- If both task and strategy document exist, agents may execute only the assigned task scope.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 295 is the assigned task.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm Task 295 supersedes the Task 294 "payload/images only" rule for future full report-generation workflows.
- [x] Record assumptions, blockers, or unclear status items before editing docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a Task 295 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Implementation Notes

- Updated `AGENTS.md` so strategy/model/backtest implementation, tuning, validation, or reportable research runs require a relevant `docs/strategy/*.md` after the assigned task file and before execution.
- Added `docs/strategy/README.md` to document the required order:

```text
state files -> relevant task.md -> relevant docs/strategy/*.md -> implementation/backtest/report generation
```

- Added `docs/strategy/STRATEGY_TEMPLATE.md` with required sections for market rationale, hypothesis, factors, entry/exit, risk, costs, expected value, validation plan, failure modes, artifacts, and safety boundary.
- Updated blog/report docs so full report workflows produce `payload.json`, colocated PNGs, and `report-ko.md` in the same artifact folder.
- Kept image references same-folder relative paths such as `./summary_equity_curve.png`.
- Kept `report-en.md`, `image_plan.md`, `image_plan.json`, and `images/` out of the default workflow.
- Clarified that the chart-generation prompt creates PNGs only; `report-ko.md` is created by the report-writing step.
- No backtest was executed.
- No DB mutation was performed.
- No strategy/backtest code was changed.
- No live trading, exchange order/account endpoint, secret, or `.env` behavior was added.

# Verification Results

Passed:

```bash
test -d docs/strategy
test -f docs/strategy/STRATEGY_TEMPLATE.md
test -f docs/strategy/README.md
rg -n "docs/strategy|strategy markdown|전략 문서|pre-backtest|백테스트.*전" AGENTS.md docs/strategy docs/blog
rg -n "report-ko.md|초안|draft|payload.json|summary_equity_curve.png" docs/blog AGENTS.md docs/strategy
rg -n "\./images|daily_report/YYYY-MM-DD|image_plan.md|image_plan.json|report-en.md" docs/blog AGENTS.md docs/strategy
git diff --check -- AGENTS.md docs/blog/backtest_report_data_rules.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/template.md docs/blog/image_generation_prompt.md docs/strategy/README.md docs/strategy/STRATEGY_TEMPLATE.md
```

Notes:

- The third `rg` command returned no `./images` or `daily_report/YYYY-MM-DD` matches.
- `report-en.md`, `image_plan.md`, and `image_plan.json` matches remain only in "not generated by default" or image-generation role-boundary contexts.

# Acceptance Criteria

- `AGENTS.md` requires a relevant `docs/strategy/*.md` before any strategy/model backtest implementation or execution.
- `docs/strategy/` exists.
- A reusable strategy markdown template exists under `docs/strategy/`.
- Blog/report docs require `report-ko.md` draft generation for full report workflows.
- Blog/report docs still require payload and chart images as report inputs/artifacts.
- Blog/report docs use same-folder image references, not `./images/...`.
- Blog/report docs do not require `report-en.md`, `image_plan.md`, `image_plan.json`, or `images/` by default.
- The new strategy-doc gate does not weaken the existing task/state workflow gate.
- No backtest is executed.
- No DB mutation is performed.
- No live trading, exchange order/account endpoint, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required if only documentation and rule files are changed.

## Integration Tests

- Verify `docs/strategy/` exists.
- Verify strategy template exists.
- Verify `AGENTS.md` contains the pre-backtest strategy-doc gate.
- Verify report workflow docs mention `report-ko.md` draft generation.

## Contract Tests

- Verify docs do not require `./images/` for current report markdown image references.
- Verify docs do not require default `report-en.md`, `image_plan.md`, or `image_plan.json`.
- Verify docs describe same-folder `payload.json`, `report-ko.md`, and PNGs.
- Verify docs specify missing payload values should be marked `[확인 필요]`.

## Safety Tests

- Confirm no `.env`, API key, private key, DB dump, CSV dump, or secret file is created.
- Confirm no strategy/backtest code is changed.
- Confirm no exchange order/account/private endpoint behavior is added.
- Confirm no DB mutation command is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
test -d docs/strategy
test -f docs/strategy/STRATEGY_TEMPLATE.md
rg -n "docs/strategy|strategy markdown|전략 문서|pre-backtest|백테스트.*전" AGENTS.md
rg -n "report-ko.md|초안|draft|payload.json|summary_equity_curve.png" docs/blog
rg -n "\./images|daily_report/YYYY-MM-DD|image_plan.md|image_plan.json|report-en.md" docs/blog AGENTS.md
git diff --check
```

Expected note:

- `rg` matches for `image_plan.md`, `image_plan.json`, and `report-en.md` are acceptable only when the docs explicitly say they are not created by default.

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
