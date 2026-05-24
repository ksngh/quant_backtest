# Goal

Add market-regime and additional indicator features needed to judge whether pattern signals work under specific volatility, liquidity, trend, and mean-reversion conditions.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- Current pattern detectors rely mainly on ATR, volume ratio, displacement candle, and pivots.
- Several economic filters are placeholders or not implemented, including liquidity and spread filters.
- There is no canonical regime tag attached to signals/trades.

Read and inspect:

- `quant_bitcoin/indicators/atr.py`
- `quant_bitcoin/indicators/volume_ratio.py`
- `quant_bitcoin/indicators/displacement_candle.py`
- `quant_bitcoin/indicators/pivots.py`
- `quant_bitcoin/indicators/support_resistance_zone.py`
- `quant_bitcoin/indicators/swing_structure.py`
- `tasks/indicators/liquidity.md`
- `tasks/031_IMPLEMENT_VOLUME_RATIO.md`
- pattern detector configs and scoring functions

# Extracted Roles

- Owner role:
  - Indicator and regime-feature contract owner.
- Supporting roles:
  - Pattern detector role: may consume additive indicators later.
  - Metrics role: uses regime tags for attribution.
  - Data role: supplies OHLCV-derived features only unless a future task adds order book data.
- Forbidden roles:
  - No machine learning model training.
  - No live order book dependency for offline tests.
  - No strategy tuning beyond additive feature availability.

# Context

Code-level hints:

- Consider new modules under `quant_bitcoin/indicators/`:
  - `realized_volatility.py`
  - `trend_strength.py`
  - `liquidity_proxy.py`
  - `spread_proxy.py`
  - `mean_reversion.py`
  - `market_regime.py`
- Keep each indicator pure, deterministic, and offline.
- Add output columns similar to existing indicator modules: symbol, timestamp, value, status, is_valid.
- For regime tags, use percentile or threshold bands and avoid optimized thresholds in the first task.

Functional intent:

- The backtest should tag trades by market condition so research can separate alpha from regime exposure.

# Scope

- Implement a minimal regime tagging layer using existing ATR/volume/trend inputs.
- Add liquidity/spread proxy indicators if feasible using OHLCV only.
- Add trend-strength and mean-reversion indicators sufficient for attribution.
- Add tests and docs for each indicator contract.
- Do not force detectors to use new indicators unless explicitly within scope and additive.

# Out of Scope

- External macro data ingestion.
- Order book data ingestion.
- ML classifiers.
- Parameter optimization.

# Requirements

- Indicators must be pure functions over supplied candle data.
- Warm-up rows must be clearly invalid or unknown.
- Regime labels must be deterministic and documented.
- Indicators must not use future candles for current labels.
- Pattern detectors may record regime context but should not silently change entry behavior unless the task explicitly says so.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A candle stream can be enriched with volatility, volume/liquidity, trend, and mean-reversion regime tags.
- Regime labels are available for trade attribution.
- Warm-up and missing data behavior is tested.
- No look-ahead is introduced.

# Required Tests

## Unit Tests

- Add indicator tests for normal, warm-up, missing, and invalid inputs.
- Add no-lookahead tests for regime labels.
- Test output schema columns.

## Integration Tests

- Add a backtest fixture that attaches regime tags to executions or metadata without changing fills.

## Contract Tests

- Update `quant_bitcoin/indicators/__init__.py` exports if new public indicators are added.
- Document indicator output schemas.

## Safety Tests

- Confirm indicators do not call exchange APIs, use secrets, or place orders.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest tests/indicators tests/backtesting/test_strategy_engine.py
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
