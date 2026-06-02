# LOOKBACK_RETURN_MOMENTUM v1 Strategy Document

## 1. Strategy Identity

- Strategy name: `LOOKBACK_RETURN_MOMENTUM`
- Strategy version: `v1`
- Strategy slug: `lookback_return_momentum`
- Stable strategy description: 과거 일정 구간의 수익률을 확인하는 모멘텀 전략.
- Owner task: `TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC`
- Revision task: `TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION`
- Revision task: `TASK_309_LOOKBACK_RETURN_MOMENTUM_ATR_RISK_EXIT_REVISION`
- Revision task: `TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC`
- Status: `research_only`
- Last updated: 2026-06-01

## 2. Market and Data Scope

- Exchange: Binance public market data for research.
- Market: BTC/USDT spot-style OHLCV research data.
- Symbol: `BTCUSDT`
- Primary timeframe: `1m`, `5m`, and `15m`.
- Higher timeframes: none. This baseline must not use higher-timeframe confirmation or filters.
- Intended Task 305 validation period:
  - start inclusive: `2026-02-01T00:00:00Z`
  - end exclusive: `2026-05-01T00:00:00Z`
- Required data: completed OHLCV candles. Signal logic uses close prices only.
- Known data limitations:
  - The signal requires at least `lookback_bars` prior closes.
  - The first `lookback_bars` candles must not produce a signal.
  - Stop/target simulation needs candle high/low data even though entry signal uses only close data.
  - ATR risk distance requires enough completed high/low/close candles for `ATR(14)` with full-window warm-up.
  - A signal must not enter while ATR is unavailable, zero, negative, or non-finite.
  - Task 311 can optionally require `ATR_at_entry / entry_price * 10000 >= minimum_atr_bps` for cost-feasibility diagnostics.

## 3. Market Phenomenon

- Phenomenon: recent close-to-close directional return may persist over a short future holding window.
- Why it may appear in BTC: BTCUSDT can show short-term continuation when recent order flow, aggressive buying/selling, or forced participation pushes price in one direction.
- Economic or microstructure rationale: if the last `N` completed candles moved far enough in one direction, that move may indicate temporary imbalance between buy and sell pressure. If that imbalance does not immediately disappear, the next `M` candles may continue in the same direction.
- Why this baseline is tested:
  - it is a simple falsifiable baseline for whether recent BTCUSDT close-to-close directional pressure persists at all.
  - it creates a low-complexity reference before adding pattern filters, trend filters, or higher-timeframe confirmation.
  - it separates "directional signal exists" from "directional signal survives costs and reward/risk constraints".
  - it provides a deliberately plain comparator for later, more complex strategy families.
- Expected market regime: short-term directional pressure with enough follow-through to overcome fees, spread, slippage, and losing trades.
- Regimes where this should not work:
  - choppy mean-reverting ranges.
  - low-volatility noise where `momentum_return` barely clears the threshold.
  - whipsaw regimes where recent continuation quickly reverses.
  - high-cost conditions where edge is smaller than round-trip transaction costs.

Theory and reference notes:

- Jegadeesh and Titman (1993), "Returns to Buying Winners and Selling Losers", documents intermediate-horizon momentum in equities and is used here only as a general reference for delayed information diffusion and continuation, not as proof that minute-level BTC momentum must work.
- Moskowitz, Ooi, and Pedersen (2012), "Time Series Momentum", supports the broader idea that recent own-asset returns can carry directional information across liquid assets, while this project must still validate whether that survives BTCUSDT intraday costs.
- The strategy assumes short-term price pressure can persist because information is not always incorporated instantly, order-flow imbalance can continue over several candles, and trend-following participation can reinforce recent moves.
- The same mechanism can fail when the recent move is exhaustion, when liquidity mean-reverts quickly, or when average follow-through is smaller than the ATR-based stop/target distance plus transaction costs.

## 4. Hypothesis

- Primary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 entry_threshold 이상이면 이후 holding_bars 동안 같은 상승 방향 수익률을 보일 것이다.`
- Secondary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 -entry_threshold 이하이면 이후 holding_bars 동안 같은 하락 방향 수익률을 보일 것이다.`
- Economic constraint: direction accuracy alone is not enough. Average profit when direction is correct must exceed average loss when direction is wrong plus fees, spread, and slippage.
- Cost-aware validation constraint: a directional signal is not enough to enter if the planned take-profit and stop-loss structure does not leave non-negative net reward and acceptable net reward/risk after estimated round-trip costs.

