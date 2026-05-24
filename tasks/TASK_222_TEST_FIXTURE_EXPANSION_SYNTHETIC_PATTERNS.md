# Task 222: TEST_FIXTURE_EXPANSION_SYNTHETIC_PATTERNS

# Goal

Build deterministic synthetic fixtures for all six patterns covering long/short, fill/no-fill, stop/target, invalid, weak, and no-lookahead cases.

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

- Many new tasks require stable pattern fixtures.
- FVG has broader deterministic coverage from prior tasks; non-FVG fixtures need expansion.
- Synthetic fixtures should make economic assumptions clear and avoid random data.

# Scope

- tests/fixtures/
- tests/patterns/
- tests/backtesting/
- tests/risk/
- quant_bitcoin/testing/  # create only if project already has or task justifies a test helper package

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Create fixture builders for FAIR_VALUE_GAP, ORDER_BLOCK, TRENDLINE_BREAK, CUP_AND_HANDLE, DIAMOND, and ADAM_AND_EVE.
- For each supported direction, include at least one valid event fixture and one invalid/no-event fixture.
- Include entry fill/no-fill cases for market and limit modes.
- Include stop-first, target-first, ambiguous, soft-invalidation, and time-stop exit cases.
- Include full-batch versus at-index no-lookahead parity fixtures.
- Document fixture intent in comments or fixture README.

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

Assumptions:
- This task is test infrastructure only. It should not change production detector, risk, strategy, backtest, persistence, backend, or frontend behavior.
- Existing deterministic candle snippets from pattern tests can be centralized into reusable fixture builders instead of inventing new stochastic datasets.
- Touched files are expected to be limited to `tests/fixtures/synthetic_patterns.py`, `tests/fixtures/README.md`, `tests/patterns/test_synthetic_pattern_fixtures.py`, and task/status/backlog/history ledgers.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- All six patterns have deterministic unit fixtures.
- At least FVG/OB/Trendline/Diamond cover both LONG and SHORT.
- Cup/A&E explicitly assert bullish-only support and unsupported inverse behavior.
- Fixtures are reusable across detector, action builder, risk, and engine tests.

# Required Tests

## Unit Tests

- Add unit tests appropriate to every changed pure function or data contract.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Meta-test: fixture builders produce sorted standard candles.
- No-lookahead parity tests.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Test suite size increases.
- Fixture helpers must not become hidden production dependencies.

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

# Completion Notes

Files changed:
- `tests/fixtures/__init__.py`
- `tests/fixtures/README.md`
- `tests/fixtures/synthetic_patterns.py`
- `tests/patterns/test_synthetic_pattern_fixtures.py`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_222_TEST_FIXTURE_EXPANSION_SYNTHETIC_PATTERNS.md`

Implementation summary:
- Added reusable deterministic synthetic fixture builders for FVG, Order Block, Trendline, Cup/Handle, Diamond, and Adam/Eve patterns.
- Covered bullish and bearish directions for FVG, Order Block, Trendline, and Diamond; documented Cup/Handle and Adam/Eve as bullish-only fixtures with unsupported inverse no-event candles.
- Added reusable entry case metadata for market fill, limit fill, and limit no-fill, plus exit case metadata for stop-first, target-first, ambiguous, soft-invalidation, and time-stop paths.
- Added fixture README documenting that fixtures are offline deterministic test data only.

Tests added or updated:
- Added `tests/patterns/test_synthetic_pattern_fixtures.py` for sorted standard candles, valid/invalid detection, no-lookahead at-index parity, entry fill/no-fill coverage, exit case matrix coverage, and supported direction coverage.

Tests run:
- `pytest tests/patterns/test_synthetic_pattern_fixtures.py`
- `pytest tests/patterns`
- `pytest tests/risk tests/backtesting`
- `pytest tests/strategies`
- `git diff --check`

Codex self-review result:
- Scope stayed within test fixtures/tests and ledger updates.
- No production detector, risk, strategy, backtest, backend, frontend, persistence, live trading, signed request, or secret handling behavior was changed.
- Fixtures are deterministic and use no network/exchange clients.

Known limitations:
- Fixtures are compact synthetic paths designed for unit/contract reuse, not empirical market scenarios.
- Cup/Handle and Adam/Eve inverse behavior is represented as unsupported inverse no-event fixtures because current detectors support bullish structures only.

Recommended next task:
- Task 223 `PERFORMANCE_REPORT_PATTERN_RESEARCH_NOTE_AUTOGENERATION`.
