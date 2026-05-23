# Goal

Run strategies automatically when a finalized candle is observed, using the existing Binance public WebSocket candle ingestion path and the new canonical order-intent/paper-execution contract.

This task enables real-time dry-run/paper strategy execution. It must not place real orders.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/market_data/binance_websocket.py`
- `quant_bitcoin/market_data/websocket_ingestion_cli.py`
- `quant_bitcoin/market_data/postgres_provider.py` or the current PostgreSQL candle provider location
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/execution/`
- `quant_bitcoin/risk/`
- `tests/market_data/test_binance_websocket.py`
- `tests/backtesting/`
- `tests/execution/`

# Extracted Roles

- Owner role:
  - Real-time runtime owner.
  - Owns closed-candle trigger flow, idempotency, strategy invocation, and dry-run/paper execution handoff.
- Supporting roles:
  - Market-data role: persists closed candles.
  - Strategy role: evaluates candles and emits semantic actions.
  - Execution role: accepts canonical order intents in dry-run/paper mode.
  - Risk role: may block or approve intents with deterministic checks.
- Forbidden roles:
  - No live order execution.
  - No signed Binance requests.
  - No account endpoint calls.
  - No futures/margin implementation.
  - No API key loading.

# Context

The WebSocket ingestor currently stores closed candles only. The owner wants the system to run every minute or on each relevant closed candle. This requires a runtime component that reacts after candle persistence, loads the recent candle window, runs a strategy, converts actions to order intents, and sends them to dry-run or paper execution.

# Scope

- Add a `RealtimeCandleCloseRunner` or equivalent runtime service.
- Support one symbol/interval at first.
- Trigger only on finalized closed candles.
- Load recent candles from PostgreSQL after persistence.
- Run one configured strategy.
- Convert actions to order intents.
- Execute through dry-run or paper execution only.
- Record structured runtime output for debugging.
- Add idempotency so the same candle does not produce duplicate executions after reconnect or duplicate upsert.
- Add CLI command for real-time dry-run/paper mode if appropriate.

# Out of Scope

- Binance live or testnet order execution.
- Multi-strategy portfolio runtime.
- Distributed scheduler.
- ML model inference.
- Dashboard changes.
- Futures/margin execution.
- Startup gap fill beyond invoking the existing backfill workflow separately.

# Requirements

- Runner must not execute on open/in-progress WebSocket klines.
- Runner must be idempotent by `source/symbol/interval/open_time/strategy_key` or an equivalent deterministic key.
- Runner must support bounded test mode.
- Runner must support dry-run mode that only logs or returns actions/intents/reports.
- Runner must support paper mode through the canonical paper execution client.
- Runner must use stored candle data, not raw WebSocket messages, as the strategy input source.
- Runner must preserve market-data boundary: WebSocket ingestion remains able to run without strategy execution.
- Runtime output must include candle identity, strategy key, actions, order intents, execution reports, and warnings/errors.

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

- A fake closed-candle event can trigger strategy evaluation exactly once.
- Duplicate closed-candle events do not create duplicate paper executions.
- Open WebSocket klines do not trigger strategy evaluation.
- Dry-run mode creates no state mutation.
- Paper mode creates deterministic execution reports.
- No exchange account/order endpoint is called.
- Existing WebSocket ingestion remains market-data-only unless the new runtime is explicitly used.

# Required Tests

## Unit Tests

- Test runner ignores open/in-progress candle events.
- Test runner triggers on closed candle event.
- Test runner loads recent candles after persistence.
- Test runner emits order intents from strategy actions.
- Test idempotency prevents duplicate execution for same candle.
- Test dry-run mode does not mutate paper balances.
- Test paper mode records execution report.

## Integration Tests

- Test WebSocket parsed closed candle can flow into runner with fake repository/provider.
- Test CLI bounded run with fake connector and fake execution client.
- Test reconnect/duplicate message does not duplicate intent execution.

## Contract Tests

- WebSocket ingestion remains usable without strategy runtime.
- Strategy runtime does not fetch Binance directly.
- Execution client interface is used instead of direct paper-trader mutation.

## Safety Tests

- No API key loading.
- No signed request code.
- No Binance order/account endpoint usage.
- No live trading mode.

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
pytest tests/market_data/test_binance_websocket.py
pytest tests/execution
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
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
