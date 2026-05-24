# Goal

Wire currently implemented market-regime tagging, strict continuity validation, and backtest guardrails into the canonical strategy CLI so the features are usable in normal repository workflows.

# Source Requirement

Latest repo findings:
- `MarketRegimeConfig` and `calculate_market_regime()` exist.
- `StrategyEngineConfig` accepts `market_regime_by_timestamp`, `enforce_candle_continuity`, and `guardrails`.
- `PostgresCandleDataProvider` supports `enforce_continuity`.
- The canonical strategy CLI currently does not expose all of these controls.

# Extracted Roles

- Owner role:
  - Canonical backtest workflow owner.
- Supporting roles:
  - Indicator role: computes market regime.
  - Backtest engine role: consumes regime/guardrails/continuity config.
  - CLI/docs/frontend role: surfaces the selected settings and results.
- Forbidden roles:
  - No strategy tuning.
  - No live trading.
  - No frontend execution controls.

# Context

A feature that exists only in Python config is easy to miss. To analyze poor performance by regime or enforce clean data, canonical `quant-bitcoin-strategy-backtest` must expose these options.

# Scope

- Add CLI flags:
  - `--enforce-candle-continuity`,
  - `--enable-market-regime`,
  - market-regime window/threshold overrides as needed,
  - `--max-account-drawdown`,
  - `--max-consecutive-losses`,
  - `--max-daily-loss`.
- Pass `enforce_continuity` into `PostgresCandleDataProvider`.
- Compute market regime rows when enabled and pass `market_regime_by_timestamp` to `StrategyEngineConfig`.
- Build `BacktestGuardrailConfig` from CLI args and pass to engine.
- Persist selected settings in strategy parameters/run metadata.
- Add output warnings when continuity is disabled or market regime tagging is disabled.

# Out of Scope

- Do not make continuity mandatory by default if it would break existing partial-window runs.
- Do not alter detector definitions.
- Do not introduce live execution behavior.

# Requirements

- CLI arguments validate correctly.
- Regime attribution is no longer `UNKNOWN` when market regime tagging is enabled and warm-up is satisfied.
- Guardrail blocks appear as deterministic blocked executions.
- Continuity validation can reject a gap when enabled.
- Metadata clearly records enabled/disabled status.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- Continuity, regime, and guardrail options are opt-in so existing partial-window CLI workflows remain compatible.
- Market regime tags are computed from already-loaded candles and passed to the existing strategy engine only.
- Guardrails are deterministic backtest blocks, not live risk controls.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added canonical CLI flags for candle continuity, market-regime tagging, regime window/minimum trading value, and backtest-only guardrails.
- Passed continuity into `PostgresCandleDataProvider` and regime/guardrails into `StrategyEngineConfig`.
- Recorded workflow settings in strategy parameters/output metadata and added disabled-feature warnings by default.
- No live execution behavior was introduced.
- Next task: Task 180 `COST_PROFILE_PRESETS_AND_SENSITIVITY_REPORTING`.

# Acceptance Criteria

- CLI test covers continuity reject.
- CLI test covers max consecutive loss guardrail.
- CLI test covers market regime metadata present in executions/attribution.
- Existing no-regime default remains backwards-compatible.

# Required Tests

## Unit Tests

- Parser/config construction tests.
- Market regime timestamp mapping.

## Integration Tests

- CLI run with regime enabled.
- CLI run with guardrail enabled.
- Provider continuity validation.

## Contract Tests

- README/API docs updated for new CLI options and metadata.

## Safety Tests

- No live execution clients imported or invoked.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/indicators/test_market_regime.py tests/market_data/test_postgres_provider.py
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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
