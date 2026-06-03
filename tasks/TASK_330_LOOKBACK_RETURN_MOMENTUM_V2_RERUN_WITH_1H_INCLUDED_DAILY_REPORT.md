# Task 330: LOOKBACK_RETURN_MOMENTUM_V2_RERUN_WITH_1H_INCLUDED_DAILY_REPORT

# Goal

Rerun the `Lookback Return Momentum V2` higher-timeframe validation from the
backtest stage and regenerate the daily-report artifact from the new results.

The rerun must include `1h`. A report where `1h` is missing, skipped, or treated
only as a limitation does not satisfy this task.

# Source Requirement

Owner request on 2026-06-04:

> 이거 백테스트 다시하고 결과정리 처음부터 다시해줘.
> 1. 백테스트 다시하기
> 2. 그걸로 다시 리포트 만들기.
> 1h가 빠져있어서는 안돼..

Additional owner report-writing requirement on 2026-06-04:

> 330 실행하는데, 리포트 좀 자세하게 작성해줘. v1이랑 비교하면서,
> v1이랑 비교군을 바꾼 이유를 상세하게 적어야해. 저번 테스트
> 결과에서는 전제가 정보 반영의 지연이었는데 분봉으로는 정보 반영이
> 안될 거 같아서 시간을 늘려봤다는 이유여야 하고, 그 이유에 대한
> 이번 실험을 진행하는데 있어서 필요한 정보들을 집어 넣어줘야해.
> 그리고 실제 논문이나 레퍼런스를 가져오면 더 좋고, 그냥 단지
> 저번에꺼 그대로 이유를 가져와서는 안돼. 가져올 건 간략하게 가져오고,
> 이번에 바뀐 내용에 대해 근거를 정확하게 잡아야해. 그리고 시간청산에
> 대한 이유도 세세히 설명해야하고, 그걸 고칠 보완점도 명확하게 잡아줘.
> 그리고 regime이 반영이 안된 거에 대해서 다음에 테스트를 어떻게 하면
> 좋을지도 보완점으로 잡아줘. 그리고 regime에 대한 내용도 살짝 넣어주고.

Interpreted requirement:

- Redo the V2 validation rather than only rewriting the existing report.
- Regenerate the report from the new rerun results.
- `1h` must be included as an executed timeframe.
- If the full `2021-01-01T00:00:00Z` to `2026-06-01T00:00:00Z`
  native `1h` window cannot be made continuous, do not silently skip `1h`.
  Instead, use an explicitly documented `1h`-inclusive common continuous window
  for `1h`, `4h`, and `1d`.
- The report must be more detailed than Task 327/329 and must explicitly compare
  V2 against V1:
  - V1 tested short-timeframe `1m`/`5m`/`15m` close-to-close momentum and later
    ATR reward/cost geometry;
  - V2 keeps the same signal family but changes the comparison group to `1h`,
    `4h`, and `1d` because the original economic premise is delayed
    information diffusion, slow participant reaction, and slower position
    adjustment;
  - minute bars can be dominated by microstructure noise, spread crossing,
    liquidation bursts, and local order-flow pressure, so a failure or weak
    result on minute bars does not by itself test the information-delay premise
    well;
  - the report must explain that V2 is a horizon-alignment diagnostic, not a
    copied rationale from V1.
- The report must use actual theory references as background, while clearly
  stating that they are not proof that this BTCUSDT implementation works.
- The report must explain the time-exit rule in detail:
  - why `holding_bars` exists;
  - how it makes the lookback horizon and forward validation horizon explicit;
  - why it prevents stale positions from turning a short-horizon momentum test
    into an indefinite trend-following test;
  - how frequent time exits can indicate that price did not reach either `1 ATR`
    stop or target inside the declared forecast window;
  - what to test next if time exits dominate.
- The report must include regime context:
  - yearly attribution is a first pass, not a true regime model;
  - the current task does not condition entries on bull/bear/trend/volatility/
    liquidity/risk-on regimes;
  - the interpretation must explain why regime omission limits the conclusion;
  - the recommended next task must propose a predeclared regime diagnostic rather
    than post-result tuning.

# Extracted Roles

- Owner role:
  - Requires the V2 validation and report to be redone from the backtest stage.
  - Requires `1h` to be present in the final comparison.
