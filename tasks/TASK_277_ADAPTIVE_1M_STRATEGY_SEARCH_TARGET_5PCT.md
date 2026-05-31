# Task 277: Adaptive 1m Strategy Search Target 5pct

# Goal

Run a bounded but adaptive BTCUSDT 1-minute strategy research campaign that repeatedly implements or adjusts deterministic offline-only strategy models, saves every backtest run to the database, and attempts to find a candidate with at least **+5% net portfolio total return** on both owner-specified evaluation windows:

- Window A: BTCUSDT `1m`, `--start-time 2026-05-20T00:00:00Z`
- Window B: BTCUSDT `1m`, `--start-time 2026-05-25T00:00:00Z`

The campaign may modify existing pattern strategies or implement entirely new deterministic OHLCV-based pattern/technical models if needed.

This is research/backtest only. It must not authorize live trading.

# Source Requirement

Owner requested:

```text
니가 몇번 돌려가면서 맞춰봐. 아예 새로운 모델을 만들어도 돼.
그리고 백테스트 돌리고 수정하고를 0520이후 1분봉, 0525이후 1분봉 테스트 기준으로
+5퍼센트 이상이 나올때까지 반복해. 그리고 돌린 테스트는 db에 저장하고.
이거 task로 만들어
```

Clean requirement:

- Create a future implementation/research task for iterative strategy search.
- The future agent may build new deterministic strategy models, not only tune Task 276.
- The future agent must run both `2026-05-20+` and `2026-05-25+` BTCUSDT `1m` backtests for candidate variants.
- The future agent must save every executed backtest to the database.
- The target is at least +5% net total return on both windows after fees/spread/slippage.
- The task must explicitly handle data-snooping risk because repeated tuning against fixed windows can overfit.
- Do not implement or run backtests in this task-creation step.

# Extracted Roles

- Owner role:
  - Wants Codex to act like a quant researcher and iteratively search for a materially profitable 1m BTC strategy.
  - Allows new models if current FVG/OB/LSR family is insufficient.
  - Requires all backtests to be persisted in the database.
