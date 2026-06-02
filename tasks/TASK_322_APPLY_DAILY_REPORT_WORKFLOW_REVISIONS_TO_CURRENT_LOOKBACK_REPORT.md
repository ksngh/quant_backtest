# Task 322: APPLY_DAILY_REPORT_WORKFLOW_REVISIONS_TO_CURRENT_LOOKBACK_REPORT

# Goal

Regenerate or revise the current `Lookback Return Momentum V1` Tistory HTML report artifact so it reflects the completed Task 319-321 daily-report workflow rules.

The target report is:

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`

# Source Requirement

Owner request:

> ㅇㅇ 리포트에 적용하는 task

Interpreted as: create a bounded execution task, not execute it yet, that applies the newly completed reusable workflow revisions to the existing current report artifact. The relevant workflow revisions are:

- Task 319: representative-trade diagnostic narrative depth.
- Task 320: backtest-setting algorithm and pseudocode explanation.
- Task 321: strategy assumption and theory/background depth.

# Extracted Roles

- Owner role:
  - Wants the current report artifact to reflect the latest report-writing workflow.
  - Wants the application to be a concrete report rewrite/regeneration task, not another workflow-doc revision.
- Supporting roles:
  - Report artifact maintainer: revise the current `report-ko.html` and, only if needed for consistency, report-facing narrative fields in colocated `payload.json`.
  - Workflow follower: read and apply the current `docs/blog` template/style/workflow/data/image/handoff rules.
  - Strategy-context reader: read the relevant strategy document and saved Task 311/312/314/316 context before rewriting.
- Forbidden roles:
  - Strategy/backtest implementer.
  - Backtest runner or parameter tuner.
  - Database mutator.
  - Candle backfill executor.
  - Reusable workflow/template editor, unless a narrow broken-reference fix is explicitly discovered and recorded.
  - Live trading or exchange-order executor.

# Context

Tasks 319-321 updated reusable `docs/blog` guidance but deliberately did not rewrite existing report artifacts.

The current report artifact already exists from Tasks 312, 314, 316, and 318:

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/summary_equity_curve.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/cost_impact.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/reward_cost_geometry.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/accepted_entries_by_variant.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_win_trade.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_loss_trade.png`

This task should apply the latest workflow rules to the current report text and HTML structure while preserving saved Task 311 facts.

# Scope

