# Task 066 — INTRABAR_SEQUENCING_POLICY_AND_STRESS_MODES

## Why
OHLC candles do not encode the true intrabar path. When entry, stop, and target are all reachable in the same candle, backtests can overstate or understate performance if resolution is inconsistent.

## Scope
Create a reusable deterministic intrabar sequencing policy contract and tests for long/short ambiguity handling.

## In Scope
- Add `quant_bitcoin/backtesting/intrabar_policy.py` with deterministic pure helpers.
- Add policy enums/dataclasses:
  - `IntrabarSequencingMode`
  - `IntrabarTouch`
  - `IntrabarDecision`
  - `IntrabarPolicyConfig`
- Implement touch detection and ambiguity resolution for long and short.
- Add docs `docs/18_INTRABAR_SEQUENCING_POLICY.md`.
- Add targeted tests `tests/backtesting/test_intrabar_policy.py`.

## Out of Scope
- Rewriting full exit simulation engine behavior.
- Transaction costs, live trading, exchange API usage, persistence changes.

## Acceptance Criteria
1. Documentation clearly explains ambiguity, bias risk, and supported modes.
2. `intrabar_policy.py` provides deterministic pure functions and validates numeric/price invariants.
3. Ambiguous long and short same-candle cases are covered in tests.
4. `CONSERVATIVE` does not choose favorable outcomes when both stop and target are reachable.
5. `SKIP_AMBIGUOUS` returns explicit skipped/ambiguous decision.
6. Existing exit simulation tests continue to pass.

## Verification
- `pytest tests/backtesting/test_intrabar_policy.py`
- `pytest tests/patterns/test_pattern_exit_simulation.py`
- `pytest` (if feasible)
- `git diff --check`
