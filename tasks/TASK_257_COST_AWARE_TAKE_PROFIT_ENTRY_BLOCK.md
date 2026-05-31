# Task 257: Cost-Aware Take-Profit Entry Block

# Goal

Block simulated entries when the configured take-profit/target price would still produce a non-positive net result after transaction costs, spread, and slippage.

For the current FVG v2 channel strategy, this means:

- At entry construction time, compute the executable target from the channel width.
- Compute the expected gross reward from entry price to that executable target.
- Estimate round-trip costs from the active cost profile/config.
- If target hit would be net loss or zero/insufficient positive reward, emit a deterministic `SKIP` instead of an entry.

# Source Requirement

Owner clarified:

```text
진입했을 때 손익비를 계산해서 익절선에서 익절해도 손해가 나면 거래하면 안돼..
```

Owner then clarified the FVG v2 channel target/stop formula:

```text
익절 선은 채널만큼의 거리야.
숏을 친다고 가정해보자. 손절라인은 추세선 위쪽 라인에 닿았을 때가 손절라인일테고,
익절라인은 아랫쪽 선과 윗쪽 선의 차이만큼을 지금 비트코인 가격에서 뺀 만큼 내려갔을 때인거야.
롱으로 치면, 상승 추세선과 하락 추세선만큼의 차이만큼을 지금 가격에서 더한만큼에서 익절인거고,
하락 추세선에 닿으면 손절인거야
```

Clean requirement:

- Do not enter a trade if reaching the intended take-profit line would still lose money after fees/spread/slippage.
- For FVG v2 channel entries, replace the prior opposite-channel-line target with a channel-width projection from the entry/current price:
  - `channel_width_at_entry = upper_line_price_at_entry - lower_line_price_at_entry`
  - LONG target = `entry_price + channel_width_at_entry`
  - SHORT target = `entry_price - channel_width_at_entry`
- For stop lines:
  - SHORT stop = upper channel line at the relevant candle index.
  - LONG stop = lower-side stop. If existing Task 251 retest-structure-low policy remains active, implementation must explicitly decide whether owner's "하락 추세선에 닿으면 손절" supersedes it or whether structure-low remains an extra conservative stop.
- The reason must be inspectable in metadata so skipped trades are explainable.

# Extracted Roles

- Owner role:
  - Defines the economic entry constraint: no trade when the best intended target is cost-negative.
  - Defines FVG v2 channel target distance as one channel width from entry/current price.
- Supporting roles:
  - Strategy/backtest role: blocks candidate entries before executable actions are generated.
  - Risk/exit role: changes channel target calculation from opposite-line target to channel-width projection.
  - Cost model role: estimates round-trip fee/spread/slippage using existing transaction-cost config/cost profile.
  - Metadata role: records channel width, projected target, stop source, gross reward, estimated cost, net reward, net R/R, and block reason.
  - Test role: adds deterministic positive/negative net target fixtures.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, account endpoints, or order endpoints.
  - Do not optimize strategy parameters for profitability.
  - Do not hide skipped candidates; they must be visible as `SKIP` diagnostics.
  - Do not change cost model semantics outside the assigned entry-block rule.

# Context

Existing code already has `CostAwareEntryFilterConfig` and `_cost_aware_entry_filter_decision()` in `quant_bitcoin/backtesting/pattern_action_builder.py`. That path estimates gross reward bps, round-trip cost bps, net reward bps, and net R/R for generic pattern entries. However, recent FVG v2 channel actions are built by `build_fvg_channel_trade_actions()` and currently do not consistently block channel entries when the target line is too close to overcome realistic costs.

Task 256 changed FVG v2 channel entry direction:

- upper-boundary retest -> LONG,
- lower-boundary retest -> SHORT,
- prior implementation still targets the opposite channel line.

The owner now clarified that the target should be projected one full channel width from the entry/current price, not simply the opposite channel boundary. Because channel targets can still be too close after costs, any target that is net-negative after `conservative_crypto_1m` costs should not be entered.

