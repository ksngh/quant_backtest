# LOOKBACK_RETURN_MOMENTUM v2 Strategy Document

## 1. Strategy Identity

- Strategy name: `LOOKBACK_RETURN_MOMENTUM`
- Strategy version: `v2`
- Strategy slug: `lookback_return_momentum`
- Stable strategy description: 과거 일정 구간의 수익률을 확인하는 모멘텀 전략.
- Owner task: `TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION`
- Revision task: `TASK_330_LOOKBACK_RETURN_MOMENTUM_V2_RERUN_WITH_1H_INCLUDED_DAILY_REPORT`
- Status: `research_only`
- Last updated: 2026-06-04

Versioning note:

- V1 documents the original short-timeframe lookback-return momentum baseline and later ATR/cost-aware revisions.
- Owner clarified on 2026-06-03 that the higher-timeframe information-delay validation should be the report-facing V2.
- Task 324 remains a superseded short-timeframe no-cost ATR-1 draft and must not be executed as the active V2 path unless it is retitled or reversioned by a later task.
- V2 is assigned to the higher-timeframe information-delay validation because this task changes the hypothesis time scale to `1h`, `4h`, and `1d` while preserving the same signal family.
- Task 330 reruns V2 with `1h` included. If the full 2021-2026 native `1h` window cannot be repaired, Task 330 uses a documented common continuous fallback window rather than skipping `1h`.

## 2. Market and Data Scope

- Exchange: Binance public market data for research.
- Market: BTC/USDT spot-style OHLCV research data.
- Symbol: `BTCUSDT`
- Primary timeframe: `1h`, `4h`, and `1d`.
- Higher timeframes: none beyond the tested candle interval itself. V2 does not use a separate higher-timeframe confirmation filter.
- Intended test period:
  - start inclusive: `2021-01-01T00:00:00Z`
  - preferred fixed end exclusive: `2026-06-01T00:00:00Z`
  - if local data does not reach that end for all intervals, use the latest common complete end timestamp and record the actual effective window per interval.
- Required data: completed OHLCV candles. Signal logic uses close prices only; ATR and exits require high/low/close.
- Known data limitations:
  - The signal requires at least `lookback_bars` prior closes.
  - The first `lookback_bars` candles must not produce a signal.
  - ATR risk distance requires enough completed high/low/close candles for `ATR(14)` with full-window warm-up.
  - A signal must not enter while ATR is unavailable, zero, negative, or non-finite.
  - `1h`, `4h`, and `1d` must be loaded as native intervals through the market-data path. Do not silently derive `4h` from `1h` unless a separate assigned task implements, tests, and documents that derivation.
  - Local Task 326 creation found no Task 324 report markdown and no Task 324 compact summary JSON. Execution must distinguish owner-provided prior short-timeframe evidence from repository-backed prior metrics unless those artifacts are later created.

## 3. Market Phenomenon

- Phenomenon: recent own-asset close-to-close return may continue over a later higher-timeframe holding window.
- Why it may appear in BTC: BTC can react to information, flow, and risk appetite in waves rather than instantly. A meaningful `1h`, `4h`, or `1d` move may reflect delayed participant reaction, gradual portfolio adjustment, or trend-following participation that persists beyond the signal candle.
- Economic or microstructure rationale:
  - Information may not be incorporated immediately by all participants.
  - Capital allocation, fund-flow response, and position adjustment can unfold over hours or days.
  - Trend-following participants can reinforce a recent move after the initial impulse.
  - Risk-on/risk-off changes, ETF-related flow, macro repricing, and cross-session positioning can propagate at a slower cadence than minute bars.
- Behavioral rationale:
  - Underreaction can appear when participants update beliefs gradually.
  - Anchoring and slow attention can delay full repricing after news or regime changes.
  - Performance chasing or forced risk adjustment can extend a move after the first return impulse.
- Expected market regime:
  - directional regimes where the latest one-day, three-day, one-week, or one-month return captures slow information absorption rather than one-candle exhaustion.
  - regimes where BTC moves with persistent flow or macro/risk appetite rather than short-lived liquidation bursts.
