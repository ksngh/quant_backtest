# Task 283: Principle-First BTC Microstructure Strategy Development

# Goal

Design, implement, and backtest a new offline BTCUSDT research strategy suite that starts from explicit Bitcoin market microstructure principles rather than simple indicator combinations. The task must produce deterministic factor snapshots, strategy candidates, realistic fee/spread/slippage accounting, persisted DB backtests, validation diagnostics, and a markdown report.

This is a research-only task. It must not promote any model to live trading.

# Source Requirement

Owner request:

```text
You are a top quant researcher, system trading strategist, market microstructure researcher, and backtest validation expert.

I want to build Bitcoin automated trading strategies by understanding why a price movement can happen first, then finding factors/indicators/patterns, then designing entries/exits/stops/take-profits, and finally validating with fee/slippage-aware backtests.

Do not use shallow combinations like "buy when RSI is low".
Principle first.
Consider fee, round-trip fee, market slippage, limit fill failure, spread, volatile execution distortion, close stops, close take-profits, R multiple, win rate, intrabar ambiguity, same-candle entry/exit order, MTF validation, overfitting, sample size, and market-regime failure modes.

Final output structure should cover:
I. core BTC market principles
II. factor candidates
III. strategy candidates
IV. backtest design
V. top 5 priorities
VI. pre-implementation checklist

Then design and implement it.
```

Clean requirement:

- Create a concrete implementation task from the principle-first research framework.
- Implement deterministic OHLCV-based strategy candidates only after this task is assigned for implementation.
- Backtest BTCUSDT with realistic non-zero fees, spread, slippage, and conservative intrabar assumptions.
- Persist every decision-driving run to DB.
- Do not stop after the first failed candidate; continue in-task batches until a passing candidate is found, the owner pauses, or a hard data/runtime/safety blocker is reached and recorded.
- Keep all results research-only because prior Tasks 277-282 show strong data-snooping and overfit risk on the fixed May 2026 windows.

# Extracted Roles

- Owner role:
  - Requires principle-first research design and implementation.
  - Requires realistic transaction costs and enough trades.
  - Requires repeated implementation/backtest/revision when targets are not met.
  - Requires saved markdown documentation of the final strategy and validation result.
- Supporting roles:
  - Quant research lead: define economic/microstructure hypotheses before indicators.
  - Factor engineer: build completed-candle-only factor snapshots.
  - Strategy implementer: implement deterministic long/short research candidates.
  - Backtest engineer: simulate next-candle execution, conservative intrabar exits, sizing, fees, spread, and slippage.
  - Validation lead: run OOS, endpoint, cost-stress, MTF, attribution, and overfit diagnostics.
  - Reporting role: write a markdown report with strategy logic, run IDs, pass/fail gates, failure modes, and implementation notes.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange private/order/account endpoints.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, liquidation, real margin, or real borrow behavior.
  - Machine learning model training unless a later task explicitly assigns it.
  - Frontend/backend API/dashboard work unless separately assigned.

# Context

Recent research state:

- Task 276 implemented `LIQUIDITY_SWEEP_REVERSAL`, but the initial 2026-05-20+ run had 20 candidates and 0 fills due cost-aware RR rejects and unfilled retests.
- Task 277 tested adaptive 1m strategies across the 2026-05-20+ and 2026-05-25+ owner windows; no candidate met +5% on both windows.
- Task 280 ran 576 DB-persisted model variants; best combined owner-window return was only about +0.2% to +0.3% at primary 10% sizing.
- Task 281 found a high-activity owner-window candidate at +5.7295% with 62 round trips, but it was selected on the fixed owner window.
- Task 282 replayed Task 281 without retuning and found likely overfit: pre-owner conservative validation was -2.7997%, pre-owner high-slippage stress was -8.9497%, and local 1m data has April/May gaps.

Local BTCUSDT 1m data caveat from Task 282:

- Requested 2026-04-20 data is not fully available locally.
- Actual local 1m availability starts at 2026-05-10T00:00:00Z.
- There is an internal gap from 2026-05-17T15:19:00Z to 2026-05-20T00:00:00Z.
- This task must not claim full April-20-forward validation unless data repair/backfill has happened in a separate assigned task.

