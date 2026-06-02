# LOOKBACK_RETURN_MOMENTUM v2 Strategy Document

## 1. Strategy Identity

- Strategy name: `LOOKBACK_RETURN_MOMENTUM`
- Strategy version: `v2`
- Strategy slug: `lookback_return_momentum`
- Stable strategy description: 과거 일정 구간의 수익률을 확인하는 모멘텀 전략.
- Owner task: `TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION`
- Status: `research_only`
- Last updated: 2026-06-02

## 2. Market and Data Scope

- Exchange: Binance public market data for research.
- Market: BTC/USDT spot-style OHLCV research data.
- Symbol: `BTCUSDT`
- Primary timeframe: `1m`, `5m`, and `15m`.
- Higher timeframes: none. V2 must not use higher-timeframe confirmation or filters.
- Intended test period:
  - start inclusive: `2026-02-01T00:00:00Z`
  - end exclusive: `2026-05-01T00:00:00Z`
- Required data:
  - completed OHLCV candles.
  - close prices for signal calculation.
  - high/low/close values for ATR and stop/take-profit checks.
- Known data limitations:
  - The signal requires at least `lookback_bars` prior closes.
  - The first `lookback_bars` candles must not produce a signal.
  - ATR risk distance requires enough completed high/low/close candles for `ATR(14)` with full-window warm-up.
  - A signal must not enter while ATR is unavailable, zero, negative, or non-finite.
  - V2 is a no-cost gross diagnostic. It does not answer whether the strategy survives fees, spread, or slippage.

## 3. Market Phenomenon

- Phenomenon: recent close-to-close directional return may persist over a short future holding window.
- Why it may appear in BTC: BTCUSDT can show short-term continuation when recent order flow, aggressive buying/selling, liquidation pressure, or forced participation pushes price in one direction.
- Economic or microstructure rationale: a sufficiently large recent move can represent temporary order-flow imbalance. If liquidity replenishment and opposite-side participation are slow, the imbalance can continue for several more candles.
- Behavioral rationale: delayed reaction, underreaction to new information, and trend-following participation can make recent directional moves persist briefly instead of reversing immediately.
- Expected market regime:
  - directional pressure continues after the lookback window.
  - ATR is large enough for a `1 ATR` target to be reachable before time exit.
  - whipsaw is limited enough that stop-first outcomes do not dominate.
- Regimes where this should not work:
  - choppy mean-reverting ranges.
  - low-volatility noise where momentum clears the threshold but does not travel `1 ATR`.
  - exhaustion spikes where the lookback move is the end of the move.
  - high-friction real trading conditions. V2 deliberately removes cost calculation, so such regimes are outside this diagnostic claim.
- Report-ready summary: Lookback Return Momentum V2 tests whether recent completed-candle return contains enough raw directional information to reach a symmetric `1 ATR` target before a symmetric `1 ATR` stop or time exit, before considering transaction costs.

## 3.1 Theory and References

This section is required before generating a full daily/Tistory report for this strategy.

- Why this strategy might have an edge:
  - Recent returns can summarize short-term order-flow pressure and participant reaction.
  - If information diffusion is delayed or trend-following flows continue, recent direction can have short-term continuation value.
  - V2 removes costs to isolate whether the signal and `1 ATR` exit geometry have raw gross value before asking whether the edge is large enough for real execution friction.
- What market mechanism it assumes:
  - completed-candle return is a noisy proxy for short-horizon directional pressure.
  - `ATR_at_entry` is a local volatility scale for measuring whether the next move is meaningful rather than a fixed percentage artifact.
  - symmetric `1 ATR` exits test the simplest volatility-normalized win/loss geometry.
- What participant behavior it assumes:
  - aggressive buyers or sellers may continue after a visible move.
  - slower participants may adjust positions over multiple candles instead of instantly.
  - short-term trend followers may reinforce the recent move.
- Why the chosen timeframe can expose the mechanism:
  - `1m` checks immediate continuation but is noisy and turnover-heavy.
  - `5m` reduces some microstructure noise while still measuring intraday continuation.
  - `15m` checks slower continuation with fewer trades and lower churn.
- When the theory should fail:
  - recent returns are exhaustion rather than continuation.
  - local volatility is dominated by reversals.
  - same-candle stop/take-profit ambiguity or stop-first priority dominates results.
  - gross edge is too small to survive real transaction costs, even if the no-cost diagnostic is positive.
