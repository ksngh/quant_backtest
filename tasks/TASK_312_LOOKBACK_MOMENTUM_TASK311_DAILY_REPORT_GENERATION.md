# Task 312: LOOKBACK_MOMENTUM_TASK311_DAILY_REPORT_GENERATION

# Goal

Generate a Tistory-ready Korean daily report from the completed Task 311 `LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC` results.

# Source Requirement

Owner request on 2026-06-02:

> ㅇㅋ daily report 만들어줘

Interpreted as: use the latest completed Task 311 momentum ATR reward/cost geometry diagnostic and create a full daily report artifact. This task is the required execution task because no relevant daily-report task existed when the request was made.

# Extracted Roles

- Owner role:
  - Requests a publishable daily report from the Task 311 result.
- Supporting roles:
  - Report artifact builder: create the colocated report folder, payload, required charts/images, and `report-ko.html`.
  - Data interpreter: summarize Task 311 result without changing saved metrics or rerunning the backtest.
  - Style/template follower: follow the current `docs/blog` daily-report workflow, template, style, payload, image, handoff, and HTML template rules.
  - Strategy context reader: read the `LOOKBACK_RETURN_MOMENTUM` strategy document so the report opens with strategy-level explanation rather than raw run labels.
- Forbidden roles:
  - Backtest runner.
  - Strategy/code implementer.
  - Parameter optimizer.
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend/API implementer.

# Context

Task 311 completed after Task 309 showed symmetric `1 ATR` stop/target geometry could not pass the cost-aware gate. Task 311 tested:

- stop fixed at `1 ATR`;
- take-profit candidates `2.0`, `2.5`, `3.0 ATR`;
- minimum ATR bps candidates `0.0`, `20.0`;
- cost profile `conservative_crypto_1m`;
- cost-aware gate preserved with `min_net_reward_bps=0.0`, `min_net_rr=1.0`, `liquidity_role=TAKER`;
- `BTCUSDT` `1m`, `5m`, and `15m`;
- window `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.

Task 311 persisted runs `1192`-`1209`, saved raw JSON and manifest under `reports/task_311_atr_reward_cost_geometry_raw_outputs/`, and saved the task report at `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`.

Key result to preserve:

- Asymmetric ATR targets made entries cost-feasible.
- `1m` accepted entries started at `2.5 ATR`.
- `5m` and `15m` accepted entries started at `2.0 ATR`.
- Every filled variant was net negative after costs.
- `minimum_atr_bps=20.0` reclassified many low-ATR candidates as `ATR_TOO_SMALL_FOR_COST` but did not change accepted trades or PnL.

# Scope

- Read required state files and this task before implementation.
- Read:
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `reports/TASK_311_LOOKBACK_RETURN_MOMENTUM_ATR_REWARD_COST_GEOMETRY_DIAGNOSTIC.md`
  - `reports/task_311_atr_reward_cost_geometry_raw_outputs/manifest.json`
  - relevant Task 311 raw JSON files as needed
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/image_generation_prompt.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/report_template.html`
- Create a colocated daily-report artifact under:

```text
reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/
```

- Create at minimum:
  - `payload.json`
  - `report-ko.html`
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `reward_cost_geometry.png`
  - `accepted_entries_by_variant.png`
- Use Task 311 saved outputs only. Do not run a new backtest.
- Prefer generated matplotlib/plotly/static charts from saved data over AI-generated imagery.
- Use filename-only image references in `payload.json` and same-folder relative image references in `report-ko.html`.
- Ensure report-facing title is strategy/version-centered, for example `Lookback Return Momentum V1`, not a verbose experiment label.
- Include a concise strategy description in the opening, not raw exchange/run framing.
- Include version-change or experiment-change summary in `핵심요약`, such as moving from symmetric `1 ATR` target to asymmetric `2.0/2.5/3.0 ATR` target candidates.
- Preserve the current `백테스트 설정` style from the workflow.
- Interpret both:
  - why entries became cost-feasible after increasing target distance;
  - why filled variants still lost after costs.
- End with `해석` and reasoned improvement direction.

# Out of Scope

- New backtest execution.
- Parameter tuning/search beyond interpreting Task 311 saved results.
- Strategy/code changes.
- Strategy document changes unless a factual inconsistency blocks report generation.
- Database mutation.
- Candle backfill.
- Existing report artifact rewrites outside the new Task 312 artifact folder.
- Frontend/backend/API changes.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- The report must be `report-ko.html`, not Markdown.
- The HTML must follow the current Tistory-oriented workflow:
  - primary desktop review target: `1392px * 708px`;
  - responsive behavior for narrower viewports;
  - use `docs/blog/report_template.html` as layout/reading-flow reference.