## 5. Factors and Indicators

Only one factor is allowed in the first version.

| Factor | Formula / Definition | Required Data | Expected Direction | Confounders |
|---|---|---|---|---|
| `momentum_return` | `close[t] / close[t - lookback_bars] - 1` | completed candle close prices | positive values support long; negative values support short | noise, reversal after extension, cost drag, same-candle stop/target ambiguity |

Explicitly excluded factors:

- General ATR entry filter. ATR is allowed as the risk/exit distance after Task 309. Task 311 additionally allows an explicit `minimum_atr_bps` volatility floor only for the assigned reward/cost geometry diagnostic; it must be disabled by default with `minimum_atr_bps = 0.0`.
- volume filter.
- trend score.
- FVG.
- Order Block.
- higher-timeframe filter.
- liquidity target.
- any other confirmation filter not listed in this document.

## 6. Pattern or Signal Logic

- Pattern name: `LOOKBACK_RETURN_MOMENTUM`
- Momentum formula:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

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

- Confirmation condition: none beyond the threshold rule. This strategy is a pure momentum baseline.
- Invalid setup condition:
  - fewer than `lookback_bars` prior completed closes are available.
  - prior close used in the denominator is missing or invalid.
  - `entry_threshold <= 0`.
  - `lookback_bars <= 0`.
  - `holding_bars <= 0`.
- Look-ahead prevention rule:
  - compute the signal only from completed candles up to index `t`.
  - do not use any candle after `t` when computing `momentum_return`.
  - v1 implementation enters at the completed signal candle close.

## 6.1 Timeframe Rationale

Task 305 compares `1m`, `5m`, and `15m` because each interval tests a different trade-off between signal speed, noise, turnover, and transaction-cost drag.

| Timeframe | Why It Is Included | Main Risk |
|---|---|---|
| `1m` | Highest-turnover and fastest-reaction version. It checks whether very short continuation exists immediately after recent pressure. | Most sensitive to fees, spread, slippage, and microstructure noise. |
| `5m` | Middle layer between noisy `1m` and slower `15m`. It tests whether a one-hour lookback and thirty-minute hold can reduce churn while preserving continuation. | May still trade often enough to be cost-sensitive, and may lag fast reversals. |
| `15m` | Lower-turnover comparison. It tests whether slower candles reduce cost drag and whipsaw. | Produces fewer trades and responds more slowly, so sample size and delayed entries can be problems. |

Concrete default window meaning:

| Timeframe | lookback_bars | holding_bars | entry_threshold | Interpretation |
|---|---:|---:|---:|---|
| `1m` | 20 | 5 | 0.001 | last 20 minutes -> next 5 minutes |
| `5m` | 12 | 6 | 0.0015 | last 1 hour -> next 30 minutes |
| `15m` | 8 | 4 | 0.002 | last 2 hours -> next 1 hour |

## 7. Entry Logic

Long entry:

- Enter long only when no position is open.
- Required signal:

```text
momentum_return >= entry_threshold
```

- Example default for `1m`:

```text
lookback_bars = 20
entry_threshold = 0.001
```

- Interpretation: if price rose at least `0.1%` over the last 20 completed 1-minute candles, the strategy marks a long entry candidate.

Short entry:

- Enter short only when no position is open.
- Required signal:

```text
momentum_return <= -entry_threshold
```

- Example default for `1m`:

```text
lookback_bars = 20
entry_threshold = 0.001
```

- Interpretation: if price fell at least `0.1%` over the last 20 completed 1-minute candles, the strategy marks a short entry candidate.

Flat/no-trade entry:

- Do not enter when:

```text
-entry_threshold < momentum_return < entry_threshold
```

- Do not enter during the initial insufficient-lookback region.
- Do not enter if a position is already open, regardless of whether the new signal is the same direction or opposite direction.

Execution timing:

- Signal candle: completed candle at index `t`.
- Execution price: signal candle close.
- Market/limit assumption: research-only market-on-signal-close fill using the existing strategy engine `requested_price` path.
- Same-candle entry/exit rule:
  - stop/target/time exits are not evaluated on the entry candle.
  - exit checks start from the next completed candle after entry.
  - if an exit occurs on a candle, the strategy does not open a new position on that same candle.

Cost-aware entry gate for Task 305 validation:

- A valid momentum signal may still be rejected before entry if estimated transaction costs make the planned reward/risk unattractive.
- The gate version is `cost_aware_entry_filter_v1`.
- Task 305 validation defaults:

```text
cost_aware_entry_filter_enabled = true
min_net_reward_bps = 0.0
min_net_rr = 1.0
liquidity_role = taker
```

- The gate uses the planned entry, stop, and take-profit levels from the active v1 risk model.
- For Task 309 and later ATR-risk runs, the gate computes planned gross reward and risk from the ATR-derived stop and take-profit distances.
- Task 311 diagnostic adds one explicit pre-cost volatility floor when configured:

```text
atr_bps = ATR_at_entry / entry_price * 10000
entry allowed by this filter only if atr_bps >= minimum_atr_bps
```

- `minimum_atr_bps = 0.0` disables the floor and preserves the Task 309 behavior.
- If the floor rejects a candidate, the skip reason should be `ATR_TOO_SMALL_FOR_COST`.
- If cost-aware filtering is enabled and the filter cannot compute a valid decision, the entry must fail closed.
- A blocked signal is a skipped entry, not a new strategy family or a live-trading action.

## 8. Exit Logic

- Stop loss:
  - Task 309 v1 risk distance:

```text
R_distance = ATR_at_entry
ATR_at_entry = ATR(14, RMA, completed candles through signal candle t)
```

  - Long conceptual formula:

```text
stop_price = entry_price - (stop_loss_atr_multiple * ATR_at_entry)
```

  - Short conceptual formula:

```text
stop_price = entry_price + (stop_loss_atr_multiple * ATR_at_entry)
```

- Take profit:
  - Long conceptual formula:

```text
take_profit_price = entry_price + (take_profit_atr_multiple * ATR_at_entry)
```

  - Short conceptual formula:

```text
take_profit_price = entry_price - (take_profit_atr_multiple * ATR_at_entry)
```

- Default ATR risk settings for Task 309:

```text
risk_distance_mode = atr
atr_period = 14
atr_smoothing = RMA
stop_loss_atr_multiple = 1.0
take_profit_atr_multiple = 1.0
```

- Task 311 asymmetric reward/cost diagnostic settings:

```text
risk_distance_mode = atr
atr_period = 14
atr_smoothing = RMA
stop_loss_atr_multiple = 1.0
take_profit_atr_multiple in {2.0, 2.5, 3.0}
minimum_atr_bps in {0.0, 20.0}
```

- Task 311 does not change the momentum signal. It changes only the planned reward distance and the optional minimum ATR volatility floor.

- ATR no-lookahead timing:
  - ATR uses completed candles through the signal candle `t`.
  - The v1 implementation enters at the signal candle close, so high/low/close of candle `t` are known when ATR is read.
  - Do not use any candle after `t` to compute `ATR_at_entry`.
  - Exit checks still start from the next completed candle after entry.
- Invalid ATR handling:
  - If ATR is missing, invalid, zero, negative, or non-finite, skip the entry candidate.
  - The skipped entry must expose a diagnostic reason such as `INVALID_ATR_RISK_DISTANCE`.

- Time exit:

```text
if bars_since_entry >= holding_bars:
    exit at close
```

- Early exit: none.
- Opposite signal handling:
  - Do not reverse.
  - Do not close early due to opposite signal.
  - While a position is open, use only stop loss, take profit, or time exit.
- Stop/target same-candle priority:
  - If both stop loss and take profit are reachable in the same candle, assume stop loss happens first.
  - This applies to both long and short positions.
- Exit ordering:
  - first check stop loss.
  - then check take profit.
  - then check time exit at close.
  - therefore, if the final holding candle also touches stop or target, stop/target takes precedence over time exit.

Risk-distance decision:

- `1R` is now one ATR at entry for the assigned Task 309 workflow.
- Formula:

```text
R_distance = ATR_at_entry
ATR_at_entry = ATR(14, RMA) at the completed signal candle
```

