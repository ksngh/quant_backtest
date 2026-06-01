# Task 292: Report-Facing Strategy Version Naming

# Goal

Remove task/candidate identifiers from report-facing payloads, graph titles, folder names, and image filenames. Use a reader-facing strategy name and strategy version instead.

The report reader should see names like:

```text
priority_ensemble_activity_scout_v1_equity_curve.png
priority_ensemble_activity_scout_v1_drawdown.png
priority_ensemble_activity_scout_v1_cost_breakdown.png
```

not names containing internal task/candidate identifiers such as:

```text
t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002
T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002
```

# Source Requirement

Owner request:

```text
리포트를 쓰는 입장에서는 task 몇번인지 관심이 없어.. 그냥 strategy랑 그 strategy버전 으로 해야해. 지금은 모든 사진에 T_이라고 적혀있거든. 이거 치우고 STRATEGY_V1_그래프 종류. 이런식으로 가야해
```

Clean requirement:

- Blog/report artifacts must hide task numbers and internal candidate IDs from reader-facing names.
- Strategy/report naming must use a user-facing `strategy_name` and `strategy_version`.
- Existing Task 291 artifact must be renamed/regenerated to use the report-facing naming convention.
- The report-facing `strategy_name` must be the actual strategy name, not a generic placeholder.
- Graph image titles must not include `Task`, `TASK`, `T281`, `T287`, run IDs, or internal candidate IDs.
- Payload title fields must use report-facing strategy/version naming.

# Extracted Roles

- Owner role:
  - Wants report artifacts to read like productized strategy versions, not internal task logs.
- Supporting roles:
  - Naming contract writer: update daily-report rules and handoff prompt.
  - Artifact migrator: rename/regenerate the existing Task 291 artifact folder and PNG files.
  - Payload updater: add reader-facing strategy/version fields and remove internal candidate IDs from blog-facing fields.
  - Chart regenerator: regenerate image titles with report-facing names.
  - Validator: ensure no report-facing payload/image filenames/titles contain task IDs or candidate IDs.
- Forbidden roles:
  - No new strategy development.
  - No new backtest execution.
  - No DB schema migration.
  - No frontend/backend/API changes.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No API keys, secrets, or `.env` changes.

# Context

Task 291 created this colocated artifact folder:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/
```

That folder and the graph titles still expose the internal candidate ID `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.

The owner clarified that report readers do not care which task created the strategy. The blog/report layer needs its own reader-facing identity.

# Scope

- Read:
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/template.md`
  - current Task 291 payload and images.
- Update blog rules to require a reader-facing identity block, for example:

```json
{
  "title": {
    "strategy_name": "Priority Ensemble Activity Scout",
    "strategy_version": "V1",
    "strategy_label": "Priority Ensemble Activity Scout V1",
    "market_summary": "Binance BTCUSDT 1m",
    "period": "2026-04-20 00:00:00 UTC ~ 2026-05-19 23:59:00 UTC",
    "pr": "https://github.com/ksngh/quant_backtest/pull/167"
  }
}
```

- Define naming rules:
  - Folder: `reports/blog_payloads/{strategy_slug}/{strategy_version_slug}/{period_slug}/`
  - Image filename: `{strategy_slug}_{strategy_version_slug}_{graph_kind}.png`
  - Graph title: `{Strategy Label} - {Graph Name}`
  - Markdown title: `# {Strategy Label} 백테스트 리포트`
- For the existing migrated artifact, use the actual report-facing strategy identity:
  - `strategy_name`: `Priority Ensemble Activity Scout`
  - `strategy_version`: `V1`
  - `strategy_label`: `Priority Ensemble Activity Scout V1`
  - `strategy_slug`: `priority-ensemble-activity-scout`
  - `strategy_version_slug`: `v1`
- Keep internal source identifiers only in task reports, not in report-facing payload fields, image filenames, or graph titles.
- Regenerate or rename current images to:

