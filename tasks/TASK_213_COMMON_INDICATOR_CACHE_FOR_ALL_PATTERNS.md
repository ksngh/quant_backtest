# Task 213: COMMON_INDICATOR_CACHE_FOR_ALL_PATTERNS

# Goal

Extend indicator caching beyond FVG/Order Block so all pattern detectors can share ATR, volume, displacement, pivot, and regime computations safely.

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

- FVG/Order Block have cached at-index helpers through fvg_detection_cache.py.
- Other patterns recompute ATR, volume, pivots, and displacement on rolling prefixes.
- A common cache can improve consistency and runtime for backtests and WFO.

# Scope

- quant_bitcoin/backtesting/fvg_detection_cache.py
- quant_bitcoin/patterns/*.py
- quant_bitcoin/strategies/patterns.py
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

- Rename or generalize IndicatorCache and PatternEvaluationContext so they are not FVG-specific.
- Cache ATR, volume ratio, displacement rows, pivot rows, and optional market regime rows.
- Provide at-index helpers for Trendline, Cup, Diamond, and Adam/Eve using cached indicators.
- Ensure cache uses only data available up to current_index for no-lookahead behavior.
- Preserve existing FVG/OB helper aliases if needed for compatibility.

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
- Preserve the existing `fvg_detection_cache.py` module and `IndicatorCache.for_fvg` alias for compatibility while generalizing the class behavior.
- Add cached at-index helpers as a shared execution path first; avoid changing detector algorithms beyond feeding already-visible cached indicator rows.
- Exact files expected: `quant_bitcoin/backtesting/fvg_detection_cache.py`, selected `quant_bitcoin/patterns/*.py` helper calls if needed, `quant_bitcoin/strategies/patterns.py`, and focused pattern/backtesting tests.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Generalized the FVG cache module around `PatternIndicatorCache` and `SharedPatternEvaluationContext` while preserving `IndicatorCache` and `PatternEvaluationContext` aliases plus `IndicatorCache.for_fvg`.
- Cached ATR, volume ratio, displacement rows, pivot rows, optional market-regime rows, and exposed visible-row helpers that clip to `current_index`.
- Added cached at-index helpers for Trendline, Cup and Handle, Diamond, and Adam/Eve; wired all six pattern strategies and canonical pattern runner construction through shared context when available.
- Stub/non-standard strategies in CLI tests keep the legacy prefix `evaluate()` fallback.
- No live trading, exchange order/account endpoint, credential, or `.env` behavior was introduced.

# Acceptance Criteria

- All six patterns can evaluate at-index using shared cache.
- Full-batch and cached at-index results match for event end_index current_index where expected.
- Runtime or at least redundant calculation count is reduced in tests/benchmarks.

# Required Tests

## Unit Tests

- Unit: pivot rows in cache respect confirmed_index <= current_index filter.

## Integration Tests

- Integration: strategy_for_pattern() can use shared context for each pattern.

## Contract Tests

- No-lookahead: cached at-index output does not change when future candles are appended.
- Regression: IndicatorCache.for_fvg alias still works if retained.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Refactor can touch many imports.
- Careless cache reuse could introduce future leakage, so tests must be strict.

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
- Scope stayed within the assigned cache, pattern strategy, runner wiring, compatibility export, and focused tests.
- The change remains offline/backtest-only and does not fetch data, sign requests, or place orders.
- No-lookahead behavior is protected by visible cache slices, confirmed pivot filtering, rolling-prefix parity tests, and future-append regression tests.
- Known limitation: non-FVG/OB cached helpers currently reuse the public at-index detector contracts over visible cached candles; deeper detector-internal reuse of cached pivot/displacement frames can be a later optimization if profiling justifies it.

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
