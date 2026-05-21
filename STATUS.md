# Project Status

## Current Overall Phase
Phase 74: Multiple-testing and data-snooping control protocol completed.

## Current Step
Task `tasks/071_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md` completed with a dedicated multiple-testing/data-snooping governance protocol for pattern strategy research, including split protection, variant counting rules, baseline requirements, and conservative promotion/rejection rules.

## Current Goal
Apply conservative experiment-family governance before broad parameter sweeps so pattern strategy claims are controlled for false discovery and holdout leakage.

## Current Active Task
None (awaiting owner assignment).

## Last Completed Step (Short)
Task 071 completed: created `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md` and task document `tasks/071_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`, formalizing family-wise multiple-testing controls, locked holdout policy, and promotion evidence requirements across pattern/RSI/confluence research.

## Recommended Next Step
Create a follow-up implementation task for lightweight statistical helper utilities (`bonferroni_threshold`, `benjamini_hochberg_thresholds`, `count_strategy_variants`) plus tests to standardize protocol enforcement in research scripts and reports.

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
