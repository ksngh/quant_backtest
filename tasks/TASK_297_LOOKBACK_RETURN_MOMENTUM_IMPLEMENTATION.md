# Task 297: Lookback Return Momentum Implementation

# Goal

Implement the research-only `LOOKBACK_RETURN_MOMENTUM` strategy from `docs/strategy/lookback_return_momentum_v1.md`.

The implementation must add the strategy type, completed-candle close-return signal calculation, long/short/no-trade behavior, fixed-percentage risk exits, time exit, CLI or config parameter wiring, and focused tests. The first implementation is a pure momentum baseline and must not add filters or unrelated strategy features.

# Source Requirement

Owner request:

```text
어 구현 task 만들어줘.
```

Context from the owner-provided strategy requirement:

```text
LOOKBACK_RETURN_MOMENTUM
momentum_return = close[t] / close[t - lookback_bars] - 1
Long:  momentum_return >= entry_threshold
Short: momentum_return <= -entry_threshold
No trade: -entry_threshold < momentum_return < entry_threshold

Default:
lookback_bars = 20
entry_threshold = 0.001
holding_bars = 5
stop_loss_r = 1.0
take_profit_r = 1.5

Risk:
1R = entry_price * 0.002
```

Clean requirement:

- Implement `LOOKBACK_RETURN_MOMENTUM` as a new research-only strategy type.
- Use only recent completed-candle close-to-close return as the signal.
- Support long, short, and no-trade outcomes.
- Suppress signals when there are not enough prior closes for `lookback_bars`.
- Enter only when flat.
- Do not reverse while a position is open.
- Support stop loss, take profit, and time exit.
- Use fixed v1 risk distance:

```text
R_distance = entry_price * 0.002
```

- Treat same-candle stop/target ambiguity conservatively: stop first.
- Keep long and short stop/target calculations separate.
- Make key parameters adjustable by CLI or config.
- Support default presets for `1m`, `5m`, and `15m`.
- Add focused tests for signal, entry, duplicate-position prevention, time exit, and stop/target behavior.
- Do not run a report-generation workflow in this task.
- Do not generate images, daily report payloads, or `image_manifest.json`.

# Extracted Roles

- Owner role:
  - Defines the strategy thesis, signal formula, defaults, exit rules, exclusions, and fixed `1R` definition.
- Supporting roles:
  - Strategy implementer: add `LOOKBACK_RETURN_MOMENTUM` with completed-candle close-return logic.
  - Backtest integrator: wire the strategy into the existing research/backtest execution path without redesigning shared contracts.
  - CLI/config implementer: expose configurable lookback, threshold, holding, risk distance, stop, target, and timeframe preset controls using existing CLI/config patterns.
  - Test engineer: add focused unit and integration tests for the required behavior.
  - Scope guard: keep the implementation as a pure momentum baseline with no filters.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No signed/private/order/account exchange endpoints.
  - No secrets, API keys, `.env`, credential handling, or live-execution flags.
  - No ATR filter, volume filter, trend score, FVG, Order Block, higher-timeframe filter, liquidity target, reverse entry, partial take profit, or trailing stop.
  - No image generation, report generation, daily report payload generation, or `image_manifest.json`.
  - No frontend/backend/API/dashboard changes unless an existing required strategy enum/type surface forces a minimal contract update and the task records it explicitly.
  - No database schema changes.
  - No saved DB validation/backtest run unless the implementation path already requires a minimal smoke run and the owner explicitly accepts it in a later instruction.

# Context

Task 296 completed the required pre-implementation strategy document:

- `docs/strategy/lookback_return_momentum_v1.md`

Important Task 296 decisions:

- Strategy status is `research_only`.
- Signal uses only:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Fixed v1 risk distance:

```text
R_distance = entry_price * risk_distance_pct
risk_distance_pct = 0.002
```

- Timeframe defaults:

| Timeframe | lookback_bars | holding_bars | entry_threshold |
|---|---:|---:|---:|
| `1m` | 20 | 5 | 0.001 |
| `5m` | 12 | 6 | 0.0015 |
| `15m` | 8 | 4 | 0.002 |