- References:
  - `jegadeesh_titman_1993`:
    - Title: Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency
    - Author/source: Narasimhan Jegadeesh and Sheridan Titman
    - Year/date: 1993
    - Link or local path: general external literature reference
    - Why it matters for this strategy: documents momentum as a general delayed-information/continuation phenomenon, but does not prove minute-level BTCUSDT momentum works.
  - `moskowitz_ooi_pedersen_2012`:
    - Title: Time Series Momentum
    - Author/source: Tobias J. Moskowitz, Yao Hua Ooi, and Lasse H. Pedersen
    - Year/date: 2012
    - Link or local path: general external literature reference
    - Why it matters for this strategy: supports the broader idea that an asset's own recent return can carry directional information; BTCUSDT intraday use still requires project-specific validation.

## 4. Hypothesis

Write the hypothesis in testable form.

- Primary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 entry_threshold 이상이면 이후 holding_bars 안에 1 ATR 익절에 도달하는 비율과 손익 구조가 no-cost 기준으로 양호할 것이다.`
- Secondary hypothesis: `BTCUSDT는 최근 N개 봉 수익률이 -entry_threshold 이하이면 이후 holding_bars 안에 1 ATR 익절에 도달하는 비율과 손익 구조가 no-cost 기준으로 양호할 것이다.`
- Diagnostic boundary: this hypothesis is about gross/no-cost behavior only. It does not claim cost-aware profitability.

## 5. Factors and Indicators

List only factors that are needed to observe the phenomenon.

| Factor | Formula / Definition | Required Data | Expected Direction | Confounders |
|---|---|---|---|---|
| `momentum_return` | `close[t] / close[t - lookback_bars] - 1` | completed candle close prices | positive supports long; negative supports short | noise, exhaustion, reversal after extension, no-cost overstatement |
| `ATR_at_entry` | `ATR(14, RMA)` using completed candles through signal candle `t` | completed high/low/close | scales stop and take-profit distance | ATR warm-up, volatility regime shift, same-candle ambiguity |

Explicitly excluded factors:

- transaction-cost-aware entry gate.
- fee/spread/slippage feasibility filter.
- minimum ATR bps floor.
- volume filter.
- trend score.
- FVG.
- Order Block.
- higher-timeframe filter.
- liquidity target.
- session/time-of-day filter.
- any other confirmation filter not listed in this document.

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

- Confirmation condition: none beyond the threshold rule. V2 is still a pure lookback-return momentum diagnostic.
- Invalid setup condition:
  - fewer than `lookback_bars` prior completed closes are available.
  - prior close used in the denominator is missing or invalid.
  - `entry_threshold <= 0`.
  - `lookback_bars <= 0`.
  - `holding_bars <= 0`.
  - `ATR_at_entry` is missing, zero, negative, or non-finite.
- Look-ahead prevention rule:
  - compute `momentum_return` only from completed candles up to index `t`.
  - compute `ATR_at_entry` only from completed candles through signal candle `t`.
  - do not use any candle after `t` for signal or ATR calculation.
- Report-facing rule summary: V2 enters from the same lookback-return signal as V1, but evaluates the raw gross path with no transaction-cost adjustment and exits on symmetric `1 ATR` stop/take-profit rules.

## 7. Entry Logic

Long entry:

- Enter long only when no position is open.
- Required signal:

```text
momentum_return >= entry_threshold
```

- Predeclared Task 324 parameters:

```text
1m: lookback_bars = 20, entry_threshold = 0.0004
5m: lookback_bars = 12, entry_threshold = 0.0006
15m: lookback_bars = 8, entry_threshold = 0.0008
```

Short entry:

- Enter short only when no position is open.
- Required signal:

```text
momentum_return <= -entry_threshold
```

- Use the same interval-specific parameter set as long entries.

Execution timing:

- Signal candle: completed candle at index `t`.
- Execution candle: signal candle close, preserving the existing momentum implementation assumption unless implementation constraints require an explicit documented change.
- Market/limit assumption: research-only signal-close fill using the existing strategy-engine path.
- Same-candle entry/exit rule:
  - stop/take-profit/time exits are not evaluated on the entry candle.
  - exit checks start from the next completed candle after entry.
  - if an exit occurs on a candle, V2 does not open a new position on that same candle.

Cost gate:

- `cost_aware_entry_filter_enabled = false`.
- Cost feasibility must not block entries in V2.
- If implementation metadata emits any cost-aware fields for compatibility, they must clearly indicate disabled/no-cost diagnostic status and must not affect entry decisions.

## 8. Exit Logic

- Stop loss:

```text
R_distance = ATR_at_entry
Long stop_price = entry_price - ATR_at_entry
Short stop_price = entry_price + ATR_at_entry
```

- Take profit:

```text
Long take_profit_price = entry_price + ATR_at_entry
Short take_profit_price = entry_price - ATR_at_entry
```

- Time exit:

```text
if bars_since_entry >= holding_bars:
    exit at close