- Supporting roles:
  - Data preflight role: verifies `BTCUSDT` `1h`, `4h`, and `1d` continuity.
  - Data repair role: attempts bounded public candle backfill for missing native
    `1h` candles if the full fixed window still has gaps.
  - Validation-window role: if full-window `1h` continuity cannot be repaired,
    selects a common continuous window that includes `1h`, `4h`, and `1d`.
  - Strategy-document maintainer: updates `docs/strategy/lookback_return_momentum_v2.md`
    before rerun if the validation window/data policy differs from Task 326.
  - Backtest runner: reruns the predeclared V2 grid with `1h`, `4h`, and `1d`.
- Report artifact generator: creates a fresh payload, PNG images, and
  `report-ko.html` from the new rerun results.
- Report writer: writes a detailed Tistory hELLO `report-ko.html` that combines
  V2-style data display with V1-style dense interpretation, compares V1 and V2,
  explains the timeframe shift from minute bars to `1h`/`4h`/`1d`, explains
  time-exit behavior, and records regime limitations plus the next diagnostic.
  - Verification role: validates JSON, image files, HTML, wording, and safety.
- Forbidden roles:
  - Live trader.
  - Real Binance order executor.
  - Signed exchange request caller.
  - Account/order/private endpoint caller.
  - API key or `.env` user.
  - Frontend/backend/API implementer.
  - Parameter optimizer.
  - Post-result tuning role.

# Context

Task 326 validated V2 on the intended `2021-01-01T00:00:00Z <= candle time <
2026-06-01T00:00:00Z` window. `4h` and `1d` passed continuity and were executed,
but `1h` had 7 internal gaps totaling 14 missing native public kline open times.
Bounded public backfill attempts stored 0 candles for those exact missing
`1h` open times, so Task 326 skipped `1h` rather than running on incomplete data.

The owner now rejects a report where `1h` is absent. This task therefore changes
the execution rule:

- preferred path: repair the full native `1h` window and run all six V2 variants;
- fallback path: if full-window repair fails, choose a shorter common continuous
  window that includes `1h`, `4h`, and `1d`, then rerun all six V2 variants on
  that common window.

The owner also requires the report to explain the research logic more precisely
than the previous V2 artifact. The key comparison is not merely "V1 failed,
V2 tries higher timeframes." The report must explain why the comparison group
changed:

- V1 treated short-timeframe close-to-close returns as a baseline for whether
  recent directional pressure persists after costs and ATR reward/risk rules.
- The deeper economic premise behind momentum is delayed information diffusion,
  underreaction, slow position adjustment, and trend-following participation.
- That premise can be poorly aligned with `1m`/`5m`/`15m`, because those bars
  mix information with microstructure noise, local liquidity demand, forced
  liquidation bursts, and short-term reversal.
- V2 therefore moves the same signal family to `1h`, `4h`, and `1d` to test
  whether the raw no-cost edge becomes clearer when the prediction horizon is
  closer to the economic mechanism being claimed.

References to use as background, not as proof:

- Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers:
  Implications for Stock Market Efficiency", Journal of Finance, DOI
  `10.1111/j.1540-6261.1993.tb04702.x`.
- Moskowitz, Ooi, and Pedersen (2012), "Time Series Momentum", Journal of
  Financial Economics, DOI `10.1016/j.jfineco.2011.11.003`.
- Hong and Stein (1999), "A Unified Theory of Underreaction, Momentum Trading,
  and Overreaction in Asset Markets", Journal of Finance, DOI
  `10.1111/0022-1082.00184`.
- Barberis, Shleifer, and Vishny (1998), "A Model of Investor Sentiment",
  Journal of Financial Economics, DOI `10.1016/S0304-405X(98)00027-0`.
- Daniel, Hirshleifer, and Subrahmanyam (1998), "Investor Psychology and
  Security Market Under- and Overreactions", Journal of Finance, DOI
  `10.1111/0022-1082.00077`.

Report interpretation must keep the references bounded:

- They support the plausibility of momentum, underreaction, gradual information
  diffusion, behavioral bias, and time-series momentum as research premises.
- They do not prove that BTCUSDT spot, this exact close-to-close proxy, this
  ATR-1 exit geometry, or this selected window should produce tradable profit.
- The report must avoid importing V1 theory verbatim; it must connect each
  reference to why a higher-timeframe test is more coherent for the current
  information-delay question.

Known Task 326 `1h` missing ranges:

- `2021-02-11T04:00:00Z`
- `2021-03-06T02:00:00Z`
- `2021-04-20T02:00:00Z` to `2021-04-20T03:00:00Z`
- `2021-04-25T05:00:00Z` to `2021-04-25T07:00:00Z`
- `2021-08-13T02:00:00Z` to `2021-08-13T05:00:00Z`
- `2021-09-29T07:00:00Z` to `2021-09-29T08:00:00Z`
- `2023-03-24T13:00:00Z`

