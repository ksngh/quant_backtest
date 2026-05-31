# Goal

Create a repair-and-validation research task that addresses the Task 284 failure modes by making the strategy testable across multiple independent BTCUSDT 1m periods, not only the overlapping 2026-05-20 and 2026-05-25 owner windows.

The task must implement a reusable multi-window validation runner, then use it to repair or replace the Task 283/284 candidate only if the repaired strategy survives realistic fee/spread/slippage costs, multiple non-overlapping windows, side/regime attribution checks, and overfit diagnostics.

# Source Requirement

Owner asked to create a follow-up task to complement the suspicious Task 284 result and ensure the strategy can be tested across multiple periods:

- "그걸 보완하기위한 task를 만들어줘."
- "여러 구간에서 테스트 할 수 있어야해"

# Extracted Roles

- Owner role: define the research target, require multi-period validation, and decide whether later Task 285 execution is assigned.
- Supporting roles: quant researcher, system trading strategy designer, market microstructure researcher, backtest validation engineer, persistence/test engineer.
- Forbidden roles: live trader, real exchange order executor, API-key manager, frontend/backend feature owner, futures/leverage implementer.

# Context

Task 284 found no detected persistence or fee-accounting bug in the Task 283 best candidate, but rejected robustness:

- Task 283/284 best candidate: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.
- Owner replay from 2026-05-20: run `960`, `+5.7327pct`, `62` completed trips, total cost `40,593.49`, cost mismatch `0`.
- Owner replay from 2026-05-25: run `961`, `+3.5337pct`, `17` completed trips, total cost `19,432.60`, cost mismatch `0`.
- Available pre-owner replay from 2026-05-10 to 2026-05-17: run `962`, `-2.6638pct`, `54` completed trips.
- Pre-owner high-slippage stress: run `989`, `-8.6028pct`.
- 2026-05-20 attribution was short-side concentrated: LONG net approximately `-2,125.15`, SHORT net approximately `+59,452.47`.
- Return without top-three winners on 2026-05-20 stayed positive but dropped to approximately `+2.0213pct`, below the owner target.
- Local BTCUSDT 1m data starts at `2026-05-10T00:00:00Z`, not `2026-04-20T00:00:00Z`.
- Local data has an internal gap from `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z`, missing about `3400` 1m candles.
- The 2026-05-20 and 2026-05-25 windows overlap, so passing both is not an independent OOS claim.

Therefore Task 285 must not treat the fixed owner windows as sufficient. It must make complete, non-overlapping, configurable windows a first-class validation object and must explicitly reject candidates that only work because of side concentration, endpoint dependence, missing-data artifacts, or cost underestimation.

# Scope

- Add a Task 285 research runner under `quant_bitcoin/backtesting/`.
- Add focused tests under `tests/backtesting/`.
- Generate a markdown report at `reports/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`.
- Persist every executed Task 285 backtest or diagnostic run to the existing database with explicit metadata:
  - `research.task_id=TASK_285`
  - parent task/candidate references when replaying Task 283/284 logic
  - strategy/candidate name
  - window name, start, end, candle count, and gap status
  - cost assumptions and cost audit summary
  - pass/fail gate outcomes
- Reuse existing Task 283/284 helpers where appropriate, but do not silently change their historical results.
- Support arbitrary multi-window testing through CLI/config inputs.
- Split available local data into complete non-overlapping validation windows before judging robustness.
- Repair or replace the rejected candidate with deterministic OHLCV-based factors, indicators, or patterns only inside this task.

# Out of Scope

- Live trading.
- Real Binance order execution.
- Signed exchange requests.
- API keys or `.env` changes.
- Futures, leverage, margin, liquidation engine assumptions, or portfolio optimization.
- Frontend or backend API changes.
- Dashboard work.
- Machine learning models.
- Retrospectively editing Task 283 or Task 284 persisted results.
- Claiming production readiness.

# Requirements