```

- Early exit: none.
- Opposite signal handling:
  - do not reverse.
  - do not close early due to opposite signal.
  - while a position is open, use only stop loss, take profit, or time exit.
- Stop/target same-candle priority:
  - if both stop loss and take profit are reachable in the same candle, assume stop loss happens first.
  - this applies to both long and short positions.
- Exit ordering:
  - first check stop loss.
  - then check take profit.
  - then check time exit at close.
  - therefore, if the final holding candle also touches stop or target, stop/take-profit takes precedence over time exit.

## 9. Risk and Position Sizing

- Position sizing: use existing project sizing conventions in the assigned implementation task. This document does not introduce a new sizing model.
- Risk per trade:
  - `risk_distance_mode = atr`.
  - `atr_period = 14`.
  - `atr_smoothing = RMA`.
  - `stop_loss_atr_multiple = 1.0`.
  - `take_profit_atr_multiple = 1.0`.
  - `1R = ATR_at_entry`.
- Max concurrent positions: one open position maximum.
- Long/short constraints:
  - long and short signals are both supported for research.
  - no reverse entry.
  - no overlapping positions.
- Cash/margin assumptions:
  - no live trading.
  - no real margin, borrow, futures, leverage, liquidation, or funding assumptions.
  - any short simulation is research accounting only unless a later task defines broader execution assumptions.
- Research-only constraints:
  - V2 is not deployable from this document alone.
  - implementation/backtest execution requires a later assigned task after this document exists.

## 10. Cost and Execution Assumptions

- Entry fee: `0` for Task 324 no-cost diagnostic.
- Exit fee: `0` for Task 324 no-cost diagnostic.
- Round-trip fee: `0` for Task 324 no-cost diagnostic.
- Spread: `0` for Task 324 no-cost diagnostic.
- Slippage: `0` for Task 324 no-cost diagnostic.
- Minimum slippage: disabled for Task 324 no-cost diagnostic.
- Volatility slippage: disabled for Task 324 no-cost diagnostic.
- Fee-adjusted break-even: not applicable to this no-cost diagnostic.
- Slippage-adjusted break-even: not applicable to this no-cost diagnostic.
- Cost and reward/risk explanation for reports:
  - V2 intentionally removes costs to isolate raw signal and exit geometry.
  - Any positive no-cost result must be described as gross diagnostic evidence only.
  - Any future claim about practical viability must rerun the strategy with explicit fee, spread, slippage, and cost-aware interpretation.

## 11. Expected Value

```text
E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost
```

- Expected win rate: unknown before backtesting.
- Expected average win: approximately `+1 ATR` when take-profit is hit; otherwise time-exit close result.
- Expected average loss: approximately `-1 ATR` when stop is hit; otherwise time-exit close result.
- Expected R multiple: unknown before backtesting.
- Required break-even win rate:
  - approximately greater than `50%` before costs when outcomes are symmetric `+1 ATR` and `-1 ATR`.
  - time exits can shift the realized break-even point because not every trade exits exactly at stop or target.
  - after real costs are reintroduced, required win rate will be higher than the no-cost estimate.
- Minimum acceptable trade count: to be defined by the Task 324 execution report before interpreting results.
- Cost and reward/risk explanation for reports: V2 deliberately asks whether the raw gross path has enough signal value before transaction costs. It must not be summarized as cost-aware profitability.

## 12. Validation Plan

- In-sample window:

```text
2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z
```

- Out-of-sample window: required before promotion beyond diagnostic research; not part of Task 324.
- Walk-forward windows: required before promotion beyond diagnostic research; not part of Task 324.
- Multi-timeframe checks:
  - run separately on `1m`, `5m`, and `15m`.
  - do not use higher-timeframe filters.
- Predeclared Task 324 run grid:

| Interval | lookback_bars | holding_bars | entry_threshold | stop ATR multiple | take-profit ATR multiple | costs |
|---|---:|---:|---:|---:|---:|---|
| `1m` | 20 | 5 | 0.0004 | 1.0 | 1.0 | zero/no-cost |
| `5m` | 12 | 6 | 0.0006 | 1.0 | 1.0 | zero/no-cost |
| `15m` | 8 | 4 | 0.0008 | 1.0 | 1.0 | zero/no-cost |

- Fee stress: out of scope for Task 324 because the assigned diagnostic is no-cost.
- Slippage stress: out of scope for Task 324 because the assigned diagnostic is no-cost.
- Outlier removal: summarize whether returns depend on a small number of large continuation trades if the task report has enough data.
- Random/baseline comparison:
  - compare against no-trade baseline.
  - compare against buy-and-hold for the same period if the existing reporting workflow provides it.
  - randomized direction/shuffled signal comparison is optional and requires a later task if not already available.
- Buy-and-hold comparison: required if readily available from existing reporting conventions.
- Long-only and short-only attribution: required to identify side concentration.
- Regime/session attribution:
  - optional for diagnostics only.
  - must not become an entry filter in V2.

## 13. Failure Modes

- Cost-dominated failure:
  - not directly tested in V2 because costs are disabled.
  - if V2 is only barely positive before costs, that implies likely cost failure when realistic friction is reintroduced.
- Low trade-count failure:
  - fewer trades make the no-cost conclusion unstable.
- Side concentration:
  - performance may come only from long or only from short trades.
- Outlier dependence:
  - one or two large continuation trades may dominate gross results.
- Choppy regime:
  - repeated reversals can make symmetric `1 ATR` stops dominate.
- Trend regime:
  - the strategy may exit too early at `1 ATR` and fail to capture larger continuation.
- High-volatility execution distortion:
  - large candles can create same-candle stop/take-profit ambiguity.
- Same-candle ambiguity:
  - stop-first priority can make ambiguous candles pessimistic relative to best-case path assumptions.

## 14. Required Artifacts

- Saved backtest runs: required for Task 324 execution if the project runner persists results.
- Trade log: required.
- Equity curve: required if generated by the existing reporting convention.
- Cost breakdown: not applicable as a cost-impact chart for V2; if a cost field is included, it must show zero/no-cost diagnostic status.
- Representative win/loss trades: recommended for later reporting if trades exist.
- Daily report payload: out of scope unless a later report task asks for it.
- Daily report images: out of scope unless a later report task asks for them.
- Draft report: out of scope unless a later report task asks for it.
- Task report: required under `reports/` for Task 324 execution.

## 15. Implementation Notes

- Files/modules expected to change:
  - strategy/config/runner files only if current code cannot express `v2`, disabled costs, or zero-cost diagnostics through existing parameters.
  - tests for strategy/config/runner behavior if implementation changes are needed.
- Reusable components:
  - existing `LOOKBACK_RETURN_MOMENTUM` signal calculation.
  - existing ATR risk-distance calculation.
  - existing stop/take-profit/time-exit engine behavior.
- Tests required:
  - V2 no-cost config disables cost-aware entry filtering.
  - zero-cost/no-cost setting prevents fee/spread/slippage PnL reduction.
  - `1 ATR` stop exits correctly.
  - `1 ATR` take-profit exits correctly.
  - same-candle stop/take-profit ambiguity follows stop-first policy.
  - invalid ATR blocks entry with a diagnostic reason.
- Backward compatibility concerns:
  - V1 saved runs and metadata must remain interpretable.
  - V2 should not rewrite or reinterpret V1 cost-aware results.
  - If implementation uses the same strategy key, metadata must clearly identify `version = v2` and no-cost diagnostic settings.
- Data persistence notes:
  - saved runs should record `research.task_id = TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION`.
  - saved runs should record no-cost settings explicitly.
  - saved runs should record `cost_aware_entry_filter_enabled = false`.
  - Task 324 persisted V2 no-cost validation runs `1210` (`1m`), `1211` (`5m`), and `1212` (`15m`) with explicit `strategy_version = v2` metadata.

## 16. Safety Boundary

- This strategy is research-only unless a later task explicitly changes that status.
- This strategy must not call exchange order/account/private endpoints.
- This strategy must not require secrets, API keys, or `.env` changes.
- This strategy must not place real orders.
- Live trading remains out of scope.
- This document creation does not authorize implementation or backtest execution by itself.

## 17. Change Log

- 2026-06-02: Created V2 strategy document for Task 324. Defines no-cost gross diagnostic assumptions, symmetric `1 ATR` stop/take-profit exits, same February-to-May validation window, `1m`/`5m`/`15m` intervals, and the required boundary that implementation/backtest execution must wait for assignment after this strategy document exists.
- 2026-06-02: Executed Task 324 after assignment. The runner now supports explicit `--lookback-return-momentum-version v2` metadata while preserving default `v1` behavior. V2 no-cost ATR-1 runs were persisted as `1210`/`1211`/`1212` and summarized in `reports/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`.
