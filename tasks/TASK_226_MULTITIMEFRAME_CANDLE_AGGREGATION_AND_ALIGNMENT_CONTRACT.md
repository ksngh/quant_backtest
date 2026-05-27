# Task 226: Multi-Timeframe Candle Aggregation and Alignment Contract

# Goal

Add a deterministic multi-timeframe candle aggregation and alignment contract so 1m base-candle FVG evaluation can safely consume completed 5m, 15m, and future higher-timeframe context without look-ahead.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Market-data/backtest contract owner for offline multi-timeframe candle alignment.
- Supporting roles:
  - Indicator role.
  - Pattern backtest role.
  - Test fixture role.
  - Documentation/API contract role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

Current canonical pattern backtests evaluate a single candle stream. The next FVG research cycle needs higher-timeframe context, but higher-timeframe candles must only become visible after they are complete. This task creates the base alignment layer before any EMA or FVG scoring logic depends on it.

# Scope

- Verify existing candle timestamp semantics from `docs/04_DATA_CONTRACT.md`, providers, and tests before implementing alignment rules.
- Add a pure aggregation/alignment helper, likely `quant_bitcoin/backtesting/multitimeframe_candles.py` or `quant_bitcoin/indicators/multitimeframe.py`.
- Support configurable higher timeframes such as `5m`, `15m`, and `1h` from a lower-timeframe source such as `1m`.
- For each base candle, expose only the latest fully closed higher-timeframe candle available at that base candle timestamp.
- Emit explicit metadata for timeframe, source interval, close-availability semantics, warmup/cooldown, missing higher-timeframe rows, and no-lookahead guarantees.
- Integrate with the shared indicator cache only if the integration remains isolated and reusable for later tasks.

# Out of Scope

- No EMA, FVG, Fibonacci, entry, exit, or profitability logic in this task.
- No database schema migration unless an existing persistence contract requires metadata shape documentation only.
- No live market-data calls, exchange calls, websocket calls, or order-book dependency.
- No automatic resampling of arbitrary non-divisible intervals without an explicit validation error.

# Requirements

- Aggregation must be deterministic and pure: input candles in, aligned DataFrame/records out.
- Input candles must be sorted ascending; unsorted input must raise `ValueError` or reuse the existing project validation pattern.
- Higher-timeframe OHLCV must be computed using completed lower-timeframe candles only.
- The alignment function must not expose an in-progress 5m/15m candle to a 1m event that occurs before that higher-timeframe candle is complete.
- The output must make missing higher-timeframe context explicit rather than silently forward-filling unavailable data.
- The implementation must support future reuse by market-regime, trend-score, and pattern detectors without coupling to FVG internals.

# Status Tracking

## Execution Notes

- Assumption: source timestamps follow `docs/04_DATA_CONTRACT.md` and represent candle open time.
- Assumption: a higher-timeframe candle is visible when `close_time <= base timestamp`, so a 5m candle opened at `00:00` is first visible to the `00:05` base candle.
- Blockers: none for Task 226.
- Safety: implementation is pure pandas/offline code with no network, exchange, order, account, key, or `.env` behavior.

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Completed `quant_bitcoin/backtesting/multitimeframe_candles.py` with deterministic completed-candle aggregation and alignment metadata.
- Added `tests/backtesting/test_multitimeframe_candles.py` for 1m-to-5m/15m alignment, no-lookahead boundary behavior, validation, incomplete windows, row-count preservation, and offline safety.
- Updated `docs/04_DATA_CONTRACT.md` with multi-timeframe derived-candle semantics.
- Verification:
  - `pytest tests/backtesting/test_multitimeframe_candles.py`
  - `pytest tests/backtesting/test_pattern_detection_optimization.py tests/backtesting/test_strategy_cli_persistence.py`
  - `pytest tests/backtesting/test_pattern_detection_optimization.py tests/backtesting/test_strategy_postgres_runner_cli.py` could not run because `tests/backtesting/test_strategy_postgres_runner_cli.py` does not exist in this repository.

# Acceptance Criteria

- A documented helper can aggregate and align 1m candles to 5m and 15m completed candles.
- No-lookahead behavior is covered by boundary tests around higher-timeframe close transitions.
- Alignment metadata identifies source interval, target intervals, and availability semantics.
- The helper is reusable by later indicator/scoring tasks without importing strategy or execution modules.
- Existing single-timeframe tests continue to pass.

# Required Tests

## Unit Tests

- `tests/backtesting/test_multitimeframe_candles.py` covers 1m-to-5m and 1m-to-15m aggregation.
- Boundary test: a base candle before a 5m close does not see that 5m candle.
- Boundary test: the first base candle after a 5m close can see the completed 5m candle.
- Validation tests for unsorted timestamps, missing OHLCV columns, unsupported intervals, and partial final higher-timeframe windows.

## Integration Tests

- Optional shared indicator-cache integration test if a cache entry is added.
- Synthetic FVG-like dataset test confirming aligned higher-timeframe rows can be joined without changing raw candle count.

## Contract Tests

- Document alignment semantics in `docs/04_DATA_CONTRACT.md` or a focused multi-timeframe note if public metadata shape changes.
- Record that higher-timeframe data is derived from completed lower-timeframe candles and is not a live feed.

## Safety Tests

- Static check or targeted test confirms no exchange/order/account endpoint imports are added.
- No network calls in the aggregation helper or tests.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_multitimeframe_candles.py
pytest tests/backtesting/test_pattern_detection_optimization.py tests/backtesting/test_strategy_postgres_runner_cli.py
pytest
git diff --check
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
