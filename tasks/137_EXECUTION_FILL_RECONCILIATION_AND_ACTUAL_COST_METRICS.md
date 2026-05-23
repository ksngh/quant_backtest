# Goal

Record actual execution fills and calculate actual fee and slippage metrics by comparing execution reports against pre-trade reference prices and simulated cost assumptions.

This task analyzes testnet or later live fills. It does not enable live trading by itself.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/execution/`
- `quant_bitcoin/persistence/`
- `db/init/001_schema.sql`
- `tests/execution/`
- `tests/persistence/`
- `tasks/132_CANONICAL_ORDER_INTENT_AND_PAPER_EXECUTION.md`
- `tasks/135_BINANCE_SPOT_TESTNET_EXECUTION_CLIENT.md`

# Extracted Roles

- Owner role:
  - Execution quality analytics owner.
  - Owns actual fill persistence, fee normalization, VWAP calculation, and side-aware slippage calculation.
- Supporting roles:
  - Execution role: supplies order intent and execution fills.
  - Persistence role: stores reports/fills or metadata.
  - Backtest cost role: provides simulated cost assumptions for comparison.
- Forbidden roles:
  - No live trading enablement.
  - No margin/futures implementation.
  - No dynamic fee-tier trading decision logic.
  - No account portfolio management.

# Context

The backtest engine can simulate fees, spread, and slippage using basis-point assumptions. Actual execution quality requires comparing intended reference prices against exchange fills and actual commissions. Actual slippage must be calculated side-aware.

# Scope

- Add persistence or metadata contract for order intents, execution reports, and fills.
- Calculate fill VWAP.
- Calculate actual commission by fill.
- Preserve commission asset separately.
- Calculate side-aware slippage bps: BUY uses `(fill_vwap - reference_price) / reference_price * 10000`; SELL uses `(reference_price - fill_vwap) / reference_price * 10000`.
- Compare actual fee/slippage with simulated assumptions when available.
- Add JSON/report output for execution-quality diagnostics.
- Support testnet fills first.
- If commission asset conversion is unavailable, preserve raw commission and mark normalized quote commission as unavailable.

# Out of Scope

- Live trading enablement.
- Margin/futures fees.
- Funding/borrow fee modeling.
- Automatic fee-tier lookup unless separately approved.
- Real-time dashboard.
- Tax/accounting reporting.

# Requirements

- Every execution report must retain original order intent identity.
- Every fill must retain fill price, fill quantity, fill timestamp if available, commission, commission asset, maker/taker flag if available, and safe raw payload.
- Actual VWAP must be quantity-weighted.
- Slippage calculation must be side-aware.
- Reference price must be explicit and stored.
- Missing reference price must produce a warning and skip slippage calculation.
- Commission asset conversion must not be guessed.
- Simulated-vs-actual comparison must not mutate backtest results.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Execution fills can be represented and persisted or serialized deterministically.
- VWAP calculation is correct for multi-fill orders.
- BUY slippage and SELL slippage use opposite signs correctly.
- Commission and commission asset are preserved.
- Missing commission conversion does not produce fake quote-denominated fee.
- Report output compares actual metrics to simulated cost configuration when available.
- Ordinary tests do not call real exchange APIs.

# Required Tests

## Unit Tests

- Test VWAP for one fill.
- Test VWAP for multiple fills.
- Test BUY slippage bps.
- Test SELL slippage bps.
- Test zero or missing reference price fails safely.
- Test commission asset is preserved.
- Test missing commission conversion produces explicit unavailable field.
- Test simulated-vs-actual fee comparison.

## Integration Tests

- Test fake Binance testnet execution response maps to fills.
- Test execution report persistence/readback if schema or repository is added.
- Test runtime runner output includes actual fee/slippage metrics after fake fill.

## Contract Tests

- Backtesting cost helpers remain pure.
- Execution reconciliation does not call strategy code.
- Persistence read models do not re-submit orders.

## Safety Tests

- No live order execution.
- No account endpoint dependency in ordinary tests.
- No API keys in tests.
- No signed requests in metric-only code.

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
pytest
```

Additional verification:

```bash
pytest tests/execution
pytest tests/persistence
pytest tests/backtesting/test_strategy_engine_accounting.py
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
