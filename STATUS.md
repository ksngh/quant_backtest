# Project Status

## Current Overall Phase
Phase 129: Task 109 FVG cache naming alignment completed.

## Current Step
Task 109 completed: renamed pattern cache ownership to FVG-specific module with compatibility re-export.

## Current Goal
Keep optimized FVG cache ownership explicit under `quant_bitcoin.backtesting.fvg_detection_cache` while preserving compatibility imports.

## Current Active Task
No active implementation task (await owner assignment of Task 110+).

## Last Completed Step (Short)
Task 109 completed: moved FVG cache canonical imports to `quant_bitcoin.backtesting.fvg_detection_cache` and retained `pattern_detection_cache` as compatibility re-export.

## Recommended Next Step
Recommended next task: Task 110 `PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT`.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Frontend package install/build remains blocked in this environment by npm registry access restrictions.

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
