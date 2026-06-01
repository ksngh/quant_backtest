# Task 291: Blog Payload Artifact Layout and Multi-Image Rules

# Goal

Update the daily backtest report workflow so each report payload is stored in a strategy/date-specific artifact folder, with the payload JSON and all report images colocated in that folder. Expand the image rules beyond equity/drawdown so daily reports can include the charts needed for strategy interpretation, cost analysis, and trade quality review.

# Source Requirement

Owner request:

```text
리포트를 만드는데 이미지가 더 많이 필요하지 않아? 이미지 만드는 rule을 수정해야할 거 같고, blog_payloads에는 strategy와 날짜를 기준으로 폴더를 만들고 거기에 json과 이미지를 넣어줘. images를 따로 만드는거 말고. 그래서 blog_payloads안에, strategy와 날짜를 기준으로 폴더가 생성되고 json과 이미지 파일들이 여러개 들어있게끔 만들어줘
```

Clean requirement:

- Daily report artifacts must no longer use a shared `reports/blog_payloads/images/` directory for new payloads.
- New payload artifacts must be stored under a strategy/date-specific directory under `reports/blog_payloads/`.
- The payload JSON and all image PNG files must live in the same report artifact directory.
- The report image rules must support multiple images, not only equity curve and drawdown.
- The existing Task 290 artifact should be migrated or regenerated into the new folder layout when this task is executed.

# Extracted Roles

- Owner role:
  - Wants a cleaner blog payload folder structure and richer report image set.
- Supporting roles:
  - Rule editor: update `docs/blog/backtest_report_data_rules.md`, `docs/blog/daily_report_workflow.md`, and `docs/blog/agent_handoff_prompt.md`.
  - Artifact organizer: define and apply the `reports/blog_payloads/{strategy_slug}/{date_or_period_slug}/` layout.
  - Chart planner: define required/optional report images and when they can be generated from saved run data.
  - Payload migrator: move or regenerate the Task 290 payload and images into the new colocated folder.
  - Validator: check payload image references, folder layout, JSON validity, forbidden fields, and non-empty PNG files.
- Forbidden roles:
  - No new strategy development.
  - No new model search.
  - No new backtest execution unless explicitly added by a later task.
  - No DB schema migration.
  - No frontend/backend/API changes.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No API keys, secrets, or `.env` changes.

# Context

Task 289 created the daily report template and handoff workflow.

Task 290 saved a payload for the latest completed persisted validation run and generated two images:

- `reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json`
- `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png`
- `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png`

The owner now wants the artifact structure changed so `blog_payloads` contains a folder keyed by strategy and date, and that folder contains the JSON plus multiple images directly. That means the Task 290 shared `images/` layout should be treated as legacy and replaced for new report payloads.

# Scope

- Read:
  - `docs/blog/template.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - the Task 290 payload and images.
- Update the daily-report rules to use this folder convention for new payloads:

```text
reports/blog_payloads/{strategy_slug}/{period_slug}/
```

Example:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/
  payload.json
  equity_curve.png
  drawdown.png
  price_with_trades.png
  trade_pnl_distribution.png
  cost_breakdown.png
  side_attribution.png
  exit_reason_attribution.png
```

- Define slug rules:
  - `strategy_slug`: lowercase, ASCII, hyphen-separated, max practical length if needed.
  - `period_slug`: `YYYYMMDD-YYYYMMDD` from backtest period if available.
  - If period is unavailable, use report date `YYYYMMDD`.
- Update image rules so payload `images` can hold multiple image entries.
- Keep image references as filenames only, not absolute paths and not `./images/...`.
- Define minimum report images when saved data is available:
  - `equity_curve`: cost-adjusted equity over time.
  - `drawdown`: drawdown from the same equity series.
  - `price_with_trades`: close price with entry/exit markers when trade timestamps exist.
  - `trade_pnl_distribution`: completed trade lifecycle net PnL or R distribution when lifecycle outcomes exist.
  - `cost_breakdown`: fee/spread/slippage breakdown when cost metadata exists.
