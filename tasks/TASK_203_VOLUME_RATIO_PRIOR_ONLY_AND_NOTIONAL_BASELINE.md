# Task 203: VOLUME_RATIO_PRIOR_ONLY_AND_NOTIONAL_BASELINE

# Goal

Add prior-only and quote-notional-aware volume ratio baselines for better breakout/displacement confirmation.

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

- Current volume ratio rolling baseline includes the current candle.
- A spike candle can raise its own baseline and reduce the measured spike ratio.
- Crypto data often has quote_volume, which can be a better activity proxy than base volume.

# Scope

- quant_bitcoin/indicators/volume_ratio.py
- quant_bitcoin/patterns/*.py
- tests/indicators/test_volume_ratio.py
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

- Add baseline_mode: CURRENT_INCLUSIVE and PRIOR_ONLY.
- Add volume_input_mode: BASE_VOLUME, QUOTE_VOLUME_IF_AVAILABLE, TRADING_VALUE.
- Preserve current default behavior unless task explicitly updates defaults.
- Expose baseline_mode and volume_input_mode in output columns or metadata.
- Allow pattern configs to pass volume ratio config variants.

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
- Preserve existing current-inclusive base-volume behavior by default.
- Implement `baseline_mode` and `volume_input_mode` as explicit config enums/strings while retaining the existing boolean compatibility path from Task 202.
- Pattern detector changes are limited to passing/recording volume ratio configuration for existing offline research logic.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Prior-only volume ratio on spike candle is higher than current-inclusive in a deterministic fixture.
- Quote volume is used when available and configured.
- Pattern detectors continue to work with old and new volume ratio configs.

# Required Tests

## Unit Tests

- Unit: current-inclusive backward compatibility.
- Unit: prior-only baseline excludes current candle.
- Unit: quote volume fallback behavior.

## Integration Tests

- Integration: FVG displacement volume confirmation with prior-only config.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Volume threshold pass rates may increase under prior-only mode.
- Historical score distributions will change under new configs.

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

- Files changed: `quant_bitcoin/indicators/volume_ratio.py`, `quant_bitcoin/indicators/__init__.py`, `quant_bitcoin/patterns/fair_value_gap.py`, `quant_bitcoin/patterns/order_block.py`, `quant_bitcoin/patterns/trendline_break.py`, `quant_bitcoin/patterns/cup_and_handle.py`, `quant_bitcoin/patterns/diamond.py`, `quant_bitcoin/patterns/adam_and_eve.py`, `tests/indicators/test_volume_ratio.py`, `tests/patterns/test_fair_value_gap.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added explicit `VolumeRatioBaselineMode` and `VolumeInputMode`, preserved default current-inclusive base-volume behavior, kept `baseline_includes_current` as a compatibility override, added DataFrame/snapshot metadata for selected baseline/input modes, added quote-volume fallback and trading-value inputs, and passed full normalized pattern candles into volume-ratio calculation so pattern configs can use quote/notional variants.
- Tests added or updated: volume-ratio prior-only mode compatibility, quote-volume selection/fallback, trading-value calculation, metadata schema checks, invalid mode validation, snapshot metadata, and FVG prior-only/quote-volume integration coverage.
- Tests run: `pytest tests/indicators/test_volume_ratio.py tests/patterns/test_fair_value_gap.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; scope stayed within volume-ratio indicator and pattern detector integration, offline-only behavior was preserved, no secrets/live trading/order endpoints were added, and tests cover the new modes plus default compatibility.
- Known limitations: pattern event payloads still expose the resulting scalar `volume_ratio`; the selected volume input/baseline metadata is available on indicator outputs/snapshots rather than copied onto every pattern event.
- Recommended next task: Task 204 `ATR_TIMING_AND_REGIME_THRESHOLD_CALIBRATION`.
