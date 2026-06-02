# Task 319: DAILY_REPORT_REPRESENTATIVE_TRADE_DIAGNOSTIC_WORKFLOW_REVISION

# Goal

Revise the reusable Korean daily-report workflow so every future `대표 거래` section explains the selected trade as an integrated diagnostic narrative, while avoiding a checklist-like table of contents or separate subheadings for each diagnostic question.

# Source Requirement

Owner request on 2026-06-02:

> 대표 거래에는 다음과 같은 내용이 포함되어야 하는데, 다음 리스트들을 목차로 따로 만들지말고, 그냥 내용만 하위에 포함되게끔 만들어줘야해.
>
> 왜 그 거래가 발생했는가
> 진입 조건이 정상적으로 작동했는가
> 청산 조건이 의도대로 작동했는가
> 수익/손실이 전략의 논리에서 나온 것인가, 우연한 변동성에서 나온 것인가
> 이 거래가 전체 성과를 왜곡하고 있는가
> 같은 유형의 거래가 반복적으로 나타나는가
> 백테스트 엔진이나 체결 로직 버그 가능성은 없는가

Interpreted as: create a bounded future documentation/workflow task. The implementation should update reusable report-generation guidance so the above points are always covered inside the `대표 거래` narrative, not rendered as standalone headings, a separate table of contents, or a visible checklist.

# Extracted Roles

- Owner role:
  - Defines the report-quality requirement for representative trade explanations.
  - Wants richer trade diagnostics without making the section feel like a mechanical checklist.
- Supporting roles:
  - Daily-report workflow maintainer: update reusable `docs/blog` workflow/template/style/handoff/data-rule documents.
  - Report narrative designer: describe how to fold diagnostic questions into natural Korean paragraphs, bullets, captions, or callouts.
  - Verification role: confirm future guidance requires all diagnostic points while explicitly forbidding separate diagnostic-question headings.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Existing report artifact regenerator.
  - Current report narrative editor unless a separate current-artifact task is assigned.
  - Image generator.
  - Database mutator.
  - Candle backfill runner.
  - Frontend/backend/API implementer.
  - Live trader or real Binance order executor.

# Context

Recent report workflow tasks refined Tistory publishing, image handling, and interpretation style:

- Task 303 moved future reports toward interpretation-centered Korean narratives.
- Task 313 established hELLO-skin layout and interpretation-boundary rules.
- Task 315 added representative trade chart context-window and image QA rules.
- Task 317 removed standalone hypothesis sections and added Tistory image-placeholder workflow.
- Task 318 applied CSS-only `.section-image` behavior to the current report artifact.

This task should only create the future workflow change for representative trade explanations. It must not run a new backtest or revise the current report artifact unless the owner separately assigns that artifact update.

# Scope

