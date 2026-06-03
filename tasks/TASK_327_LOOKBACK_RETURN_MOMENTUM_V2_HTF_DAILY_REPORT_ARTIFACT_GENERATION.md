# Task 327: LOOKBACK_RETURN_MOMENTUM_V2_HTF_DAILY_REPORT_ARTIFACT_GENERATION

# Goal

Generate the full Tistory daily-report artifact for the completed
`LOOKBACK_RETURN_MOMENTUM` V2 higher-timeframe validation result.

This task exists because Task 326 produced the research task report and compact
summary JSON under `reports/`, but did not apply the full daily-report workflow.
The required final artifact is not Markdown. It must be a colocated blog report
folder containing:

- `payload.json`
- same-folder PNG chart images
- `report-ko.html`

# Source Requirement

Owner feedback after Task 326 completion:

> 아니 레포트 만드는 워크플로우는 없어? html이 산출물이고 이미지랑 json 만드는거

Interpreted requirement:

- Use the existing `docs/blog` full report workflow.
- Convert the saved Task 326 V2 higher-timeframe result into a Tistory-ready
  daily-report artifact.
- The final human-facing report must be `report-ko.html`.
- The data handoff must be `payload.json`.
- Report images must be PNG files colocated with `payload.json` and referenced
  by filename only.
- Do not run new backtests or tune parameters while generating the report.

# Extracted Roles

- Owner role:
  - Requests the proper full daily-report workflow output, not only a research
    task report.
- Supporting roles:
  - Report artifact builder: create the colocated artifact folder, `payload.json`,
    PNG charts, and `report-ko.html`.
  - Data interpreter: use saved Task 326 results and persisted saved-run data
    only, without changing metrics or rerunning validation.
  - Chart generator: create readable deterministic PNG charts from saved result,
    equity, trade, exit, side, yearly, and candle data where available.
  - HTML report writer: follow the Tistory hELLO `report-ko.html` workflow and
    write a Korean blog-ready report.
  - Strategy context reader: read the V2 strategy document so the report opens
    with the strategy idea and theory, not internal task/run labels.
  - Verification role: verify JSON, image files, HTML structure, image paths,
    and safety boundaries.
- Forbidden roles:
  - Backtest runner.
  - Parameter optimizer.
  - Strategy/code implementer.
  - Database mutator, except read-only queries of saved run/equity/trade/candle
    data required to render report artifacts.
  - Frontend/backend/API implementer.
  - Live trader.
  - Real Binance order executor.
  - Private exchange endpoint caller.
  - Account/order endpoint caller.
  - API key or `.env` user.

# Context

Task 326 completed the V2 higher-timeframe no-cost ATR-1 validation.

Saved inputs:

- `docs/strategy/lookback_return_momentum_v2.md`
- `reports/task_326_htf_no_cost_atr1_summary.json`
- `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
- persisted saved runs:
  - `1213`: `4h_1d_to_12h`, total return `-10.40%`
  - `1214`: `4h_3d_to_1d`, total return `+14.82%`
  - `1215`: `1d_1w_to_1d`, total return `+8.47%`
  - `1216`: `1d_1m_to_1w`, total return `+21.64%`

Task 326 also recorded a `1h` data blocker:

- native Binance public `1h` candles from `2021-01-01T00:00:00Z` to
  `2026-06-01T00:00:00Z` exclusive had 7 internal gaps totaling 14 missing
  open times;
- bounded public kline backfill attempts stored 0 candles for those gaps;
- the two `1h` variants were skipped rather than run over incomplete,
  synthetic, or derived data.

Report interpretation boundary:

- The executed `4h` and `1d` V2 variants are gross/no-cost diagnostics only.
- Three of four executed variants were positive before transaction costs.
- This supports testing slower horizons further, but does not imply cost-aware
  profitability or deployability.
- `1h` is a data-coverage blocker, not a negative strategy result.
- The result must not claim that all momentum strategies work or fail.

# Scope

- Read required state files and this task before implementation.
- Read:
  - `docs/strategy/lookback_return_momentum_v2.md`
  - `reports/task_326_htf_no_cost_atr1_summary.json`
  - `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/report_template.html`
- Create a colocated full report artifact under:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/
```

- Create at minimum:
  - `payload.json`
  - `report-ko.html`
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- Create optional images when saved data is available and the chart improves
  readability:
  - `htf_variant_comparison.png`
  - `yearly_attribution.png`
  - `exit_mix.png`
  - `side_attribution.png`
  - `data_coverage.png`
- Use same-folder image references in `report-ko.html`, for example
  `./summary_equity_curve.png`.
- Use filename-only image references in `payload.json`.
- Use saved Task 326 data and read-only saved-run/candle queries only.
- Select a primary report run before image generation. Default primary run:
  `1d_1m_to_1w`, because it had the highest saved gross/no-cost return among
  executed V2 variants.
