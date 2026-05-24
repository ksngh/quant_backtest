# Task 218: CHART_PATTERN_CANDIDATE_EXPLOSION_AND_OVERFIT_DIAGNOSTICS

# Goal

Quantify candidate generation complexity and overfit risk for Cup-and-Handle, Diamond, and Adam-and-Eve detectors.

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

- Cup-and-Handle, Diamond, and Adam/Eve build many candidate combinations per bar.
- Current configs have max_candidates_per_bar or max_candidate_windows_per_bar guards.
- High candidate counts can indicate chart pattern overfit and selection bias.

# Scope

- quant_bitcoin/patterns/cup_and_handle.py
- quant_bitcoin/patterns/diamond.py
- quant_bitcoin/patterns/adam_and_eve.py
- quant_bitcoin/backtesting/score_calibration.py
- tests/patterns/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Record candidate_count, evaluated_candidate_count, rejected_by_reason counts, selected_rank, and max guard hit status.
- Expose candidate diagnostics in event metadata or optional detector diagnostics output.
- Add overfit warnings when candidate count is high relative to pivot count or bars observed.
- Keep detector default output lightweight unless diagnostics are enabled.

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

Assumptions / notes:
- Keep detector output backward compatible by default; expose candidate diagnostics only when `enable_candidate_diagnostics` is enabled in detector config.
- Store diagnostics on emitted events as metadata-style dicts rather than changing strategy/backtest execution contracts.
- Record deterministic rejection buckets at candidate evaluation boundaries; detailed rejection semantics stay limited to detector-local rules.
- Exact files expected: Cup/Handle, Diamond, Adam/Eve detector modules and focused pattern tests.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added opt-in `enable_candidate_diagnostics` configs for Cup/Handle, Diamond, and Adam/Eve detectors.
- Added `chart_pattern_candidate_diagnostics_v1` event metadata with candidate counts, evaluated counts, deterministic rejection buckets, selected rank, max-guard status, density ratios, and overfit warnings.
- Preserved default detector output behavior by leaving `candidate_diagnostics` empty unless diagnostics are enabled.
- Added score-calibration aggregation under `chart_pattern_candidate_overfit_attribution_v1` and a `CHART_PATTERN_CANDIDATE_OVERFIT_RISK` flag for trades carrying guard/overfit diagnostics.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior were added.

# Acceptance Criteria

- Diagnostics-enabled run reports candidate counts for Cup, Diamond, Adam/Eve.
- Max candidate guard hit is visible.
- Rejected reason counts are deterministic.
- Default detector output remains backward compatible unless diagnostics config is enabled.

# Required Tests

## Unit Tests

- Unit: candidate_count increments for synthetic pivot records.
- Unit: max candidate guard hit recorded.
- Unit: rejection reason counts stable.

## Integration Tests

- Integration: overfit warning appears for high candidate density fixture.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Diagnostics mode may increase memory and CPU use.
- Adding rejection reasons can make detector internals more complex.

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

Self-review summary:
- Implemented only the assigned chart-pattern candidate diagnostics and score-calibration overfit attribution scope.
- Touched only the three assigned pattern detectors, score calibration, focused pattern tests, and one score-calibration test.
- Default detector behavior remains backward compatible; diagnostics require explicit config opt-in.
- Added no order execution, signed exchange request, secret handling, frontend, backend API, or database schema behavior.
- Verification passed with targeted and broad suites.

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

Verification run:

```bash
pytest tests/patterns/test_cup_and_handle.py tests/patterns/test_diamond.py tests/patterns/test_adam_and_eve.py tests/backtesting/test_score_calibration.py
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
