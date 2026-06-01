# Task 290: Save Recent Backtest Report Payload

# Goal

Save a compact daily-report payload and report-ready graph images for the most recent relevant saved backtest result so it can be handed to an agent that writes a Korean daily backtest report with `docs/blog/template.md`.

This task does not create a final blog report. It creates the saved payload and graph image files that the reporting workflow can consume.

# Source Requirement

Owner request:

```text
ㅇㅋ 그럼 이번에 돌린거 한번 저장해보자
```

Owner clarification:

```text
아니 그리고 혹시 테스트하고 저기형식에 넣을 그래프 사진까지 만들어 줄 수 있나??
```

Owner clarification:

```text
결과 그래프를 추가하는 거까지 rule에 넣어줘.
```

Clean requirement:

- Use the daily-report workflow created in Task 289.
- Save the result data for the most recent relevant backtest/validation run into a compact payload.
- The saved payload must follow `docs/blog/backtest_report_data_rules.md`.
- The payload must be usable by `docs/blog/agent_handoff_prompt.md`.
- Generate report-ready graph images from the selected saved run when graph/equity data is available.
- Save graph image filenames into the payload `images` fields so they can be used by the template image markdown.
- Update the daily-report rules so result graph generation and markdown image wiring are mandatory when saved graph data is available.
- Run validation checks for payload JSON, required keys, forbidden fields, and generated image files.
- Do not run a new backtest unless a later task explicitly says to do so.
- Do not create a final blog report in this task.

# Extracted Roles

- Owner role:
  - Wants the most recent backtest result saved in the new daily-report payload format.
- Supporting roles:
  - Result resolver: determine which saved run is meant by "이번에 돌린거".
  - Payload builder: map saved run metrics, costs, setup, interpretation, and representative trades into `backtest_report_payload`.
  - Chart builder: generate equity curve and, if data is available, drawdown PNG files from the selected saved run.
  - Validation role: check the payload is valid JSON and does not include forbidden blog-payload fields.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No new strategy development.
  - No new model search.
  - No new backtest execution unless this task is later expanded by the owner.
  - No DB schema migration.
  - No frontend/backend/API changes.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No API keys, secrets, or `.env` changes.

# Context

Task 289 created:

- `docs/blog/template.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/daily_report_workflow.md`

Those documents define how to save a small result payload and how a later agent should turn that payload into a report.

The template expects graph references like:

```markdown
![백테스트 결과 그래프](./images/[graph-name].png)
```

Therefore this task should save graph files in a stable `images/` directory near the payload/report artifacts and put only the image filenames in the payload, following `docs/blog/backtest_report_data_rules.md`.

The current conversation has many saved research/backtest runs from Tasks 277-287. The latest completed backtest-validation work is Task 287, which persisted runs `1085`-`1159` and documented a rejected primary strategy. No new backtest was run during the PR publishing step; only verification tests and PR creation were performed.

Assumption for this task:

- "이번에 돌린거" means the most recent relevant saved backtest/validation result from the current research sequence, not the PR verification test commands.
- If a single latest relevant saved run cannot be resolved unambiguously, stop and record the ambiguity instead of inventing values.

# Scope

- Read `docs/blog/backtest_report_data_rules.md`.
- Read `docs/blog/daily_report_workflow.md`.
- Ensure `docs/blog/backtest_report_data_rules.md`, `docs/blog/daily_report_workflow.md`, and `docs/blog/agent_handoff_prompt.md` require result graph image handling:
  - equity curve PNG when saved graph data exists.
  - optional drawdown PNG when an equity series is available.
  - image filenames only in payload fields.
  - no synthetic graph from invented values.
- Resolve the target saved run using this precedence:
  - explicit owner-provided run id if the owner adds one before execution.
  - latest saved run referenced in the current task/history context.
  - latest persisted research/backtest run from the most recent completed backtest task.
  - if multiple plausible target runs remain, stop and record the ambiguity.
- Read the selected saved run and its available summary/trade/cost metadata from existing persistence.
- Build one compact `backtest_report_payload`.
- Save the payload as JSON under `reports/blog_payloads/`.
- Generate an equity curve PNG under `reports/blog_payloads/images/` when graph/equity points are available.
- Generate a drawdown PNG under `reports/blog_payloads/images/` when enough equity points are available.
- Put only the generated image filenames into:
  - `images.equity_curve`
  - `images.drawdown`
- If graph data is unavailable, store image fields as `null` and document why.
- Save a short Task 290 note under `reports/` explaining:
  - which internal run was used.
  - which fields were complete.
  - which fields were saved as `null`.
  - which graph images were generated or why graph generation was unavailable.
  - why no final blog report was generated yet.
- Include PR information in the payload using PR #167 or its URL if appropriate.
- Keep internal run id/config/commit out of the payload itself.

# Out of Scope

- No final daily report generation.
- No new backtest execution.
- No synthetic graph generation from invented values.
- No strategy implementation.
- No model retuning.
- No DB schema change.
- No database mutation beyond reading existing saved run data.
- No frontend/backend/API/dashboard changes.
- No live trading.
- No exchange order/account/private endpoints.
- No API keys, secrets, or `.env` changes.

# Requirements

