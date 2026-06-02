# Task 317: TISTORY_IMAGE_EMBED_AND_HYPOTHESIS_OMISSION_WORKFLOW_REVISION

# Goal

Revise the reusable daily-report workflow and Tistory HTML/CSS rules so future report images can be reinserted by the owner using Tistory image placeholders inside a full-width `.section-image` wrapper, and so future daily reports do not include a separate `가설` / hypothesis section by default.

# Source Requirement

Owner request on 2026-06-02:

> 데일리 리포트는 티스토리에 글을 올릴 거란 말이야. 그래서 이미지가
> `<div class="section-image"> [##_Image|...|alignCenter|width="100%"|_##] </div>`
> 이런식으로 들어가야 하는게 좋아보여. 어차피 이미지는 내가 다시 삽입해야해. 저 이미지는 예시일 뿐이니까 css 구조를 다시 짜줘. 지금은 왜냐면 이미지가 꽉 안차 저렇게 하면.
>
> 그리고 리포트에 가설 부분은 작성하지 않는쪽으로 워크플로를 수정해줘
>
> 위에 해당하는 내용들을 task로 작성해줘

Interpreted as: create a bounded future implementation task, not execute it immediately, that updates reusable `docs/blog` report-generation docs/template/CSS for Tistory publishing. The example Tistory image token is only a placeholder shape; future reports should not hardcode that exact image ID.

# Extracted Roles

- Owner role:
  - Publishes daily reports to Tistory and will manually reinsert images in the Tistory editor.
  - Requests a full-width image wrapper compatible with Tistory `[##_Image|...|width="100%"|_##]` placeholders.
  - Requests removal of the separate report `가설` / hypothesis section from the default workflow.
- Supporting roles:
  - Tistory template maintainer: update reusable HTML/CSS structure so `.section-image` fills the report content width when Tistory image placeholders are inserted.
  - Daily-report workflow maintainer: update template/style/workflow/handoff/data-rule docs so generated reports do not create a standalone hypothesis section by default.
  - Verification role: confirm docs and template contain the new Tistory placeholder/full-width image rules and no default hypothesis-section requirement remains.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Strategy-document editor unless a narrow read-only cross-reference is needed.
  - Existing report artifact regenerator.
  - Image generator.
  - Database mutator.
  - Candle backfill runner.
  - Frontend/backend/API implementer.
  - Live trader.
  - Real Binance order executor.

# Context

Recent daily-report tasks established reusable Tistory hELLO workflow rules and report artifacts:

- Task 313 updated hELLO-skin layout and full-width image guidance.
- Task 315 updated consistent image-generation and no-crop image rules.
- Task 316 regenerated current report images and copy wording.

The owner now clarified that final publication occurs in Tistory, where images are manually reinserted as Tistory placeholders such as:

```html
<div class="section-image">
  [##_Image|kage@example/example/placeholder/img.png|alignCenter|width="100%"|_##]
</div>
```

The exact image token is not stable and must not be hardcoded. The reusable template/CSS should instead make the wrapper and any Tistory-generated image markup fill the report body width.

# Scope

