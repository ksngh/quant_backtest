# Task 316: REGENERATE_LOOKBACK_MOMENTUM_REPORT_IMAGES_AND_COPY_RULE_REVISION

# Goal

Regenerate the current `Lookback Return Momentum V1` Tistory report images under the Task 315 image-generation rules, and revise the awkward `더 강한 결론` wording in both the current report and reusable report-writing rules.

# Source Requirement

Owner request on 2026-06-02:

> 어어 그럼 다시 이미지 생성하는 task 만들어줘봐. 그리고 리포트에 '더 강한 결론을 내려면'이라는 문구가 있는데, 강한 결론이라는 문구가 어색해. 이것도 수정 반영하는 task 만들어줘

Interpreted as: create a bounded execution task, not execute it immediately, that fixes the existing report artifact images and updates the reusable report wording rule so future reports do not use the awkward `강한 결론` phrasing.

# Extracted Roles

- Owner role:
  - Requests a new task to regenerate the existing report images under the updated image rules.
  - Points out that `더 강한 결론을 내려면` / `강한 결론` is awkward in the report.
- Supporting roles:
  - Report artifact maintainer: update the existing colocated report artifact in place.
  - Image generator: regenerate report PNGs from saved Task 311 data only, using Task 315 visual rules.
  - Copy/style maintainer: replace awkward generalization-boundary wording in the current report and reusable docs.
  - Data verifier: preserve Task 311 numerical facts when refreshing report-facing assets.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Strategy-document editor, except if a read-only clarification is needed in the completion note.
  - Database mutator.
  - Candle backfill runner.
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend/API implementer.

# Context

Task 314 regenerated the current Task 312 report artifact under:

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/`

Task 315 then updated reusable `docs/blog` image-generation rules, but intentionally did not regenerate existing PNG files. The owner now wants the current report images regenerated under those new rules.

Current search results show the awkward wording appears in:

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `docs/blog/backtest_report_data_rules.md`

This task should update the current report and reusable docs so future reports prefer natural wording such as:

- `전략군 전체에 대해 판단하려면`
- `전략군 전체로 판단 범위를 넓히려면`
- `결론의 적용 범위를 넓히려면`
- `일반화하려면`

# Scope

- Read required state files and this task before implementation.
- Read the current strategy/result/report context:
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`
  - `reports/task_311_atr_reward_cost_geometry_raw_outputs/manifest.json`
  - relevant saved raw outputs under `reports/task_311_atr_reward_cost_geometry_raw_outputs/`
  - current artifact files under `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/`
- Read the current reusable report/image rules:
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/report_template.html`
- Use the existing reference image for representative-trade context:
  - `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`
- Regenerate same-folder PNGs in the existing artifact folder:
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `reward_cost_geometry.png`
  - `accepted_entries_by_variant.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- Update only the existing report artifact files needed for image/copy consistency:
  - `report-ko.html`
  - `payload.json` only if image metadata, captions, or narrative fields need to stay consistent.
- Update reusable copy rules only where the awkward wording appears:
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
- Update state files after execution.

# Out of Scope

- New backtest execution.
- Parameter tuning/search.
- Strategy logic changes.
- Strategy document changes.
- Database mutation.
- Candle backfill.
- Creating a new report folder.
- Editing unrelated report artifacts.
- Changing `docs/blog/report_template.html` unless a narrow copy-rule reference is required by this task.
- Replacing the established Tistory hELLO template layout.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Regenerate images from saved Task 311 outputs only.
- Preserve Task 311 metrics and current report facts:
  - no new run IDs;
  - no changed net/gross PnL, trade counts, accepted-entry counts, costs, return, expectancy, drawdown, or interval labels unless verified against saved Task 311 data.
- Apply the Task 315 image rules:
  - generate the target canvas directly when possible;
  - do not crop to meet a size target;
  - preserve aspect ratio and pad unused space if resizing is unavoidable;
  - keep titles, axes, legends, labels, callouts, and annotations inside a safe area;
  - use consistent color semantics across all images;
  - avoid placing long text over dense chart areas.
- Use stable image dimensions:
  - prefer `1800px * 1000px` for standard charts and representative trade charts;
  - prefer `1800px * 1200px` when the chart is dense enough that labels would otherwise overlap;
  - keep generated PNGs large enough for the Tistory hELLO `1120px` body to display clearly.
