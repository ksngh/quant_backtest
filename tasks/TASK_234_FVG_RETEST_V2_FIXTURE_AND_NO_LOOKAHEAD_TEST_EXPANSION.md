# Task 234: FVG Retest V2 Fixture and No-Lookahead Test Expansion

# Goal

Create reusable deterministic fixtures and regression tests for FVG v2 multi-timeframe trend, Fibonacci confluence, retest/reaction entries, liquidity targets, and stop modes.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Test fixture and regression-test owner for FVG v2 research mechanics.
- Supporting roles:
  - Indicator role.
  - Pattern detector role.
  - Backtest strategy role.
  - Risk/exit role.
  - CLI role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The FVG v2 task batch touches several shared contracts. Dedicated fixtures are needed so later changes do not accidentally introduce look-ahead, change baseline FVG behavior, or misreport retest fill quality.

# Scope

- Add or extend synthetic fixtures under `tests/fixtures/` for bullish and bearish FVG retests.
- Include 1m base candles with deterministic 5m/15m aggregate behavior.
- Include examples for trend-aligned, trend-misaligned, Fibonacci-confluent, non-confluent, liquidity-target-present, liquidity-target-missing, touch-without-reaction, and stop-hit cases.
- Add helper assertions for no-lookahead higher-timeframe visibility.
- Add metadata snapshot fixtures for expected diagnostic keys without overfitting exact profitability results.
- Ensure fixtures can be reused by detector, entry, risk, CLI, parameter-grid, and frontend/API tests.

# Out of Scope

- No new production strategy behavior unless needed solely to expose fixture hooks from prior tasks.
- No large historical data files committed to the repo.
- No external data download.
- No benchmark performance claims.

# Requirements

- Fixtures must be small, deterministic, and easy to reason about from raw candles.
- Bullish and bearish directions must both be represented.
- No-lookahead assertions must cover higher-timeframe boundary transitions and pivot confirmation delays.
- Fixture metadata must document intended scenario and expected behavior.
- Existing synthetic pattern fixtures must not be broken or renamed unnecessarily.
- Tests must avoid brittle dependence on unrelated metric ordering unless the order is part of the contract.

# Status Tracking

## Execution Notes

- Assumption: fixtures remain test-only and introduce no public API/schema changes.
- Assumption: fixture metadata snapshots validate expected keys without overfitting profitability metrics.
- Blockers: none for Task 234.
- Safety: fixtures contain no credentials, API keys, endpoint references, network calls, or live trading behavior.

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

- Added reusable `tests/fixtures/synthetic_fvg_v2.py` bullish/bearish retest v2 scenarios.
- Added fixture tests for shape, baseline FVG event detection, multi-timeframe visibility, pivot confirmation delay, reaction no-fill, and diagnostic key snapshots.
- Verification:
  - `pytest tests/fixtures tests/indicators tests/patterns/test_fair_value_gap.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_parameter_grid.py`

# Acceptance Criteria

- Reusable FVG v2 fixture helpers exist and are imported by multiple test modules.
- No-lookahead regression tests fail if incomplete 5m/15m candles leak into 1m events.
- Baseline FVG tests prove default behavior is unchanged when FVG v2 options are disabled.
- Retest/reaction/target/stop scenarios are independently testable.
- Full targeted test suite passes deterministically.

# Required Tests

## Unit Tests

- `tests/fixtures/test_synthetic_fvg_v2.py` validates fixture shape, scenario labels, and expected candle relationships.
- No-lookahead helper tests for multi-timeframe visibility and pivot confirmation.
- Metadata snapshot tests for event/action diagnostic keys.

## Integration Tests

- Run FVG detector, entry simulation, risk planner, and CLI tests using shared fixtures.
- Parameter-grid smoke test over fixture dataset.

## Contract Tests

- Document fixture scenario names and intended reuse in a test README or fixture module docstring.
- Confirm no public API schema change is introduced solely by fixtures.

## Safety Tests

- Fixtures contain no credentials, API keys, or external endpoint references.
- Tests perform no network calls.

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
pytest tests/fixtures tests/indicators tests/patterns/test_fair_value_gap.py tests/backtesting/test_pattern_action_builder.py
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_parameter_grid.py
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
