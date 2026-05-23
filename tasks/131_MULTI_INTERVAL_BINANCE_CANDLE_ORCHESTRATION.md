# Goal

Make Binance public candle collection operational for multiple supported minute intervals such as `1m`, `5m`, `15m`, and `30m` through a first-class orchestration workflow.

The existing downloader/backfiller/WebSocket code already supports several minute intervals. This task turns that capability into an explicit, tested, repeatable workflow instead of requiring one manual command per interval.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `quant_bitcoin/market_data/binance_downloader.py`
- `quant_bitcoin/market_data/binance_backfill.py`
- `quant_bitcoin/market_data/binance_backfill_cli.py`
- `quant_bitcoin/market_data/binance_websocket.py`
- `quant_bitcoin/market_data/websocket_ingestion_cli.py`
- `quant_bitcoin/persistence/`
- `db/init/001_schema.sql`
- `tests/market_data/`
- existing PostgreSQL persistence tests

# Extracted Roles

- Owner role:
  - Market-data orchestration owner.
  - Owns interval list parsing, multi-interval sequencing, and per-interval result reporting.
- Supporting roles:
  - Persistence role: stores candles by `source + symbol + interval + open_time` uniqueness.
  - CLI role: exposes multi-interval workflows.
  - Test role: verifies interval-specific behavior without live Binance dependency.
- Forbidden roles:
  - No strategy execution.
  - No order execution.
  - No account endpoints.
  - No signed requests.
  - No API keys.
  - No live trading.

# Context

The downloader/backfill/WebSocket modules validate minute intervals through a supported interval set and already store interval as part of the candle identity. However, operational workflows still require separate commands for each interval. The owner wants `5m`, `15m`, and similar intervals to be collected predictably.

# Scope

- Add a reusable multi-interval backfill runner.
- Add CLI support for interval lists, for example `--intervals 1m,5m,15m`.
- Preserve the existing single-interval `--interval` behavior.
- Ensure results are reported per interval.
- Ensure errors identify the failing interval.
- Ensure checkpoint behavior remains per `source/symbol/interval/mode`.
- Optionally add multi-interval readiness checks for WebSocket ingestion configuration.
- Do not make WebSocket ingestion multiplexing mandatory if separate processes are safer.

# Out of Scope

- Strategy execution on candle close.
- Live order execution.
- Testnet or live Binance account integration.
- New database schema unless the existing interval key cannot support the workflow.
- Futures/margin market-data endpoints.
- Non-minute intervals unless owner explicitly requests them in a separate task.

# Requirements

- Support interval list parsing with whitespace trimming and de-duplication while preserving requested order.
- Reject unsupported intervals before creating repositories or making network calls.
- Keep `1m`, `3m`, `5m`, `15m`, and `30m` behavior consistent with the current `MINUTE_INTERVALS` contract.
- Return deterministic JSON summary with `symbol`, `intervals`, and per-interval `results` entries.
- Preserve the existing single-interval CLI entrypoint.
- Add tests proving that the same `open_time` can exist for different intervals without collision.
- Add tests proving the runner calls the underlying backfiller once per interval.
- Add tests proving invalid intervals fail before any network call.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Multi-interval backfill can be invoked from CLI without manually running one command per interval.
- Existing single-interval backfill remains backward-compatible.
- Invalid interval list input fails deterministically and safely.
- Per-interval summaries include stored candle counts and fetched page counts.
- No order/account endpoint is called or introduced.
- Tests cover at least `5m` and `15m`.
- Project state files are updated after completion.

# Required Tests

## Unit Tests

- Test interval-list parser with `"1m,5m,15m"`.
- Test interval-list parser trims whitespace.
- Test interval-list parser de-duplicates repeated intervals.
- Test invalid interval is rejected.
- Test multi-interval runner calls the backfiller once per interval.
- Test failed interval reports interval-specific error.

## Integration Tests

- Test CLI with `--intervals 1m,5m,15m` using fake repository/backfiller.
- Test CLI preserves `--interval 1m` single-interval behavior.
- Test persisted candle uniqueness separates different intervals.

## Contract Tests

- Existing `BinanceHistoricalBackfiller.run(... interval="1m")` contract remains unchanged.
- Existing `quant-bitcoin-binance-backfill --interval 1m` remains valid.
- Market-data code remains market-data-only.

## Safety Tests

- Assert no order endpoint path is introduced.
- Assert no API key or signature parameter is accepted by new CLI options.
- Assert tests do not call real Binance endpoints.

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
pytest
```

Additional verification:

```bash
pytest tests/market_data/test_binance_backfill.py
pytest tests/market_data/test_binance_backfill_cli.py
pytest tests/market_data/test_binance_websocket.py
pytest tests/persistence
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
