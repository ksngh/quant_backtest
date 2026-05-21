# Task 068: PATTERN_EVENT_STUDY_SCHEMA

## Goal
Define a reusable pattern event-study schema that separates pattern-event recording from forward-label analysis before strategy promotion.

## Scope
- Add reusable event-study dataclasses and serialization helpers.
- Add deterministic DataFrame conversion.
- Add tests for FVG-like and generic event conversion and optional metadata handling.
- Add focused documentation for event-study boundaries and no-look-ahead rules.

## Out of Scope
- Pattern extraction implementation changes.
- Forward-label calculation implementation.
- Strategy backtests and live/exchange behavior.

## Deliverables
- `quant_bitcoin/backtesting/pattern_event_study.py`
- `tests/backtesting/test_pattern_event_study.py`
- `docs/19_PATTERN_EVENT_STUDY_SCHEMA.md`

## Acceptance Criteria
- Canonical event-study record dataclass exists and supports current pattern event dataclasses.
- Forward-label config and label dataclasses exist for future labeling workflows.
- `pattern_event_to_study_record(...)` converts dataclass/mapping events safely with optional metadata.
- `records_to_dataframe(...)` produces deterministic column ordering.
- Tests cover FVG-like conversion, generic conversion, DataFrame conversion, and optional metadata.

## Verification
- `pytest tests/backtesting/test_pattern_event_study.py`
- Relevant pattern tests
- Full `pytest` if feasible
- `git diff --check`
