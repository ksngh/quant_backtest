# Task 306: Lookback Momentum Report Owner Feedback HTML Template Revision

# Goal

Revise the existing `Lookback Return Momentum` Korean blog report using the owner feedback and the newly provided `docs/blog/report_template.html` layout/style reference.

This task is a report-writing task only. It must not run a new backtest, change strategy logic, regenerate metrics, or mutate saved backtest records.

# Source Requirement

Owner request:

```text
내가 너 리포트를 보고 피드백해줄테니까 이거 반영해주는 task만들어줘.
...
docs/blog/report_template.html 파일 넣어놨거든, 거기에 맞춰서 리포트 작성해줘
```

Clean requirement:

- Create a task to revise the current `Lookback Return Momentum` report based on owner feedback.
- Use `docs/blog/report_template.html` as the primary structure/style reference for the rewritten report.
- Rewrite the report body directly; do not create a planning draft as the final deliverable.
- Keep saved metrics and image references factual.
- Do not run new validations or change backtest/strategy code.

# Extracted Roles

- Owner role:
  - Wants the existing report revised for clearer framing, less awkward wording, and better explanation of the strategy's observed result.
  - Wants interpretation to generalize correctly: if the result is successful, explain the evidence-supported success drivers; if it fails, explain the evidence-supported failure drivers.
  - Wants the report aligned to `docs/blog/report_template.html`.
  - Wants fewer obvious disclaimers about backtesting/research and fewer "default value" labels.
  - Wants the strategy's theory and economic background strengthened, not only a generic explanation of why momentum exists.
- Supporting roles:
  - Report writer role: rewrite the Korean report body.
  - Data integrity role: preserve saved-result facts and avoid inventing unsupported success/failure causes.
  - Template role: read and follow `docs/blog/report_template.html`.
  - Status-tracking role: update state files after execution.
- Forbidden roles:
  - No strategy/backtest implementation.
  - No new backtest execution.
  - No parameter tuning/search.
  - No candle backfill or DB mutation.
  - No image generation/regeneration unless a broken reference requires a narrow repair.
  - No frontend/backend/API/dashboard changes.
  - No live trading behavior, exchange order/account/private endpoints, signed requests, secrets, or `.env` changes.

# Context

- Task 301 generated the first `Lookback Return Momentum V1` Korean report.
- Task 302 revised awkward "성과가 약하다" phrasing and Markdown readability.
- Task 304 rewrote the same report using the revised daily-report prompt/style guidance.
- The owner has now provided more specific report feedback and added `docs/blog/report_template.html`.
- Assumption for execution:
  - The target report is `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`.
  - `payload.json` in the same folder may be updated only if report-facing text fields must stay consistent with the rewritten report.
  - Existing PNG filenames and saved metrics must remain unchanged unless a broken Markdown reference is discovered.
- If the owner intended a different report than the existing `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`, stop after recording the ambiguity and ask for clarification before editing.

# Scope

- Read-only context:
  - `docs/blog/report_template.html`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`
- Allowed report artifacts:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json` only for matching report-facing text fields.
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

# Out of Scope

- New backtest execution.
- Task 305 result incorporation unless explicitly requested in a separate task.
- Parameter tuning or strategy revision.
- Strategy/source/test code changes.
- Saved-run DB mutation.
- Candle backfill.
- Image regeneration unless required to repair a broken reference.
- Creating a new report artifact folder unless the existing target is missing or the task is updated first.
- Adding generic disclaimers such as "연구용", "가상 포지션", or "실제 주문은 넣지 않았습니다".

# Requirements

- Read `docs/blog/report_template.html` before editing the report.
- Rewrite the report according to the owner feedback:
  - Remove the opening sentence that starts like `Binance BTCUSDT 1m / 15m 기본값 비교...`.
  - Replace the opening with a short plain-language explanation of what `Lookback Return Momentum` is.
  - Remove awkward "기본값" wording from comparison labels such as `1m 기본값`.
  - Avoid using `기본값` where it is not necessary.
  - Revise the core-point section currently titled or framed like `The kicker`.
  - Make the key point explain the strategy's observed result, not just a narrow detail such as total USDT cost.
  - If the saved result is positive, explain the likely success drivers using saved evidence such as gross edge, win/loss structure, cost absorption, holding-period behavior, and drawdown.
  - If the saved result is negative or cost-dominated, explain the likely failure drivers using saved evidence such as gross-vs-net gap, reward/risk geometry, churn, exit mix, cost drag, or insufficient edge after costs.
  - Explain that a useful positive gross signal still needs enough planned reward/risk after costs, but do not force that sentence to be the only key point if the data indicates a different primary driver.
  - Do not invent ATR, liquidation, delayed-exit, microstructure, or behavioral explanations unless supported by the available saved report data, strategy document, or clearly cited external background.
  - Expand "전략에 포함된 가정과 이론적 배경" with a deeper explanation of the strategy's theory and economic background.
  - The theory section should cover why this strategy might have an edge, what economic/behavioral mechanisms it assumes, what market condition would make it work, and what condition would make it fail.
  - For `Lookback Return Momentum`, this can include recent return continuation, order-flow imbalance, delayed information incorporation, herding/feedback trading, stop/forced-flow effects, and the tradeoff between signal speed, turnover, and transaction costs.
  - Include references if useful, but keep them readable and not academic-heavy. If exact citation details are needed, verify them before use.
  - Do not include phrases like `연구용 가상 포지션`, `연구용`, or `실제 주문은 넣지 않았습니다`.
  - Remove the section `주의해서 볼 점`.
  - Rename `해석과 다음 보완점` to `해석`.
  - In `해석`, avoid `연구용` wording.
  - Remove the sentence: `이 리포트는 전략 채택 판단이 아니라, 다음 실험에서 무엇을 줄이고 무엇을 추가할지 정리하기 위한 연구용 기록입니다.`
  - Replace `첫째`, `둘째`, `셋째`-style enumeration with simple `-` bullets.
  - Prefer wording like `보완점은 다음과 같다` over `다음 실험에서는`, and include the reason for each listed improvement.
  - Align the report's structure and visual reading flow with `docs/blog/report_template.html`.
