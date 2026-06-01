# Task 294: Colocated Daily Report Payload Image Regeneration

# Goal

Update the daily-report artifact contract again per owner correction, then regenerate the current report payload and chart images so `payload.json` and all PNG images live in the same report-specific directory.

The owner explicitly does not want `report-ko.md`, `report-en.md`, `image_plan.md`, or an `images/` subdirectory for this artifact generation pass.

# Source Requirement

Owner request:

```text
오케 그럼 이거에 맞춰서 다시 진행해보자.
기존에 있던 이미지랑 json은 지우고.
아니근데 report-ko.md는 생성하지 않아도 되는데.
image_plan이랑.
그냥 여기서는 payload와 image들만 있으면 돼.
그리고 images/ 내부로 안옮겨도 돼.
그냥 payload.json이랑 images들은 같은 디렉토리 내부에 있게끔 해주고, 이미지랑 payload 뽑아줘
```

Clean requirement:

- Replace the Task 293 `images/` subdirectory and image-plan artifact requirement for this workflow.
- The report artifact folder should contain only `payload.json` and generated PNG images.
- Do not generate `report-ko.md`.
- Do not generate `report-en.md`.
- Do not generate `image_plan.md` or `image_plan.json`.
- Do not create or use an `images/` subdirectory for this artifact.
- Delete the existing report-facing payload/images for the current saved report artifact before regenerating them.
- Regenerate `payload.json` and chart PNG files from the saved backtest result.

# Extracted Roles

- Owner role:
  - Defines the final artifact layout.
  - Wants actual payload and image files generated now.
  - Does not want markdown reports or image-plan files in this pass.
- Supporting roles:
  - Data contract updater: align docs/rules with colocated `payload.json` and image files.
  - Artifact generator: regenerate the current saved-run report payload and images.
  - Validator: confirm old payload/images are removed, new payload/images are colocated, non-empty, and internally referenced correctly.
- Forbidden roles:
  - No new strategy development.
  - No new backtest execution unless a missing source artifact makes regeneration impossible and the owner explicitly approves a later task.
  - No DB mutation.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No API keys, secrets, or `.env` changes.
  - No frontend/backend/API/dashboard changes.

# Context

Task 292 regenerated the current report-facing payload and images for `Priority Ensemble Activity Scout V1` under:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

Task 293 then updated the future document contract to:

```text
daily_report/YYYY-MM-DD-[strategy-slug]/
  report-ko.md
  report-en.md
  payload.json
  image_plan.md
  images/
```

The owner has now corrected that artifact contract. For this pass, the desired artifact should not contain markdown reports, image-plan files, or an `images/` subfolder. It should contain only:

```text
[report-folder]/
  payload.json
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
  [optional variant or attribution PNG files]
```

The source saved run should be the same current report source used by Tasks 290-292 unless implementation finds a newer explicitly relevant saved result in the existing task history. Earlier tasks resolved run `1159` read-only as the current report source.

# Scope

Allowed files and artifacts:

- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/template.md`
- `docs/blog/image_generation_prompt.md`
- Current report artifact folder to be regenerated.
- Optional traceability report under `reports/`.
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

Allowed actions:

- Update daily-report docs so generated artifact folders contain colocated `payload.json` and PNG files.
- Remove or supersede Task 293 rules requiring `images/`, `image_plan.md`, `report-ko.md`, and `report-en.md` for this artifact workflow.
- Delete the existing current report-facing `payload.json` and PNG images before regeneration.
- Regenerate `payload.json` and PNG chart images from the saved result using read-only data access.
- Keep report-facing strategy/version naming and avoid internal task/run/candidate IDs in payload copy, image filenames, and chart titles.
- Save generated images in the same directory as `payload.json`.

# Out of Scope

- Do not generate `report-ko.md`.
- Do not generate `report-en.md`.
- Do not generate `image_plan.md`.
- Do not generate `image_plan.json`.
- Do not place images under an `images/` subdirectory.
- Do not execute a new backtest.
- Do not mutate DB records.
- Do not create live-trading behavior.
- Do not call exchange order/account/private endpoints.
- Do not add secrets, API keys, `.env`, or signed exchange requests.
- Do not change frontend/backend/API/dashboard code.

# Requirements

## Artifact Layout

Use a report-specific folder with colocated payload and images:

```text
[report-folder]/
  payload.json
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

