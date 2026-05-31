# Task 263: Backtest Cash Currency Denomination Guardrail

# Goal

Make backtest cash denomination explicit for `BTCUSDT` runs so owner-entered KRW capital is not silently interpreted as USDT and does not distort sizing, costs, PnL, or equity.

# Source Requirement

Owner asked after reviewing cost behavior:

```text
야 cost 산정이 잘못된거 같아.. 왜냐면 bitcoin이 70000몇천불인데, 내가 starting cash로 써놓은거는 원화 기준이거든..? 상관없나 어차피?
```

Clean requirement:

- Clarify and guard the quote-currency assumption for strategy backtests.
- `BTCUSDT` prices imply `starting_cash` is denominated in USDT unless an explicit conversion feature is provided.
- If the owner wants KRW capital input, the CLI should support or warn about converting KRW to USDT before sizing.

# Extracted Roles

- Owner role:
  - Provides capital in KRW and expects the backtest to reflect that intent.
- Supporting roles:
  - CLI role: owns capital-currency flags, validation, warnings, and metadata.
  - Strategy runner role: passes converted quote-currency starting cash into the existing engine without changing engine accounting semantics.
  - Metadata role: records source cash currency, quote cash currency, conversion rate, and conversion source/manual override.
  - Documentation role: explains that `BTCUSDT` uses USDT quote cash.
  - Test role: verifies conversion/warnings and preserved explicit USDT behavior.
- Forbidden roles:
  - Do not add live FX lookup, network calls, credentials, exchange account endpoints, or order endpoints.
  - Do not change transaction-cost math unless needed only to label currencies.
  - Do not introduce live trading behavior.

# Context

Current Task 260 default owner profile uses:

```bash
--starting-cash 1000000
--position-sizing-mode cash_fraction
--position-sizing-value 0.10
```

For `BTCUSDT`, the backtest engine interprets this as `1,000,000 USDT`, not `1,000,000 KRW`. If the owner intended `1,000,000 KRW`, the equivalent quote-cash should be approximately:

```text
1,000,000 KRW / KRW_PER_USDT
```

The exact conversion rate must be explicit and auditable. The project should not fetch exchange rates from the network in this task.

# Scope

- Add explicit quote-currency/cash-denomination metadata for strategy backtests.
- Add a safe way to handle owner KRW capital, for example:
  - `--starting-cash-currency KRW`
  - `--quote-currency USDT`
  - `--krw-per-usdt <rate>`
  - convert `starting_cash` to quote-currency engine cash before running.
- Alternatively, if implementation chooses not to convert yet, add a hard warning/error when `BTCUSDT` is run with likely KRW-denominated owner defaults.
- Preserve existing behavior when `--starting-cash-currency USDT` or no conversion is explicitly selected.
- Ensure metadata shows both source and effective quote cash.
- Update README/API contract.
- Add tests.

# Out of Scope

- No live exchange-rate lookup.
- No exchange order/account endpoints.
- No credentials or `.env` changes.
- No database schema migration unless existing JSON metadata is insufficient.
- No changes to FVG channel geometry, entry logic, stop/target math, or volume filters.
- No frontend UI unless a future task explicitly asks for it.

# Requirements

- For `BTCUSDT`, the engine must continue accounting in the quote currency, USDT.
- If owner supplies KRW starting cash, conversion must be explicit:
  - source cash amount
  - source currency `KRW`
  - quote currency `USDT`
  - `krw_per_usdt`
  - effective quote starting cash
- Starting-cash display/metadata must make the distinction obvious.
- Position sizing must use effective quote cash, not the raw KRW amount.
- Cost totals must remain in quote currency unless explicitly converted for display.
- Existing USDT behavior must remain available.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read strategy engine sizing/cost metadata code.
- [x] Read README/API contract sections for cash/cost fields.
- [x] Decide whether this task converts KRW to USDT or only adds guardrails/warnings.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Backtest output clearly states the effective quote-currency starting cash.
- KRW-denominated owner input cannot silently be treated as USDT.
- If conversion is implemented, sizing uses converted quote cash.
- If conversion is not implemented, the CLI emits a clear error/warning requiring explicit USDT cash or explicit conversion parameters.
- Metadata records cash denomination and conversion assumptions.
- Existing USDT workflows still pass tests.
- No live FX lookup, exchange order/account endpoint, credential, or live trading behavior is introduced.

# Required Tests

## Unit Tests

- Cash-denomination metadata builder.
- KRW-to-USDT conversion or guardrail validation.
- Existing USDT default behavior.

## Integration Tests

- CLI output includes source/effective quote cash metadata.
- Position sizing uses effective quote cash when conversion is enabled.

## Contract Tests

- README/API contract updated for cash denomination fields.
- No database schema change expected if JSON metadata is sufficient.

## Safety Tests

- Confirm no network exchange-rate lookup, signed request, account endpoint, order endpoint, credentials, or live order behavior.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine*.py -q
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

- Completed (2026-05-28): Added explicit `--starting-cash-currency`, `--quote-currency`, and `--krw-per-usdt` CLI handling. KRW input is converted to effective USDT quote cash before engine sizing, output/persistence metadata records source and effective quote cash, and existing USDT behavior is preserved.
- Follow-up completed (2026-05-28): Changed the CLI and owner FVG default cash input to KRW with `--krw-per-usdt 1500`, so the default `--starting-cash 1000000` is treated as KRW and converted to approximately `666.67` USDT quote cash. Direct USDT quote-cash workflows remain available with `--starting-cash-currency USDT`.
- Verification passed: `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`; `pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine*.py -q`; `git diff --check`.
- Follow-up verification passed: `pytest tests/backtesting/test_pattern_postgres_runner_cli.py -q`; `pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine*.py -q`; `git diff --check`.
