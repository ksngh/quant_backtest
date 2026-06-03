# Task 329: REGENERATE_LOOKBACK_RETURN_MOMENTUM_V2_REPORT_WITH_TASK328_WORKFLOW

# Goal

Regenerate the existing `Lookback Return Momentum V2` Tistory daily-report
artifact so the current report itself reflects the Task 328 workflow standard:

- preserve the V2-style artifact form and data display;
- recover V1-style dense result-to-driver-to-limitation-to-next-action logic;
- reclaim every major table and image in the `해석` section;
- remove report-facing sentence-final `봅니다.` wording and related vague
  observational phrasing.

The target artifact is:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/
```

# Source Requirement

Owner request on 2026-06-04:

> ㅇㅇ 재생성하는 task

Interpreted requirement:

- Create a task to regenerate the current V2 report artifact using the
  completed Task 328 workflow.
- This is a task-creation request, not immediate execution.
- The future execution should update the existing V2 artifact in place from
  saved Task 326/327 data.
- Do not run new backtests, tune parameters, fill missing candles, or change
  strategy logic.

# Extracted Roles

- Owner role:
  - Requests the current V2 report to be regenerated under the revised report
    workflow.
- Supporting roles:
  - Report artifact regenerator: updates `payload.json`, `report-ko.html`, and
    PNGs only as needed within the existing V2 artifact folder.
  - Data interpreter: uses saved Task 326/327 data and read-only saved-run data
    only.
  - HTML report writer: applies the Task 328 daily-report structure and Korean
    prose rules.
  - Image QA/regeneration role: verifies existing PNGs against current image
    rules and regenerates only if a chart is stale, cropped, mislabeled, or no
    longer matches the regenerated report/payload.
  - Verification role: validates JSON, HTML structure, image references,
    wording rules, and safety boundaries.
- Forbidden roles:
  - Backtest runner.
  - Parameter optimizer.
  - Strategy/code implementer.
  - Strategy-document editor unless a factual contradiction blocks report
    generation.
  - Database mutator, except read-only saved-run/trade/equity/candle reads
    needed to regenerate the report artifact.
  - Candle backfill executor.
  - Frontend/backend/API implementer.
  - Live trader.
  - Real Binance order executor.
  - Private exchange endpoint caller.
  - Account/order endpoint caller.
  - API key or `.env` user.

# Context

Task 327 generated the current `Lookback Return Momentum V2` higher-timeframe
Tistory daily-report artifact from saved Task 326 data:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
  htf_variant_comparison.png
  yearly_attribution.png
  exit_mix.png
  side_attribution.png
  data_coverage.png
```

Task 328 then revised the reusable daily-report workflow. It found that the V2
report already had strong artifact form and data display, but its logic was too
close to showing results rather than reasoning through them.

Task 328 now requires future reports to:

- keep V2-like data surfaces such as data coverage, result comparison, cost
  impact, exit mix, side attribution, yearly/regime attribution, and
  representative trades when supported by payload;
- add V1-like dense reasoning:
  - strategy idea;
  - version or experiment change;
  - main result;
  - supporting drivers;
  - limiting evidence;
  - bounded conclusion;
  - what cannot be concluded;
  - next action and why;
- connect every major table or image to an interpretive takeaway;
- use direct report-facing Korean wording without sentence-final `봅니다.`.

Saved V2 result facts that must remain intact unless saved inputs prove a
correction is needed:

- Strategy label: `Lookback Return Momentum V2`.
- Period: `2021-01-01T00:00:00Z` to `2026-06-01T00:00:00Z` exclusive.
- Data blocker: native `1h` candle data had internal gaps, so `1h` variants
  were skipped rather than treated as failed strategy runs.
- Executed runs:
  - `1213`: `4h_1d_to_12h`, total return about `-10.40%`.
  - `1214`: `4h_3d_to_1d`, total return about `+14.82%`.
  - `1215`: `1d_1w_to_1d`, total return about `+8.47%`.
  - `1216`: `1d_1m_to_1w`, total return about `+21.64%`.
- Interpretation boundary:
  - The result is gross/no-cost diagnostic evidence only.
  - It supports further testing of slower horizons compared with the failed
    short-timeframe V1/V2 diagnostics.
  - It does not prove cost-aware profitability.
  - It does not prove momentum strategies generally work.

# Scope

When this task is assigned for execution, do the following.

