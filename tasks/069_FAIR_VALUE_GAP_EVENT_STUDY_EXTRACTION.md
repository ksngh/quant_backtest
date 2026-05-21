# Task 069: FAIR_VALUE_GAP_EVENT_STUDY_EXTRACTION

## Goal
Implement a pure Fair Value Gap event-study extraction workflow that records only newly confirmed events using rolling completed-candle prefixes without look-ahead.

## Scope
- Add a public FVG event-study extraction function for deterministic event records.
- Reuse existing pattern event-study schema conversion.
- Enforce defensive standard-candle normalization and ascending timestamp validation.
- Suppress duplicates by stable `event_id`.
- Add focused tests for empty/insufficient input, deterministic bullish/bearish extraction, duplicate suppression, no-look-ahead behavior, input immutability, and clear validation errors.

## Out of Scope
- Forward-return labels, MFE/MAE labels, retest/fill labels.
- Trade simulation, entry/exit logic, risk management, costs/slippage.
- Live trading or exchange API behavior.

## Deliverables
- `quant_bitcoin/backtesting/pattern_event_study.py`
- `tests/backtesting/test_fvg_event_study.py`

## Acceptance Criteria
- Public extractor accepts candles plus optional symbol/timeframe/config.
- Extractor iterates rolling prefixes and includes only events with `end_index == current_index`.
- Duplicate events are suppressed by `event_id`.
- Extractor converts detector output to `PatternEventStudyRecord` deterministically.
- Missing required columns and unsorted timestamps raise clear errors.
- Input candle object is not mutated.
- Tests cover empty, insufficient, bullish and bearish valid samples (where practical), duplicate suppression, no-look-ahead confirmation timing, missing columns, unsorted timestamps, and non-mutating input.

## Verification
- `pytest tests/backtesting/test_fvg_event_study.py`
- relevant FVG detector tests
- full `pytest` if feasible
- `git diff --check`
