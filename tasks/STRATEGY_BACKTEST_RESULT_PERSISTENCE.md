# Task: Strategy-Level Backtest Result Persistence (PostgreSQL)

## Mode
implement

## Why this task exists
After the backtest workflow moved to strategy-level execution (strategy selected per run), completed strategy backtest results must be persisted so they can be queried later by backend read APIs and visualized by frontend dashboards **without re-running the backtest**. The current path does not yet guarantee a reusable, database-backed persisted result bundle for this strategy-level flow.

## Goal
Persist each completed **strategy-level simulated backtest** result to PostgreSQL in a transactionally consistent form that includes run metadata, strategy metadata, pattern metadata, summary metrics, simulated trades, and graph-ready time-series points.

## Scope (implementation task)
Allowed in the future implementation task:
- Add/extend strategy-level backtest persistence behavior.
- Define/implement persistence payload mapping from completed strategy backtest result.
- Persist the full run bundle transactionally.
- Update CLI behavior for persistence output and optional non-persist mode.
- Add/update tests and relevant documentation.

Likely files (as needed):
- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/__init__.py`
- `quant_bitcoin/persistence/postgres.py`
- `quant_bitcoin/persistence/__init__.py`
- `db/init/001_schema.sql`
- `db/changes/*.sql` (if schema policy requires migration/change files)
- `tests/backtesting/test_pattern_strategy_backtest.py`
- `tests/backtesting/test_pattern_postgres_runner_cli.py`
- `tests/persistence/test_postgres_persistence.py`
- `README.md`
- `STATUS.md`
- `BACKLOG.md` (only if follow-up backend/frontend tasks are discovered)

## Explicitly out of scope (implementation task)
- Pattern detector algorithm changes unless strictly necessary for persistence integration.
- Pattern risk/exit planner algorithm changes unless strictly necessary for persistence integration.
- Live trading/execution behavior.
- Backend API implementation.
- Frontend implementation.
- API contract rollout for backend endpoints.
- GitHub Actions / PR automation / approval workflow additions.
- Any exchange order/account endpoint behavior.

## Required design decisions (must be documented in implementation PR/task notes)

### 1) Persistence target decision
Document and implement one clear decision:
- Reuse existing backtest persistence tables, **or**
- Extend schema/tables for strategy-level pattern backtest results.

Decision must include rationale and compatibility implications.

### 2) Strategy metadata persistence
Persist strategy-level metadata including:
- `strategy_id`
- `strategy_name`
- `selected_strategy`
- `strategy_version` (if applicable)
- strategy parameters (serialized)
- deterministic parameter hash
- underlying pattern identifiers

### 3) Run metadata persistence
Persist run-level metadata including:
- source
- symbol
- interval
- requested start/end timestamps
- actual candle start/end timestamps
- candle count
- starting cash
- run status
- created/completed timestamps
- deterministic run key or equivalent identifier

### 4) Summary metrics persistence
Persist summary metrics including:
- starting cash
- ending cash
- final equity
- total return
- trade count
- win/loss counts (if available)
- realized PnL (if available)
- max drawdown (if available)
- metadata explaining unavailable metrics

### 5) Simulated trade persistence
Persist trade-level rows including:
- deterministic sequence order
- strategy identifier
- underlying pattern identifier
- pattern event id
- direction
- entry timestamp/price
- exit timestamp/price
- exit reason
- quantity or simulated size (if available)
- realized PnL or R-multiple (if available)
- metadata payload

### 6) Graph-ready point persistence
Persist time-series rows including:
- candle timestamp
- close price
- cash
- position
- equity
- drawdown (if available)
- trade marker id (if present)
- signal/event marker (if present)

Rows must be reproducibly ordered by deterministic timestamp sequence.

### 7) Transactionality
Persist one completed run atomically:
- strategy config/metadata
- run metadata
- summary metrics
- trades
- graph points

All rows for one run must commit together or roll back together.

### 8) Idempotency policy
Must define and document one explicit behavior for deterministic reruns:
- replace prior rows for same run key, **or**
- create a new run record for each execution.

Implementation and tests must follow the chosen policy.

### 9) CLI persistence behavior
Strategy-level backtest CLI must:
- run strategy backtest
- support persistence default or explicit persist flag (documented decision)
- optionally support `--no-persist`
- emit JSON including persisted `backtest_run_id` when saved
- avoid persistence when validation/preconditions fail

### 10) Backend/frontend readiness
Persisted shape must allow future backend read APIs and frontend charting to load completed results directly, with no backtest rerun required.

## Safety boundaries (must remain enforced)
- Simulation-only persistence; no live trading.
- No real Binance order execution.
- No exchange order endpoints.
- No exchange account endpoints.
- No API keys or secret handling changes.
- No `.env` dependency introduction.
- No signed requests.
- No paper-trader behavior that can place real orders.
- Ordinary test suite must not require network or live exchange access.

## Required tests (future implementation)
- Strategy-level completed result maps to a persistence payload.
- Strategy metadata is persisted, including selected strategy + underlying pattern identifiers.
- Run metadata is persisted.
- Summary metrics are persisted.
- Simulated trades persist in deterministic sequence order.
- Graph-ready points persist in deterministic timestamp order.
- Persistence is transactional.
- Injected persistence failure causes full rollback for that run.
- Idempotency behavior matches documented decision.
- CLI returns `backtest_run_id` when persistence succeeds.
- CLI supports non-persist mode if specified by chosen CLI policy.
- Read model can load completed persisted strategy backtest result without re-running.
- Ordinary tests run without requiring live PostgreSQL unless explicitly marked optional integration tests.
- No live trading/order execution/API-key/.env/signed-request/order-endpoint/account-endpoint behavior is introduced.

## Documentation updates required (future implementation)
- Update `README.md` with strategy-level backtest persistence behavior.
- Document strategy backtest run command that saves results.
- Document non-persist mode usage if supported.
- Document persisted result shape for future backend/frontend consumers.
- Update `STATUS.md` when project state changes.
- Update `BACKLOG.md` if new follow-up backend/frontend tasks are discovered.

## Acceptance criteria for this task document
- `tasks/STRATEGY_BACKTEST_RESULT_PERSISTENCE.md` exists.
- It explains why strategy-level persistence is needed.
- It defines the target persisted result shape.
- It defines strategy metadata persistence requirements.
- It defines run metadata persistence requirements.
- It defines summary metric persistence requirements.
- It defines simulated trade persistence requirements.
- It defines graph-ready point persistence requirements.
- It requires transactional persistence.
- It requires a documented idempotency decision.
- It requires CLI persistence behavior definition.
- It states backend/frontend should read persisted results without rerunning backtests.
- It preserves no-live-trading safety boundaries.
- It does not implement application code.

## Verification (for implementation task)
- Run task-specified tests and checks.
- Confirm deterministic ordering expectations for trades and graph points.
- Confirm rollback behavior via failure-path test.

## Verification (for this task-creation step)
- `git diff --check`

## Completion checklist (for implementation task)
- Files changed.
- Implementation summary.
- Tests added/updated.
- Tests run.
- Codex self-review result.
- Known limitations.
- Recommended next task.