- This replaces the previous fixed-percentage risk distance used by earlier Task 297/305/308 diagnostics.
- Earlier saved runs using `risk_distance_pct = 0.002` must be interpreted as fixed-percentage diagnostics and distinguished from Task 309 ATR-risk runs by metadata.
- This strategy still must not use a general ATR entry filter in v1. The only allowed ATR entry filter for Task 311 is the explicitly assigned `minimum_atr_bps` floor for cost-feasibility diagnostics, and it defaults to disabled.

## 9. Risk and Position Sizing

- Position sizing: not defined in this document. A later implementation task must use existing project sizing conventions or explicitly document new sizing behavior.
- Risk per trade:
  - `risk_distance_mode = atr`.
  - `atr_period = 14`.
  - `atr_smoothing = RMA`.
  - `stop_loss_atr_multiple = 1.0`.
  - default `take_profit_atr_multiple = 1.0`.
  - Task 311 diagnostic `take_profit_atr_multiple` candidates: `2.0`, `2.5`, `3.0`.
  - Task 311 diagnostic `minimum_atr_bps` candidates: `0.0`, `20.0`.
  - `1R = ATR_at_entry`.
- Max concurrent positions: one open position maximum.
- Long/short constraints:
  - long and short signals are both supported for research.
  - no reverse entry in v1.
  - no overlapping positions.
- Cash/margin assumptions:
  - no live trading.
  - no real margin, borrow, futures, leverage, liquidation, or funding assumptions.
  - any short simulation must remain research accounting only unless a later task defines broader execution assumptions.
- Research-only constraints:
  - strategy is not deployable from this document alone.
  - implementation and backtest require a later assigned task.

## 10. Cost and Execution Assumptions

- Entry fee: set by the active backtest cost configuration.
- Exit fee: set by the active backtest cost configuration.
- Round-trip fee: must be included in validation before any performance claim.
- Spread: must be included in validation before any performance claim.
- Slippage: must be included in validation before any performance claim.
- Minimum slippage: must follow existing project cost assumptions if available.
- Volatility slippage: must follow existing project cost assumptions if available.
- Fee-adjusted break-even: must be reported in future validation because the signal threshold is small.
- Slippage-adjusted break-even: must be reported in future validation because short holding windows can be cost-sensitive.
- Task 305/309 cost profile: use `conservative_crypto_1m` unless the assigned implementation records a different named cost profile before execution.
- Task 305/309 cost-aware reward/risk gate:
  - Compute planned gross reward from entry to take-profit.
  - Compute planned gross risk from entry to stop.
  - In Task 309 ATR-risk mode, planned reward and risk are both derived from `ATR_at_entry`.
  - Estimate one-side cost from fee, spread, and slippage assumptions.
  - Estimate round-trip cost as `2 * one_side_cost_bps`.
  - Compute:

```text
net_reward_bps = gross_reward_bps - round_trip_cost_bps
net_risk_bps = gross_risk_bps + round_trip_cost_bps
net_rr = net_reward_bps / net_risk_bps
```

  - Reject an entry if:
    - gross reward is non-positive.
    - gross risk is non-positive.
    - estimated net reward is below `min_net_reward_bps`.
    - estimated net reward/risk is below `min_net_rr`.
    - required cost inputs are unavailable while the filter is enabled.

Task 311 reward/cost geometry expectation:

- With `stop_loss_atr_multiple = 1.0` and `take_profit_atr_multiple = 1.0`, positive round-trip cost forces `net_rr < 1.0`.
- Raising `take_profit_atr_multiple` can make `gross_reward_bps` large enough to clear both cost and `min_net_rr`.
- For a long or short candidate using ATR distance:

```text
gross_reward_bps = atr_bps * take_profit_atr_multiple
gross_risk_bps = atr_bps * stop_loss_atr_multiple
net_reward_bps = gross_reward_bps - round_trip_cost_bps
net_risk_bps = gross_risk_bps + round_trip_cost_bps
net_rr = net_reward_bps / net_risk_bps
```

- For `min_net_rr = 1.0`, a candidate needs:

```text
gross_reward_bps >= gross_risk_bps + (2 * round_trip_cost_bps)
```

