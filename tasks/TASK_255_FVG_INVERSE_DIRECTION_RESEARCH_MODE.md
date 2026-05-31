# Task 255: FVG Inverse Direction Research Mode

# Goal

Add an explicit research-only mode that reverses FVG trade direction so bullish FVG entries can be tested as short candidates and bearish FVG entries can be tested as long candidates, without changing the default FVG strategy behavior.

# Source Requirement

Owner asked:

```text
궁금한건데 매수랑 매도를 반대로 하는 전략을 해봐 지금 fvg에서.
```

Interpreted requirement:

- Try a contrarian/inverse FVG strategy where buy and sell direction are reversed.
- Keep this as a backtest/research experiment, not live trading behavior.
- Make the behavior explicit in CLI/config/metadata so results are not confused with normal FVG.

# Extracted Roles

- Owner role:
  - Defines the research hypothesis: current FVG may be directionally wrong, so test the opposite side.
- Supporting roles:
  - Strategy/backtest role: adds opt-in inverse direction handling for FVG actions.
  - CLI/metadata role: exposes a clear flag and run metadata for inverse FVG mode.
  - Test role: proves default FVG direction is unchanged and inverse mode flips only FVG trade direction.
- Forbidden roles:
  - Do not change default FVG behavior.
  - Do not add live trading, signed exchange requests, credentials, account endpoints, or real order endpoints.
  - Do not add frontend controls unless a later frontend task explicitly requests them.
  - Do not invert non-FVG patterns unless explicitly assigned.
  - Do not use inverse mode to auto-select profitable parameters.

# Context

Recent FVG work added entry-mode experiments, FVG v2 diagnostics, FVG v2 channel entries/exits, channel overlays, cost metadata, and explicit standalone channel-scan semantics. The owner is now asking for a direct research comparison where FVG trade side is reversed.

The likely implementation surface is the canonical pattern action build path:

- FVG detector emits bullish/bearish events and raw entry actions.
- `_build_actions()` and `_expand_raw_actions()` convert raw actions into executable `StrategyAction`s.
- `build_pattern_trade_actions()` creates entry and exit actions from the selected `position_side`.
- FVG v2 channel mode has its own entry-side inference in `build_fvg_channel_trade_actions()` / `simulate_channel_retest_entry()` and should be handled carefully so the inverse behavior is explicit and tested.

# Scope

- Add a default-off CLI/config flag for inverse FVG direction, for example `--fvg-inverse-direction`.
- Apply inversion only for `FAIR_VALUE_GAP`.
- Preserve normal FVG behavior when the flag is absent.
- Ensure inverse mode is visible in strategy parameters, run metadata, action metadata, and diagnostics where relevant.
- Define how inversion applies to:
  - baseline FVG pattern action expansion,
  - FVG retest v2 entry modes,
  - FVG v2 channel mode.
- Add deterministic tests proving:
  - bullish FVG normal mode still enters LONG,
  - bearish FVG normal mode still enters SHORT,
  - bullish FVG inverse mode enters SHORT,
  - bearish FVG inverse mode enters LONG,
  - metadata labels the run/action as inverse/contrarian.

# Out of Scope

- No live trading.
- No exchange order/account endpoints.
- No frontend UI changes.
- No automatic strategy selection based on inverse-mode performance.
- No inversion for Order Block, Trendline, Cup and Handle, Diamond, Adam and Eve, or other patterns.
- No database schema migration unless existing JSON metadata cannot carry the required fields.
- No change to position sizing, costs, slippage, or account semantics except where existing side-specific logic already applies to the reversed side.

# Requirements

- Default behavior must remain unchanged.
- Inverse mode must be opt-in and clearly named as research-only.
- Inverse mode must reverse FVG `position_side` before executable action generation.
- Risk/exit plan direction must remain internally consistent with the reversed executable side.
- Action metadata must include fields such as:
  - `fvg_direction_mode`,
  - `fvg_inverse_direction_enabled`,
  - `original_position_side`,
  - `effective_position_side`,
  - `direction_inversion_reason`.
