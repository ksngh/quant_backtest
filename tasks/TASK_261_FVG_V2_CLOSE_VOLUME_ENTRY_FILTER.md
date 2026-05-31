# Task 261: FVG V2 Close Volume Entry Filter

# Goal

Add a close-candle volume filter to the current default FVG v2 channel workflow so a long/buy entry signal is skipped when the completed signal candle's volume is too low.

# Source Requirement

Owner requested after Task 260:

```text
여기다가 이제 볼륨도 추가해줘. 매수신호가 딱 나왔는데 종가시점 거래량이 너무 낮으면 매수 안하도록.
```

Clean requirement:

- Add a volume gate to the FVG v2 channel/default strategy-backtest entry path.
- When a buy/long signal appears, evaluate the completed signal/retest candle's volume at close.
- If that candle's volume is below the configured low-volume threshold, do not enter the trade.
- Record the skip reason and volume diagnostics in metadata.

# Extracted Roles

- Owner role:
  - Defines the desired behavior: do not buy when the signal candle closes with too little volume.
- Supporting roles:
  - CLI role: exposes volume filter controls and defaults.
  - Strategy/backtest role: applies the filter before executable entry actions are handed to the engine.
  - Indicator role: reuses existing candle-based volume ratio logic where possible.
  - Metadata role: records volume threshold, current volume, baseline volume, ratio, and skip reason.
  - Test role: verifies low-volume entries are skipped and adequate-volume entries are preserved.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, account endpoints, or exchange order endpoints.
  - Do not use intrabar/order-book volume or real-time exchange APIs.
  - Do not change channel geometry, retest direction rules, close-based retest rules, target/stop math, or Task 260 owner defaults except to add this volume gate.
  - Do not implement 15m/1h multi-timeframe alignment in this task.

# Context

Task 260 made the owner FVG v2 channel profile the default for `FAIR_VALUE_GAP` strategy backtests. The minimal command is now:

```bash
quant-bitcoin-strategy-backtest \
  --start-time 2026-05-28T00:00:00Z
```

The current FVG v2 channel retest confirmation from Task 259 is close-based:

- upper-boundary retest requires close-based confirmation and maps to LONG
- lower-boundary retest requires close-based confirmation and maps to SHORT

This task adds a completed-candle volume gate after a signal is formed and before entry is allowed. The owner specifically mentioned "매수신호" / buy signal, so the first implementation should gate LONG entries. SHORT volume gating can be added only if explicitly requested or if the task is amended.

The project already has candle volume and volume-ratio indicator work, including prior-only / quote-notional-aware variants from earlier tasks. Prefer reusing that existing code rather than inventing a separate ad hoc rolling calculation.

# Scope

- Add a default-on volume entry filter for the Task 260 FVG owner profile.
- Apply the filter to FVG v2 channel LONG/buy entry candidates before execution.
- Use only completed candle data available at the entry decision time.
- Prefer a no-lookahead baseline: compare the signal candle volume against prior completed candles, not against future candles.
- Add CLI controls for:
  - enabling/disabling the volume entry filter
  - lookback window
  - minimum volume ratio
  - input mode if supported by existing volume-ratio code
- Add metadata for accepted and skipped entries.
- Add tests for low-volume skip and adequate-volume pass.
- Update README/API contract if new metadata fields are emitted.

# Out of Scope

- No live trading.
- No exchange account/order endpoints.
- No credentials or `.env` changes.
- No intrabar volume, order-book volume, or real-time volume feed.
- No 15m/1h multi-timeframe entry alignment.
- No frontend UI changes unless metadata contract requires a type/doc update.
- No database schema migration unless existing persistence cannot store the metadata as JSON.
- No change to FVG channel line drawing or construction point labels.

# Requirements

- Default behavior for the owner FVG v2 channel profile:
  - volume filter enabled
  - suggested initial threshold: `minimum_volume_ratio = 1.0`
  - suggested initial lookback: `20`
  - suggested baseline: prior completed candles only
- If the entry signal is LONG and the completed signal candle volume ratio is below threshold:
  - emit a non-executable `SKIP` action
  - skip reason should be deterministic, for example `LOW_CLOSE_VOLUME_ENTRY_FILTER`
  - no entry execution should be created for that candidate
- If volume data is missing/invalid:
  - fail closed for the owner default profile by skipping the LONG entry with explicit metadata, unless implementation discovers an existing project convention that requires a different behavior.
- Metadata should include:
  - schema version, for example `close_volume_entry_filter_v1`
  - enabled flag
  - applies_to_side, initially `LONG`
  - signal candle timestamp/index
  - current/signal candle volume
  - baseline volume
  - volume ratio
  - minimum volume ratio
  - lookback/window
  - baseline mode/input mode
  - pass/fail result
  - skip reason when blocked
- Explicit CLI overrides must win.
- The filter must remain offline backtesting/research only.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/indicators/volume_ratio.py`.
- [x] Read relevant FVG channel tests.
- [x] Confirm whether default threshold `1.0` and lookback `20` are acceptable, or record them as implementation assumptions.
- [x] Record assumptions, blockers, or unclear status items before coding.

Implementation assumptions:

- The owner-approved initial default is `minimum_volume_ratio=1.0`, `window=20`.
- The baseline is `PRIOR_ONLY` and requires a full prior window; invalid/missing volume fails closed for LONG entries when the filter is enabled.
- The first implementation applies only to FVG v2 channel LONG entries, matching the owner wording "매수신호".

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] Minimal owner command applies the volume entry filter by default.
- [x] A LONG/buy FVG v2 channel entry candidate on a low-volume completed signal candle is skipped.
- [x] An otherwise identical adequate-volume candidate is allowed.
- [x] Skip metadata records current volume, baseline volume, volume ratio, threshold, and reason.
- [x] Explicit CLI disable/threshold overrides work.
- [x] Existing Task 259 close-based retest behavior remains unchanged except for the added volume gate.
- [x] Existing Task 260 owner defaults remain active.
- [x] No live trading behavior or exchange order/account endpoint behavior is introduced.

# Required Tests

## Unit Tests

- [x] Volume filter config builder/default test.
- [x] Low-volume LONG entry candidate emits `LOW_CLOSE_VOLUME_ENTRY_FILTER`.
- [x] Adequate-volume LONG entry candidate passes.
- [x] Missing/invalid volume handling is deterministic.
- [x] Explicit disable flag bypasses the volume gate.

## Integration Tests

- [x] CLI minimal command metadata includes enabled close-volume entry filter defaults.
- [x] FVG v2 channel action builder/run path applies the filter before engine execution.
- [x] Existing FVG channel tests still pass.

## Contract Tests

- [x] Update README/API contract if metadata names are added.
- [x] No database schema change expected if metadata stays in existing JSON fields.

## Safety Tests

- [x] Confirm no live trading controls, signed requests, exchange order endpoints, account endpoints, credentials, or real exchange order behavior are introduced.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_fvg_channel.py tests/indicators/test_volume_ratio.py -q
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
