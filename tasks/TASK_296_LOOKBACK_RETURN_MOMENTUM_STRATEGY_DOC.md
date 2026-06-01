# Task 296: Lookback Return Momentum Strategy Document

# Goal

Create a pre-implementation strategy document for `LOOKBACK_RETURN_MOMENTUM` under `docs/strategy/`.

This task exists because the owner wants to document the simplest pure lookback-return momentum baseline before any strategy implementation or backtest execution. The task is documentation-only: it creates the strategy markdown file and updates state files, but it does not implement strategy code, CLI wiring, tests, or saved backtest runs.

# Source Requirement

Owner request:

```text
가장 단순한 Lookback Return Momentum 전략을 구현해줘.
...
이 문서를 docs/strategy 안에 만들 수 있는 task 생성해줘
```

Clean requirement:

- Create a task that allows writing the owner-provided `LOOKBACK_RETURN_MOMENTUM` strategy document under `docs/strategy/`.
- The future strategy document must describe a pure momentum baseline using only recent `N` close-to-close return.
- The document must explicitly exclude FVG, Order Block, trend score, volume filter, ATR filter, higher-timeframe filter, liquidity target, reverse entry, partial take profit, trailing stop, image generation, report generation, daily report payload generation, and `image_manifest.json` generation.
- The document must capture the requested signal, long/short/no-trade logic, default parameters, timeframe-specific defaults, exit rules, same-candle stop-first assumption, duplicate-position prevention, test plan, and completion criteria.
- Do not implement the strategy in this task.
- Do not run a backtest in this task.

# Extracted Roles

- Owner role:
  - Defines the baseline strategy thesis and allowed/excluded features.
  - Decides that the next step should be a strategy document under `docs/strategy/`.
- Supporting roles:
  - Strategy-document author: create `docs/strategy/lookback_return_momentum_v1.md` from `docs/strategy/STRATEGY_TEMPLATE.md`.
  - Scope guard: ensure the task remains documentation-only.
  - Requirement normalizer: record formulas, parameters, assumptions, open questions, and test expectations clearly.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No strategy implementation.
  - No backtest execution.
  - No parameter tuning or validation run.
  - No CLI/config implementation.
  - No production code changes.
  - No frontend/backend/API/dashboard changes.
  - No live trading, real order execution, signed/private/order/account exchange endpoints, secrets, API keys, or `.env` changes.

# Context

Task 295 added a pre-backtest strategy-document gate:

```text
state files -> relevant task.md -> relevant docs/strategy/*.md -> implementation/backtest/report generation
```

At task creation time, no `LOOKBACK_RETURN_MOMENTUM` task or strategy document exists. Therefore this task should create only the relevant strategy markdown document first and stop. A separate later implementation task may add the strategy type and tests after the strategy document exists.

# Scope

Allowed files:

- `docs/strategy/lookback_return_momentum_v1.md`
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

Allowed actions:

- Create `docs/strategy/lookback_return_momentum_v1.md` using `docs/strategy/STRATEGY_TEMPLATE.md` as the structure baseline.
- Record the strategy as `research_only`.
- Record the pure close-return momentum thesis and formula:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Record long, short, and no-trade signal rules:

```text
long:  momentum_return >= entry_threshold
short: momentum_return <= -entry_threshold
none:  -entry_threshold < momentum_return < entry_threshold
```

- Record insufficient-lookback behavior: no signal before `lookback_bars` historical closes are available.
- Record first-version position rule: enter only when flat; do not reverse while a position is open.
- Record exit rules:
  - stop loss.
  - take profit.
  - time exit after `holding_bars`.
  - conservative stop-first assumption when stop and target are both reachable in the same candle.
- Record long and short stop/target calculations separately.
- Record default parameters and timeframe-specific defaults.
- Record required future tests for signal calculation, long/short/no signal, insufficient lookback, duplicate-entry prevention, time exit, and long/short stop/target handling.
- Record open questions and implementation blockers explicitly, especially the exact price-distance definition of `1R` because the original owner requirement specified `stop_loss_r` and `take_profit_r` but did not define the base `R` unit.
- Follow-up owner clarification resolved the v1 base `R` unit as `1R = entry_price * 0.002`.

# Out of Scope

- Do not add `LOOKBACK_RETURN_MOMENTUM` to strategy enums or strategy dispatch.
- Do not implement signal generation code.
- Do not implement stop loss, take profit, time exit, or backtest behavior.
- Do not add CLI/config flags.
- Do not add or update tests.
- Do not execute pytest unless only doc/state verification requires it.
- Do not run backtests.
- Do not persist DB runs.
- Do not generate reports, images, payloads, or manifests.
- Do not modify frontend/backend/API/dashboard code.
- Do not add live trading, real Binance order execution, exchange order/account/private endpoint usage, secrets, API keys, or `.env` changes.

