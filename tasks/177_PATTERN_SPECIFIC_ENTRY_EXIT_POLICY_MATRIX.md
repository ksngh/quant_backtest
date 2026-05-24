# Goal

Define and implement a pattern-specific entry/exit policy matrix so continuation, retest, reversal, and breakout patterns do not all share one implicit timing assumption.

# Source Requirement

Owner concern: buy/sell timing might be algorithmically wrong. Current pattern strategy path can apply one default entry mode across patterns even though FVG, Order Block, Trendline Break, Cup and Handle, Diamond, and Adam and Eve have different economic timing assumptions.

# Extracted Roles

- Owner role:
  - Pattern strategy design owner.
- Supporting roles:
  - Pattern detector owners: provide event fields.
  - Risk planner owner: maps entry to stops/targets.
  - CLI/docs/frontend owners: expose selected policy.
- Forbidden roles:
  - No automatic optimization.
  - No live trading.
  - No unsupported strategy claims.

# Context

Different patterns have different economic entry assumptions:
- FVG/Order Block often favor retest entries.
- Trendline Break and Cup/Handle often favor breakout confirmation entries.
- Diamond may need breakout or failed-break retest variants.
- Adam and Eve often uses neckline breakout confirmation.

Applying a single default to all patterns can produce systematically bad timing.

# Scope

- Create a policy contract such as `PatternExecutionPolicy`.
- For each supported pattern define default allowed entry modes and exit assumptions:
  - FVG: retest/midpoint/boundary and optional confirmation momentum.
  - Order Block: zone midpoint/zone 0.618/retest.
  - Trendline Break: confirmation close/next open/retest of trendline.
  - Cup and Handle: breakout close/next open/retest of neckline.
  - Diamond: boundary breakout/breakdown close/next open.
  - Adam and Eve: neckline breakout/next open/retest of neckline.
- Wire selected policy through CLI and strategy metadata.
- Keep current default backwards-compatible until owner changes default.
- Add frontend display of selected entry policy and why that policy fits the pattern.

# Out of Scope

- Do not tune thresholds for profitability.
- Do not add ML or optimizer.
- Do not enable live trading.
- Do not rewrite detectors.

# Requirements

- Each pattern has explicit documented entry/exit policy.
- CLI rejects unsupported pattern/mode combinations.
- Strategy output metadata records policy key, entry mode, and economic rationale.
- Frontend shows policy details.
- Existing default behavior remains stable unless a test explicitly covers changed default.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- Policy metadata is explanatory and validation-oriented; it must not auto-optimize entries or exits.
- Current default behavior remains stable. Unsupported combinations should fail early only when an explicit incompatible mode is requested.
- Frontend display is read-only and must consume saved/API metadata only.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `pattern_execution_policy_v1` matrix for supported patterns with allowed entry modes, exit assumptions, economic rationale, and research hypothesis.
- CLI rejects unsupported explicit pattern/mode combinations before loading candles.
- Strategy output/API metadata records policy key, selected entry mode, and rationale; frontend displays the policy in Strategy Logic.
- Default behavior remains market-on-confirmation unless an explicit compatible mode is requested.
- Next task: Task 178 `RISK_REWARD_TARGET_STOP_VALIDITY_AND_DOMINANCE_AUDIT`.

# Acceptance Criteria

- Invalid pattern/mode combination fails before backtest execution.
- Valid combinations emit expected metadata.
- Frontend displays policy explanation for known patterns.
- Docs explain which policies are research hypotheses, not guarantees.

# Required Tests

## Unit Tests

- Policy contract validation.
- Pattern-to-mode compatibility matrix.
- Metadata serialization.

## Integration Tests

- CLI tests for at least FVG, Order Block, Trendline Break.

## Contract Tests

- API contract includes policy metadata.

## Safety Tests

- No execution clients imported into pattern policy modules.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/strategies/test_pattern_explanations.py
npm --prefix frontend run build
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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
