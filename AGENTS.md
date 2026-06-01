# Project

This is a Python Bitcoin quantitative trading project.

The project starts small and evolves gradually. The current focus is candle data, technical-analysis strategies, basic backtesting, and paper trading. Live trading and risk management are later phases.

# Mandatory State-Driven Workflow (Execute First)

- Every agent must read `BACKLOG.md`, `PROJECT_HISTORY.md`, and `STATUS.md` before doing any work.
- Every agent must find and read the relevant `task.md` before any implementation, refactoring, testing, design, documentation, or file modification.
- If no relevant `task.md` exists, the only allowed action is to create or update the appropriate `task.md`, then stop.

Required execution order:
- Read `BACKLOG.md`
- Read `PROJECT_HISTORY.md`
- Read `STATUS.md`
- Find the relevant `task.md`
- If no relevant `task.md` exists, create it and stop
- If a relevant `task.md` exists, execute only the work defined in that task
- For strategy/model/backtest work, find and read the relevant `docs/strategy/*.md` after the task file and before implementation or execution
- If a strategy/model/backtest task exists but no relevant strategy document exists, create or update only the appropriate `docs/strategy/*.md`, update state files, then stop
- Update `STATUS.md` after execution
- Append progress to `PROJECT_HISTORY.md` after execution
- Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split
- Clearly record the next task

Progress tracking is mandatory for every task:
- current active task
- completed work
- remaining work
- blocked items
- next task

- Agents must not start the next task automatically unless a new relevant `task.md` exists for that next task.
- Agents must not silently expand scope beyond the current `task.md`.

Absolute rules:
- No `task.md`, no execution.
- No state-file reading, no execution.
- No relevant `docs/strategy/*.md`, no strategy/model/backtest implementation or execution.
- No state-file update, no completion.

# Current Scope

- project setup
- market data contract
- CSV/local data provider
- RSI strategy
- basic backtest
- paper trader
- Binance historical candle downloader later

# Out of Scope by Default

Codex must not implement the following unless an assigned future task explicitly requests them:

- live trading
- real Binance order execution
- risk management
- dashboard
- database
- scheduler
- FastAPI
- Streamlit
- Docker
- machine learning
- futures
- leverage
- portfolio optimization

# Working Rules

- Read `AGENTS.md` before working.
- Read relevant docs before working.
- Read the assigned task file before coding.
- For any strategy/model/backtest implementation, parameter tuning, validation run, or reportable research run, read the relevant `docs/strategy/*.md` before coding or execution.
- Strategy documents live under `docs/strategy/` and must be created from `docs/strategy/STRATEGY_TEMPLATE.md` when missing.
- Every newly created task document must follow `tasks/TASK_TEMPLATE.md` (section structure/checklists/verification blocks).
- Ledger segmentation rule: archive `BACKLOG.md` and `PROJECT_HISTORY.md` in fixed **50-task ranges** (for example `*_task_001_050.md`, `*_task_051_100.md`) and keep root files as recent high-signal windows with archive pointers.
- For consistent command handling and reusable prompt formats, follow `docs/10_CODEX_COMMAND_GUIDE.md`.
- Do not proceed with implementation or documentation changes unless a specific task document is assigned.
- If no task document is assigned, stop and ask the project owner to assign or create a task, even if the user prompt is written as a direct command.
- If the assigned task asks for strategy/model/backtest work and the relevant strategy document is missing, create or update only the strategy document, update state files, and stop before running any backtest or changing strategy code.
- If implementation changes strategy logic, risk logic, cost assumptions, execution assumptions, validation windows, or research/live-trading boundary, update the relevant strategy document in the same task.
- If the requirement is unclear, extract roles and write assumptions before implementation.
- Make small, incremental changes.
- Do not expand scope beyond the assigned task.
- Do not modify unrelated files.
- Add or update tests when implementation tasks are performed later.
- Run verification commands when possible.
- Summarize changed files, behavior added, tests run, and known limitations.

# Project Status Tracking

- Codex must read `STATUS.md` before starting implementation tasks.
- Codex must use short `STATUS.md` as the current-state pointer (phase, step, active task, blockers, and safety boundary).
- Codex must use `PROJECT_HISTORY.md` only when historical context is relevant to the assigned task.
- Codex must use `BACKLOG.md` when selecting, creating, or discussing future candidate work.
- Codex should prefer focused backend/frontend status docs when they exist, rather than loading full project history by default.
- Codex must update `STATUS.md` when project state changes.
- When a task is completed, Codex must update `STATUS.md` and append a concise completion note to `PROJECT_HISTORY.md`.
- If completion creates new future work, Codex must update `BACKLOG.md` with follow-up candidate items; if a backlog item is completed, Codex must remove or mark it as completed in `BACKLOG.md`.
- Codex must not mark phases, steps, or checklist items complete unless acceptance criteria and verification are satisfied.
- If completion is uncertain, Codex must leave the item open and record the uncertainty in `STATUS.md`.


