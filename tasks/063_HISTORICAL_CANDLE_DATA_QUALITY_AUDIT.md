# Task 063: Historical Candle Data Quality Audit

## Purpose
Implement a deterministic, pure audit module for standard historical candle data quality so research and backtest conclusions rely on validated inputs.

## Scope
- Add `quant_bitcoin/market_data/data_quality.py` with report/config models and the public `audit_standard_candles(...)` API.
- Audit the standard candle schema (`timestamp`, `open`, `high`, `low`, `close`, `volume`) for:
  - missing required columns,
  - invalid timestamps,
  - non-ascending timestamps,
  - duplicate timestamps,
  - missing expected intervals (default `1m`),
  - invalid numeric OHLCV values,
  - invalid OHLC relationships (`high < low`, open/close outside range),
  - negative volume,
  - zero-volume count/ratio,
  - empty input handling,
  - optional expected start/end boundary coverage gaps.
- Add tests in `tests/market_data/test_data_quality.py`.
- Keep implementation research/backtest only (no exchange order/account calls, no API keys, no DB writes).

## Out Of Scope
- No live market fetch integration.
- No strategy or backtest engine changes.
- No PostgreSQL CLI integration beyond pure module/tests.
- No transaction cost/risk model changes.

## Required Deliverables
1. `quant_bitcoin/market_data/data_quality.py` created and publicly usable.
2. `tests/market_data/test_data_quality.py` created with deterministic unit coverage.
3. `STATUS.md` updated with completion summary and recommended next step.
4. `PROJECT_HISTORY.md` appended with concise completion note.

## Acceptance Criteria
- Valid standard candle inputs return a clean report.
- Missing required columns yield `ERROR` issue(s).
- Unsorted timestamps yield `ERROR` issue(s).
- Duplicate timestamps are detected.
- Missing 1-minute intervals are detected.
- Invalid OHLC relationships are detected.
- Negative volume is detected.
- Zero-volume candles are counted with count/ratio.
- Caller input is not mutated.
- Tests cover valid data, missing columns, unsorted timestamps, duplicates, gaps, invalid OHLC, negative volume, zero volume, and empty input.

## Verification
- Run targeted tests for the new module.
- Run full `pytest` if feasible.
- Run `git diff --check`.

## Notes
This task is strictly data-quality auditing for historical/paper research workflows and must preserve no-live-trading safety boundaries.