- Representative trade chart requirements:
  - include candles before entry and after exit, not only the entry-to-exit segment;
  - use the `20260520-20260528` `representative_win_trade.png` as the style/context reference;
  - include entry, exit, stop, target, and local high/low in the visible y-axis range with padding;
  - show setup, follow-through, reversal, or chop context where saved candles allow it;
  - apply the same context rule to win and loss examples;
  - avoid overlapping entry/exit/stop/target labels.
- Report copy requirements:
  - replace `더 강한 결론을 내려면`, `더 강한 결론`, and similar `강한 결론` phrasing with natural Korean wording.
  - Preferred meaning: the tested version result is bounded, and additional validation is needed before expanding the claim to a broader strategy family.
  - Do not weaken the existing interpretation that the current V1 configuration is not effective after costs under tested conditions.
  - Do not overstate that all momentum strategies are invalid.
  - Do not add `연구용`, actual-order disclaimers, internal task IDs, run IDs, or other reader-facing implementation details.
- Preserve the Tistory hELLO HTML layout:
  - single-file HTML with internal CSS;
  - centered `.report-page`;
  - `--page-max-width: 1120px`;
  - mobile-safe width;
  - left-first tables;
  - full-width image display.
- Keep image references colocated:
  - HTML references should use same-folder relative paths such as `./summary_equity_curve.png`;
  - payload image references should remain filename-only;
  - do not create an `images/` subdirectory.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Read Task 311 report, manifest, and relevant raw outputs.
- [x] Read the current artifact folder.
- [x] Read the required `docs/blog` workflow/template/style/image/data/handoff files.
- [x] Review the representative-trade reference image path.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- The six current report PNGs are regenerated in place under the Task 315 no-crop, context-window, and label-overlap rules.
- Representative trade images show enough pre-entry and post-exit context to understand the trade surroundings.
- Regenerated images are not visibly cropped and have readable labels/annotations.
- `report-ko.html` no longer contains `더 강한 결론` or `강한 결론` wording.
- Reusable `docs/blog` rules no longer instruct future report writers to use `더 강한 결론` or `강한 결론` wording.
- The replacement wording preserves the intended interpretation boundary: the tested version can fail under current conditions, but the result alone should not be generalized to reject the entire strategy family.
- Task 311 saved metrics are preserved.
- Existing artifact structure remains colocated with no `images/` subdirectory.
- No new backtest, DB mutation, strategy/code change, candle backfill, live trading behavior, order/account/private endpoint usage, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless implementation touches reusable code.

## Integration Tests

- If an existing image-generation script is changed or created, add focused tests for:
  - output filename contract;
  - same-folder image placement;
  - no `images/` subdirectory;
  - payload image reference format.

## Contract Tests

