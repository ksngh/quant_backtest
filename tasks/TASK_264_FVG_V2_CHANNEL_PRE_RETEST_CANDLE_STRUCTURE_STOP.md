# Task 264: FVG V2 Channel Pre-Retest Candle Structure Stop

# Goal

Change FVG v2 channel entry stops so each close-based channel retest uses the candle immediately before the retest candle as the structural stop reference.

# Source Requirement

Owner requested:

```text
아.. 손절라인 바꿀게.. 하락 추세선에서 숏치는 경우, 리테스트가 종가 기준으로 하락 선밑에 갔을때 숏포지션으로 매수하는거잖아? 그럼 손절라인은 그 리테스트 바로 직전 캔들의 고가로 해야해. 마찬가지로 상승 선 위로 리테스트 했을때 롱포지션을 잡는 거라면, 손절라인은 그 직전 캔들의 저가로 잡아야해.
```

Clean requirement:

- For SHORT entries from a downward/lower channel-line close retest, stop should be the high of the candle immediately before the retest/entry candle.
- For LONG entries from an upward/upper channel-line close retest, stop should be the low of the candle immediately before the retest/entry candle.
- Use the retest candle's immediately previous candle, not the channel boundary line, not the retest candle high/low, and not a multi-candle min/max.

# Extracted Roles

- Owner role:
  - Defines the intended stop rule for FVG v2 channel retest entries.
- Supporting roles:
  - Channel entry simulation role: calculates stop price from the pre-retest candle.
  - Metadata role: records stop source, pre-retest candle index/timestamp/high/low, and old line-stop diagnostic price if useful.
  - Test role: verifies LONG and SHORT stop references.
  - Documentation/API role: updates contract text for channel stop metadata.
- Forbidden roles:
  - Do not change channel geometry construction.
  - Do not change close-based retest confirmation from Task 259.
  - Do not change volume filter behavior from Tasks 261-262.
  - Do not change take-profit target projection unless necessary to preserve valid risk math.
  - Do not add live trading, exchange order execution, credentials, signed requests, account endpoints, or order endpoints.

# Context

Current FVG v2 channel behavior after recent tasks:

- Task 256 maps upper-boundary retests to LONG and lower-boundary retests to SHORT.
- Task 257 projects targets one channel width from entry price.
- Task 259 requires close-based retest confirmation.
- Task 261/262 applies close-volume filtering to both entry sides.

Current stop behavior is line-based:

- LONG stop uses the lower channel line.
- SHORT stop uses the upper channel line.

The owner now wants stop behavior to be pre-retest-candle structure based:

- LONG stop = low of the candle immediately before the retest entry candle.
- SHORT stop = high of the candle immediately before the retest entry candle.

# Scope

- Update `quant_bitcoin/patterns/fvg_channel.py` channel retest entry stop calculation.
- Preserve entry price as the close-based retest confirmation close.
- Preserve target policy as projected one channel width from entry price unless validation requires a skip.
- Add metadata:
  - `stop_source`
  - `pre_retest_candle_index`
  - `pre_retest_candle_timestamp`
  - `pre_retest_candle_low`
  - `pre_retest_candle_high`
  - old diagnostic line stop price if useful, for example `line_stop_price_diagnostic`.
- Update any API/frontend metadata contract text as needed.
- Add/adjust tests for LONG and SHORT.

# Out of Scope

- No live trading.
- No exchange account/order endpoints.
- No credentials or `.env` changes.
- No channel geometry redesign.
- No 15m/1h multi-timeframe entry alignment.
- No cash-currency conversion; that is Task 263.
- No frontend drawing changes unless metadata names are exposed in existing contract/types.

# Requirements

- LONG channel retest:
  - entry remains the close-based retest close.
  - stop price = immediately previous candle low.
  - stop source records `PRE_RETEST_CANDLE_LOW`.
- SHORT channel retest:
  - entry remains the close-based retest close.
  - stop price = immediately previous candle high.
  - stop source records `PRE_RETEST_CANDLE_HIGH`.
- If there is no previous candle available:
  - emit deterministic non-executable SKIP or preserve existing behavior only if explicitly justified in metadata.
- Risk per unit must be positive:
  - LONG requires stop below entry.
  - SHORT requires stop above entry.
  - invalid stop relation must emit deterministic SKIP metadata, not an executable trade.
- Existing close-volume and cost-aware filters must still run consistently with the new stop price.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/patterns/fvg_channel.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read relevant FVG channel tests.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- LONG channel retest stop uses the immediately previous candle low.
- SHORT channel retest stop uses the immediately previous candle high.
- Metadata makes the stop source and pre-retest candle explicit.
- Invalid/missing pre-retest stop data is handled deterministically.
- Existing close-based retest confirmation remains unchanged.
- Existing all-side volume filter remains unchanged.
- Tests cover both LONG and SHORT stop behavior.
- No live trading behavior or exchange order/account endpoint behavior is introduced.

# Required Tests

## Unit Tests

- LONG channel entry stop equals previous candle low.
- SHORT channel entry stop equals previous candle high.
- Missing previous candle handling.
- Invalid stop relation handling.

## Integration Tests

- Pattern action builder metadata uses the new stop price/risk per unit.
- Cost-aware entry filter uses the new stop price for net R/R where applicable.
- Existing FVG channel tests pass after expectation updates.

## Contract Tests

- Update README/API contract if stop metadata field names change.
- No database schema change expected if metadata remains JSON.

## Safety Tests

- Confirm no live trading controls, signed requests, exchange order endpoints, account endpoints, credentials, or real exchange order behavior are introduced.

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
pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
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

# Completion Notes

- Completed (2026-05-28): FVG v2 channel LONG entries now stop at the immediately previous retest candle low, SHORT entries stop at the immediately previous retest candle high, exit simulation uses that fixed stop price, and invalid/missing pre-retest stop data emits a deterministic non-executable skip.
- Verification passed: `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`; `pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine*.py -q`; `git diff --check`.
