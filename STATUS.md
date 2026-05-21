# Project Status

## Current Overall Phase
Phase 67: Backtest transaction cost model contract implemented.

## Current Step
Task `tasks/064_BACKTEST_TRANSACTION_COST_MODEL_CONTRACT.md` completed with deterministic backtest transaction-cost contract and pure helper coverage.

## Current Goal
Provide reusable net-backtest transaction-cost primitives (fees, spread, slippage) without changing existing backtest engine behavior.

## Current Active Task
None (awaiting owner assignment).

## Last Completed Step (Short)
Task 064 completed: added pure `quant_bitcoin.backtesting.costs` contract with side/liquidity enums, validated config, side-aware effective execution price, deterministic gross-vs-cost breakdown, volatility-adjusted slippage with minimum floor, and targeted unit tests.

## Recommended Next Step
Create a follow-up task to integrate `TransactionCostConfig` usage into RSI and pattern backtest simulation paths as an opt-in net-backtest mode while preserving current default gross behavior.

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