Run:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null
```

Run image dimension checks:

```bash
sips -g pixelWidth -g pixelHeight reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/*.png
```

Verify the awkward wording is gone from the current report and reusable docs:

```bash
rg -n "더 강한 결론|강한 결론" \
  reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html \
  docs/blog/DAILY_REPORT_TEMPLATE.md \
  docs/blog/DAILY_REPORT_STYLE.md \
  docs/blog/backtest_report_data_rules.md
```

Expected result: no matches.

Verify image references stay colocated:

```bash
rg -n "images/|image_plan|report-en|run_id|TASK_|Task " reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json
```

Expected result: no matches.

Verify saved metrics against Task 311 manifest with a focused script or explicit JSON comparison. At minimum, compare final equity/net PnL/gross PnL/cost/trade-count fields used by the report to the saved manifest/raw outputs.

Run:

```bash
git diff --check
```

## Safety Tests

- Confirm no API keys, secrets, `.env` files, live trading behavior, signed requests, or exchange order/account/private endpoint behavior are added.
- Run a focused safety grep over changed files:

```bash
rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" \
  docs/blog \
  reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost \
  tasks/TASK_316_REGENERATE_LOOKBACK_MOMENTUM_REPORT_IMAGES_AND_COPY_RULE_REVISION.md \
  STATUS.md BACKLOG.md PROJECT_HISTORY.md
```

# Visual Verification

- Inspect the regenerated `representative_win_trade.png` and `representative_loss_trade.png` visually.
- Confirm:
  - no clipped title, axis label, legend, candle, stop/target line, or annotation;
  - representative trade charts include surrounding candles;
  - labels do not overlap candles or each other in a way that makes the chart hard to read;
  - the image remains readable when displayed at the Tistory hELLO report body width.
- If browser or image-view verification is unavailable, record that limitation in `STATUS.md` and the completion summary.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected.
- Existing saved metrics preserved.
- Image artifact contract respected.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.

# Verification

Default verification for this task is the required contract/safety/visual checks above. Do not run the full test suite unless reusable code changes make it necessary.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- visual verification result
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary (2026-06-02)

## Files Changed

- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/summary_equity_curve.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/cost_impact.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/reward_cost_geometry.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/accepted_entries_by_variant.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_win_trade.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_loss_trade.png`
- `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `docs/blog/backtest_report_data_rules.md`
- `tasks/TASK_316_REGENERATE_LOOKBACK_MOMENTUM_REPORT_IMAGES_AND_COPY_RULE_REVISION.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`

## Implementation Summary

- Regenerated the six current report PNGs in place from saved Task 311 data and current payload facts.
- Used direct `1800px`-wide canvases with explicit white backgrounds, safe padding, annotation bands, and no crop-based resizing.
- Regenerated representative win/loss trade charts with surrounding pre-entry and post-exit `15m` candles read from local PostgreSQL in read-only mode because the saved raw outputs contain trade metadata but not OHLC context windows.
- Replaced awkward `더 강한 결론` / `강한 결론` wording with `전략군 전체로 판단 범위를 넓히려면` in the current HTML report and reusable report-writing rules.
- Preserved the existing Tistory hELLO report layout, same-folder image references, filename-only payload image references, and Task 311 saved metrics.

## Tests Added or Updated

- No unit tests were added because no reusable code was changed.

## Tests Run

- `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null`
- `sips -g pixelWidth -g pixelHeight reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/*.png`
- `rg -n "더 강한 결론|강한 결론" ...` with no matches.
- `rg -n "images/|image_plan|report-en|run_id|TASK_|Task " ...` with no matches.
- Focused JSON comparison verified payload `variant_metrics` and `main_tp3_minatr0_metrics` against the saved Task 311 manifest.
- `find ... -name images` and `find ... -name 'report-en*' -o -name 'image_plan*'` returned no forbidden artifact paths.
- `git diff --check`
- `rg -n "[ \t]+$" ...` with no trailing-whitespace matches.
- Focused safety grep over changed docs/report/task/state files; matches were limited to declarative safety-policy text in docs/state/task files.

## Visual Verification Result

- Inspected `summary_equity_curve.png`, `cost_impact.png`, `reward_cost_geometry.png`, `accepted_entries_by_variant.png`, `representative_win_trade.png`, and `representative_loss_trade.png`.
- Confirmed chart titles, labels, table cells, representative trade markers, stop/target lines, and annotation bands are visible and not cropped.
- Reworked `accepted_entries_by_variant.png` after visual QA found the rightmost column was clipped.
- Combined overlapping `Exit/Stop` labels in the representative loss chart and kept x-axis labels away from the close annotation.

## Codex Self-Review Result

- Scope stayed within Task 316.
- No strategy logic, backtest execution, parameter tuning/search, DB mutation, candle backfill, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change was added.
- Saved Task 311 metrics were preserved and checked against the manifest.
- No unnecessary abstraction was introduced.

## Known Limitations

- The regenerated equity chart uses saved execution/equity result points available from Task 311 outputs rather than a full per-candle mark-to-market equity series.
- Representative trade chart OHLC context was read from the local candle database in read-only mode because the saved Task 311 raw outputs did not include surrounding candle windows.
- PNGs were generated from deterministic SVG canvases and converted with `sips` because the current environment did not expose a project image-generation utility for this exact artifact refresh.

## Recommended Next Task

- No automatic next task. If broader claims about `LOOKBACK_RETURN_MOMENTUM` are needed, create a separate locked OOS/WFO or trade-quality diagnostic task with predeclared windows and filters.