Default fallback window if the full window cannot be repaired:

```text
2023-03-25T00:00:00Z <= candle time < 2026-06-01T00:00:00Z
```

Reason:

- it starts after the last known `1h` missing open time;
- it is aligned to `1d`, `4h`, and `1h` candle boundaries;
- it allows `1h` to be included without synthetic candles or silent gap
  tolerance.

# Scope

- Read required state files and this task before execution.
- Read:
  - `docs/strategy/lookback_return_momentum_v2.md`
  - `reports/task_326_htf_no_cost_atr1_summary.json`
  - `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`
  - current `docs/blog` report workflow docs
  - relevant market-data/backtest/strategy modules needed for preflight and run
- Update `docs/strategy/lookback_return_momentum_v2.md` before running backtests
  if the execution uses the fallback common continuous window or any data policy
  not already documented.
- Re-run data preflight for `BTCUSDT` `1h`, `4h`, and `1d`.
- Attempt bounded public `1h` backfill for missing full-window gaps if needed.
- Choose the execution window:
  - full fixed window if `1h`, `4h`, and `1d` are continuous;
  - otherwise the latest common continuous `1h`-included window, defaulting to
    `2023-03-25T00:00:00Z` through `2026-06-01T00:00:00Z` exclusive if
    preflight confirms continuity.
- Rerun the exact V2 primary grid for all six variants:

| Interval | Variant | lookback_bars | holding_bars | entry_threshold |
|---|---|---:|---:|---:|
| `1h` | `1h_1d_to_6h` | 24 | 6 | 0.005 |
| `1h` | `1h_3d_to_1d` | 72 | 24 | 0.015 |
| `4h` | `4h_1d_to_12h` | 6 | 3 | 0.010 |
| `4h` | `4h_3d_to_1d` | 18 | 6 | 0.030 |
| `1d` | `1d_1w_to_1d` | 7 | 1 | 0.030 |
| `1d` | `1d_1m_to_1w` | 30 | 7 | 0.100 |

- Preserve V2 assumptions unless explicitly changed by this task:
  - no transaction costs;
  - no cost-aware entry filter;
  - `ATR(14, RMA)`;
  - `1 ATR` stop-loss;
  - `1 ATR` take-profit;
  - stop-first same-candle ambiguity;
  - signal candle close entry;
  - exit checks from the next completed candle;
  - flat-only/no-reverse behavior.
- Save a new task report under `reports/`.
- Save compact summary JSON under `reports/`.
- Generate a fresh daily-report artifact from the new rerun results.
- The fresh report artifact folder must include:
  - `payload.json`
  - `report-ko.html`
  - same-folder PNG images
- Use a new artifact folder rather than overwriting Task 327/329 output.
  - If full window is repaired, use:

```text
reports/blog_payloads/lookback-return-momentum/v2/20210101-20260601-htf-no-cost-atr1-1h-included/
```

  - If fallback window is used, use:

```text
reports/blog_payloads/lookback-return-momentum/v2/20230325-20260601-htf-no-cost-atr1-1h-included/
```

- Update state files after execution.

# Out of Scope

- Running a secondary parameter grid.
- Changing the V2 signal definition.
- Adding volume, FVG, Order Block, market regime, macro, ETF flow, or DXY
  filters.
- Cost-aware validation.
- Fee/spread/slippage modeling beyond the explicit no-cost boundary.
- Treating full-window `1h` gaps as acceptable without documentation.
- Silently deriving `1h` from another interval.
- Deriving `1h` from lower timeframe candles unless a separate documented,
  tested derivation path already exists or is explicitly implemented and tested
  inside this task before use.
- DB schema changes.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, or private
  endpoints.
- Secrets or `.env` changes.

# Requirements

- `1h` must appear in the executed results table and the daily report.
- A final report that only says `1h` was blocked is not acceptable for this task.
- If the full 2021-2026 window cannot include `1h`, the task must clearly state
  the actual 1h-inclusive common window and compare all timeframes on that same
  effective window.
- Do not mix `1h`, `4h`, and `1d` over different effective windows unless the
  report explicitly separates the analysis and explains why. The preferred
  rerun is one common window.
- Do not silently fill missing candles with synthetic OHLCV.
- If official/public backfill still cannot repair full-window `1h`, the fallback
  common continuous subwindow is the default policy.
- The report must state the actual period in the title metadata, setup table,
  data coverage section, and interpretation.