- Regimes where this should not work:
  - choppy mean-reverting ranges.
  - exhaustion moves where a high lookback return marks a local peak or trough.
  - news shocks that fully reprice in one candle.
  - low-volatility regimes where thresholds are rarely met or ATR exits dominate before continuation.
  - regimes where one side, one year, or one outlier explains most of the result.
- Report-ready summary: V2 tests whether the same close-to-close momentum idea is more coherent on `1h`, `4h`, and `1d`, where information diffusion and slower participant adjustment are more plausible than on `1m`/`5m` microstructure windows.

V1-to-V2 comparison logic:

- V1 tested the short-timeframe baseline on `1m`, `5m`, and `15m`. It asked whether recent minute-level directional pressure could survive realistic costs and ATR reward/risk geometry.
- V2 does not merely "try another parameter range." It changes the comparison group because the economic premise being tested is information-delay momentum.
- If delayed information diffusion, slow attention, staged allocation, and position adjustment are the intended mechanisms, minute bars may be a poor primary test. `1m`/`5m`/`15m` include spread crossing, very local order-flow pressure, liquidation bursts, and fast reversal dynamics that can hide or invert slower information effects.
- `1h`, `4h`, and `1d` better align the signal horizon with the mechanism: intraday reaction delay, session-to-session adjustment, daily fund-flow response, and slower risk-on/risk-off repricing.
- V2 is therefore a horizon-alignment diagnostic. It is not a direct profitability comparison against V1 because V2 removes costs and changes the timeframe set.

## 3.1 Theory and References

This section is required before generating a full daily/Tistory report for this strategy.

- Why this strategy might have an edge:
  - If information, capital flows, and positioning are incorporated gradually, recent positive or negative returns can summarize directional pressure that has not fully dissipated.
  - A higher-timeframe return can reduce the influence of spread crossing, one-minute liquidation bursts, and local order-flow noise that can dominate very short bars.
  - The tested signal is intentionally simple, so a positive no-cost result would indicate raw directional timing before adding cost-aware execution or additional filters.
- What market mechanism it assumes:
  - delayed information diffusion;
  - underreaction to new information;
  - slow position adjustment;
  - order-flow continuation;
  - trend-following participation after an initial move.
- What participant behavior it assumes:
  - some participants react later than others;
  - allocation changes can be staged across sessions or days;
  - trend-followers may join only after a move becomes visible;
  - discretionary and systematic participants may rebalance after daily or multi-hour signals rather than every minute.
- Why the chosen timeframe can expose the mechanism:
  - `1h` can capture intraday information propagation while reducing minute-level noise.
  - `4h` can capture session-level continuation and cross-session adjustment.
  - `1d` can capture daily information diffusion, fund-flow response, and slower allocation effects.
  - These horizons are better aligned with an information-delay premise than the prior `1m`, `5m`, and `15m` tests.
- Why the prior minute-level comparator may be insufficient for this premise:
  - `1m`/`5m`/`15m` can capture the mechanics of immediate liquidity taking rather than gradual information diffusion.
  - A negative minute-level result can mean the close-to-close proxy is too noisy at that horizon, not that the broader momentum mechanism is absent.
  - Minute-level tests are still valuable for execution and turnover/cost questions, but they are less direct evidence for slower information-delay mechanisms.
- When the theory should fail:
  - when the recent move is mainly a liquidation burst or exhaustion event;
  - when the market mean-reverts quickly after a visible move;
  - when a single event or year dominates performance;
  - when continuation exists but is smaller than realistic transaction costs;
  - when close-to-close return is a poor proxy for the relevant flow or information.