# Scope

- Update FVG v2 channel target calculation:
  - channel width is the distance between upper and lower channel lines at entry candle index,
  - LONG target is entry/current price plus channel width,
  - SHORT target is entry/current price minus channel width.
- Update FVG v2 channel exit simulation so take-profit checks use the projected target price, not the opposite boundary line, unless later explicitly configured otherwise.
- Preserve stop behavior explicitly:
  - SHORT stop uses the upper channel line.
  - LONG stop policy must be made explicit in metadata. If Task 251 structure-low stop remains, also record the owner-stated lower-line stop reference.
- Extend or reuse the existing cost-aware entry filter for FVG v2 channel actions.
- Ensure the filter can evaluate:
  - LONG: target reward = target price - entry price,
  - SHORT: target reward = entry price - target price.
- Estimate round-trip costs using the same transaction-cost config/liquidity role/cost profile used by the backtest engine.
- Block entry when:
  - gross reward is non-positive, or
  - net reward after estimated round-trip costs is less than or equal to zero, or
  - configured minimum net reward/minimum net R/R threshold is not met.
- Emit `StrategyActionType.SKIP` with a clear reason such as `COST_INFEASIBLE_TAKE_PROFIT`.
- Preserve diagnostic metadata:
  - `gross_reward_bps`,
  - `estimated_round_trip_cost_bps`,
  - `net_reward_bps`,
  - `net_rr`,
  - `min_net_reward_bps`,
  - `min_net_rr`,
  - `entry_price`,
  - `target_price`,
  - `stop_price`,
  - `channel_width_at_entry`,
  - `target_price_source`,
  - `projected_channel_width_target`,
  - `cost_profile_name`,
  - `liquidity_role`,
  - `cost_aware_entry_filter`.
- Wire the strategy runner/CLI so the filter uses the active `--cost-profile conservative_crypto_1m` or explicit cost args.
- Keep default behavior explicit and documented:
  - either always enforce `net_reward_bps > 0` for channel mode when costs are configured,
  - or add a clearly named default-on guardrail flag for channel mode.

# Out of Scope

- No live trading.
- No exchange order/account endpoints.
- No new optimizer or profitability auto-selection.
- No frontend redesign.
- No database schema migration unless existing JSON metadata cannot carry the skip diagnostics.
- No change to Task 256 channel direction rules.
- No change to raw/effective execution price semantics.
- No pyramiding or simultaneous positions.

# Requirements

- FVG v2 channel entries must not be emitted when their intended target is cost-negative.
- FVG v2 channel take-profit target must be projected by one channel width from the entry/current price:
  - LONG target = entry + channel width.
  - SHORT target = entry - channel width.
