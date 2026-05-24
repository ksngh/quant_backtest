# Goal

Fix the Fair Value Gap execution/risk mismatch where the strategy can enter at the actual market fill price while stop/target simulation still uses the original FVG midpoint/reference entry price, causing take-profit exits to appear as realized losses.

# Source Requirement

Owner-reported issue after reviewing persisted FVG backtest trades:

- The strategy appears to buy/sell in a way that always loses money.
- This is not just poor timing; even with imperfect entry timing, some profitable exits should appear.
- Investigation found a structural mismatch:
  - FVG risk plans are built from `event.entry_reference` such as the FVG midpoint.
  - The default action builder can fill entry at `MARKET_ON_CONFIRMATION_CLOSE`, which may be far above a bullish FVG midpoint or far below a bearish FVG midpoint.
  - Exit simulation still evaluates stops and targets from the original reference entry price.
  - Result: a long can buy at `110` and "take profit" at `102`, producing a real loss while metadata reports a target hit or positive R multiple.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md` only as needed for recent FVG context
- `tasks/154_ENTRY_FILL_PRICE_MODEL_SEPARATION.md`
- `tasks/157_INTRABAR_SEQUENCING_POLICY_INTEGRATION.md`
- `tasks/159_NO_LOOKAHEAD_PATTERN_DETECTION_CONTRACT.md`
- `tasks/160_TRANSACTION_COST_AND_SLIPPAGE_REALISM.md`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/fair_value_gap_risk_exit.py`
- `quant_bitcoin/patterns/entry_simulation.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/risk/exit_plan.py`
- `quant_bitcoin/risk/exit_simulation.py`
- relevant FVG/action-builder/strategy-engine tests

# Extracted Roles

- Owner role:
  - Backtest execution correctness owner.
  - Owns the requirement that realized trade PnL, exit reason, and R metadata must agree with actual fill prices.
- Supporting roles:
  - FVG detector role: emits signal-time FVG events without look-ahead.
  - Risk planner role: creates stop/target plans from a consistent entry price.
  - Entry simulator role: determines actual historical fill price and timestamp.
  - Strategy engine role: computes realized PnL from actual requested/fill prices.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No exchange account/order endpoints.
  - No strategy profitability tuning or parameter optimization.
  - No dashboard redesign beyond minimal contract/docs updates if required.

# Context

Current behavior to verify and fix:

- `create_fair_value_gap_risk_exit_plan()` creates a plan using `event.entry_reference`.
- `build_pattern_trade_actions()` may simulate entry at the confirmation candle close and emits `requested_price=entry.fill_price`.
- The same original `risk_plan` is then passed into `simulate_pattern_exit()`.
- Therefore exit targets and realized R are calculated from `risk_plan.entry_price`, not necessarily from the actual fill price.

Expected behavior:

- For market entries, actual entry fill price must be the basis for risk-per-unit, R targets, target ordering, and realized R.
- For limit/reference entries, if the fill occurs at the planned reference price, the original risk plan can remain valid.
- If a fill price differs from the risk plan entry price, the risk plan must be adjusted or rebuilt before exit simulation.
- A `TAKE_PROFIT` exit must not be possible at a price that produces negative realized PnL for the actual entry/fill side.

# Scope

- Align FVG/pattern action-builder risk plan entry price with actual entry fill price before exit simulation.
- Ensure target prices are directionally valid relative to the actual fill price:
  - LONG targets must be greater than actual entry fill price.
  - SHORT targets must be less than actual entry fill price.
- Ensure target ordering is directionally coherent after any rebuild/filter:
  - LONG targets progress upward.
  - SHORT targets progress downward.
- Ensure realized R metadata is computed from the actual fill-adjusted risk plan.
- Preserve no-lookahead behavior: exit simulation may use only candles available after/at the fill path being simulated, not future data for event detection.
- Add regression tests for bullish and bearish FVG paths where the old implementation would mark a target hit that is actually a loss.
- Update docs/API/README only if output contract or semantics change.
- Update `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md` after execution.

# Out of Scope

- Changing FVG detection definitions.
- Changing `BULLISH -> LONG` or `BEARISH -> SHORT` direction mapping unless tests prove it is wrong.
- Retuning FVG scores, thresholds, stops, or take-profit multiples for profitability.
- Adding ML, optimization, live trading, exchange execution, or frontend redesign.
- Enabling Task 138 or any live order flow.

