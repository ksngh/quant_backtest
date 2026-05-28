# Task 239: Cost-Aware Net R/R Entry Filter

# Goal

Prevent structurally unprofitable backtest entries by adding a deterministic pre-entry gate that allows a pattern trade only when the expected reward exceeds estimated round-trip transaction cost and the cost-adjusted net R/R meets the configured threshold.

# Source Requirement

Owner concern: the strategy is losing on nearly every trade because the expected move often does not exceed the combined fee, spread, and slippage burden. The user requested one recommended solution rather than multiple alternative approaches.

Forensic finding from the 2026-05-20 02:17 FVG short case:

- `conservative_crypto_1m` uses `taker_fee_bps = 10.0`, `spread_bps = 3.0`, `slippage_bps = 5.0`, and volatility-adjusted slippage.
- The sampled candle produced `effective_slippage_bps = 5.385319471381747`.
- Approximate per-side transaction burden was about `18.3853 bps`.
- Approximate round-trip burden was about `36.77 bps` before any additional safety buffer.
- Small 1m FVG moves can be below this cost threshold even when the raw pattern logic is valid.

# Extracted Roles

- Owner role:
  - Backtest expectancy and trade-admission owner.
- Supporting roles:
  - Pattern action builder role: owns pre-entry skip decision.
  - Risk planning role: exposes entry/stop/target distances before action emission.
  - Cost model role: estimates round-trip cost without future candle look-ahead.
  - CLI/API role: exposes filter parameters and skip diagnostics.
  - Test role: proves cost-infeasible trades are skipped deterministically.
- Forbidden roles:
  - No live trading.
  - No order placement.
  - No exchange account or signed endpoint behavior.
  - No optimizer that searches for profitable thresholds automatically.
  - No future candle data in pre-entry cost estimation.

# Context

A raw R/R calculation can look acceptable while the net R/R is negative after transaction costs. The recommended admission rule is to estimate round-trip cost at decision time, subtract it from expected reward, add it to expected risk, and skip trades that do not clear both a minimum net reward and minimum net R/R threshold.

Use one deterministic estimator to avoid look-ahead:

```text
estimated_one_side_cost_bps = fee_bps + spread_bps + effective_slippage_bps_from_entry_candle
estimated_round_trip_cost_bps = 2 * estimated_one_side_cost_bps
net_reward_bps = gross_reward_bps - estimated_round_trip_cost_bps
net_risk_bps = gross_risk_bps + estimated_round_trip_cost_bps
net_rr = net_reward_bps / net_risk_bps
```

Recommended default thresholds for this filter when enabled:

```text
min_net_reward_bps = 20.0
min_net_rr = 1.5
```

With the sampled `conservative_crypto_1m` cost profile, this implies a rough gross target-distance floor near `57 bps` before a trade is allowed.

# Scope

- Add a cost-aware entry gate in the pattern action-building path before entry actions are emitted.
- Compute planned gross reward/risk from the selected entry, stop, and target prices.
- Estimate round-trip transaction cost using the selected cost profile and the current/entry candle volatility only.
- Add CLI/config parameters:
  - `enable_cost_aware_entry_filter`,
  - `min_net_reward_bps`, default `20.0`,
  - `min_net_rr`, default `1.5`.
- When the filter is enabled and a trade fails the gate, emit a deterministic skip diagnostic instead of an entry action.
- Store skip metadata:
  - `skip_reason = "COST_INFEASIBLE_NET_RR"`,
  - `gross_reward_bps`,
  - `gross_risk_bps`,
  - `estimated_round_trip_cost_bps`,
  - `net_reward_bps`,
  - `net_risk_bps`,
  - `net_rr`,
  - `min_net_reward_bps`,
  - `min_net_rr`,
  - `cost_profile_name`,
  - `cost_estimation_basis = "entry_candle_volatility"`.
- Include the same economics metadata on accepted trades so later analysis can compare admitted and skipped opportunities.
- Document that this filter is a deterministic research/backtest gate, not an optimizer.

