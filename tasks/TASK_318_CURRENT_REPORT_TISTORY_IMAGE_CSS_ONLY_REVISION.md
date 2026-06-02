# Task 318: CURRENT_REPORT_TISTORY_IMAGE_CSS_ONLY_REVISION

# Goal

Update only the current Lookback Return Momentum report's HTML/CSS so the already-generated report artifact reflects the recently completed Task 317 Tistory `.section-image` behavior, without changing report text, metrics, images, payload data, strategy logic, or reusable workflow documents.

# Source Requirement

Owner request on 2026-06-02:

> 현재 리포트에 css쪽만 수정해주라, 방금작업한 태스크 내용반영해서

Interpreted as: apply the Task 317 image-wrapper/full-width Tistory CSS behavior to the current report artifact only. Because Task 317 explicitly excluded existing `reports/**` artifact edits and is already completed, this task exists as a separate bounded implementation task before any current-report CSS modification.

# Extracted Roles

- Owner role:
  - Publishes the current daily report on Tistory.
  - Wants the current report CSS to reflect the just-completed Task 317 image-wrapper behavior.
  - Requests CSS-only changes.
- Supporting roles:
  - Current report artifact maintainer: update only the internal CSS of the current `report-ko.html` artifact so `.section-image` wrappers and Tistory image placeholders fill the report content width.
  - Verification role: confirm only CSS-related report changes are made and no report facts, images, metrics, payload data, strategy logic, or reusable docs are changed.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Reusable workflow/template/document editor for this task.
  - Image generator.
  - Report narrative/copy editor except if required to preserve valid HTML around CSS-only edits.
  - Database mutator.
  - Candle backfill runner.
  - Frontend/backend/API implementer.
  - Live trader.
  - Real Binance order executor.

# Context

Task 317 updated reusable `docs/blog` workflow/template/style/handoff/data/image rules and `docs/blog/report_template.html` so future reports support Tistory image placeholders inside full-width `.section-image` wrappers and omit standalone hypothesis sections by default.

Task 317 deliberately did not edit existing report artifacts. The current report artifact that should receive the CSS-only follow-up is:

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`

The matching current artifact folder also contains `payload.json` and PNG images, but those files are out of scope for this CSS-only task.

# Scope

- Read required state files and this task before implementation.
- Read the current report artifact:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
- Read `docs/blog/report_template.html` only as the Task 317 CSS reference.
- Modify only CSS inside the current report artifact as needed to reflect Task 317's Tistory image behavior:
  - `.section-image` uses the available report content width.
  - direct `img` elements inside `.section-image` fill the section width without unexpected shrinkage.
  - common Tistory-generated figure/image wrappers inside `.section-image` fill the section width.
  - Tistory placeholder output such as `[##_Image|...|alignCenter|width="100%"|_##]` remains compatible with the wrapper.
  - margins/padding do not prevent the image area from visually filling the content column.
  - captions remain readable and separate from the image wrapper.
- Update state files after execution.

# Out of Scope

- Editing any current report text, headings, interpretation, metrics, table values, image references, or payload values.
- Editing `payload.json`.
- Editing or regenerating PNG files.
- Editing `report-ko.md` or any other report artifact.
- Editing reusable `docs/blog` workflow/template/style/handoff/data/image rules.
- Running or changing any backtest.
- Parameter tuning/search.
- Strategy logic changes.
- Strategy document changes.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Dashboard, FastAPI, Streamlit, scheduler, Docker, machine learning, futures, leverage, or portfolio optimization work.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Do not hardcode any real Tistory `kage@...` image identifier.
- Keep changes CSS-only inside the target `report-ko.html` artifact.
- Preserve the existing hELLO layout and current report dimensions, including the centered `.report-page` and `--page-max-width: 1120px` unless a narrow CSS compatibility adjustment is explicitly necessary.
- The target report must support this owner-side replacement shape without causing the image to appear narrow:

```html
<div class="section-image">
  [##_Image|...|alignCenter|width="100%"|_##]
</div>
```

- If the existing report already has local image preview `<img>` tags, keep them functional and full-width.
- Do not change the report's narrative or remove/add sections in this task, even though Task 317 changed future workflow guidance around standalone hypothesis sections.

# Status Tracking

## Before Implementation

- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read the current target report artifact.
- [x] Read `docs/blog/report_template.html` as the Task 317 CSS reference.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- The current target report artifact's CSS reflects Task 317's full-width `.section-image` / Tistory-placeholder behavior.
- Only CSS inside `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html` is changed for the report artifact.
- `payload.json` and PNG artifacts remain unchanged.
- Reusable `docs/blog` documents and templates remain unchanged in this task.
- No report metrics, narrative, headings, image file references, or strategy/backtest facts are changed.
- No new backtest, DB mutation, strategy/code change, candle backfill, live trading behavior, order/account/private endpoint usage, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required; this is a CSS-only artifact task.

## Integration Tests

- Not required unless implementation creates or changes executable code, which is out of scope.

## Contract Tests

Run:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null
```

Verify Task 317-compatible CSS selectors exist in the current report:

```bash
rg -n "section-image|figure|imageblock|tt_article_useless_p_margin|width: 100%|max-width: 100%" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
```

Verify the diff is limited to the target report CSS plus mandatory state/task tracking files:

```bash
git diff --name-only
```

Run whitespace/diff validation:

```bash
git diff --check
```

## Safety Tests

Run:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_318_CURRENT_REPORT_TISTORY_IMAGE_CSS_ONLY_REVISION.md
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
- Current report CSS updated only after this task is assigned for implementation.

# Verification

Default:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null
rg -n "section-image|figure|imageblock|tt_article_useless_p_margin|width: 100%|max-width: 100%" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html
git diff --name-only
git diff --check
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_318_CURRENT_REPORT_TISTORY_IMAGE_CSS_ONLY_REVISION.md
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
  - `tasks/TASK_318_CURRENT_REPORT_TISTORY_IMAGE_CSS_ONLY_REVISION.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Added the Task 317 `.section-image` full-width CSS rules to the current report artifact.
  - Kept the change CSS-only inside the target report artifact; no report narrative, metrics, image references, payload values, or PNG files were changed.
  - Preserved the existing hELLO layout and `--page-max-width: 1120px`.
- Tests added or updated:
  - No automated tests were added; this is a CSS-only report artifact task.
- Tests run:
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null`
  - `rg -n "section-image|figure|imageblock|tt_article_useless_p_margin|width: 100%|max-width: 100%" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
  - `git diff --name-only`
  - `git diff --check`
  - `rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_318_CURRENT_REPORT_TISTORY_IMAGE_CSS_ONLY_REVISION.md`
- Codex self-review result:
  - Scope respected; the report artifact change was CSS-only and limited to the assigned current report.
  - No backtest, strategy/code, DB, image-generation, reusable-doc, live-trading, exchange-order, secret, or `.env` behavior was introduced.
- Known limitations:
  - Visual verification in the actual Tistory editor still requires owner-side paste/reinsert review because Tistory may wrap image tokens differently after upload.
- Recommended next task:
  - Owner review of the current report in Tistory after manually reinserting images; create a separate task only if Tistory emits an additional wrapper shape that needs CSS coverage.