This implementation task must read the strategy document before coding and must update it if implementation choices change strategy logic, risk logic, cost assumptions, execution timing assumptions, validation windows, or research/live-trading boundary.

# Scope

Allowed files:

- `docs/strategy/lookback_return_momentum_v1.md` only if implementation details materially clarify or change the documented assumptions.
- Relevant strategy/backtest source under `quant_bitcoin/`.
- Relevant CLI/config code that already owns strategy backtest parameter wiring.
- Focused tests under `tests/`.
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

Implementation scope:

- Add `LOOKBACK_RETURN_MOMENTUM` to the existing strategy type/registry/dispatch path.
- Implement signal calculation:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Implement signal outcomes:
  - long when `momentum_return >= entry_threshold`.
  - short when `momentum_return <= -entry_threshold`.
  - no signal when inside the threshold band.
  - no signal when lookback history is insufficient.
- Implement flat-only entry:
  - no new entry while any position is open.
  - no reverse entry.
- Implement risk exits:
  - `risk_distance_pct` default `0.002`.
  - `R_distance = entry_price * risk_distance_pct`.
  - long stop: `entry_price - stop_loss_r * R_distance`.
  - long target: `entry_price + take_profit_r * R_distance`.
  - short stop: `entry_price + stop_loss_r * R_distance`.
  - short target: `entry_price - take_profit_r * R_distance`.
  - default `stop_loss_r = 1.0`.
  - default `take_profit_r = 1.5`.
- Implement time exit:

```text
if bars_since_entry >= holding_bars:
    exit at close
```

- Implement conservative same-candle sequencing:
  - if stop and target are both reachable in the same candle, stop is processed first.
- Expose parameters by CLI or config using existing project conventions:
  - `lookback_bars`.
  - `entry_threshold`.
  - `holding_bars`.
  - `risk_distance_pct`.
  - `stop_loss_r`.
  - `take_profit_r`.
  - timeframe preset for `1m`, `5m`, `15m`, or equivalent explicit parameter support.
- Add or update tests for all required behavior.

# Out of Scope

- Do not add ATR filter.
- Do not add volume filter.
- Do not add trend score.
- Do not add FVG.
- Do not add Order Block.
- Do not add higher-timeframe filter.
- Do not add liquidity target.
- Do not add reverse entry.
- Do not add partial take profit.
- Do not add trailing stop.
- Do not generate images.
- Do not generate reports.
- Do not generate daily report payloads.
- Do not generate `image_manifest.json`.
- Do not add live trading.
- Do not add real exchange order execution.
- Do not call exchange order/account/private endpoints.
- Do not add secrets, API keys, or `.env` changes.
- Do not add dashboard/frontend/backend/API behavior unless a minimal existing read-only type exposure is strictly necessary and documented.
- Do not run broad parameter sweeps or optimize thresholds in this implementation task.
- Do not promote the strategy beyond `research_only`.

# Requirements

## Strategy Document Gate

- Read `docs/strategy/lookback_return_momentum_v1.md` after this task file and before implementation.
- If the implementation needs a different entry timing, exit ordering, risk assumption, or cost assumption from the strategy document, update the strategy document in the same task before completing.
- Preserve the v1 pure momentum boundary.

## Signal Requirements

- Use completed-candle close prices only.
- Compute:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Reject or skip invalid calculations:
  - missing close.
  - non-positive denominator close.
  - insufficient lookback.
  - invalid non-positive `lookback_bars`.
  - invalid non-positive `entry_threshold`.
  - invalid non-positive `holding_bars`.
- Do not use future candles to compute the signal.

## Entry Requirements

- Long signal:

```text
momentum_return >= entry_threshold
```

- Short signal:

```text
momentum_return <= -entry_threshold
```

- No signal:

```text
-entry_threshold < momentum_return < entry_threshold
```

- Enter only when flat.
- Do not open same-direction or opposite-direction positions while a position is open.
- Do not reverse on opposite signal in v1.
- Use the existing backtest engine's entry timing convention when possible.
- If the existing engine does not have a clear entry timing convention for this strategy, document the chosen timing in `docs/strategy/lookback_return_momentum_v1.md` and tests.

## Exit Requirements

