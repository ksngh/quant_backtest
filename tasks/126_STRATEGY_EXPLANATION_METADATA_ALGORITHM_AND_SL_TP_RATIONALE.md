# Strategy Explanation Metadata For Algorithm And S/L T/P Rationale

# Goal

Persist and display human-readable strategy explanation metadata for each backtest run.

When viewing a completed backtest in the site, the user must be able to see:

- which algorithm/pattern was used;
- how the pattern is detected;
- when long/short entry occurs;
- what S/L strategy was planned;
- what T/P strategy was planned;
- partial-exit behavior if applicable;
- soft-invalidation/time-stop behavior if applicable;
- why the pattern design uses those rules;
- known limitations.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- `quant_bitcoin/patterns/fair_value_gap_risk_exit.py`
- `quant_bitcoin/patterns/order_block_risk_exit.py`
- `quant_bitcoin/patterns/trendline_break_risk_exit.py`
- `quant_bitcoin/patterns/cup_and_handle_risk_exit.py`
- `quant_bitcoin/patterns/diamond_risk_exit.py`
- `quant_bitcoin/patterns/adam_and_eve_risk_exit.py`
- `quant_bitcoin/risk/exit_plan.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- `backend/quant_backtest_api/services/backtest_results.py`
- `frontend/src/types/api.ts`
- `frontend/src/app/page.tsx`

# Extracted Roles

- Owner role:
  - Strategy documentation metadata owner.
  - Responsible for generating, persisting, exposing, and displaying strategy explanation metadata.

- Supporting roles:
  - Pattern detection role:
    - Provides algorithm detection rules.
  - Risk/exit role:
    - Provides S/L and T/P rules.
  - Persistence role:
    - Stores explanation metadata in strategy config or run metadata.
  - API/frontend role:
    - Exposes and renders explanation metadata.
  - Test role:
    - Verifies metadata exists and is displayable.

- Forbidden roles:
  - No algorithm optimization in this task.
  - No live trading.
  - No real order execution.
  - No exchange private endpoints.
  - No API key handling.
  - No unsupported inverse patterns invented.

# Context

The site currently displays raw strategy parameters, run metadata, and result metadata. Users need a more readable explanation of the strategy used in a specific run.

Existing strategy and risk planner code already encodes much of the explanation:

- FVG:
  - three-candle imbalance;
  - displacement and volume confirmation;
  - FVG boundary stop;
  - R-multiple targets and reaction/time-stop logic.
- Order Block:
  - opposing source candle before displacement;
  - zone-based entry;
  - zone boundary stop;
  - no-reaction time stop.
- Trendline Break:
  - confirmed pivot trendline;
  - ATR-buffered breakout;
  - breakout/retest/event stop;
  - trendline re-entry soft invalidation.
- Cup and Handle:
  - bullish rim/bottom/handle/breakout structure;
  - handle low stop;
  - measured target;
  - neckline soft exit.
- Diamond:
  - expansion/contraction pivot structure;
  - boundary breakout/breakdown;
  - measured target;
  - close back inside range invalidation.
- Adam and Eve:
  - bullish double-bottom variant;
  - Eve or wider Adam/Eve low stop;
  - measured target;
  - neckline soft exit.

# Scope

- Add strategy explanation metadata builder.
- Store explanation metadata in `strategy_configs.metadata` where possible.
- Include run-specific resolved values in `backtest_runs.metadata` or `backtest_results.metadata` where useful.
- Expose explanation metadata through existing detail API.
- Add frontend cards for:
  - Algorithm Summary;
  - Entry Rules;
  - Stop-Loss Rules;
  - Take-Profit Rules;
  - Risk/Exit Management;
  - Design Rationale;
  - Limitations.
- Preserve raw JSON panels.

# Out of Scope

- Changing algorithm behavior.
- Implementing missing S/L or T/P behavior.
- Runtime optimization.
- Runtime persistence.
- New pattern algorithms.
- Live trading.

# Requirements

- Each supported pattern must have explanation metadata.
- Explanation metadata must be JSON-serializable.
- Explanation metadata must be stable for deterministic strategy configuration.
- Explanation metadata must include:
  - `algorithm_key`
  - `algorithm_name`
  - `direction_support`
  - `detection_rules`
  - `entry_rules`
  - `stop_loss_rules`
  - `take_profit_rules`
  - `partial_exit_rules`
  - `soft_invalidation_rules`
  - `time_stop_rules`
  - `design_rationale`
  - `known_limitations`
- If S/L or T/P is not actually connected in the canonical execution path at the time of implementation, metadata must state that clearly.
- Do not claim a rule is active unless the canonical execution path actually uses it.
- The UI must show explanation in readable sections, not only raw JSON.
- Old runs without explanation metadata must render safely.

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

- Completed run detail includes strategy explanation metadata.
- Frontend selected run detail displays algorithm and S/L/T/P explanation.
- Each supported pattern has a tested explanation payload.
- Explanation payload does not overstate inactive behavior.
- Old runs without metadata render without crashing.
- Raw strategy parameters remain visible.

# Required Tests

## Unit Tests

- Test explanation builder for:
  - `FAIR_VALUE_GAP`
  - `ORDER_BLOCK`
  - `TRENDLINE_BREAK`
  - `CUP_AND_HANDLE`
  - `DIAMOND`
  - `ADAM_AND_EVE`
- Test JSON serialization.
- Test inactive lifecycle warning when applicable.
- Test unsupported pattern raises a clear error.

## Integration Tests

- Persist a completed run with explanation metadata.
- Load run detail through backend service.
- Confirm explanation metadata is present.
- Render frontend detail with explanation metadata.

## Contract Tests

- Strategy metadata remains deterministic.
- Existing strategy parameters remain unchanged.
- API response remains backward-compatible.

## Safety Tests

- No exchange order/account endpoints.
- No API key loading.
- No signed requests.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Explanation matches actual implementation.
- Inactive S/L or T/P behavior is not presented as active.
- UI is readable and handles missing metadata.

# Verification

Default:

```bash
pytest
```

Frontend verification if applicable:

```bash
cd frontend
npm test
npm run build
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
- frontend build result
- patterns covered
- metadata storage location
- Codex self-review result
- known limitations
- recommended next task
