# Goal

Fix the canonical pattern backtest path so engine-level sizing and explicit pattern quantity overrides propagate correctly from raw pattern actions to executable entry actions.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py` builds raw pattern actions, then `_expand_raw_actions()` expands entries through `build_pattern_trade_actions()`.
- `quant_bitcoin/backtesting/pattern_action_builder.py` currently emits pattern entry actions with a fixed `quantity=1.0`.
- `quant_bitcoin/backtesting/strategy_engine.py` treats an action-level quantity as higher priority than engine-level `PositionSizingConfig`.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/145_CANONICAL_CLI_PERSISTENCE_WIRING_FOR_SIZING_MARGIN.md`
- `tasks/116_PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/sizing.py`
- `quant_bitcoin/strategies/patterns.py`
- relevant backtesting CLI and engine tests

# Extracted Roles

- Owner role:
  - Backtest sizing contract owner.
  - Owns propagation of quantity intent from strategy filters/CLI to the execution engine.
- Supporting roles:
  - Strategy action role: preserves semantic action boundaries.
  - Pattern action-builder role: converts pattern lifecycle events without overriding sizing unintentionally.
  - Persistence/CLI role: records sizing metadata without changing trading behavior.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No exchange order/account endpoint calls.
  - No frontend/dashboard changes unless only docs/types need additive clarification.
  - No broad strategy rewrite beyond sizing propagation.

# Context

Code-level hints:

- Start in `_expand_raw_actions()` in `strategy_postgres_runner_core.py`. It receives the raw `StrategyAction` with `quantity` from `PatternEntryFilterConfig.quantity_override`, but does not pass it into `build_pattern_trade_actions()`.
- In `pattern_action_builder.py`, inspect the `StrategyAction(... quantity=1.0 ...)` creation. That fixed value should not be emitted when the intent is to let `StrategyEngineConfig.position_sizing` decide size.
- In `strategy_engine.py`, `_resolve_entry_quantity()` intentionally gives action-level quantity precedence. Preserve that design; fix the caller path that sets action quantities too eagerly.
- Add metadata such as `entry_quantity_source`, `engine_sizing_allowed`, `raw_action_quantity`, and `pattern_quantity_override` only if useful and non-breaking.

Functional intent:

- If the owner sets `--pattern-quantity-override`, that explicit quantity must reach the entry action.
- If no explicit quantity override exists, the entry action should allow engine sizing modes such as `fixed_quantity`, `cash_fraction`, or `target_notional` to work.
- Do not regress cash-bounded resizing/blocking behavior from Tasks 140-145.

# Scope

- Fix quantity propagation in the canonical pattern strategy CLI path.
- Ensure default pattern entries do not force `quantity=1.0` when engine sizing should own size.
- Preserve explicit raw action quantity overrides when intentionally provided.
- Preserve backward-compatible default behavior for `trade_quantity` under `fixed_quantity` sizing.
- Update JSON/persistence metadata only where it clarifies sizing source without schema-breaking changes.
- Add targeted regression tests for each sizing mode through the canonical CLI/action-builder/engine path.

# Out of Scope

- Risk-per-trade sizing based on stop distance; that is a separate future task.
- Portfolio optimization.
- Multi-symbol capital allocation.
- Frontend visualization changes.
- Live execution or exchange order sizing.

# Requirements

- `build_pattern_trade_actions()` must accept a nullable entry quantity or equivalent sizing-intent parameter.
- `_expand_raw_actions()` must pass the raw action quantity, when present, to the builder.
- Builder-created entry actions must set `quantity=None` when engine sizing should be used.
- Explicit `--pattern-quantity-override` must still override engine-level sizing.
- CLI output metadata must make it possible to audit whether quantity came from action override or engine config.
- Existing `PositionSizingMode.FIXED_QUANTITY`, `CASH_FRACTION`, and `TARGET_NOTIONAL` behavior must remain valid.
- Existing insufficient-funds resize/block semantics must remain valid.
- No strategy detector should need to know account cash to emit a pattern event.

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

- Running a canonical pattern backtest with `--position-sizing-mode cash_fraction --position-sizing-value 0.25` sizes entries from available cash rather than fixed `1.0` BTC.
- Running with `--position-sizing-mode target_notional --position-sizing-value 1000` sizes entries around the target notional.
- Running with `--pattern-quantity-override 0.02` produces an action-level entry quantity of `0.02` and does not use engine sizing for that entry.
- Default fixed-quantity behavior remains backward-compatible.
- Sizing metadata clearly indicates the quantity source.
- Existing relevant tests pass.

# Required Tests

## Unit Tests

- Add tests for `build_pattern_trade_actions()` showing:
  - no raw quantity leaves entry `quantity=None` or equivalent engine-owned sizing marker;
  - explicit raw quantity is preserved;
  - metadata records sizing source.
- Add tests for `_expand_raw_actions()` quantity propagation from raw pattern action to expanded entry action.

## Integration Tests

- Add canonical CLI/engine tests for `fixed_quantity`, `cash_fraction`, `target_notional`, and `pattern_quantity_override`.
- Verify final execution notional/quantity changes when sizing mode changes.

## Contract Tests

- Ensure `StrategyAction.quantity` remains backward-compatible.
- Ensure JSON output/persistence metadata changes are additive only.

## Safety Tests

- Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- Confirm strategy code still does not call exchange APIs.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_cli_persistence.py
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