The final implementation must choose and document the concrete `[report-folder]`.

Preferred folder if no better current project convention is selected during implementation:

```text
daily_report/YYYY-MM-DD-[strategy-slug]/
```

but without `report-ko.md`, `report-en.md`, `image_plan.md`, or `images/`.

## Existing Artifact Cleanup

- Delete the existing current report-facing `payload.json` and PNG images before regenerating.
- Do not delete unrelated reports or task reports.
- Do not remove saved backtest DB records.
- If multiple candidate artifact folders exist, only remove the one being regenerated and record the path.

## Payload Requirements

- Save the new payload as `payload.json`.
- Use report-facing `strategy_name`, `strategy_version`, and `strategy_label`.
- Do not expose task number, run id, internal candidate id, config dump, git commit, DB dump, or source file paths in final report-facing payload fields.
- Image references in payload must be colocated filenames only, not `./images/...`.
- Include enough data for `docs/blog/template.md`:
  - summary.
  - setup.
  - hypotheses.
  - strategy assumptions and theory.
  - rules.
  - cost assumptions.
  - metrics.
  - cost impact.
  - illusion/overfit checks.
  - representative trades.
  - interpretation.

## Image Requirements

Required generated PNGs:

```text
summary_equity_curve.png
cost_impact.png
representative_win_trade.png
representative_loss_trade.png
```

`summary_equity_curve.png`:

- Must show equity curve and drawdown in the same image.
- Must be generated from saved equity/graph data only.
- Must not create a separate default `drawdown_curve.png`.

`cost_impact.png`:

- Must show transaction cost impact using saved cost fields.
- If cost-level equity curves are unavailable, use aggregate gross PnL, fee, spread, slippage, total transaction cost, and net PnL.
- Chart title/labels must not use `cost stress`.

`representative_win_trade.png` and `representative_loss_trade.png`:

- Prefer candlestick charts when source candle/trade-window data is available.
- Must show entry/exit markers and available stop/target/pattern-zone data.
- If candle-window data is unavailable, generate a clear fallback chart using available trade metadata and record the limitation in payload/report metadata.

Optional images:

- Additional colocated PNGs are allowed when they improve report usefulness, such as:
  - `trade_pnl_distribution.png`
  - `side_attribution.png`
  - `exit_reason_attribution.png`
  - `price_with_trades.png`
  - variant `10_equity_curve_...png` or `20_cost_impact_...png`

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 294 is the assigned task.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm the owner correction supersedes the Task 293 `images/` and image-plan rules for this artifact generation pass.
- [x] Identify the current artifact folder to delete/regenerate.
- [x] Identify the saved result source to use without running a new backtest.
- [x] Record assumptions, blockers, or unclear status items before implementation.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a Task 294 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Implementation Notes

- Selected report folder:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

- Updated the daily-report artifact rules so this workflow generates only `payload.json` and PNG files in the same report folder.
- Removed the Task 293 default requirement for `report-ko.md`, `report-en.md`, `image_plan.md`, `image_plan.json`, and an `images/` subdirectory from this payload/image workflow.
- Deleted the previous current report-facing `payload.json` and PNG files in the selected report folder before regeneration.
- Regenerated `payload.json` and eight colocated PNG images from the saved result using read-only data access.
- Corrected the report-facing total return display to `-35.5861%` from the saved final equity/net PnL relationship, then regenerated `summary_equity_curve.png` and `cost_impact.png` so chart annotations match the payload.
- Required PNGs generated:
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- Optional PNGs generated:
  - `price_with_trades.png`
  - `trade_pnl_distribution.png`
  - `side_attribution.png`
  - `exit_reason_attribution.png`
- No new backtest was executed.
- No DB mutation was performed.
- No live trading, exchange order/account endpoint, secret, or `.env` behavior was added.

# Verification Results

Passed:

