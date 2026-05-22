# Project Status

## Current Overall Phase
Phase 117: Task 097 canonical backtest regression/research suite completed.

## Current Step
Task 097 completed: added canonical persistence regression tests and verified project-wide regression suite.

## Current Goal
Prepare and execute Task 099 ledger segmentation/template-enforcement setup before broader ledger cleanup work.

## Current Active Task
Task 099 `LEDGER_SEGMENTATION_AND_TEMPLATE_ENFORCEMENT` (task document created; implementation not started).

## Last Completed Step (Short)
Task 097 completed: added strategy persistence adapter regression coverage for canonical equity graph values and trade metadata action/position-side preservation.

## Recommended Next Step
Execute Task 099 by segmenting root ledgers into recent-window + archive chunks and adding explicit TASK_TEMPLATE enforcement rule.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Frontend package install/build remains blocked in this environment by npm registry access restrictions.
- Full pytest currently has one unrelated existing failure in `tests/market_data/test_websocket_ingestion_cli.py` docker-compose connection-string assertion.

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
- Backend area status: `backend/STATUS.md`
- Frontend area status: `frontend/STATUS.md`
