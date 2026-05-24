# Goal

Make pattern entry fill modes truthful by separating actual market-on-confirmation-close fills from reference-price or limit-style fills.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE` in `quant_bitcoin/patterns/entry_simulation.py` fills at the confirmation candle close.
- `build_pattern_trade_actions()` currently creates a synthetic confirmation candle whose OHLC all equal `risk_plan.entry_price`.
- This makes a market-on-close mode behave like a reference-price fill for some pattern plans.

Read and inspect:

- `tasks/112_EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT.md`
- `tasks/093_ENTRY_FILL_INTRABAR_INTEGRATION.md`
- `quant_bitcoin/patterns/entry_simulation.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/patterns/*_risk_exit.py`
- `quant_bitcoin/backtesting/intrabar_policy.py`
- entry simulation and strategy engine tests

# Extracted Roles

- Owner role:
  - Historical fill-model contract owner.
  - Owns naming and semantics of pattern entry modes.
- Supporting roles:
  - Pattern risk-plan role: supplies entry references.
  - Backtest runner role: supplies actual confirmation/future candles.
  - Engine role: executes requested prices after the fill model decides them.
- Forbidden roles:
  - No exchange order placement.
  - No live limit-order routing.
  - No frontend work except docs if needed.

# Context

Code-level hints:

- In `pattern_action_builder.py`, replace the synthetic confirmation candle with the real confirmation candle where possible.
- `_expand_raw_actions()` knows the current index and can pass `candles.iloc[index - 1]` as the actual confirmation candle.
- Keep `risk_plan.entry_price` as an entry reference, not as a fake market close.
- For FVG/Order Block midpoint retests, use `LIMIT_AT_ENTRY_REFERENCE` or a new explicit reference-fill mode rather than misusing market-on-close.
- If a new mode is added, update `PatternEntryMode`, docs, tests, and CLI metadata.

Functional intent:

- Market fill means actual candle close or next open.
- Limit/reference fill means historical OHLC must touch the reference price.
- Backtest output must make the fill assumption auditable.

# Scope

- Update entry fill simulation contracts and call sites.
- Pass actual confirmation candle data from the canonical runner to the builder.
- Preserve existing requested-price execution after fill simulation.
- Add explicit metadata fields describing fill source and assumption.
- Add tests with confirmation close different from entry reference.

# Out of Scope

- Live limit order management.
- Order book fill probability.
- Maker/taker queue modeling.
- Changing detector pattern definitions.

# Requirements

- `MARKET_ON_CONFIRMATION_CLOSE` must use the actual confirmation candle close.
- `MARKET_ON_NEXT_OPEN` must use the actual next candle open.
- Reference/limit modes must require a valid reference price and OHLC touch.
- Synthetic candles must not be used to disguise reference fills as market fills.
- Metadata must expose `entry_mode`, `fill_price_source`, `confirmation_close`, `entry_reference`, and whether the fill was market or reference/limit.
- Legacy tests relying on old synthetic behavior must be updated deliberately.

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

- If confirmation close is `100` and risk plan entry price is `95`, market-on-confirmation-close fills at `100`.
- Limit-at-entry-reference fills at `95` only if a future candle range touches `95`.
- No-fill cases produce `SKIP` with clear metadata.
- Strategy engine receives explicit `requested_price` equal to the fill simulation result.
- JSON output and persisted metadata make the fill assumption clear.

# Required Tests

## Unit Tests

- Test each `PatternEntryMode` with confirmation close distinct from entry reference.
- Test no-fill expiration for limit modes.
- Test invalid custom/reference price behavior.

## Integration Tests

- Test canonical `_expand_raw_actions()` passes the actual confirmation candle.
- Test a pattern lifecycle run where market and reference modes produce different execution prices.

## Contract Tests

- Ensure `StrategyAction.requested_price` remains optional and backward-compatible.
- Document any new entry mode in public docs or task notes.

## Safety Tests

- Confirm no live orders or exchange endpoints are added.
- Confirm historical fill simulation remains deterministic and offline.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/patterns/test_entry_simulation.py tests/backtesting/test_strategy_engine.py
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
