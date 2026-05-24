# Task 190: ENTRY_EXIT_INTRABAR_COMBINED_SEQUENCING

# Goal

Add a combined intrabar sequencing contract for candles where entry, stop, and target can all be touched in the same OHLC bar.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P0**

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

- Existing exit simulation resolves stop/target ambiguity, but entry simulation only checks whether a limit price is touched.
- If a limit entry, hard stop, and target are all within the same OHLC range, OHLC data does not reveal the true intrabar sequence.
- Current behavior can still embed optimistic or conservative assumptions depending on future_candles slicing and policy order.

# Scope

- quant_bitcoin/backtesting/intrabar_policy.py
- quant_bitcoin/patterns/entry_simulation.py
- quant_bitcoin/risk/exit_simulation.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- tests/backtesting/test_intrabar_policy.py
- tests/patterns/test_entry_simulation.py
- tests/risk/test_exit_simulation.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Extend IntrabarTouch/IntrabarDecision or add a new combined entry-exit decision object.
- Handle entry-only, entry+stop, entry+target, stop+target, and entry+stop+target touch cases.
- Expose CONSERVATIVE, OPTIMISTIC, STOP_FIRST, TARGET_FIRST, ENTRY_FIRST_THEN_STOP, ENTRY_FIRST_THEN_TARGET, and SKIP_AMBIGUOUS behavior for combined entry/exit cases.
- Record ambiguity metadata on entry SKIP, entry FILLED, and exit actions.
- Default canonical pattern backtests must use CONSERVATIVE unless explicitly overridden.
- Do not infer high/low order from OHLC; all decisions must be policy-driven.

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
- Existing exit-only ambiguity behavior remains backward compatible by default.
- Combined entry/exit sequencing applies when the first exit-simulation candle is also the entry-fill candle.
- Default canonical behavior remains `CONSERVATIVE`.
- No OHLC high/low ordering is inferred; outcomes are policy-driven only.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Same-candle all-three-touch fixtures produce deterministic outcomes under each supported policy.
- Ambiguous decisions record is_ambiguous, decision_reason, decision_outcome, and intrabar_policy.
- SKIP_AMBIGUOUS can skip ambiguous entry/exit cases without producing hidden fills.
- Existing exit-only ambiguity behavior remains backward compatible unless a combined policy is provided.

# Required Tests

## Unit Tests

- Unit: LONG entry, stop below, target above, all touched; conservative resolves to stop or skip according to policy.
- Unit: SHORT symmetric all-three-touch cases.
- Unit: entry+target touched but stop not touched under conservative and optimistic modes.

## Integration Tests

- Integration: pattern_action_builder emits metadata for ambiguous entry/exits.

## Contract Tests

- Regression: no target-first outcome occurs under CONSERVATIVE.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Conservative combined sequencing may reduce previously reported profitability.
- Some limit entry trades may become SKIP or immediate stop depending on policy.

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
  - `quant_bitcoin/risk/exit_simulation.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `tests/backtesting/test_intrabar_policy.py`
  - `tests/patterns/test_pattern_exit_simulation.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_190_ENTRY_EXIT_INTRABAR_COMBINED_SEQUENCING.md`
- Implementation summary:
  - Added combined entry/stop/target sequencing metadata and policy handling for cases where the first exit-simulation candle is the actual entry-fill candle.
  - Preserved existing exit-only ambiguity behavior unless the combined entry/exit condition is present.
  - Added `ENTRY_EXIT_AMBIGUOUS` SKIP behavior for skip-ambiguous cases and recorded `combined_intrabar_decision` metadata on entries/skips.
- Tests added or updated:
  - Added intrabar policy, exit simulation, and pattern action-builder tests for entry+target, entry+stop+target, conservative/optimistic, and skip-ambiguous behavior.
- Tests run:
  - `pytest tests/backtesting/test_intrabar_policy.py tests/patterns/test_pattern_exit_simulation.py tests/backtesting/test_pattern_action_builder.py`
  - `pytest tests/patterns tests/risk tests/backtesting tests/strategies`
  - `git diff --check`
- Codex self-review result:
  - Scope, architecture boundaries, offline-only safety, no-lookahead behavior, and documentation/ledger updates checked against `reviews/CODEX_SELF_REVIEW.md`.
- Known limitations:
  - OHLC bars still cannot reveal true high/low order; same-candle entry/exit outcomes remain policy-driven.
- Recommended next task:
  - Task 191 `PATTERN_EXECUTION_SIMULATION_TRACE_SCHEMA`.