# Scope

- Add or update offline-only research code under:
  - `quant_bitcoin/backtesting/`
  - `quant_bitcoin/patterns/` only if a reusable deterministic detector is justified.
  - `quant_bitcoin/strategies/` only if integrating with existing strategy abstractions is lower-risk than a task-local research runner.
- Add focused tests under:
  - `tests/backtesting/`
  - `tests/patterns/` or `tests/strategies/` only for reusable pattern/strategy modules created by this task.
- Generate:
  - `reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`
- Persist all decision-driving backtests to DB with additive metadata:
  - `research.task_id = TASK_283`
  - `research.research_mode = principle_first_microstructure`
  - strategy family
  - variant ID
  - factor set ID
  - cost profile
  - window ID
  - validation group
  - MTF configuration
  - no-live-trading declaration
  - research-only declaration

# Out of Scope

- No live trading.
- No real exchange order placement.
- No private/order/account endpoints.
- No API keys, signed requests, `.env`, or credential handling.
- No futures, leverage, real margin, real borrow, liquidation, or funding assumptions.
- No dashboard/frontend/backend API work.
- No portfolio optimization.
- No strategy promotion beyond research-only.
- No claim that April 20 onward validation is complete unless missing candle data has been repaired by a separate assigned task.

# Requirements

## Research Principles To Encode

The implementation report must start from these principle families and tie every factor/strategy candidate back to at least one family.

1. Trend continuation
   - BTC directional moves can persist because of leverage crowding, momentum chasing, stop/liq cascades, cross-session follow-through, and slow response by discretionary participants.
   - Observable data: momentum, EMA slope, ADX-like trend strength, higher-high/lower-low structure, body ratio, volume expansion, MTF alignment.
   - Failure regimes: chop, low-liquidity fakeouts, late-stage exhaustion, high spread/slippage.

2. Mean reversion after forced movement
   - Sharp short-term dislocations can mean-revert after stop clusters or liquidation-like moves exhaust.
   - Observable data: return shock, range expansion, wick rejection, volume spike, close-back-inside, distance from VWAP/EMA, realized-volatility expansion then contraction.
   - Failure regimes: true trend days, news moves, liquidation cascades that continue.

3. Volatility clustering and compression breakout
   - Low realized range can precede expansion; high volatility can persist once the market begins repricing.
   - Observable data: ATR percentile, realized-volatility percentile, Bollinger width, range compression, displacement candle, volume expansion.
   - Failure regimes: false breakouts in low participation hours, cost-dominated tiny ranges, excessively wide stops in high volatility.

4. Liquidity sweep / stop hunting
   - Prior highs/lows, session ranges, swing points, and round numbers can concentrate stops and breakout orders; price may sweep then reclaim or continue.
   - Observable data: previous high/low sweep, close-back-inside, wick ratio, volume spike, displacement, retest success, local support/resistance flip.
   - Failure regimes: real breakout, slow grinding trends, low-volume sweeps with no reversal flow.

5. Market structure change
   - Higher-high/higher-low or lower-high/lower-low structure breaks can precede repricing if followed by displacement and successful retest.
   - Observable data: swing structure, change of character, support/resistance flip, FVG/order-block proxy, displacement, retest.
   - Failure regimes: over-filtering, too few trades, retest never fills, late entry.

6. Session/time effects
   - BTC trades 24/7, but liquidity and volatility differ across Asia/Europe/US sessions, daily open, weekly open, and funding-time-adjacent periods.
   - Observable data: hour, day of week, UTC session, session range, session volume, distance from daily/weekly open.
   - Failure regimes: regime shifts, holidays, weekend liquidity, one-off macro/news events.

7. Volume/participation confirmation
   - Price movement without participation can fail; volume spike can confirm continuation or identify exhaustion depending on candle structure.
   - Observable data: volume ratio, volume percentile, body/range with volume, failed breakout despite high volume, low-volume drift.
   - Failure regimes: Binance-only volume proxy limitations, wash/noise volume, missing trade/tick data.