- Preserve:
  - Saved metrics.
  - Existing same-folder image references.
  - Existing payload image filename semantics.
  - No internal task/run identifiers in the public-facing report unless already required by the artifact contract.
- If `payload.json` is edited, do not change saved numerical metrics. Only update report-facing narrative fields to match the rewritten report.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 306 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read `docs/blog/report_template.html`.
- [x] Read required daily-report workflow/style/data docs.
- [x] Read the target report and payload.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 306 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- The report opens with a concise explanation of `Lookback Return Momentum`, not a market/timeframe/cost sentence.
- The report does not use `기본값` in comparison labels or other awkward places.
- The main interpretation explains the strategy's observed outcome using evidence-supported success or failure drivers, not only a narrow metric such as total USDT cost.
- The theoretical-background section gives a stronger strategy-level theoretical and economic explanation, not only a generic momentum-occurrence explanation.
- The report does not include `연구용`, `가상 포지션`, or `실제 주문은 넣지 않았습니다`.
- The `주의해서 볼 점` section is removed.
- The section formerly framed as `해석과 다음 보완점` is titled `해석`.
- The final interpretation uses `-` bullets, not `첫째/둘째/셋째`.
- The ending uses `보완점은 다음과 같다` style and explains why each improvement matters.
- The report follows `docs/blog/report_template.html` closely enough that the layout can be migrated to that HTML structure later.
- Existing saved metrics and image references remain factual.
- No new backtest, strategy change, DB mutation, or image generation is performed.

# Required Tests

## Unit Tests

- Not required unless implementation introduces a reusable report-rendering utility, which is out of scope by default.

## Integration Tests

- Not required for a markdown-only report rewrite.

## Contract Tests

- Verify `payload.json` remains valid if changed:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null
```

- Verify same-folder PNG references remain and no `images/` subfolder references are introduced:

```bash
rg -n "\./[A-Za-z0-9_\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
! rg -n "\./images/|images/" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
```

- Verify forbidden report phrasing is absent:

```bash
! rg -n "기본값|연구용|가상 포지션|실제 주문은 넣지 않았습니다|주의해서 볼 점|해석과 다음 보완점|첫째|둘째|셋째|이 리포트는 전략 채택 판단이 아니라" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
```

## Safety Tests

- Confirm no live-trading or secret-related wording/behavior was introduced:

```bash
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed|order endpoint|account endpoint" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- No saved metrics changed.
- No image filename semantics changed.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.
- Owner feedback items were all addressed or explicitly documented if not applicable.

# Verification

Recommended:

```bash
test -s docs/blog/report_template.html
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null
rg -n "\./[A-Za-z0-9_\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
! rg -n "\./images/|images/" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json
! rg -n "기본값|연구용|가상 포지션|실제 주문은 넣지 않았습니다|주의해서 볼 점|해석과 다음 보완점|첫째|둘째|셋째|이 리포트는 전략 채택 판단이 아니라" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md
git diff --check -- reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528 tasks/TASK_306_LOOKBACK_MOMENTUM_REPORT_OWNER_FEEDBACK_HTML_TEMPLATE_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
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
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
  - `tasks/TASK_306_LOOKBACK_MOMENTUM_REPORT_OWNER_FEEDBACK_HTML_TEMPLATE_REVISION.md`
- Implementation summary:
  - Rewrote the target Korean report so it opens with a plain-language `Lookback Return Momentum` explanation.
  - Removed awkward `기본값`, `연구용`, `가상 포지션`, actual-order disclaimer, `주의해서 볼 점`, and `해석과 다음 보완점` wording from the report.
  - Strengthened the strategy-level theoretical/economic background and explained the observed negative result through saved gross-vs-net PnL, exit mix, turnover, cost drag, and reward/risk evidence.
  - Updated only matching report-facing payload narrative fields; saved metrics and image filenames were not changed.
- Tests added or updated:
  - None. This was a markdown/payload narrative revision only.
- Tests run:
  - `test -s docs/blog/report_template.html`
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null`
  - `rg -n "\./[A-Za-z0-9_\-]+\.png" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `! rg -n "\./images/|images/" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `! rg -n "기본값|연구용|가상 포지션|실제 주문은 넣지 않았습니다|주의해서 볼 점|해석과 다음 보완점|첫째|둘째|셋째|이 리포트는 전략 채택 판단이 아니라" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`
  - `! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed|order endpoint|account endpoint" reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
  - `git diff --check -- reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528 tasks/TASK_306_LOOKBACK_MOMENTUM_REPORT_OWNER_FEEDBACK_HTML_TEMPLATE_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md`
- Codex self-review result:
  - Scope respected; no backtest, strategy/code, DB, image-generation, frontend/backend/API, live-trading, exchange endpoint, secret, or `.env` change was introduced.
  - No saved numerical metrics or image filename semantics were changed.
- Known limitations:
  - The report still reflects the existing 2026-05-20~2026-05-28 artifact only; Task 305's separate three-month cost-aware validation is not incorporated by this task.
- Recommended next task:
  - Create a separate blog-report task if the owner wants a new report based on Task 305's three-month cost-aware `1m`/`5m`/`15m` validation.
