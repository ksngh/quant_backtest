# Task 195: CUP_AND_HANDLE_LOCAL_TREND_AND_BREAKOUT_RETEST

# Goal

Improve Cup-and-Handle robustness by replacing global prior-uptrend logic with local trend context and adding neckline retest/failure handling.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P2**

# Extracted Roles

- Owner role: Project owner / quant research lead.
- Supporting roles:
  - Quant researcher: validate economic assumptions, score calibration, and OOS diagnostics.
  - System trading architect: maintain action, risk, sizing, cost, and execution contracts.
  - Backtest verification engineer: preserve no-lookahead, fill correctness, intrabar policy, and deterministic tests.
  - Code reviewer: enforce scope, safety, and architecture boundaries.
- Forbidden roles:
- Live trading implementation unless the task explicitly says otherwise.
- Real exchange order execution.
- Secret/key management changes outside documented safety scope.
- Unrelated frontend/backend/database changes unless listed in Scope.

# Context

- Current prior uptrend check compares left rim close/high against the first candle in the supplied frame.
- This makes detection sensitive to caller window start.
- Risk planner creates neckline soft-exit metadata, but automatic simulator integration must be ensured in a later/common task.

# Scope

- quant_bitcoin/patterns/cup_and_handle.py
- quant_bitcoin/patterns/cup_and_handle_risk_exit.py
- quant_bitcoin/patterns/entry_simulation.py
- tests/patterns/test_cup_and_handle.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Add local prior uptrend config: lookback window, minimum return rate, optional higher-high condition.
- Keep legacy global prior uptrend available only as explicit compatibility mode.
- Add neckline retest entry mode and breakout follow-through confirmation options.
- Expose prior_uptrend_method, prior_uptrend_strength, neckline_retest_status, and handle_quality metadata.
- Clarify detector target_reference versus risk measured target semantics.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for this task's historical context.
- [x] Confirm this task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Identify exact source files and tests touched by this task.
- [x] Confirm no live trading, real order execution, signed exchange request, or secret handling is introduced.

Assumptions before implementation:
- Local prior-uptrend logic should become the default while legacy/global behavior remains explicitly selectable.
- Neckline retest entry is simulated as a deterministic limit touch against the event neckline/entry reference.
- Breakout follow-through uses completed candles only and remains opt-in.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Local prior uptrend fixture passes independent of frame start.
- Legacy behavior is available when selected.
- Neckline retest mode waits for retest and skips if no retest within max_wait_bars.
- Breakout failure below neckline exits or skips according to configured policy.

# Required Tests

## Unit Tests

- Unit: local uptrend detected over fixed lookback.
- Unit: same pattern rejected when local uptrend absent.
- Unit: neckline retest fill/no-fill cases.
- Unit: detector target_reference and risk measured_target are both documented in metadata.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Existing events may disappear if default prior-uptrend logic changes.
- Retest mode reduces trade count.

# Review Checklist

- [x] Scope respected.
- [x] Requirement matched.
- [x] Role ownership respected.
- [x] Architecture boundaries respected.
- [x] Data contract respected where applicable.
- [x] No hardcoded secrets.
- [x] No real order execution unless explicitly requested by a future owner-approved live task.
- [x] No unnecessary abstractions.
- [x] No lookahead introduced.
- [x] Pattern/risk/indicator semantics are documented in metadata or docs.
- [x] Tests cover both success and failure/skip paths.

# Verification

Default:

```bash
pytest
```

Recommended targeted verification for this task:

```bash
pytest tests/patterns tests/risk tests/backtesting
pytest tests/strategies
git diff --check
```

If frontend files are changed:

```bash
cd frontend && npm run build
```

If backend/API files are changed and dependencies are available:

```bash
pytest backend/tests
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

# Completion Summary

- Files changed:
  - `quant_bitcoin/patterns/cup_and_handle.py`
  - `quant_bitcoin/patterns/entry_simulation.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `quant_bitcoin/strategies/pattern_execution_policy.py`
  - `tests/patterns/test_cup_and_handle.py`
  - `tests/patterns/test_cup_and_handle_risk_exit.py`
  - `tests/patterns/test_entry_simulation.py`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_195_CUP_AND_HANDLE_LOCAL_TREND_AND_BREAKOUT_RETEST.md`
- Implementation summary:
  - Replaced default prior-uptrend evaluation with local lookback configuration while preserving explicit `LEGACY_GLOBAL` compatibility mode.
  - Added neckline retest status, follow-through bars, handle-quality metadata, and target-reference semantics metadata.
  - Added `LIMIT_AT_NECKLINE_RETEST` entry simulation support and policy/action metadata wiring.
- Tests added or updated:
  - Added local uptrend pass/fail tests, neckline retest/failure status tests, and neckline retest entry simulation coverage.
  - Updated Cup-and-Handle risk fixture for expanded event metadata.
- Tests run:
  - `pytest tests/patterns/test_cup_and_handle.py tests/patterns/test_cup_and_handle_risk_exit.py tests/patterns/test_entry_simulation.py tests/strategies/test_pattern_execution_policy.py`
  - `pytest tests/patterns tests/risk tests/backtesting tests/strategies`
  - `git diff --check`
- Codex self-review result:
  - Scope, no-lookahead boundaries, offline-only safety, test coverage, and ledger updates checked against `reviews/CODEX_SELF_REVIEW.md`.
- Known limitations:
  - Neckline retest/failure is OHLC close/range based and does not infer intrabar sequence.
- Recommended next task:
  - Task 196 `DIAMOND_PIVOT_SPLIT_AND_BOUNDARY_VALIDATION`.
