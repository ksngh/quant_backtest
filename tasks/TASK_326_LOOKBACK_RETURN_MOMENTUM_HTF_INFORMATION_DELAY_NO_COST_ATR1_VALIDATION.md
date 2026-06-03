# Task 326: LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION

# Goal

Define a higher-timeframe validation task for the `LOOKBACK_RETURN_MOMENTUM`
family. The task will test whether the information-delay momentum hypothesis is
better aligned with `BTCUSDT` `1h`, `4h`, and `1d` candles than with the prior
`1m`/`5m`/`15m` short-horizon tests.

Core question:

- `1m`, `5m`, and `15m` close-to-close momentum did not show useful no-cost
  behavior under the tested symmetric `1 ATR` exit geometry. Does the same
  signal family show a positive raw no-cost edge on `1h`, `4h`, or `1d`, where
  delayed information diffusion, participant reaction delay, fund flows, and
  slower position adjustment are more plausible?

This task document is planning-only until explicitly assigned for execution. Do
not run the backtest during task creation.

# Source Requirement

Owner requirement:

> 정보 반영 지연 때문에 모멘텀이 생긴다는 전제라면, 1m/5m/15m 20개가량 momentum
> 분석은 정보 반영 지연과 관련이 약할 수 있다. 차라리 1h, 4h, 1d로 봐야 할
> 수 있다. 기간은 2021년부터 시작한다. 비용산정은 하지 않는다. 손절 및 익절은
> 동일하게 1 ATR로 한다.

Interpreted requirement:

- Strategy family: `LOOKBACK_RETURN_MOMENTUM`
- Research task type: higher-timeframe information-delay momentum diagnostic
- Timeframes:
  - `1h`
  - `4h`
  - `1d`
- Start date:
  - `2021-01-01T00:00:00Z`
- Preferred fixed reproducible end date:
  - `2026-06-01T00:00:00Z` exclusive
- If local data does not reach the preferred end date:
  - use the latest common complete candle across `1h`, `4h`, and `1d`;
  - record the actual effective start/end per interval;
  - do not silently compare intervals over different end dates.
- Costs:
  - no cost calculation;
  - no cost-aware entry filter;
  - zero fee;
  - zero spread;
  - zero slippage;
  - report must clearly state this is a gross/no-cost diagnostic only.
- Stop/take-profit:
  - `risk_distance_mode = atr`
  - `atr_period = 14`
  - `atr_smoothing = RMA`
  - `stop_loss_atr_multiple = 1.0`
  - `take_profit_atr_multiple = 1.0`
- Entry:
  - same signal family as V1/V2;
  - signal uses completed candle close-to-close lookback return;
  - entry at signal candle close unless implementation requires a documented
    existing path.
- No tuning after seeing results.

Task number selection:

- `STATUS.md` and `BACKLOG.md` show Task 325 as the latest completed task.
- Therefore this new task is Task 326.

Strategy document selection:

- Chosen strategy document: `docs/strategy/lookback_return_momentum_v2.md`
- Reason:
  - the repository currently keeps this strategy family in versioned files
    (`lookback_return_momentum_v1.md`);
  - owner clarified on 2026-06-03 that the higher-timeframe information-delay
    validation should be the report-facing V2;
  - Task 324 remains a superseded short-timeframe no-cost symmetric `1 ATR`
    draft and must not be executed as the active V2 path unless a later task
    retitles or re-versions it;
  - this task changes the research horizon and hypothesis alignment while
    preserving the signal family, so `v2` keeps version sequencing clearer than
    introducing a parallel `lookback_return_momentum_htf_v1.md` naming branch.
- Rejected alternative:
  - `docs/strategy/lookback_return_momentum_htf_v1.md` would be acceptable if
    the owner later prefers an HTF-specific branch, but it is not selected here.

# Extracted Roles

- Owner role:
  - Defines the new hypothesis and experiment scope.
  - Requires higher timeframes because the information-delay premise may be
    weakly aligned with minute-level candles.
  - Requires no transaction costs and symmetric `1 ATR` stop/take-profit.
