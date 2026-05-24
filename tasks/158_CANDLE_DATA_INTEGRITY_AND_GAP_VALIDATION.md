# Goal

Strengthen candle data validation before strategy evaluation so duplicate timestamps, missing intervals, invalid OHLC values, and timezone inconsistencies do not silently distort backtests.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `PostgresCandleDataProvider.load()` parses and sorts candles but does not visibly enforce strict uniqueness/gap/OHLC invariant checks.
- `strategy_engine._validate_candles()` checks required columns and monotonic increasing timestamps only.
- Several detectors validate some OHLC fields independently, but canonical validation should happen before simulation.

Read and inspect:

- `quant_bitcoin/market_data/postgres_provider.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/patterns/*` normalization functions
- `quant_bitcoin/persistence/postgres.py`
- existing candle provider/data contract tests

# Extracted Roles

- Owner role:
  - Market-data contract owner for backtest input correctness.
- Supporting roles:
  - Provider role: normalizes database rows to standard candles.
  - Engine role: rejects invalid backtest input.
  - Persistence role: supplies rows without changing trading logic.
- Forbidden roles:
  - No exchange download behavior changes unless only data quality metadata is needed.
  - No frontend behavior.
  - No live trading behavior.

# Context

Code-level hints:

- Add a reusable validator, for example `quant_bitcoin/market_data/candle_validation.py` or `quant_bitcoin/backtesting/candle_validation.py`.
- Use it from `PostgresCandleDataProvider.load()` and `run_strategy_backtest_engine()`.
- For interval gap detection, map supported intervals such as `1m`, `3m`, `5m`, `15m`, `30m`; allow opt-out if a provider cannot guarantee continuity.
- Check:
  - required columns;
  - finite numeric open/high/low/close/volume;
  - strictly increasing timestamp;
  - no duplicate timestamp;
  - `high >= max(open, close)`;
  - `low <= min(open, close)`;
  - `high >= low`;
  - positive prices;
  - non-negative volume;
  - UTC-aware or normalized timestamps.

Functional intent:

- Bad candle data should fail fast before signal generation or accounting.

# Scope

- Implement reusable standard candle validation.
- Wire validation into PostgreSQL provider and canonical strategy engine.
- Keep errors clear and actionable.
- Add tests for duplicate, missing, invalid OHLC, invalid numeric, and timezone cases.

# Out of Scope

- Historical data repair/backfill automation.
- Live WebSocket gap fill.
- Dashboard display of data quality.
- Exchange API changes.

# Requirements

- Duplicate timestamps must be rejected or explicitly deduplicated by a documented policy; prefer rejection for backtests.
- Missing interval gaps must be detected when interval is known.
- OHLC invariant violations must raise `ValueError` before strategy evaluation.
- Timestamp timezone handling must be deterministic.
- Validators must not mutate caller input unexpectedly.
- Existing valid fixtures must continue to pass.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Backtest engine rejects duplicate timestamps.
- Backtest engine rejects invalid OHLC rows.
- Provider detects missing `1m` candle gaps when configured to enforce continuity.
- Error messages identify the violated field or timestamp.
- All pattern detectors still receive valid normalized candles.

# Required Tests

## Unit Tests

- Add validator tests for every invalid candle case.
- Test timezone normalization/rejection policy.
- Test no-mutation behavior.

## Integration Tests

- Add provider-level tests with duplicated and missing PostgreSQL-style rows.
- Add canonical engine tests proving invalid input is rejected before actions execute.

## Contract Tests

- Ensure standard candle schema remains `timestamp`, `open`, `high`, `low`, `close`, `volume`.
- Document interval gap policy where provider/engine config exposes it.

## Safety Tests

- Confirm no exchange endpoints or live trading behavior are introduced.
- Confirm no API keys or `.env` files are involved.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest tests/market_data tests/backtesting/test_strategy_engine.py tests/backtesting/test_basic.py
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
