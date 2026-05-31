# Goal

Run and save a broader backtest sweep using the currently available `ORDER_BLOCK`, `FAIR_VALUE_GAP`, Order Block confluence, and multi-timeframe settings.

# Source Requirement

Owner asked:

```text
오더블록, fvg, 글고 15m, 30m ,1h분봉 등 활용할 수 있는 모든 것들을 활용해서 백테스트 돌려줘봐
```

Interpretation:

- Use the current repo features, not new implementation.
- Save backtest runs so the owner can inspect them later.
- Include both `ORDER_BLOCK` and `FAIR_VALUE_GAP` variants.
- Include available multi-timeframe contexts such as 15m, 30m, and 1h where the current CLI supports them.
- Avoid live trading and real order execution.

# Extracted Roles

- Owner role: Wants saved broad research runs using all currently useful OB/FVG/MTF options.
- Supporting roles:
  - Research runner: Select bounded command variants and execute them with persistence enabled.
  - Backtest analyst: Record run IDs and key results.
  - Status tracker: Update task/status/history/backlog after execution.
- Forbidden roles:
  - Live trading or real exchange order execution.
  - Exchange order/account endpoint calls.
  - Strategy implementation changes.
  - Database schema changes.
  - Frontend/dashboard changes.
  - New higher-timeframe backfill implementation; Task 265 remains separate.

# Context

Current relevant completed work:

- Task 260 made the current FVG v2 channel owner profile the default for `FAIR_VALUE_GAP`.
- Task 266 added FVG same-direction Order Block confluence.
- Task 267 made the default FVG OB confluence local/fast.
- Task 270 added optional `ORDER_BLOCK` MTF filtering using completed resampled base candles.
- Task 271 changed default `ORDER_BLOCK` confirmation-close stop/target to previous-candle 1R.
- Task 273 saved `ORDER_BLOCK` candidate runs:
  - Run 98 baseline;
  - Run 99 volume 1.5x;
  - Run 100 MTF 15m;
  - Run 101 cost-aware RR 0.6 with 0 fills;
  - Run 102 61.8% retest wait-20.

Known limitation:

- Current MTF OB support is resampled from loaded base candles, not separate DB-backed 15m/30m/1h candles.
- DB-backed 1h/4h context remains Task 265 and is out of scope here.

# Scope

- Execute saved `quant-bitcoin-strategy-backtest` commands only.
- Use local stored candle data through the existing Postgres provider.
- Persist runs by omitting `--no-persist`.
- Prefer a bounded sweep, for example:
  - `ORDER_BLOCK` 61.8% retest + 15m MTF;
  - `ORDER_BLOCK` 61.8% retest + 30m MTF;
  - `ORDER_BLOCK` 61.8% retest + 1h MTF;
  - `ORDER_BLOCK` 61.8% retest + 15m,30m,1h MTF;
  - `FAIR_VALUE_GAP` default owner profile;
  - `FAIR_VALUE_GAP` default owner profile + OB confluence;
  - `FAIR_VALUE_GAP` default owner profile + OB confluence using `historical_detector` compatibility if runtime allows;
  - optional reduced/diagnostic variant if a command produces no fills.
- Record:
  - command;
  - backtest run ID;
  - trade count;
  - gross/net PnL;
  - final equity;
  - warnings;
  - any zero-fill/blocking notes.

# Out of Scope

- Code changes.
- Test changes.
- New task implementation such as Task 265 or Task 272.
- Live trading.
- Real Binance order placement.
- New data downloads or backfills.
- Dashboard/frontend changes.

# Requirements

- Save all successful runs.
- Keep the sweep bounded to avoid excessive runtime.
- Stop and report if local Postgres or the CLI is unavailable.
- Use realistic default costs unless explicitly testing diagnostic zero-cost behavior.
- Do not use `--enable-cost-aware-entry-filter` as a default in this broad sweep, because Task 273 showed relaxed cost-aware RR produced 0 fills under the current 1R OB structure.
- For FVG runs, prefer current owner defaults before adding extra filters.
- For OB MTF runs, include 15m, 30m, and 1h variants where supported by `--ob-mtf-timeframes`.

# Status Tracking

## Before Execution

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before running commands.
- [x] Confirm selected commands are existing CLI options.

## After Execution

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- At least four saved runs are attempted unless blocked by environment.
- At least one `ORDER_BLOCK` MTF saved run is attempted.
- At least one `FAIR_VALUE_GAP` saved run is attempted.
- Run IDs and summary metrics are recorded in this task document.
- No code changes are made.
- No live trading or exchange order endpoints are used.

# Required Tests

## Unit Tests

- Not applicable; this is a saved-run research task.

## Integration Tests

- Execute selected `quant-bitcoin-strategy-backtest` commands with persistence enabled.

## Contract Tests

- Confirm successful CLI outputs are parseable JSON and include `backtest_run_id`.

## Safety Tests

- Confirm commands use offline backtest CLI only.
- Confirm no live trading or exchange order/account endpoints are called.

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

Default command family:

```bash
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK ...
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP ...
```

Exact commands and saved run IDs must be recorded after execution.

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

# Execution Results

Executed on 2026-05-28 with persistence enabled. All commands used the offline strategy backtest CLI and local stored candle data; no live trading or exchange order endpoints were used.

Common options:

```bash
--start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10
```

| Variant | Saved run | Trades | Gross PnL | Net PnL | Final equity | Total cost | Elapsed | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| OB 61.8 retest + 15m MTF | 103 | 81 | 0.0715 | -9.8838 | 656.7829 | 9.9553 | 28.03s | Saved |
| OB 61.8 retest + 30m MTF | 105 | 20 | -0.0118 | -2.5385 | 664.1282 | 2.5267 | 23.88s | Saved |
| OB 61.8 retest + 1h MTF | 106 | 55 | 0.1219 | -6.6448 | 660.0219 | 6.7667 | 24.34s | Saved |
| OB 61.8 retest + 15m,30m,1h MTF | 107 | 14 | -0.0118 | -1.7853 | 664.8814 | 1.7735 | 28.06s | Saved |
| FVG default owner profile | 108 | 8 | -0.0472 | -1.1014 | 665.5653 | 1.0542 | 192.26s | Saved |
| FVG + local OB confluence, zone overlap | 109 | 2 | -0.0862 | -0.3401 | 666.3266 | 0.2539 | 145.84s | Saved |
| FVG + historical detector OB confluence | none | n/a | n/a | n/a | n/a | n/a | 900.01s | Timed out at 15 minutes |

Commands:

```bash
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 20 --enable-ob-mtf-filter --ob-mtf-timeframes 15m
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 20 --enable-ob-mtf-filter --ob-mtf-timeframes 30m
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 20 --enable-ob-mtf-filter --ob-mtf-timeframes 1h
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 20 --enable-ob-mtf-filter --ob-mtf-timeframes 15m,30m,1h
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --fvg-require-order-block-confluence
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --fvg-require-order-block-confluence --fvg-order-block-confluence-source historical_detector
```

Summary:

- Task 274 acceptance criteria are satisfied: at least four runs were attempted, OB MTF and FVG saved runs were produced, run IDs and metrics are recorded, and no code changes were made for this task.
- The best Task 274 result by net PnL was run 109 among saved FVG variants and run 107 among saved OB variants.
- The historical detector confluence branch is runtime-blocked for this date range/profile and should not be expanded without narrowing the dataset or optimizing that path.
