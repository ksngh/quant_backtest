# Task 188: PATTERN_EXECUTION_PATH_UNIFICATION

# Goal

Unify canonical pattern backtest execution so all pattern strategies use the same fill-aware entry, risk-plan alignment, exit simulation, and metadata path.

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

- Current pattern execution can flow through the simple StrategyAction wrapper in quant_bitcoin/strategies/patterns.py or through the richer build_pattern_trade_actions() path.
- The richer path simulates actual fills, aligns the risk plan to fill price, emits exit actions, and carries risk metadata.
- The simple wrapper emits ENTER_LONG/ENTER_SHORT without requested_price and can leave execution price, risk_per_unit, and target semantics dependent on engine defaults.

# Scope

- quant_bitcoin/strategies/patterns.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- quant_bitcoin/patterns/entry_simulation.py
- quant_bitcoin/risk/exit_simulation.py
- quant_bitcoin/strategies/actions.py
- tests/backtesting/
- tests/strategies/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Define one canonical pattern execution path for backtests.
- All six pattern strategies must be able to emit actions through build_pattern_trade_actions() or a single equivalent canonical abstraction.
- Preserve existing strategy_for_pattern() public surface unless a task-local compatibility shim is explicitly documented.
- Pattern event metadata must preserve pattern_event_id, pattern_type, direction, pattern_status, pattern_score, score_components, entry_reference, stop_reference, target_reference, and risk_plan status.
- Entry, risk alignment, exit simulation, and partial exits must use the same path for FAIR_VALUE_GAP, ORDER_BLOCK, TRENDLINE_BREAK, CUP_AND_HANDLE, DIAMOND, and ADAM_AND_EVE.
- If a legacy wrapper path remains, it must be marked explicitly as legacy/simple-entry and must not be used by canonical pattern backtest runners.

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
- Work is limited to offline pattern strategy/backtest modules and tests.
- Existing public `strategy_for_pattern()` imports must remain usable.
- If current code already uses a canonical path in places, this task should harden/verify that contract rather than redesign public interfaces.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Raw pattern strategy outputs now explicitly identify the legacy/simple-entry path and declare that canonical expansion is required before execution/accounting.
- `build_pattern_trade_actions()` now marks fill-aware canonical actions and preserves event id/type/status/score/reference/risk metadata for all pattern types.
- `PatternStrategyBase.evaluate()` now uses the same raw signal helper as optimized `evaluate_at()` paths, removing duplicated wrapper logic.
- `quant_bitcoin.backtesting.__init__` lazily exports walk-forward helpers to avoid a risk/backtesting circular import during strategy imports.
- Tests added/updated: pattern strategy contract tests and canonical builder metadata tests.
- Tests run: `pytest tests/strategies/test_pattern_strategies.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_walk_forward.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review: scope respected, no live trading/order/account/API key behavior added, public `strategy_for_pattern()` surface preserved, canonical runner behavior remains offline simulation only.
- Known limitation: direct `strategy.evaluate()` remains a raw signal API for compatibility; canonical runners must expand it before accounting.
- Recommended next task: Task 189.

# Acceptance Criteria

- A canonical pattern action expansion path is documented in code comments or docs.
- All pattern strategy evaluations used by canonical backtests route through fill-aware risk alignment.
- No pattern produces executable entry actions when its risk plan is INVALID or SKIPPED.
- No take-profit action can be generated at a price that is non-actionable relative to actual fill price.
- Existing public imports remain usable or deprecation is explicit and covered by tests.

# Required Tests

## Unit Tests

- Unit: construct one deterministic event per pattern and assert canonical expansion emits an entry with fill-adjusted risk metadata.
- Unit: invalid risk plan returns SKIP only.
- Unit: FVG actual fill different from event entry_reference produces fill_adjusted_risk_per_unit.

## Integration Tests

- Integration: strategy_for_pattern() with each supported key uses canonical action expansion in a minimal backtest fixture.

## Contract Tests

- Regression: wrapper/simple path cannot silently bypass fill alignment in canonical runner.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Historical backtest results may change because execution price and targets become consistent.
- Trade counts may change if prior wrapper-only entries lacked exit simulation.
- Some tests that asserted bare ENTER actions may need to assert richer metadata instead.

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