- References:
  - `docs/strategy/lookback_return_momentum_v1.md`:
    - Title: LOOKBACK_RETURN_MOMENTUM v1 Strategy Document
    - Author/source: local project strategy document
    - Year/date: 2026-06-01
    - Link or local path: `docs/strategy/lookback_return_momentum_v1.md`
    - Why it matters for this strategy: documents the original signal formula, completed-candle no-lookahead rule, ATR risk-distance behavior, and theory notes for delayed information diffusion, underreaction, order-flow continuation, and trend-following participation.
  - `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`:
    - Title: LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION
    - Author/source: local project task
    - Year/date: 2026-06-02
    - Link or local path: `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
    - Why it matters for this strategy: records the superseded short-timeframe no-cost symmetric `1 ATR` draft that motivated moving the active V2 naming to the higher-timeframe information-delay path after owner clarification.
  - `task_324_report_if_available`:
    - Title: Task 324 V2 no-cost ATR-1 validation report
    - Author/source: local project report
    - Year/date: absent when this document was created
    - Link or local path: `reports/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
    - Why it matters for this strategy: if it exists during execution, use it as repository-backed evidence that short-timeframe V2 did not show useful no-cost behavior.
  - `task_324_summary_if_available`:
    - Title: Task 324 V2 no-cost ATR-1 compact summary
    - Author/source: local project report JSON
    - Year/date: absent when this document was created
    - Link or local path: `reports/task_324_v2_no_cost_atr1_summary.json`
    - Why it matters for this strategy: if it exists during execution, use it for the `1m`, `5m`, and `15m` comparison metrics.
  - `jegadeesh_titman_1993`:
    - Title: "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency"
    - Author/source: Narasimhan Jegadeesh and Sheridan Titman, Journal of Finance
    - Year/date: 1993
    - Link or local path: DOI `10.1111/j.1540-6261.1993.tb04702.x`, `https://doi.org/10.1111/j.1540-6261.1993.tb04702.x`
    - Why it matters for this strategy: general background for momentum, delayed information diffusion, and underreaction. It is not proof that BTCUSDT intraday or higher-timeframe crypto momentum must work.
  - `moskowitz_ooi_pedersen_2012`:
    - Title: "Time Series Momentum"
    - Author/source: Tobias J. Moskowitz, Yao Hua Ooi, and Lasse Heje Pedersen, Journal of Financial Economics
    - Year/date: 2012
    - Link or local path: DOI `10.1016/j.jfineco.2011.11.003`, `https://doi.org/10.1016/j.jfineco.2011.11.003`; author-hosted PDF `https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf`
    - Why it matters for this strategy: general background that own-asset past returns can carry directional information across liquid assets. It is not proof that this exact BTCUSDT implementation works.
  - `hong_stein_1999`:
    - Title: "A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets"
    - Author/source: Harrison Hong and Jeremy C. Stein, Journal of Finance
    - Year/date: 1999
    - Link or local path: DOI `10.1111/0022-1082.00184`, `https://doi.org/10.1111/0022-1082.00184`; NBER working paper `https://www.nber.org/papers/w6324`
    - Why it matters for this strategy: provides a theory where gradual information diffusion can create short-run underreaction and trend-chasing behavior. It supports testing a slower horizon than minute bars, but does not validate this BTCUSDT rule.
  - `barberis_shleifer_vishny_1998`:
    - Title: "A Model of Investor Sentiment"
    - Author/source: Nicholas Barberis, Andrei Shleifer, and Robert Vishny, Journal of Financial Economics
    - Year/date: 1998
    - Link or local path: DOI `10.1016/S0304-405X(98)00027-0`, `https://doi.org/10.1016/S0304-405X(98)00027-0`
    - Why it matters for this strategy: models belief formation that can produce underreaction and overreaction. It supports behavioral plausibility, not a guarantee of crypto momentum.
  - `daniel_hirshleifer_subrahmanyam_1998`:
    - Title: "Investor Psychology and Security Market Under- and Overreactions"
    - Author/source: Kent Daniel, David Hirshleifer, and Avanidhar Subrahmanyam, Journal of Finance
    - Year/date: 1998
    - Link or local path: DOI `10.1111/0022-1082.00077`, `https://doi.org/10.1111/0022-1082.00077`; University of Michigan record `https://hdl.handle.net/2027.42/73431`
    - Why it matters for this strategy: connects investor overconfidence and biased self-attribution to underreaction/overreaction patterns. It is a behavioral background source only.

Report-reference boundary:

- Report writers must not state that these papers prove this BTCUSDT V2 works.
- The references justify why it is reasonable to test momentum and why a higher timeframe can be more coherent for an information-delay hypothesis.
- The actual evidence for V2 must come from the saved Task 330 runs, not from the references.

## 4. Hypothesis