```bash
test -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json
test -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/summary_equity_curve.png
test -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/cost_impact.png
test -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/representative_win_trade.png
test -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/representative_loss_trade.png
test ! -d reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/images
test ! -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/report-ko.md
test ! -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/report-en.md
test ! -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/image_plan.md
test ! -f reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/image_plan.json
python -m json.tool reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json >/dev/null
find reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519 -maxdepth 1 -name '*.png' -size +0c -print
rg -n '"filename":\s*"[^"]*/|"path":\s*"[^"]*/|markdown_path|\.\/images|images/' reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json
rg -n 'T281|T287|TASK|Task|candidate_id|run_id' reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json
find reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519 -maxdepth 1 -name 'priority_ensemble_activity_scout_v1_*' -print
find reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519 -maxdepth 1 -type f ! -name 'payload.json' ! -name '*.png' -print
git diff --check
```

Notes:

- The `rg` commands for disallowed payload references and internal markers returned no matches.
- PNG embedded-string marker checks with `strings` returned no disallowed internal markers.

# Acceptance Criteria

- Relevant docs no longer require `report-ko.md`, `report-en.md`, `image_plan.md`, `image_plan.json`, or `images/` for this payload/image artifact workflow.
- The old current report-facing payload/images are removed before regeneration.
- A new `payload.json` exists in the selected report folder.
- Required PNG files exist in the same directory as `payload.json`:
  - `summary_equity_curve.png`
  - `cost_impact.png`
  - `representative_win_trade.png`
  - `representative_loss_trade.png`
- No `images/` subdirectory is created for the regenerated artifact.
- No `report-ko.md`, `report-en.md`, `image_plan.md`, or `image_plan.json` is created for the regenerated artifact.
- `payload.json` references colocated image filenames only.
- Generated PNG files are non-empty.
- The payload and chart titles do not expose task number, run id, internal candidate id, or `T281`/`T287`/`TASK` markers.
- No new backtest is executed.
- No DB mutation is performed.
- No live trading, exchange order endpoint, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required if only docs and artifact generation scripts are used.
- If reusable exporter/image code is added, add focused tests for:
  - colocated image filename generation.
  - payload image reference shape.
  - no `images/` subdirectory references.
  - internal marker filtering.

## Integration Tests

- Verify the selected artifact folder exists.
- Verify `payload.json` exists.
- Verify required PNGs exist and are non-empty.
- Verify no `images/` subdirectory exists in the artifact folder.
- Verify no markdown report or image-plan file exists in the artifact folder.

## Contract Tests

- Verify docs mention colocated `payload.json` and images.
- Verify docs do not require `./images/[filename].png` for this artifact payload.
- Verify docs say image references in payload are filenames only.
- Verify required image filenames appear in docs and payload.
- Verify payload image filenames do not contain `/`.

## Safety Tests

- Confirm no `.env`, API key, private key, DB dump, CSV dump, or secret file is created.
- Confirm no code path calls exchange order/account/private endpoints.
- Confirm no DB mutation command is introduced.
- Confirm regeneration uses read-only saved-run/source data.

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
test -f [report-folder]/payload.json
test -f [report-folder]/summary_equity_curve.png
test -f [report-folder]/cost_impact.png
test -f [report-folder]/representative_win_trade.png
test -f [report-folder]/representative_loss_trade.png
test ! -d [report-folder]/images
test ! -f [report-folder]/report-ko.md
test ! -f [report-folder]/report-en.md
test ! -f [report-folder]/image_plan.md
test ! -f [report-folder]/image_plan.json
python -m json.tool [report-folder]/payload.json >/dev/null
find [report-folder] -maxdepth 1 -name '*.png' -size +0c -print
rg -n "\"filename\": \"[^\"]*/|\"markdown_path\": \"\\.\\/images/" [report-folder]/payload.json && exit 1 || true
rg -n "T281|T287|TASK|Task|candidate_id|run_id" [report-folder]/payload.json [report-folder]/*.png && exit 1 || true
git diff --check
```

Expected notes:

- `rg ... [report-folder]/*.png` may not inspect binary PNG content reliably on every platform. If it cannot inspect PNG text chunks, use `strings` against PNGs for internal marker checks.
- If representative trade candlestick windows are unavailable, fallback images are acceptable only if the payload records the limitation.

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