# Requirements

## Strategy Document Requirements

The strategy document must include:

- Strategy identity:
  - name: `LOOKBACK_RETURN_MOMENTUM`
  - version: `v1`
  - slug: `lookback_return_momentum`
  - status: `research_only`
  - owner task: `TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC`
- Market/data scope:
  - BTCUSDT.
  - timeframes: `1m`, `5m`, `15m`.
  - required data: OHLCV candles, with signal logic using close prices only.
  - higher timeframes: none.
- Market phenomenon:
  - recent directional close-to-close return may reflect short-term order-flow pressure.
  - if pressure persists, the next `M` bars may continue in the same direction.
- Hypothesis:
  - if recent `N`-bar return exceeds a positive threshold, future `M`-bar direction may be positive.
  - if recent `N`-bar return is below the negative threshold, future `M`-bar direction may be negative.
  - direction accuracy is not sufficient unless average wins beat average losses and trading costs.
- Factors:
  - only `momentum_return`.
  - no ATR, volume, trend score, FVG, Order Block, or higher-timeframe factor.
- Signal logic:
  - formula.
  - long rule.
  - short rule.
  - no-trade rule.
  - insufficient-lookback no-signal rule.
  - completed-candle/no-lookahead rule.
- Entry logic:
  - enter long only when flat and long signal exists.
  - enter short only when flat and short signal exists.
  - do not enter when no signal exists.
  - do not reverse on opposite signal while a position is open.
- Exit logic:
  - stop loss.
  - take profit.
  - time exit.
  - separate long/short calculations.
  - same-candle stop/target priority: stop first.
- Default parameters:

```text
lookback_bars = 20
entry_threshold = 0.001
holding_bars = 5
stop_loss_r = 1.0
take_profit_r = 1.5
```

- Timeframe-specific defaults:

| Timeframe | lookback_bars | holding_bars | entry_threshold | Interpretation |
|---|---:|---:|---:|---|
| `1m` | 20 | 5 | 0.001 | last 20 minutes -> next 5 minutes |
| `5m` | 12 | 6 | 0.0015 | last 1 hour -> next 30 minutes |
| `15m` | 8 | 4 | 0.002 | last 2 hours -> next 1 hour |

- Explicit exclusions:
  - ATR filter.
  - volume filter.
  - trend score.
  - FVG.
  - Order Block.
  - higher-timeframe filter.
  - liquidity target.
  - reverse entry.
  - partial take profit.
  - trailing stop.
  - image generation.
  - report generation.
  - daily report payload generation.
  - `image_manifest.json` generation.
- Future implementation test plan:
  - signal calculation.
  - long signal.
  - short signal.
  - no signal.
  - lookback shortage.
  - duplicate-entry prevention.
  - time exit.
  - long and short stop/target.
  - same-candle stop-first behavior.

## Risk-Distance Requirements

The strategy document must not silently invent unresolved mechanics. The original document explicitly recorded:

- What is the base price-distance definition of `1R`?
- Should `1R` be derived from a fixed return, `entry_threshold`, a configurable `risk_return`, or another rule?
- Until the base `R` unit is defined, implementation must treat stop/target distance as blocked or requiring an explicit implementation assumption.

Owner follow-up resolved this item:

```text
1R = entry_price * 0.002
```

The strategy document must now record fixed `0.2%` entry-price risk distance as the v1 default.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 296 is the assigned task.
- [x] Read `docs/strategy/README.md`.
- [x] Read `docs/strategy/STRATEGY_TEMPLATE.md`.
- [x] Confirm no existing `docs/strategy/lookback_return_momentum_v1.md` should be overwritten.
- [x] Record any unresolved assumptions before editing docs.

## After Implementation