- Primary hypothesis: `BTCUSDT는 높은 시간축에서 최근 lookback_bars 구간 수익률이 entry_threshold 이상이면 이후 holding_bars 동안 같은 상승 방향의 양의 gross/no-cost 기대값을 보일 것이다.`
- Secondary hypothesis: `BTCUSDT는 높은 시간축에서 최근 lookback_bars 구간 수익률이 -entry_threshold 이하이면 이후 holding_bars 동안 같은 하락 방향의 양의 gross/no-cost 기대값을 보일 것이다.`
- Timeframe-alignment hypothesis: `1h`, `4h`, and `1d`는 `1m`, `5m`, `15m`보다 정보 반영 지연 가설과 시간축이 더 잘 맞을 수 있다.
- V1 comparison hypothesis: V1 short-timeframe failures or weak results do not fully test the information-delay premise if the mechanism unfolds over hours or days rather than minutes.
- Null hypothesis: tested V2 close-to-close momentum with symmetric `1 ATR` exits does not show positive gross/no-cost edge from 2021 onward.
- Interpretation boundary: a positive V2 result is raw gross diagnostic evidence only. It does not imply cost-aware profitability or deployability.

## 5. Factors and Indicators

| Factor | Formula / Definition | Required Data | Expected Direction | Confounders |
|---|---|---|---|---|
| `momentum_return` | `close[t] / close[t - lookback_bars] - 1` | completed candle close prices | positive values support long; negative values support short | exhaustion, reversal after extension, regime shifts, single-year dominance, close-to-close proxy weakness |
| `ATR_at_entry` | `ATR(14, RMA)` using completed candles through signal candle `t` | completed high/low/close | defines symmetric stop and take-profit distance | high volatility can widen exits; low volatility can trigger invalid/warm-up skips or noisy fills |

Explicitly excluded factors:

- volume filter.
- FVG.
- Order Block.
- market regime filter.
- higher-timeframe confirmation beyond the tested interval itself.
- DXY filter.
- equity index filter.
- ETF/fund-flow filter.
- alternative momentum definitions.
- parameter optimization after seeing results.

## 6. Pattern or Signal Logic

- Pattern name: `LOOKBACK_RETURN_MOMENTUM`
- Long signal interpretation:

```text
momentum_return >= entry_threshold
```

- Short signal interpretation:

```text
momentum_return <= -entry_threshold
```

- No-trade condition:

```text
-entry_threshold < momentum_return < entry_threshold
```

- Confirmation condition: none. V2 remains a pure close-to-close momentum diagnostic.
- Invalid setup condition:
  - fewer than `lookback_bars` prior completed closes are available;
  - prior close used in the denominator is missing, zero, negative, or invalid;
  - `entry_threshold <= 0`;
  - `lookback_bars <= 0`;
  - `holding_bars <= 0`;
  - ATR is unavailable, zero, negative, or non-finite at entry.
- Look-ahead prevention rule:
  - compute the signal only from completed candles up to index `t`;
  - do not use any candle after `t` when computing `momentum_return`;
  - ATR uses completed candles through signal candle `t`;
  - exit checks start from the next completed candle after entry.
- Report-facing rule summary: V2 enters in the direction of a meaningful completed close-to-close return on `1h`, `4h`, or `1d`, then tests whether symmetric `1 ATR` stop/take-profit exits reveal a raw no-cost edge.

## 6.1 Timeframe Rationale

| Timeframe | Why It Is Included | Main Risk |
|---|---|---|
| `1h` | Captures intraday to one-day information propagation while reducing minute-level microstructure noise. | Still affected by intraday reversals, liquidation bursts, and session noise. |
| `4h` | Captures session-level continuation and cross-session position adjustment. | Fewer trades and possible lag after fast information shocks. |
| `1d` | Captures daily information diffusion, fund-flow response, macro/risk-flow propagation, and slower allocation effects. | Lower sample size, higher regime dependence, and potential single-year dominance. |

Predeclared primary grid:

| Interval | Variant | lookback_bars | holding_bars | entry_threshold | Interpretation |
|---|---|---:|---:|---:|---|
| `1h` | `1h_1d_to_6h` | 24 | 6 | 0.005 | Last 1 day return -> next 6 hours |
| `1h` | `1h_3d_to_1d` | 72 | 24 | 0.015 | Last 3 days return -> next 1 day |
| `4h` | `4h_1d_to_12h` | 6 | 3 | 0.010 | Last 1 day return -> next 12 hours |
| `4h` | `4h_3d_to_1d` | 18 | 6 | 0.030 | Last 3 days return -> next 1 day |
| `1d` | `1d_1w_to_1d` | 7 | 1 | 0.030 | Last 1 week return -> next 1 day |
| `1d` | `1d_1m_to_1w` | 30 | 7 | 0.100 | Last 1 month return -> next 1 week |

Grid rationale:

- The grid is small and theory-driven to reduce data snooping.
- Thresholds are larger than short-timeframe thresholds because higher timeframes require more meaningful moves.
- Optional secondary grids must not run unless a later task explicitly assigns them.

## 7. Entry Logic

Long entry:

- Enter long only when no position is open.
- Required signal:

```text
momentum_return >= entry_threshold
```

- Entry price: signal candle close.

Short entry:

- Enter short only when no position is open.
- Required signal:

```text
momentum_return <= -entry_threshold
```

- Entry price: signal candle close.

Execution timing:

- Signal candle: completed candle at index `t`.
- Execution candle: same completed signal candle, using close price.
- Market/limit assumption: offline research market-on-signal-close fill through the existing strategy engine requested-price path.
- Same-candle entry/exit rule:
  - stop/take-profit/time exits are not evaluated on the entry candle;
  - exit checks start from the next completed candle after entry;
  - if an exit occurs on a candle, the strategy should not open a new position on that same candle.

Flat/no-trade behavior:

- Do not enter during the initial insufficient-lookback region.
- Do not enter if a position is already open.
- Do not reverse on an opposite signal.

## 8. Exit Logic

- Stop loss:

```text
R_distance = ATR_at_entry
ATR_at_entry = ATR(14, RMA, completed candles through signal candle t)

LONG stop_price = entry_price - (1.0 * ATR_at_entry)
SHORT stop_price = entry_price + (1.0 * ATR_at_entry)
```

- Take profit:

```text
LONG take_profit_price = entry_price + (1.0 * ATR_at_entry)
SHORT take_profit_price = entry_price - (1.0 * ATR_at_entry)
```

- Time exit:

```text
if bars_since_entry >= holding_bars:
    exit at close
```

Time-exit rationale:

- `holding_bars` defines the forecast horizon being tested. The strategy asks whether a lookback return over a declared past window predicts continuation over a declared future window.
- Without time exit, a position could remain open until stop or target much later, turning the test into an indefinite trend-following or volatility breakout diagnostic rather than a finite-horizon information-delay test.
- Time exit also prevents stale signals from being carried after the original information-diffusion window has likely passed.
- A high time-exit share is not automatically good or bad. It can mean:
  - the signal direction was not strong enough to reach `1 ATR` target before the forecast window expired;
  - ATR was too wide for the selected holding horizon;
  - the move continued slowly but not enough for the target;
  - the holding window was too short for the chosen lookback horizon;
  - the market was choppy or regime-mismatched.
- Report interpretation must connect time-exit share to result quality. If a positive variant has many time exits, check whether time exits carry positive average R or whether stop/target exits do most of the work. If a negative variant has many time exits, check whether the forecast horizon is too short or whether the signal is not directional enough.
- Future improvements should be predeclared:
  - compare holding horizons while keeping the lookback/threshold fixed;
  - separate target/stop-dominated variants from time-exit-dominated variants;
  - test adaptive holding windows only after documenting the rule before execution;
  - evaluate whether regime labels explain time-exit dominance.

- Early exit: none.
- Opposite signal handling:
  - do not reverse;
  - do not close early due to opposite signal;
  - while a position is open, use only stop loss, take profit, or time exit.
- Stop/target same-candle priority:
  - if both stop loss and take profit are reachable in the same candle, assume stop loss happens first.
  - This applies to both long and short positions.
- Exit ordering:
  - check stop loss first;
  - check take profit second;
  - check time exit third.

Risk/exit settings:

```text
risk_distance_mode = atr
atr_period = 14
atr_smoothing = RMA
stop_loss_atr_multiple = 1.0
take_profit_atr_multiple = 1.0
minimum_atr_bps = 0.0
```

## 9. Risk and Position Sizing

- Position sizing:

```text
starting_cash = 1000000
starting_cash_currency = KRW
quote_currency = USDT
krw_per_usdt = 1500
position_sizing_mode = cash_fraction
position_sizing_value = 0.10
```

- Risk per trade:
  - `1R = ATR_at_entry`
  - stop distance: `1 ATR`
  - take-profit distance: `1 ATR`
- Max concurrent positions: one open position maximum.
- Long/short constraints:
  - long and short signals are both supported for research;
  - flat-only/no-reverse;
  - no overlapping positions.
- Cash/margin assumptions:
  - no live trading;
  - no real margin, borrow, futures, leverage, liquidation, or funding assumptions;
  - short behavior remains simulated research accounting only.
- Research-only constraints:
  - V2 is not deployable from this document or from a no-cost result.
  - Cost-aware validation and OOS/WFO validation are separate later tasks.

## 10. Cost and Execution Assumptions

- Entry fee: `0 bps`
- Exit fee: `0 bps`
- Round-trip fee: `0 bps`
- Spread: `0 bps`
- Slippage: `0 bps`
- Minimum slippage: `0 bps`
- Volatility slippage: `0`
- Fee-adjusted break-even: not evaluated in this task because this is a no-cost gross diagnostic.
- Slippage-adjusted break-even: not evaluated in this task because this is a no-cost gross diagnostic.

No-cost diagnostic settings:

```text
cost_profile = zero by effective all-zero manual settings
cost_aware_entry_filter_enabled = false
maker_fee_bps = 0
taker_fee_bps = 0
spread_bps = 0
slippage_bps = 0
minimum_slippage_bps = 0
volatility_slippage_multiplier = 0
```

Boundary:

- The report must clearly state this is gross/no-cost evidence only.
- A positive result does not imply deployability.
- A negative result weakens this exact close-to-close HTF proxy and symmetric ATR-1 exit geometry, but does not reject momentum mechanisms generally.

## 11. Expected Value

```text
E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost
```

- Expected win rate: not assumed; must be measured.
- Expected average win: approximately bounded by `1 ATR` take-profit when target exits dominate, but time exits can create different outcomes.
- Expected average loss: approximately bounded by `1 ATR` stop-loss when stop exits dominate, but time exits can create different outcomes.
- Expected R multiple: must be measured as average R or equivalent metric from completed trades.
- Required break-even win rate:
  - under pure symmetric `1 ATR` stop/take-profit and zero cost, a simplified target/stop-only model needs a hit rate above roughly 50%;
  - time exits and intra-candle stop-first ambiguity can shift the realized threshold.
- Minimum acceptable trade count: must be sufficient to avoid a one-year, one-side, or one-outlier conclusion; report sample weakness explicitly when trade count is low.
- Cost and reward/risk explanation for reports:
  - V2 intentionally removes transaction costs to isolate raw directional and exit geometry behavior.
  - If V2 is positive no-cost, the next task must reintroduce realistic fees, spread, and slippage before any viability claim.
  - If V2 is negative no-cost, the tested HTF close-to-close proxy is weak under this grid, but other momentum definitions or regime filters remain untested.

## 12. Validation Plan

- In-sample window:
  - `2021-01-01T00:00:00Z <= candle time < 2026-06-01T00:00:00Z`
  - This task is a broad historical diagnostic, not an OOS/WFO validation.
- Out-of-sample window: out of scope.
- Walk-forward windows: out of scope.
- Multi-timeframe checks:
  - compare `1h`, `4h`, and `1d` as separate primary intervals.
  - do not use higher-timeframe confirmation filters.
