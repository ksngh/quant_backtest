# Execution Readiness Safety Audit

Task 170 audit date: 2026-05-24.
Task 224 pattern boundary re-audit date: 2026-05-24.

## Verdict

The project is **not ready for live trading**. Live order execution remains
blocked by Task 138 until the owner explicitly approves a future live-execution
task and that task implements the required fail-closed controls.

Current execution support is limited to:

- local paper execution from canonical `OrderIntent` objects;
- closed-candle realtime dry-run or paper-mode execution;
- Binance Spot **testnet-only** signed order requests with fake-HTTP test
  coverage and explicit testnet credential requirements;
- execution-quality metrics from submitted execution reports.

No current backend or frontend API exposes order submission controls. Strategy,
backtest, and market-data code must remain separate from execution clients.

## Task 224 Pattern Research Boundary Re-Audit

Pattern research code remains **backtest/paper-only**. The Task 224 audit
covered `quant_bitcoin/strategies/` and `quant_bitcoin/backtesting/` and found
no direct imports from `quant_bitcoin.execution`, no embedded Binance order
endpoint strings, and no testnet credential environment keys in those strategy
or backtesting modules.

Pattern strategy, detector, score, risk, cost, walk-forward, report, and
diagnostic outputs are research artifacts. They may describe simulated order
intent, simulated fills, stop/target policies, costs, and paper/live readiness
gaps, but they must not submit orders, sign requests, read API secrets, or call
exchange order/account endpoints.

This boundary is covered by `tests/safety/test_pattern_live_boundary.py`, which
statically checks the audited modules for execution-client imports, signed-order
endpoint constants, testnet credential keys, and signed-request helper usage.

## Current Safety Boundary

- `PaperExecutionClient` mutates only in-memory paper balances and positions.
- `RealtimeCandleCloseRunner` consumes stored candles and an injected execution
  client; it does not fetch Binance data directly and defaults to `dry_run=True`.
- `BinanceSpotTestnetExecutionClient` requires
  `BINANCE_TESTNET_API_KEY` and `BINANCE_TESTNET_API_SECRET`, rejects the live
  Binance base URL, requires `testnet.binance.vision`, and allowlists only
  `/api/v3/order`.
- Product policy blocks spot/testnet short entries before request creation.
- Ordinary tests use fake HTTP clients and fake credentials.
- Repository status still records live trading, real Binance order execution,
  signed live requests, and order/account endpoint usage as blocked.

## Not Production Ready

The following capabilities are missing or incomplete for real execution:

| Area | Current status | Required before live trading |
| --- | --- | --- |
| Owner approval | Task 138 remains blocked | Explicit owner approval recorded in task/status docs |
| Live enablement | No live client enabled | Non-default explicit live mode with startup readiness checks |
| Kill switch | Not implemented for live mode | Runtime kill switch that fails closed before request signing |
| Max notional | Not implemented for live mode | Per-order and daily notional caps |
| Pattern strategy boundary | Backtest/paper-only; no execution-client imports in strategy/backtesting modules | Keep strategy/backtest modules isolated from execution clients and prove this in PR safety tests |
| Stale data | Not implemented for live mode | Candle age and clock-skew checks before intent submission |
| Duplicate orders | Deterministic client IDs exist | Live duplicate client-order-id/idempotency policy |
| Order book/fill model | Backtest/paper approximations only | Pre-trade liquidity and expected-fill checks |
| Partial fills | Reports can represent fills | Live partial-fill polling/reconciliation policy |
| Cancel/replace | Not implemented | Cancel, replace, timeout, and orphan-order handling |
| Rate limits | Not implemented | Exchange rate-limit budgeting and backoff |
| Reconnect/recovery | Realtime runner has local idempotency | Durable restart recovery and execution reconciliation |
| Exchange filters | Not implemented | Min notional, lot size, step size, and tick size validation |
| Fees | Simulated and reported fees exist | Real fee asset normalization policy without guessing |
| Monitoring | Not implemented | Alerts for rejects, stale data, disconnects, and drawdown |
| Secrets | Testnet env vars only | Live credential storage, rotation, and redaction policy |
| Funding/margin/liquidation | Explicitly unsupported | Must remain out of scope for spot live; separate task for margin/futures |

## Required Live Readiness Checklist

Before any live order can be submitted, a future task must prove all of the
following:

- live trading disabled by default;
- no `ENABLE_LIVE_TRADING=true` or equivalent default;
- explicit owner approval recorded in the task and `STATUS.md`;
- live endpoint allowlist separated from testnet endpoint allowlist;
- credentials fail closed when absent or malformed;
- kill switch checked before request signing;
- per-order max notional and daily notional/loss limits;
- duplicate client-order-id behavior is deterministic;
- spot live rejects `ENTER_SHORT`, `EXIT_SHORT`, margin, futures, and leverage;
- exchange symbol filters validated before request submission;
- stale candle/clock-skew checks block execution;
- partial-fill, cancel/replace, timeout, and orphan-order recovery policies;
- durable execution reconciliation after reconnect/restart;
- structured logging of every intent/report without secrets;
- ordinary tests make no real network calls;
- PR review confirms strategy and market-data layers do not import live clients.

## Follow-Up Task Candidates

- `LIVE_EXECUTION_KILL_SWITCH_AND_MAX_NOTIONAL_GUARDS`
- `LIVE_EXECUTION_SYMBOL_FILTER_AND_STALE_DATA_PRECHECKS`
- `LIVE_EXECUTION_IDEMPOTENCY_AND_RESTART_RECONCILIATION`
- `LIVE_EXECUTION_CANCEL_REPLACE_AND_PARTIAL_FILL_POLICY`
- `LIVE_EXECUTION_MONITORING_ALERTING_AND_SECRET_POLICY`

These are prerequisites for unblocking Task 138. They do not authorize live
trading by themselves.