- CLI strategy parameter metadata must include the inverse direction setting.
- Persisted/API metadata should make inverse runs distinguishable from normal FVG runs through existing JSON metadata paths.
- FVG v2 channel behavior must be explicitly decided and tested:
  - either supported by reversing channel retest side and opposite boundary logic, or
  - blocked with a clear skip/validation reason if inversion is not compatible yet.
- Existing FVG v2 channel/default tests must remain stable.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read FVG strategy/detector source files relevant to raw action side selection.
- [x] Read FVG channel source if inverse behavior touches channel mode.
- [x] Read existing FVG action-builder/CLI tests.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- CLI accepts an explicit inverse FVG direction flag.
- Strategy parameters and run/action metadata identify inverse direction mode.
- Normal FVG direction tests still pass unchanged.
- Inverse FVG fixture produces opposite entry side from the same FVG event.
- Exit/risk behavior remains directionally consistent with the effective side.
- FVG v2 channel compatibility is either implemented and tested or deliberately blocked with a clear reason.
- No live trading behavior or exchange endpoint usage is introduced.

# Required Tests

## Unit Tests

- FVG side inversion helper or action-builder test for bullish-to-short and bearish-to-long.
- Metadata test for original/effective side fields.
- Default-off regression test.

## Integration Tests

- CLI metadata test for the inverse direction flag.
- Focused strategy runner test showing inverse mode creates reversed FVG executions on deterministic candles.

## Contract Tests

- API/metadata contract update if new persisted fields are exposed in saved-run metadata.
- Ensure existing metadata JSON paths can carry the inverse-mode fields without schema migration.

## Safety Tests

- Confirm no live trading, signed requests, credentials, account endpoints, or order endpoints are added.
- Confirm inverse mode is unavailable for non-FVG patterns unless a later task explicitly enables it.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
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

- Files changed:
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `docs/api/API_CONTRACT.md`
  - `tasks/TASK_255_FVG_INVERSE_DIRECTION_RESEARCH_MODE.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Added `--fvg-inverse-direction` as an explicit default-off research flag for `FAIR_VALUE_GAP`.
  - Added `strategy_config.parameters.fvg_direction` metadata using schema `fvg_direction_mode_config_v1`.
  - Added action metadata fields `fvg_direction_mode`, `fvg_inverse_direction_enabled`, `original_position_side`, `effective_position_side`, and `direction_inversion_reason`.
  - Baseline FVG inverse mode flips LONG to SHORT and SHORT to LONG before canonical action expansion.
  - Inverse risk plans use the original risk distance symmetrically on the opposite side and generate opposite-side R-multiple targets.
  - FVG channel inverse mode is deliberately blocked with `FVG_INVERSE_DIRECTION_CHANNEL_UNSUPPORTED` because channel boundary inversion needs a separate rule contract.
  - Non-FVG use of `--fvg-inverse-direction` fails fast.
- Tests added or updated:
  - Bullish FVG inverse flips LONG to SHORT.
  - Bearish FVG inverse flips SHORT to LONG.
  - Default-off FVG behavior remains normal.
  - FVG channel inverse mode emits a clear skip.
  - CLI metadata records inverse research mode.
  - Non-FVG inverse flag is rejected.
- Tests run:
  - `python -m py_compile quant_bitcoin/backtesting/strategy_postgres_runner_core.py quant_bitcoin/backtesting/pattern_action_builder.py`
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, signed requests, credentials, account endpoints, or exchange order endpoints added.
  - Default FVG behavior is covered by regression tests.
- Known limitations:
  - FVG v2 channel inverse behavior is not implemented; it is blocked explicitly until a separate channel-boundary inverse contract is assigned.
  - This does not evaluate profitability; it only enables the research mode.
- Recommended next task:
  - Run the approved 2026-05-20+ FVG backtest once normally and once with `--fvg-inverse-direction`, using the same cost profile and sizing, then compare gross PnL, total costs, trade count, and equity curve.
