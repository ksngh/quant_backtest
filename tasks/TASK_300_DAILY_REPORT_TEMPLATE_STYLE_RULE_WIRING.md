# Task 300: Daily Report Template and Style Rule Wiring

# Goal

Update the daily-report rules so any future request to write a daily report uses:

- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/image_generation_prompt.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/agent_handoff_prompt.md`

This task is documentation/workflow wiring only. It must not generate a report, run a backtest, create payloads, or generate images.

# Source Requirement

Owner request:

```text
그리고 그걸로 데일리리포트 써달라고 하면, docs/blog/daily_report_template이랑 daily_report_style보고 작성하는것좀 rule에 추가해주는 task를 만들어줄래? 물론 그리고 daily report workflow랑 image generation도 같이 따라야 할테구.
```

Clean requirement:

- Create a task to add explicit daily-report routing rules.
- When the owner asks for a daily report from a strategy/backtest result, Codex must read the daily report template and style docs before writing.
- The workflow must also follow the existing daily report workflow, image-generation rules, payload/data rules, and agent handoff prompt.
- Fix stale references if current docs still point to the older `docs/blog/template.md` name.

# Extracted Roles

- Owner role:
  - Wants daily report writing to consistently use the current template/style docs and image workflow.
- Supporting roles:
  - Documentation workflow role: update the daily-report rule docs.
  - Report-writing role: define required read order before `report-ko.md` creation.
  - Image workflow role: ensure image generation still follows `docs/blog/image_generation_prompt.md`.
  - Payload role: preserve `docs/blog/backtest_report_data_rules.md` as the payload contract.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.
- Forbidden roles:
  - No report generation.
  - No payload generation.
  - No image generation.
  - No backtest execution.
  - No strategy/model implementation.
  - No DB mutation.
  - No frontend/backend/API change.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No secrets or `.env` changes.

# Context

- Task 289 created the initial daily-report workflow docs.
- Tasks 290-295 evolved payload/image/report-draft rules.
- Current docs include `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md`.
- Some existing docs may still reference the older `docs/blog/template.md` name. This task should reconcile those references if they are stale.
- Task 299 was created to validate `LOOKBACK_RETURN_MOMENTUM`. If the owner later asks for a daily report from Task 299 results, this workflow should govern that report-writing request.

# Scope

- Inspect and update only relevant documentation:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - optionally `docs/10_CODEX_COMMAND_GUIDE.md` if needed for owner command routing
- Add an explicit rule:
  - For daily report writing requests, read `DAILY_REPORT_TEMPLATE.md` and `DAILY_REPORT_STYLE.md` before drafting `report-ko.md`.
  - Use `DAILY_REPORT_TEMPLATE.md` for section structure.
  - Use `DAILY_REPORT_STYLE.md` for tone, forbidden expressions, internal-term conversion, and interpretation style.
  - Use `daily_report_workflow.md` for routing/order of operations.
  - Use `image_generation_prompt.md` for required PNG creation rules.
  - Use `backtest_report_data_rules.md` for payload structure.
  - Use `agent_handoff_prompt.md` when handing payload/images to a writing agent.
- Update stale references from `docs/blog/template.md` to `docs/blog/DAILY_REPORT_TEMPLATE.md` where appropriate.
- Preserve the colocated `payload.json`/PNG/`report-ko.md` workflow unless the owner separately requests a different artifact layout.

# Out of Scope

- No actual daily report creation.
- No report-ko.md generation.
- No payload.json generation.
- No PNG/image generation.
- No image-plan file creation.
- No backtest execution.
- No strategy validation execution.
- No strategy/model/backtest code changes.
- No market-data backfill.
- No database writes.
- No dashboard/frontend/backend/API changes.
- No live trading behavior.
- No exchange order/account/private endpoint behavior.
- No secrets or `.env` changes.

# Requirements

- Daily-report docs must clearly state the required read order for report-writing requests.
- `DAILY_REPORT_TEMPLATE.md` must be named as the canonical report structure source.
- `DAILY_REPORT_STYLE.md` must be named as the canonical writing style source.
- `daily_report_workflow.md` must remain the routing/workflow source.
- `image_generation_prompt.md` must remain the image-generation source.
- `backtest_report_data_rules.md` must remain the payload/data source.
- `agent_handoff_prompt.md` must be updated if it still references the old template path.
- The rule must apply whether the report is for `LOOKBACK_RETURN_MOMENTUM` or any other strategy.
- The docs must continue to forbid inventing missing payload values.
- The docs must continue to forbid task/run/internal IDs in public report-facing files.
- The docs must continue to require same-folder image references and no default `images/` subfolder, unless a later task explicitly changes that contract.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 300 is the assigned task.
- [x] Read this task file before documentation changes.
- [x] Read relevant daily-report docs before editing.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 300 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Daily-report workflow docs explicitly require reading `DAILY_REPORT_TEMPLATE.md` before writing `report-ko.md`.
- Daily-report workflow docs explicitly require reading `DAILY_REPORT_STYLE.md` before writing `report-ko.md`.
- Image-generation rules remain linked from the daily-report workflow.
- Payload/data rules remain linked from the daily-report workflow.
- Agent handoff prompt references the canonical template/style docs.
- Stale `docs/blog/template.md` references are removed or corrected where they refer to the canonical daily report template.
- No report, payload, image, backtest, DB mutation, or strategy code change is performed.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Not applicable; documentation-only task.

## Integration Tests

- Not applicable; documentation-only task.

## Contract Tests

- Search confirms canonical docs are referenced:

```bash
rg -n "DAILY_REPORT_TEMPLATE|DAILY_REPORT_STYLE|daily_report_workflow|image_generation_prompt|backtest_report_data_rules|agent_handoff_prompt" docs/blog docs/10_CODEX_COMMAND_GUIDE.md
```

- Search confirms stale canonical-template references are corrected:

```bash
rg -n "docs/blog/template.md|`template.md`" docs/blog docs/10_CODEX_COMMAND_GUIDE.md
```

Any remaining match must be intentionally documented as legacy context, not active workflow guidance.

## Safety Tests

- Confirm documentation-only change does not add live trading behavior, exchange endpoints, secrets, or `.env` guidance.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Documentation points to the correct canonical files.
- No report generation.
- No payload generation.
- No image generation.
- No backtest execution.
- No strategy/code change.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.

# Verification

Recommended:

```bash
git diff --check -- docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
rg -n "DAILY_REPORT_TEMPLATE|DAILY_REPORT_STYLE|daily_report_workflow|image_generation_prompt|backtest_report_data_rules|agent_handoff_prompt" docs/blog docs/10_CODEX_COMMAND_GUIDE.md
rg -n "docs/blog/template.md|`template.md`" docs/blog docs/10_CODEX_COMMAND_GUIDE.md
rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md
```

Verification result (2026-05-31):

- `git diff --check -- docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md STATUS.md PROJECT_HISTORY.md BACKLOG.md` passed with no output.
- `rg -n "DAILY_REPORT_TEMPLATE|DAILY_REPORT_STYLE|daily_report_workflow|image_generation_prompt|backtest_report_data_rules|agent_handoff_prompt" docs/blog docs/10_CODEX_COMMAND_GUIDE.md` returned the expected canonical doc references.
- ``rg -n 'docs/blog/template\.md|`template\.md`' docs/blog docs/10_CODEX_COMMAND_GUIDE.md`` returned no active workflow matches.
- `rg -n '\./images/' docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/daily_report_workflow.md docs/blog/backtest_report_data_rules.md docs/blog/agent_handoff_prompt.md docs/blog/image_generation_prompt.md docs/10_CODEX_COMMAND_GUIDE.md` returned no matches.
- `rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md` returned only existing safety-boundary/forbidden-scope text, not new live-trading behavior.

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

Completed on 2026-05-31.

Files changed:

- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/image_generation_prompt.md`
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `STATUS.md`
- `PROJECT_HISTORY.md`
- `BACKLOG.md`
- `tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md`

