# Goal

Reconcile project state files and install the next executable task sequence for multi-interval data, real-time strategy execution, performance analytics, paper/testnet/live execution, fee/slippage reconciliation, and short-product policy.

This task is documentation/state-management only. It must not implement trading, execution, WebSocket callbacks, account access, or metric calculations.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/114_INTRABAR_STOP_TARGET_AMBIGUITY_POLICY.md`
- `tasks/115_BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY.md`
- `tasks/116_PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/118_TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION.md`
- current task bundle files for Tasks 130-137

# Extracted Roles

- Owner role:
  - Project state and task-ledger owner.
  - Owns task sequencing, status consistency, and next-task declaration.
- Supporting roles:
  - Documentation role: copies task documents into `tasks/`.
  - Backlog role: records upcoming tasks and dependencies.
  - History role: appends concise task-bundle creation history.
- Forbidden roles:
  - No source implementation.
  - No test implementation.
  - No Binance API calls.
  - No live trading.
  - No credential handling.
  - No schema changes.

# Context

The project state files can drift from the actual completed implementation state. Before adding new implementation work, the current status must accurately reflect recent completed work and the next active task. The new work requested by the owner spans multiple responsibilities and must be split into explicit task files before implementation.

# Scope

- Copy Tasks 130-137 into the repository `tasks/` directory.
- Update `STATUS.md` to reflect the latest completed source-backed task state.
- Update `BACKLOG.md` with Tasks 130-137 as current candidates or planned follow-ups.
- Append a concise `PROJECT_HISTORY.md` note stating that the execution task bundle was added.
- Ensure the next recommended implementation task is Task 130 unless the owner reprioritizes.
- Keep the task numbering and names stable.

# Out of Scope

- Implementing multi-interval backfill.
- Implementing Sharpe/Sortino metrics.
- Implementing real-time strategy execution.
- Implementing paper/testnet/live execution clients.
- Implementing fee/slippage reconciliation.
- Enabling live trading.
- Editing application source files or tests.

# Requirements

- `STATUS.md` must not claim Task 114 is the latest completed task if Tasks 115-118 are already recorded as completed elsewhere and reflected in source.
- `BACKLOG.md` must include the new tasks with dependency ordering.
- `PROJECT_HISTORY.md` must include a short note for this task bundle creation.
- The next task must be explicitly recorded.
- No implementation files outside state/task docs may be modified.
- All new task documents must follow `tasks/TASK_TEMPLATE.md` section structure.

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

- Tasks 130-137 exist under `tasks/`.
- `STATUS.md` reflects the latest completed source-backed task state and identifies the next implementation task.
- `BACKLOG.md` lists Tasks 130-137 with concise purpose and status.
- `PROJECT_HISTORY.md` has a concise completion note for this state reconciliation/task-bundle creation.
- No application source files are changed.
- No tests are required beyond file-content review for this documentation-only task.

# Required Tests

## Unit Tests

- Not applicable for documentation/state-file-only work.

## Integration Tests

- Not applicable for documentation/state-file-only work.

## Contract Tests

- Verify every new task document contains all required task-template sections.
- Verify task numbering is stable and does not collide with existing tasks.

## Safety Tests

- Verify no task changes introduce API keys, `.env` files, signed requests, or live order execution.
- Verify live execution remains blocked outside the later guarded live rollout task.

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

Additional verification:

```bash
python - <<'TASKCHECK'
from pathlib import Path
required = [
    '# Goal', '# Source Requirement', '# Extracted Roles', '# Context', '# Scope',
    '# Out of Scope', '# Requirements', '# Status Tracking', '# Acceptance Criteria',
    '# Required Tests', '# Review Checklist', '# Verification',
    '# Codex Self-Review Requirement', '# PR Review Requirement', '# Completion Summary Required'
]
for path in sorted(Path('tasks').glob('12[0-7]_*.md')):
    text = path.read_text()
    missing = [section for section in required if section not in text]
    if missing:
        raise SystemExit(f'{path}: missing {missing}')
print('task documents satisfy required section structure')
TASKCHECK
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