- Read required state files and this task before implementation.
- Read current reusable daily-report docs/template before editing:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html`
- Update reusable docs/template only as needed to support:
  - Tistory image-placeholder insertion inside `<div class="section-image">...</div>`.
  - Full-width image display for Tistory placeholder output when the owner replaces local image references in the editor.
  - Clear guidance that report HTML should use placeholder-friendly wrappers and not rely only on local `./image.png` tags as the final Tistory paste format.
  - Removal of a standalone `가설`, `검증 가설`, `실험 가설`, or hypothesis section from the default report structure.
- Update `docs/blog/report_template.html` CSS if needed so:
  - `.section-image` uses the available report content width.
  - images, Tistory image containers, or generated figures inside `.section-image` use `width: 100%` / `max-width: 100%` and do not shrink unexpectedly.
  - default margins/padding do not prevent the image area from visually filling the content column.
  - captions remain readable and separate from the image token/wrapper.
- Update state files after execution.

# Out of Scope

- Editing existing `reports/**/report-ko.html`, `reports/**/report-ko.md`, `reports/**/payload.json`, or PNG artifacts.
- Regenerating current report images.
- Running or changing any backtest.
- Parameter tuning/search.
- Strategy logic changes.
- Strategy document changes, except read-only review if explicitly needed.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Dashboard, FastAPI, Streamlit, scheduler, Docker, machine learning, futures, leverage, or portfolio optimization work.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Treat the owner-provided Tistory image token as an example only; do not copy its concrete `kage@...` identifier into reusable docs except as an obviously fake placeholder.
- Future report HTML guidance must support this shape:

```html
<div class="section-image">
  [##_Image|...|alignCenter|width="100%"|_##]
</div>
```

- The `.section-image` CSS/template guidance must make inserted images fill the report content width in the Tistory hELLO context.
- The workflow must explicitly say that the owner may replace local image tags or placeholders with Tistory-uploaded image tokens before publishing.
- The default report section structure must not include a standalone hypothesis section.
- If experiment intent is still useful, fold it into existing narrative sections such as `핵심요약`, `전략에 포함된 가정과 이론적 배경`, `백테스트 설정`, or `해석` without labeling it as `가설`.
- Update Korean style/template rules to prevent headings such as:
  - `가설`
  - `검증 가설`
  - `실험 가설`
  - `Hypothesis`
- Keep research-only/live-trading safety boundaries unchanged.
- Keep image-generation rules consistent with Task 315; this task is about final Tistory embedding/layout, not chart generation style.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read the relevant `docs/blog` workflow/template/style/data/image-rule files.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- `docs/blog/report_template.html` or the relevant docs define `.section-image` rules that make Tistory-inserted images fill the report content width.
- Reusable docs show the Tistory image-placeholder wrapper shape with a fake/generic placeholder, not the owner-provided concrete image ID.
- Workflow/handoff guidance tells future report writers that final Tistory publishing may require owner-side image reinsertion and that generated HTML should remain compatible with that step.
- The default daily-report section structure no longer asks writers to create a standalone `가설` / hypothesis section.
- Style/template rules explicitly prohibit standalone hypothesis headings in final daily reports unless a future assigned task specifically requests them.
- Experiment purpose or tested assumption, when needed for clarity, is folded into existing report sections without a `가설` heading.
- Existing report artifacts remain untouched.
- No backtest, strategy/code, database, live trading, exchange endpoint, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless a structured report-generation script or schema validator is changed.

## Integration Tests

- Not required unless a report-generation script is changed.

## Contract Tests

- Verify the updated docs/template contain Tistory placeholder and full-width image wrapper guidance:

```bash
rg -n "section-image|\[##_Image|width=\"100%\"|티스토리|Tistory" docs/blog
```

- Verify standalone hypothesis-section language is removed or explicitly forbidden in final-report guidance:

```bash
rg -n "가설|검증 가설|실험 가설|Hypothesis|hypothesis" docs/blog
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
- No standalone final-report hypothesis section remains as a default.
- Tistory image placeholder examples use fake/generic IDs only.

# Verification

Default:

```bash
rg -n "section-image|\[##_Image|width=\"100%\"|티스토리|Tistory" docs/blog
rg -n "가설|검증 가설|실험 가설|Hypothesis|hypothesis" docs/blog
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

# Completion Notes

- Implemented reusable Tistory image embedding guidance in `docs/blog/report_template.html`, `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/daily_report_workflow.md`, `docs/blog/agent_handoff_prompt.md`, `docs/blog/backtest_report_data_rules.md`, `docs/blog/image_generation_prompt.md`, and `docs/blog/DAILY_REPORT_STYLE.md`.
- Added `.section-image` full-width CSS and placeholder-friendly examples using fake/generic Tistory image tokens only.
- Removed the standalone default hypothesis section from the final-report workflow and redirected experiment intent/tested assumptions into existing narrative sections.
- Existing report artifacts under `reports/` were not modified.
- Verification passed: Tistory placeholder/full-width rg check, hypothesis-rule rg check, `git diff --name-only -- reports`, and `git diff --check`.