- Present the full `4h`/`1d` comparison in compact tables and optional charts.
- Record the blocked `1h` variants in data coverage or limitations, not as
  failed trades.
- Update state files after execution.

# Out of Scope

- New backtest execution.
- Re-running Task 326.
- Filling or deriving missing `1h` candles.
- Parameter tuning or secondary-grid exploration.
- Transaction-cost-aware validation.
- Fee, spread, or slippage estimation beyond explaining that Task 326 set all
  transaction-cost components to zero.
- Strategy/code changes.
- Strategy document changes unless a factual inconsistency blocks report
  generation.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Editing reusable `docs/blog` workflow files unless the current workflow
  directly blocks artifact generation; if that happens, record a follow-up task
  instead of expanding scope silently.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private
  endpoints.
- Secrets or `.env` changes.

# Requirements

- The report must be `report-ko.html`, not Markdown.
- The artifact schema must follow
  `docs/blog/backtest_report_data_rules.md`.
- The report writing process must follow:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/report_template.html`
- The image generation process must follow
  `docs/blog/image_generation_prompt.md`.
- The HTML must be a single complete file with internal CSS.
- The HTML must use the Tistory hELLO layout contract:

```css
:root {
  --page-max-width: 1120px;
}

.report-page {
  max-width: var(--page-max-width);
  width: calc(100% - 32px);
  margin: 0 auto;
}
```

- The HTML must use `<main class="report-page">`.
- Images must be full-width inside `.section-image`.
- Tables must be wrapped with `<div class="table-scroll">`.
- Tables must be left aligned by default; numeric columns may be right aligned
  only where helpful.
- The main title should be `Lookback Return Momentum V2`.
- The subtitle should use the stable strategy description from the strategy
  document, not a verbose experiment label.
- The opening paragraph must explain the strategy idea first.
- `핵심 요약` must briefly explain what changed in V2:
  - V2 shifts the hypothesis time scale toward higher timeframes;
  - Task 326 used no transaction costs and symmetric `1 ATR` stop/take-profit;
  - `1h` could not be validated because of data continuity gaps.
- The report must include the required daily-report sections:
  - `핵심 요약`
  - `전략에 포함된 가정과 이론적 배경`
  - `백테스트 설정`
  - `결과`
  - `대표 거래`
  - `해석`
- The report must not create a standalone `가설`, `검증 가설`, `실험 가설`, or
  `Hypothesis` section.
- The report must explain the no-cost boundary:
  - fees, spread, and slippage were all zero;
  - gross PnL and net PnL are therefore identical by configuration;
  - cost-aware viability remains untested.
- `cost_impact.png` must not imply a real cost-aware result. It should show the
  zero-cost diagnostic boundary clearly, for example gross/net equivalence and
  zero fee/spread/slippage components.
- The report must preserve saved Task 326 numerical facts.
- The report must not expose internal task IDs, run IDs, candidate IDs, raw DB
  dump names, git commits, secrets, or config dumps in reader-facing prose,
  image titles, image filenames, or report captions.
- Internal run IDs may be used only during execution for read-only source lookup
  and may be recorded in task/status completion notes, not in the blog-facing
  article.
- The report must avoid prohibited wording from the style guide, including
  `그것은`, awkward `기본값`, old English micro-headings, and obvious
  backtest-order disclaimers.
- The `해석` section must clearly separate:
  - what the V2 saved result supports under the tested conditions;
  - what it cannot prove about cost-aware profitability;
  - why the `1h` blocker limits the higher-timeframe comparison;
  - why this result does not decide whether all momentum strategies work or
    fail.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read this task.
- [x] Read the relevant strategy document.
- [x] Read the Task 326 report and compact summary JSON.
- [x] Read required daily-report workflow/style/template/image/payload docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open
  question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and
  verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- Artifact folder exists:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/
```

- `payload.json` exists, is valid JSON, and follows the colocated payload/images
  schema.
- `report-ko.html` exists and is a Tistory-ready Korean HTML report.
- Required PNG files exist and are non-empty:
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- PNG files are colocated with `payload.json`.
- No `images/` subfolder is created.
- No `report-ko.md`, `report-en.html`, `report-en.md`, `image_plan.md`, or
  `image_plan.json` is created.
- `payload.json` image references are filename-only.
- `report-ko.html` image references use same-folder `./[filename].png` paths.
- `report-ko.html` includes the hELLO skin `.report-page` layout contract.
- `report-ko.html` includes full-width `.section-image` image styling.
- `report-ko.html` has no reader-facing task IDs, run IDs, or candidate IDs.
- `report-ko.html` includes the no-cost diagnostic boundary and does not imply
  cost-aware profitability.
- `report-ko.html` treats the `1h` issue as a data blocker, not a strategy
  failure.
- Saved Task 326 metrics are preserved.
- No new backtest, parameter tuning/search, DB mutation, strategy/code change,
  live trading behavior, order/account/private endpoint usage, secret, or
  `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless reusable helper code is added.

## Integration Tests

- Not required unless reusable exporter code is added.

## Contract Tests

- Validate JSON:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json >/dev/null
```

