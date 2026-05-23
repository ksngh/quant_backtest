# Goal

Fix the canonical strategy backtest CLI failure where a run reaches JSON output and crashes because a `pandas.Timestamp` value is not JSON serializable, then masks the original error with an invalid runtime logger call.

# Source Requirement

User reported this runtime failure after running `quant-bitcoin-strategy-backtest`:

```text
TypeError: Object of type Timestamp is not JSON serializable

During handling of the above exception, another exception occurred:

TypeError: log_runtime_exception() takes 1 positional argument but 2 were given
```

# Extracted Roles

- Owner role: Canonical strategy backtest CLI output and exception handling.
- Supporting roles: Runtime logging helper, CLI regression tests.
- Forbidden roles: Live trading, exchange order execution, account endpoint access, unrelated dashboard/API changes.

# Context

The failure occurs after invoking the packaged console script from a Python 3.11 conda environment. The CLI should serialize all stdout JSON deterministically and should preserve useful error logging if an unexpected exception occurs.

# Scope

- Identify which `quant-bitcoin-strategy-backtest` output field is carrying a raw `pandas.Timestamp`.
- Convert timestamp-like values in CLI stdout payloads to JSON-safe strings before `json.dumps`.
- Correct the strategy CLI exception logging call so it matches the current `log_runtime_exception` signature.
- Add focused regression coverage for timestamp serialization and exception logging behavior.

# Out of Scope

- Changing strategy/backtest financial semantics.
- Adding new backtest features or new CLI options.
- Changing persistence schema or dashboard behavior unless required to fix the serialization bug.
- Live trading or exchange order/account API usage.

# Requirements

- A successful strategy backtest run must not emit raw `pandas.Timestamp` objects in the JSON payload.
- Runtime metadata, events, diagnostics, executions, and nested metadata must be JSON serializable.
- Unexpected CLI exceptions must be logged without raising a secondary `TypeError`.
- Existing public CLI names and documented options must remain compatible.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `quant-bitcoin-strategy-backtest` can serialize a normal successful result payload containing timestamp-like values.
- The CLI exception handler calls `log_runtime_exception` with the supported signature.
- A regression test fails on the reported bug before the fix and passes after the fix.
- No unrelated behavior is changed.

# Required Tests

## Unit Tests

- Add or update focused tests around strategy CLI JSON serialization of timestamp-like payloads.
- Add or update a focused test for the CLI `main` exception logging path if practical.

## Integration Tests

- Run the relevant strategy CLI test module or a targeted CLI invocation with `--no-persist` if a database-independent fixture exists.

## Contract Tests

- Confirm existing CLI options still parse, including `--pattern`, `--start-time`, and `--starting-cash`.

## Safety Tests

- Confirm no live trading behavior, exchange order endpoints, signed requests, or API-key handling are introduced.

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
pytest
```

Targeted:

```bash
pytest -q tests -k "strategy_postgres_runner_cli or runtime_exception or json"
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

# Completion Notes

- Completed (2026-05-23): added JSON-safe recursive serialization for canonical strategy CLI output, fixed strategy and pattern CLI exception logging calls, and added focused regression coverage for timestamp metadata serialization plus logger signature compatibility.
- Verification passed:
  - `/opt/anaconda3/envs/quant-bitcoin/bin/python -m pytest -q tests/backtesting/test_strategy_cli_persistence.py tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `/opt/anaconda3/envs/quant-bitcoin/bin/python -m pytest -q tests -k "strategy_postgres_runner_cli or runtime_exception or json"`
  - `/opt/anaconda3/envs/quant-bitcoin/bin/python -m py_compile quant_bitcoin/backtesting/strategy_postgres_runner_core.py quant_bitcoin/backtesting/strategy_postgres_runner_cli.py quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
  - `/opt/anaconda3/envs/quant-bitcoin/bin/quant-bitcoin-strategy-backtest --help`
  - `git diff --check`
- Full `/opt/anaconda3/envs/quant-bitcoin/bin/python -m pytest -q` completed with unrelated existing failures in `tests/strategies/test_single_pattern_strategies.py::test_diamond_bullish_event_enters_long` and `test_diamond_bearish_event_enters_short`; 630 passed, 1 skipped, 2 failed.