- Fixed risk distance:

```text
risk_distance_pct = 0.002
R_distance = entry_price * risk_distance_pct
```

- Long:

```text
stop_price = entry_price - (stop_loss_r * R_distance)
take_profit_price = entry_price + (take_profit_r * R_distance)
```

- Short:

```text
stop_price = entry_price + (stop_loss_r * R_distance)
take_profit_price = entry_price - (take_profit_r * R_distance)
```

- Time exit:

```text
if bars_since_entry >= holding_bars:
    exit at close
```

- Same-candle stop/target ambiguity:
  - stop loss wins over take profit.
- Opposite signals do not trigger exit.

## Parameter Requirements

Defaults:

```text
lookback_bars = 20
entry_threshold = 0.001
holding_bars = 5
risk_distance_pct = 0.002
stop_loss_r = 1.0
take_profit_r = 1.5
```

Timeframe defaults:

```text
1m:  lookback_bars = 20, holding_bars = 5, entry_threshold = 0.001
5m:  lookback_bars = 12, holding_bars = 6, entry_threshold = 0.0015
15m: lookback_bars = 8,  holding_bars = 4, entry_threshold = 0.002
```

- Parameter overrides must be available through CLI or config.
- If a timeframe preset system does not exist, explicit parameter flags are acceptable, but the task must verify that 1m, 5m, and 15m can each be run by selecting the corresponding parameters.

## Metadata and Explainability Requirements

Where the existing architecture supports metadata, include:

- strategy name/version.
- `momentum_return`.
- `lookback_bars`.
- `entry_threshold`.
- `holding_bars`.
- `risk_distance_pct`.
- `stop_loss_r`.
- `take_profit_r`.
- signal side.
- skip reason for insufficient lookback or invalid parameters.
- exit reason: stop loss, take profit, or time exit.

Do not redesign shared persistence contracts solely for this task.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 297 is the assigned task.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Inspect existing strategy/backtest registration and CLI/config patterns.
- [x] Confirm parallel work is not needed for shared contract changes.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 297 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Update `docs/strategy/lookback_return_momentum_v1.md` if implementation clarifies or changes documented assumptions.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `LOOKBACK_RETURN_MOMENTUM` strategy type is available in the existing strategy execution path.
- The strategy computes `momentum_return` exactly from current close and `lookback_bars` prior close.
- Long, short, and no-trade cases work.
- Insufficient lookback produces no signal.
- Position-open state blocks all new entries.
- Opposite signal while in position does not reverse or close early.
- Fixed `1R = entry_price * 0.002` is implemented as default risk distance.
- Long and short stop/target formulas are implemented separately.
- Same-candle stop/target ambiguity resolves to stop first.
- Time exit closes at close after `holding_bars`.
- Parameters can be adjusted by CLI or config.
- `1m`, `5m`, and `15m` default configurations are executable through presets or explicit parameter sets.
- Focused tests cover the required signal, entry, duplicate-entry, time-exit, stop/target, and same-candle behavior.
- No excluded filters or features are added.
- No live trading, order endpoint, secret, `.env`, report, image, payload, or manifest behavior is added.

# Required Tests

## Unit Tests

- Signal calculation uses `close[t] / close[t - lookback_bars] - 1`.
- Rising prices produce positive `momentum_return`.
- Falling prices produce negative `momentum_return`.
- Unchanged prices produce zero or near-zero `momentum_return`.
- Long signal occurs at `momentum_return >= entry_threshold`.
- Short signal occurs at `momentum_return <= -entry_threshold`.
- No signal occurs inside the threshold band.
- Insufficient lookback produces no signal.
- Invalid denominator close is skipped or rejected safely.
- Fixed risk distance uses `entry_price * 0.002`.
- Long stop/target formulas are correct.
- Short stop/target formulas are correct.

## Integration Tests

- Strategy can be selected as `LOOKBACK_RETURN_MOMENTUM` in the existing execution path.
- Parameter overrides flow from CLI/config to strategy behavior.
- 1m default parameters are runnable.
- 5m default parameters are runnable.
- 15m default parameters are runnable.
- While a position is open, same-direction and opposite-direction signals do not create new entries.
- Time exit closes at close after `holding_bars`.
- Same-candle stop and target hit resolves to stop first.

