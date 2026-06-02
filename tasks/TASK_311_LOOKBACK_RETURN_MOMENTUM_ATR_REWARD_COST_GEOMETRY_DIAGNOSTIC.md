# Task 311: LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC

# Goal

Test whether `LOOKBACK_RETURN_MOMENTUM` can produce cost-feasible entries when stop distance stays at `1 ATR` but reward distance is raised above cost using asymmetric ATR take-profit multiples and a minimum ATR volatility floor.

# Source Requirement

Owner request after Task 309:

> 아 그럼 reward를 cost 보다 높이려면 어떻게 해야해

Follow-up approval:

> 어어 그렇게 해주라

Interpreted as: create and then execute a bounded experiment using `1 ATR` stop, `2-3 ATR` take-profit candidates, and a minimum ATR bps filter.

# Extracted Roles

- Owner role: approves testing asymmetric ATR reward/risk and ATR volatility floor to make planned reward exceed costs.
- Supporting roles:
  - Strategy document maintainer: updates `docs/strategy/lookback_return_momentum_v1.md` before implementation or backtest execution.
  - Strategy implementer: adds any missing CLI/config/filter support for asymmetric ATR reward and minimum ATR bps filtering.
  - Backtest runner: executes only the bounded validation grid defined in this task.
  - Report writer: saves a task report under `reports/` explaining cost feasibility and results.
  - Test maintainer: adds or updates focused tests for the ATR reward/cost filter behavior and metadata.
- Forbidden roles:
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend API implementer.
  - Parameter optimizer outside the predeclared grid.

# Context

Task 309 replaced fixed entry-price percentage risk distance with ATR-based distance. The default geometry became `1 ATR` stop and `1 ATR` take-profit. Under the preserved cost-aware gate, every candidate was blocked because a symmetric 1:1 gross reward/risk cannot satisfy `min_net_rr=1.0` after positive estimated round-trip cost:

```text
net_rr = (gross_reward_bps - round_trip_cost_bps) / (gross_risk_bps + round_trip_cost_bps)
```

When `gross_reward_bps == gross_risk_bps`, any positive cost makes `net_rr < 1.0`.

This task changes the experiment geometry, not the signal definition:

- keep stop distance at `1 ATR`;
- test take-profit distance at `2 ATR`, `2.5 ATR`, and `3 ATR`;
- add a minimum ATR bps filter so extremely small ATR regimes do not create trades whose planned reward is too small to clear cost.

# Scope

- Read required state files and this task before any implementation.
- Read `docs/strategy/lookback_return_momentum_v1.md` after this task and before strategy/code/backtest work.
- Update `docs/strategy/lookback_return_momentum_v1.md` before code/backtest execution to document:
  - asymmetric ATR reward/risk diagnostic;
  - stop fixed at `1 ATR`;
  - take-profit candidates `2.0`, `2.5`, and `3.0 ATR`;
  - minimum ATR bps filter;
  - expected cost-feasibility formula;
  - no post-result tuning boundary.
- Implement only missing support required by this task:
  - CLI/config support for `--minimum-atr-bps` if absent;
  - entry rejection when `ATR_at_entry / entry_price * 10000 < minimum_atr_bps`;
  - metadata for `atr_bps`, `minimum_atr_bps`, and skip reason, preferably `ATR_TOO_SMALL_FOR_COST`.
- Preserve Task 305/309 cost-aware entry gate for the primary validation:
  - `--enable-cost-aware-entry-filter`;
  - `--min-net-reward-bps 0.0`;
  - `--min-net-rr 1.0`;
  - `--liquidity-role TAKER`;
  - `--cost-profile conservative_crypto_1m`.
