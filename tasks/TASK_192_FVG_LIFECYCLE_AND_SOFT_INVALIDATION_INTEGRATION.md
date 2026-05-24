# Task 192: FVG_LIFECYCLE_AND_SOFT_INVALIDATION_INTEGRATION

# Goal

Wire FVG lifecycle state and midpoint reaction failure into actual post-entry exit simulation rather than leaving it as detached metadata.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P1**

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

- FVG detector has FRESH/PARTIALLY_FILLED/FILLED/BROKEN lifecycle classification.
- FVG risk planner creates FairValueGapReactionFailureRule metadata.
- simulate_pattern_exit currently consumes generic SoftInvalidationRule, so pattern-specific FVG rule must be explicitly converted and passed.

# Scope

- quant_bitcoin/patterns/fair_value_gap.py
- quant_bitcoin/patterns/fair_value_gap_risk_exit.py
- quant_bitcoin/risk/exit_simulation.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- tests/patterns/test_fair_value_gap.py
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

- Add a translator from FairValueGapReactionFailureRule to simulator-compatible soft/time invalidation behavior.
- Define side-aware favorable close after midpoint rule: LONG expects close > midpoint, SHORT expects close < midpoint within configured bars.
- Add optional post-entry FVG fill/break lifecycle monitoring using only candles after entry fill.
- Preserve retrospective_lifecycle as event-study only and prevent its accidental use in live-style signal detection.
- Record exit reason/metadata when reaction failure causes exit.

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
- Retrospective lifecycle remains an event-study option only and must not alter default signal-time detection.
- FVG reaction failure is evaluated only on candles after the simulated entry fill.
- LONG midpoint success requires close above the midpoint; SHORT midpoint success requires close below the midpoint within the configured reaction window.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A LONG FVG that fails to close above midpoint within reaction_failure_bars exits deterministically.
- A SHORT FVG symmetric case exits deterministically.
- FVG lifecycle updates use only post-fill candles.
- Retrospective lifecycle cannot contaminate signal-time detection tests.

# Required Tests

## Unit Tests

- Unit: midpoint reaction success does not trigger soft exit.
- Unit: midpoint reaction failure triggers SOFT_INVALIDATION or TIME_STOP with FVG-specific metadata.
- Unit: retrospective_lifecycle=True changes event-study output but is not used by at-index default.

## Integration Tests

- Integration: pattern_action_builder passes FVG soft invalidation rule when available.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- More FVG trades may exit early.
- Exit reason distributions will change.

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
  - `quant_bitcoin/backtesting/pattern_invalidation.py`
  - `quant_bitcoin/backtesting/pattern_strategy.py`
  - `tests/backtesting/test_pattern_invalidation.py`
  - `tests/patterns/test_pattern_exit_simulation.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_192_FVG_LIFECYCLE_AND_SOFT_INVALIDATION_INTEGRATION.md`
- Implementation summary:
  - Added FVG reaction-failure translation from `FairValueGapReactionFailureRule` to simulator-compatible soft invalidation.
  - Changed FVG midpoint invalidation from immediate midpoint break to post-entry reaction-window failure.
  - Added side-aware favorable-close checks and post-entry FVG lifecycle metadata in soft-invalidation exits.
  - Wired canonical and deprecated pattern strategy paths through the same FVG invalidation translator.
- Tests added or updated:
  - Updated invalidation contract tests for `fvg_reaction_failure_soft_invalidation_v1`.
  - Added LONG success/failure and SHORT symmetric exit simulation tests.
  - Updated CLI expansion test to assert FVG reaction-failure metadata.
- Tests run:
  - `pytest tests/backtesting/test_pattern_invalidation.py tests/patterns/test_pattern_exit_simulation.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_no_lookahead_contract.py`
  - `pytest tests/patterns tests/risk tests/backtesting tests/strategies`
  - `git diff --check`
- Codex self-review result:
  - Scope, offline-only safety, no-lookahead boundaries, metadata contracts, and ledger updates checked against `reviews/CODEX_SELF_REVIEW.md`.
- Known limitations:
  - FVG lifecycle metadata is derived from OHLC post-entry candles only; it does not infer intrabar order.
- Recommended next task:
  - Task 193 `ORDER_BLOCK_RETEST_MITIGATION_AND_CLUSTER_DETECTOR`.