- The report must not expose internal task IDs, run IDs, candidate IDs, or raw file names in reader-facing prose unless needed in a non-reader-facing payload/debug field.
- The report must not use awkward wording prohibited by the current style guide, including `그것은`.
- The report must avoid "기본값" phrasing unless the style guide explicitly allows the context.
- The report must not say real orders were not placed or use obvious backtest disclaimers.
- The report must make the central result clear:
  - reward/cost geometry was fixed enough to allow fills;
  - realized trade quality still did not cover costs.
- The payload must preserve saved numerical facts from Task 311:
  - candidates, accepted entries, cost-blocked entries, ATR-too-small entries, invalid ATR blocks, completed trades, gross PnL, net PnL, cost, return, expectancy/hit ratio where available.
- The report must include purposeful tables only where they improve readability. Avoid overly wide raw grid tables in the article body; use charts or compact summary tables when the full grid is too dense.
- Use only saved Task 311 data for metrics.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Read Task 311 report and manifest.
- [x] Read required daily-report workflow/style/template/image/payload docs.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- A new artifact folder exists at `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/`.
- `payload.json` exists, is valid JSON, and references images by filename only.
- `report-ko.html` exists and is a Tistory-ready Korean HTML report.
- Required PNG images exist and are non-empty:
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `reward_cost_geometry.png`
  - `accepted_entries_by_variant.png`
- Report content follows the current docs/blog workflow and style rules.
- Report metrics match Task 311 saved data.
- No new backtest, DB mutation, strategy/code change, live trading behavior, order/account/private endpoint usage, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless helper code is added.

## Integration Tests

- Not required unless reusable exporter code is added.

## Contract Tests

- Validate JSON:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null
```

- Verify required artifacts exist and PNG files are non-empty.
- Verify payload image references are filename-only.
- Verify `report-ko.html` references same-folder image filenames.
- Verify forbidden report-facing wording from the current style guide is absent.
- Run:

```bash
git diff --check
```

## Safety Tests

- Confirm no code/report workflow added by this task calls exchange order/account/private endpoints.
- Confirm no API keys, secrets, or `.env` files are added or modified.
- Run a focused diff grep for:

```bash
rg -n "api[_-]?key|secret|\\.env|create_order|new_order|/api/v3/order|account endpoint|private endpoint|SIGNED|ENABLE_LIVE_TRADING"
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
- Existing Task 311 saved metrics preserved.
- Daily-report style and HTML workflow followed.

# Verification

Default:

```bash
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null
git diff --check
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# Completion Summary

- Files changed:
  - `tasks/TASK_312_LOOKBACK_MOMENTUM_TASK311_DAILY_REPORT_GENERATION.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/report-ko.html`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/summary_equity_curve.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/cost_impact.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/reward_cost_geometry.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/accepted_entries_by_variant.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_win_trade.png`
  - `reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/representative_loss_trade.png`
- Implementation summary:
  - Generated the colocated Tistory-ready `report-ko.html` from saved Task 311 outputs only.
  - Generated `payload.json` with sanitized metrics and filename-only image references.
  - Generated six same-folder PNGs at `1392px * 708px`, including required summary/cost/reward/entry charts plus representative win/loss trade charts.
  - Preserved the Task 311 numerical results without running a new backtest or mutating DB/code/strategy files.
- Tests added or updated:
  - None. No reusable helper code was added.
- Tests run:
  - `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-atr-reward-cost/payload.json >/dev/null`
  - artifact existence/non-empty/image-reference verification script
  - visible HTML forbidden-word and nesting verification script
  - `sips -g pixelWidth -g pixelHeight` for all generated PNGs
  - focused artifact safety grep for order/account/private endpoint and live-trading markers
  - `git diff --check`
- Codex self-review result:
  - Passed. Scope stayed within Task 312; no new backtest, DB mutation, strategy/code change, live trading behavior, exchange order/account/private endpoint usage, secret, or `.env` change was introduced.
- Known limitations:
  - The report is a publication artifact from the already saved Task 311 result; it does not add new validation evidence or tune parameters.
- Recommended next task:
  - Create a bounded `LOOKBACK_RETURN_MOMENTUM` trade-quality diagnostic that tests a stronger ATR floor derived from cost geometry, directional continuation confirmation, or time-of-day/liquidity filtering.

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
