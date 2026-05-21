# Task 065: Pattern Entry Simulation Contract

## Purpose
Define a reusable, deterministic, pure entry-simulation contract for completed-candle historical pattern research so entry assumptions are explicit and configurable before future net/backtest realism phases.

## Scope
- Add `quant_bitcoin/patterns/entry_simulation.py` with reusable contract types and pure helpers.
- Support entry modes:
  - `MARKET_ON_CONFIRMATION_CLOSE`
  - `MARKET_ON_NEXT_OPEN`
  - `LIMIT_AT_ENTRY_REFERENCE`
  - `LIMIT_AT_PATTERN_MIDPOINT`
  - `LIMIT_AT_PATTERN_BOUNDARY`
  - `LIMIT_AT_CUSTOM_PRICE`
- Support statuses:
  - `FILLED`
  - `NOT_FILLED`
  - `CANCELLED`
  - `INVALID`
- Implement:
  - `create_entry_plan_from_event(event, mode, direction, custom_price=None, max_wait_bars=None)`
  - `simulate_pattern_entry(plan, confirmation_candle, future_candles)`
- Add deterministic tests in `tests/patterns/test_entry_simulation.py`.

## Out Of Scope
- No transaction-cost integration.
- No exit simulation changes.
- No live trading or exchange calls.
- No persistence/database writes.

## Required Deliverables
1. `quant_bitcoin/patterns/entry_simulation.py` created with pure deterministic behavior.
2. `tests/patterns/test_entry_simulation.py` created with focused coverage.
3. `STATUS.md` updated with completion summary and recommended next step.
4. `PROJECT_HISTORY.md` appended with concise completion note.

## Acceptance Criteria
- Market-on-confirmation-close fills at confirmation close.
- Market-on-next-open fills at next candle open if available.
- Limit modes fill only when a future candle range touches the limit.
- `max_wait_bars` produces deterministic no-fill behavior via configured expiry status.
- Midpoint/boundary modes consume compatible event fields (`zone_mid`, `zone_low`, `zone_high`) and stay generic for future pattern events.
- Missing or invalid event fields produce clear invalid behavior.
- Required candle columns validated and unsorted candles rejected.
- Caller inputs are not mutated.
- Existing relevant pattern tests continue to pass.

## Verification
- `pytest tests/patterns/test_entry_simulation.py`
- `pytest tests/patterns/test_pattern_exit_simulation.py tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py`
- `pytest` (if feasible)
- `git diff --check`

## Notes
This task establishes the reusable entry simulation contract only; integration into existing pattern backtest workflows is a follow-up task.
