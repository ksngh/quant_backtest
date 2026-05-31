# Goal

Make `ORDER_BLOCK` entries fail closed when the planned stop/target does not produce acceptable net reward/risk after estimated fees, spread, and slippage.

# Source Requirement

Owner clarified:

```text
수수료계산해서 손익비 안나오면 거래하면 안돼
```

Interpretation:

- Before entering an `ORDER_BLOCK` trade, estimate round-trip cost from the selected transaction-cost config.
- Compare the intended stop/target reward and risk after costs.
- If the configured net reward/risk threshold is not met, emit a `SKIP` action instead of entering.

# Extracted Roles

- Owner role: Defines that entries with insufficient fee-adjusted reward/risk must not trade.
- Supporting roles:
  - Pattern action builder: Evaluate cost-adjusted reward/risk before emitting entry actions.
  - Strategy runner/CLI: Make the guard available and defaulted for `ORDER_BLOCK`.
  - Tests: Verify LONG/SHORT blocking and pass cases with realistic cost profiles.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint calls.
  - Changing FVG channel behavior unless needed to preserve existing tests.
  - Changing cash denomination or position sizing behavior.
  - Changing Order Block detector signal rules beyond entry cost gating.

# Context

Current state after Task 271:

- `ORDER_BLOCK` defaults to `conservative_crypto_1m` costs unless explicitly overridden.
- `ORDER_BLOCK` confirmation-close entries default to `previous_candle_1r` stop/target:
  - LONG stop = previous candle low.
  - LONG target = current close + risk.
  - SHORT stop = previous candle high.
  - SHORT target = current close - risk.
- A generic cost-aware entry filter already exists behind `--enable-cost-aware-entry-filter`.
- The current generic filter is not an `ORDER_BLOCK` owner-profile default.

Implementation assumption unless owner clarifies otherwise:

- Make cost-aware entry blocking default-on for `ORDER_BLOCK` owner profile when a nonzero cost profile/manual cost config is active.
- Preserve explicit debug/compatibility escape hatch through the existing `--cost-profile zero` and/or a new explicit disable flag if needed.
- Use configurable thresholds rather than hardcoding a single profitability rule.

# Scope

- Apply cost-aware entry gating to `ORDER_BLOCK` entries by default.
- Ensure the gate uses the risk plan after Task 271 previous-candle stop/target adjustment.
- Block both LONG and SHORT entries when:
  - gross reward is non-positive;
  - gross risk is non-positive;
  - net reward after estimated round-trip costs is below the configured minimum;
  - net reward/risk is below the configured minimum.
- Record metadata explaining:
  - gross reward/risk bps;
  - estimated one-side and round-trip cost bps;
  - net reward/risk bps;
  - net RR;
  - thresholds;
  - cost profile;
  - skip reason.

# Out of Scope

- Live trading.
- Real Binance order placement.
- New indicators.
- Dashboard visualization.
- Database schema changes unless existing JSON metadata is insufficient.
- Changing Task 271 stop/target formulas.
- Changing the actual engine PnL accounting model.

# Requirements

- `ORDER_BLOCK` default command should enforce the fee-adjusted entry guard.
- The guard must evaluate after the final effective risk plan is known.
- The guard must work for both LONG and SHORT.
- The guard must support explicit zero-cost debugging:
  - `--cost-profile zero` should disable nonzero-cost auto blocking unless the owner explicitly enables thresholds.
- The guard must support explicit threshold tuning:
  - reuse existing `--min-net-reward-bps` and `--min-net-rr` if practical;
  - or add `ORDER_BLOCK`-specific CLI aliases if needed for clarity.
- Default threshold decision should be documented in metadata/tests.
- Existing FVG behavior must not regress.
- Existing optional `--enable-cost-aware-entry-filter` behavior must remain compatible.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.
- [ ] Read current cost-aware entry filter code.
- [ ] Read current `ORDER_BLOCK` default-profile code.
- [ ] Confirm whether existing generic cost-aware filter can be reused without changing FVG semantics.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `ORDER_BLOCK` default backtests skip entries whose fee-adjusted net reward/risk is insufficient.
- LONG insufficient net RR emits a `SKIP` action instead of `ENTER_LONG`.
- SHORT insufficient net RR emits a `SKIP` action instead of `ENTER_SHORT`.
- Passing LONG/SHORT cases still enter and can exit through the existing engine.
- Skip metadata clearly shows cost assumptions and net RR calculation.
- `--cost-profile zero` remains usable for zero-cost debugging.
- Existing Task 270 volume/MTF filters remain unchanged.
- Existing Task 271 previous-candle risk/exit formula remains unchanged.
- No live trading behavior or exchange order endpoints are added.

# Required Tests

## Unit Tests

- `ORDER_BLOCK` LONG is blocked when costs make net reward/RR insufficient.
- `ORDER_BLOCK` SHORT is blocked when costs make net reward/RR insufficient.
- `ORDER_BLOCK` LONG passes when net reward/RR meets thresholds.
- `ORDER_BLOCK` SHORT passes when net reward/RR meets thresholds.
- Zero-cost debug config does not auto-block profitable gross setups.

## Integration Tests

- CLI default `ORDER_BLOCK` profile enables or auto-enforces the cost-aware guard.
- CLI metadata records selected thresholds and cost profile.
- Existing `--enable-ob-entry-volume-filter` and `--enable-ob-mtf-filter` still compose with cost-aware blocking.

## Contract Tests

- Skip reason remains stable, preferably `COST_INFEASIBLE_NET_RR` unless an `ORDER_BLOCK`-specific reason is justified.
- Summary/workflow metadata records the guard as active for `ORDER_BLOCK`.

## Safety Tests

- No API keys or `.env` files added.
- No live order/exchange account endpoints called.
- Backtests remain offline deterministic.

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

Default targeted verification:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_order_block.py -q
git diff --check
```

If strategy engine cost/PnL accounting is touched, also run:

```bash
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_pattern_strategy_backtest.py -q
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
