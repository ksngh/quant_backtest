# Task 308: LOOKBACK_RETURN_MOMENTUM Lower Entry-Threshold Backtest and Daily Report

## Predeclared Grid

This grid was fixed before any Task 308 backtest run.

Shared validation configuration:

- Strategy: `LOOKBACK_RETURN_MOMENTUM` v1.
- Strategy document: `docs/strategy/lookback_return_momentum_v1.md`.
- Validation window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.
- Runner end-time convention: the candle loader treats `--end-time` as inclusive, so each interval uses the last closed candle before `2026-05-01T00:00:00Z`.
- Cost profile: `conservative_crypto_1m`.
- Cost-aware entry gate: `cost_aware_entry_filter_v1` enabled.
- Gate thresholds: `min_net_reward_bps=0.0`, `min_net_rr=1.0`, `liquidity_role=TAKER`.
- Non-threshold strategy settings are fixed from Task 305:
  - `risk_distance_pct=0.002`.
  - `stop_loss_r=1.0`.
  - `take_profit_r=1.5`.
  - flat-only/no-reverse entry policy.
  - same-candle stop-first exit handling.
- Sizing/accounting:
  - `--starting-cash 1000000 --starting-cash-currency KRW --krw-per-usdt 1500`.
  - effective quote starting cash: `666.6666666666666 USDT`.
  - `--position-sizing-mode cash_fraction --position-sizing-value 0.10`.

Predeclared threshold candidates:

| Interval | lookback_bars | holding_bars | Comparator threshold | Lower threshold candidates |
|---|---:|---:|---:|---|
| `1m` | 20 | 5 | `0.0010` | `0.0008`, `0.0006`, `0.0004` |
| `5m` | 12 | 6 | `0.0015` | `0.0012`, `0.0009`, `0.0006` |
| `15m` | 8 | 4 | `0.0020` | `0.0016`, `0.0012`, `0.0008` |

Expected diagnostic before running: lowering `entry_threshold` can increase raw momentum candidates, but it does not change the fixed target/risk geometry. With `risk_distance_pct=0.002` and `take_profit_r=1.5`, planned gross reward is `30 bps` and planned gross risk is `20 bps`. Under `conservative_crypto_1m`, the minimum round-trip transaction-cost estimate is already `36 bps` before volatility adjustment. Therefore Task 308 must verify whether lower thresholds only increase blocked candidates or whether a configuration/implementation issue changes that behavior.

## Results

Data preflight passed with the same window semantics used by Task 305.

| Interval | Expected candles | Found candles | First candle | Last included candle |
|---|---:|---:|---|---|
| `1m` | 128,160 | 128,160 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:59:00+00:00` |
| `5m` | 25,632 | 25,632 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:55:00+00:00` |
| `15m` | 8,544 | 8,544 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:45:00+00:00` |

Saved run outputs are stored in `reports/task_308_lower_entry_threshold_raw_outputs/`.

| Interval | Label | Run id | entry_threshold | Raw candidates | Accepted | Blocked | Blocked long | Blocked short | Trades | Return |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | comparator | 1168 | 0.0010 | 79,981 | 0 | 79,981 | 39,961 | 40,020 | 0 | 0.0000% |
| `1m` | lower 20% | 1169 | 0.0008 | 88,660 | 0 | 88,660 | 44,384 | 44,276 | 0 | 0.0000% |
| `1m` | lower 40% | 1170 | 0.0006 | 97,860 | 0 | 97,860 | 49,022 | 48,838 | 0 | 0.0000% |
| `1m` | lower 60% | 1171 | 0.0004 | 107,492 | 0 | 107,492 | 54,001 | 53,491 | 0 | 0.0000% |
| `5m` | comparator | 1172 | 0.0015 | 17,171 | 0 | 17,171 | 8,554 | 8,617 | 0 | 0.0000% |
| `5m` | lower 20% | 1173 | 0.0012 | 18,723 | 0 | 18,723 | 9,345 | 9,378 | 0 | 0.0000% |
| `5m` | lower 40% | 1174 | 0.0009 | 20,372 | 0 | 20,372 | 10,180 | 10,192 | 0 | 0.0000% |
| `5m` | lower 60% | 1175 | 0.0006 | 22,097 | 0 | 22,097 | 11,051 | 11,046 | 0 | 0.0000% |
| `15m` | comparator | 1176 | 0.0020 | 5,937 | 0 | 5,937 | 2,941 | 2,996 | 0 | 0.0000% |
| `15m` | lower 20% | 1177 | 0.0016 | 6,411 | 0 | 6,411 | 3,188 | 3,223 | 0 | 0.0000% |
| `15m` | lower 40% | 1178 | 0.0012 | 6,899 | 0 | 6,899 | 3,446 | 3,453 | 0 | 0.0000% |
| `15m` | lower 60% | 1179 | 0.0008 | 7,449 | 0 | 7,449 | 3,706 | 3,743 | 0 | 0.0000% |

Candidate-count change from current comparator to the lowest threshold:

| Interval | Comparator candidates | Lowest-threshold candidates | Increase | Accepted entries |
|---|---:|---:|---:|---:|
| `1m` | 79,981 | 107,492 | +34.40% | 0 |
| `5m` | 17,171 | 22,097 | +28.69% | 0 |
| `15m` | 5,937 | 7,449 | +25.47% | 0 |

Common block reason for every candidate: `COST_INFEASIBLE_NET_RR`.

Realized PnL and realized costs were zero because no candidate passed the pre-entry gate and no fills occurred.

## Interpretation

- Lowering `entry_threshold` did what it should do at the signal layer: it increased raw momentum candidates across all tested intervals.
- It did not solve the no-entry behavior because `entry_threshold` does not change the fixed target/risk geometry.
- With `risk_distance_pct=0.002` and `take_profit_r=1.5`, planned gross reward is `30 bps` and planned gross risk is `20 bps`.
- Under `conservative_crypto_1m`, minimum round-trip cost is already `36 bps` before volatility adjustment.
- Therefore the best possible pre-entry net reward is at most `-6 bps`, and `net_rr` is below the required `1.0`.
- The current no-fill behavior is consistent with the declared cost-aware gate. It is not explained by a lack of raw signals.
- A threshold-only revision is insufficient. A separate task must predeclare and test changes to reward/risk geometry, `risk_distance_pct`, `take_profit_r`, timeframe-specific cost assumptions, or a deliberately separated gross-vs-net diagnostic.

## Daily Report Artifact

Generated colocated HTML daily-report artifact:

```text
reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-lower-threshold/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