```text
priority_ensemble_activity_scout_v1_equity_curve.png
priority_ensemble_activity_scout_v1_drawdown.png
priority_ensemble_activity_scout_v1_price_with_trades.png
priority_ensemble_activity_scout_v1_trade_pnl_distribution.png
priority_ensemble_activity_scout_v1_cost_breakdown.png
priority_ensemble_activity_scout_v1_side_attribution.png
priority_ensemble_activity_scout_v1_exit_reason_attribution.png
```

- Move/regenerate artifact to:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

- Remove or archive the old report-facing folder with internal ID naming after the new folder is verified.
- Save a Task 292 report under `reports/`.

# Out of Scope

- No final blog report writing unless a later task explicitly asks for it.
- No new backtest execution.
- No strategy retuning.
- No metric changes.
- No DB mutation.
- No DB schema change.
- No frontend/backend/API/dashboard changes.
- No live trading.
- No exchange order/account/private endpoints.
- No API keys, secrets, or `.env` changes.

# Requirements

- Blog-facing payload must contain `strategy_name`, `strategy_version`, and `strategy_label`.
- Blog-facing payload title must not expose task IDs or internal candidate IDs.
- Blog-facing artifact folder must not expose task IDs or internal candidate IDs.
- Blog-facing image filenames must not expose task IDs or internal candidate IDs.
- Graph titles rendered into PNGs must not expose task IDs or internal candidate IDs.
- Payload image references must remain filenames only.
- All referenced images must exist in the same folder as `payload.json`.
- Internal IDs may be documented only in `reports/TASK_292_...md`, not in `payload.json`.
- The old Task 291 folder with `t281...` naming must be removed after the new folder is verified, unless removing it would delete unrelated files.
- The implementation must not call exchange order endpoints.
- The implementation must not place orders.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 292 is the assigned task.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no newer owner message changes the report-facing naming convention.
- [x] Confirm the Task 291 artifact folder exists.
- [x] Confirm the target report-facing identity to use for the current artifact.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a Task 292 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `docs/blog/backtest_report_data_rules.md` defines report-facing strategy/version naming.
- `docs/blog/daily_report_workflow.md` routes new artifacts to strategy/version/period folders.
- `docs/blog/agent_handoff_prompt.md` tells writing agents to use `strategy_label`, not internal IDs.
- Current artifact exists under:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

- The folder contains:
  - `payload.json`
  - `priority_ensemble_activity_scout_v1_equity_curve.png`
  - `priority_ensemble_activity_scout_v1_drawdown.png`
  - `priority_ensemble_activity_scout_v1_price_with_trades.png`
  - `priority_ensemble_activity_scout_v1_trade_pnl_distribution.png`
  - `priority_ensemble_activity_scout_v1_cost_breakdown.png`
  - `priority_ensemble_activity_scout_v1_side_attribution.png`
  - `priority_ensemble_activity_scout_v1_exit_reason_attribution.png`
- `payload.json` references only those filenames.
- `payload.json` does not contain `T281`, `T287`, `TASK`, `Task`, `run_id`, `candidate_id`, or the full internal candidate ID.
- Referenced PNG filenames do not contain `T281`, `T287`, `TASK`, `Task`, or candidate IDs.
- PNG titles do not visibly include `T281`, `T287`, `TASK`, `Task`, or candidate IDs.
- The old report-facing artifact folder with the `t281...` slug is removed after verification.
- No new backtest is executed.
- No database mutation is performed.
- No live trading, exchange order endpoint, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required unless reusable naming or chart-generation code is added.
- If reusable code is added, test:
  - strategy/version slug generation.
  - image filename generation.
  - internal ID redaction from payload fields.

## Integration Tests

- Verify the new artifact folder exists.
- Verify referenced image files exist and are non-empty.
- Verify the old internal-ID folder is removed or empty.

## Contract Tests

- Validate JSON parseability.
- Validate required top-level payload keys.
- Validate title fields include report-facing `strategy_name`, `strategy_version`, and `strategy_label`.
- Search payload for internal ID markers:
  - `T281`
  - `T287`
  - `TASK`
  - `Task`
  - `candidate_id`
  - `run_id`
