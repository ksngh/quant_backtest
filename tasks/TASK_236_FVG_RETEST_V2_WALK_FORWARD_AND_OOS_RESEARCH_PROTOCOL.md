# Task 236: FVG Retest V2 Walk-Forward and Out-of-Sample Research Protocol

# Goal

Define and implement a reproducible research protocol for evaluating FVG v2 across walk-forward and out-of-sample windows without promoting the strategy based on narrow in-sample tuning.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Pattern research validation owner for FVG v2 walk-forward and OOS evaluation.
- Supporting roles:
  - Walk-forward validation role.
  - Parameter-grid role.
  - Performance metrics role.
  - Report generation role.
  - Documentation role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

FVG v2 introduces several configurable axes. Without a predeclared validation protocol, results can become overfit. The project already has pattern WFO and parameter-grid infrastructure; this task applies those tools specifically to the FVG v2 candidate.

# Scope

- Create a documented FVG v2 research protocol with train/validation/test/holdout split definitions.
- Use existing walk-forward validation and parameter-grid tools where possible rather than adding a new optimizer.
- Record all attempted parameter combinations, including losing variants.
- Add aggregate reporting by timeframe trend alignment, Fibonacci confluence, liquidity-target availability, entry trigger, stop mode, regime, session, and cost profile.
- Add promotion/rejection criteria for FVG v2 as a research candidate only.
- Generate or enable a markdown/JSON research note summarizing evidence and limitations.

# Out of Scope

- No live, paper, or testnet trading promotion.
- No automatic best-parameter deployment.
- No hidden post-hoc retuning after weak OOS results.
- No new historical data download unless separately assigned as a data task.

# Requirements

- Research protocol must require realistic transaction cost/slippage settings or explicitly flag zero-cost results as debugging-only.
- Walk-forward output must include per-fold and aggregate metrics, sparse-window warnings, drawdown, hit rate, expectancy, average R, MFE/MAE, and no-fill rates.
- Parameter ranges must be predeclared in docs or config fixtures before execution.
- OOS failures must be recorded; do not remove poor-performing folds from the report.
- Results must identify whether weakness comes from no-fill retests, poor follow-through, trend filter overblocking, liquidity target scarcity, or cost drag.
- Research output must remain reproducible with dataset identity and config hash metadata.

# Status Tracking

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

# Acceptance Criteria

- A runnable FVG v2 WFO/OOS command or documented command set exists.
- A deterministic fixture/smoke test verifies research output schema without large data dependency.
- Protocol documentation states promotion and rejection criteria.
- All attempted variants are logged in output or report metadata.
- No strategy is marked live/paper approved as part of this task.

# Required Tests

## Unit Tests

- Parameter declaration validation tests reject missing ranges, invalid ranges, and excessive combinations.
- Research report tests cover FVG v2 fields and missing diagnostics.
- Promotion/rejection summary helper tests if a helper is added.

## Integration Tests

- Walk-forward smoke test over deterministic fixture data.
- Parameter-grid plus WFO integration test with small bounded combinations.
- Research note generation test for FVG v2 candidate.

## Contract Tests

- Add or update `docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md` or equivalent.
- Document that FVG v2 remains research/backtest-only after protocol implementation.

## Safety Tests

- No live trading approval, no exchange order calls, no signed requests.
- Reports must include experimental/research-only caveat.

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
pytest tests/backtesting/test_walk_forward.py tests/backtesting/test_pattern_parameter_grid.py tests/backtesting/test_performance_metrics.py
pytest tests/backtesting/test_pattern_postgres_runner_cli.py
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

# Completion Notes

Completed on 2026-05-27.

Files changed:

- `quant_bitcoin/backtesting/fvg_retest_v2_research_protocol.py`
- `quant_bitcoin/backtesting/walk_forward.py`
- `tests/backtesting/test_fvg_retest_v2_research_protocol.py`
- `tests/backtesting/test_walk_forward.py`
- `tests/strategies/test_pattern_strategies.py`
- `docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md`
- `docs/24_WALK_FORWARD_VALIDATION_SCHEMA.md`
- `docs/27_PATTERN_PARAMETER_GRID.md`
- `README.md`

Implementation summary:

- Added FVG retest v2 parameter-declaration validation, default predeclared grid, WFO research protocol runner, JSON/markdown research note, dataset/config hashes, and research-only promotion/rejection summaries.
- Extended WFO regime stratification with FVG v2 reporting dimensions for entry trigger, trend alignment, Fibonacci confluence, liquidity target availability, and stop mode.
- Added timing diagnostics to fold diagnostics so MFE/MAE evidence can flow into protocol summaries.
- Documented the FVG v2 train/validation/test/holdout protocol, command set, required reporting dimensions, and rejection/promotion rules.

Tests added or updated:

- Added FVG v2 protocol validation and bounded WFO smoke tests.
- Updated WFO stratification tests for FVG v2 dimensions.
- Updated a strategy test double to accept the expanded FVG risk-plan keyword contract.

Tests run:

- `pytest tests/backtesting/test_fvg_retest_v2_research_protocol.py tests/backtesting/test_walk_forward.py tests/backtesting/test_pattern_parameter_grid.py tests/backtesting/test_performance_metrics.py` (passed)
- `pytest tests/backtesting/test_pattern_postgres_runner_cli.py` (passed)
- `pytest tests/strategies/test_pattern_strategies.py::test_pattern_strategy_raw_signal_is_explicit_legacy_input_for_canonical_expansion` (passed)
- `pytest` (passed: 1130 passed, 1 skipped)
- `rg "order endpoint|account endpoint|api_key|credential|\\.env|signed request|live trading|place orders" quant_bitcoin/backtesting/fvg_retest_v2_research_protocol.py docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md -n` (reviewed; safety-boundary text only)
- `git diff --check` (passed)

Codex self-review result:

- Scope respected: FVG v2 research validation/reporting only.
- No live, paper, testnet, exchange order/account, signed request, API key, or `.env` behavior added.
- Existing WFO/grid tools were reused; no automatic best-parameter deployment or hidden optimizer was introduced.
- All attempted variants are retained in protocol output.

Known limitations:

- The protocol runner is code-level JSON/markdown output plus documented command set; no dedicated standalone CLI wrapper was added.
- Real dataset holdout execution remains a future owner-run research activity.

Recommended next task:

- Task 237 `FVG_RETEST_V2_DOCUMENTATION_STATUS_HISTORY_BACKLOG_RECONCILIATION`.