Notes:

- Final report artifact is `report-ko.html`.
- No `images/` subdirectory was created.
- Payload image references are filename-only.
- HTML image references use `./[filename].png`.
- Report-facing folder/file names do not include task numbers, run ids, or internal candidate ids.
- Because accepted entries were zero, the representative win/loss images are fallback diagnostic images showing that every raw candidate was blocked before entry.

## Verification

- `python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-lower-threshold/payload.json >/dev/null` -> passed.
- Artifact contract check -> passed:
  - `payload.json` exists.
  - `report-ko.html` exists.
  - four required PNGs exist and are colocated.
  - no `images/` folder exists.
  - no `report-en.html`, `report-en.md`, `image_plan.md`, or `image_plan.json` exists.
  - payload image references are filename-only.
  - HTML image references are `./[filename].png`.
  - `report-ko.html` does not contain task numbers, run ids, or internal candidate ids.
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `19 passed`.
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q` -> `20 passed`.
- `git diff --check -- reports/TASK_308_LOOKBACK_RETURN_MOMENTUM_LOWER_ENTRY_THRESHOLD_BACKTEST_DAILY_REPORT.md reports/task_308_lower_entry_threshold_raw_outputs reports/blog_payloads/lookback-return-momentum/v1/20260201-20260501-lower-threshold STATUS.md BACKLOG.md PROJECT_HISTORY.md` -> passed.
- Broader command `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py -q` -> `30 passed, 2 failed`.
  - The failures were existing `FAIR_VALUE_GAP` CLI expectation mismatches in `test_strategy_cli_outputs_position_signal_and_execution_side` and `test_strategy_cli_accepts_equity_risk_fraction_sizing`.
  - Task 308 did not modify the `FAIR_VALUE_GAP` path or CLI sizing behavior.

## Codex Self-Review

- Scope respected: executed only Task 308's lower `entry_threshold` grid and report artifact generation.
- Requirement matched: grid was predeclared before execution; cost-aware gate stayed enabled; `1m`/`5m`/`15m` ran over the assigned window; results were interpreted; `report-ko.html` was generated.
- Role ownership respected: no live trading, backend, frontend, scheduler, DB schema, or dashboard work was added.
- Architecture boundary respected: strategy code was not changed in this task; runs used existing offline backtest CLI and local saved candle data.
- Safety respected: no secrets, `.env`, real order behavior, private exchange endpoints, or live-trading behavior were introduced.
- Tests and verification run: focused strategy/runner/persistence tests passed; artifact contract checks passed; broad persistence command has two known unrelated `FAIR_VALUE_GAP` failures recorded above.

## Recommended Next Task

Create a separate `LOOKBACK_RETURN_MOMENTUM` reward/risk geometry diagnostic task if the owner wants to continue. That task should predeclare changes to `risk_distance_pct`, `take_profit_r`, timeframe-specific cost assumptions, or a separate gross-vs-net diagnostic before running any new backtests.