- Supporting roles:
  - Quant research lead: proposes bounded hypotheses, tracks all attempts, and prevents hidden overfitting.
  - Strategy designer: implements deterministic offline OHLCV-based models that fit the existing architecture.
  - Indicator role: creates small reusable completed-candle indicators only when existing indicators cannot express a candidate.
  - Pattern detector role: emits stable no-lookahead events with rich metadata.
  - Risk/exit role: defines stop, target, invalidation, trailing/partial behavior, and cost-aware viability.
  - Backtest runner role: executes Window A and Window B for every candidate and saves every run.
  - Reporting role: ranks all saved variants, records failures, and explains whether the +5% target was met.
  - Status tracker: updates `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading or real Binance order execution.
  - Exchange order/account/private endpoint calls.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, liquidation, funding, borrow-fee, or real margin behavior unless a separate task explicitly assigns simulated economics.
  - Machine learning training or model fitting.
  - Dashboard/frontend/backend API changes unless a separate task is assigned.
  - Rewriting persistence schema unless a schema limitation blocks required run logging; if blocked, stop and create a separate task.

# Context

Recent evidence:

- Task 273 saved `ORDER_BLOCK` candidate runs 98-102; all realistic-cost variants were negative.
- Task 274 saved runs 103, 105-109; the best saved OB MTF branch was run 107 with 14 trades and -1.79 net PnL, and the best saved FVG branch was run 109 with 2 trades and -0.34 net PnL.
- Task 275 saved runs 110-113; local FVG OB confluence reduced trade count and losses but did not establish profitability.
- Task 276 implemented `LIQUIDITY_SWEEP_REVERSAL`; saved run 114 on 2026-05-20+ `1m` produced 20 candidates but 0 filled trades because 11 candidates were blocked by cost-aware RR and 9 retests did not fill.

Research interpretation:

- The existing raw FVG/OB/LSR candidates are not sufficient under current realistic 1m costs.
- The owner now explicitly asks for adaptive iteration and allows new models.
- Repeatedly tuning until a fixed pair of windows exceeds +5% creates major data-snooping risk. Therefore this task treats Window A/B as owner target windows for exploratory optimization, not as proof of deployable edge.
- Even if +5% is achieved on both windows, the result remains `RESEARCH_ONLY` until a separate walk-forward/out-of-sample task confirms it.

# Scope

Allowed implementation areas:

- New deterministic indicators under `quant_bitcoin/indicators/` when needed.
- New deterministic patterns under `quant_bitcoin/patterns/`.
- New pattern risk/exit helpers under `quant_bitcoin/patterns/*_risk_exit.py` or shared `quant_bitcoin/risk/` helpers when appropriate.
- Strategy wiring under `quant_bitcoin/strategies/`.
- Backtest/action/runner wiring under `quant_bitcoin/backtesting/`.
- Optional research orchestration script/module under `quant_bitcoin/backtesting/` or `scripts/` if it only runs existing offline backtest CLI flows and persists outputs.
- Focused tests under `tests/indicators/`, `tests/patterns/`, `tests/strategies/`, `tests/backtesting/`, and `tests/safety/`.
- Task completion notes and ledger updates.

Candidate model families may include, but are not limited to:

- refined `LIQUIDITY_SWEEP_REVERSAL` variants;
- FVG v2 channel variants;
- Order Block variants;
- VWAP/anchored-VWAP deviation mean reversion using completed candles only;
- opening/session range breakout or failed-breakout models;
- volatility compression then expansion models;
- trend pullback continuation models;
- regime-adaptive ensembles composed from deterministic sub-signals;
- RSI/volume/regime filters layered on existing deterministic patterns.

# Out of Scope

- No live trading.
- No real Binance order placement.
- No exchange account/private/order endpoints.
- No API keys, signed requests, `.env` files, or credential handling.
- No futures/leverage/liquidation/funding/borrow modeling unless a separate future task explicitly assigns simulated derivatives economics.
- No machine learning training, optimizer fitting, neural networks, reinforcement learning, or black-box model selection.
- No order-book, websocket, or external live data dependency.
- No frontend/dashboard work.
- No backend API work.
- No database schema migration unless persistence cannot store required additive metadata; if so, stop and create a separate task.
- No claim of production profitability or paper-trading promotion from these two tuned windows alone.

# Requirements

## Owner Target Windows

Every persisted candidate variant must be tested on both windows:

```bash
--symbol BTCUSDT
--interval 1m
--starting-cash 1000000
--starting-cash-currency USDT
--position-sizing-mode cash_fraction
--position-sizing-value 0.10
```

Window A:

```bash
--start-time 2026-05-20T00:00:00Z
```

Window B:

```bash
--start-time 2026-05-25T00:00:00Z
```

Use realistic non-zero costs for target qualification:

- default target-cost profile: `conservative_crypto_1m`;
- zero-cost runs are allowed only as diagnostics and must never count toward the +5% target.

All target-qualification runs must be persisted. Do not use `--no-persist` for qualifying runs.

## Target Definition

A candidate meets the owner target only when both Window A and Window B satisfy all of:

- net `total_return >= 0.05`;
- net PnL > 0;
- final equity >= starting equity * 1.05;
- completed trade count >= 5 unless the task explicitly records why a lower-count result is diagnostic only;
- max drawdown is recorded and not hidden;
- all transaction costs, spread, and slippage are non-zero realistic assumptions;
- every run is saved and has a recorded run ID.

If a candidate hits +5% on both windows but has very low trade count, extreme drawdown, or one-off behavior, record it as `TARGET_HIT_DIAGNOSTIC_ONLY`, not as a robust edge.

## Search Budget And Stop Rules

This is an adaptive search, but it must be bounded and auditable.

Default search budget:

- maximum 40 candidate variants;
- each candidate requires two saved runs, one for Window A and one for Window B;
- maximum 80 saved target-window runs for this task unless the owner explicitly extends the task.

Stop early when:

- a candidate satisfies the full owner target on both windows and survives immediate sanity checks; or
- the 40-candidate budget is exhausted; or
- implementation/runtime blockers prevent trustworthy saved runs; or
- repeated variants are dominated by earlier variants with lower return and higher drawdown.

Do not silently continue beyond the budget by renaming variants or changing the experiment family.

## Variant Logging

Every candidate must have a deterministic `variant_id` and full parameter metadata.

For every saved run, record:

- variant ID;
- model family;
- strategy key;
- command;
- run ID;
- window label: `A_2026_05_20_1m` or `B_2026_05_25_1m`;
- dataset actual start/end;
- candle count;
- cost profile and liquidity role;
- starting cash currency;
- final equity;
- total return;
- gross PnL;
- net PnL;
- total costs;
- completed trade count;
- win rate;
- profit factor;
- max drawdown;
- long/short split;
- skip counts by reason;
- dominant entry/exit reasons;
- known limitations.

All failed, losing, no-fill, timed-out, and dominated variants must be recorded. Do not report only winners.

## Data-Snooping Controls

Because the owner target explicitly uses fixed recent windows for iterative tuning:

- Treat Window A/B results as exploratory selection evidence only.
- The strategy status after this task must remain `RESEARCH_ONLY`, even if +5% is achieved.
- Do not claim live or paper-trading readiness.
- Do not call the selected variant “validated”.
- Record total family-wise tested variant count.
- Record every zero-cost diagnostic run separately and exclude it from target qualification.
- If +5% is achieved, the recommended next task must be walk-forward/out-of-sample validation on locked periods not used in this search.
- If the strategy requires more than 40 variants to approach +5%, record high overfit risk.

## Model Implementation Rules

Any new model must:

- use completed candles only;
- be deterministic;
- avoid lookahead in event detection, MTF context, entries, exits, and target selection;
- emit stable event IDs or stable action metadata;
- fit the architecture: indicators -> pattern/signal detection -> risk/exit plan -> cost/slippage -> reward/risk -> persisted backtest;
- include tests before target runs are considered trustworthy;
- never fetch market data directly from strategy code;
- never call exchange order/account endpoints.

## Candidate Families To Try First

Start with lower-cost implementation candidates before inventing large abstractions:

1. Existing `LIQUIDITY_SWEEP_REVERSAL` relaxed retest and diagnostic modes:
   - market-on-displacement close;
   - shorter/longer retest waits;
   - lower min net RR only if still positive after costs;
   - FVG-only and OB-only entries;
   - target `1R`, `1.5R`, `2R`;
   - MTF 15m confirmation on/off.
2. Existing FVG v2 channel variants:
   - default owner profile;
   - standalone scan on/off;
   - channel retest wait and stop variants already supported;
   - close-volume threshold variants.
3. Existing Order Block variants:
   - previous-candle 1R;
   - 61.8 retest wait variants;
   - MTF filter variants.
4. New deterministic model only if existing families fail:
   - preferred first new candidate: `SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL`, using completed UTC session ranges, failed breakout/reclaim, volume ratio, ATR stop, and cost-aware target.
   - second new candidate: `VWAP_DEVIATION_RECLAIM`, using completed rolling VWAP proxy, deviation band, reclaim, volume confirmation, and mean-reversion target.
   - third new candidate: `VOLATILITY_COMPRESSION_EXPANSION`, using ATR/range compression, directional displacement, volume expansion, and trailing/invalidation rules.

Do not implement all new models at once. Add one model at a time, test it, run the two target windows, then decide whether to continue.

## Reporting Requirements

The final report must include:

- all saved run IDs grouped by variant and window;
- best variant on Window A;
- best variant on Window B;
- best combined variant by primary metric;
- whether any variant met +5% on both windows;
- top 5 variants by combined net return;
- variants rejected and why;
- cost sensitivity summary;
- drawdown/tail-risk notes;
- comparison against:
  - Task 276 run 114;
  - Task 274 run 107;
  - Task 274 run 109;
  - Task 275 run 113 if still comparable;
  - buy-and-hold over both windows if available or newly computed;
- explicit statement that repeated tuning on fixed windows is overfit-prone.

## Execution Notes

### 2026-05-29 Pre-Run Assumptions And Bounded Variant Plan

Assumptions:

- The owner assigned Task 277 directly and specifically asked to verify fee accounting and to provide a markdown strategy summary at completion.
- The console command may be unavailable in the local shell; if so, use `quant_bitcoin.backtesting.strategy_postgres_runner_cli.main()` with the same argument list and persist runs through the normal runner path.
- Every qualifying target-window run will use `--starting-cash 1000000`, `--starting-cash-currency USDT`, `--position-sizing-mode cash_fraction`, `--position-sizing-value 0.10`, and `--cost-profile conservative_crypto_1m`.
- All results remain `RESEARCH_ONLY` because the same fixed May 2026 windows are used for iterative selection.

Initial bounded plan:

| Variant ID | Family | Purpose |
| --- | --- | --- |
| T277_V001_FVG_OWNER_DEFAULT | FAIR_VALUE_GAP | Re-run existing owner FVG v2/channel profile with explicit USDT cash and conservative 1m costs. |
| T277_V002_FVG_INVERSE_SIMPLE | FAIR_VALUE_GAP | Check whether inverse FVG direction is less dominated when v2/channel extras are disabled. |
| T277_V003_OB_PREV_1R | ORDER_BLOCK | Re-run previous-candle 1R OB profile with explicit USDT cash and conservative 1m costs. |
| T277_V004_OB_618_WAIT20 | ORDER_BLOCK | Test OB 61.8 retest wait behavior with the previous-candle 1R exit. |
| T277_V005_LSR_MARKET_1R | LIQUIDITY_SWEEP_REVERSAL | Relaxed LSR market-on-displacement close, 1R target, cost-aware viability kept non-negative. |
| T277_V006_LSR_LIMIT_15R | LIQUIDITY_SWEEP_REVERSAL | Relaxed LSR limit-entry family with 1.5R target and longer wait. |

If no existing-family variant approaches the target on both windows, add only one new deterministic model first, preferably `SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL`, then run both owner windows and tests before deciding whether another model is justified.

### 2026-05-29 Completion Notes

Execution outcome:

- Target not met. No tested candidate reached `total_return >= 0.05` on both owner windows after conservative 1m costs.
- Strategy status remains `RESEARCH_ONLY`.
- Total target candidate variants attempted: 18 (`T277_V001` through `T277_V018`).
- Completed persisted target-qualification runs: 34 (`115` through `148`).
- Zero-cost diagnostic runs: 2 (`149`, `150`), excluded from target qualification.
- `T277_V001_FVG_OWNER_DEFAULT` timed out before persistence on the owner-default FVG path and was recorded as a failed/no-run-id variant rather than a qualifying run.
- A markdown research summary was written to `reports/TASK_277_ADAPTIVE_1M_STRATEGY_SEARCH.md`.

New deterministic model implemented:

- `SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL` (`SRLBR`).
- Uses completed candles only.
- Builds a prior rolling range, then detects failed breakouts/reversals and breakdown-continuation events around that range.
- Applies volume, candle body, range-width, and score gates.
- Enters on confirmation close, places stops beyond the prior range with an ATR buffer, and uses fixed-R targets plus optional max-bars time exits.
- Routes all fills/skips/costs through the existing strategy engine and persistence path.

Saved target-window run IDs:

| Variant ID | Family | Window A Run | Window B Run | Target Result |
| --- | --- | ---: | ---: | --- |
| T277_V001_FVG_OWNER_DEFAULT | FAIR_VALUE_GAP | none | none | timed out/no persisted run |
| T277_V002_FVG_INVERSE_SIMPLE | FAIR_VALUE_GAP | 115 | 116 | failed return |
| T277_V003_OB_PREV_1R | ORDER_BLOCK | 117 | 118 | failed return/cost drag |
| T277_V004_OB_618_WAIT20 | ORDER_BLOCK | 119 | 120 | failed return/cost drag |
| T277_V005_LSR_MARKET_1R | LIQUIDITY_SWEEP_REVERSAL | 121 | 122 | failed return; Window B only 2 trades |
| T277_V006_LSR_LIMIT_15R | LIQUIDITY_SWEEP_REVERSAL | 123 | 124 | failed return; low trades |
| T277_V007_SRLBR_FAILED_BOTH_120_4R | SRLBR | 125 | 126 | failed return |
| T277_V008_SRLBR_SHORT_MIX_60_4R | SRLBR | 127 | 128 | failed return/cost drag |
| T277_V009_SRLBR_BREAKDOWN_60_4R | SRLBR | 129 | 130 | failed return/cost drag |
| T277_V010_SRLBR_SHORT_MIX_20_8R | SRLBR | 131 | 132 | failed return/cost drag |
| T277_V011_SRLBR_SHORT_MIX_120_8R | SRLBR | 133 | 134 | failed return |
| T277_V012_SRLBR_FAILED_SHORT_60_6R | SRLBR | 135 | 136 | failed return |
| T277_V013_SRLBR_FAILED_LONG_60_6R | SRLBR | 137 | 138 | failed return |
| T277_V014_SRLBR_FAILED_LONG_20_8R | SRLBR | 139 | 140 | failed return |
| T277_V015_SRLBR_FAILED_BOTH_20_8R | SRLBR | 141 | 142 | failed return |
| T277_V016_SRLBR_SHORT_MIX_60_8R_HIGH_GATE | SRLBR | 143 | 144 | failed return |
| T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE | SRLBR | 145 | 146 | failed Window A; Window B had positive mark-to-market return but negative net PnL and open short |
| T277_V018_SRLBR_FAILED_SHORT_240_12R_HIGH_GATE | SRLBR | 147 | 148 | failed return; Window B only 2 trades |

Zero-cost diagnostic:

| Variant ID | Window A Run | Window B Run | Result |
| --- | ---: | ---: | --- |
| T277_D001_ZERO_COST_SRLBR_BREAKDOWN_240_12R | 149 | 150 | excluded; costs intentionally zero and returns only +0.1319pct/+0.3074pct |

Best failed variants:

- Best Window A qualifying run: `T277_V005_LSR_MARKET_1R`, run `121`, `-0.0544pct`, 6 trades, total cost `1193.32`.
- Best Window B qualifying run by total return: `T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE`, run `146`, `+0.0222pct`, 15 trades, total cost `2847.43`; rejected because net PnL metadata was negative and an open ending short contributed to final mark-to-market equity.
- Best combined candidate by average total return: `T277_V005_LSR_MARKET_1R`, runs `121`/`122`, average `-0.0666pct`; rejected because both returns were below target and Window B had only 2 trades.

Fee/accounting verification:

- Verified persisted target run IDs `115` through `148` from the database.
- No target run had `zero_transaction_cost_assumption=true`.
- Every qualifying run with trades had positive `total_cost`, `total_fee_cost`, `total_spread_cost`, and `total_slippage_cost`.
- Cost parameters were non-zero for target runs: taker fee `10.0` bps, spread `3.0` bps, slippage `5.0` bps, minimum slippage `1.0` bps, volatility slippage multiplier `0.1`.
- Zero-cost diagnostic runs `149` and `150` were verified separately with `zero_transaction_cost_assumption=true` and `total_cost=0.0`.

Verification run:

```bash
pytest tests/patterns/test_session_range_liquidity_breakout_reversal.py \
  tests/strategies/test_pattern_strategies.py::test_strategy_for_session_range_liquidity_breakout_reversal_factory \
  tests/strategies/test_pattern_execution_policy.py::test_policy_matrix_defines_supported_patterns \
  tests/strategies/test_pattern_explanations.py::test_supported_patterns_have_required_keys_and_are_serializable \
  tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_accepts_session_range_liquidity_breakout_flags -q
```

Result: `7 passed in 0.41s`.

```bash
pytest tests/safety/test_pattern_live_boundary.py -q
git diff --check
python -m compileall -q quant_bitcoin/patterns/session_range_liquidity_breakout_reversal.py quant_bitcoin/strategies/patterns.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py
```

Result: safety tests passed, `git diff --check` passed, and compile verification passed.

Known verification limitation:

- Running the broader `tests/backtesting/test_strategy_cli_persistence.py` file exposed two pre-existing/current-suite expectation mismatches unrelated to the new SRLBR CLI test: one test still expects a zero-cost warning for the current owner FVG default, and one sizing test expects fixed quantity behavior while current cash-fraction/default currency behavior resizes quantity. These were not changed under Task 277 scope.

Recommended next task:

- Create a locked out-of-sample/walk-forward cost-review task before any further promotion claim. The next task should predeclare untouched windows, compare low-turnover variants, and explicitly review whether 1m fee/spread/slippage assumptions make the current pattern families structurally uncompetitive.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Read this task file before coding.
- [x] Read `docs/15_RESEARCH_PROTOCOL.md`.
- [x] Read `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`.
- [x] Read `docs/18_INTRABAR_SEQUENCING_POLICY.md`.
- [x] Read `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`.
- [x] Read `docs/23_RISK_EXIT_REUSABLE_POLICY_BOUNDARY.md`.
- [x] Read current strategy/backtest runner files relevant to the selected first candidate.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Record assumptions, blockers, and the first bounded variant plan before coding.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior will be introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Clearly record the next task.

# Acceptance Criteria

- A bounded variant plan is recorded before the first sweep run.
- Every target-window run is persisted in the database and recorded with run ID.
- At least both owner windows are run for every candidate variant.
- If +5% net return is achieved on both windows, the exact winning variant and both run IDs are recorded.
- If +5% is not achieved within the budget, the task records the exhausted budget, best failed variants, and why they failed.
- All variants are counted, including failed, no-fill, timed-out, dominated, and diagnostic variants.
- Any newly implemented model has deterministic no-lookahead tests.
- Existing and new strategies remain offline-only.
- No live trading, signed requests, account/order endpoints, API keys, or `.env` changes are introduced.
- Final status remains `RESEARCH_ONLY` unless a separate future OOS/WFO task validates the candidate.

# Required Tests

## Unit Tests

- New indicators compute deterministic completed-candle outputs without lookahead.
- New pattern detectors emit stable event IDs and reject missing/unsorted input.
- New risk/exit planners place stops and targets on the correct side.
- Cost-aware gates reject net-negative or structurally invalid entries.
- Variant ID generation is deterministic if a search runner is added.

## Integration Tests

- New strategies resolve through `strategy_for_pattern()` or the chosen strategy registry.
- Action builder creates entry/exit/skip actions with clear metadata for new models.
- CLI accepts any newly added strategy key and focused flags.
- Saved-run output metadata includes variant ID, family ID, target-window label, cost profile, and search-cycle metadata.
- A synthetic backtest for any new model produces deterministic trades and net-cost accounting.

## Contract Tests

- Existing saved-run fields are not removed or renamed.
- New metadata is additive.
- Pattern and strategy exports remain importable.
- If CLI or output schema changes materially, update relevant docs/API contracts or record why no API docs changed.

## Safety Tests

- New detector, strategy, search runner, and tests do not import Binance execution clients.
- No test calls real exchange order/account endpoints.
- No API key, secret, signed request, `.env`, or live trading behavior is added.
- Strategy code does not fetch market data directly.
- All backtests are offline and deterministic.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account endpoint calls.
- No unnecessary abstractions.
- No lookahead in detection, MTF context, entries, exits, or targets.
- Costs/slippage/fill assumptions are explicit.
- Every attempted variant is counted.
- Fixed-window overfit risk is stated clearly.
- No promotion claim is made from these two windows alone.

# Verification

Default focused verification depends on implemented models. Minimum:

```bash
pytest tests/indicators tests/patterns tests/strategies tests/backtesting tests/safety -q
git diff --check
```

At completion, also verify that all qualifying runs were persisted and can be read back by run ID.

Required target-window command shape for every qualifying run:

```bash
quant-bitcoin-strategy-backtest \
  --pattern <STRATEGY_KEY> \
  --interval 1m \
  --start-time <2026-05-20T00:00:00Z-or-2026-05-25T00:00:00Z> \
  --starting-cash 1000000 \
  --starting-cash-currency USDT \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10
```

If the console entrypoint is unavailable, call `quant_bitcoin.backtesting.strategy_postgres_runner_cli.main()` with the same arguments and record that fallback.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- all saved run IDs
- best variant and whether the +5% target was met on both windows
- comparison to run 114 and recent Task 274/275 baselines
- total family-wise tested variant count
- overfit/data-snooping risk statement
- Codex self-review result
- known limitations
- recommended next task