- The report must keep the title `Lookback Return Momentum V2`.
- The report must not expose reader-facing task IDs, run IDs, internal candidate
  IDs, DB dumps, config dumps, secrets, or commits.
- The report must avoid sentence-final `봅니다.` and existing daily-report banned
  phrasing.
- The report must include:
  - `핵심 요약`
  - `전략에 포함된 가정과 이론적 배경`
  - `백테스트 설정`
  - `결과`
  - `대표 거래`
  - `해석`
- The report must compare V1 and V2:
  - V1: short-timeframe `1m`/`5m`/`15m`, cost-aware ATR reward/cost geometry,
    minute-level continuation baseline, cost/turnover sensitivity.
  - V2: higher-timeframe `1h`/`4h`/`1d`, no-cost gross diagnostic, symmetric
    `1 ATR` stop/take-profit, horizon-alignment test for information-delay
    momentum.
  - The comparison must state that V2 changes the timeframe and cost boundary,
    so it is not a direct profitability comparison against V1.
- The report must include a detailed time-exit explanation:
  - `holding_bars` defines the forecast horizon;
  - time exit prevents stale positions from remaining open after the tested
    momentum window;
  - high time-exit share can mean continuation existed but was too slow, or that
    the ATR target/stop geometry was not reached inside the intended horizon;
  - next improvements should include predeclared holding horizon comparison,
    target/stop versus time-exit attribution, and regime-conditioned holding
    tests if the data supports it.
- The report must include regime discussion:
  - mention that yearly attribution is only a coarse proxy;
  - explain why bull/bear trend, volatility, liquidity, and risk-on/risk-off
    regimes can change momentum behavior;
  - record that no regime filter was used in Task 330;
  - recommend a later predeclared regime task using objective labels such as
    moving-average trend state, realized-volatility/ATR percentile, drawdown
    state, and liquidity/trading-value proxy, with OOS/WFO after the diagnostic.
- The report must reclaim:
  - data coverage;
  - result comparison;
  - gross/no-cost boundary;
  - exit mix;
  - side attribution;
  - yearly attribution;
  - V1/V2 comparison and why the comparison group changed;
  - time-exit rationale and time-exit failure modes;
  - regime limitation and next regime diagnostic;
  - representative trades.
- The report must explain whether including `1h` changes the Task 326/329
  interpretation.
- The report must not claim cost-aware profitability.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.
- [ ] Read this task.
- [ ] Read `docs/strategy/lookback_return_momentum_v2.md`.
- [ ] Read Task 326/327/329 reports and payloads as comparison context.
- [ ] Read the current `docs/blog` workflow docs before report generation.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open
  question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and
  verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.
- [ ] Append completion progress to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- Task file is created using `tasks/TASK_TEMPLATE.md` structure.
- Strategy document exists before backtest execution.
- Strategy document is updated before execution if the fallback common window or
  any new data policy is used.
- Data preflight records first candle, last candle, duplicate count, gap count,
  and selected effective window for `1h`, `4h`, and `1d`.
- `1h` is executed, not skipped.
- All six primary-grid variants are rerun or a blocker is recorded explaining
  why no `1h`-included continuous window exists.
- Compact summary JSON is saved under `reports/`.
- Task report is saved under `reports/`.
- A new daily-report artifact folder is created with `payload.json`,
  `report-ko.html`, and same-folder PNGs.
- The new report compares `1h`, `4h`, and `1d` from the rerun results.
- The report preserves the no-cost diagnostic boundary.
- State files are updated after execution.
- No live trading, exchange order/account/private endpoint, secret, or `.env`
  behavior is introduced.

# Required Tests

## Unit Tests

- Required only if implementation changes are needed:
  - data window selection helper tests if a helper is added;
  - strategy/runner metadata tests if rerun metadata handling changes;
  - report-generation helper tests if reusable code is added.

## Integration Tests

- If existing CLI paths are sufficient, run focused backtest/report verification
  rather than adding new tests.
- If code changes are made, run relevant focused tests:

```bash
pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/market_data -q
```

## Contract Tests

- Validate compact summary JSON:

```bash
python -m json.tool reports/task_330_v2_1h_included_no_cost_atr1_summary.json >/dev/null
```