## Factor Snapshot Requirements

Build completed-candle-only factor snapshots. At minimum include:

- returns over multiple horizons: 1, 3, 5, 15, 30, 60 minutes.
- rolling realized volatility and range percentile.
- ATR/TR and ATR percentile.
- EMA slope and MTF trend state.
- rolling high/low breakout distance.
- swing high/low and market-structure state.
- wick ratio, body ratio, close location value.
- volume moving average ratio and volume percentile.
- session tag and hour/day features.
- distance from daily open and optional weekly open.
- volatility compression and expansion flags.
- liquidity sweep flags against recent swing/session highs/lows.
- factor metadata proving no future candle is used.

Every trade must store enough factor snapshot metadata to explain why it entered and why it exited.

## Strategy Candidate Families

Implement candidates in priority order. If the first batch fails, use diagnostics to continue to later candidates or variants inside this task rather than stopping immediately.

### Priority 1: Liquidity Sweep Reversal V2

- Core hypothesis: stop clusters around recent swing/session highs/lows create forced flow; a sweep that closes back inside the range with volume and rejection may reverse.
- Entry:
  - LONG after downside sweep of recent low, close reclaim, rejection wick/body confirmation, and optional volume expansion.
  - SHORT after upside sweep of recent high, close reclaim, rejection wick/body confirmation, and optional volume expansion.
- Stop:
  - structural stop beyond sweep extreme plus ATR buffer.
- Take profit:
  - minimum fee/slippage-adjusted 1.2R to 2.5R target, opposite range liquidity, or trailing invalidation.
- Invalid setup:
  - target distance cannot cover estimated round-trip cost plus required edge.
  - stop too tight relative to ATR/noise.
  - spread/slippage stress makes expected R non-positive.

### Priority 2: Volatility Compression Breakout

- Core hypothesis: BTC volatility clusters; tight range compression followed by displacement can produce multi-candle continuation.
- Entry:
  - LONG on completed breakout above compression range with body ratio and volume confirmation.
  - SHORT on completed breakdown below compression range with body ratio and volume confirmation.
- Stop:
  - opposite side of compression range or ATR-based structural stop.
- Take profit:
  - 1.5R to 3R, partial/trailing diagnostic if supported task-locally, and early exit on failed close back into range.
- Invalid setup:
  - compression range too narrow to pay costs.
  - breakout candle too extended versus target distance.

### Priority 3: MTF Trend Pullback Continuation

- Core hypothesis: pullbacks aligned with 15m/1h trend can resume as momentum traders and forced exits reinforce the direction.
- Entry:
  - 1m pullback into EMA/VWAP-like zone while completed 15m/1h trend slope and structure agree.
  - confirmation candle closes back in trend direction.
- Stop:
  - pullback structure low/high or ATR buffer.
- Take profit:
  - fixed R multiple, prior swing liquidity, or trailing stop.
- Invalid setup:
  - higher-timeframe trend is stale, mixed, or from an incomplete candle.
  - local pullback has no favorable reward after costs.

### Priority 4: Volume Climax Mean Reversion

- Core hypothesis: liquidation-like or stop-driven moves can exhaust after a large range, volume spike, and long wick rejection.
- Entry:
  - fade only when return shock, volume spike, wick rejection, and close-location reversal agree.
- Stop:
  - beyond climax extreme plus ATR buffer.
- Take profit:
  - mean reversion to EMA/VWAP-like anchor or 1R/1.5R target after cost gate.
- Invalid setup:
  - MTF trend strongly agrees with the shock direction and no reclaim appears.
  - volatility remains expanding without contraction/reclaim.

### Priority 5: Session Range Liquidity Trap

- Core hypothesis: Asia/Europe/US session highs/lows attract breakout orders; failed session-range breaks can reverse, while confirmed breaks can continue.
- Entry:
  - failed breakout/reclaim variant and confirmed breakout continuation variant.
- Stop:
  - session sweep extreme or range midpoint invalidation depending on mode.
- Take profit:
  - opposite session range boundary, R multiple, or trailing after continuation.
- Invalid setup:
  - session range too small after costs.
  - range too stale or crosses a known local data gap.

