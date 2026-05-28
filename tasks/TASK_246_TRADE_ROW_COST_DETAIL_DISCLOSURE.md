# Task 246: Trade Row Cost Detail Disclosure

# Goal

Make fee, spread, slippage, total cost, raw price, and effective price easy to inspect for each trade without overcrowding the trade table.

# Source Requirement

Owner feedback:

5. The user needs to confirm fee and slippage details for each trade.

# Extracted Roles

- Owner role:
  - Frontend trade-review UX owner.
- Supporting roles:
  - API consumer role: uses existing trade `metadata.cost_breakdown`, `raw_price`, and `effective_price`.
  - Backend role: only needed if the API does not expose the required fields.
  - Test role: owns frontend type/build and helper coverage.
- Forbidden roles:
  - Do not change transaction-cost formulas unless explicitly assigned.
  - Do not add DB migrations in this task.
  - Do not add live trading, order controls, or exchange account behavior.

# Context

Tasks 238-240 made cost details available through execution metadata and frontend trade columns. The current table may still be too dense for quick review. A better UX is to keep high-signal columns visible and expose full cost details per trade via row expansion or a compact details panel.

# Scope

- Add per-trade cost detail disclosure in the trade review table.
- Show at least:
  - raw price,
  - effective price,
  - fee cost,
  - spread cost,
  - slippage cost,
  - total cost,
  - fee bps,
  - spread bps,
  - effective slippage bps,
  - volatility bps,
  - cost profile name.
- Keep legacy rows without `cost_breakdown` safe and readable.
- Reduce table crowding if needed by moving detailed cost columns into expandable content.

# Out of Scope

- Do not change backend cost calculations.
- Do not change DB schema.
- Do not add order-book or real exchange fee lookup.
- Do not implement chart drag/zoom here; Task 242 owns chart interactions.

# Requirements

- User can inspect cost details per trade from the UI.
- Missing cost details render as unavailable, not zero.
- Raw and effective price labels remain unambiguous.
- Table remains readable on mobile and desktop.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `frontend/AGENTS.md` if present.
- [ ] Read this assigned task file before coding.
- [ ] Confirm API exposes `cost_breakdown` for new runs or document blocker.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when completed.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- Each trade row has an obvious way to view fee/slippage/spread details.
- The UI distinguishes raw fill price from effective diagnostic price.
- Legacy rows without `cost_breakdown` do not crash or show misleading zeroes.
- Frontend build/type checks pass.

# Required Tests

## Unit Tests

- Test cost-detail extraction helper if introduced.
- Test legacy missing-cost fallback behavior if helpers are testable.

## Integration Tests

- Run frontend typecheck/build.
- If browser tooling is available, verify expanding a trade row shows cost detail fields.

## Contract Tests

- Confirm frontend type and displayed fields match API `cost_breakdown` contract.

## Safety Tests

- Confirm no live trading controls, exchange fee lookup, or signed exchange requests are added.

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
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:helpers
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