# Requirements

- Actual fill price and risk plan entry price must be consistent for exit simulation.
- `TAKE_PROFIT` exits must have non-negative gross PnL for the actual position side and actual fill price.
- `HARD_STOP` exits must not be mislabeled as take-profit due to stale reference-entry targets.
- Target lists must exclude targets that are not actionable relative to the actual fill price.
- Realized R metadata must be based on the same entry price used for actual exit simulation.
- Existing limit/reference entry behavior must remain deterministic.
- FVG no-lookahead detector guarantees from Task 159 must remain intact.
- All changes must be backtest-only and simulation-only.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
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

- A bullish FVG market-fill scenario where actual fill is above the original midpoint no longer exits at a lower "take-profit" price.
- A bearish FVG market-fill scenario where actual fill is below the original midpoint no longer exits at a higher "take-profit" price.
- No `TAKE_PROFIT` action created by the pattern action builder has negative gross PnL when replayed by the strategy engine from actual fill price.
- Realized R metadata and trade PnL agree in sign for LONG and SHORT exits.
- Existing FVG no-lookahead tests still pass.
- Existing strategy-engine accounting tests still pass.
- No live trading or exchange order behavior is introduced.

# Required Tests

## Unit Tests

- Add/modify `tests/backtesting/test_pattern_action_builder.py` to cover actual-fill risk-plan rebuild/alignment for bullish and bearish FVG-style events.
- Add tests that target prices are filtered/sorted relative to actual fill price for LONG and SHORT.
- Add tests that `realized_r_multiple` sign agrees with actual fill/exit PnL sign.

## Integration Tests

- Add/modify canonical strategy runner tests in `tests/backtesting/test_pattern_postgres_runner_cli.py` or `tests/backtesting/test_strategy_engine.py` to verify an actual FVG-like market fill cannot produce `TAKE_PROFIT` with negative realized PnL.
- Run existing FVG detector and no-lookahead tests.

## Contract Tests

- Verify FVG direction mapping remains `BULLISH -> LONG`, `BEARISH -> SHORT`.
- Verify no-lookahead detector parity remains unchanged.
- Verify output metadata clearly distinguishes original `entry_reference` from actual `fill_price` and fill-adjusted risk plan entry price if both are retained.

## Safety Tests

- Confirm no API keys, `.env`, live trading, signed exchange requests, or order/account endpoint calls are introduced.
- Confirm changes remain inside backtest/pattern/risk simulation boundaries.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_strategy_engine.py tests/patterns/test_fair_value_gap.py tests/patterns/test_no_lookahead_contract.py
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

- Files changed:
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/172_FVG_ACTUAL_FILL_RISK_PLAN_ALIGNMENT.md`
- Implementation summary:
  - `build_pattern_trade_actions()` now aligns a valid risk plan to the actual filled entry price before exit simulation.
  - Fill-adjusted plans recompute stop distance/risk-per-unit from the original structural stop and ATR buffer.
  - Targets are rebuilt or filtered so LONG targets remain above actual fill and SHORT targets remain below actual fill, then sorted in execution direction.
  - Exit simulation and realized R metadata now use the same fill-adjusted plan used by actual execution prices.
  - Metadata preserves both the original entry reference and the fill-adjusted risk plan entry/risk values.
- Tests added or updated:
  - Added long/short regression coverage for stale-reference target filtering.
  - Added target direction/order regression coverage.
  - Added strategy-engine replay coverage that verifies fill-adjusted take-profit does not produce negative gross PnL.
  - Updated the limit-entry test fixture so the entry fill and risk plan are internally consistent.
- Tests run:
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_strategy_engine.py tests/patterns/test_fair_value_gap.py tests/patterns/test_no_lookahead_contract.py`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed inside Task 172 backtest/pattern action-building behavior.
  - No frontend, live trading, exchange order, credential, or unrelated feature work was added.
  - Tests and ledgers were updated.
- Known limitations:
  - This fixes stale reference-entry targets; it does not retune FVG profitability, FVG detection rules, or stop/take-profit parameters.
- Recommended next task:
  - No automatic next implementation task. Assign or create the next non-live task explicitly.