- The `minimum_atr_bps` floor is a diagnostic guard against tiny ATR regimes where reward distance remains too small relative to estimated costs.

Cost-aware metadata requirements:

- Accepted entries and skipped-entry diagnostics should expose:
  - enabled.
  - blocked.
  - block reason.
  - gross reward bps.
  - gross risk bps.
  - estimated one-side cost bps.
  - estimated round-trip cost bps.
  - net reward bps.
  - net risk bps.
  - net RR.
  - minimum net reward bps.
  - minimum net RR.
  - risk distance mode.
  - ATR period.
  - ATR smoothing method.
  - ATR value at entry.
  - stop ATR multiple.
  - take-profit ATR multiple.
  - minimum ATR bps.
  - ATR bps at entry.

Execution assumptions still requiring future implementation decision:

- None for v1 implementation mechanics. Future validation tasks still need to choose cost profiles, research windows, and interpretation thresholds before making any performance claim.

Implemented v1 execution assumptions:

- Entry price timing: signal candle close.
- Stop/target intrabar check order: stop loss first, then take profit.
- Time exit order: after stop/target checks on the final holding candle.
- Entry candle exits: disabled.
- Same-candle re-entry after exit: disabled.

## 11. Expected Value

```text
E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost
```

- Expected win rate: unknown before backtesting.
- Expected average win: bounded by the active `take_profit_atr_multiple` when target is hit, otherwise time-exit close result.
- Expected average loss: bounded by `stop_loss_atr_multiple = 1.0` when stop is hit, otherwise time-exit close result.
- Expected R multiple: unknown before backtesting.
- Required break-even win rate:
  - approximately greater than `1 / (1 + 1.0) = 50%` before costs for pure 1 ATR loss and 1 ATR win outcomes.
  - higher than 50% after fees, spread, slippage, time exits, and partial-sized outcomes.
  - lower before-cost win rates can be viable only when the active take-profit multiple is greater than the stop multiple and enough targets are reached.
- Minimum acceptable trade count: to be defined by a later validation task before interpreting results.

## 12. Validation Plan

- In-sample / diagnostic validation window for Task 305:

```text
2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z
```

- Task 309 ATR-risk validation:
  - reuse the same February-to-May diagnostic window.
  - reuse the Task 308 lower `entry_threshold` grid without post-result tuning.
  - compare raw candidates, accepted entries, cost-blocked entries, gross/net PnL, cost drag, expectancy, and exit mix against the Task 308 no-entry result.

- Task 311 ATR reward/cost geometry diagnostic:
  - reuse the same February-to-May diagnostic window.
  - use the lowest Task 308 threshold per interval:
    - `1m`: `lookback_bars = 20`, `holding_bars = 5`, `entry_threshold = 0.0004`.
    - `5m`: `lookback_bars = 12`, `holding_bars = 6`, `entry_threshold = 0.0006`.
    - `15m`: `lookback_bars = 8`, `holding_bars = 4`, `entry_threshold = 0.0008`.
  - keep `stop_loss_atr_multiple = 1.0`.
  - test `take_profit_atr_multiple in {2.0, 2.5, 3.0}`.
  - test `minimum_atr_bps in {0.0, 20.0}`.
  - keep the cost-aware gate enabled with `min_net_reward_bps = 0.0`, `min_net_rr = 1.0`, and `conservative_crypto_1m`.
  - no post-result tuning is allowed inside this task.
  - report raw candidates, accepted entries, cost-blocked entries, ATR-too-small entries, invalid ATR entries, trade count, gross/net PnL, realized costs, expectancy or average net R, and comparison against Task 309.

- Out-of-sample window: required before promotion beyond diagnostic research.
- Walk-forward windows: required before promotion beyond diagnostic research.
- Multi-timeframe checks:
  - execute separately on `1m`, `5m`, and `15m`.
  - do not use higher-timeframe filters.
- Task 305/309 data requirement:
  - `1m`, `5m`, and `15m` local candles must be preflighted for the full February-to-May diagnostic window.
  - if `5m` is missing or discontinuous, a bounded public market-data backfill is allowed for this window only.
  - the validation report must record the exact runner end-time semantics and the last included closed candle for each interval.