## Execution And Cost Model

Use conservative backtest assumptions:

- Signal generation:
  - completed candle close only.
  - no future candles in factors.
  - MTF features must come from the previous fully completed higher-timeframe candle.
- Execution:
  - default market execution on next candle open or task-local equivalent already used in current research runners.
  - signal candle and execution candle must be separated.
  - no overlapping positions unless explicitly implemented and tested as bounded independent layers.
  - no leverage; notional must be cash-bounded.
  - simulated short is research-only and must be labeled as such if used.
- Costs:
  - primary profile: `conservative_crypto_1m`.
  - entry fee and exit fee must both be reflected.
  - spread and slippage must both be reflected.
  - volatility-linked slippage should be used where the existing cost model supports it.
  - zero-cost runs are diagnostics only and cannot pass acceptance.
- Intrabar exits:
  - use candle high/low for stop/take-profit detection.
  - if stop and take-profit are both touched in the same candle, assume the adverse stop fills first.
  - if entry and exit can happen in the same execution candle, use a conservative sequence and record the assumption.
- Entry viability:
  - pre-entry reward/risk must exceed the estimated round-trip fee/spread/slippage hurdle.
  - stop distance must exceed a minimum ATR/noise threshold.
  - take-profit distance must exceed the fee/slippage-adjusted break-even by a configured safety margin.

Per-strategy report format must include:

- Entry Price
- Stop Loss
- Take Profit
- Risk per Trade
- Expected R
- Required Win Rate
- Fee-adjusted Break-even
- Slippage-adjusted Break-even
- Invalid Setup Condition
- Early Exit Condition

## Backtest Windows

Primary local windows:

- `owner_0520_latest`: BTCUSDT 1m from 2026-05-20T00:00:00Z through latest available local candle.
- `owner_0525_latest`: BTCUSDT 1m from 2026-05-25T00:00:00Z through latest available local candle.
- `available_pre_owner_0510_0517`: BTCUSDT 1m from 2026-05-10T00:00:00Z through 2026-05-17T15:19:00Z if continuity checks pass.
- `weekly_available_slices`: contiguous local weekly or partial-week slices only if continuity checks pass.
- `endpoint_trim`: drop first/last 12h and 24h from target windows.
- `cost_stress`: 2x and 3x fee/spread/slippage stress on the top candidates.
- `entry_delay`: one-candle delayed entry diagnostic for the top candidates.

If a 2026-04-20-forward window is requested but data remains missing, record `DATA_BLOCKED_0420_COVERAGE` and do not fabricate candles.

## Multi-Timeframe Validation

When data is available or can be safely resampled from completed 1m candles, validate:

- 1m standalone.
- 5m standalone or 1m signal aggregated to completed 5m context.
- 15m standalone or 1m entry plus completed 15m trend filter.
- 1h standalone or 1m/5m entry plus completed 1h trend filter.
- 15m entry plus completed 4h trend filter if 4h context is locally available or safely resampled from continuous data.

MTF checks must answer:

- Does higher-timeframe alignment improve net return, drawdown, or profit factor?
- Does higher-timeframe filtering reduce trades too far?
- Does a candidate depend on one side only?
- Does the signal survive when the filter threshold is loosened/tightened?

## Required Metrics

For every decision-driving run, compute/report when available:

- total return and final equity.
- max drawdown.
- Sharpe, Sortino, Calmar, if supported by existing metric helpers.
- win rate.
- average win/loss.
- profit factor.
- expectancy.
- average and median R.
- max consecutive losses.
- completed round trips and execution count.
- average holding time.
- total fee, spread, slippage, and combined cost.
- cost/gross-PnL ratio.
- long-only and short-only attribution.
- strategy-family attribution.
- regime/session attribution.
- largest winner contribution and top-three winner contribution.
- endpoint sensitivity.
- cost-stress sensitivity.
- no-cost diagnostic gap.
- random-entry/simple-baseline comparison if low-cost to implement with existing helpers.

## Repeated Development Loop

The implementation must not stop after a rejected first batch. It must continue by using diagnostics from failed candidates to choose the next variant, while staying within deterministic OHLCV-only and no-live-trading boundaries.

