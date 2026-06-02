# Task Template

# Goal

Revise the reusable daily-report generation workflow, templates, style rules, payload rules, and strategy-document guidance so future Tistory blog reports are generated with clearer strategy-level framing, better HTML layout, stronger theoretical grounding, and more readable section/table/list behavior.

This task must update the report-generation workflow and rules. It must not directly rewrite an existing report artifact.

# Source Requirement

Owner request:

> 하기전에 리포트 스타일을 고쳐줘. 리포트를 직접 고치는게 아니라, 리포트를 생성할때의 워크플로를 고치는 게 목적이야. 그러니까 template이나 rule을 수정해달라는 소리야. 필요한 payload와 사전 작업 워크플로를 고쳐도 괜찮고.
>
> 나는 구체적인 내용을 말할건데, 너는 추상화 해서 알아들어야해. 그리고 tistory에 쓸 블로그 글이야.

Specific owner examples to abstract into reusable rules:

- Default HTML design target should be `1392 * 708`, while still responsive.
- Report titles should avoid overly granular experiment phrases such as `낮은 진입 기준 비교`. Use the strategy name/version as the default title, and only add a concise mechanism/version-basis phrase when necessary.
- The subtitle/lead should describe the strategy itself, not the latest experiment action. For Lookback Return Momentum, an acceptable stable description is `과거 일정 구간의 수익률을 확인하는 모멘텀 전략`.
- When the strategy version changes, the core summary should explain what changed between versions, such as fixed `R` reward/risk versus ATR-based reward/risk.
- Tables are useful, but they must stay readable and have clear purpose. Overly large or semantically ambiguous tables should be split or reduced.
- Hypothesis sections should visibly use bullet items. If bullets are already present, CSS must make them visible and readable.
- Theoretical/economic background must be more concrete and reference-backed. Strategy-document creation/update workflow should require rationale and references, and report-generation workflow should pull from that source.
- Fold `전략규칙` into `전략에 포함된 가정과 이론적 배경` rather than rendering it as a separate default report section.
- Preserve the current `백테스트 설정` section behavior and structure.
- Every proposed improvement should explain why that improvement follows from the result.
- Avoid awkward Korean wording, especially `그것은`.
- No further result-specific feedback can be encoded from the current failed experiment because the experiment did not produce enough filled-trade evidence.

# Extracted Roles

- Owner role: defines report-quality expectations and Tistory publishing constraints.
- Supporting roles:
  - Blog workflow maintainer: updates `docs/blog` generation workflow and style rules.
  - HTML template maintainer: updates `docs/blog/report_template.html` or the corresponding HTML layout guidance.
  - Payload/data-rule maintainer: updates report payload requirements if a new field is needed for stable strategy descriptions, version-change summaries, table intent, or references.
  - Strategy-document workflow maintainer: updates strategy-document rules so future strategy docs include stronger theory/rationale/reference material that reports can reuse.
- Forbidden roles:
  - One-off report artifact editor.
  - Backtest runner.
  - Strategy implementation editor.
  - Live trader or exchange executor.

# Context

Tasks 303 and 307 already revised daily-report workflow docs to improve Korean report interpretation and switch final full-report output to `report-ko.html`. Task 308 generated a Lookback Return Momentum daily report, and the owner identified remaining workflow/style issues. The target is not the generated Task 308 report itself; the target is the reusable report creation system used for future Tistory posts.

Task 309 remains created but not executed. The owner asked to fix the report workflow before proceeding with that ATR strategy task.

# Scope

