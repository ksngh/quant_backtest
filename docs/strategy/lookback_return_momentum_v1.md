# LOOKBACK_RETURN_MOMENTUM v1 Strategy Document

## 1. Strategy Identity

- Strategy name: `LOOKBACK_RETURN_MOMENTUM`
- Strategy version: `v1`
- Strategy slug: `lookback_return_momentum`
- Owner task: `TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC`
- Status: `research_only`
- Last updated: 2026-05-31

## 2. Market and Data Scope

- Exchange: Binance public market data for research.
- Market: BTC/USDT spot-style OHLCV research data.
- Symbol: `BTCUSDT`
- Primary timeframe: `1m`, `5m`, and `15m`.
- Higher timeframes: none. This baseline must not use higher-timeframe confirmation or filters.
- Intended test period: to be assigned by a later implementation/backtest task.
- Required data: completed OHLCV candles. Signal logic uses close prices only.
- Known data limitations:
  - The signal requires at least `lookback_bars` prior closes.
  - The first `lookback_bars` candles must not produce a signal.
  - Stop/target simulation needs candle high/low data even though entry signal uses only close data.
  - The base price-distance definition is fixed for v1: `1R = entry_price * 0.002`.

## 3. Market Phenomenon

- Phenomenon: recent close-to-close directional return may persist over a short future holding window.
- Why it may appear in BTC: BTCUSDT can show short-term continuation when recent order flow, aggressive buying/selling, or forced participation pushes price in one direction.
- Economic or microstructure rationale: if the last `N` completed candles moved far enough in one direction, that move may indicate temporary imbalance between buy and sell pressure. If that imbalance does not immediately disappear, the next `M` candles may continue in the same direction.
- Expected market regime: short-term directional pressure with enough follow-through to overcome fees, spread, slippage, and losing trades.
- Regimes where this should not work:
  - choppy mean-reverting ranges.
  - low-volatility noise where `momentum_return` barely clears the threshold.
  - whipsaw regimes where recent continuation quickly reverses.
  - high-cost conditions where edge is smaller than round-trip transaction costs.

## 4. Hypothesis

- Primary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 entry_threshold 이상이면 이후 holding_bars 동안 같은 상승 방향 수익률을 보일 것이다.`
- Secondary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 -entry_threshold 이하이면 이후 holding_bars 동안 같은 하락 방향 수익률을 보일 것이다.`
- Economic constraint: direction accuracy alone is not enough. Average profit when direction is correct must exceed average loss when direction is wrong plus fees, spread, and slippage.

## 5. Factors and Indicators

Only one factor is allowed in the first version.

| Factor | Formula / Definition | Required Data | Expected Direction | Confounders |
|---|---|---|---|---|
| `momentum_return` | `close[t] / close[t - lookback_bars] - 1` | completed candle close prices | positive values support long; negative values support short | noise, reversal after extension, cost drag, same-candle stop/target ambiguity |

Explicitly excluded factors:

- ATR filter.
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

## 8. Exit Logic

- Stop loss:
  - Fixed v1 risk distance:

```text
R_distance = entry_price * 0.002
```

  - Long conceptual formula:

```text
stop_price = entry_price - (stop_loss_r * R_distance)
```

  - Short conceptual formula:

```text
stop_price = entry_price + (stop_loss_r * R_distance)
```

- Take profit:
  - Long conceptual formula:

```text
take_profit_price = entry_price + (take_profit_r * R_distance)
```

  - Short conceptual formula:

```text
take_profit_price = entry_price - (take_profit_r * R_distance)
```

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

- `1R` is fixed at `0.2%` of entry price.
- Formula:

```text
R_distance = entry_price * risk_distance_pct
risk_distance_pct = 0.002
```

- This is the v1 default and should be configurable by CLI or config in a later implementation task.
- This strategy must not use ATR-based, swing-based, or recent-range-based `1R` in v1.

## 9. Risk and Position Sizing

- Position sizing: not defined in this document. A later implementation task must use existing project sizing conventions or explicitly document new sizing behavior.
- Risk per trade:
  - `stop_loss_r = 1.0`.
  - `risk_distance_pct = 0.002`.
  - `1R = entry_price * 0.002`.
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

- Entry fee: to be set by existing backtest cost configuration or a later implementation task.
- Exit fee: to be set by existing backtest cost configuration or a later implementation task.
- Round-trip fee: must be included in validation before any performance claim.
- Spread: must be included in validation before any performance claim.
- Slippage: must be included in validation before any performance claim.
- Minimum slippage: must follow existing project cost assumptions if available.
- Volatility slippage: must follow existing project cost assumptions if available.
- Fee-adjusted break-even: must be reported in future validation because the signal threshold is small.
- Slippage-adjusted break-even: must be reported in future validation because short holding windows can be cost-sensitive.

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
- Expected average win: bounded by `take_profit_r = 1.5` when target is hit, otherwise time-exit close result.
- Expected average loss: bounded by `stop_loss_r = 1.0` when stop is hit, otherwise time-exit close result.
- Expected R multiple: unknown before backtesting.
- Required break-even win rate:
  - approximately greater than `1 / (1 + 1.5) = 40%` before costs for pure 1R loss and 1.5R win outcomes.
  - higher than 40% after fees, spread, slippage, time exits, and partial-sized outcomes.
- Minimum acceptable trade count: to be defined by a later validation task before interpreting results.

## 12. Validation Plan

- In-sample window: to be assigned by a later backtest task.
- Out-of-sample window: required before promotion beyond diagnostic research.
- Walk-forward windows: required before promotion beyond diagnostic research.
- Multi-timeframe checks:
  - execute separately on `1m`, `5m`, and `15m`.
  - do not use higher-timeframe filters.
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
  - `1R` is calculated as `entry_price * 0.002`.
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
- Fixed-distance failure: a fixed `0.2%` risk distance may be too tight in high-volatility periods or too wide in low-volatility periods.

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
  - long and short stop/target formulas.
  - stop-first same-candle priority.
- Backward compatibility concerns:
  - do not alter existing strategy behavior.
  - add new behavior under the explicit `LOOKBACK_RETURN_MOMENTUM` strategy type only.
- Data persistence notes:
  - no DB mutation in this documentation task.
  - future saved runs should store strategy name, version, parameters, timeframe, costs, and `risk_distance_pct = 0.002`.

## 16. Safety Boundary

- This strategy is research-only unless a later task explicitly changes that status.
- This strategy must not call exchange order/account/private endpoints.
- This strategy must not require secrets, API keys, or `.env` changes.
- This strategy must not place real orders.
- Live trading remains out of scope.
- The following are explicitly excluded from this strategy version:
  - ATR filter.
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