Allowed in-task adjustments:

- add deterministic factors listed in this task.
- add or tune a candidate family listed in this task.
- adjust stop/target mode within the listed strategy family.
- adjust cost-aware RR thresholds.
- adjust MTF filters using completed higher-timeframe candles only.
- adjust session filters.
- add stricter activity/cost/outlier guards.

Not allowed:

- using future outcome to set per-trade direction.
- training ML models.
- fabricating missing data.
- changing cost accounting to make results pass.
- zero-cost pass claims.
- live trading behavior.

Stop conditions:

- a candidate passes all acceptance gates; or
- the owner explicitly pauses; or
- a hard data/runtime/safety blocker prevents further valid execution and is recorded in `STATUS.md`, `PROJECT_HISTORY.md`, `BACKLOG.md`, the task file, and the report.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm this task file is assigned before coding or running backtests.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Reconfirm local BTCUSDT 1m data coverage and continuity.
- [x] Predeclare run windows, candidate families, cost profiles, and stop conditions.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] A principle-first design section is saved in the Task 283 report using the owner's requested structure:
  - I. core BTC market principles.
  - II. factor candidates.
  - III. strategy candidates.
  - IV. backtest design.
  - V. top 5 priorities.
  - VI. implementation checklist.
- [x] A deterministic offline Task 283 research runner or equivalent integration is implemented.
- [x] At least the top three candidate families are implemented or explicitly blocked by a recorded technical reason; the report must explain any unimplemented priority family.
- [x] Every factor used for entry has a completed-candle/no-lookahead test or deterministic fixture.
- [x] Every decision-driving backtest is persisted to DB with `research.task_id = TASK_283`.
- [x] Primary target windows `owner_0520_latest` and `owner_0525_latest` are run for every candidate promoted to final comparison.
- [x] Realistic primary costs are non-zero and include entry/exit fee, spread, and slippage.
- [x] Persisted fee/spread/slippage formulas are recomputed and mismatch count is reported.
- [x] A candidate can be labeled `TARGET_PASSED_RESEARCH_ONLY` only if:
  - `owner_0520_latest` total return is at least `+3.0pct` after costs.
  - `owner_0525_latest` total return is at least `+3.0pct` after costs.
  - `owner_0520_latest` has at least `50` completed round trips.
  - fee/spread/slippage costs are non-zero and cost-audit mismatch count is `0`.
  - same-candle stop/take ambiguity is handled conservatively.
  - no single winner contributes more than `40pct` of net profit on the owner window.
  - top three winners contribute no more than `70pct` of net profit on the owner window.
  - cost/gross-PnL ratio is not excessive for the strategy family, with `0.75` as the default warning threshold.
  - endpoint-trim and high-cost stress diagnostics do not show the result is purely endpoint/cost fragile.
- [x] If no candidate passes, the task remains incomplete unless a hard blocker is reached and documented. Do not present a failed first batch as completion.
- [x] The final report includes strategy logic, factor rationale, run IDs, costs, trade count, attribution, overfit checks, and research-only caveat.
- [x] No result is promoted beyond `RESEARCH_ONLY`.

# Required Tests

## Unit Tests

- Factor snapshot builder uses only current/prior completed candles.
- MTF resampling/filtering uses only previous fully completed higher-timeframe candles.
- Liquidity sweep flags are deterministic and do not use future candles.
- Volatility compression/expansion flags are deterministic and no-lookahead.
- Structural stop/target calculations reject invalid or cost-negative setups.
- Same-candle stop/take ambiguity resolves stop-first.
- Cost-audit helper recomputes fee/spread/slippage/total cost and detects mismatches.

## Integration Tests

- Task 283 runner executes a small deterministic fixture end to end without exchange clients.
- Persisted metadata includes task ID, strategy family, variant ID, window ID, cost profile, MTF config, and research-only declarations.
- Report generation includes the owner's required six sections and final pass/fail gate table.

## Contract Tests