- Fee stress: out of scope.
- Slippage stress: out of scope.
- Outlier removal: out of scope for execution, but report should flag if one year or one side dominates.
- Random/baseline comparison: out of scope.
- Buy-and-hold comparison: optional report context only if already available; do not expand execution scope to add new benchmark infrastructure.
- Long-only and short-only attribution: required in the report.
- Regime/session attribution: yearly attribution required; finer regime/session attribution is out of scope.
- Regime boundary for Task 330:
  - Task 330 does not apply bull/bear, volatility, liquidity, macro, ETF-flow, DXY, or risk-on/risk-off filters.
  - Yearly attribution is only a coarse proxy for regime. It can show that one calendar year dominates, but it does not isolate trend state, volatility state, drawdown/recovery state, or liquidity state.
  - The report must mention that a positive or negative aggregate result may be regime-specific.
  - A recommended follow-up should predeclare objective regime labels before seeing results, such as:
    - price above/below a long moving average for trend state;
    - realized volatility or ATR percentile for volatility state;
    - drawdown/recovery state from rolling highs;
    - trading-value or volume percentile for liquidity state;
    - optional external risk-flow proxies only if their data source and timestamp alignment are documented.
  - Regime diagnostics must not tune entry thresholds after seeing which regime wins.

Required data preflight:

- For each interval:
  - duplicate timestamp count;
  - gap count;
  - first candle;
  - last candle;
  - expected count if interval support permits;
  - whether the fixed preferred end exists.
- Determine latest common complete end timestamp across `1h`, `4h`, and `1d` if the preferred end is unavailable for any interval.

Required primary runs:

| Interval | Variant | lookback_bars | holding_bars | entry_threshold |
|---|---|---:|---:|---:|
| `1h` | `1h_1d_to_6h` | 24 | 6 | 0.005 |
| `1h` | `1h_3d_to_1d` | 72 | 24 | 0.015 |
| `4h` | `4h_1d_to_12h` | 6 | 3 | 0.010 |
| `4h` | `4h_3d_to_1d` | 18 | 6 | 0.030 |
| `1d` | `1d_1w_to_1d` | 7 | 1 | 0.030 |
| `1d` | `1d_1m_to_1w` | 30 | 7 | 0.100 |

## 13. Failure Modes

- Cost-dominated failure:
  - Not tested in V2 because costs are deliberately zero.
  - If V2 passes no-cost, cost-aware validation remains mandatory.
- Low trade-count failure:
  - `1d` variants can produce few trades, especially with high thresholds.
  - Report inference strength must be reduced when sample size is weak.
- Side concentration:
  - If only long or only short trades drive the result, do not generalize to symmetric momentum.
- Outlier dependence:
  - If one large trade, one month, or one year dominates, report it as regime/outlier-specific.
- Choppy regime:
  - Repeated reversals can produce stop-loss dominated exits.
- Trend regime:
  - Trend regimes may help momentum, but can also enter late after exhaustion.
- High-volatility execution distortion:
  - ATR expands during stress, which can widen stop/target distances and change holding behavior.
- Same-candle ambiguity:
  - Stop-first policy is conservative when stop and take-profit are both reachable in the same candle.
- Proxy mismatch:
  - Close-to-close return may not capture the actual information-delay mechanism if volume, order flow, macro synchronization, or risk-flow alignment is the driver.
- Horizon mismatch:
  - If `1h`/`4h`/`1d` do not improve on the minute-level baseline, this weakens the current close-to-close information-delay proxy across the tested horizons.
  - It still does not reject all momentum mechanisms because regime filters, alternative definitions, volume/order-flow proxies, macro/risk-flow alignment, and OOS/WFO remain untested.
- Time-exit dominance:
  - If time exits dominate a variant, the report must explain whether the selected holding window is too short, the ATR target is too wide, or the signal is not producing enough continuation within the declared horizon.
- Regime omission:
  - If performance differs materially by year or side, the result should be treated as regime-sensitive until a predeclared regime attribution task is run.

## 14. Required Artifacts

- Saved backtest runs:
  - required if execution proceeds beyond strategy-document prerequisite.
  - Persisted run IDs must be recorded in the task report and compact summary JSON.
- Trade log:
  - use persisted run data or saved output if available.
- Equity curve:
  - not required as an image in this task unless a later report task asks for it.
- Cost breakdown:
  - must show `total_cost = 0` and zero-cost assumptions in summary/report.
- Representative win/loss trades:
  - not required unless a later daily/Tistory report task asks for them.
