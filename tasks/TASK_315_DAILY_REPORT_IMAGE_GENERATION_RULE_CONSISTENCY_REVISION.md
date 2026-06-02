# Task 315: DAILY_REPORT_IMAGE_GENERATION_RULE_CONSISTENCY_REVISION

# Goal

Revise the reusable daily-report image generation rules so future report images are consistent across runs, avoid accidental cropping, provide enough trade-chart context, and prevent text/annotation overlap.

# Source Requirement

Owner request on 2026-06-02:

> 이미지 생성에 대한 규칙을 다시 만들어줘. 만들때마다 달라지니 일관적으로 만들었으면 좋겠어.
> 1. 템플릿은 현재가 딱 좋은듯해
> 2. 지금은 크기 맞춘다고 했는데, 이미지가 짤린거 같아
> 3. 거래를 보려면 주변의 시야도 필요해서, representative_win-trade같은 경우는 20260520-20260528쪽의 representative_win_trade.png를 참조해서 그런식으로 만들어줘
> 4. 보면 글자가 겹쳐있는 부분들이 있는데 이거 수정좀 해줘
> 5. 지금 당장 이미지들을 고쳐달란게 아니라, 규칙을 변경하는거야

Interpreted as: update the reusable report-image workflow/rules, not the current generated PNG artifacts, so future chart generation has a stable visual contract and QA process.

# Extracted Roles

- Owner role:
  - Provides feedback that image outputs vary too much, some images appear cropped, representative trade charts need wider context, and some labels overlap.
- Supporting roles:
  - Image workflow editor: update reusable `docs/blog` image-generation rules.
  - Report workflow editor: update only the docs needed so report generation consistently invokes the improved image rules.
  - Visual contract maintainer: preserve the current HTML template/layout contract while defining image canvas, margin, no-crop, trade-context, and annotation-collision rules.
  - Reference reviewer: use `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png` as the style/reference example for representative trade context.
- Forbidden roles:
  - Current image fixer.
  - Backtest runner.
  - Strategy/code implementer.
  - Database mutator.
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend/API implementer.

# Context

Task 313 established the Tistory hELLO report template and layout rules. Task 314 regenerated a report with larger images, but the owner observed that matching target sizes can still produce cropped or visually cramped images.

The current HTML template is considered good and should be preserved. The problem is the reusable chart-generation rule set: it needs a stable image contract that future agents follow every time.

The key distinction for this task:

- Do revise reusable rules in `docs/blog`.
- Do not regenerate or patch existing PNG images in any `reports/blog_payloads/**` folder.

# Scope

- Read required state files and this task before implementation.
- Read:
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/report_template.html`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png` as the representative-trade context reference
- Update reusable `docs/blog` rules as needed, with primary ownership in:
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
- Update `docs/blog/DAILY_REPORT_TEMPLATE.md` or `docs/blog/DAILY_REPORT_STYLE.md` only if needed to keep report-writing guidance consistent with the image rules.
- Preserve the current `docs/blog/report_template.html` unless a narrow wording-only reference to image requirements is necessary. The owner said the current template is good.
- Update state files after execution.

# Out of Scope

- Regenerating or editing existing PNG files.
- Editing existing `report-ko.html` files.
- Editing existing `payload.json` report artifacts.
- Running a new backtest.
- Parameter tuning/search.
- Strategy/code changes.
- Strategy document changes.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Keep the current report HTML template contract intact:
  - Tistory hELLO target.
  - `1120px` centered body width.
  - full-width image rendering in HTML.
  - simple, readable report layout.
- Define a stable image canvas contract so outputs do not vary by task:
  - fixed recommended canvas sizes by image type;
  - consistent margins/padding;
  - consistent font-size bands;
  - consistent title/subtitle/legend placement;
  - consistent color semantics for equity, drawdown, gross/net, win/loss, entry, exit, stop, target, and cost.
- Add explicit no-crop rules:
  - Do not create a smaller image and crop it to fit the target size.
  - Do not use square thumbnail generation or post-processing that crops chart content.
  - Generate the target canvas directly whenever possible.
  - If resizing is unavoidable, preserve aspect ratio and pad unused space rather than cropping data, axes, legends, titles, or annotations.
  - Leave enough outer padding so axis labels, tick labels, titles, legends, and callouts remain visible.
- Add representative trade context rules:
  - Representative trade charts must not zoom only to entry/exit candles.
  - Include pre-entry context and post-exit context so the reader can see setup, follow-through, reversal, or chop.
  - Use the `20260520-20260528` `representative_win_trade.png` as the style reference for showing surrounding candles and explanatory context.
  - Define a minimum context window, for example entry-to-exit span plus a bounded number of candles before entry and after exit, adjusted by timeframe and available candle data.
  - Ensure y-axis range includes entry, exit, stop, target, and local high/low with padding; do not cut off stop/target lines.
  - Apply the same context principle to both `representative_win_trade.png` and `representative_loss_trade.png`.
- Add annotation and label collision rules:
  - Prefer a dedicated annotation panel or reserved top/bottom margin for dense metrics instead of placing long text over candles.
  - Keep chart titles and labels short.
  - Use abbreviations for repeated metrics.
  - Move legends outside the plotting area when needed.
  - Avoid overlapping entry/exit/stop/target labels with candles or with each other.
  - If labels would overlap, omit lower-priority labels or use a compact numbered callout with a small legend.
  - Require a visual QA pass or equivalent static check before completion.
- Add image-generation validation rules:
  - Check each PNG is non-empty.
  - Check dimensions match the intended canvas.
  - Check payload image references are filename-only.
  - Check HTML references remain same-folder relative paths.
  - When an image is regenerated in future tasks, inspect representative trade images for crop and label overlap before completing.
