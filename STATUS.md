# Project Status

## Current Overall Phase
Phase 75: Multiple-testing helper utilities completed.

## Current Step
Task `tasks/072_MULTIPLE_TESTING_HELPER_UTILITIES.md` completed with deterministic helper utilities and tests for Bonferroni/BH thresholds and strategy-variant counting.

## Current Goal
Use reusable statistical helper utilities in research/backtest workflows so tested-variant counting and conservative thresholds are consistent and deterministic.

## Current Active Task
None (awaiting owner assignment).

## Last Completed Step (Short)
Task 072 completed: implemented `bonferroni_threshold`, `benjamini_hochberg_thresholds`, and `count_strategy_variants` in `quant_bitcoin/backtesting/multiple_testing.py` with focused unit tests in `tests/backtesting/test_multiple_testing_helpers.py`. Verification: `pytest -q` and `git diff --check` passed.

## Recommended Next Step
Assign and execute the next prioritized backlog/task item (for example event-study or robustness extensions) while keeping multiple-testing governance helpers as shared primitives.

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