- Daily report payload:
  - required for Task 330 execution.
- Daily report images:
  - required for Task 330 execution.
- Draft report:
  - task report markdown under `reports/` is required if validation executes.
- Tistory report:
  - Task 330 requires `report-ko.html` with V1/V2 comparison, detailed timeframe-change rationale, time-exit explanation, regime limitation, and next-task recommendation.
- Compact summary JSON:
  - required under `reports/` if validation executes.

## 15. Implementation Notes

- Files/modules expected to change:
  - This document is the required strategy-document prerequisite.
  - If later execution reveals the existing runner already supports all required overrides, no strategy code change should be made.
  - If metadata must record `v2`, change only the minimal strategy/runner metadata path needed and test it.
- Reusable components:
  - `quant_bitcoin/strategies/lookback_return_momentum.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `quant_bitcoin/indicators/atr.py`
  - `quant_bitcoin/market_data/postgres_provider.py`
  - `quant_bitcoin/market_data/candle_validation.py`
  - `quant_bitcoin/market_data/binance_backfill.py`
  - `quant_bitcoin/market_data/binance_backfill_cli.py`
- Tests required if implementation changes:
  - momentum config accepts explicit HTF grid overrides;
  - strategy version or metadata records V2/HTF variant if code changes are made for versioning;
  - no-cost settings keep all transaction-cost fields at zero;
  - cost-aware entry filter is disabled;
  - `1 ATR` stop exits correctly;
  - `1 ATR` take-profit exits correctly;
  - invalid ATR blocks entries;
  - signal uses completed close-to-close data only;
  - CLI can run `LOOKBACK_RETURN_MOMENTUM` on `1h`, `4h`, and `1d`.
- Backward compatibility concerns:
  - Current code metadata may still report `strategy_version = v1`; if a later task needs persisted V2 metadata, implement a narrow metadata override rather than changing old V1 semantics.
  - Do not change existing V1 saved-run interpretation.
- Data persistence notes:
  - Native `1h`, `4h`, and `1d` support exists in the public REST backfill allowlist and candle continuity deltas as of Task 325.
  - Do not run real DB backfill unless the assigned execution scope explicitly allows it after data preflight.

## 16. Safety Boundary

- This strategy is research-only unless a later task explicitly changes that status.
- This strategy must not call exchange order/account/private endpoints.
- This strategy must not require secrets, API keys, or `.env` changes.
- This strategy must not place real orders.
- Binance public candle backfill may be used only for market-data collection when explicitly assigned.
- Strategy code must not fetch data or call exchange APIs.
- Live trading remains out of scope.

## 17. Change Log

- 2026-06-03: Created V2 strategy document for Task 326. Documented the higher-timeframe information-delay hypothesis, selected `1h`/`4h`/`1d` timeframes, no-cost gross diagnostic boundary, symmetric `1 ATR` stop/take-profit geometry, predeclared six-variant primary grid, required data preflight, bounded interpretation rules, Task 324 artifact absence, implementation notes, and safety boundary. No backtest, data backfill, strategy code change, DB mutation, report generation, live trading behavior, exchange endpoint behavior, secret, or `.env` change was performed.
- 2026-06-03: Task 326 validation executed where native data continuity allowed it. `1h` variants were blocked because native Binance public `1h` candles had 7 internal gaps / 14 missing open times and bounded public backfill returned 0 candles for those gaps. `4h`/`1d` no-cost symmetric `1 ATR` runs were persisted as `1213`-`1216`; three of four executable variants were positive gross/no-cost, with best `1d_1m_to_1w` at `+21.64%`. No strategy code, cost assumption, signal rule, live trading behavior, order/account/private endpoint behavior, secret, or `.env` change was added.
- 2026-06-04: Updated for Task 330 before rerun. Added the V1-to-V2 comparison logic, the reason the comparison group changes from `1m`/`5m`/`15m` to `1h`/`4h`/`1d`, expanded academic reference links, detailed time-exit rationale and failure modes, fallback common-window policy, and regime-omission interpretation requirements. No strategy code, cost assumption, signal rule, live trading behavior, order/account/private endpoint behavior, secret, or `.env` change was added by this document update.