- Read required state files and this task first.
- Read the current strategy and report inputs:
  - `docs/strategy/lookback_return_momentum_v2.md`
  - `reports/task_326_htf_no_cost_atr1_summary.json`
  - `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - `tasks/TASK_327_LOOKBACK_RETURN_MOMENTUM_V2_HTF_DAILY_REPORT_ARTIFACT_GENERATION.md`
  - `tasks/TASK_328_DAILY_REPORT_DATA_RICH_LOGIC_DENSE_WORKFLOW_REVISION.md`
  - current `payload.json`
  - current `report-ko.html`
- Read current reusable report workflow docs:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/report_template.html`
- Regenerate the existing artifact in place under:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/
```

- Update `payload.json` if needed so it includes Task 328-era presentation
  fields:
  - `presentation_notes.table_purposes`
  - `presentation_notes.chart_purposes`
  - `presentation_notes.required_interpretive_takeaways`
  - `presentation_notes.logic_chain`
  - `presentation_notes.forbidden_copy_checks`
- Regenerate `report-ko.html` so the prose follows Task 328.
- Verify existing PNGs against current image-generation rules.
- Reuse existing PNGs if they are still correct, readable, not cropped, and
  connected to the regenerated report.
- Regenerate PNGs only when needed to keep chart purpose, labels, dimensions,
  or report interpretation consistent.
- Keep same-folder image references such as `./summary_equity_curve.png`.
- Keep filename-only image references in `payload.json`.
- Update state files after execution.

# Out of Scope

- Creating a new report folder.
- Running a new backtest.
- Re-running Task 326.
- Parameter tuning or secondary-grid exploration.
- Editing strategy/backtest code.
- Changing strategy assumptions, risk logic, cost assumptions, execution
  assumptions, validation windows, or research/live-trading boundaries.
- Filling, deriving, or backfilling missing `1h` candles.
- Treating the skipped `1h` variants as negative strategy results.
- Transaction-cost-aware validation.
- Adding fee, spread, or slippage estimates beyond stating that Task 326 used
  zero transaction costs.
- DB mutation.
- Frontend/backend/API changes.
- Reusable `docs/blog` workflow edits. If a workflow gap remains, create a
  follow-up task instead of expanding scope.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, or private
  endpoints.
- Secrets or `.env` changes.

# Requirements

- The final report artifact must remain a colocated Tistory HTML report:
  - `payload.json`
  - `report-ko.html`
  - same-folder PNGs
- The report must remain titled `Lookback Return Momentum V2`.
- The main title must not include internal experiment labels like
  `higher-timeframe`, `no-cost`, `ATR1`, or `Task 326`.
- The subtitle/lead must describe the strategy, not the internal task. Use the
  stable strategy description from the strategy document or payload.
- `핵심 요약` must explain:
  - what Lookback Return Momentum is;
  - what changed in V2;
  - the main result;
  - the main driver of the result;
  - the gross/no-cost boundary.
- `결과` must preserve V2-style data display:
  - data coverage;
  - setup;
  - variant/result comparison;
  - cost impact or no-cost boundary;
  - exit mix;
  - side attribution;
  - yearly/regime attribution;
  - representative trades.
- Tables should remain compact and purposeful. Large tables must be split or
  reduced if they obscure interpretation.
- Each major table/image must answer:
  - what it shows;
  - why it matters;
  - how it changes interpretation.
- `대표 거래` must not be isolated anecdotes. It must explain:
  - why the trade happened;
  - whether entry/exit matched the strategy logic;
  - whether the trade reflects a recurring pattern or only one example;
  - whether it supports strategy behavior, volatility behavior, or a limitation.
- `해석` must reclaim the major evidence from:
  - result comparison;
  - data coverage;
  - cost impact/no-cost boundary;
  - exit mix;
  - side attribution;
  - yearly attribution;
  - representative trades.
- `해석` must clearly state:
  - The tested V2 higher-timeframe no-cost implementation had positive gross
    evidence in three of four executed `4h`/`1d` variants.
  - This supports the idea that information-delay momentum is more aligned with
    slower horizons than the earlier minute-level tests.
  - This does not imply cost-aware profitability.
  - This does not reject or prove the entire momentum strategy family.
  - The blocked `1h` data should be handled as data coverage limitation.
- The report must avoid:
  - sentence-final `봅니다.`;
  - `라고 봅니다`;
  - `로 봅니다`;
  - `해 봅니다`;
  - awkward `그것은`;
  - `강한 결론` / `더 강한 결론`;
  - unnecessary `기본값`;
  - standalone `가설` / `Hypothesis` section;
  - obvious backtest-order disclaimers;
  - reader-facing task/run/internal candidate IDs.
- The final HTML must preserve the Tistory hELLO layout:
  - internal CSS;
  - `--page-max-width: 1120px`;
  - `.report-page { max-width: var(--page-max-width); width: calc(100% - 32px); margin: 0 auto; }`;
  - full-width `.section-image` images;
  - left-first table alignment;
  - mobile-safe table/image handling.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read the current V2 strategy document.
- [x] Read Task 326/327/328 references.
- [x] Read the existing V2 artifact.
- [x] Read the current `docs/blog` workflow docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- `payload.json` is updated or verified to include Task 328-era presentation
  notes and logic-chain fields.
- `report-ko.html` is regenerated under the existing V2 artifact folder.
- Existing PNGs are reused or regenerated according to current image rules.
- The regenerated report keeps V2-style data display while adding V1-style
  dense interpretation logic.
- Major tables and images are explicitly reclaimed in `해석`.
- The report has no report-facing sentence-final `봅니다.` wording.
- The report does not expose task IDs, run IDs, internal candidate IDs, DB
  dumps, config dumps, credentials, or source dumps in reader-facing prose.
- Saved Task 326 numerical facts are preserved unless a documented saved-input
  correction is found.
- No new backtest, parameter tuning, DB mutation, candle backfill,
  strategy/code change, frontend/backend/API change, live trading behavior,
  exchange endpoint behavior, secret, or `.env` change is introduced.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Not required unless executable code is changed.

## Integration Tests

- Not required unless a report-generation script is changed.

## Contract Tests

- Validate JSON:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json >/dev/null
```