- FVG v2 channel target metadata must distinguish the projected width target from the older opposite-boundary target.
- The skip reason must distinguish cost-infeasible target trades from no-fill, duplicate-channel, and open-position skips.
- The cost estimate must use the same cost profile/config as the run.
- Both LONG and SHORT channel examples must be covered.
- Existing generic pattern cost-aware filter tests must continue to pass.
- Metadata must make the decision auditable from saved actions/runs.
- No real order behavior or signed exchange call may be introduced.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read this assigned task file before coding.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/costs.py`.
- [x] Read `quant_bitcoin/backtesting/cost_profiles.py`.
- [x] Read `quant_bitcoin/patterns/fvg_channel.py`.
- [x] Confirm current cost-aware filter semantics and decide whether to reuse or adapt it.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A channel LONG fixture with target reward smaller than round-trip costs emits `SKIP`.
- A channel SHORT fixture with target reward smaller than round-trip costs emits `SKIP`.
- A channel fixture with target reward comfortably larger than costs still emits entry/exit actions.
- LONG channel target equals entry/current price plus channel width.
- SHORT channel target equals entry/current price minus channel width.
- Exit simulation uses the projected channel-width target for take-profit.
- Skip metadata includes gross reward, estimated round-trip cost, net reward, net R/R, target price, stop price, entry price, cost profile, and liquidity role.
- CLI/runner path applies the filter when a cost profile is selected.
- Existing Task 256 direction tests remain passing.
- No live trading, signed requests, credentials, account endpoints, or order endpoints are introduced.

# Required Tests

## Unit Tests

- Cost-negative LONG channel target is blocked.
- Cost-negative SHORT channel target is blocked.
- Cost-positive channel target is allowed.
- LONG projected target fixture: `target_price == entry_price + channel_width_at_entry`.
- SHORT projected target fixture: `target_price == entry_price - channel_width_at_entry`.
- LONG/SHORT take-profit hit fixtures use the projected channel-width target.
- Existing `_cost_aware_entry_filter_decision()` generic tests still pass.

## Integration Tests

- Strategy runner / action-builder test with `conservative_crypto_1m` metadata proving channel cost guard is applied.
- CLI metadata or parser test proving selected cost profile reaches the channel action builder.

## Contract Tests

- Verify skip metadata is JSON-serializable through existing action/run metadata paths.
- Update API contract if new top-level flattened fields are added.

## Safety Tests

- Confirm no live trading controls, signed requests, exchange order endpoints, account endpoints, credentials, or real exchange order behavior are introduced.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_fvg_channel.py -q
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

# Completion Summary

Completed on 2026-05-28.

- Files changed:
  - `quant_bitcoin/patterns/fvg_channel.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `backend/tests/test_backtest_results_service.py`
  - `frontend/src/types/api.ts`
  - `docs/api/API_CONTRACT.md`
  - `tests/patterns/test_fvg_channel.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `tasks/TASK_257_COST_AWARE_TAKE_PROFIT_ENTRY_BLOCK.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Changed FVG v2 channel take-profit target from opposite channel boundary to one channel width projected from entry price.
  - LONG target is `entry_price + channel_width_at_entry`; SHORT target is `entry_price - channel_width_at_entry`.
  - LONG stop now uses the lower channel line, matching the latest owner clarification; retest structure low remains diagnostic metadata only.
  - SHORT stop remains the upper channel line.
  - Added channel cost guard that auto-enables when non-zero transaction costs are configured and blocks `COST_INFEASIBLE_TAKE_PROFIT` when the projected target is not net-profitable after estimated round-trip fee/spread/slippage.
  - Wired the active transaction-cost config/cost profile into FVG event-expansion channel actions and standalone visible-prefix channel actions.
  - Exposed projected target and cost-filter metadata through saved-run service flattening, frontend API types, and API contract docs.
- Tests added or updated:
  - LONG/SHORT projected channel-width target fixtures.
  - LONG/SHORT projected take-profit exit fixtures.
  - Dynamic lower-line LONG stop fixture.
  - Cost-negative LONG and SHORT channel target block fixtures.
  - Cost-positive channel target allowed fixture.
  - CLI channel target policy metadata fixture.
  - Backend serialization fixture for projected target/cost metadata.
- Tests run:
  - `python -m py_compile quant_bitcoin/patterns/fvg_channel.py quant_bitcoin/backtesting/pattern_action_builder.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py backend/quant_backtest_api/services/backtest_results.py`
  - `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py backend/tests/test_backtest_results_service.py -q`
  - `npm --prefix frontend run typecheck`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, signed requests, credentials, account endpoints, or exchange order endpoints added.
  - Changes stayed inside FVG v2 channel target/stop/cost-aware entry semantics.
- Known limitations:
  - The cost guard estimates round-trip costs in basis points before sizing; actual realized cost can still vary with volatility-adjusted slippage and execution path.
  - The retest confirmation rule remains unchanged.
- Recommended next task:
  - Re-run the approved owner FVG v2 channel command and inspect `COST_INFEASIBLE_TAKE_PROFIT` skips, projected targets, side distribution, total costs, and equity curve.
