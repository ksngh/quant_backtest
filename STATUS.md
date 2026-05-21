# Project Status

## Current Overall Phase
Phase 71: Pattern event-study schema implemented.

## Current Step
Task `tasks/068_PATTERN_EVENT_STUDY_SCHEMA.md` completed with reusable pattern event-study dataclasses, conversion helpers, deterministic DataFrame serialization, and targeted tests.

## Current Goal
Provide reusable schema contracts for pattern event studies so research can separate detection events from forward labels before strategy promotion.

## Current Active Task
None (awaiting owner assignment).

## Last Completed Step (Short)
Task 068 completed: added pure `quant_bitcoin.backtesting.pattern_event_study` module with canonical event-study/label dataclasses, event-to-record conversion for current pattern dataclasses, deterministic record DataFrame conversion, and focused unit coverage.

## Recommended Next Step
Create a follow-up task to implement forward-label generation (fixed horizons + MFE/MAE + R-multiple hit order) with strict no-look-ahead guarantees and event-study dataset assembly CLI.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.

## Current Safety Boundary
- No live trading.
- No real Binance order execution.
- No API keys in code.
- No committed `.env` files.
- No signed exchange requests.
- No order/account endpoint usage.

## Focused Context Pointers
- Historical/completed ledger: `PROJECT_HISTORY.md`
- Future/deferred candidate work: `BACKLOG.md`
- If introduced later, area-focused status docs (for example backend/frontend) should be preferred for area tasks over full project history.