- Validate required artifact files:

```bash
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/summary_equity_curve.png
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/cost_impact.png
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/representative_win_trade.png
test -f reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/representative_loss_trade.png
```

- Validate required Task 328 payload/report concepts:

```bash
rg -n "logic_chain|chart_purposes|required_interpretive_takeaways|table_purposes" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json
rg -n "data coverage|result comparison|exit mix|side attribution|yearly|gross/no-cost|비용 0|해석|보완점" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
```

- Validate image references:

```bash
rg -n "src=\"(?!\\./)[^\"]+\\.png|images/|\\.md" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
```

Expected:

- no matches.

- Validate forbidden public wording:

```bash
rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다|그것은|강한 결론|더 강한 결론|기본값|Hypothesis|검증 가설|실험 가설" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
```

Expected:

- no matches.

- Validate no reader-facing internal IDs:

```bash
rg -n "Task [0-9]+|TASK_[0-9]+|run id|run_id|candidate_id|DB dump|config dump|commit" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
```

Expected:

- no matches.

## Safety Tests

- Confirm no live trading, order/account/private endpoint, secret, or `.env`
  behavior was added:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env|/api/v3/order|account endpoint|private endpoint" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1 tasks/TASK_329_REGENERATE_LOOKBACK_RETURN_MOMENTUM_V2_REPORT_WITH_TASK328_WORKFLOW.md STATUS.md BACKLOG.md PROJECT_HISTORY.md
```

Expected:

- no new unsafe behavior;
- declarative safety text is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Existing V2 artifact regenerated in place.
- Saved Task 326 metrics preserved.
- Task 328 data-rich and logic-dense workflow applied.
- Major tables/images reclaimed in `해석`.
- `봅니다.` copy rule satisfied.

# Verification

Default:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json >/dev/null
git diff --check
rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다|그것은|강한 결론|더 강한 결론|기본값|Hypothesis|검증 가설|실험 가설" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the
result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before
merge if this task is included in a PR.

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
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_329_REGENERATE_LOOKBACK_RETURN_MOMENTUM_V2_REPORT_WITH_TASK328_WORKFLOW.md`
- Implementation summary:
  - Regenerated the existing V2 `report-ko.html` in place with Task 328-style data-rich, logic-dense interpretation.
  - Added Task 328-era `presentation_notes` fields to `payload.json`, including table purposes, chart purposes, required interpretive takeaways, and logic chain.
  - Reused existing PNGs after confirming they match the current stable size rules.
  - Preserved saved Task 326 metrics and treated `1h` as a data coverage limitation rather than a failed strategy result.
- Tests added or updated:
  - No unit or integration tests were required because no executable code changed.
- Tests run:
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json >/dev/null`
  - required artifact `test -f` checks for `payload.json`, `report-ko.html`, and required PNGs
  - `rg -n "logic_chain|chart_purposes|required_interpretive_takeaways|table_purposes" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json`
  - `rg -n "data coverage|result comparison|exit mix|side attribution|yearly|gross/no-cost|비용 0|해석|보완점" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `rg -n -P "src=\"(?!\\./)[^\"]+\\.png|images/|\\.md" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다|그것은|강한 결론|더 강한 결론|기본값|Hypothesis|검증 가설|실험 가설" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `rg -n "Task [0-9]+|TASK_[0-9]+|run id|run_id|candidate_id|DB dump|config dump|commit" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `git diff --check`
- Codex self-review result:
  - Scope respected. Only the assigned V2 report artifact and state/task tracking files were changed.
  - No backtest, parameter tuning, DB mutation, candle backfill, strategy/code change, frontend/backend/API change, live trading behavior, exchange endpoint behavior, secret, or `.env` change was introduced.
- Known limitations:
  - Existing `1h` candle continuity gaps remain unresolved. The report records this as a data coverage limitation.
  - The report is still a gross/no-cost diagnostic and does not establish cost-aware profitability.
- Recommended next task:
  - Create a cost-aware V2 follow-up for the positive `4h`/`1d` variants and a separate `1h` data policy task if the owner wants continuous `1h` comparison.
