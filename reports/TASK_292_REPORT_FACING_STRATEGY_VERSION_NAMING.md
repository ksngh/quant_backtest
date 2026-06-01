# TASK 292 Report-Facing Strategy Version Naming

## Source

- Internal source persisted run: `1159` used for read-only graph/trade/cost/attribution extraction.
- Internal source strategy id: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Report-facing strategy name: `Priority Ensemble Activity Scout`.
- Report-facing strategy version: `V1`.
- Report-facing strategy label: `Priority Ensemble Activity Scout V1`.
- Period: `2026-04-20 00:00:00 UTC ~ 2026-05-19 23:59:00 UTC`.

## Naming Change

Task 291 stored the report artifact under an internal candidate slug. Task 292 replaces that reader-facing path and all image names with strategy/version naming.

New artifact folder:

```text
reports/blog_payloads/priority-ensemble-activity-scout/v1/20260420-20260519/
```

Current files:

```text
payload.json
priority_ensemble_activity_scout_v1_equity_curve.png
priority_ensemble_activity_scout_v1_drawdown.png
priority_ensemble_activity_scout_v1_price_with_trades.png
priority_ensemble_activity_scout_v1_trade_pnl_distribution.png
priority_ensemble_activity_scout_v1_cost_breakdown.png
priority_ensemble_activity_scout_v1_side_attribution.png
priority_ensemble_activity_scout_v1_exit_reason_attribution.png
```

Removed legacy report-facing folder:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/
```

## Payload Changes

- Added report-facing title identity:
  - `strategy_name`: `Priority Ensemble Activity Scout`
  - `strategy_version`: `V1`
  - `strategy_label`: `Priority Ensemble Activity Scout V1`
- Replaced image references with `priority_ensemble_activity_scout_v1_*` filenames.
- Removed internal task/candidate labels from payload title fields, daily-report copy, representative trade reasons, and exit-reason attribution labels.
- Kept source/internal identifiers only in this internal task report, not in the blog-facing payload.

## Generated Images

- Equity curve: `Priority Ensemble Activity Scout V1 - Equity Curve`
- Drawdown: `Priority Ensemble Activity Scout V1 - Drawdown`
- Price/trade markers: `Priority Ensemble Activity Scout V1 - Price With Trades`
- Trade PnL distribution: `Priority Ensemble Activity Scout V1 - Trade PnL Distribution`
- Cost breakdown: `Priority Ensemble Activity Scout V1 - Cost Breakdown`
- Side attribution: `Priority Ensemble Activity Scout V1 - Side Attribution`
- Exit reason attribution: `Priority Ensemble Activity Scout V1 - Exit Reason Attribution`

## Verification

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

Results:

- JSON parse: passed.
- Required title fields: passed.
- Filename-only image references: passed.
- All referenced PNG files exist and are non-empty.
- Payload internal marker search: no matches.
- PNG embedded string marker search: no matches.
- Old internal-ID report-facing folder removed.
- `git diff --check`: passed.

## Safety

- No new backtest was executed.
- No database mutation was performed.
- No live trading behavior was added.
- No exchange order/account/private endpoint was called.
- No secret or `.env` file was created or modified.

## Known Limitations

- Image verification checks filenames, file existence, file size, and embedded string markers. It does not perform OCR against rendered chart pixels.
- Trade PnL distribution still uses saved exit execution `net_pnl` proxy. Official result metrics remain lifecycle attribution based.

## Next Task

- Use this payload when the owner asks for the actual Korean daily report markdown for `Priority Ensemble Activity Scout V1`.
