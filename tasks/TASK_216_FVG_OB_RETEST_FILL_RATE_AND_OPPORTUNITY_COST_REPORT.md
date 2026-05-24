# Task 216: FVG_OB_RETEST_FILL_RATE_AND_OPPORTUNITY_COST_REPORT

# Goal

Add dedicated diagnostics for FVG and Order Block retest entries: fill rate, missed moves, opportunity cost, and adverse excursion.

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

- Retest entries may improve price/risk but miss trades.
- Market confirmation entries may fill every signal but chase after displacement.
- Research needs to quantify missed opportunities, not only filled trade PnL.

# Scope

- quant_bitcoin/backtesting/
- quant_bitcoin/patterns/fair_value_gap.py
- quant_bitcoin/patterns/order_block.py
- quant_bitcoin/patterns/entry_simulation.py
- tests/backtesting/
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

- For each FVG/OB signal, record whether each entry mode filled, bars waited, and max favorable move before fill/expiry.
- Measure opportunity cost for not-filled retest entries: post-signal MFE and whether market entry would have hit target.
- Measure adverse excursion after fill for retest versus market entries.
- Group diagnostics by pattern direction, zone size ATR, volume ratio, displacement strength, and regime when available.

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
- Implement reporting as offline diagnostics over already-built pattern actions and supplied OHLCV candles.
- Reuse entry simulation metadata (`ENTRY_FILLED`, `ENTRY_NOT_FILLED`, bars waited, entry mode, requested/fill prices) instead of changing fill behavior.
- Exact files expected: a focused backtesting diagnostics module, optional canonical runner metadata wiring, and focused tests under `tests/backtesting/`.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `fvg_ob_retest_opportunity_v1` diagnostics over canonical pattern actions and supplied OHLCV candles.
- The report separates filled entries, not-filled retest entries, missed moves, market-entry target-hit opportunity, bars waited, and adverse excursion after fill.
- Diagnostics are direction-aware for LONG and SHORT opportunity cost.
- Canonical pattern CLI output now includes the report in diagnostics and summary metadata.
- Grouping is provided by pattern direction, zone-size bucket, volume-ratio bucket, displacement-strength bucket, regime, and entry mode.
- No live trading, exchange order/account endpoint, signed request, credential, or `.env` behavior was introduced.

# Acceptance Criteria

- Report distinguishes missed trades from losing trades.
- Retest fill rate and average bars waited are available.
- Opportunity cost metrics are direction-aware.

# Required Tests

## Unit Tests

- Unit: retest not filled but price hits market-entry target records missed_move.
- Unit: retest filled after N bars records bars_waited.
- Unit: LONG/SHORT opportunity cost symmetry.

## Integration Tests

- Integration: comparison report includes FVG and OB sections.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Requires evaluating unfilled signals, increasing computation.

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
- Scope stayed within offline backtesting diagnostics, canonical runner metadata wiring, and focused tests.
- The diagnostic consumes existing action metadata and does not change entry-fill or execution behavior.
- Missed trades and losing filled trades are represented separately.
- No exchange API, live order, signed request, secret, or `.env` behavior was added.
- Known limitation: opportunity cost is computed over the supplied candle window after the signal timestamp; callers must supply the intended evaluation horizon.

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
