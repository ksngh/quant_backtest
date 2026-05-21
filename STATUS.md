# Project Status

## Current Overall Phase
Phase 70: Portfolio equity curve engine implemented.

## Current Step
Task `tasks/067_PORTFOLIO_EQUITY_CURVE_ENGINE.md` completed with reusable equity-curve construction and drawdown series utilities plus targeted tests.

## Current Goal
Provide reusable portfolio equity-curve series for candle-by-candle mark-to-market and drawdown analysis across backtest workflows.

## Current Active Task
None (awaiting owner assignment).

## Last Completed Step (Short)
Task 067 completed: added pure `quant_bitcoin.backtesting.equity_curve` module with standard-candle validation, generic trade normalization, deterministic equity-point generation, and drawdown-series calculation with focused unit coverage.

## Recommended Next Step
Create a follow-up task to integrate equity-curve outputs into persisted backtest graph/report read models and add higher-level risk-adjusted metrics built from the shared curve result.

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
