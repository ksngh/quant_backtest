# Task 072: MULTIPLE_TESTING_HELPER_UTILITIES

## Goal
Implement lightweight, deterministic statistical helper utilities that operationalize the repository multiple-testing protocol in reusable code for research scripts and reports.

## Scope
Implementation task for pure helper functions and tests:
- Add `bonferroni_threshold(...)` helper.
- Add `benjamini_hochberg_thresholds(...)` helper.
- Add `count_strategy_variants(...)` helper.
- Add focused unit tests for normal and boundary behavior.
- Keep implementation pure (no exchange/network/database/live-trading dependencies).

## Out Of Scope
- Bootstrap reality-check implementation.
- Deflated Sharpe ratio implementation.
- Backtest engine contract redesign.
- Pattern detector logic changes.
- Live trading or real exchange order execution.
- Dashboard/API/database/scheduler additions.

## Proposed Ownership Boundary
- Allowed modules: `quant_bitcoin/backtesting/` or `quant_bitcoin/research/` utility layer (owner chooses final file path while preserving existing architecture conventions).
- Tests under `tests/backtesting/` or aligned test area matching selected module path.
- No public interface redesign for existing backtest runner contracts.

## Required Deliverables
1. Pure helper implementations:
   - `bonferroni_threshold(alpha: float, tested_variants: int) -> float`
   - `benjamini_hochberg_thresholds(alpha: float, tested_variants: int) -> list[float]`
   - `count_strategy_variants(search_space: Mapping[str, Sequence | set | tuple | list | range | int]) -> int`
2. Unit tests covering nominal and edge cases.
3. `STATUS.md` updated on completion with verification summary and next step.
4. `PROJECT_HISTORY.md` appended with concise completion note after acceptance.

## Functional Expectations

### 1) `bonferroni_threshold`
- Computes family-wise Bonferroni cutoff as `alpha / tested_variants`.
- Must reject invalid `alpha` (`<= 0` or `> 1`) with deterministic `ValueError`.
- Must reject invalid `tested_variants` (`<= 0`) with deterministic `ValueError`.

### 2) `benjamini_hochberg_thresholds`
- Returns monotonic non-decreasing BH critical values for ranks `i=1..m` as `(i / m) * alpha`.
- Input checks:
  - invalid `alpha` (`<= 0` or `> 1`) -> `ValueError`
  - invalid `tested_variants` (`<= 0`) -> `ValueError`
- Output length must equal `tested_variants`.

### 3) `count_strategy_variants`
- Deterministically counts declared variant cardinality from a pre-declared search-space mapping.
- Expected behavior:
  - each key contributes multiplicative cardinality
  - sequence-like values use unique declared candidates only (deduplicated)
  - scalar integers may represent explicit cardinality only when clearly documented and positive
- Must reject:
  - empty search space
  - zero-cardinality dimensions
  - negative or non-finite cardinalities
  - unsupported value types
- Must preserve type stability and return plain `int`.

## Acceptance Criteria
- All three helpers exist with docstrings and deterministic validation behavior.
- Unit tests cover:
  - valid nominal cases
  - input-validation failures
  - empty-input/search-space failures
  - sorting/ordering stability where applicable
  - output type stability (`int` for variant count; list length and monotonicity for BH thresholds)
- `pytest` passes for new/updated tests.
- Safety posture unchanged (no live-trading behavior, no exchange order endpoints).

## Verification
- `pytest -q`
- `git diff --check`
- Optional targeted run: `pytest -q tests/backtesting -k "multiple_testing or variant"`

## Notes
This task intentionally implements only lightweight protocol-enforcement helpers so research outputs can consistently report tested-variant counts and conservative significance thresholds before broader parameter sweeps.
