# Task 231: FVG Liquidity Target Resolver and Take-Profit Policy

# Goal

Add a no-lookahead liquidity-target resolver so FVG retest trades can use prior swing highs/lows and optional structural zones as take-profit candidates instead of relying only on generic R-multiple targets.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - FVG risk/exit and structural target owner.
- Supporting roles:
  - Pivot/swing indicator role.
  - Pattern strategy role.
  - Backtest attribution role.
  - Test fixture role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The existing FVG risk planner accepts structural targets, but the current FVG strategy does not supply prior swing liquidity targets. The retest strategy needs explicit upside/downside liquidity objectives to evaluate whether a trade has enough room before entry.

# Scope

- Add a pure resolver such as `quant_bitcoin/backtesting/fvg_liquidity_targets.py` or an indicator-level structural target helper.
- Use confirmed pivots/swing structure available at event confirmation time to find directionally valid targets.
- For bullish FVG, select actionable targets above entry/reference price; for bearish FVG, select actionable targets below entry/reference price.
- Optionally include support/resistance zones or opposite FVG zones only when they are available without look-ahead and are clearly documented.
- Wire resolver output into `FairValueGapStrategy._risk_plan()` via `structural_targets`.
- Add metadata for target source, target price, distance, estimated R, and missing-target reason.

# Out of Scope

- No live liquidity/order-book data or bid-ask order-flow analysis.
- No guarantee that structural targets are profitable or predictive.
- No automatic target optimization or hindsight selection.
- No stop-mode changes; that is Task 232.

# Requirements

- Only confirmed pivots or structures visible at the event timestamp may be used.
- Resolver must return an empty target list with clear metadata when no actionable target exists.
- Risk planner must still provide R-multiple fallback targets when structural targets are absent unless a config explicitly requires liquidity targets.
- A config should support requiring at least one liquidity target and optionally requiring a minimum target R.
- Output diagnostics must separate structural target targets from R-multiple targets.
- Existing target semantics normalization must remain compatible.

# Status Tracking

## Execution Notes

- Assumption: liquidity targets are OHLCV confirmed-pivot structural targets, not order-book liquidity.
- Assumption: R-multiple fallback targets remain available unless a future task changes fallback policy.
- Blockers: none for Task 231.
- Safety: no live data, order-book subscription, network, exchange, order/account, key, `.env`, or live trading behavior was added.

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Added confirmed-pivot FVG liquidity target resolver with wrong-side, duplicate, no-lookahead, and minimum-R filtering.
- Added opt-in FVG risk config fields and strategy wiring to pass structural targets into risk plans.
- Added risk-plan liquidity target metadata wrapper and docs caveat.
- Verification:
  - `pytest tests/backtesting/test_fvg_liquidity_targets.py tests/patterns/test_fair_value_gap_risk_exit.py tests/backtesting/test_pattern_strategy_backtest.py tests/backtesting/test_pattern_postgres_runner_cli.py`

# Acceptance Criteria

- Bullish synthetic data resolves prior pivot highs above entry as targets.
- Bearish synthetic data resolves prior pivot lows below entry as targets.
- Targets on the wrong side of entry are excluded.
- FVG strategy risk plan receives structural targets and target metadata when enabled.
- No liquidity-target default behavior change occurs unless configured or retest preset enables it.

# Required Tests

## Unit Tests

- `tests/backtesting/test_fvg_liquidity_targets.py` covers bullish, bearish, no-target, wrong-side target, duplicate target, and minimum-R filtering.
- `tests/patterns/test_fair_value_gap_risk_exit.py` covers structural target injection into risk plans.
- No-lookahead pivot confirmation tests reuse or extend existing pivot fixtures.

## Integration Tests

- `tests/backtesting/test_pattern_strategy_backtest.py` or CLI tests confirm strategy output includes liquidity-target metadata.
- Risk-exit audit test groups outcomes by structural-target availability if diagnostics are added.

## Contract Tests

- Document liquidity target metadata and caveats: OHLCV/pivot-derived, not true order-book liquidity.
- Update API schema notes if serialized strategy output gains new target fields.

## Safety Tests

- No order-book subscription, Binance network call, or order/account endpoint import.
- No real trading behavior.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_fvg_liquidity_targets.py tests/patterns/test_fair_value_gap_risk_exit.py
pytest tests/backtesting/test_pattern_strategy_backtest.py tests/backtesting/test_pattern_postgres_runner_cli.py
pytest
git diff --check
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
