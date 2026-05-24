# Goal

Add a frontend panel that turns diagnostics into a concise explanation of why the selected run performed poorly and which next experiment should be run.

# Source Requirement

Owner request: “백테스트해보니까 성과가 별로 안좋더라구. 이유 찾아서 분석해줘.” The frontend should show this analysis directly for each saved run, not only raw charts/metrics.

# Extracted Roles

- Owner role:
  - Backtest diagnosis UX owner.
- Supporting roles:
  - Backend diagnostics role.
  - Performance metrics role.
  - Frontend presentation role.
- Forbidden roles:
  - No automatic strategy retuning.
  - No live trading.
  - No promises of profitability.

# Context

Once Tasks 173-178 produce metrics and diagnostics, the user needs a readable conclusion:
- Is performance weak because the strategy loses after entry?
- Is the entry late?
- Are costs too high?
- Are stops too frequent?
- Is sample size too small?
- Is the score filter unhelpful?
- Does a specific regime or side dominate losses?

# Scope

- Add `Run Conclusion` frontend panel.
- Inputs:
  - performance metrics,
  - diagnostics,
  - timing diagnostics,
  - risk audit,
  - score calibration,
  - cost summary,
  - attribution.
- Output:
  - top 3 likely failure reasons,
  - confidence level based on sample size,
  - direct evidence rows,
  - recommended next analysis:
    - try FVG retest mode,
    - enable cost profile,
    - run walk-forward validation,
    - inspect stop dominance,
    - inspect score bucket calibration,
    - inspect regime attribution.
- Use deterministic rule mapping, not AI generation.
- Hide raw evidence behind details.

# Out of Scope

- No LLM dependency inside frontend.
- No strategy mutation.
- No backtest execution from frontend.
- No live trading.

# Requirements

- Panel must render even when only partial metadata exists.
- Must not overstate conclusions when sample size is small.
- Must include a “not enough data” state.
- Must distinguish mechanical anomalies from weak strategy edge.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read frontend `AGENTS.md`.
- [x] Read frontend `STATUS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- The panel is deterministic rule mapping over saved metadata only; no LLM or frontend backtest execution is introduced.
- Partial metadata must produce low-confidence or not-enough-data output.
- Recommendations are next analyses to run outside the dashboard, not buttons or execution controls.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A bad fixture run renders a clear conclusion.
- A good fixture run does not show false critical warnings.
- A legacy fixture shows partial/no-diagnostics state.
- Frontend build passes.

# Required Tests

## Unit Tests

- Rule mapping from diagnostic flags to conclusions.
- Sample size confidence label.
- Missing diagnostics fallback.

## Integration Tests

- Frontend fixture if harness exists.
- Backend diagnostics response consumed safely.

## Contract Tests

- Document frontend diagnostic panel inputs.

## Safety Tests

- No backtest or order execution controls.

# Verification

Default:

```bash
npm --prefix frontend run build
pytest backend/tests/test_backtest_results_service_runtime.py
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

# Completion Summary

- Files changed:
  - `frontend/src/lib/runConclusion.ts`
  - `frontend/src/app/page.tsx`
  - `frontend/tests/runConclusion.test.ts`
  - `frontend/package.json`
  - `frontend/tsconfig.test.json`
  - `frontend/STATUS.md`
  - `docs/api/API_CONTRACT.md`
- Implementation summary:
  - Added a read-only Run Conclusion panel with top likely failure reasons, confidence label, evidence rows, and next analysis recommendations.
  - Added deterministic rules for mechanical anomalies, cost drag, entry timing, exit/risk dominance, score calibration, weak edge, and sample-size limitations.
  - Added helper tests for bad, good, and legacy/no-diagnostics fixtures.
  - Documented the frontend metadata inputs and safety boundary.
- Tests added or updated:
  - Added `frontend/tests/runConclusion.test.ts`.
  - Updated frontend helper test script and TypeScript test config.
- Tests run:
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run build`
  - `pytest backend/tests/test_backtest_results_service_runtime.py`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed within Task 184; no LLM dependency, frontend backtest execution, order endpoint, strategy mutation, live control, API key, or `.env` behavior was added.
- Known limitations:
  - Conclusions are deterministic heuristics over available metadata; missing/legacy diagnostics intentionally produce partial or not-enough-data output.
- Recommended next task:
  - Task 185.
