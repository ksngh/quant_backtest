# Task 209: GUARDRAIL_OPEN_POSITION_KILL_SWITCH_AND_EXPOSURE_CAPS

# Goal

Extend backtest-only guardrails from entry blocking to optional open-position liquidation and exposure caps.

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

- Current guardrails block new entries on max drawdown, max consecutive losses, or max daily loss.
- They do not force close existing positions.
- Production-style risk needs kill-switch semantics even in research simulation.

# Scope

- quant_bitcoin/backtesting/sizing.py
- quant_bitcoin/backtesting/strategy_engine.py
- quant_bitcoin/strategies/actions.py
- tests/backtesting/test_strategy_engine.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Add guardrail options: close_open_position_on_breach, max_position_notional, max_symbol_notional, max_leverage_simulated.
- When close_open_position_on_breach is enabled, generate or apply deterministic forced exit at current candle close/effective price.
- Record guardrail breach reason and forced-exit metadata.
- Keep default behavior backward compatible: entry-only blocking unless explicitly enabled.
- Do not add live trading behavior.

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
- Forced exits are strategy-engine simulated exits only; they reuse normal long/short exit accounting and do not create live order behavior.
- Default remains entry-only guardrails unless `close_open_position_on_breach=True`.
- `max_position_notional`, `max_symbol_notional`, and `max_leverage_simulated` apply to new entry notional before affordability checks and use the existing insufficient-funds policy for block vs resize behavior.
- Exact files expected: `quant_bitcoin/backtesting/sizing.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `quant_bitcoin/strategies/actions.py`, and `tests/backtesting/test_strategy_engine.py`.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Entry-only guardrail behavior remains default.
- Forced liquidation mode closes open long and short positions in fixtures.
- Exposure cap blocks or resizes new entries deterministically.
- Metadata distinguishes guardrail block from strategy exit.

# Required Tests

## Unit Tests

- Unit: max drawdown breach blocks new entry.
- Unit: max drawdown breach closes open position when configured.
- Unit: max notional cap blocks oversized action.
- Unit: short forced close uses correct BUY side.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Forced exits can change exit reason attribution and performance metrics.
- Exposure cap may conflict with existing affordability resize behavior.

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

- Files changed: `quant_bitcoin/backtesting/sizing.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `tests/backtesting/test_strategy_engine.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: extended `BacktestGuardrailConfig` with opt-in forced open-position exits and entry exposure caps, made forced exits reuse normal long/short accounting at current candle close, added guardrail metadata distinguishing forced exits from strategy exits, and added deterministic cap block/resize behavior for entry notional.
- Tests added or updated: default entry-only behavior, forced long close, forced short close with BUY side, max-position-notional block, and max-symbol-notional resize.
- Tests run: `pytest tests/backtesting/test_strategy_engine.py`; `pytest tests/backtesting`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; behavior remains backtest-only, default-compatible, and no exchange clients/order endpoints/secrets/live execution behavior were added.
- Known limitations: symbol-level notional cap is single-symbol within the current engine; portfolio-wide multi-symbol aggregation is not modeled.
- Recommended next task: Task 210 `RISK_SOFT_INVALIDATION_AUTOWIRING`.
