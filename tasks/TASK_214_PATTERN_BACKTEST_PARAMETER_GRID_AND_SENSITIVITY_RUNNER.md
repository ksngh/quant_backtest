# Task 214: PATTERN_BACKTEST_PARAMETER_GRID_AND_SENSITIVITY_RUNNER

# Goal

Add an offline parameter-grid runner for pattern configs, entry modes, cost profiles, and risk settings with deterministic sensitivity outputs.

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

- Many proposed improvements require comparing thresholds and modes rather than trusting one default.
- Pattern detector thresholds include ATR multipliers, volume ratios, pivot windows, candidate counts, entry modes, stop modes, and cost profiles.
- Sensitivity analysis helps identify overfit parameters and robust ranges.

# Scope

- quant_bitcoin/backtesting/
- quant_bitcoin/cli/
- tests/backtesting/
- tests/cli/
- docs/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Add a grid runner that can vary selected pattern config fields, risk config fields, entry modes, cost profiles, and sizing modes.
- Use deterministic seeds/order and JSON-safe output.
- Report trade count, fill rate, expectancy, average R, hit rate, profit factor, max drawdown, cost ratio, and no-fill count.
- Support dry-run validation of parameter grid without executing full backtest.
- Warn on combinatorial explosion and enforce max combinations.

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
- Implement an offline, deterministic utility module and lightweight CLI wrapper without changing live/execution boundaries.
- Prefer reusing the canonical pattern runner/building blocks for actual backtests; keep dry-run grid validation independent and fast.
- Exact files expected: new or existing `quant_bitcoin/backtesting/` grid runner module, `quant_bitcoin/cli/` entry point if present or a backtesting CLI module if project conventions require, focused `tests/backtesting/`, optional `tests/cli/`, and a docs note.
- No live trading, exchange order/account endpoints, signed requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `pattern_parameter_grid_v1`, a deterministic offline parameter-grid runner with stable parameter hashes, dry-run validation, max-combination guardrails, and large-grid warnings.
- Added a local CSV CLI for the grid runner with repeated `--param path=value1,value2` inputs and clear invalid-path errors.
- Supported detector/risk config fields, entry mode/settings, cost profiles, sizing mode/value, and pattern entry filters.
- Executed rows report trade count, candidate count, fill rate, expectancy, average R, hit rate, profit factor, max drawdown, cost ratio, and no-fill count.
- Added docs for supported parameter paths, CLI usage, metrics, and safety boundaries.
- No live trading, exchange order/account endpoint, signed request, credential, or `.env` behavior was introduced.

# Acceptance Criteria

- Grid runner can run a small FVG and Trendline fixture.
- Output includes parameter set identity/hash.
- Max combination guard prevents accidental huge runs.
- Results are stable across repeated runs.

# Required Tests

## Unit Tests

- Unit: parameter grid expansion respects max combinations.
- Unit: config hash stable for same parameter set.

## Integration Tests

- Integration: two-mode FVG entry comparison returns two rows.

## Contract Tests

- CLI: invalid parameter path fails clearly.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Large grids can be slow if guardrails are not enforced.

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
- Scope stayed within offline backtesting utility, CLI, docs, and focused tests.
- The runner reuses canonical pattern action expansion and strategy engine behavior instead of introducing a parallel accounting model.
- Max-combination and dry-run paths are deterministic and JSON-safe.
- Safety boundary is unchanged: no exchange data fetch, signed request, order/account endpoint, API key, or `.env` mutation.
- Known limitation: CLI parameter values are simple scalar comma-separated values; nested dataclass fields and structured list parameters are intentionally not supported in this first grid runner.

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
