# Goal

Improve backtest reproducibility by recording dataset identity, candle quality summary, strategy/action configuration hashes, validation seed values, and environment-relevant assumptions.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- Saved runs include strategy/runtime metadata, but serious research requires enough information to reproduce exactly what data/config generated a result.
- New validation and data-quality tasks need dataset and config fingerprints.

Read and inspect:

- `tasks/124_PERSIST_BACKTEST_RUNTIME_METADATA.md`
- `tasks/128_STRATEGY_CLI_JSON_TIMESTAMP_SERIALIZATION_FIX.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- README backtest/run-key documentation

# Extracted Roles

- Owner role:
  - Backtest reproducibility metadata owner.
- Supporting roles:
  - Runner role: builds canonical run metadata.
  - Persistence role: saves run metadata transactionally.
  - Data provider role: reports candle ranges/counts/quality.
- Forbidden roles:
  - No external tracking service.
  - No secrets in metadata.
  - No live trading behavior.

# Context

Code-level hints:

- Add canonical metadata fields near `_build_runtime_metadata()` in `strategy_postgres_runner_core.py`.
- Include:
  - code/engine version already available;
  - selected strategy/pattern;
  - strategy parameter hash;
  - candle source/symbol/interval/start/end/count;
  - actual candle start/end;
  - data quality summary from Task 158 if available;
  - cost/sizing/risk configs;
  - intrabar policy;
  - random seeds for validation/Monte Carlo tasks.
- Never include database passwords, connection URLs with credentials, API keys, `.env` contents, or local absolute paths unless sanitized.

Functional intent:

- A saved run should be auditable and reproducible without guessing config assumptions.

# Scope

- Add reproducibility metadata to CLI JSON and persisted run metadata.
- Add deterministic hashes for strategy parameters and relevant configs where missing.
- Add dataset/candle quality summary fields.
- Sanitize sensitive inputs.
- Add tests for hash stability and secret redaction.

# Out of Scope

- Git commit discovery if unavailable in runtime environment.
- External experiment tracking.
- Live trading audit logs.

# Requirements

- Metadata must be deterministic for the same input config and candle range.
- Sensitive values must be redacted.
- Missing optional environment information must not fail a run.
- Hashes must use canonical JSON or equivalent stable serialization.
- Documentation must explain which metadata is required for reproducibility.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Two identical runs produce identical config hashes.
- Changing a key strategy/cost/sizing parameter changes the relevant hash.
- Database URL credentials and secrets are not persisted or printed.
- Saved run metadata contains dataset identity and actual candle range/count.

# Required Tests

## Unit Tests

- Test canonical hash generation stability.
- Test secret redaction.
- Test metadata builder with missing optional fields.

## Integration Tests

- Test canonical CLI JSON contains reproducibility metadata.
- Test persistence save/load preserves metadata.

## Contract Tests

- Update README/API contract if fields are exposed.
- Ensure metadata is JSON-safe and backward-compatible.

## Safety Tests

- Test no API key, database password, or `.env` value is printed or persisted.
- Confirm no exchange endpoint behavior.

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
pytest tests/backtesting/test_strategy_cli_persistence.py tests/backtesting/test_strategy_persistence_adapter.py
pytest
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