- Fee stress: required because the signal threshold is small and holding periods are short.
- Slippage stress: required because the strategy may trade frequently.
- Outlier removal: evaluate whether performance depends on a few large trend continuation trades.
- Random/baseline comparison:
  - compare against no-trade baseline.
  - compare against buy-and-hold for the same period.
  - compare against randomized entry direction or shuffled signal diagnostic if assigned later.
- Buy-and-hold comparison: required for the same symbol and period.
- Long-only and short-only attribution: required to identify side concentration.
- Regime/session attribution:
  - optional for diagnostics only.
  - must not become an entry filter in v1.

Required future test cases:

- Signal calculation:
  - `momentum_return` uses `close[t]` and `close[t - lookback_bars]`.
  - rising prices produce positive signal values.
  - falling prices produce negative signal values.
  - unchanged prices produce a value near zero.
- Long signal:
  - `momentum_return >= entry_threshold` produces a long signal.
- Short signal:
  - `momentum_return <= -entry_threshold` produces a short signal.
- No signal:
  - `-entry_threshold < momentum_return < entry_threshold` produces no entry.
- Lookback shortage:
  - no signal before enough historical closes exist.
- Position duplicate prevention:
  - no new entry while a position is open, for same-direction or opposite-direction signals.
- Time exit:
  - exit at close when `bars_since_entry >= holding_bars`.
- Stop/target:
  - long stop and target are calculated separately from short stop and target.
  - `1R` is calculated as completed-candle `ATR_at_entry`.
  - invalid or unavailable ATR blocks entry with a diagnostic reason.
  - configured `minimum_atr_bps` blocks entries with `ATR_TOO_SMALL_FOR_COST` when `atr_bps` is below the floor.
  - long stop/target use `entry_price -/+ ATR_at_entry * multiple`.
  - short stop/target use `entry_price +/- ATR_at_entry * multiple`.
  - same-candle stop and target ambiguity resolves to stop first.

## 13. Failure Modes

- Cost-dominated failure: threshold and holding window may create many small trades whose gross edge is smaller than fees, spread, and slippage.
- Low trade-count failure: high threshold settings may produce too few trades for reliable inference.
- Side concentration: results may depend only on long trades or only on short trades.
- Outlier dependence: a few strong continuation trades may dominate total returns.
- Choppy regime: recent `N`-bar return may mark exhaustion rather than continuation.
- Trend regime: late entries after strong trends may be vulnerable to pullback.
- High-volatility execution distortion: stop and target can both be touched in one candle; stop-first assumption may materially change results.
- Same-candle ambiguity: must be handled conservatively and consistently.
- ATR-distance failure: ATR may still be too small relative to round-trip costs in quiet regimes or too wide relative to achievable follow-through in volatile reversal regimes.
- Minimum ATR floor failure: raising `minimum_atr_bps` may remove too many candidates or concentrate entries in volatile whipsaw regimes.
- Asymmetric target failure: larger take-profit multiples may clear the pre-entry cost gate but fail to realize if follow-through is insufficient before stop or time exit.
- ATR warm-up failure: early signals or sparse data may be skipped because ATR is not valid yet.
- Cost-aware gate over-filtering: the net reward/risk filter may reject most or all high-turnover signals when the planned reward is small relative to estimated round-trip costs.
- Cost-estimation mismatch: the pre-entry estimate may differ from realized fees, spread, and slippage, so both blocked-entry counts and realized net PnL must be reported.

## 14. Required Artifacts

- Saved backtest runs: not created by this task. Required in a later implementation/backtest task.
- Trade log: not created by this task. Required in a later validation task.
- Equity curve: not created by this task.
- Cost breakdown: not created by this task. Required before any performance claim.
- Representative win/loss trades: not created by this task.
- Daily report payload: explicitly out of scope for this task.
- Daily report images: explicitly out of scope for this task.
- Draft report: explicitly out of scope for this task.

## 15. Implementation Notes

- Files/modules expected to change in a later implementation task:
  - completed in Task 297 for the first implementation version:
    - strategy module and strategy runner dispatch.
    - strategy signal implementation.
    - backtest action and exit simulation wiring.
    - CLI parameter wiring.
    - focused tests for signal and exit behavior.
- Reusable components:
  - completed-candle close-return calculation.
  - flat-only position gate.
  - conservative stop-first same-candle handling if not already reusable.