- Verify required artifacts exist and PNG files are non-empty.
- Verify payload image references are filename-only.
- Verify `report-ko.html` references same-folder image filenames.
- Verify `report-ko.html` contains:
  - `<main class="report-page">`
  - `--page-max-width: 1120px`
  - `width: calc(100% - 32px)`
  - `.section-image`
  - `report-figure`
  - `table-scroll`
- Verify forbidden report-facing wording from the current style guide is absent.
- Verify reader-facing task IDs, run IDs, and candidate IDs are absent.
- Run:

```bash
git diff --check
```

## Safety Tests

- Confirm no code/report workflow added by this task calls exchange
  order/account/private endpoints.
- Confirm no API keys, secrets, or `.env` files are added or modified.
- Run a focused artifact and changed-file safety grep:

```bash
rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1 tasks/TASK_327_LOOKBACK_RETURN_MOMENTUM_V2_HTF_DAILY_REPORT_ARTIFACT_GENERATION.md STATUS.md BACKLOG.md PROJECT_HISTORY.md
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
- Existing Task 326 saved metrics preserved.
- Existing daily-report workflow followed.
- Tistory hELLO HTML output produced.
- No-cost diagnostic boundary is clear.
- `1h` data blocker is not treated as a failed strategy result.

# Verification

Default:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json >/dev/null
git diff --check
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
- report artifact folder
- source result files used
- generated payload/images/HTML
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary (2026-06-03)

- Files changed:
  - `docs/strategy/lookback_return_momentum_v2.md`
  - `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
  - `tasks/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - `tasks/TASK_327_LOOKBACK_RETURN_MOMENTUM_V2_HTF_DAILY_REPORT_ARTIFACT_GENERATION.md`
  - `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - `reports/task_326_htf_no_cost_atr1_summary.json`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/report-ko.html`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/summary_equity_curve.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/cost_impact.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/representative_win_trade.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/representative_loss_trade.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/htf_variant_comparison.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/yearly_attribution.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/exit_mix.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/side_attribution.png`
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/data_coverage.png`
- Implementation summary:
  - Aligned the higher-timeframe information-delay path to `Lookback Return Momentum V2` per owner clarification.
  - Marked the older short-timeframe Task 324 V2 draft as superseded for version naming unless a later task retitles or re-versions it.
  - Generated the full Tistory hELLO daily-report artifact from saved Task 326 results only.
  - Did not run a new backtest, tune parameters, mutate DB records, change strategy code, backfill candles, or change frontend/backend code.
- Report artifact folder:
  - `reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/`
- Source result files used:
  - `reports/task_326_htf_no_cost_atr1_summary.json`
  - `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - saved read-only run/equity/trade/candle data for Task 326 runs.
- Generated payload/images/HTML:
  - `payload.json`
  - `report-ko.html`
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
  - `htf_variant_comparison.png`
  - `yearly_attribution.png`
  - `exit_mix.png`
  - `side_attribution.png`
  - `data_coverage.png`
- Tests added or updated:
  - None. This task generated report artifacts and did not add reusable helper code.
- Tests run:
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/payload.json`
  - Artifact validation for required files, non-empty PNGs, no forbidden sidecar files, filename-only payload image refs, same-folder HTML image refs, hELLO CSS tokens, and forbidden reader-facing wording.
  - `sips -g pixelWidth -g pixelHeight reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1/*.png`
  - Old strategy-version path/reference grep over changed docs and artifacts.
  - HTML forbidden wording and internal-ID grep over `report-ko.html`.
  - `rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING" reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1 tasks/TASK_327_LOOKBACK_RETURN_MOMENTUM_V2_HTF_DAILY_REPORT_ARTIFACT_GENERATION.md docs/strategy/lookback_return_momentum_v2.md STATUS.md BACKLOG.md PROJECT_HISTORY.md`
  - `git diff --check`
- Codex self-review result:
  - Passed. Scope stayed within Task 327 plus the owner-requested V2 naming correction. No live-trading, order/account endpoint, secret, `.env`, frontend/backend, DB mutation, candle backfill, or new backtest behavior was added.
- Known limitations:
  - The report is a gross/no-cost diagnostic artifact; cost-aware viability remains untested.
  - `1h` remains a data-coverage blocker from Task 326 and is not treated as a strategy failure.
  - PNG generation used local deterministic chart rendering and `sips` conversion because common Python plotting libraries were unavailable in the active environment.
  - Browser visual QA was not run.
- Recommended next task:
  - Create a cost-aware V2 follow-up for the positive `4h`/`1d` variants, especially `1d_1m_to_1w` and `4h_3d_to_1d`, and separately decide whether to repair or exclude the blocked `1h` data window before any broader higher-timeframe conclusion.
