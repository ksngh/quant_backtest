# Task 201: MARKET_REGIME_CONDITIONED_PATTERN_THRESHOLDS

# Goal

Allow pattern thresholds and entry filters to vary by market regime while preserving deterministic defaults.

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

- Market regime is currently available as optional execution metadata and attribution context.
- Pattern detectors still use static thresholds for volume, ATR breakout distance, pivot windows, and minimum score.
- Crypto 1m behavior differs materially across high-vol trend, low-vol range, liquidity, spread, session, and weekend regimes.

# Scope

- quant_bitcoin/indicators/market_regime.py
- quant_bitcoin/strategies/patterns.py
- quant_bitcoin/backtesting/strategy_engine.py
- quant_bitcoin/cli/
- tests/indicators/test_market_regime.py
- tests/strategies/test_patterns.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Define a pattern_regime_thresholds_v1 config layer outside detector core or as optional detector config extension.
- Support threshold overrides for volume ratio, breakout_atr_multiplier, minimum_pattern_score, and optional entry blocking.
- Do not change default detector behavior when regime config is absent.
- Attach regime context and applied threshold metadata to events/actions.
- Add CLI/report metadata indicating whether regime-conditioned thresholds were enabled.

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
- Regime-conditioned thresholds are opt-in and must preserve detector defaults when absent.
- Threshold evaluation is research/backtest metadata only and does not introduce live execution behavior.
- `quant_bitcoin/cli/` does not exist in this repo; canonical CLI wiring lives in `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Static default outputs are unchanged when no regime config is supplied.
- A high-vol fixture can apply different breakout threshold than normal-vol fixture.
- Entry block can prevent trades in LOW liquidity or WIDE spread proxy regimes.
- Applied threshold values are visible in action metadata.

# Required Tests

## Unit Tests

- Unit: regime override applied for specified market_regime.
- Unit: missing regime falls back to default.
- Unit: low-liquidity block emits SKIP with reason.

## Integration Tests

- Integration: strategy_engine attribution preserves applied regime metadata.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Parameter space expands and can overfit if not validated OOS.
- Some historical trades may be filtered out.

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

- Files changed: `quant_bitcoin/indicators/market_regime.py`, `quant_bitcoin/indicators/__init__.py`, `quant_bitcoin/strategies/patterns.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`, `tests/indicators/test_market_regime.py`, `tests/strategies/test_pattern_strategies.py`, `tests/backtesting/test_strategy_engine.py`, `tests/backtesting/test_strategy_cli_persistence.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added opt-in `pattern_regime_thresholds_v1` default/regime-bucket thresholds, high-vol override support, low-liquidity/wide-spread entry blocking, strategy SKIP decisions, engine blocked-entry metadata, and CLI workflow/parameter reporting.
- Tests added or updated: market-regime threshold resolution/fallback/blocking unit tests, strategy SKIP test, engine applied-threshold/block tests, and CLI workflow metadata test.
- Tests run: `pytest tests/indicators/test_market_regime.py tests/strategies/test_pattern_strategies.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_cli_persistence.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; changes stayed in offline indicator/strategy/backtest/CLI metadata scope, default behavior remains disabled without config, and no live trading/order endpoint/secret behavior was added.
- Known limitations: regime thresholds increase research parameter space and can overfit without OOS validation; CLI currently exposes a conservative fixed set of regime threshold flags rather than arbitrary per-regime JSON config.
- Recommended next task: Task 202 `INDICATOR_CURRENT_INCLUSION_AND_PRIOR_BASELINE_CONTRACT`.