- Run a bounded validation over the same Task 305/308/309 candle window:
  - symbol: `BTCUSDT`;
  - intervals: `1m`, `5m`, `15m`;
  - time window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`;
  - runner end-time convention must be recorded exactly.
- Use the lowest Task 308 threshold per interval to focus this task on reward/cost geometry rather than signal-frequency search:
  - `1m`: `lookback_bars=20`, `holding_bars=5`, `entry_threshold=0.0004`;
  - `5m`: `lookback_bars=12`, `holding_bars=6`, `entry_threshold=0.0006`;
  - `15m`: `lookback_bars=8`, `holding_bars=4`, `entry_threshold=0.0008`.
- Predeclared validation grid:
  - `stop_loss_atr_multiple=1.0` fixed;
  - `take_profit_atr_multiple` candidates: `2.0`, `2.5`, `3.0`;
  - `minimum_atr_bps` candidates: `0.0` and `20.0`.
- Save raw JSON outputs and a manifest under `reports/task_311_atr_reward_cost_geometry_raw_outputs/`.
- Save a task report under `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`.

# Out of Scope

- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, or private endpoints.
- Frontend/backend/API changes.
- Candle backfill unless local data preflight proves the assigned window is missing.
- Machine learning, futures, leverage, portfolio optimization, or scheduler work.
- Relaxing or disabling the cost-aware gate for the primary validation.
- Searching entry thresholds beyond the predeclared lowest Task 308 threshold per interval.
- Post-result tuning of ATR period, ATR target multiples, minimum ATR bps, cost assumptions, or holding bars.
- Daily blog `report-ko.html` generation unless the owner explicitly adds it before execution.

# Requirements

- `1R` remains `ATR_at_entry`.
- ATR default remains `ATR(14)`, RMA smoothing, completed signal-candle timing from Task 309.
- Primary stop stays at `1 ATR`.
- Take-profit candidates must be exactly:
  - `2.0 ATR`;
  - `2.5 ATR`;
  - `3.0 ATR`.
- Minimum ATR bps candidates must be exactly:
  - `0.0` disabled comparator;
  - `20.0` bps volatility floor.
- Minimum ATR bps filter formula:

```text
atr_bps = ATR_at_entry / entry_price * 10000
entry allowed by this filter only if atr_bps >= minimum_atr_bps
```

- Cost-aware gate must still compute:

```text
gross_reward_bps
gross_risk_bps
estimated_round_trip_cost_bps
net_reward_bps = gross_reward_bps - estimated_round_trip_cost_bps
net_risk_bps = gross_risk_bps + estimated_round_trip_cost_bps
net_rr = net_reward_bps / net_risk_bps
```

- A candidate should be accepted only if all required gates pass:
  - valid momentum signal;
  - valid ATR risk distance;
  - `atr_bps >= minimum_atr_bps`;
  - cost-aware gate passes.
- Runner output and persisted metadata must include:
  - `risk_distance_mode`;
  - ATR period/smoothing/timing;
  - stop ATR multiple;
  - take-profit ATR multiple;
  - `minimum_atr_bps`;
  - accepted/cost-blocked/ATR-too-small/invalid-ATR counts where available.
- The report must compare against Task 309:
  - raw candidates;
  - accepted entries;
  - cost-blocked entries;
  - ATR-too-small blocked entries;
  - invalid ATR blocks;
  - trade count;
  - gross PnL;
  - net PnL;
  - total realized cost;
  - expectancy or average net R when available;
  - whether raising reward multiple made any candidate cost-feasible.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Confirm the strategy doc records asymmetric ATR reward/risk and minimum ATR bps before code/backtest execution.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- `docs/strategy/lookback_return_momentum_v1.md` documents the Task 311 asymmetric ATR reward/cost diagnostic before code/backtest execution.
- `LOOKBACK_RETURN_MOMENTUM` supports a configurable minimum ATR bps entry filter if it is not already available.
- Default production/research behavior is not silently changed beyond this assigned workflow.
- The primary validation uses `1 ATR` stop, `2.0/2.5/3.0 ATR` take-profit candidates, and `0.0/20.0` minimum ATR bps candidates.
- The Task 305/309 cost-aware gate remains enabled in the primary validation.
- Focused tests cover:
  - minimum ATR bps pass/fail behavior;
  - metadata fields for `atr_bps` and `minimum_atr_bps`;
  - cost-aware acceptance can occur when planned reward is sufficiently above cost;
  - runner CLI metadata for the new setting.
- Bounded validation runs for `1m`, `5m`, and `15m`, or any missing-data blocker is documented before stopping.
- A task report under `reports/` records exact commands, run identifiers if persisted, parameters, results, interpretation, known limitations, and next task.
- No live trading behavior, real order execution, private exchange endpoint usage, hardcoded secrets, or `.env` changes are introduced.

# Required Tests

## Unit Tests

- Add or update focused strategy tests for `minimum_atr_bps`.
- Add or update cost-aware tests showing asymmetric ATR target geometry can pass when net reward/risk clears the gate.

## Integration Tests

- Run focused momentum strategy/runner tests:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
```

