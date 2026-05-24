# Goal

Integrate the reusable intrabar sequencing policy into pattern exit simulation, including ambiguous stop/target and break-even/trailing-stop sequencing cases.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `quant_bitcoin/backtesting/intrabar_policy.py` defines reusable modes such as conservative, optimistic, stop-first, target-first, entry-first, and skip-ambiguous.
- `quant_bitcoin/risk/exit_simulation.py` currently uses a fixed stop-before-target policy and updates break-even/trailing stop levels before stop/target checks.
- Same-candle high/low sequencing is unknowable from OHLC data and must be explicit.

Read and inspect:

- `tasks/114_INTRABAR_STOP_TARGET_AMBIGUITY_POLICY.md`
- `quant_bitcoin/backtesting/intrabar_policy.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/patterns/entry_simulation.py`
- tests for risk exit simulation and intrabar policy

# Extracted Roles

- Owner role:
  - Backtest fill/exit sequencing policy owner.
- Supporting roles:
  - Risk simulator role: evaluates stop/target/time/soft invalidation.
  - Pattern action-builder role: passes configured policy.
  - CLI/config role: surfaces selected policy if added to CLI.
- Forbidden roles:
  - No exchange/tick replay implementation.
  - No live order routing.
  - No detector rule tuning.

# Context

Code-level hints:

- Add `intrabar_policy_config: IntrabarPolicyConfig | None` to `simulate_pattern_exit()`.
- Use `detect_intrabar_touches()` and `resolve_intrabar_decision()` when stop and target can both be touched in the same candle.
- Decide how break-even/trailing stop updates should be sequenced. Do not silently update BE/trailing from the favorable extreme before evaluating an adverse stop if that makes results optimistic.
- Add metadata fields: `intrabar_policy`, `is_ambiguous`, `ambiguous_stop_target`, `decision_reason`.
- Keep default behavior conservative to preserve prior safety orientation.

Functional intent:

- Every ambiguous candle outcome should be explainable and reproducible.
- Users should be able to run sensitivity tests across intrabar policies.

# Scope

- Wire `IntrabarPolicyConfig` into `simulate_pattern_exit()` and builder call sites.
- Preserve default conservative behavior.
- Add optional CLI arg only if it does not broaden scope too much.
- Add tests for stop-first, target-first, conservative, optimistic, and skip-ambiguous.
- Record ambiguity counts or metadata in summary where practical.

# Out of Scope

- Tick-level replay.
- Order book sequencing.
- Live execution assumptions.
- Changing pattern detector signals.

# Requirements

- Same-candle stop/target ambiguity must use the configured policy, not hard-coded logic.
- BE/trailing-stop sequencing assumptions must be explicit in code and metadata.
- `SKIP_AMBIGUOUS` must avoid fabricating favorable or unfavorable exits where policy says skip.
- Default policy must remain conservative unless explicitly changed.
- Output metadata must allow users to audit ambiguous decisions.

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

- A candle touching both stop and target exits at stop under conservative/stop-first policy.
- The same fixture exits at target under target-first/optimistic policy.
- The same fixture does not create a fill under skip-ambiguous policy.
- BE/trailing ambiguity is tested and documented.
- Existing pattern backtests remain deterministic.

# Required Tests

## Unit Tests

- Test `resolve_intrabar_decision()` integration in `simulate_pattern_exit()`.
- Test all-three-touched scenarios.
- Test BE/trailing activation same candle as stop/target.

## Integration Tests

- Run a canonical pattern action-builder fixture with ambiguous OHLC and verify policy-specific execution output.

## Contract Tests

- Ensure `PatternExitEvent.metadata` remains JSON-safe.
- Ensure default behavior is documented and backward-compatible where possible.

## Safety Tests

- Confirm no live/tick execution behavior is introduced.
- Confirm no exchange endpoints are called.

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
pytest tests/backtesting/test_intrabar_policy.py tests/risk/test_exit_simulation.py tests/backtesting/test_pattern_action_builder.py
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