- Keep report images data-driven. Do not invent candles, trade values, volume context, or PnL details that are not in payload/raw outputs.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read the relevant `docs/blog` workflow/template/style/image/data/handoff files.
- [x] Review the requested representative-trade reference image path.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- Reusable image generation docs define a consistent image contract for future daily-report PNGs.
- The updated rules explicitly prevent crop-based resizing and require padding/aspect-ratio preservation.
- Representative trade chart rules require surrounding context before entry and after exit, with the `20260520-20260528` representative win trade image named as the reference example.
- The rules include concrete label/annotation overlap prevention guidance.
- The rules include image QA checks for dimensions, non-empty files, filename-only payload references, same-folder HTML references, crop avoidance, and label readability.
- Current `docs/blog/report_template.html` remains unchanged unless a narrow consistency note is required.
- Existing report artifacts and PNG files are not edited.
- No new backtest, DB mutation, strategy/code change, live trading behavior, order/account/private endpoint usage, secret, or `.env` change is introduced.

# Completion Summary (2026-06-02)

## Files Changed

- `docs/blog/image_generation_prompt.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_315_DAILY_REPORT_IMAGE_GENERATION_RULE_CONSISTENCY_REVISION.md`

## Implementation Summary

- Added a stable daily-report image visual contract with fixed recommended canvas sizes, safe-area padding, font-size bands, title/plot/annotation band separation, and consistent color semantics.
- Added explicit no-crop rules: generate the target canvas directly, avoid square thumbnail/center-crop processing, preserve aspect ratio, and use padding rather than cropping.
- Strengthened representative trade rules so win/loss trade charts include pre-entry and post-exit candle context, use the `20260520-20260528` representative win trade as the reference style, preserve entry/exit/stop/target/local high-low on the y-axis, and prefer annotation bands over text on candles.
- Added label/annotation overlap prevention rules across image generation, data rules, workflow, handoff prompt, template, and style docs.
- Preserved `docs/blog/report_template.html`; no template diff was introduced by Task 315.
- Did not regenerate or edit existing report PNGs, `report-ko.html`, or `payload.json` artifacts.

## Tests Added Or Updated

- No unit or integration tests were added because Task 315 is a documentation workflow update only.

## Tests Run

- `rg -n "no-crop|crop|padding|aspect ratio|representative_win_trade|surrounding|pre-entry|post-exit|overlap|annotation|1120px|1800" docs/blog`
- `git diff --name-only -- reports`
- `git diff --check`
- `rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" docs/blog tasks/TASK_315_DAILY_REPORT_IMAGE_GENERATION_RULE_CONSISTENCY_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md`
- `rg -n "[ \\t]+$" docs/blog/image_generation_prompt.md docs/blog/backtest_report_data_rules.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md tasks/TASK_315_DAILY_REPORT_IMAGE_GENERATION_RULE_CONSISTENCY_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md`
- `git diff -- docs/blog/report_template.html`
- `git status --short -- docs/blog/report_template.html reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`

## Verification Notes

- Required image-rule keywords were present in `docs/blog`.
- `git diff --check` passed.
- Trailing whitespace check returned no matches.
- Safety grep matches were limited to safety-boundary text in docs/task/state files and did not indicate new executable behavior.
- `git diff -- docs/blog/report_template.html` returned no diff.
- `git status --short -- reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png` showed no status entry for the reference image.
- `git diff --name-only -- reports` still listed pre-existing dirty report artifacts under `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/`; Task 315 did not edit report artifacts.

## Codex Self-Review Result

- Scope respected: only Task 315 documentation workflow files and required task/state ledgers were updated.
- Requirement matched: rules now address consistency, no-crop resizing, representative trade context, and annotation overlap.
- Role ownership respected: report/image workflow docs were updated; strategy/backtest/frontend/backend/API/DB behavior was not changed.
- Safety respected: no secrets, `.env` changes, live trading behavior, signed requests, or order/account/private endpoint behavior were added.
- Simplicity respected: no new code, abstractions, exporter, or test harness was introduced.

## Known Limitations

- Existing generated images were intentionally not fixed or regenerated.
- No browser or visual-regression run was performed because the task was limited to reusable documentation rules.
- The repository already has unrelated dirty report artifacts and prior `docs/blog` edits; Task 315 worked with that dirty tree without reverting unrelated changes.

## Recommended Next Task

- No next task is automatically active. If the owner wants the current Task 314 images fixed under the new rules, create a separate bounded artifact-regeneration task.

# Required Tests

## Unit Tests

- Not required unless reusable code is added.

## Integration Tests

- Not required unless reusable image-generation code is added.

## Contract Tests

- Verify the updated docs contain the required image-rule concepts:

```bash
rg -n "no-crop|crop|padding|aspect ratio|representative_win_trade|surrounding|pre-entry|post-exit|overlap|annotation|1120px|1800" docs/blog
```

- Verify current report artifacts were not modified by this task:

```bash
git diff --name-only -- reports
```

- Run:

```bash
git diff --check
```

## Safety Tests

- Confirm no API keys, secrets, `.env` files, live trading behavior, or exchange order/account/private endpoint behavior are added.

```bash
rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" docs/blog tasks/TASK_315_DAILY_REPORT_IMAGE_GENERATION_RULE_CONSISTENCY_REVISION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md
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
- Current report template preserved unless narrowly justified.
- Existing report artifacts and PNGs untouched.
- Future image rules are specific enough to produce consistent outputs.
- Representative trade context and label-overlap rules are concrete and verifiable.

# Verification

Default:

```bash
rg -n "crop|padding|aspect ratio|representative_win_trade|surrounding|pre-entry|post-exit|overlap|annotation|1120px|1800" docs/blog
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