- If CLI metadata or persistence output changes, run the focused persistence metadata test:

```bash
python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q
```

## Contract Tests

- Verify saved-run metadata or task-report output records ATR period, risk mode, stop ATR multiple, take-profit ATR multiple, and minimum ATR bps.
- Run whitespace verification:

```bash
git diff --check
```

## Safety Tests

- Confirm no code path added by this task calls Binance order/account/private endpoints.
- Confirm no API keys, secrets, or `.env` files are added or modified.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Strategy document updated before implementation/backtest execution.
- No post-result tuning beyond the predeclared validation grid.

# Verification

Default focused verification:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q
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

# Completion Summary

## Files Changed

- `docs/strategy/lookback_return_momentum_v1.md`
- `quant_bitcoin/strategies/lookback_return_momentum.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `tests/strategies/test_lookback_return_momentum.py`
- `tests/backtesting/test_lookback_return_momentum_runner.py`
- `reports/task_311_atr_reward_cost_geometry_raw_outputs/*.json`
- `reports/task_311_atr_reward_cost_geometry_raw_outputs/manifest.json`
- `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`

## Implementation Summary

- Documented Task 311 asymmetric ATR reward/cost diagnostic before code and backtest execution.
- Added configurable `minimum_atr_bps` support to `LOOKBACK_RETURN_MOMENTUM`.
- Added ATR bps metadata and `ATR_TOO_SMALL_FOR_COST` skip diagnostics.
- Added CLI wiring for `--minimum-atr-bps`.
- Added runner diagnostics for ATR-too-small blocked entries.
- Ran the predeclared 18-run validation grid over `1m`, `5m`, and `15m`.

## Tests Added Or Updated

- Added strategy tests for minimum ATR bps rejection and asymmetric ATR target acceptance after costs.
- Added runner tests for CLI metadata propagation and minimum ATR bps blocking.

## Tests Run

- `python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q`
- `python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q`
- `python -m json.tool` for all 18 raw Task 311 outputs
- `python -m json.tool` for `reports/task_311_atr_reward_cost_geometry_raw_outputs/manifest.json`
- `git diff --check`
- Code diff safety grep for API keys, secrets, `.env`, live order endpoints, signed endpoints, and `ENABLE_LIVE_TRADING`

## Codex Self-Review Result

- Scope respected: only Task 311 strategy/backtest/report work was executed.
- No frontend/backend API scope was changed.
- No live trading behavior, order endpoint, account endpoint, private endpoint, secret, or `.env` change was introduced.
- Strategy document was updated before implementation and validation.

## Known Limitations

- This task did not tune outside the predeclared `2.0/2.5/3.0 ATR` target and `0.0/20.0` minimum ATR bps grid.
- `minimum_atr_bps=20.0` did not change accepted entries; it only reclassified low-ATR rejected candidates.
- The validation is limited to the February-April 2026 window.

## Recommended Next Task

Create a bounded trade-quality diagnostic for accepted momentum entries. The next task should test a stronger ATR floor derived from the cost formula, directional continuation confirmation, or time-of-day/liquidity filtering, because Task 311 proved entry feasibility but filled variants still lost after costs.