- Read required state files and this task before implementation.
- Read current reusable daily-report docs/template before editing:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html` only if representative-trade HTML structure guidance needs a small wording update.
- Update reusable report workflow guidance so future `대표 거래` sections include, in natural prose or compact integrated bullets:
  - why the trade happened;
  - whether the entry condition operated normally;
  - whether the exit condition operated as intended;
  - whether profit/loss appears strategy-driven or more likely random volatility/noise;
  - whether the trade materially distorts overall performance;
  - whether similar trade types recur across the backtest;
  - whether there is any plausible backtest-engine, fill-logic, or execution-sequencing bug signal.
- Require the section to integrate those points into the trade narrative instead of creating a visible table of contents or standalone headings named after each question.
- Add guidance for graceful handling of unavailable evidence:
  - If the saved payload lacks enough data to answer a point, the report must say so briefly and avoid inventing facts.
  - If a point requires aggregate trade-pattern evidence that is absent, classify it as a limitation or recommended next diagnostic.
- Update state files after execution.

# Out of Scope

- Editing existing `reports/**/report-ko.html`, `reports/**/report-ko.md`, `reports/**/payload.json`, or PNG artifacts.
- Regenerating current report images.
- Running, changing, or tuning any backtest.
- Strategy logic changes.
- Strategy document changes unless a separate assigned strategy task requires them.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Dashboard, FastAPI, Streamlit, scheduler, Docker, machine learning, futures, leverage, or portfolio optimization work.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- The future workflow must explicitly say that the diagnostic prompts are writer obligations, not visible subsection titles.
- The report should read like a trade story plus diagnostic interpretation, for example:
  - setup context before entry;
  - trigger and fill explanation;
  - exit path and realized result;
  - interpretation of whether the trade reflects the strategy thesis;
  - contribution to total performance;
  - recurrence/bug-check note if supported by data.
- The workflow must prohibit shallow statements such as `진입 조건은 정상 작동했다` unless the report points to the concrete evidence available in payload/run outputs.
- The workflow must distinguish:
  - single-trade chart evidence;
  - aggregate recurrence evidence;
  - engine/fill sanity checks;
  - unavailable evidence that should be labeled as a limitation.
- The workflow must preserve research-only framing and must not imply live-trading readiness from one representative trade.
- If example Korean phrasing is added, it must be generic and reusable, not tied to a hardcoded saved run unless clearly labeled as an example.

# Status Tracking

## Before Implementation

- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Read this task.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm this is documentation/workflow work only, not a report-regeneration task.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Reusable daily-report docs require future representative trade sections to cover all seven owner-specified diagnostic points.
- The docs explicitly state that those seven points must not become separate visible headings, a table of contents, or a mechanical checklist in the final report.
- The docs provide natural Korean narrative guidance for integrating the points inside the `대표 거래` section.
- The docs explain how to handle missing evidence without hallucinating unsupported trade diagnostics.
- Existing report artifacts, payloads, images, backtests, strategy/code, database records, live trading behavior, exchange endpoints, secrets, and `.env` files remain unchanged.

# Required Tests

## Unit Tests

- Not required; this is a reusable documentation/workflow task.

## Integration Tests

- Not required unless implementation changes executable code, which is out of scope.

## Contract Tests

Run documentation checks:

```bash
rg -n "대표 거래|진입 조건|청산 조건|전체 성과|체결 로직|백테스트 엔진|목차|체크리스트" docs/blog
```

Run diff validation:

```bash
git diff --name-only
git diff --check
```

## Safety Tests

Run:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_319_DAILY_REPORT_REPRESENTATIVE_TRADE_DIAGNOSTIC_WORKFLOW_REVISION.md
```

Expected: no unsafe live-trading/order/secret behavior is introduced; declarative safety text in task/state files is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Diagnostic prompts integrated into narrative guidance, not converted into report headings.

# Verification

Default:

```bash
rg -n "대표 거래|진입 조건|청산 조건|전체 성과|체결 로직|백테스트 엔진|목차|체크리스트" docs/blog
git diff --name-only
git diff --check
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_319_DAILY_REPORT_REPRESENTATIVE_TRADE_DIAGNOSTIC_WORKFLOW_REVISION.md
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

# Completion Summary (2026-06-02)

- Files changed: `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/daily_report_workflow.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/agent_handoff_prompt.md`, `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, and this task file.
- Implementation summary: updated reusable daily-report guidance so future `대표 거래` sections cover the seven owner diagnostic points inside natural trade narratives, not as visible headings, a table of contents, or a checklist.
- Tests added or updated: none; documentation/workflow task only.
- Tests run: required docs `rg`, `git diff --check`, safety grep, and self-review.
- Codex self-review result: scope respected; no current report artifacts, images, backtests, strategy/code, DB records, live trading behavior, exchange endpoints, secrets, or `.env` files were changed.
- Known limitations: existing reports were not regenerated; future reports must have enough trade-level and aggregate data to answer recurrence and engine/fill sanity points.
- Recommended next task: execute Task 320, then Task 321, if not already completed in the same owner-assigned batch.