- [x] Create `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 296 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Clearly record the recommended next task.

# Implementation Notes

- Created `docs/strategy/lookback_return_momentum_v1.md` from the strategy template structure.
- Captured the owner-provided pure momentum baseline using only completed close-to-close `momentum_return`.
- Documented long, short, no-trade, insufficient-lookback, and flat-only/no-reverse entry behavior.
- Documented stop loss, take profit, time exit, and conservative same-candle stop-first priority.
- Documented default parameters and `1m`/`5m`/`15m` timeframe-specific defaults.
- Explicitly excluded ATR, volume, trend score, FVG, Order Block, higher-timeframe filter, liquidity target, reverse entry, partial take profit, trailing stop, image generation, report generation, daily report payload generation, and `image_manifest.json`.
- Initially recorded the unresolved base `1R` price-distance definition as a future implementation blocker.
- Updated the strategy document after owner clarification: v1 uses fixed percentage risk distance, `1R = entry_price * 0.002`.
- No strategy code, CLI/config wiring, tests, backtest execution, DB mutation, report, image, live trading behavior, exchange endpoint behavior, secret, or `.env` change was added.

# Verification Results

Passed:

```bash
test -f docs/strategy/lookback_return_momentum_v1.md
rg -n "LOOKBACK_RETURN_MOMENTUM|momentum_return|lookback_bars|entry_threshold|holding_bars|stop_loss_r|take_profit_r" docs/strategy/lookback_return_momentum_v1.md
rg -n "FVG|Order Block|ATR filter|volume filter|trend score|higher-timeframe|reverse entry|partial take profit|trailing stop" docs/strategy/lookback_return_momentum_v1.md
git diff --check -- docs/strategy/lookback_return_momentum_v1.md tasks/TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
git diff --name-only -- docs/strategy/lookback_return_momentum_v1.md quant_bitcoin tests frontend backend reports
```

Additional scope check:

```bash
git status --short docs/strategy/lookback_return_momentum_v1.md quant_bitcoin tests frontend backend reports tasks/TASK_296_LOOKBACK_RETURN_MOMENTUM_STRATEGY_DOC.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
```

Notes:

- Task 296 changed only `docs/strategy/lookback_return_momentum_v1.md`, this task file, and root state files.
- Existing untracked `reports/` artifacts were already present in the working tree and were not modified by this task.

# Codex Self-Review Result

- Scope respected: documentation-only Task 296 was executed; no implementation/backtest scope was added.
- Requirement matched: the strategy document captures the owner-provided signal, rules, parameters, exclusions, tests, and completion boundary.
- Status tracking complete: `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` were updated.
- Role ownership respected: no frontend/backend/API/dashboard, execution, DB, or live-trading responsibility was touched.
- Safety checks passed: no secrets, `.env`, exchange endpoints, order behavior, or real trading behavior were added.
- Risk-distance clarification recorded: `1R = entry_price * 0.002`.

# Acceptance Criteria

- `docs/strategy/lookback_return_momentum_v1.md` exists.
- The document follows the section structure of `docs/strategy/STRATEGY_TEMPLATE.md`.
- The document records `LOOKBACK_RETURN_MOMENTUM` as `research_only`.
- The document records the pure close-return momentum formula.
- The document records long, short, no-trade, insufficient-lookback, and flat-only entry behavior.
- The document records stop loss, take profit, time exit, and same-candle stop-first priority.
- The document records the default parameters and `1m`/`5m`/`15m` timeframe defaults.
- The document explicitly excludes all owner-listed non-baseline features.
- The document records the future implementation and test requirements.
- The document records fixed v1 `1R` base-distance definition: `entry_price * 0.002`.
- No strategy code is implemented.
- No backtest is executed.
- No DB records are mutated.
- No live trading, exchange order/account endpoint, secret, API key, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required for this documentation-only task.

## Integration Tests

- Not required for this documentation-only task.

## Contract Tests

Run documentation checks:

```bash
test -f docs/strategy/lookback_return_momentum_v1.md
rg -n "LOOKBACK_RETURN_MOMENTUM|momentum_return|lookback_bars|entry_threshold|holding_bars|stop_loss_r|take_profit_r" docs/strategy/lookback_return_momentum_v1.md
rg -n "FVG|Order Block|ATR filter|volume filter|trend score|higher-timeframe|reverse entry|partial take profit|trailing stop" docs/strategy/lookback_return_momentum_v1.md
git diff --check -- docs/strategy/lookback_return_momentum_v1.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
```

## Safety Tests

Confirm no implementation/runtime artifacts were added:

```bash
git diff --name-only -- docs/strategy/lookback_return_momentum_v1.md quant_bitcoin tests frontend backend reports
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.
- No strategy implementation or backtest execution.

# Verification

Default for this documentation-only task:

```bash
test -f docs/strategy/lookback_return_momentum_v1.md
rg -n "LOOKBACK_RETURN_MOMENTUM|momentum_return|same-candle|stop" docs/strategy/lookback_return_momentum_v1.md
git diff --check -- docs/strategy/lookback_return_momentum_v1.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
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
