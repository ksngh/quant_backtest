# Goal

Add an explicit simulated-margin initial-margin guard for backtest-only short simulation.

This task should allow a user to intentionally simulate leveraged short exposure while making the leverage, required initial margin, and unsupported economics explicit. It must not implement real margin/futures trading.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/135_PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/142_SHORT_BUYING_POWER_POLICY.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/strategies/actions.py`
- `tests/backtesting/test_strategy_engine_accounting.py`
- relevant execution policy tests under `tests/execution/`

# Extracted Roles

- Owner role:
  - Backtest-only simulated-margin guard owner.
  - Owns initial-margin requirement checks for simulated short exposure.
- Supporting roles:
  - Short buying-power role: delegates explicit leverage cases to this guard.
  - Metrics role: reports required margin and block reasons.
  - Documentation role: preserves unsupported-economics warnings.
- Forbidden roles:
  - No real margin account integration.
  - No real futures integration.
  - No borrow-fee model.
  - No funding-fee model.
  - No maintenance margin model.
  - No liquidation engine.
  - No exchange account/order endpoint calls.

# Context

Task 142 should make default oversized shorts blocked or resized. Some research workflows still need intentional leveraged short simulation. The existing code already says no borrow fees, no futures funding, and no maintenance margin/liquidation model. This task adds only a minimal initial-margin check so explicit leverage simulation can be constrained.

Example:

- `starting_cash=10_000`, `price=80_000`, `quantity=1`, `leverage=5` requires `16_000` initial margin and must be blocked.
- `starting_cash=10_000`, `price=80_000`, `quantity=1`, `leverage=10` requires `8_000` initial margin and may be allowed only when explicit simulated-margin mode is enabled.

# Scope

- Add a backtest-only simulated-margin config, if not already modeled in Task 142.
- Support explicit leverage for short simulation.
- Compute required initial margin as `notional / leverage` or an equivalent documented formula.
- Block or resize entries when required initial margin plus costs exceeds available buying power.
- Add stable reason strings such as `INSUFFICIENT_INITIAL_MARGIN`.
- Include margin policy metadata in summary/execution metadata where needed.
- Preserve existing short PnL accounting after an allowed leveraged short is opened and closed.

# Out of Scope

- Maintenance margin.
- Liquidation price.
- Cross/isolated margin behavior.
- Borrow fees.
- Funding fees.
- Real exchange margin/futures behavior.
- CLI wiring. That is Task 145.
- Account-state field expansion. That is Task 144.

# Requirements

- Simulated margin must be opt-in and backtest-only.
- Leverage must be positive, finite, and greater than or equal to `1.0` unless a stricter bound is chosen.
- Required initial margin must be deterministic and tested.
- Insufficient margin must block or resize according to explicit policy.
- The engine must not imply liquidation protection or exchange margin accuracy.
- Summary metadata must continue to include unsupported economics limitations.
- Existing non-margin short policy from Task 142 must remain intact.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 142 is completed or explicitly approved as a dependency.
- [x] Confirm this Task 143 is recorded as the current active implementation task before coding.
- [x] Confirm Task 144 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 144 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Explicit simulated-margin config exists for backtest-only use.
- `10_000` cash / `80_000` price / `1 BTC` short / `5x` leverage blocks due to insufficient initial margin.
- `10_000` cash / `80_000` price / `1 BTC` short / `10x` leverage is allowed only when explicit simulated-margin mode is enabled and costs fit available buying power.
- Required initial margin is recorded in execution or summary metadata.
- Unsupported maintenance margin/liquidation/funding/borrow limitations remain visible.
- No real margin/futures behavior is added.

# Required Tests

## Unit Tests

- Test invalid leverage values fail validation.
- Test required initial margin calculation.
- Test insufficient initial margin blocks or resizes a short entry.
- Test sufficient initial margin allows a short entry only in explicit simulated-margin mode.
- Test margin metadata contains leverage and required initial margin.
- Test existing profitable and losing short PnL remains correct after allowed margin simulation.

## Integration Tests

- Test canonical backtest path with explicit simulated-margin config.
- Test canonical backtest path without explicit simulated-margin config keeps Task 142 default behavior.
- Test product-policy execution paths still reject spot short intents.

## Contract Tests

- Simulated margin config is clearly backtest-only.
- Existing execution fields remain readable.
- `ENTER_SHORT` and `EXIT_SHORT` mappings remain unchanged for allowed simulation shorts.

## Safety Tests

- No Binance margin endpoint is called.
- No Binance futures endpoint is called.
- No Binance account endpoint is called.
- No Binance order endpoint is called.
- No API keys are required.
- No live trading flag/default is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Initial-margin guard is not represented as a full futures/margin engine.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/execution
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