- Validate generated payload JSON:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/payload.json >/dev/null
```

- Validate required artifact files:

```bash
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/payload.json
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/summary_equity_curve.png
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/cost_impact.png
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/representative_win_trade.png
test -f reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/representative_loss_trade.png
```

- Validate `1h` is present in saved results and report:

```bash
rg -n "\"interval\": \"1h\"|1h_1d_to_6h|1h_3d_to_1d" reports/task_330_v2_1h_included_no_cost_atr1_summary.json reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/payload.json reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
```

- Validate report wording and internal-ID safety:

```bash
rg -n "봅니다\\.|라고 봅니다|로 봅니다|해 봅니다|그것은|강한 결론|더 강한 결론|기본값|Hypothesis|검증 가설|실험 가설" reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
rg -n "Task [0-9]+|TASK_[0-9]+|run id|run_id|candidate_id|DB dump|config dump|commit" reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
```

Expected:

- no matches.

- Validate same-folder PNG references:

```bash
rg -n -P "src=\"(?!\\./)[^\"]+\\.png|images/|\\.md" reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
```

Expected:

- no matches.

## Safety Tests

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env|/api/v3/order|account endpoint|private endpoint" quant_bitcoin docs reports tasks STATUS.md BACKLOG.md PROJECT_HISTORY.md
```

Expected:

- no new unsafe behavior.
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
- `1h` included in execution and final report.
- Full-window repair or fallback common continuous window documented.
- No post-result tuning.
- No cost-aware viability claim from no-cost results.

# Verification

Default:

```bash
python -m json.tool reports/task_330_v2_1h_included_no_cost_atr1_summary.json >/dev/null
git diff --check
rg -n "\"interval\": \"1h\"|1h_1d_to_6h|1h_3d_to_1d" reports/task_330_v2_1h_included_no_cost_atr1_summary.json reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/payload.json reports/blog_payloads/lookback-return-momentum/v2/<period-slug>/report-ko.html
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
- data coverage and selected effective window
- run ids
- report artifact path
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary

- Completed on 2026-06-04.
- Strategy document updated before execution: `docs/strategy/lookback_return_momentum_v2.md`.
- Full preferred `2021-01-01T00:00:00Z <= candle time < 2026-06-01T00:00:00Z` native `1h` window still had 7 internal gaps / 14 missing open times after bounded public backfill attempts returned `stored_candles=0`.
- Selected common continuous `1h`-included fallback window:
  - `2023-03-25T00:00:00Z <= candle time < 2026-06-01T00:00:00Z`.
  - `1h`: 27,936 rows, 0 gaps.
  - `4h`: 6,984 rows, 0 gaps.
  - `1d`: 1,164 rows, 0 gaps.
- Persisted run IDs:
  - `1217`: `1h_1d_to_6h`, `-12.36%`.
  - `1218`: `1h_3d_to_1d`, `-9.09%`.
  - `1219`: `4h_1d_to_12h`, `-4.44%`.
  - `1220`: `4h_3d_to_1d`, `+1.60%`.
  - `1221`: `1d_1w_to_1d`, `+7.72%`.
  - `1222`: `1d_1m_to_1w`, `+3.38%`.
- Saved compact summary JSON:
  - `reports/task_330_v2_1h_included_no_cost_atr1_summary.json`.
- Saved task report:
  - `reports/TASK_330_LOOKBACK_RETURN_MOMENTUM_V2_RERUN_WITH_1H_INCLUDED_DAILY_REPORT.md`.
- Saved Tistory report artifact:
  - `reports/blog_payloads/lookback-return-momentum/v2/20230325-20260601-htf-no-cost-atr1-1h-included/`.
- Generated required HTML and PNG outputs:
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
  - none; no strategy/backtest source-code behavior changed.
- Tests and verification run:
  - compact summary JSON validation.
  - payload JSON validation.
  - PNG existence and `1800 x 1000` dimension verification.
  - `1h` presence checks across summary, payload, and HTML report.
  - report wording/internal-ID/same-folder-image-reference checks.
  - `python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
  - `pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` passed: `25 passed`.
  - `git diff --check` passed.
  - safety grep found no new unsafe behavior.
- Codex self-review result:
  - passed; scope stayed within Task 330, no unrelated implementation work was added, no post-result tuning was performed, and no live trading/order/account/private endpoint/secret/`.env` behavior was introduced.
- Known limitations:
  - The task used a fallback continuous window rather than the full `2021` start because native `1h` gaps could not be repaired through public backfill.
  - Results are gross/no-cost diagnostics only.
  - Short-side economics are simulated and not a spot-execution viability claim.
  - Regime is represented only by yearly attribution, not by a predeclared regime model.
  - No OOS/WFO validation was performed.
- Recommended next task:
  - Create a predeclared cost-aware and regime-attribution validation for the positive daily-horizon V2 variants, with objective regime labels defined before execution.
