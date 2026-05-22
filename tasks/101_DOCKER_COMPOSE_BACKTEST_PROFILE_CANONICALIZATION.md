# Task 101: DOCKER_COMPOSE_BACKTEST_PROFILE_CANONICALIZATION

## Status

Planned

# Goal

Fix the known Docker Compose test mismatch and align the backtest profile with the canonical strategy-backtest CLI.

# Source Requirement

Current `STATUS.md` reports a full-pytest blocker in `tests/market_data/test_websocket_ingestion_cli.py` related to Docker Compose connection-string assertion. Current `docker-compose.yml` still uses the pattern CLI module under the backtest profile instead of the canonical strategy CLI.

# Extracted Roles

- Owner role: Project owner approves whether the backtest profile should be a help-only smoke command or a bounded no-persist backtest smoke command.
- Supporting roles: Codex agent updates Docker Compose and tests within the assigned scope.
- Forbidden roles: Live trading, exchange order execution, production deployment, new Docker services, database schema changes, or broad CLI redesign.

# Context

`docker-compose.yml` uses env-interpolated PostgreSQL URLs and the backtest service calls `quant_bitcoin.backtesting.pattern_postgres_runner_cli --help`. The websocket ingestion test asserts a literal expanded PostgreSQL URL that is no longer present in the compose file. The project now prefers canonical `quant-bitcoin-strategy-backtest` / `strategy_postgres_runner_cli` paths.

# Scope

- Update `docker-compose.yml` backtest service to use the canonical strategy-backtest CLI path.
- Update the compose assertion in `tests/market_data/test_websocket_ingestion_cli.py` so it validates env-interpolated `DATABASE_URL` semantics rather than a literal expanded connection string.
- Keep the websocket ingestor service behavior unchanged except for tests required by the compose assertion.
- Update `STATUS.md` to remove or clarify the known pytest blocker if the targeted test passes.

# Out of Scope

- Do not change database credentials, default DB names, or Docker volume behavior unless required for the failing assertion.
- Do not introduce live ingestion into the backtest service.
- Do not add new Docker profiles or deployment infrastructure.

# Requirements

- Backtest profile must use canonical CLI ownership.
- Test expectations must match the actual env-interpolated compose file.
- Do not weaken the test so much that it no longer confirms Postgres service wiring.

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

- `tests/market_data/test_websocket_ingestion_cli.py` no longer fails on a hardcoded literal URL mismatch.
- Backtest service command points to canonical strategy-backtest CLI behavior.
- Websocket ingestor compose assertions still verify service presence, unbounded ingest default, command, and health dependency.
- `STATUS.md` no longer lists this exact failure as current if verified.

# Required Tests

## Unit Tests

- Not applicable unless helper parsing is introduced.

## Integration Tests

- `tests/market_data/test_websocket_ingestion_cli.py` passes.

## Contract Tests

- Docker Compose service contract remains: postgres, backtest, and websocket-ingestor profiles use correct service-discovery URL forms.

## Safety Tests

- No live trading, no real Binance order execution, no API keys, no `.env` files.

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

Task-specific:

```bash
pytest -q tests/market_data/test_websocket_ingestion_cli.py
python -m compileall quant_bitcoin
git diff --check
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