- Define optional report images when saved attribution metadata exists:
  - `side_attribution`: Long vs Short net PnL, trade count, or expectancy.
  - `exit_reason_attribution`: exit reason count and net PnL.
  - `rolling_return_or_expectancy`: rolling trade or time-window performance.
  - `regime_attribution`: volatility/session/regime result if metadata exists.
- Migrate or regenerate the current Task 290 artifacts into the new folder layout.
- Update the payload JSON so image references match the colocated files.
- Save a Task 291 report under `reports/` explaining:
  - old layout.
  - new layout.
  - generated/migrated files.
  - images generated and unavailable image reasons.
  - verification results.

# Out of Scope

- No final blog report writing unless a later task explicitly asks for it.
- No new backtest execution.
- No synthetic chart data.
- No invented strategy metrics.
- No DB schema change.
- No frontend/backend/API/dashboard changes.
- No live trading.
- No exchange order/account/private endpoints.
- No API keys, secrets, or `.env` changes.

# Requirements

- New report artifact folders must live under `reports/blog_payloads/`.
- New report artifact folders must be keyed by strategy and date/period.
- Payload JSON and all report images must be colocated in the same artifact folder.
- New payloads must not store images under `reports/blog_payloads/images/`.
- Payload image references must be filenames only.
- Payload image references must not include:
  - absolute paths.
  - `./images/`.
  - `images/`.
  - parent-directory references.
- The image schema must support multiple images without becoming a metadata-heavy artifact list.
- Recommended payload image shape:

```json
{
  "images": {
    "primary": "equity_curve.png",
    "items": [
      {
        "id": "equity_curve",
        "filename": "equity_curve.png",
        "caption": "[짧은 캡션]",
        "section": "summary"
      },
      {
        "id": "drawdown",
        "filename": "drawdown.png",
        "caption": "[짧은 캡션]",
        "section": "results"
      }
    ]
  }
}
```

- Missing images must be omitted from `images.items` or represented with `filename: null` and a clear reason field.
- The writing prompt must instruct the report agent to render images using `![caption](./filename.png)` because files are colocated with the final payload/report folder.
- The workflow must say that final markdown reports should be written or copied into the same folder if generated later, so image links remain local.
- Existing Task 290 payload values must remain semantically unchanged except for the artifact folder and image schema/path changes.
- If richer images cannot be generated from saved run data, store only the available images and document missing images in the Task 291 report.
- The implementation must not call exchange order endpoints.
- The implementation must not place orders.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 291 is the assigned task.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no newer owner message changes the requested layout.
- [x] Confirm Task 290 artifact files exist before migration/regeneration.
- [x] Confirm whether graph/trade/cost/attribution data is available for richer images.
- [x] Record any missing image inputs before chart generation.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a Task 291 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `docs/blog/backtest_report_data_rules.md` defines the new strategy/date folder layout.
- `docs/blog/daily_report_workflow.md` routes new payload creation into the new colocated folder layout.
- `docs/blog/agent_handoff_prompt.md` tells the writing agent to use colocated image filenames, not `./images/...`.
- A Task 290-compatible artifact folder exists under:

```text
reports/blog_payloads/{strategy_slug}/{period_slug}/
```

- That folder contains:
  - `payload.json`
  - `equity_curve.png`
  - `drawdown.png`
  - any additional images that can be generated from saved run data.
- The migrated/regenerated `payload.json` parses as JSON.
- The migrated/regenerated payload references only filenames for images.
- Every non-null image filename referenced by the payload exists in the same folder and is non-empty.
- The payload omits forbidden blog-payload fields such as `run_id`, `git_commit`, and full config dumps.
- A Task 291 report exists under `reports/`.
- No new backtest is executed.
- No database mutation is performed.
- No live trading, exchange order endpoint, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required unless reusable payload-layout or chart-generation code is added.
- If reusable code is added, test:
  - strategy/date slug generation.
  - filename-only image references.
  - missing image handling.
  - forbidden field omission.

## Integration Tests

- If regenerating charts from DB persistence, use read-only extraction only.
- Verify the new artifact folder exists.
- Verify referenced image files exist and are non-empty.

## Contract Tests

