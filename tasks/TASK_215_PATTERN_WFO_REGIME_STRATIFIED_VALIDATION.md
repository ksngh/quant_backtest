# Task 215: PATTERN_WFO_REGIME_STRATIFIED_VALIDATION

# Goal

Extend pattern walk-forward validation to stratify results by market regime, session, liquidity, spread proxy, and entry mode.

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

- Task 182 extended WFO validation to pattern strategies.
- Market regime and tradability proxies exist, but validation should show whether edge is regime-dependent.
- This task supports deciding whether pattern thresholds should be regime-conditioned.

# Scope

- quant_bitcoin/backtesting/walk_forward.py
- quant_bitcoin/backtesting/performance_metrics.py
- quant_bitcoin/indicators/market_regime.py
- quant_bitcoin/cli/
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

- Add fold-level stratified attribution by market_regime, volatility_regime, liquidity_regime, spread_regime, session_tag, weekday_tag, and entry_mode.
- Report in-sample versus out-of-sample stability by pattern type.
- Include sample-size warnings for sparse strata.
- Allow user to require minimum trades per fold/stratum.
- Persist/report JSON-safe validation metadata.

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
- Extend existing offline `walk_forward.py` payloads instead of adding a new engine path.
- Use existing `market_regime.py` output when enabled by CLI/config; do not infer or fetch external data.
- Exact files expected: `quant_bitcoin/backtesting/walk_forward.py`, `quant_bitcoin/backtesting/walk_forward_cli.py`, focused `tests/backtesting/test_walk_forward.py`, and optional docs note if schema changes need explanation.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Extended `WalkForwardConfig` with opt-in regime stratification and minimum-trades-per-stratum controls.
- Added `walk_forward_regime_stratification_v1` fold diagnostics grouped by market regime, volatility, liquidity, spread, session, weekday, and entry mode.
- Added aggregate `walk_forward_regime_stratification_aggregate_v1` and pattern IS/OOS stability metadata.
- Wired `walk_forward_cli` flags for `--enable-regime-stratification` and `--min-trades-per-stratum`.
- Sparse strata are explicitly marked and warning messages are emitted.
- No live trading, exchange order/account endpoint, signed request, credential, or `.env` behavior was introduced.

# Acceptance Criteria

- Pattern WFO output contains regime/session stratification when regime tagging enabled.
- Sparse strata are flagged rather than overinterpreted.
- Fold stability metrics remain deterministic.

# Required Tests

## Unit Tests

- Unit: fold attribution groups by supplied regime metadata.
- Unit: sparse stratum warning triggered.

## Integration Tests

- Integration: pattern WFO fixture emits OOS expectancy by regime.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Reports become larger.
- Small datasets may show many low-confidence warnings.

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
- Scope stayed within offline WFO validation, CLI flags, and focused backtesting tests.
- Existing action builders and strategy engine remain authoritative; stratification is reporting metadata only.
- Market regime data is derived from already supplied OHLCV candles and is opt-in.
- Sparse groups are marked rather than interpreted as reliable edge.
- Known limitation: IS/OOS stability metadata currently reports pattern fold activity and completed OOS trade counts, not a separate in-sample backtest over train windows.

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
