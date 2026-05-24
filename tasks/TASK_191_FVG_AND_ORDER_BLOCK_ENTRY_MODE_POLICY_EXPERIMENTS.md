# Task 191: FVG_AND_ORDER_BLOCK_ENTRY_MODE_POLICY_EXPERIMENTS

# Goal

Separate FVG and Order Block economic entry hypotheses into explicit market-chase, midpoint-limit, boundary-limit, and retracement-limit experiment modes.

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

- FVG and Order Block economics are often zone-retest hypotheses, but market-on-confirmation-close can behave like momentum chase.
- Task 176 added FVG entry-mode experiments, but the policy should be generalized, enforced, and paired with Order Block.
- Entry mode should affect fill rate, bars waited, entry distance from zone, MAE/MFE, and expectancy attribution.

# Scope

- quant_bitcoin/patterns/fair_value_gap.py
- quant_bitcoin/patterns/order_block.py
- quant_bitcoin/patterns/entry_simulation.py
- quant_bitcoin/patterns/fair_value_gap_risk_exit.py
- quant_bitcoin/patterns/order_block_risk_exit.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- quant_bitcoin/cli/
- tests/patterns/
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

- Define canonical FVG entry modes: confirmation close, next open, zone midpoint limit, near boundary limit, far boundary limit, custom price.
- Define canonical Order Block entry modes: confirmation close, next open, zone midpoint limit, 0.618 retracement limit, zone boundary limit, custom price.
- Attach pattern-specific compatibility metadata for each mode.
- For each mode, record fill rate, missed trade count, bars waited, entry-reference distance, zone distance, MFE, MAE, average R, and expectancy when runner supports comparison.
- Default behavior must remain backward compatible unless the task explicitly changes a documented default.
- If default remains market confirmation, label it as CHASE/MOMENTUM variant, not generic FVG/OB entry.

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
- Backward-compatible default remains market-on-confirmation-close, but metadata must label it as a chase/momentum variant.
- Entry-mode comparison remains offline/research-only and must not add live trading, exchange order/account endpoints, signed requests, API keys, or `.env` behavior.
- Existing canonical builder should emit SKIP diagnostics for unsupported/invalid entry modes instead of raising during batch comparison.
- Scope is limited to FVG/Order Block entry mode metadata, price calculation, comparison reporting, and tests.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- FVG and OB entry-mode comparison can run deterministically on a small fixture.
- Unsupported entry modes emit SKIP diagnostics rather than raising hidden exceptions in batch backtests.
- Report metadata distinguishes retest-style entries from confirmation-close entries.
- No stale reference target can become a take-profit loss after different fill modes.

# Required Tests

## Unit Tests

- Unit: FVG midpoint limit fills only on retest candle.
- Unit: OB 0.618 limit computes side-aware price.
- Unit: boundary limit uses LONG lower/upper boundary semantics correctly.

## Integration Tests

- Integration: comparison runner returns fill and no-fill cases.

## Contract Tests

- Regression: market-on-confirmation close still works when explicitly selected.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Retest modes can reduce trade count and alter historical results.
- Comparison output may increase CLI/report complexity.

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
  - `quant_bitcoin/patterns/entry_simulation.py`
  - `quant_bitcoin/strategies/pattern_execution_policy.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `docs/api/API_CONTRACT.md`
  - `tests/patterns/test_entry_simulation.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tests/strategies/test_pattern_execution_policy.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_191_FVG_AND_ORDER_BLOCK_ENTRY_MODE_POLICY_EXPERIMENTS.md`
- Implementation summary:
  - Added explicit FVG near-boundary/far-boundary and Order Block 0.618 retracement entry modes.
  - Added pattern policy hypotheses that label market modes as chase/momentum and retest modes as separate research variants.
  - Extended entry policy metadata with entry style, hypothesis, zone distance, entry-reference distance, and boundary-variant details.
  - Added read-only pattern entry-mode comparison output for selected patterns while preserving legacy FVG comparison keys.
- Tests added or updated:
  - Added unit tests for side-aware FVG boundary prices and Order Block 0.618 price calculation.
  - Added builder metadata tests for FVG near-boundary and Order Block 0.618 modes.
  - Added policy matrix and CLI comparison tests for the new canonical experiment modes.
- Tests run:
  - `pytest tests/patterns/test_entry_simulation.py tests/backtesting/test_pattern_action_builder.py tests/strategies/test_pattern_execution_policy.py tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `pytest tests/patterns tests/risk tests/backtesting tests/strategies`
  - `git diff --check`
- Codex self-review result:
  - Scope, data contract, no-lookahead, offline-only safety, tests, and ledger updates checked against `reviews/CODEX_SELF_REVIEW.md`.
- Known limitations:
  - Custom-price comparison mode still requires caller-supplied research price to be economically meaningful; without it the mode produces invalid/no-fill diagnostics rather than an inferred price.
- Recommended next task:
  - Task 192 `FVG_LIFECYCLE_AND_SOFT_INVALIDATION_INTEGRATION`.