- Supporting roles:
  - Strategy-document maintainer: create or update
    `docs/strategy/lookback_return_momentum_v2.md` from
    `docs/strategy/STRATEGY_TEMPLATE.md` before any implementation or backtest
    execution.
  - Strategy/backtest implementer: reuse the `LOOKBACK_RETURN_MOMENTUM` signal
    family and add only minimal metadata, version, or routing changes required
    for HTF validation.
  - Data preflight role: verify local `BTCUSDT` `1h`, `4h`, and `1d` candle
    coverage from `2021-01-01T00:00:00Z`, including continuity, duplicates,
    first/last candle, expected count, and missing intervals.
  - Public candle backfill role: if data is missing and the owner assigns
    backfill inside this task, use only the existing Binance public spot kline
    backfill path.
  - Report writer: save a concise task report under `reports/`, separating
    no-cost gross diagnostics from real-world cost-aware viability.
  - Verification role: add/update tests only if implementation changes are
    needed, then run focused verification.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Private exchange endpoint caller.
  - Account/order endpoint caller.
  - API key or `.env` user.
  - Frontend/backend implementer unless explicitly required by this task.
  - Post-result parameter tuner.

# Context

Previous short-timeframe diagnosis:

- `LOOKBACK_RETURN_MOMENTUM` uses completed close-to-close lookback return:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Prior short-timeframe validation covered `1m`, `5m`, and `15m`.
- Owner-provided Task 324 evidence says the V2 no-cost symmetric `1 ATR`
  validation was negative across the tested short timeframes:
  - `1m`: negative no-cost return;
  - `5m`: near flat but not positive;
  - `15m`: negative no-cost return.
- Local repository state when this task was created:
  - `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
    exists;
  - `docs/strategy/lookback_return_momentum_v2.md` does not exist;
  - `reports/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
    does not exist;
  - `reports/task_324_v2_no_cost_atr1_summary.json` does not exist.
- Execution must not fabricate missing stored metrics. If Task 324 report
  artifacts still do not exist during execution, record the absence and separate
  owner-provided prior evidence from repository-backed evidence.

Theoretical mismatch to address:

- Information-diffusion delay is more plausibly visible over hours or days than
  over one-minute bars.
- `1m` and `5m` tests may mix the signal with microstructure noise,
  liquidation bursts, short-term reversal, spread crossing, and local
  order-flow pressure.
- `1h`, `4h`, and `1d` better align with:
  - participant reaction delay;
  - institutional allocation delay;
  - ETF/fund flow timing;
  - session-to-session continuation;
  - macro/risk-on/risk-off propagation;
  - slower position adjustment.

Internal references:

- `docs/strategy/lookback_return_momentum_v1.md`
  - documents the original signal formula;
  - documents delayed information diffusion, underreaction, order-flow
    continuation, and trend-following participation as theory references;
  - warns that those references do not prove minute-level BTCUSDT momentum
    works.
- `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
  - defines the short-timeframe V2 no-cost symmetric `1 ATR` validation.
- `reports/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`
  - required if it exists at execution time;
  - should be used as the repository-backed reason for moving to `1h`, `4h`,
    and `1d`.
- `reports/task_324_v2_no_cost_atr1_summary.json`
  - required if it exists at execution time;
  - should supply compact prior metrics for `1m`, `5m`, and `15m`.

Academic references:

- Jegadeesh and Titman, 1993, "Returns to Buying Winners and Selling Losers"
  - Use only as general theory/background for momentum, delayed information
    diffusion, and underreaction.
  - Do not cite it as proof that BTCUSDT intraday or crypto HTF momentum must
    work.
- Moskowitz, Ooi, and Pedersen, 2012, "Time Series Momentum"
  - Use only as general background that own-asset past returns can carry
    directional information across liquid assets.
  - Do not cite it as proof that this exact implementation works.

Research question:

- Does higher-timeframe close-to-close momentum show positive raw no-cost
  expectancy when tested from 2021 onward with symmetric `1 ATR` exits?

# Scope

- Read required state files and this task before execution.
- Read `docs/strategy/lookback_return_momentum_v1.md`.
- Read `docs/strategy/lookback_return_momentum_v2.md` if it exists.
- Create or update `docs/strategy/lookback_return_momentum_v2.md` before any
  implementation or backtest execution.
- If `docs/strategy/lookback_return_momentum_v2.md` is missing at execution
  start:
  - create it from `docs/strategy/STRATEGY_TEMPLATE.md`;
  - document the HTF V2 rules, theory, references, validation grid, and
    research-only/live-trading boundary;
  - update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`;
  - stop before implementation/backtest execution if required by the project
    strategy-document rule.