- Read `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, this task file, and relevant Task 283/284 files before implementation.
- Perform a data coverage audit before every multi-window run.
- Detect missing candles and split available data into contiguous complete ranges.
- Support at least these window modes:
  - explicit named windows, for example `--window name:start:end`
  - a JSON or markdown-adjacent config file describing named windows
  - auto-discovered complete windows from local BTCUSDT 1m data
  - fixed owner replay windows for comparison only
  - non-overlapping validation windows for robustness decisions
- Default to conservative handling of incomplete windows:
  - skip incomplete windows for pass/fail decisions unless explicitly marked as diagnostic
  - record gap start/end and missing candle count in the report
  - do not interpolate or forward-fill candles for trading simulation
- Include predeclared default windows from available local data:
  - `available_pre_owner_0510_0517`: 2026-05-10 to 2026-05-17T15:19, diagnostic/OOS where complete enough
  - `owner_segment_0520_0522`: non-overlapping segment beginning 2026-05-20
  - `owner_segment_0522_0524`
  - `owner_segment_0524_0526`
  - `owner_segment_0526_latest`
  - `owner_0520_full`: replay/diagnostic only
  - `owner_0525_full`: replay/diagnostic only because it overlaps `owner_0520_full`
- If later data backfill exists, include these additional independent windows:
  - `oos_0420_0427`
  - `oos_0427_0504`
  - `oos_0504_0510`
  - any complete weekly windows discovered between 2026-04-20 and latest
- Implement or reuse a normalized window result model that records:
  - total return
  - net PnL
  - gross PnL
  - total costs
  - fee, spread, and slippage components
  - completed round trips
  - long/short net PnL and trade counts
  - max drawdown
  - win rate
  - profit factor
  - expectancy
  - average and median R where available
  - average holding time
  - top-winner contribution
  - return without top 1 and top 3 winners
  - endpoint-trim result
  - cost-stress result
  - data gap status
- Keep signal and execution separated:
  - signal uses completed candle data only
  - execution occurs on a later candle or with an explicitly recorded shifted-exit/shifted-entry rule
  - same-candle stop/take-profit ambiguity must use a conservative ordering
  - no future candles may be used to decide entry
- Cost handling must be realistic and auditable:
  - non-zero taker fee per execution
  - entry and exit fees
  - spread cost
  - slippage cost
  - volatility slippage or minimum slippage where available
  - formula-level cost audit mismatch count must be `0`
  - summary-level cost audit mismatch must be `0`
  - include no-cost diagnostics only as diagnostics, never as pass criteria
- Repair work must specifically address Task 284 weaknesses:
  - short-side concentration after 2026-05-20
  - long sleeve losing or cost-dominated behavior
  - pre-owner cost dominance
  - overlapping-window false confidence
  - endpoint sensitivity
  - top-winner dependence
  - regime dependence
- Candidate repair options may include deterministic versions of:
  - side-regime gate using completed higher-timeframe trend proxies from resampled candles
  - short-only mode with explicit single-side declaration and stricter OOS tests
  - long/short separate sleeve validation before combining
  - cost-aware entry gate based on expected move versus round-trip cost
  - volatility/activity regime selector
  - session/liquidity filter
  - stop-distance floor so noise and cost do not dominate
  - take-profit or trailing exit that remains fee-adjusted positive
  - cooldown and duplicate-signal suppression
  - outlier-capped sizing
- The task must run repeated in-task implementation/backtest/revision batches if the first repaired candidate fails, unless a hard blocker is reached:
  - missing data prevents the required independent windows
  - runtime exceeds a documented limit
  - safety boundary would be violated
  - owner explicitly pauses or redirects
- Every tested candidate must be persisted to DB and included in the report, including rejected candidates.
- The report must clearly separate:
  - owner-window replay results
  - independent validation results
  - incomplete-window diagnostics
  - fee/slippage stress tests
  - side/regime/session attribution
  - overfit conclusion
  - whether the candidate is still research-only

# Pass / Fail Gates

A Task 285 candidate may be labeled `ROBUST_MULTI_WINDOW_RESEARCH_CANDIDATE` only if all applicable gates pass:

- At least `4` independent non-overlapping complete validation windows are tested when data allows.
- If fewer than `4` complete windows are locally available, the task must mark the result `DATA_LIMITED_RESEARCH_ONLY`, even if returns are positive.
- Total completed round trips across independent pass/fail windows must be at least `50`.
- Each primary independent OOS window with enough candles should have at least `10` completed round trips, unless the candidate is explicitly low-frequency and the report labels the sample-size limitation.
- Net return must be positive after realistic costs in at least `75pct` of independent windows.
- Aggregate net return across independent windows must exceed `+3pct` after realistic costs.
- No single independent window may contribute more than `60pct` of aggregate net PnL.
- Return without the top three winners must remain positive or the candidate must be rejected for outlier dependence.
- Long and short sleeves must be reported separately.
- If only one side is profitable, the strategy must be explicitly reclassified as single-side and retested with the other side disabled.
- Pre-owner or earliest available OOS window must not be materially cost-dominated:
  - cost/gross ratio must be reported
  - if gross PnL is positive but net PnL is negative due to costs, the report must explain and fail the candidate unless the repaired cost gate removes the behavior
- Fee/spread/slippage stress must be tested at `1x`, `2x`, and `3x`.
- `2x` cost stress must not turn the independent aggregate result below `-1pct`.
- `3x` cost stress must be reported and may fail the promotion gate.
- Formula-level and summary-level cost audit mismatches must be `0`.
- Fixed 2026-05-20 and 2026-05-25 windows may not be the only passing evidence.
- Any data gap must be visible in the report and excluded from pass/fail calculations unless explicitly approved in the task implementation notes.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `tasks/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`.
- [x] Read Task 283 and Task 284 implementation/report files relevant to candidate replay and cost audit behavior.
- [x] Confirm the current active task is Task 285 before coding.
- [x] Confirm no frontend/backend/API/live-trading scope is needed.
- [x] Record available data coverage and any missing-window blocker before running candidate batches.

## After Implementation

- [x] Update `STATUS.md` with Task 285 outcome, blocker state, and next task.
- [x] Append Task 285 completion or blocker summary to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark Task 285 completed, blocked, or split.
- [x] Save the Task 285 report under `reports/`.
- [x] Record all persisted run IDs in the report and status/history entries.
- [x] Leave uncertain checklist items open and document uncertainty.

# Acceptance Criteria

- A Task 285 runner exists and can execute BTCUSDT 1m strategy validation across multiple named windows.
- The runner supports arbitrary window definitions without code edits.
- The runner detects gaps and prevents incomplete windows from silently passing robustness gates.
- The runner persists every run/diagnostic to DB with Task 285 metadata.
- The runner can replay the Task 283/284 best candidate as a baseline.
- At least one repaired or replacement deterministic strategy candidate is implemented and evaluated, unless data coverage is a documented hard blocker.
- Multiple candidate batches are attempted if earlier candidates fail and no hard blocker exists.
- Cost audit mismatch count is computed and reported for every persisted run.
- Long/short, session/regime, endpoint, and outlier attribution are included in the report.
- The report gives a clear final status:
  - `ROBUST_MULTI_WINDOW_RESEARCH_CANDIDATE`
  - `DATA_LIMITED_RESEARCH_ONLY`
  - `ROBUSTNESS_REJECTED_RESEARCH_ONLY`
  - `BLOCKED`
- No live trading behavior, real order endpoint, signed request, API key, `.env`, futures, or leverage behavior is added.

# Required Tests

## Unit Tests

- Window parser accepts multiple explicit named windows and rejects malformed window definitions.
- Data gap detector identifies missing 1m candle ranges and reports missing candle counts.
- Complete-window splitter returns contiguous non-overlapping ranges.
- Cost audit recomputation catches intentional mismatches and passes exact persisted-style cost formulas.
- Side attribution computes long-only and short-only net PnL/trade counts correctly.
- Outlier attribution computes top winner contribution and return excluding top winners.
- Pass/fail gate evaluator rejects overlapping-only positive evidence.

## Integration Tests

- A small deterministic OHLCV fixture runs through at least three configured windows and produces separate persisted-style result summaries.
- A fixture with an internal candle gap marks the affected window as incomplete and excludes it from pass/fail gates.
- A replay fixture verifies that Task 283/284 candidate metadata is preserved when used as the baseline.
- A repaired candidate fixture persists or serializes Task 285 metadata including `research.task_id=TASK_285`.

## Contract Tests

- Existing strategy/backtest persistence contracts remain backward compatible.
- Task 283 and Task 284 tests continue to pass.
- No public backend/frontend API contract changes are introduced by this task.
- Saved metadata includes enough fields for future report/dashboard inspection without requiring live exchange data.

## Safety Tests

- No Binance order/account/private endpoint is imported or called.
- No `.env` or API-key material is read or written.
- Task 285 runner is offline-only and uses local candles/persisted data.
- No futures/leverage/margin assumptions are introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Multi-window support is genuinely configurable.
- Incomplete data cannot silently pass.
- Owner fixed windows are treated as diagnostics, not independent OOS proof.
- Strategy status remains research-only unless every Task 285 gate passes.

# Verification

Default:

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py -q
python -m compileall -q quant_bitcoin
git diff --check
```

