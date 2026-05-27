# Task 233: FVG Retest V2 CLI Diagnostics and Parameter Grid

# Goal

Expose FVG v2 research controls through the canonical CLI and extend diagnostics so entry, trend, Fibonacci, liquidity-target, stop-mode, and reaction-trigger hypotheses can be compared without mutating persistence behavior unexpectedly.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - CLI/backtest diagnostics owner for FVG v2 research controls.
- Supporting roles:
  - Pattern strategy role.
  - Parameter-grid role.
  - Performance metrics role.
  - Documentation/API contract role.
  - Frontend diagnostics role if output schema is displayed later.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The project already has FVG entry-mode comparison and parameter-grid infrastructure. FVG v2 adds more research axes: multi-timeframe trend score, Fibonacci confluence, retest trigger, liquidity targets, and stop modes. This task makes them runnable and attributable from CLI output.

# Scope

- Add CLI flags for FVG v2 controls: multi-timeframe trend scoring, EMA periods, timeframe weights, trend threshold, Fibonacci confluence, retest trigger, liquidity-target requirement, stop mode, and max wait bars.
- Keep all controls opt-in or tied to an explicit `FAIR_VALUE_GAP_RETEST`/FVG v2 preset.
- Extend JSON diagnostics with counts and outcomes by entry mode, trigger type, trend alignment, Fibonacci confluence, liquidity-target availability, stop mode, bars waited, MFE/MAE, hit rate, average R, expectancy, and missed-trade reasons.
- Extend or add parameter-grid support so declared FVG v2 parameter ranges can be enumerated without automatically selecting a winner.
- Ensure reproducibility metadata includes all selected FVG v2 settings and config hashes.
- Keep persistence behavior read-only unless existing runner persistence explicitly records completed backtest payloads as before.

# Out of Scope

- No implementation of the underlying EMA/Fibonacci/entry/target/stop logic if prior tasks are incomplete.
- No automatic model selection, optimizer, or promotion decision.
- No frontend changes unless explicitly limited to read-only metadata display in a later or same scoped sub-step.
- No live trading or exchange integration.

# Requirements

- CLI validation must reject incompatible options, for example custom price without custom-price entry mode.
- All diagnostics must be JSON-serializable and stable for snapshot tests.
- Comparison output must distinguish bad performance causes: late market entry, no-fill retest, touch-without-reaction, weak follow-through, trend-misaligned trades, no liquidity target, or stop-mode sensitivity.
- Parameter-grid output must record attempted parameter combinations and not hide losing variants.
- Existing `--compare-fvg-entry-modes` behavior must remain backward compatible.
- Warnings must identify zero-cost assumptions, market-regime disabled state, candle-continuity disabled state, and FVG v2 experimental scope when applicable.

# Status Tracking

## Execution Notes

- Assumption: Task 233 exposes selected FVG v2 research controls as stable metadata and grid axes without automatically selecting profitable variants.
- Assumption: underlying feature behavior remains opt-in and persistence behavior remains unchanged.
- Blockers: none for Task 233.
- Safety: no live trading flags, exchange/network calls, order/account endpoints, keys, or `.env` behavior were added.

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Added FVG v2 CLI settings metadata and diagnostics schema.
- Added `--fvg-entry-trigger` CLI metadata support and FVG v2 research flags.
- Extended parameter grid support for `entry.trigger` and existing FVG v2 risk/dataclass axes.
- Updated API contract and README research-only notes.
- Verification:
  - `pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_parameter_grid.py tests/backtesting/test_timing_diagnostics.py`

# Acceptance Criteria

- CLI can run baseline FVG unchanged.
- CLI can run FVG retest v2 with trend score, Fibonacci, liquidity target, and stop mode flags.
- Diagnostics include aggregate counts for each new filter/trigger axis.
- Parameter-grid/dry-run can enumerate FVG v2 declared parameter combinations.
- Output reproducibility metadata fully records FVG v2 settings.

# Required Tests

## Unit Tests

- `tests/backtesting/test_pattern_postgres_runner_cli.py` covers argument parsing, incompatible option errors, and selected metadata.
- `tests/backtesting/test_pattern_parameter_grid.py` covers FVG v2 grid expansion and max-combination guardrails.
- JSON metadata/hash tests cover new reproducibility fields.

## Integration Tests

- Deterministic CLI run over synthetic candles produces FVG v2 diagnostics with expected keys.
- Mode comparison test confirms no-fill and filled entries are counted correctly for retest triggers.
- Parameter-grid integration test confirms all attempted variants are reported.

## Contract Tests

- Update `docs/api/API_CONTRACT.md` and README command examples for new CLI flags and diagnostic keys.
- Document experimental/research-only scope and no automatic promotion.

## Safety Tests

- CLI must not expose live trading flags, account endpoint calls, or signed exchange behavior.
- Tests verify no order endpoint imports are introduced in backtesting CLI modules.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_parameter_grid.py tests/backtesting/test_timing_diagnostics.py
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