- Preflight local `BTCUSDT` candles for `1h`, `4h`, and `1d`.
- If data is missing:
  - record the precise blocker; or
  - if this task explicitly allows it at execution time, run only bounded public
    candle backfill through the existing `quant-bitcoin-binance-backfill` path.
- Validate over:

```text
2021-01-01T00:00:00Z <= candle time < 2026-06-01T00:00:00Z
```

- If the fixed end is not available for all intervals:
  - use the latest common complete end timestamp;
  - record actual start/end per interval;
  - document any interval with a different effective window instead of silently
    comparing unlike ranges.
- Use no-cost diagnostic settings:
  - `cost_profile = zero` by effective configuration;
  - `cost_aware_entry_filter_enabled = false`;
  - `maker_fee_bps = 0`;
  - `taker_fee_bps = 0`;
  - `spread_bps = 0`;
  - `slippage_bps = 0`;
  - `minimum_slippage_bps = 0`;
  - `volatility_slippage_multiplier = 0`.
- Use risk/exit settings:
  - `risk_distance_mode = atr`;
  - `atr_period = 14`;
  - `atr_smoothing = RMA`;
  - `stop_loss_atr_multiple = 1.0`;
  - `take_profit_atr_multiple = 1.0`;
  - `minimum_atr_bps = 0.0`.
- Use position sizing:
  - `starting_cash = 1000000`;
  - `starting_cash_currency = KRW`;
  - `krw_per_usdt = 1500`;
  - `position_sizing_mode = cash_fraction`;
  - `position_sizing_value = 0.10`.
- Use the same signal family:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
LONG if momentum_return >= entry_threshold
SHORT if momentum_return <= -entry_threshold
NO TRADE otherwise
```

- Preserve existing execution assumptions unless the V2 strategy document
  explicitly changes them:
  - signal uses completed candles only;
  - ATR uses completed candles through signal candle only;
  - entry at signal candle close;
  - exit checks start from the next completed candle;
  - flat-only/no-reverse behavior;
  - stop-first same-candle ambiguity;
  - stop-loss checked before take-profit, then time exit.
- Persist or save runs using existing project conventions.
- Save compact summary JSON under `reports/`.
- Save a task report under `reports/`.
- Full raw CLI JSON may be omitted from git if too large, but persisted run IDs
  and compact summary must be saved.

## Predeclared Primary Grid

Use exactly these six variants unless the owner changes them before execution.

| Interval | Variant | lookback_bars | holding_bars | entry_threshold | Interpretation |
|---|---|---:|---:|---:|---|
| `1h` | `1h_1d_to_6h` | 24 | 6 | 0.005 | Last 1 day return -> next 6 hours |
| `1h` | `1h_3d_to_1d` | 72 | 24 | 0.015 | Last 3 days return -> next 1 day |
| `4h` | `4h_1d_to_12h` | 6 | 3 | 0.010 | Last 1 day return -> next 12 hours |
| `4h` | `4h_3d_to_1d` | 18 | 6 | 0.030 | Last 3 days return -> next 1 day |
| `1d` | `1d_1w_to_1d` | 7 | 1 | 0.030 | Last 1 week return -> next 1 day |
| `1d` | `1d_1m_to_1w` | 30 | 7 | 0.100 | Last 1 month return -> next 1 week |

Grid rationale:

- `1h`: captures intraday to one-day information propagation.
- `4h`: captures session-level continuation and cross-session adjustment.
- `1d`: captures daily information diffusion, fund flow, and slower allocation
  effects.
- Thresholds are deliberately larger than short-timeframe thresholds because
  higher timeframes require meaningful movement.
- The grid is intentionally small to avoid post-result parameter search.

## Optional Secondary Grid

Do not run this grid unless explicitly assigned in a later task.

| Interval | lookback candidates | holding candidates | threshold candidates |
|---|---|---|---|
| `1h` | `12`, `24`, `48`, `72` | `3`, `6`, `12`, `24` | `0.005`, `0.010`, `0.015` |
| `4h` | `6`, `12`, `18`, `24` | `2`, `3`, `6`, `12` | `0.010`, `0.020`, `0.030` |
| `1d` | `7`, `14`, `30` | `1`, `3`, `7` | `0.030`, `0.050`, `0.100` |

## Command Template

Executor must adapt database URL and output capture to the local environment.
The command should be equivalent to:

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --source binance_spot \
  --symbol BTCUSDT \
  --interval <1h|4h|1d> \
  --start-time 2021-01-01T00:00:00Z \
  --end-time 2026-06-01T00:00:00Z \
  --lookback-bars <grid_lookback_bars> \
  --holding-bars <grid_holding_bars> \
  --entry-threshold <grid_entry_threshold> \
  --risk-distance-mode atr \
  --atr-period 14 \
  --atr-smoothing RMA \
  --stop-loss-atr-multiple 1.0 \
  --take-profit-atr-multiple 1.0 \
  --minimum-atr-bps 0.0 \
  --maker-fee-bps 0 \
  --taker-fee-bps 0 \
  --spread-bps 0 \
  --slippage-bps 0 \
  --minimum-slippage-bps 0 \
  --volatility-slippage-multiplier 0 \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --quote-currency USDT \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_326 \
  --research-run-group lookback_return_momentum_v2_htf_no_cost_atr1 \
  --research-variant-id <variant_id> \
  --enforce-candle-continuity
```