- Validate image references are filenames only.

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
python -m json.tool reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json >/dev/null
python - <<'PY'
import json
from pathlib import Path
folder = Path("reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519")
payload = json.loads((folder / "payload.json").read_text())
assert payload["title"]["strategy_name"] == "Priority Ensemble Activity Scout"
assert payload["title"]["strategy_version"] == "V1"
assert payload["title"]["strategy_label"] == "Priority Ensemble Activity Scout V1"
for marker in ["T281", "T287", "TASK", "Task", "candidate_id", "run_id"]:
    assert marker not in json.dumps(payload, ensure_ascii=False), marker
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
    assert "T281" not in name and "T287" not in name and "TASK" not in name and "Task" not in name
    path = folder / name
    assert path.exists(), path
    assert path.stat().st_size > 0, path
print("report_facing_names_ok")
PY
test ! -e reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002
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

# Execution Result

- Updated the task from generic `Strategy V1` examples to the actual report-facing identity:
  - `strategy_name`: `Priority Ensemble Activity Scout`
  - `strategy_version`: `V1`
  - `strategy_label`: `Priority Ensemble Activity Scout V1`
  - `strategy_slug`: `priority-ensemble-activity-scout`
  - `strategy_version_slug`: `v1`
- Updated daily-report data rules, workflow rules, handoff prompt, and template title placeholder so future reports use actual strategy/version naming.
- Regenerated the current report artifact from saved run `1159` using read-only DB access and saved it under:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

- Regenerated these report-facing image files:
  - `priority_ensemble_activity_scout_v1_equity_curve.png`
  - `priority_ensemble_activity_scout_v1_drawdown.png`
  - `priority_ensemble_activity_scout_v1_price_with_trades.png`
  - `priority_ensemble_activity_scout_v1_trade_pnl_distribution.png`
  - `priority_ensemble_activity_scout_v1_cost_breakdown.png`
  - `priority_ensemble_activity_scout_v1_side_attribution.png`
  - `priority_ensemble_activity_scout_v1_exit_reason_attribution.png`
- Regenerated `payload.json` so title fields, image references, report-copy strings, representative trade reasons, and attribution labels no longer expose internal task/candidate identifiers.
- Removed the old report-facing artifact folder:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/
```

- Saved the Task 292 completion report at `reports/TASK_292_REPORT_FACING_STRATEGY_VERSION_NAMING.md`.
- No new backtest was executed.
- No database mutation was performed.
- No live trading behavior, exchange order endpoint behavior, secret, or `.env` change was added.

# Verification Result

```bash
python -m json.tool reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json >/tmp/task292_payload_check.json
rg -n "T281|T287|TASK|Task|candidate_id|run_id" reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/payload.json
python - <<'PY'
import json
from pathlib import Path
folder = Path("reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519")
payload = json.loads((folder / "payload.json").read_text())
assert payload["title"]["strategy_name"] == "Priority Ensemble Activity Scout"
assert payload["title"]["strategy_version"] == "V1"
assert payload["title"]["strategy_label"] == "Priority Ensemble Activity Scout V1"
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
    assert name.startswith("priority_ensemble_activity_scout_v1_"), name
    path = folder / name
    assert path.exists(), path
    assert path.stat().st_size > 0, path
assert len(set(image_refs)) == 7, image_refs
print("task292_payload_refs_ok")
PY
test ! -e reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002
for f in reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/*.png; do strings "$f" | rg -n "T281|T287|TASK|Task|candidate_id|run_id" && exit 1 || true; done
git diff --check
```

- JSON parse: passed.
- Required title strategy/version fields: passed.
- Filename-only image references: passed.
- All referenced colocated PNG files exist and are non-empty.
- Payload internal marker search: no matches.
- PNG embedded string marker search: no matches.
- Old internal-ID artifact folder removal: passed.
- `git diff --check`: passed.
