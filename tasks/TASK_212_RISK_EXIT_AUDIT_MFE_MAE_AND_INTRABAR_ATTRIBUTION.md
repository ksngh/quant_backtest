# Task 212: RISK_EXIT_AUDIT_MFE_MAE_AND_INTRABAR_ATTRIBUTION

# Goal

Expand risk audit to attribute realized outcomes to target source, stop movement, intrabar ambiguity, MFE/MAE, and time/soft invalidation dominance.

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

- Risk audit and timing diagnostics exist, but deeper attribution is needed to understand whether poor runs come from entry chasing, stop tightness, false breakouts, or cost drag.
- Intrabar ambiguity metadata is emitted in exit simulation.
- MFE/MAE metrics help diagnose whether targets/stops are structurally reasonable.

# Scope

- quant_bitcoin/backtesting/risk_exit_audit.py
- quant_bitcoin/backtesting/timing_diagnostics.py
- quant_bitcoin/risk/exit_simulation.py
- quant_bitcoin/backtesting/strategy_engine.py
- tests/backtesting/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Group exit outcomes by pattern_type, direction, entry_mode, target_source, exit_reason, and intrabar_policy.
- Report MFE/MAE before exit and realized R by group.
- Report ambiguous_stop_target count and its PnL contribution.
- Report stop movement due to break-even/trailing where metadata permits.
- Flag stop-dominant, time-stop-dominant, soft-invalidation-dominant, and cost-dominant patterns.

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
- Extend existing offline diagnostics only; do not change fills, order execution, or strategy behavior.
- Prefer existing execution metadata and persisted OHLC path data; legacy rows without path data should emit partial diagnostics instead of failing.
- Exact files expected: `quant_bitcoin/backtesting/risk_exit_audit.py`, `quant_bitcoin/backtesting/timing_diagnostics.py`, `quant_bitcoin/risk/exit_simulation.py`, `quant_bitcoin/backtesting/strategy_engine.py`, and focused `tests/backtesting/`.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Risk audit identifies dominant exit reasons and target source quality.
- Ambiguous intrabar decisions are counted.
- MFE/MAE fields are present for completed lifecycle trades where candle path data exists.

# Required Tests

## Unit Tests

- Unit: target-source grouping works for R_MULTIPLE and MEASURED exits.
- Unit: ambiguous policy metadata counted.
- Unit: stop-dominant synthetic run gets diagnostic flag.

## Integration Tests

- Integration: strategy_engine summary contains expanded risk_exit_audit.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Metadata report size increases.
- Legacy runs without OHLC path may have partial/fallback diagnostics.

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

- Files changed: `quant_bitcoin/backtesting/risk_exit_audit.py`, `quant_bitcoin/backtesting/timing_diagnostics.py`, `quant_bitcoin/risk/exit_simulation.py`, `tests/backtesting/test_risk_exit_audit.py`, `tests/backtesting/test_timing_diagnostics.py`, `tests/backtesting/test_strategy_engine.py`, and state ledgers.
- Implementation summary: expanded risk-exit audit with grouped outcome attribution by pattern/direction/entry mode/target source/exit reason/intrabar policy, target-source quality, MFE/MAE path attribution from timing diagnostics, ambiguous intrabar PnL contribution, stop-movement metadata, and cost-dominance flags.
- Tests added or updated: target-source grouping, ambiguous intrabar counting, stop/cost dominance, timing attribution metadata, and strategy-engine summary integration coverage.
- Tests run: `pytest tests/backtesting/test_risk_exit_audit.py tests/backtesting/test_timing_diagnostics.py tests/backtesting/test_strategy_engine.py`; `pytest tests/patterns tests/risk tests/backtesting`; `pytest tests/strategies`; `git diff --check`.
- Codex self-review result: scope respected, offline diagnostics only, no live trading/exchange calls/secrets, no strategy behavior changes, and verification passed.
- Known limitations: MFE/MAE group attribution depends on saved timing diagnostics; legacy rows without matched path data report partial/fallback attribution.
- Recommended next task: Task 213 `COMMON_INDICATOR_CACHE_FOR_ALL_PATTERNS`.