# Out of Scope

- Do not change transaction-cost formulas in this task.
- Do not change price field semantics in this task except consuming the corrected fields if Task 238 has already landed.
- Do not persist detailed per-execution cost breakdowns in this task; that belongs to Task 240.
- Do not tune FVG pattern parameters, stop modes, target modes, or trend scoring.
- Do not add maker/taker fee differentiation.
- Do not use future exit candle volatility, MFE/MAE, or realized trade outcome to decide admission.
- Do not introduce live trading, exchange orders, account endpoints, API keys, or `.env` changes.

# Requirements

- The entry filter must run before the strategy opens a position.
- The filter must use only information available at the entry decision point.
- Cost estimates must reuse the configured cost profile rather than hardcoding fee/spread/slippage numbers in the action builder.
- If target, stop, or entry price is missing, the filter must not guess; it must either leave the trade unfiltered with explicit metadata or skip with an explicit invalid-plan reason if the strategy already treats the plan as invalid.
- Accepted trades must carry computed net economics metadata.
- Skipped trades must be visible in CLI/API diagnostics so the user can distinguish "no pattern" from "pattern skipped because costs dominate".
- The filter must be deterministic for identical candles, config, and cost profile.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [ ] Read this assigned task file before coding.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [ ] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:

- The first implementation may be wired through the canonical pattern/FVG action-building path because the owner concern is from an FVG backtest case.
- The estimator should treat the exit leg cost as equal to the entry-candle estimated cost to avoid future volatility look-ahead.
- The filter should be explicit/configurable so tests can compare existing baseline behavior and cost-aware behavior.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [ ] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- With the filter enabled, a trade whose `gross_reward_bps < estimated_round_trip_cost_bps + min_net_reward_bps` is skipped.
- With the filter enabled, a trade whose `net_rr < min_net_rr` is skipped.
- With the filter enabled, a trade clearing both thresholds is admitted and includes net economics metadata.
- Skip diagnostics include the full cost/reward/risk calculation needed to explain the decision.
- The filter does not use future candles, realized exit price, MFE, MAE, or post-entry outcome data.
- The filter works with the configured cost profile and does not hardcode `conservative_crypto_1m` values outside tests.
- Existing baseline behavior remains testable when the filter is disabled.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test net economics calculation:
  - gross reward/risk bps,
  - estimated round-trip cost bps,
  - net reward/risk bps,
  - net R/R.
- Test skip when `net_reward_bps` is below `min_net_reward_bps`.
- Test skip when `net_rr` is below `min_net_rr`.
- Test accept when both thresholds pass.
- Test estimator uses entry-candle volatility and not future candle volatility.

## Integration Tests

- Run deterministic FVG/pattern action-builder fixtures with `conservative_crypto_1m` and verify cost-infeasible entries produce `COST_INFEASIBLE_NET_RR` skip diagnostics.
- Run the same fixture with a larger target distance and verify the entry is admitted.
- Run CLI/API path with the filter enabled and confirm diagnostics are serialized.
- Run CLI/API path with the filter disabled and confirm baseline trade count remains comparable to existing behavior.

## Contract Tests

- API/CLI output includes skip metadata and accepted-trade economics metadata.
- Documentation explains the net R/R formula, thresholds, and no-look-ahead estimator basis.
- Frontend diagnostics, if present, can display `COST_INFEASIBLE_NET_RR` without treating it as an engine error.

## Safety Tests

- Confirm the filter does not import exchange clients or order/account endpoints.
- Confirm no API key, `.env`, or signed request behavior is added.
- Confirm all tests use deterministic offline fixtures.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_costs.py tests/backtesting/test_pattern_postgres_runner_cli.py
pytest tests/backtesting/test_pattern_parameter_grid.py || true
pytest
git diff --check
```

If the repo does not have one of the targeted test paths, run the nearest existing action-builder, cost-model, CLI, and diagnostics tests and record the substitution in the completion summary.

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