Implementation summary:

- Added explicit daily-report writing rules that require reading `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md` before drafting `report-ko.md`.
- Kept `daily_report_workflow.md`, `image_generation_prompt.md`, `backtest_report_data_rules.md`, and `agent_handoff_prompt.md` as the routing/image/data/handoff sources.
- Replaced active stale `docs/blog/template.md` guidance in daily-report workflow docs with the canonical template/style docs.
- Updated the canonical template image examples and markdown references to same-folder `./[filename].png` paths with no default `images/` subfolder.
- Updated project state files to record Task 300 completion and leave the next task owner-assigned.

Tests added or updated:

- None. This was a documentation-only workflow wiring task.

Tests run:

- `git diff --check -- docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md STATUS.md PROJECT_HISTORY.md BACKLOG.md`
- `rg -n "DAILY_REPORT_TEMPLATE|DAILY_REPORT_STYLE|daily_report_workflow|image_generation_prompt|backtest_report_data_rules|agent_handoff_prompt" docs/blog docs/10_CODEX_COMMAND_GUIDE.md`
- ``rg -n 'docs/blog/template\.md|`template\.md`' docs/blog docs/10_CODEX_COMMAND_GUIDE.md``
- `rg -n '\./images/' docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/daily_report_workflow.md docs/blog/backtest_report_data_rules.md docs/blog/agent_handoff_prompt.md docs/blog/image_generation_prompt.md docs/10_CODEX_COMMAND_GUIDE.md`
- `rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" docs/blog docs/10_CODEX_COMMAND_GUIDE.md tasks/TASK_300_DAILY_REPORT_TEMPLATE_STYLE_RULE_WIRING.md`

Codex self-review result:

- Passed. The task stayed documentation-only, updated the required state files, did not run backtests, did not generate reports/payloads/images, did not mutate the DB, did not change strategy/backend/frontend code, and did not add live trading behavior, exchange order/account endpoint behavior, secrets, or `.env` changes.

Known limitations:

- No actual `report-ko.md`, payload, or PNG was generated because this task explicitly excluded artifact creation.
- Existing historical ledger/task references to older `docs/blog/template.md` remain as historical context outside active workflow guidance.

Recommended next task:

- Owner should assign the next task explicitly. Candidate directions are report-draft generation, bounded `5m` candle backfill, locked OOS diagnostics for `LOOKBACK_RETURN_MOMENTUM`, or Task 288 model development.