# Focused Context Rule

Codex must begin with:
- `AGENTS.md`
- short root `STATUS.md`
- assigned task file
- relevant workflow docs
- relevant source/test files for the assigned area

For backend tasks, Codex should prefer:
- root `STATUS.md`
- assigned backend/API task
- `docs/api/API_CONTRACT.md` if present
- backend-relevant source and tests
- backend-focused status docs if present

For frontend tasks, Codex should prefer:
- root `STATUS.md`
- assigned frontend task
- `docs/api/API_CONTRACT.md` if present
- `frontend/STATUS.md` if present
- frontend-relevant source and tests

Codex must not load full `PROJECT_HISTORY.md` by default for backend/frontend tasks unless historical context is explicitly relevant.

# Requirement-to-Implementation Workflow

Raw requirement
-> Clean requirement
-> Role extraction
-> Responsibility boundary check
-> Task document
-> Strategy document for model/backtest work
-> Test plan
-> Implementation
-> Codex self-review
-> PR review
-> Decision/doc update if needed

# Parallel Work Rule

- Codex may use parallelism only for independent leaf tasks.
- Codex must not parallelize shared contract changes.
- Codex must not rename or redesign public interfaces during a parallel batch.
- If a shared contract change seems necessary, Codex must stop and report it instead of silently changing it.

Safe parallel examples:

- CSV provider
- RSI strategy
- PaperTrader
- isolated documentation review

Unsafe parallel examples:

- market data contract changes
- signal contract changes
- base strategy interface changes
- backtest result model changes
- project package layout changes

# Safety Rules

- Do not hardcode API keys.
- Do not commit `.env` files.
- Do not place real orders unless a future task explicitly asks for real order execution.
- Paper trading must never call real exchange order APIs.
- Binance candle downloading is allowed only for data collection, not order execution.
- Strategy code must never call exchange APIs.
- Tests must not call real exchange order endpoints.
- Do not create `ENABLE_LIVE_TRADING=true` defaults.

# Codex Self-Review Requirement

Before finishing any implementation task, Codex must perform a self-review using `reviews/CODEX_SELF_REVIEW.md`.

Codex must check:

- Did I implement only the assigned task?
- Did I modify unrelated files?
- Did I violate role ownership?
- Did I violate architecture boundaries?
- Did I add unnecessary abstractions?
- Did I add or update tests?
- Did I run verification commands?
- Did I hardcode secrets?
- Did I accidentally add real trading behavior?
- Did I accidentally call exchange order APIs?
- Did I update docs or decisions if behavior changed?

Codex must include a self-review summary before completing the task.

# Pull Request Review Requirement

When a pull request is opened, Codex review should check:

- scope expansion
- requirement mismatch
- missing tests
- architecture boundary violations
- role ownership violations
- data contract violations
- hardcoded secrets
- unsafe live trading behavior
- accidental exchange order calls
- unnecessary abstractions
- documentation updates when behavior changed

For trading-related changes, review must be strict around:

- API keys
- `.env` files
- live order execution
- exchange order endpoints
- paper trading accidentally using live clients
- Binance data downloader accidentally using order endpoints


# Area Routing Rules (Task 074)

## Backend API Tasks

Backend tasks may read:

- `backend/AGENTS.md`
- `backend/STATUS.md`
- `docs/api/API_CONTRACT.md`
- `quant_bitcoin/persistence/postgres.py`
- backend source/tests

Backend tasks must not:

- implement frontend UI
- mutate strategy/backtest logic unless assigned
- create live trading endpoints
- expose API keys
- call exchange order/account endpoints

## Frontend Tasks

Frontend tasks may read:

- `frontend/AGENTS.md`
- `frontend/STATUS.md`
- `docs/api/API_CONTRACT.md`
- frontend source/tests

Frontend tasks must not:

- modify backend repository/read-model code unless assigned
- call the database directly
- run backtests directly
- create live trading controls
- add login/auth unless assigned later

## Backtest / Research Tasks

Backtest tasks may read:

- root `AGENTS.md`
- root `STATUS.md`
- assigned task file
- relevant `docs/strategy/*.md`
- relevant `quant_bitcoin/` source/tests

Backtest tasks must not:

- modify frontend or backend API areas unless assigned
- add UI concerns into core strategy/backtest modules
- run, implement, tune, or validate a strategy/model before the relevant `docs/strategy/*.md` exists

Backtest/research execution order:

- Read root state files and the assigned task first.
- Read the relevant `docs/strategy/*.md` next.
- If the strategy document is missing, create it under `docs/strategy/`, update state files, and stop.
- Only after both task and strategy document exist may the task run backtests, tune parameters, or modify strategy/model code.
- Keep any passing or failing research result within the strategy document's declared research-only/live-trading boundary unless a later task explicitly changes that boundary.


# Completion Rules

Every implementation task must end with:

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