- Existing saved-run schema fields are not removed or renamed.
- New metadata is additive.
- Existing Task 281/282 modules remain importable.
- Existing strategy CLI behavior is unchanged unless this task explicitly wires a new opt-in research mode.

## Safety Tests

- No Task 283 code imports live execution clients.
- No test calls real exchange order/account/private endpoints.
- No API key, signed request, `.env`, or live trading behavior is added.
- Simulated short behavior, if used, is clearly labeled research-only and cash-bounded.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No private/order/account endpoints.
- No futures/leverage/live margin behavior.
- No unnecessary abstractions.
- No data fabrication.
- No zero-cost pass claim.

# Verification

Default focused verification:

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py -q
python -m compileall -q quant_bitcoin
git diff --check
```

If reusable pattern/strategy modules are added, also run their focused tests.

If full backtesting dependencies are available, run the Task 283 research command or module entry point and persist decision-driving runs to DB.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- persisted run IDs
- best candidate and pass/fail status
- fee/slippage audit result
- overfit/robustness conclusion
- Codex self-review result
- known limitations
- recommended next task

# Creation Note

Created on 2026-05-30 from the owner's principle-first BTC quant research request. No implementation or backtest execution was performed during creation because project rules require a relevant task document before execution.

# Execution Summary

- Completed on 2026-05-30.
- Implemented offline-only `quant_bitcoin/backtesting/t283_principle_first_microstructure_strategy.py`.
- Added focused tests in `tests/backtesting/test_t283_principle_first_microstructure_strategy.py`.
- Generated `reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`.
- Persisted Task 283 DB run IDs: `917`, `919`, `920`, `921`, `922`, `923`, `924`, `925`, `926`, `927`, `928`, `929`, `950`, `951`, `952`, `953`, `954`, `955`, `956`, `957`, `958`, `959`.
- Best candidate: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.
- Best primary owner-window results:
  - Run `950` `owner_0520_latest` conservative: `+5.7327pct`, `62` completed round trips, cost/gross PnL `0.4146`, largest winner contribution `0.2729`, top-three winner contribution `0.6474`.
  - Run `951` `owner_0525_latest` conservative: `+3.5337pct`, `17` completed round trips.
- Cost audit for all persisted Task 283 runs reported mismatch count `0`.
- Best-candidate conservative 0520 costs: fee `21,970.33`, spread `6,591.10`, slippage `12,032.06`, total `40,593.49`, effective one-way cost `18.4765` bps.
- Best-candidate stress runs remained above severe-loss gate:
  - Run `956` 0520 high-slippage stress: `+0.4570pct`.
  - Run `957` 0525 high-slippage stress: `+0.9603pct`.
- Endpoint trims stayed positive for the best candidate:
  - Run `952`: `+5.7776pct`.
  - Run `953`: `+3.5991pct`.
  - Run `954`: `+3.0529pct`.
  - Run `955`: `+1.4001pct`.
- Important limitation: available pre-owner slice run `959` returned `-2.6638pct`, and full April-20-forward OOS remains blocked because local BTCUSDT 1m data starts at 2026-05-10 and has the known May 17-May 20 gap.
- Final status: `TARGET_PASSED_RESEARCH_ONLY`; no live-trading or promotion claim.

# Verification Results

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py -q
# 7 passed

python -m compileall -q quant_bitcoin
# passed

git diff --check
# passed
```

# Codex Self-Review Result

- Scope respected: only Task 283 implementation, tests, report, and required ledgers were changed.
- Requirement matched: implemented principle-first factors/candidates, persisted realistic-cost backtests, repeated after first miss, and documented the passing research-only candidate.
- Architecture boundary respected: no frontend/backend API changes, no live execution, no exchange private/order endpoints.
- Safety respected: no API keys, no `.env`, no signed requests, no futures/leverage/live margin behavior.
- Tests added and verification run.
- Known uncertainty recorded: target windows pass, but pre-owner slice fails and April-20-forward OOS is data-blocked.

# Recommended Next Task

Create a locked OOS/WFO validation task for `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` only after data repair/backfill resolves the missing 2026-04-20 to 2026-05-10 coverage and the 2026-05-17 to 2026-05-20 internal gap.
