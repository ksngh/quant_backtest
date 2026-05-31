# Goal

Run a small, practical `ORDER_BLOCK` backtest sweep from the current repository state and report which combinations actually produce trades and usable results.

# Source Requirement

Owner asked:

```text
야 그냥 너가 여기서 내 레포보고 몇개 괜찮은거 이쓰면 실행시켜주면 안돼? 어차피 찍히잖아
```

Interpretation:

- Inspect the current repo/backtest CLI behavior.
- Choose several reasonable `ORDER_BLOCK` command variants.
- Execute them locally against available candle data.
- Summarize trade count, skip reasons, gross/net PnL, costs, and which filters are too restrictive.

# Extracted Roles

- Owner role: Wants practical candidate runs instead of more theoretical discussion.
- Supporting roles:
  - Research runner: Select bounded command variants and run them.
  - Backtest analyst: Parse output and compare trade count, skips, PnL, costs, and filter effects.
  - Documentation/status tracker: Record what was run and the next recommended command.
- Forbidden roles:
  - Live trading or real exchange order execution.
  - Exchange order/account endpoint calls.
  - Strategy implementation changes.
  - Database schema changes.
  - Frontend/dashboard work.

# Context

Current relevant behavior:

- Task 270: `ORDER_BLOCK` defaults to realistic `conservative_crypto_1m` costs and supports optional volume/MTF filters.
- Task 271: `ORDER_BLOCK` default confirmation-close entries use previous-candle stop and symmetric 1R target.
- Task 272: planned but not implemented; it would make fee-adjusted RR blocking default for `ORDER_BLOCK`.
- Until Task 272 is implemented, cost-aware RR blocking must be enabled explicitly with `--enable-cost-aware-entry-filter`.

The owner recently tried a strict combination including:

- 61.8% OB retest entry;
- MTF OB filter;
- cost-aware RR filter;
- volume ratio 2.5x;
- short max wait window.

That combination likely produced no trades because multiple restrictive filters were stacked.

# Scope

- Run local `quant-bitcoin-strategy-backtest` commands only.
- Use `--no-persist` by default unless the owner explicitly wants saved runs.
- Choose a small bounded sweep, for example:
  - baseline `ORDER_BLOCK`;
  - default OB + volume 1.5x or 2.0x;
  - default OB + MTF 15m only;
  - default OB + cost-aware relaxed net RR;
  - 61.8% retest with longer wait bars and relaxed filters;
  - combined practical candidate after isolating the blocking filter.
- Capture and summarize:
  - command;
  - trade count;
  - filled entries;
  - skipped entries;
  - dominant skip reasons;
  - gross PnL;
  - net PnL;
  - total cost;
  - whether LONG/SHORT both appear.

# Out of Scope

- Code changes.
- Test changes.
- Strategy parameter implementation.
- Live trading.
- Real Binance order placement.
- New data backfill.
- Dashboard inspection.

# Requirements

- Do not modify strategy code.
- Do not persist exploratory runs unless explicitly requested.
- Use existing CLI commands and local data only.
- Keep the sweep small enough to finish promptly.
- If the local database/server is unavailable, report the blocker and provide exact commands the owner can run.
- If a command produces no trades, identify whether skips are caused by:
  - no OB events;
  - entry not filled;
  - MTF filter;
  - volume filter;
  - cost-aware filter;
  - risk invalidation;
  - insufficient funds/margin.
- Recommend one next command that is not over-filtered.

# Status Tracking

## Before Execution

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before running commands.
- [x] Inspect CLI options enough to avoid invalid command variants.

## After Execution

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Execution Notes

Owner explicitly changed the task from `--no-persist` exploratory output to saved runs, so the following runs were executed with persistence enabled.

Common base command:

```bash
quant-bitcoin-strategy-backtest \
  --pattern ORDER_BLOCK \
  --start-time 2026-05-25T00:00:00Z \
  --starting-cash 1000000 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10
```

Saved results:

| Run | Variant | Backtest Run ID | Trade Count | Gross PnL | Net PnL | Final Equity |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | base command | 98 | 197 | 0.1814143415 | -24.3288656294 | 642.3569934298 |
| volume_1_5 | `--enable-ob-entry-volume-filter --ob-entry-volume-window 20 --ob-min-entry-volume-ratio 1.5` | 99 | 197 | 0.1682599546 | -24.3459877281 | 642.3398708195 |
| mtf_15m | `--enable-ob-mtf-filter --ob-mtf-timeframes 15m` | 100 | 143 | 0.4365289898 | -17.5544006547 | 649.1316608185 |
| cost_rr_0_6 | `--enable-cost-aware-entry-filter --min-net-reward-bps 0 --min-net-rr 0.6` | 101 | 0 | 0 | 0 | 666.6666666667 |
| retest_618_wait20 | `--pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 20` | 102 | 126 | 0.0676628512 | -15.2115404210 | 651.4551262457 |

Observations:

- `volume_1_5` did not reduce trade count relative to baseline, so 1.5x volume was not a useful filter on this window.
- `mtf_15m` reduced trade count from 197 to 143 and improved net PnL relative to baseline, but remained net negative under the default cost profile.
- `cost_rr_0_6` produced zero fills; even relaxed net RR cost-aware gating is too restrictive for the current 1R `ORDER_BLOCK` structure.
- `retest_618_wait20` reduced trade count and improved net PnL relative to baseline, but remained net negative.
- All saved runs emitted research/backtest warnings only; no live trading or exchange order endpoints were used.

Recommended next saved command to inspect:

```bash
quant-bitcoin-strategy-backtest \
  --pattern ORDER_BLOCK \
  --start-time 2026-05-25T00:00:00Z \
  --starting-cash 1000000 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --pattern-entry-mode limit_at_order_block_618_retracement \
  --fvg-entry-max-wait-bars 20 \
  --enable-ob-mtf-filter \
  --ob-mtf-timeframes 15m
```

# Acceptance Criteria

- At least three bounded `ORDER_BLOCK` command variants are attempted, unless blocked by local environment.
- Results are summarized in a concise comparison.
- The likely reason for zero trades in the strict command is identified from output metadata or skip reasons.
- One recommended next command is provided.
- No code changes are made.
- No live trading behavior or exchange order endpoints are used.

# Required Tests

## Unit Tests

- Not applicable; this is a command-run research task.

## Integration Tests

- Run selected `quant-bitcoin-strategy-backtest` commands with `--no-persist`.

## Contract Tests

- Confirm outputs remain parseable JSON or report the command/output failure.

## Safety Tests

- Confirm commands do not call live order/account endpoints.
- Confirm commands use offline backtest flow only.

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
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --no-persist
```

Additional command variants should be recorded in the task completion notes.

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
