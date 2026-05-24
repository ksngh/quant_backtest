# Task 207: SHORT_ECONOMICS_FUNDING_BORROW_LIQUIDATION_RESEARCH_MODEL

# Goal

Add optional research-only short economics models for borrow cost, funding cost, maintenance margin, and liquidation diagnostics without enabling live trading.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P3**

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

- Current short simulation explicitly excludes borrow fees, futures funding, maintenance margin, and liquidation.
- Short direction pattern results are therefore simulation-only and not live-tradable economics.
- Research users need to understand whether short alpha survives realistic carrying and liquidation assumptions.

# Scope

- quant_bitcoin/backtesting/sizing.py
- quant_bitcoin/backtesting/strategy_engine.py
- quant_bitcoin/backtesting/strategy_models.py
- tests/backtesting/test_strategy_engine.py
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

- Add optional ShortEconomicsConfig for borrow_fee_bps_per_day, funding_bps_per_interval, maintenance_margin_rate, and liquidation_buffer_rate.
- Default must preserve current behavior and continue to warn unsupported economics when config is disabled.
- Compute carrying costs on open short exposure over time when enabled.
- Add liquidation diagnostics without enabling exchange execution.
- Record modeled/unmodeled short economics in summary metadata.

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
- Short economics remain research-only metadata and offline accounting; they do not open live margin/futures capability or exchange endpoints.
- Default `ShortEconomicsConfig` is disabled and must preserve existing short results and warning semantics.
- Carrying costs are charged only while a short position is open, based on supplied candle timestamps/interval settings and current mark price.
- Liquidation is diagnostic-only (`would_liquidate`) and must not auto-close or mutate strategy actions.
- Exact files expected: `quant_bitcoin/backtesting/sizing.py`, `quant_bitcoin/backtesting/strategy_models.py`, `quant_bitcoin/backtesting/strategy_engine.py`, backtesting tests, and docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Disabled config preserves current short results.
- Enabled borrow/funding costs reduce short net PnL deterministically.
- Maintenance/liquidation diagnostics flag would-liquidate cases in fixtures.
- No live trading or exchange endpoint behavior is added.

# Required Tests

## Unit Tests

- Unit: borrow fee accrues over multiple candles.
- Unit: funding fee applies by interval.
- Unit: would-liquidate metadata appears when adverse move exceeds threshold.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.
- Safety: no exchange client/order endpoint import is introduced.

# Side Effects / Risks

- Short result semantics become more complex.
- Backtest runtime may increase if per-candle carrying accrual is computed.

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

- Files changed: `quant_bitcoin/backtesting/sizing.py`, `quant_bitcoin/backtesting/strategy_models.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `quant_bitcoin/backtesting/__init__.py`, `tests/backtesting/test_strategy_engine.py`, `README.md`, `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`, `docs/api/API_CONTRACT.md`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added optional `ShortEconomicsConfig`, modeled research-only short borrow/funding carrying-cost deductions while positions are open, preserved disabled/default short economics semantics, added diagnostic-only short liquidation metadata and equity-point flags, and documented that this is not live margin/futures execution.
- Tests added or updated: disabled-config compatibility, multi-candle borrow accrual, per-interval funding accrual, diagnostic-only liquidation threshold detection, and default short-accounting regression coverage.
- Tests run: `pytest tests/backtesting/test_strategy_engine.py`; `pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_engine_accounting.py`; `pytest tests/backtesting`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; implementation stayed within offline backtesting/research accounting, added tests/docs, and introduced no exchange clients, signed requests, credentials, or live order behavior.
- Known limitations: funding is a deterministic per-candle interval assumption, borrow uses supplied candle timing/intervals and mark price, and liquidation diagnostics do not simulate real exchange margin rules or auto-liquidation execution.
- Recommended next task: Task 208 `POSITION_SIZING_FILL_ADJUSTED_RISK_CONTRACT`.