- Read the required state files and this task before any implementation.
- Inspect the current report workflow/template/style sources before editing. Relevant files are expected to include:
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html`
  - `docs/strategy/README.md`
  - `docs/strategy/STRATEGY_TEMPLATE.md`
- Update only reusable workflow/template/style/data-rule/strategy-document guidance files needed to satisfy the requirements.
- Make the report-generation workflow explicitly target Tistory blog posts.
- Define a primary desktop composition target of `1392px * 708px` for the initial viewport/readability check, while requiring responsive behavior for narrower and wider screens.
- Define report title rules:
  - Default to strategy family/name plus version, for example `Lookback Return Momentum V1`.
  - Avoid granular experiment labels in the main title, such as `낮은 진입 기준 비교`.
  - Allow only concise mechanism/version-basis phrases when needed, for example `ATR 기준 수정`.
- Define lead/subtitle rules:
  - Use stable strategy-level descriptions sourced from the strategy document.
  - Do not describe the one-off experiment action as the report lead.
  - Keep the lead short enough for title-adjacent placement in the HTML template.
- Define `핵심요약` rules:
  - If the report covers a new or changed version, include a compact version-change summary.
  - Compare prior and current mechanics in plain terms, such as fixed `R` reward/risk versus ATR-based reward/risk.
  - Keep result interpretation separate from version-change explanation.
- Preserve the existing `백테스트 설정` section structure and current good behavior.
- Merge `전략규칙` into `전략에 포함된 가정과 이론적 배경` as a default report-structure rule.
- Strengthen theory/reference rules:
  - Strategy docs must explain why the strategy might work, what market mechanism it assumes, when it may fail, and what references support the reasoning.
  - Report workflow must use this strategy-doc material instead of inventing shallow theory during report writing.
  - If references are missing, the workflow must require adding them to the strategy document before generating a full report for that strategy.
- Update list/bullet styling guidance so hypothesis bullets are visibly rendered in the HTML output.
- Update table guidance:
  - Keep tables for dense metrics.
  - Require a clear table purpose.
  - Limit overly wide or ambiguous tables; split them into smaller tables or move secondary metrics to prose/cards when needed.
  - Ensure tables remain readable in the `1392px * 708px` target and responsive on mobile/Tistory widths.
- Update improvement/next-step wording rules so every proposed change explains why the result supports it.
- Add Korean wording rules that prohibit awkward phrases such as `그것은` in final report copy.
- If payload schema/rules are touched, document any new required or recommended fields without mutating existing report payload artifacts.

# Out of Scope

- Directly editing existing `reports/**/report-ko.html`, `reports/**/report-ko.md`, `reports/**/payload.json`, or image artifacts.
- Running or changing any backtest.
- Changing strategy implementation code.
- Changing `LOOKBACK_RETURN_MOMENTUM` logic or executing Task 309.
- Generating a new daily report artifact.
- Frontend/backend/API changes.
- Live trading, real exchange order execution, signed requests, private endpoints, API keys, secrets, or `.env` changes.

# Requirements

- The task must abstract the owner's concrete examples into reusable report-generation rules, not hardcode rules only for Task 308.
- The workflow must distinguish:
  - strategy identity/title,
  - stable strategy description,
  - version or mechanism changes,
  - experiment-specific validation details,
  - observed results and interpretation.
- Future report writers must be guided to avoid experiment-specific clutter in the title and lead.
- Future report writers must be guided to explain strategy version changes in the core summary when relevant.
- Future report writers must be guided to source theory and references from strategy docs.
- Strategy-document creation/update rules must require theoretical/economic rationale and references before a full blog report is generated.
- The HTML template/style guidance must support:
  - `1392px * 708px` primary desktop review target,
  - responsive layout,
  - readable bullets,
  - readable tables,
  - Tistory-friendly standalone HTML/CSS.
- Keep the current `백테스트 설정` report section intact unless a narrow styling change is required for responsiveness.
- Do not add result-specific claims about the current failed experiment beyond reusable workflow examples.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read the relevant `docs/blog` workflow/template/style/data-rule files.
- [x] Read `docs/strategy/README.md` and `docs/strategy/STRATEGY_TEMPLATE.md` before changing strategy-document workflow rules.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- Reusable daily-report workflow docs now state that Tistory report output is HTML-first and reviewed against a `1392px * 708px` primary desktop target plus responsive layouts.
- `docs/blog/report_template.html` or the relevant template/style docs include clear layout/style rules for readable bullets and tables.
- Report title rules prevent granular experiment labels as the default main title.
- Lead/subtitle rules require stable strategy-level descriptions instead of one-off experiment summaries.
- `핵심요약` rules require version-change summaries when the strategy version or mechanism changes.
- `전략규칙` is no longer a default standalone report section; its content is folded into `전략에 포함된 가정과 이론적 배경`.
- The strategy-document workflow requires concrete theory/economic rationale and references sufficient for future report generation.
- Table rules preserve useful metric tables while limiting overly wide or ambiguous tables.
- Improvement/next-step rules require explanation of why each proposed change follows from the observed result.
- Korean style rules prohibit awkward phrasing such as `그것은`.
- Existing report artifacts are not edited.
- Task 309 remains unexecuted.

# Required Tests

## Unit Tests

- Not required unless a structured report-generation script or schema validator is changed.

## Integration Tests

- Not required unless a report-generation script is changed.

## Contract Tests

- Verify the updated docs contain the required workflow rules:

```bash
rg -n "1392|708|Tistory|티스토리|전략규칙|그것은|핵심요약|레퍼런스|reference|references|version|버전" docs/blog docs/strategy
```

- Verify existing report artifacts were not modified by this task:

```bash
git diff --name-only -- reports
```

## Safety Tests

- Confirm no live trading, exchange endpoint, secret, or `.env` behavior is introduced.
- Run whitespace verification:

```bash
git diff --check
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
- Existing report artifacts untouched.
- Task 309 not executed.

# Verification

Default:

```bash
rg -n "1392|708|Tistory|티스토리|전략규칙|그것은|핵심요약|레퍼런스|reference|references|version|버전" docs/blog docs/strategy
git diff --name-only -- reports
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

- Files changed: `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/daily_report_workflow.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, `docs/blog/image_generation_prompt.md`, `docs/blog/report_template.html`, `docs/strategy/README.md`, `docs/strategy/STRATEGY_TEMPLATE.md`, and project state files.
- Implementation summary: updated reusable Tistory report-generation rules for `1392px * 708px` primary review, responsive HTML, strategy/version-centered titles, stable strategy descriptions, version-change summaries, visible bullets, purposeful tables, stronger strategy-document theory/reference requirements, folded strategy rules into the theory/background section, reasoned improvements, and prohibited awkward `그것은` wording.
- Tests added or updated: none; documentation-only task.
- Tests run: required `rg` contract check, `git diff --name-only -- reports`, and `git diff --check`.
- Codex self-review result: passed; scope stayed limited to docs/workflow and state tracking, with no report artifact edits by this task, no backtest, no strategy implementation, no live trading behavior, no secrets, and no exchange endpoint behavior.
- Known limitations: `git diff --name-only -- reports` still lists pre-existing dirty report artifacts from earlier tasks; Task 310 did not edit those files.
- Recommended next task: execute Task 309 `LOOKBACK_RETURN_MOMENTUM_ATR_RISK_EXIT_REVISION`.