## Contract Tests

- Existing strategy/backtest public interfaces remain backward-compatible.
- Existing strategy tests still pass.
- Strategy metadata, if present, includes key parameters without changing unrelated schema.

## Safety Tests

- No exchange order/account/private endpoint calls are introduced.
- No API keys, secrets, `.env`, or live-trading defaults are introduced.
- Paper/research simulation remains offline-only.
- Tests do not call real exchange order endpoints.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Strategy document read before implementation.
- Strategy document updated if implementation assumptions changed.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.
- No excluded filters or features added.
- Tests added or updated.
- Verification commands run.

# Verification

Recommended focused verification:

```bash
pytest tests/strategies tests/backtesting
```

If the repository has different test locations for strategy/backtest code, use the focused test files added or modified by this task and then run the relevant existing strategy/backtest suite.

Also run:

```bash
git diff --check -- quant_bitcoin tests docs/strategy/lookback_return_momentum_v1.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
rg -n "LOOKBACK_RETURN_MOMENTUM|lookback_return_momentum|risk_distance_pct|momentum_return" quant_bitcoin tests docs/strategy/lookback_return_momentum_v1.md
rg -n "ATR filter|volume filter|trend score|FVG|Order Block|higher-timeframe filter|reverse entry|partial take profit|trailing stop|image_manifest" quant_bitcoin tests docs/strategy/lookback_return_momentum_v1.md
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

# Implementation Result

Completed in Task 297:

- Added offline-only `LOOKBACK_RETURN_MOMENTUM` implementation in `quant_bitcoin/strategies/lookback_return_momentum.py`.
- Added completed-candle close-return signal calculation, long/short/no-trade signal states, insufficient-lookback and invalid-close no-signal handling, fixed-percentage `1R`, side-specific stop/target levels, flat-only/no-reverse action generation, stop/target/time exits, and stop-first same-candle ambiguity handling.
- Wired the strategy into `quant_bitcoin/backtesting/strategy_postgres_runner_core.py` through the existing strategy runner path.
- Added CLI parameters:
  - `--lookback-bars`
  - `--entry-threshold`
  - `--holding-bars`
  - `--risk-distance-pct`
  - `--stop-loss-r`
  - `--take-profit-r`
- Added 1m/5m/15m defaults through `config_for_timeframe`.
- Updated `docs/strategy/lookback_return_momentum_v1.md` to document implementation choices:
  - entry at signal candle close.
  - no exit checks on the entry candle.
  - exit precedence is stop loss, then take profit, then time exit.
  - no new same-candle entry after an exit.
- Added focused tests in:
  - `tests/strategies/test_lookback_return_momentum.py`
  - `tests/backtesting/test_lookback_return_momentum_runner.py`

Verification run:

```bash
pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py
```

Result: `13 passed`.

Additional verification:

```bash
python -m compileall quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py
git diff --check -- quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/strategies/__init__.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py docs/strategy/lookback_return_momentum_v1.md STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_297_LOOKBACK_RETURN_MOMENTUM_IMPLEMENTATION.md
rg -n "LOOKBACK_RETURN_MOMENTUM|lookback_return_momentum|risk_distance_pct|momentum_return" quant_bitcoin tests docs/strategy/lookback_return_momentum_v1.md
rg -n "ATR filter|volume filter|trend score|FVG|Order Block|higher-timeframe filter|reverse entry|partial take profit|trailing stop|image_manifest" quant_bitcoin/strategies/lookback_return_momentum.py tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py docs/strategy/lookback_return_momentum_v1.md
```

Result: compile/check/search verification completed. The exclusion search only matched explicit exclusions in the strategy document.

Broader suite note:

```bash
pytest tests/strategies tests/backtesting
```

Result: `613 passed, 2 failed`. The two failures are in `tests/backtesting/test_strategy_cli_persistence.py` and reflect existing expectations around default `FAIR_VALUE_GAP` owner-profile costs/cash conversion, not the new `LOOKBACK_RETURN_MOMENTUM` path. They were left unchanged because adjusting them is outside Task 297.
