# Task 304: Rewrite Lookback Momentum Daily Report With Revised Prompt

# Goal

Rewrite the existing Lookback Return Momentum daily report using the revised daily-report prompt, workflow, template, and style rules completed in Task 303.

This is a one-report artifact revision task. The implementation should update the already generated Korean report so it reflects the new interpretation-centered daily-report guidance, while preserving the underlying saved backtest facts and research-only boundary.

# Source Requirement

Owner request (Korean):

```text
daily report 다시 작성해주는 task 만들어줘. 바뀐 프롬프트로
```

Clean requirement:

- Create a bounded task to rewrite the current daily report with the changed prompt/workflow from Task 303.
- Apply the revised Korean daily-report style to the existing Lookback Return Momentum report artifact.
- Do not rerun backtests, tune strategy parameters, regenerate strategy outputs, or change strategy/backtest code.
- Preserve saved-result facts, existing image references, payload semantics, and research-only framing.

# Extracted Roles

- Owner role:
  - Requests a follow-up task that rewrites the daily report with the newly changed prompt.
  - Owns final publication/editorial approval.
- Supporting roles:
  - Report writer role: revise the Korean daily-report markdown using the Task 303 prompt/style/workflow.
  - Fact-preservation role: verify report statements against existing saved payload/report artifacts before editing.
  - Documentation/status role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.
- Forbidden roles:
  - No new backtest execution.
  - No parameter tuning/search.
  - No strategy/model implementation or refactor.
  - No candle backfill.
  - No saved-run database mutation.
  - No image generation or regeneration unless a broken Markdown reference requires a narrow repair and the reason is recorded.
  - No payload metric changes except narrow text/metadata alignment if the report rewrite makes an existing narrative field stale.
  - No frontend/backend/API changes.
  - No live trading behavior.
  - No exchange order/account/private endpoints.
  - No secrets or `.env` changes.

# Context

- Task 301 generated the Lookback Return Momentum daily-report artifact under `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/`.
- Task 302 revised the report copy for clearer concrete wording and Markdown readability.
- Task 303 updated the reusable daily-report prompt/workflow/style/template documents so future Korean reports are interpretation-centered and avoid awkward phrasing or absent-artifact mentions.
- This task applies those Task 303 reusable rules to the existing report artifact; it does not create a new strategy result.

Primary artifact to revise:

- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md`

Reference artifacts/docs to read before editing:

- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json`
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/image_generation_prompt.md`
- Relevant strategy document for the report subject, if report wording touches strategy assumptions or research/live-trading boundary.

# Scope

- Rewrite `report-ko.md` using the revised Task 303 daily-report guidance.
- Preserve the existing saved-result metrics, date window, timeframe coverage, image filenames, and research-only/live-trading boundary.
- Make the report interpretation-centered:
  - Explain what the experiment tested.
  - Summarize what happened in the saved result.
  - Explain likely causes using available saved facts.
  - Describe what to add/remove/change in the next experiment.
- Avoid awkward or discouraged wording documented in Task 303.
- Avoid main-narrative mentions of absent patterns, absent filters, uncreated images, or unavailable intervals unless they are decision-relevant; if relevant, place them in limitations or next improvements.
- Enrich representative win/loss trade descriptions with available context from the payload/report data without inventing unsupported facts.
- Keep same-folder Markdown image references valid.

# Out of Scope

- New backtest execution or reportable research run.
- Parameter search, tuning, or model development.
- Strategy/model/backtest source-code changes.
- Candle downloader or database changes.
- Regenerating chart/image assets unless a broken reference requires a narrow repair.
- Creating a new daily report for a different strategy/window.
- Backend, frontend, API, dashboard, scheduler, Docker, or deployment changes.
- Live trading, paper-trading behavior changes, exchange order/account/private endpoint calls, secrets, or `.env` changes.

# Requirements

- Read the root state files and this task before editing.
- Read the Task 303 daily-report docs listed in Context before editing.
- Compare report claims against `payload.json` and existing report artifacts before changing factual language.
- Rewrite the report in Korean with a natural publication-oriented tone.
- Preserve all numeric result claims unless directly supported by `payload.json` or existing saved artifacts.
- Do not invent pattern/filter/market-state details that are not available in the artifact data.
- Keep image references relative to the report folder and do not move assets.
- If `payload.json` contains report-facing text that directly conflicts with the rewritten report, update only the matching text field and document why.
- Update project state files after execution.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 304 is the current assigned task.
- [x] Read the Task 303 daily-report docs listed in Context.
- [x] Read `report-ko.md` and `payload.json` for the existing Lookback Return Momentum report.
- [x] Record any missing artifact data or wording ambiguity before editing.

## After Implementation

- [x] Update `STATUS.md` with the task result, blockers, and next task.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if this task is completed, blocked, split, or creates follow-up work.
- [x] Leave uncertain checklist items open and document the uncertainty.

# Acceptance Criteria

- `report-ko.md` is rewritten according to the revised Task 303 prompt/workflow/style rules.
- The report no longer relies on awkward discouraged phrasing from prior feedback.
- The report's interpretation section clearly covers experiment intent, observed saved result, likely causes, and next improvements.
- Representative trade sections include richer available context or explicitly avoid unsupported invented detail.
- The rewritten report preserves saved metrics, date window, image references, and research-only framing.
- No backtest, tuning/search, strategy/code change, DB mutation, candle backfill, frontend/backend/API change, live trading behavior, exchange private/order endpoint call, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Not required unless implementation changes code, which is out of scope.

## Integration Tests

- Not required unless implementation changes code, which is out of scope.

## Contract Tests

- Verify the report uses only existing local image filenames and saved payload facts.
- Verify Markdown image references still point to existing same-folder files.

## Safety Tests

- Confirm no live trading, exchange order/account/private endpoint, secret, or `.env` change was added.
- Confirm no new backtest or parameter tuning/search was run.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Saved-result facts preserved.
- Report uses revised prompt/workflow/style guidance.
- No unsupported claims or invented market-state details.
- Same-folder image references remain valid.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.

# Verification

Suggested verification commands:

```bash
python - <<'PY'
from pathlib import Path
report = Path('reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md')
payload = Path('reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json')
assert report.exists(), report
assert payload.exists(), payload
text = report.read_text(encoding='utf-8')
for token in ['summary_equity_curve.png', 'cost_impact.png', 'representative_win_trade.png', 'representative_loss_trade.png']:
    assert token in text, token
    assert (report.parent / token).exists(), token
print('report and image references ok')
PY
```

Optional, if the environment has the normal project test dependencies:

```bash
pytest
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
