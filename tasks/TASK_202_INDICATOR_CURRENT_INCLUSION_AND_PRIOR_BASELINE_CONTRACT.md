# Task 202: INDICATOR_CURRENT_INCLUSION_AND_PRIOR_BASELINE_CONTRACT

# Goal

Document and test whether each indicator includes the current candle, and add prior-only options where timing semantics require them.

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

- ATR, volume ratio, and regime features currently use current candle values where applicable.
- For after-close signals, current-inclusive indicators are no-lookahead.
- For pre-close or intrabar entry assumptions, current-inclusive indicators can be unrealistic.

# Scope

- quant_bitcoin/indicators/atr.py
- quant_bitcoin/indicators/volume_ratio.py
- quant_bitcoin/indicators/market_regime.py
- quant_bitcoin/indicators/pivots.py
- docs/
- tests/indicators/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Add indicator timing metadata: current_candle_included, requires_closed_candle, warmup_period, confirmation_delay.
- Document timing contract for ATR, volume ratio, displacement candle, pivot, market regime, and RSI.
- Add prior-only baseline option where feasible, beginning with volume ratio and market regime percentile/zscore.
- Ensure default behavior remains backward compatible unless explicitly changed.

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
- Preserve existing indicator output columns by default; expose timing through helper metadata and opt-in config where feasible.
- Current-inclusive indicators are treated as safe for after-close signals using completed candles.
- Prior-only baseline starts with volume ratio and market-regime percentile/zscore as requested.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Indicator snapshots include or can expose timing metadata.
- Docs explain when current-inclusive calculations are safe.
- Tests assert warm-up and current-inclusion behavior.
- Pattern detectors record whether their indicator inputs require closed candles.

# Required Tests

## Unit Tests

- Unit: volume ratio current-inclusive baseline reproduces existing output.
- Unit: prior-only volume ratio differs as expected on spike candle.
- Unit: ATR warm-up metadata equals period.
- Unit: pivot confirmation delay equals right_window.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Adding metadata columns can affect consumers expecting exact column lists if not done compatibly.

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

- Files changed: `quant_bitcoin/indicators/atr.py`, `quant_bitcoin/indicators/volume_ratio.py`, `quant_bitcoin/indicators/market_regime.py`, `quant_bitcoin/indicators/pivots.py`, `quant_bitcoin/indicators/__init__.py`, `docs/26_INDICATOR_TIMING_CONTRACT.md`, `tests/indicators/test_atr.py`, `tests/indicators/test_volume_ratio.py`, `tests/indicators/test_market_regime.py`, `tests/indicators/test_pivots.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added indicator timing metadata helpers, opt-in volume-ratio prior-only baseline, opt-in market-regime prior-only percentile/z-score baseline, snapshot timing metadata flags, and a timing contract document for ATR, volume ratio, displacement candle, pivot, market regime, and RSI.
- Tests added or updated: ATR timing metadata/warm-up, volume current-inclusive compatibility plus prior-only spike behavior, market-regime prior-only percentile/z-score behavior, and pivot confirmation delay metadata.
- Tests run: `pytest tests/indicators/test_atr.py tests/indicators/test_volume_ratio.py tests/indicators/test_market_regime.py tests/indicators/test_pivots.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; output frame schemas remain backward compatible by default, prior-only behavior is opt-in, and no live trading/order endpoint/secret behavior was added.
- Known limitations: pattern event payloads do not yet carry a dedicated top-level indicator timing block; the timing contract is available through indicator helpers and docs while existing detectors continue to operate on completed candles.
- Recommended next task: Task 203 `VOLUME_RATIO_PRIOR_ONLY_AND_NOTIONAL_BASELINE`.