- Read required state files and this task file before execution.
- Read the current report workflow/style/template/data/image/handoff docs:
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html`
- Read the relevant strategy document before report rewriting:
  - `docs/strategy/lookback_return_momentum_v1.md`
- Read saved-result context:
  - `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`
  - `reports/task_311_atr_reward_cost_geometry_raw_outputs/manifest.json`
  - existing target `payload.json`
  - existing target `report-ko.html`
- Revise only the current artifact files needed for the report update:
  - `report-ko.html`
  - `payload.json` only for report-facing narrative fields if needed to match the rewritten report.
- Preserve current colocated PNG filenames and same-folder image references unless a broken reference is found.
- Keep the report Tistory hELLO-compatible with the existing `1120px` centered `.report-page` layout and full-width image behavior.

# Out of Scope

- Running new backtests.
- Parameter tuning or post-result search.
- Changing strategy, backtest, market-data, persistence, backend, frontend, or execution code.
- Changing cost assumptions, strategy logic, risk logic, or saved-run metrics.
- Mutating the database.
- Backfilling candle data.
- Regenerating PNGs unless an existing image is missing, broken, or no longer matches its current file reference.
- Editing reusable `docs/blog` workflow/template/style/handoff/data/image docs.
- Editing other report artifacts outside the target folder.
- Adding live trading behavior, exchange order/account/private endpoint calls, secrets, or `.env` changes.

# Requirements

- Apply Task 319 representative-trade guidance:
  - `대표 거래` must explain, in natural report prose, why the trade happened.
  - It must connect entry and exit to the saved strategy rules where evidence exists.
  - It must distinguish strategy-driven PnL from volatility-driven or mechanically delayed outcomes where the saved context supports that interpretation.
  - It must address whether the representative trade distorts the overall result or whether aggregate evidence is insufficient.
  - It must address whether similar trade types recur, or state that saved aggregate evidence is insufficient.
  - It must mention backtest engine/fill-logic bug signals only if concrete saved evidence supports it.
  - Do not expose these diagnostic prompts as visible headings, a table of contents, or a checklist.
- Apply Task 320 backtest-setting guidance:
  - `백테스트 설정` must explain the tested algorithm, not only list parameters.
  - Include concise explanatory pseudocode or Python-style snippets for the material rules.
  - Cover Lookback Return Momentum entry logic, ATR calculation/use, no-lookahead completed-candle indexing, indicator warm-up/input window, fill timing, cost gate, and stop/target/time-exit behavior as relevant to the saved report.
  - Clearly distinguish explanatory pseudocode from exact implementation quotation. If exact source-derived code is used, provide only a short source reference.
- Apply Task 321 theory/background guidance:
  - `전략에 포함된 가정과 이론적 배경` must explain assumptions, mechanisms, success conditions, failure conditions, cost/reward-risk implications, evidence boundaries, and optional concise formulas.
  - For momentum, include mechanism-level discussion where supported by the strategy document: underreaction/정보 반영 지연, slow position adjustment, risk premium/tail risk, hedger/speculator structure where relevant, and spot Bitcoin caveats.
  - Do not merely list academic references.
  - Do not imply the current bounded backtest proves or disproves the broader momentum strategy family.
- Preserve the current report's bounded conclusion:
  - The tested `Lookback Return Momentum V1` configuration is difficult to view as effective after costs under the tested conditions.
  - This is not enough by itself to reject momentum strategies in general.
  - Explain why broader rejection remains premature using evidence boundaries: implementation version, symbol, time window, timeframe set, cost assumptions, missing filters/confirmations, and validation coverage.
- Keep existing owner wording rules:
  - Avoid `기본값` unless literally necessary.
  - Avoid `그것은`.
  - Avoid `The setup`, `The numbers`, `The kicker`.
  - Avoid `실제 주문`, `연구용`, `가상 포지션`, and obvious backtest disclaimers.
  - Avoid `더 강한 결론` and `강한 결론`.
- Preserve saved numerical facts:
  - Metrics must match saved Task 311 outputs and existing manifest/payload.
  - Do not alter numerical metrics unless a mismatch with saved Task 311 data is found and documented.
  - If `payload.json` is edited, update only report-facing narrative fields unless a saved-data mismatch is explicitly verified.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Read the target report artifact and saved-result context.
- [x] Read the current `docs/blog` workflow/template/style/data/image/handoff docs.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if this task was completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `report-ko.html` is revised in place under the target folder.
- The report remains a single-file Tistory hELLO-compatible HTML artifact with internal CSS.
- The report keeps `--page-max-width: 1120px`, `.report-page`, mobile-safe width, left-first tables, and full-width image behavior.
- `백테스트 설정` includes algorithm mechanics and concise explanatory pseudocode for the material strategy rules.
- `전략에 포함된 가정과 이론적 배경` explains mechanism-level theory, assumptions, failure modes, optional formulas, and evidence boundaries.
- `대표 거래` includes integrated diagnostic interpretation without visible diagnostic headings/checklists.
- The `해석` section preserves the bounded conclusion and explains why rejecting momentum generally would be premature.
- Existing PNG references remain same-folder relative references and still point to existing non-empty files.
- Saved Task 311 numerical metrics are preserved.
- No strategy/backtest/code/DB/live-trading changes are introduced.

# Required Tests

## Unit Tests

- Not required; report artifact rewrite only.

## Integration Tests

- Not required unless implementation introduces a script or helper, which this task should avoid by default.

## Contract Tests

Verify Tistory hELLO layout contract:

```bash
rg -n -- "--page-max-width: 1120px|\\.report-page|width: calc\\(100% - 32px\\)|max-width: var\\(--page-max-width\\)" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Verify Task 319 representative-trade content exists and is not exposed as diagnostic headings:

```bash
rg -n "대표 거래|진입|청산|변동성|전체 성과|반복|체결|엔진" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
rg -n "<h[23][^>]*>(진입 조건|청산 조건|버그 가능성|체결 로직|백테스트 엔진|체크리스트)" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Expected: first command has relevant matches; second command has no matches.

Verify Task 320 backtest-setting algorithm explanation:

```bash
rg -n "백테스트 설정|lookback_return|ATR|true_range|explanatory pseudocode|의사코드|완료봉|no-lookahead|warm-up|cost gate|손절|익절|시간 청산" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Verify Task 321 theory/background depth:

```bash
rg -n "전략에 포함된 가정|이론적 배경|과소반응|정보 반영|느린 포지션|리스크 프리미엄|tail risk|헤저|투기자|Bitcoin|증거 범위|수학식|기각" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Verify discouraged wording is absent:

```bash
rg -n "그것은|The setup|The numbers|The kicker|기본값|실제 주문|연구용|가상 포지션|더 강한 결론|강한 결론" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Expected: no matches unless a match appears only inside a quoted verification note, which should not be present in the final report.

Verify artifact references and formatting:

```bash
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/summary_equity_curve.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/cost_impact.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/reward_cost_geometry.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/accepted_entries_by_variant.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_win_trade.png
test -s reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_loss_trade.png
git diff --check -- reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json
```

## Safety Tests

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_322_APPLY_DAILY_REPORT_WORKFLOW_REVISIONS_TO_CURRENT_LOOKBACK_REPORT.md
```

Expected: no unsafe live-trading/order/secret behavior is introduced; declarative safety text in task/state files is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- Saved Task 311 metrics preserved.
- No current report image regeneration unless explicitly justified.
- No reusable workflow docs edited.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint behavior.
- No unnecessary abstractions.

# Verification

Default:

```bash
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
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
  - `tasks/TASK_322_APPLY_DAILY_REPORT_WORKFLOW_REVISIONS_TO_CURRENT_LOOKBACK_REPORT.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Revised the current Tistory HTML report in place to apply Task 319-321 workflow rules.
  - Removed the standalone `가설` section and folded tested assumptions into the theory/background and interpretation narrative.
  - Expanded `전략에 포함된 가정과 이론적 배경` with mechanism-level momentum rationale, references, success/failure conditions, formulas, and evidence boundaries.
  - Expanded `백테스트 설정` with explanatory pseudocode for lookback return, ATR, no-lookahead/warm-up behavior, fill timing, stop/target/time exit, and cost gate logic.
  - Expanded `대표 거래` with integrated diagnostic interpretation of why the win/loss trades occurred, why the representative win does not represent aggregate performance, recurrence evidence, and saved-field engine/fill sanity.
  - Preserved the bounded `해석` conclusion that this V1 configuration is ineffective after costs in the tested conditions, while not rejecting momentum strategies generally.
  - Preserved saved Task 311 metrics, colocated PNG filenames, and same-folder image references. `payload.json` was not edited because no report-facing saved-data mismatch required it.
- Tests added or updated:
  - None. This was a report artifact rewrite only.
- Tests run:
  - Tistory hELLO layout contract grep.
  - Representative-trade content grep and diagnostic-heading absence grep.
  - Backtest-setting algorithm/pseudocode content grep.
  - Theory/background depth grep.
  - Discouraged-wording absence grep.
  - Existing PNG non-empty checks.
  - Report/payload safety grep for live-trading/order/secret markers.
  - Trailing-whitespace grep for touched files.
  - `git diff --check`.
- Codex self-review result:
  - Scope respected. No backtest, strategy/code, DB, reusable workflow docs, payload metrics, image regeneration, live trading behavior, exchange endpoints, secrets, or `.env` changes were introduced.
- Known limitations:
  - No browser visual screenshot was run; verification used HTML contract/content checks and existing PNG existence checks.
- Recommended next task:
  - No automatic next task is set. The next step is owner review of the revised report or a PR request for the accumulated completed work.
