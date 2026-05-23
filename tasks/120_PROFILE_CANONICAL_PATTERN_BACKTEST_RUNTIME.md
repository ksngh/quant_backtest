# Profile Canonical Pattern Backtest Runtime

# Goal

Identify the exact runtime bottleneck causing pattern backtests over a small candle set, such as 400 candles, to take multiple hours.

This task is the highest-priority diagnostic task. Do not start broad refactoring until this profiling task identifies where time is actually being spent.

The expected output is a concrete runtime profile broken down by:

- candle loading;
- indicator calculation;
- pattern action building;
- pattern detector runtime by pattern;
- strategy-engine runtime;
- persistence runtime;
- JSON serialization / CLI output runtime.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `PROJECT_HISTORY.md`
- `BACKLOG.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- `quant_bitcoin/indicators/atr.py`
- `quant_bitcoin/indicators/volume_ratio.py`
- `quant_bitcoin/indicators/displacement_candle.py`
- `quant_bitcoin/indicators/pivots.py`
- `quant_bitcoin/persistence/postgres.py`
- existing tests under `tests/backtesting/`, `tests/patterns/`, and `tests/indicators/`

# Extracted Roles

- Owner role:
  - Backtesting performance owner.
  - Responsible for profiling the canonical pattern backtest path and identifying measured bottlenecks.

- Supporting roles:
  - Pattern detection role:
    - Helps identify detector-specific algorithmic hot spots.
  - Indicator role:
    - Helps identify repeated ATR, volume-ratio, displacement, and pivot calculations.
  - Persistence role:
    - Helps isolate DB load/save runtime from in-memory strategy runtime.
  - CLI role:
    - Helps expose or run profiling commands against the canonical entrypoint.

- Forbidden roles:
  - No algorithm rewrite in this task unless required for minimal instrumentation.
  - No live trading.
  - No real order execution.
  - No private exchange endpoints.
  - No API keys or secrets.
  - No frontend changes.
  - No database schema changes.

# Context

Current observed behavior: validating around 400 candles by pattern takes more than 2 hours.

This is abnormal. A 400-candle single-pattern backtest should normally complete in seconds or at worst tens of seconds, depending on pattern complexity and environment.

Likely bottlenecks:

- repeated `candles.iloc[:i]` prefix evaluation;
- repeated indicator recalculation per candle;
- repeated DataFrame `copy(deep=True)` in hot loops;
- pivot-combination explosion in Trendline Break, Cup and Handle, Diamond, or Adam and Eve;
- event duplication followed by late filtering;
- persistence accidentally happening inside loops;
- expensive JSON serialization or output construction;
- tests accidentally running integration/database paths.

The canonical path currently routes pattern backtesting through `strategy_postgres_runner_cli.py`, which loads candles, builds actions, calls `run_strategy_backtest_engine`, optionally persists results, and prints JSON.

# Scope

- Add lightweight timing instrumentation or a profiling harness.
- Measure single-pattern runtime for:
  - `FAIR_VALUE_GAP`
  - `ORDER_BLOCK`
  - `TRENDLINE_BREAK`
  - `CUP_AND_HANDLE`
  - `DIAMOND`
  - `ADAM_AND_EVE`
- Measure with persistence disabled.
- Measure with persistence enabled where locally possible.
- Measure candle loading separately from in-memory evaluation.
- Produce profiling summary suitable for follow-up optimization tasks.
- Keep instrumentation deterministic and disabled by default unless explicitly invoked.

# Out of Scope

- Rewriting pattern algorithms.
- Adding shared indicator cache.
- Adding at-index detectors.
- Persisting runtime metrics.
- Frontend display.
- API changes.
- Database schema changes.
- Live or paper trading changes.

# Requirements

- Add a profiling command, test helper, or optional CLI instrumentation path.
- Profiling must be possible without saving a completed run.
- Profiling must separate at least these phases:
  - `load_candles_ms`
  - `build_actions_ms`
  - `run_engine_ms`
  - `persist_ms`
  - `json_output_ms`
  - `total_elapsed_ms`
- For action building, break down pattern-specific runtime where possible:
  - `pattern_key`
  - `candle_count`
  - `events_detected`
  - `actions_emitted`
  - `elapsed_ms`
- Run cProfile or equivalent and record top cumulative-time functions.
- Confirm whether DB persistence is a material bottleneck by comparing `--no-persist` and persist-enabled execution.
- Confirm whether repeated indicator calculation is occurring inside candle loops.
- Confirm whether pivot-heavy detector candidate counts are exploding.
- Do not make ordinary tests slow.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Profiling output identifies the top runtime consumers by function.
- Profiling output reports phase timings for the canonical pattern backtest path.
- Profiling output reports pattern-specific runtime for each supported pattern.
- The profiling path can run with `--no-persist`.
- The profiling path can run without exchange API keys.
- The completion summary includes:
  - slowest pattern;
  - slowest function;
  - whether DB persistence is a bottleneck;
  - whether repeated indicator recalculation is observed;
  - whether pivot-combination explosion is observed;
  - recommended next optimization task.

# Required Tests

## Unit Tests

- Add tests for any timing helper to ensure:
  - timer starts and stops deterministically enough for structure validation;
  - generated timing payload contains expected keys;
  - zero/empty phases do not crash serialization.

## Integration Tests

- Add a small fixture-based integration test that runs profiling with `--no-persist`.
- Assert the profiling payload contains:
  - `total_elapsed_ms`;
  - `load_candles_ms`;
  - `build_actions_ms`;
  - `run_engine_ms`;
  - pattern timing details.

## Contract Tests

- Confirm profiling does not change strategy outputs.
- Confirm profiling does not mutate candle data.
- Confirm profiling metadata is JSON-serializable.

## Safety Tests

- Confirm profiling does not call:
  - exchange order endpoints;
  - account endpoints;
  - signed requests;
  - API key loading.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Profiling does not slow normal runs unless explicitly enabled.
- Profiling result clearly identifies the next optimization target.

# Verification

Default:

```bash
pytest
```

Recommended profiling commands:

```bash
python -m cProfile -o backtest.prof -m quant_bitcoin.backtesting.strategy_postgres_runner_cli \
  --pattern FAIR_VALUE_GAP \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T06:40:00Z \
  --no-persist

python - <<'PY'
import pstats
stats = pstats.Stats("backtest.prof")
stats.strip_dirs().sort_stats("cumtime").print_stats(50)
PY
```

Pattern-by-pattern timing smoke commands:

```bash
quant-bitcoin-pattern-backtest --pattern FAIR_VALUE_GAP --no-persist
quant-bitcoin-pattern-backtest --pattern ORDER_BLOCK --no-persist
quant-bitcoin-pattern-backtest --pattern TRENDLINE_BREAK --no-persist
quant-bitcoin-pattern-backtest --pattern CUP_AND_HANDLE --no-persist
quant-bitcoin-pattern-backtest --pattern DIAMOND --no-persist
quant-bitcoin-pattern-backtest --pattern ADAM_AND_EVE --no-persist
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
- profiling commands run
- top bottleneck functions
- slowest pattern
- persistence timing result
- Codex self-review result
- known limitations
- recommended next task