- Validate JSON parseability.
- Validate required top-level payload keys.
- Validate `images.primary` and `images.items[*].filename` contain filenames only.
- Validate no image reference starts with `/`, `./images/`, `images/`, or `../`.
- Search the payload for forbidden field names.

## Safety Tests

- Confirm no `.env`, API key, private key, DB dump, CSV dump, or secret file is created.
- Confirm no code path calls exchange order/account/private endpoints.

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
python -m json.tool reports/blog_payloads/<strategy_slug>/<period_slug>/payload.json >/dev/null
python - <<'PY'
import json
from pathlib import Path
folder = Path("reports/blog_payloads/<strategy_slug>/<period_slug>")
payload = json.loads((folder / "payload.json").read_text())
image_refs = []
images = payload.get("images", {})
if images.get("primary"):
    image_refs.append(images["primary"])
for item in images.get("items", []):
    filename = item.get("filename")
    if filename:
        image_refs.append(filename)
for name in image_refs:
    assert "/" not in name and not name.startswith(".")
    path = folder / name
    assert path.exists(), path
    assert path.stat().st_size > 0, path
print("image_refs_ok")
PY
rg -n '"(run_id|experiment_id|data_version|experiment_config|git_commit|artifact_path|artifact_paths|output_files|next_experiment|appendix|checklist)"' reports/blog_payloads/<strategy_slug>/<period_slug>/payload.json
git diff --check
```

The `rg` command should return no matches.

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

# Execution Result

- Updated daily-report image and artifact layout rules in `docs/blog/backtest_report_data_rules.md`.
- Updated daily-report workflow rules in `docs/blog/daily_report_workflow.md`.
- Updated writing-agent image instructions in `docs/blog/agent_handoff_prompt.md`.
- Updated `docs/blog/template.md` image examples from `./images/...` to colocated `./filename.png`.
- Migrated/regenerated the Task 290 payload into:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/
```

- Saved these colocated files:
  - `payload.json`
  - `equity_curve.png`
  - `drawdown.png`
  - `price_with_trades.png`
  - `trade_pnl_distribution.png`
  - `cost_breakdown.png`
  - `side_attribution.png`
  - `exit_reason_attribution.png`
- Removed the legacy Task 290 shared-layout files:
  - `reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json`
  - `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png`
  - `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png`
  - `reports/blog_payloads/images/`
- Updated `reports/TASK_290_SAVE_RECENT_BACKTEST_REPORT_PAYLOAD.md` to point to the Task 291 colocated artifact.
- Saved Task 291 report at `reports/TASK_291_BLOG_PAYLOAD_ARTIFACT_LAYOUT_AND_MULTI_IMAGE_RULES.md`.
- No new backtest was executed.
- No database mutation was performed.

# Verification Result

```bash
python -m json.tool reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/payload.json >/tmp/task291_payload_check.json
python - <<'PY'
import json
from pathlib import Path
folder = Path("reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519")
payload = json.loads((folder / "payload.json").read_text())
required = ["title", "images", "setup", "hypothesis_and_theory", "metrics", "illusion_checks", "representative_trades", "interpretation"]
assert all(k in payload for k in required)
image_refs = []
images = payload.get("images", {})
if images.get("primary"):
    image_refs.append(images["primary"])
for item in images.get("items", []):
    filename = item.get("filename")
    if filename:
        image_refs.append(filename)
for name in image_refs:
    assert "/" not in name and not name.startswith(".") and not name.startswith("/")
    path = folder / name
    assert path.exists()
    assert path.stat().st_size > 0
print("image_refs_ok")
PY
rg -n '"(run_id|experiment_id|data_version|experiment_config|git_commit|artifact_path|artifact_paths|output_files|next_experiment|appendix|checklist)"' reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/payload.json
test ! -e reports/blog_payloads/images
git diff --check
```

- JSON parse: passed.
- Required top-level payload keys: passed.
- Filename-only image references: passed.
- All referenced colocated PNG files exist and are non-empty.
- Forbidden payload fields: no matches.
- Legacy shared images directory removed.
- `git diff --check`: passed.