- The saved JSON payload must follow the top-level structure from `docs/blog/backtest_report_data_rules.md`:
  - `title`
  - `images`
  - `setup`
  - `hypothesis_and_theory`
  - `metrics`
  - `illusion_checks`
  - `representative_trades`
  - `interpretation`
- Missing values must be stored as `null`, not invented.
- Generated chart images must be based only on selected saved-run graph/equity data.
- Daily-report rules must say result graph images are generated and referenced when saved graph/equity data is available.
- The equity curve image should be visually usable in a blog report:
  - PNG format.
  - title includes strategy name and tested period when available.
  - x-axis uses time or ordered graph point index.
  - y-axis uses equity/final value units available in the saved run.
  - drawdowns or losses should not be hidden by smoothing.
- The drawdown image is optional, but if generated it must use the same equity series as the equity curve.
- The payload image fields must contain filenames only, not absolute paths.
- The payload must not include:
  - `experiment_id`
  - `run_id`
  - `data_version`
  - `experiment_config`
  - `artifact_path`
  - `git_commit`
  - `output_files`
  - full internal config dumps.
- The payload may include `title.pr`.
- The Task 290 report may mention the internal run id for traceability, but the payload must not.
- Representative trades must be selected from persisted trades when available:
  - best trade.
  - worst trade.
  - typical winner.
  - typical loser.
- If representative trades are unavailable or incompatible with the saved run format, store those entries as `null` and document the limitation.
- Fee, spread, and slippage fields must come from persisted cost metadata or trade-level cost fields. If they are unavailable, store `null` and document the limitation.
- Validation must confirm:
  - payload JSON parses.
  - required top-level keys exist.
  - forbidden fields are absent.
  - generated PNG files exist and are non-empty when image filenames are present.
- The implementation must not call exchange order endpoints.
- The implementation must not place orders.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 290 is the assigned task.
- [x] Confirm no newer owner message changes the target run.
- [x] Confirm whether a specific run id was provided.
- [x] Confirm the selected saved run is read-only input.
- [x] Record any target-run ambiguity before payload creation.
- [x] Confirm whether selected run has graph/equity data for PNG generation.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a Task 290 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A payload file exists under `reports/blog_payloads/`.
- The blog/report workflow rules mention result graph image creation and markdown wiring.
- An equity curve PNG exists under `reports/blog_payloads/images/` if saved graph/equity data is available.
- A drawdown PNG exists under `reports/blog_payloads/images/` if enough equity data is available.
- Payload `images` fields contain generated filenames or `null`.
- The payload is valid JSON.
- The payload follows `docs/blog/backtest_report_data_rules.md`.
- The payload omits forbidden blog-payload fields such as `run_id`, `git_commit`, and full config dumps.
- The payload includes PR information if available.
- Missing values are represented as `null`.
- A short Task 290 report exists under `reports/`.
- No new backtest is executed.
- Graph generation uses only selected saved-run data.
- No live trading, exchange order endpoint, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Not required unless new reusable payload-building code is added.
- If a reusable mapper is added, add focused tests for:
  - required top-level payload keys.
  - missing values mapping to `null`.
  - forbidden fields omitted.
  - image filenames are stored without absolute paths.

## Integration Tests

- If the payload is built from DB persistence, run a read-only extraction command and verify the output file exists.
- If graph images are generated, verify the PNG files exist and are non-empty.

## Contract Tests

- Validate JSON parseability.
- Validate required top-level keys.
- Search the payload for forbidden field names.
- Validate payload image fields match generated filenames or `null`.

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
python -m json.tool reports/blog_payloads/<payload-file>.json >/dev/null
rg -n '"run_id"|"git_commit"|"experiment_id"|"data_version"|"experiment_config"|"artifact_path"|"output_files"' reports/blog_payloads/<payload-file>.json
test -s reports/blog_payloads/images/<equity-curve-file>.png
python - <<'PY'
from pathlib import Path
payload = Path("reports/blog_payloads/<payload-file>.json")
image = Path("reports/blog_payloads/images/<equity-curve-file>.png")
assert payload.exists()
assert image.exists()
assert image.suffix == ".png"
assert image.stat().st_size > 0
PY
test -f reports/TASK_290_SAVE_RECENT_BACKTEST_REPORT_PAYLOAD.md
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

- Source run resolved to latest completed persisted validation run `1159` for `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`, window `pre_owner_0420_0519`, cost profile `high_slippage_stress`.
- Saved compact payload to `reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json`.
- Generated equity curve PNG at `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png`.
- Generated drawdown PNG at `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png`.
- Saved traceability note at `reports/TASK_290_SAVE_RECENT_BACKTEST_REPORT_PAYLOAD.md`.
- No new backtest was executed.
- No database mutation was performed.
- Official performance values in the payload use persisted entry-to-final-exit lifecycle attribution.

# Verification Result

```bash
python -m json.tool reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json >/tmp/task290_payload_check.json
rg -n '"(run_id|experiment_id|data_version|experiment_config|git_commit|artifact_path|artifact_paths|output_files|next_experiment|appendix|checklist)"' reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json
test -s reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png
test -s reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png
git diff --check
```

- JSON parse: passed.
- Required top-level payload keys: passed.
- Forbidden payload fields: no matches.
- PNG non-empty checks: passed.
- `git diff --check`: passed.