If Task 285 implementation adds a CLI entry point, also run the smallest deterministic fixture command and one local BTCUSDT 1m dry research run with DB persistence enabled.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- persisted run IDs
- cost audit result
- multi-window pass/fail result
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary

- Files changed:
  - `quant_bitcoin/backtesting/t285_regime_robust_multi_window_strategy_repair.py`
  - `tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py`
  - `reports/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `tasks/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`
- Implementation summary:
  - Added an offline-only Task 285 runner with configurable named windows, JSON window config support, auto complete-range helpers, gap detection, complete-window splitting, realistic `1x`/`2x`/`3x` cost profiles, DB persistence, markdown reporting, and no live-trading behavior.
  - Replayed the locked Task 283/284 candidate as a baseline and evaluated three deterministic repair candidates: short-only, regime-filtered short, and core-only short.
  - Treated fixed owner windows as diagnostic-only and used five non-overlapping independent windows for Task 285 pass/fail gates.
  - Persisted DB runs `1001`-`1020` and `1041`-`1052` with `research.task_id=TASK_285`.
- Tests added or updated:
  - Added focused Task 285 tests for window parsing, gap detection, complete-range splitting, action filtering, stress cost profiles, follow-up spec generation, overlapping-only rejection, and safety imports.
- Tests run:
  - `pytest tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py -q`
  - `pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py -q`
  - `python -m compileall -q quant_bitcoin`
  - `git diff --check`
- Persisted run IDs:
  - `1001`-`1020`, `1041`-`1052`.
- Cost audit result:
  - Formula mismatch count `0` and summary mismatch count `0` for every persisted Task 285 run.
- Multi-window pass/fail result:
  - Final status `ROBUSTNESS_REJECTED_RESEARCH_ONLY`.
  - Selected repair candidate `T285_R3_CORE_SHORT_ONLY_B2`.
  - Independent aggregate return `+3.1737pct`, but only `19` completed trips, positive windows `60pct`, return without top-three winners `-2.2531pct`, earliest OOS cost dominated, and `2x` cost stress aggregate return `-3.6686pct`.
- Codex self-review result:
  - Scope respected; no frontend/backend/API/live-trading changes; no secrets; no exchange order endpoints; tests and verification run.
- Known limitations:
  - Local BTCUSDT 1m data still starts at `2026-05-10T00:00:00Z` and has the `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z` internal gap.
  - Task 285 repaired candidates remain short-side/single-side research diagnostics and are not promoted.
- Recommended next task:
  - Create or execute a data repair/backfill task for missing BTCUSDT 1m coverage, then rerun locked multi-window/OOS validation on complete data before any further promotion claim.