Important CLI constraints:

- Do not pass `--enable-cost-aware-entry-filter`.
- Do not pass any non-zero transaction-cost option.
- Do not pass `--cost-profile` unless the implementation adds a supported
  explicit zero-cost profile; current runner behavior treats all-zero manual
  costs and no selected profile as the effective zero-cost diagnostic.
- If the console entrypoint is unavailable in the local shell, use
  `python -m quant_bitcoin.backtesting.strategy_postgres_runner_cli` with the
  same arguments and record that fallback in the report.

# Out of Scope

- Transaction-cost-aware validation.
- Fee/spread/slippage subtraction.
- Live trading.
- Real Binance orders.
- Private exchange endpoints.
- Account/order endpoints.
- New filters:
  - volume filter;
  - FVG;
  - Order Block;
  - higher-timeframe confirmation beyond the tested candle interval itself;
  - market regime filter;
  - equity index filter;
  - DXY filter;
  - ETF flow filter.
- Parameter optimization after seeing results.
- Walk-forward optimization.
- OOS protocol in this task.
- Frontend/backend/API changes.
- DB schema changes.
- Daily/Tistory report unless explicitly assigned.
- Silently deriving `4h` candles from `1h` candles. If native `4h` loading or
  backfill is unsupported, stop unless an explicit derivation method is
  implemented, tested, and documented in a separate assigned scope.

# Requirements

- Strategy document exists before backtest execution.
- `docs/strategy/lookback_return_momentum_v2.md` must include:
  - information-delay theory;
  - delayed information diffusion and underreaction references;
  - why `1h`, `4h`, and `1d` are more aligned with this hypothesis than
    `1m`/`5m`/`15m`;
  - no-cost diagnostic boundary;
  - symmetric `1 ATR` stop/take-profit geometry;
  - primary grid;
  - research-only/live-trading boundary.
- Data preflight must run for `1h`, `4h`, and `1d`.
- Start date fixed at `2021-01-01T00:00:00Z`.
- End date fixed at `2026-06-01T00:00:00Z` exclusive if data exists.
- If the fixed end is unavailable, use latest common complete end and document
  it.
- No transaction costs.
- No cost-aware entry filter.
- `1 ATR` stop.
- `1 ATR` take-profit.
- Signal close entry.
- No look-ahead.
- Stop-first same-candle ambiguity.
- Flat-only/no-reverse behavior preserved.
- Results saved under `reports/`.
- Compact summary JSON saved under `reports/`.
- Full raw CLI JSON may be omitted from git if too large, but persisted run IDs
  and compact summary must be saved.
- Report must not claim deployability.
- Report must not claim momentum strategies generally work or fail.
- Report must answer:
  - Does higher-timeframe no-cost momentum have positive gross edge?
  - Which interval performs best?
  - Are long and short symmetric?
  - Are exits dominated by stop, take-profit, or time exit?
  - Does performance differ by year?
  - Is there evidence that information-delay horizon matters?

## Required Report Sections

The generated task report under `reports/` must include:

```text
# Task 326: LOOKBACK_RETURN_MOMENTUM Higher-Timeframe Information-Delay No-Cost ATR-1 Validation

## Scope
## Hypothesis
## Theory and References
## Data Coverage
## Command Template
## Predeclared Parameter Grid
## Results
## Exit Mix
## Side Attribution
## Yearly Attribution
## Comparison Against Task 324
## Interpretation
## What This Can Reject
## What This Cannot Reject
## Known Limitations
## Recommended Next Task
## Verification
```

## Results Table Requirements

For each variant, report:

- interval
- variant id
- run id
- candles
- lookback_bars
- holding_bars
- entry_threshold
- candidate_entry_count
- accepted_entry_count
- completed_trade_count
- invalid_atr_blocked_entry_count
- gross_pnl
- net_pnl
- total_cost
- total_return
- max_drawdown
- average_r
- expectancy
- hit_ratio
- profit_factor
- stop_loss count
- take_profit count
- time_exit count
- long completed count
- short completed count
- long net PnL
- short net PnL
- ending_position
- warnings

## Yearly Attribution Requirements

Because the period starts in 2021, include yearly attribution.

For each variant and year:

- year
- completed trades
- total return
- gross PnL
- net PnL
- average R
- hit ratio
- profit factor
- max drawdown if available
- stop/take-profit/time-exit mix

Purpose:

- Determine whether the result is dominated by one market regime.
- Prevent a multi-year conclusion from hiding regime-specific behavior.
- Check whether `2021` bull, `2022` bear, `2023` recovery, `2024` ETF/risk-flow
  regime, and `2025`/`2026` conditions differ.

## Interpretation Rules

The task report must use strict bounded interpretation.

If all intervals are negative no-cost:

- The tested higher-timeframe close-to-close momentum with symmetric `1 ATR`
  exits did not show positive gross edge from 2021 onward under the tested grid.
- This is stronger evidence against this exact HTF implementation, but still
  does not reject all momentum strategies because no regime filters, external
  risk-flow filters, alternative momentum definitions, or cost-aware execution
  variants were tested.

If one or more intervals are positive no-cost:

- The positive result is raw gross diagnostic evidence only.
- It does not imply cost-aware profitability.
- Next step must reintroduce transaction costs and then validate out-of-sample
  or by walk-forward.

If only one year or one side drives the result:

- The result is regime/side-specific and should not be generalized.
- Next step should isolate the driver before adding complexity.

If `1h`/`4h`/`1d` are better than `1m`/`5m`/`15m`:

- This supports the hypothesis that the information-delay premise is better
  aligned with higher timeframes than minute-level microstructure momentum.
- It still requires cost-aware and OOS/WFO validation.

If `1h`/`4h`/`1d` are not better:

- This weakens the current close-to-close information-delay proxy across tested
  horizons.
- However, it does not reject momentum mechanisms based on volume, order flow,
  risk-flow alignment, macro synchronization, or regime filters.

# Status Tracking

## Before Implementation

- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Read this task.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Read `docs/strategy/lookback_return_momentum_v2.md` if it exists.
- [x] Read `reports/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md` if it exists.
- [x] Read `reports/task_324_v2_no_cost_atr1_summary.json` if it exists.
- [x] Read or create `docs/strategy/lookback_return_momentum_v2.md` before
      implementation/backtest execution.
- [x] If the V2 strategy document had to be created, update state files and stop
      if required by the project strategy-document rule.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm this is a no-cost gross diagnostic task, not a deployability claim.
- [x] Confirm parallel work is not used for shared strategy/backtest contract
      changes.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update the V2 strategy document if implementation changes strategy logic,
      risk logic, cost assumptions, execution assumptions, validation windows, or
      research/live boundary.
- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open
      question, or completion state changed.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if this task was completed, blocked, reprioritized, or
      split.
- [x] Mark checklist items complete only when acceptance criteria and
      verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Execution note:

- 2026-06-03: Created `docs/strategy/lookback_return_momentum_v2.md` because it was missing. Per the project strategy-document rule, execution stopped before data preflight, public candle backfill, implementation, backtest execution, report generation, compact summary JSON generation, or DB mutation. Remaining Task 326 validation work requires a later explicit owner assignment after the V2 strategy document exists.
- 2026-06-03: Continued Task 326 after owner assignment. Data preflight passed for native `BTCUSDT` `4h` and `1d` candles over the fixed preferred window, but native public `1h` candles had 7 internal continuity gaps totaling 14 missing open times. Bounded public `1h` backfill attempts through the Binance market-data kline path stored 0 candles for those gaps, so both `1h` variants were recorded as blocked instead of being run on incomplete, synthetic, or derived data. Persisted no-cost symmetric `1 ATR` runs `1213`-`1216` for the executable `4h`/`1d` primary grid. Saved `reports/task_326_htf_no_cost_atr1_summary.json` and `reports/TASK_326_LOOKBACK_RETURN_MOMENTUM_HTF_INFORMATION_DELAY_NO_COST_ATR1_VALIDATION.md`.

# Acceptance Criteria

- Task file is created using `tasks/TASK_TEMPLATE.md` structure.
- Strategy document is created or updated before any implementation/execution.
- The task clearly records:
  - references;
  - theory;
  - prior evidence from Task 324 or the absence of local Task 324 artifacts;
  - why higher timeframes are being tested;
  - no-cost diagnostic boundary;
  - exact validation period;
  - exact primary grid.
- No backtest is executed unless the task is explicitly assigned for execution.
- If execution is part of the assigned task:
  - data preflight passes or blockers are recorded;
  - `1h`, `4h`, and `1d` runs are persisted or saved;
  - compact summary JSON is saved;
  - report under `reports/` is saved;
  - state files are updated.
- No live trading, order endpoint, secret, or `.env` behavior is introduced.
- Required tests and verification pass, or precise blockers are recorded.

# Required Tests

## Unit Tests

If implementation changes are needed:

- Momentum config accepts higher-timeframe variants or explicit HTF overrides.
- Strategy version or metadata records the HTF/V2 variant.
- No-cost config disables all fee/spread/slippage.
- Cost-aware entry filter is disabled.
- `1 ATR` stop exits correctly.
- `1 ATR` take-profit exits correctly.
- Invalid ATR blocks entries.
- Signal uses completed close-to-close data only.

## Integration Tests

If implementation changes are needed:

- CLI can run `LOOKBACK_RETURN_MOMENTUM` on `1h`, `4h`, and `1d`.
- CLI can set:
  - no-cost profile/effective zero-cost settings;
  - ATR risk distance;
  - stop/take-profit ATR multiples;
  - research task id;
  - research variant id;
  - research run group.
- Persisted metadata includes:
  - strategy version;
  - interval;
  - lookback_bars;
  - holding_bars;
  - entry_threshold;
  - ATR settings;
  - zero cost assumption;
  - no-cost diagnostic boundary.

## Contract Tests

- Preflight verifies:
  - duplicate timestamp count;
  - gap count;
  - first candle;
  - last candle;
  - expected count if interval is supported.
- Confirm `4h` support before execution.
- If native `4h` loading/backfill is unsupported, do not silently derive `4h`
  from `1h` unless the derivation method is explicitly implemented, tested, and
  documented.

## Safety Tests

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" quant_bitcoin backend frontend docs reports STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks
```

Expected:

- no new live-trading behavior;
- no new order/account/private endpoint behavior;
- no committed secrets;
- declarative safety text is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Strategy document exists before implementation/backtest execution.
- Data contract respected.
- No hardcoded secrets.
- No real order execution.
- No private/account/order endpoint use.
- No unnecessary abstractions.
- No post-result tuning.
- No cost-aware entry filter in the no-cost diagnostic run.
- No non-zero transaction-cost assumption in the no-cost diagnostic run.
- No broad claim that all momentum strategies work or fail.

# Verification

Default focused verification:

```bash
pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py
git diff --check
```

If report/summary JSON is generated:

```bash
python -m json.tool reports/<summary-file>.json >/dev/null
```

Safety grep:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" quant_bitcoin backend frontend docs reports STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks
```

Expected:

- no new live-trading behavior;
- no new order/account/private endpoint behavior;
- no committed secrets;
- declarative safety text is acceptable.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the
result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before
merge.

# Completion Summary Required

- files changed
- strategy document created/updated
- data coverage
- run ids
- parameter grid
- results summary
- yearly attribution summary
- tests run
- known limitations
- whether this supports or weakens the information-delay timeframe hypothesis
- recommended next task