- Tests required:
  - signal calculation.
  - threshold boundaries.
  - insufficient lookback.
  - long/short/no-trade cases.
  - no duplicate entries while a position is open.
  - time exit.
  - fixed percentage `1R = entry_price * 0.002`.
  - ATR risk distance `1R = ATR_at_entry`.
  - invalid ATR handling.
  - long and short stop/target formulas.
  - stop-first same-candle priority.
  - cost-aware gate blocks long and short entries whose net reward/RR is insufficient.
  - cost-aware gate admits long and short entries that meet `min_net_reward_bps` and `min_net_rr`.
  - cost-aware metadata records gross reward/risk, estimated cost, net reward/risk, thresholds, and block reason.
- Backward compatibility concerns:
  - do not alter existing strategy behavior.
  - add new behavior under the explicit `LOOKBACK_RETURN_MOMENTUM` strategy type only.
- Data persistence notes:
  - Task 305 may persist validation runs through the existing offline strategy backtest workflow.
  - saved Task 305 runs should store strategy name, version, parameters, timeframe, costs, `risk_distance_pct = 0.002`, and the cost-aware gate configuration.
  - saved Task 309 runs should store strategy name, version, parameters, timeframe, costs, `risk_distance_mode = atr`, `atr_period = 14`, `atr_smoothing = RMA`, `stop_loss_atr_multiple = 1.0`, `take_profit_atr_multiple = 1.0`, and the cost-aware gate configuration.
  - saved Task 311 runs should additionally store `minimum_atr_bps`, entry `atr_bps`, and skip counts for `ATR_TOO_SMALL_FOR_COST` where available.

## 16. Safety Boundary

- This strategy is research-only unless a later task explicitly changes that status.
- This strategy must not call exchange order/account/private endpoints.
- This strategy must not require secrets, API keys, or `.env` changes.
- This strategy must not place real orders.
- Live trading remains out of scope.
- The following are explicitly excluded from this strategy version:
  - general ATR entry filter, except the explicit Task 311 `minimum_atr_bps` cost-feasibility diagnostic.
  - volume filter.
  - trend score.
  - FVG.
  - Order Block.
  - higher-timeframe filter.
  - liquidity target.
  - reverse entry.
  - partial take profit.
  - trailing stop.
  - image generation.
  - report generation.
  - daily report payload generation.
  - `image_manifest.json` generation.

## 17. Change Log

- 2026-05-31: Created v1 research-only strategy document from Task 296. The document records the pure close-to-close lookback-return momentum baseline, default parameters, `1m`/`5m`/`15m` defaults, signal/entry/exit rules, explicit exclusions, future test plan, and unresolved `1R` base-distance blocker. No strategy code or backtest was executed.
- 2026-05-31: Updated v1 risk-distance decision from owner clarification. `1R` is fixed at `entry_price * 0.002` for v1; ATR-based, swing-based, and recent-range-based risk distances remain out of scope.
- 2026-06-01: Updated for Task 305 before implementation/backtest execution. Clarified why a plain momentum baseline is tested, why `1m`/`5m`/`15m` are compared, and how `cost_aware_entry_filter_v1` computes net reward/risk after estimated round-trip fees, spread, and slippage. Public strategy version remains `v1`; Task 305 results must be distinguished by the enabled cost-aware entry gate metadata and the February-to-May 2026 validation window.
- 2026-06-01: Updated for Task 309 before implementation/backtest execution. Replaced the primary risk distance from fixed `entry_price * 0.002` to `ATR_at_entry`, using `ATR(14)` with RMA smoothing and completed candles through the signal candle. Default stop-loss and take-profit distances are both `1 ATR`; ATR remains excluded as an entry filter. Task 309 validation must distinguish ATR-risk runs from earlier fixed-percentage diagnostics through risk-distance metadata.
- 2026-06-01: Updated for Task 311 before implementation/backtest execution. Documented the asymmetric ATR reward/cost diagnostic: `1 ATR` stop, `2.0/2.5/3.0 ATR` take-profit candidates, `0.0/20.0` minimum ATR bps candidates, preserved cost-aware gate, and no post-result tuning. Clarified that `minimum_atr_bps` is an explicit diagnostic volatility floor and defaults to disabled.
