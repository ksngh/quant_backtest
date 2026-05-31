# Task 276: Liquidity Sweep Displacement FVG/OB Backtest

# Goal

Implement and initially backtest a deterministic BTCUSDT pattern strategy named `LIQUIDITY_SWEEP_REVERSAL`, built for current crypto microstructure behavior:

- identify stop-run/liquidity-sweep candles around prior swing liquidity;
- require completed-candle reclaim and displacement confirmation;
- require same-direction Fair Value Gap and/or Order Block confluence;
- enter only on retest/mitigation instead of chasing the first confirmation close;
- place stop beyond the sweep extreme;
- target nearest opposite liquidity or a fixed R multiple;
- block trades whose fee/spread/slippage-adjusted reward/risk is not viable;
- persist backtest runs with cost, slippage, skip, and attribution metadata.

This is a research/backtest task only. It must not authorize live trading.

# Source Requirement

Owner requested:

```text
여기 레포지토리는 비트코인 퀀트 백테스트 하는 레포지토리인데, 여기서 너가 요새 제일 잘 먹힐 거 같은 모델을 들고와서 백테스트 해봐.
지금 아키텍처는 패턴이랑 등등으로 나눠서, 지표 수집 후 그 걸 기반으로 패턴 감지,
그러고 손절 및 익절 전략을 들고와서 적용시킨 후 수수료와 슬리피지를 계산 한 뒤에
그걸로 손익비를 계산하고 백테스트를 하고 있어.
너는 퀀트 리서치 전문가야. 게다가 크립토에서 10년간 근무하고 있지.
완전 베테랑이니까 너가 어떤 복잡한 패턴이든 구현하고 그걸 토대로 백테스트 할 수 있도록 task를 만들어줘.
task를 만들때도 아주 자세히 만들어야겠지
```

Clean requirement:

- Create a detailed future implementation task for one high-conviction crypto backtest model.
- The task must fit the current architecture: indicators -> pattern detection -> risk/exit plan -> transaction costs/slippage -> reward/risk -> strategy backtest.
- The task must be detailed enough for a future agent to implement and run without broad reinterpretation.
- Do not implement or run the backtest in this task-creation step.

# Extracted Roles

- Owner role:
  - Wants a veteran-style, practical BTC quant research candidate rather than another blind FVG/OB parameter sweep.
  - Wants the model to be implementable inside the existing pattern/backtest architecture.
- Supporting roles:
  - Quant researcher: fixes the hypothesis, expected edge source, regime assumptions, baselines, and rejection rules before implementation.
  - Indicator role: computes no-lookahead pivots, ATR, displacement, volume ratio, market regime, liquidity/spread/session proxy context, and optional multi-timeframe trend context from completed candles only.
  - Pattern detector role: emits stable `LIQUIDITY_SWEEP_REVERSAL` events with deterministic metadata.
  - Risk/exit role: creates stops, targets, invalidation rules, and cost-aware reward/risk checks.
  - Strategy/backtest role: converts events into fill-aware actions, simulates entries/exits, applies costs/slippage, and persists results.
  - Test role: covers no-lookahead behavior, edge cases, cost gates, CLI wiring, and safety boundaries.
  - Status tracker: updates `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.
- Forbidden roles:
  - Live trading or real Binance order execution.
  - Exchange order/account/private endpoint calls.
  - API keys, signed requests, `.env` changes, or live credentials.
  - Futures, leverage, liquidation, borrow/funding, or real margin behavior.
  - Machine learning training.
  - Dashboard/frontend work unless a separate frontend task is assigned.
  - Native DB-backed higher-timeframe backfill; Task 265 remains separate.
  - Unbounded parameter search or post-hoc tuning after seeing results.

# Context

Recent project evidence:

- Task 273 showed raw `ORDER_BLOCK` variants still lost money after realistic costs; 61.8% retest wait-20 reduced loss but remained negative.
- Task 274 showed the best saved OB MTF branch was run 107: `ORDER_BLOCK` 61.8% wait-20 + 15m,30m,1h MTF, 14 trades, -1.79 net PnL.
- Task 274 showed the best saved FVG branch was run 109: FVG + local OB confluence, 2 trades, -0.34 net PnL.
- Task 275 confirmed local FVG OB confluence reduced trade count and net loss versus FVG default, but did not establish profitability.
- Task 185 already added OHLCV-derived liquidity, spread-proxy, session, weekday, and attribution metadata.
- The current strategy stack already supports ATR, pivots, displacement candles, support/resistance, swing structure, volume ratio, FVG, Order Block, market regime, multi-timeframe trend score, FVG channel logic, entry fill simulation, cost profiles, and strategy persistence.

Research thesis:

- A plain FVG or plain OB signal is too noisy on short BTC candles after costs.
- A better candidate should first require a liquidity event that plausibly clears crowded stops, then require directional reclaim/displacement, then require FVG/OB retest execution so entry price is not chasing.
- The edge hypothesis is not "FVG works" or "OB works"; it is:
  - stop liquidity is swept;
  - price reclaims the swept level;
  - displacement confirms aggressive flow in the reversal direction;
  - an inefficiency or mitigation zone gives a retest entry;
  - costs are small enough relative to planned reward.

External research context:

- Recent high-frequency crypto microstructure research continues to emphasize that intraday liquidity and volatility patterns matter for BTC/ETH execution quality.
- Prior BTC liquidity research also supports treating liquidity shocks and volatility regimes as risk-management inputs.
- These external references support using liquidity/spread/session/regime gates, but they do not prove profitability for this strategy. Profitability must be judged only by repository backtests and out-of-sample validation.

# Scope

Implement a new offline-only pattern strategy family:

- Pattern key: `LIQUIDITY_SWEEP_REVERSAL`
- Pattern type: `LIQUIDITY_SWEEP_REVERSAL`
- Strategy name: `LIQUIDITY_SWEEP_REVERSAL_PATTERN_STRATEGY`
- First supported symbol/timeframe target: BTCUSDT stored candle data, default base interval `1m`.
- First supported execution mode: historical backtest/paper simulation only.

Allowed implementation areas:

- `quant_bitcoin/indicators/` only if a small reusable helper is required and cannot be composed from existing indicators.
- `quant_bitcoin/patterns/liquidity_sweep_reversal.py`
- `quant_bitcoin/patterns/liquidity_sweep_reversal_risk_exit.py`
- `quant_bitcoin/patterns/__init__.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/strategies/pattern_execution_policy.py`
- `quant_bitcoin/strategies/pattern_explanations.py`
- `quant_bitcoin/backtesting/fvg_detection_cache.py` or equivalent pattern cache module if needed for efficient `evaluate_at`.
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- focused tests under `tests/indicators/`, `tests/patterns/`, `tests/strategies/`, `tests/backtesting/`, and `tests/safety/`.
- docs/API metadata only if output schema or CLI contract changes.

Initial saved-run scope after implementation:

- Run a small, predeclared net-cost backtest on the same recent owner comparison window:

```bash
--start-time 2026-05-25T00:00:00Z
--starting-cash 1000000
--position-sizing-mode cash_fraction
--position-sizing-value 0.10
```

- Compare against the recent saved-run baselines:
  - Task 274 run 107: best executed OB MTF branch.
  - Task 274 run 108: FVG default owner profile.
  - Task 274 run 109: FVG + local OB confluence.
  - Task 275 run 113 if it remains the comparable local FVG OB confluence follow-up.

# Out of Scope

- No live trading.
- No real Binance order placement.
- No exchange account/private/order endpoints.
- No API keys, signed requests, `.env` files, or credential handling.
- No futures, leverage, liquidation, funding, borrow-fee, or real margin modeling.
- No machine learning model training.
- No database schema migration unless persistence cannot store additive metadata; if schema change appears necessary, stop and create a separate task.
- No frontend/dashboard work.
- No native 1h/4h backfill implementation; use completed resampled base candles unless Task 265 is completed before this task is implemented.
- No order-book data or live websocket dependency.
- No portfolio optimization.
- No claim that the model is profitable until net and validation results support it.

# Requirements

## Mechanical Pattern Definition

The detector must emit a `LIQUIDITY_SWEEP_REVERSAL` event only from completed candles and must be deterministic.

Bullish setup:

- Identify a prior sell-side liquidity pool:
  - confirmed pivot low;
  - support zone lower boundary;
  - previous local swing low;
  - or a configurable lowest-low window.
- The liquidity pool must be old enough:
  - default `min_liquidity_pool_age_bars=5`;
  - default `liquidity_pool_lookback_bars=80`.
- A sweep candle must trade below the liquidity level by at least one configured threshold:
  - default `min_sweep_atr_multiplier=0.05`;
  - or default `min_sweep_bps=2.0`;
  - use the larger effective threshold when both are enabled.
- A reclaim must occur without lookahead:
  - same candle or next `reclaim_max_bars=2` completed candles close back above the swept liquidity level;
  - record whether reclaim was same-candle or delayed.
- A bullish displacement confirmation must occur on the reclaim candle or within `displacement_max_bars_after_sweep=3`:
  - close is above open;
  - body ratio >= default `0.55`;
  - true range >= default `0.8 * ATR`;
  - close is in the upper part of candle range;
  - default minimum completed-candle volume ratio >= `1.5`.
- Require at least one same-direction confluence:
  - bullish FVG created by or immediately after displacement;
  - or bullish local Order Block / mitigation zone created before displacement;
  - default first version should require FVG OR OB, not necessarily both.
- Optional stricter mode may require both FVG and OB, but must be default-off.

Bearish setup mirrors bullish setup:

- Identify prior buy-side liquidity pool around pivot high/resistance/swing high/highest-high window.
- Sweep above the pool, reclaim by closing below it, confirm bearish displacement, and require bearish FVG/OB confluence.

Event emission timing:

- Emit the event only at the completed confirmation candle close.
- The event `timestamp` must be the confirmation timestamp, not the swept liquidity timestamp.
- The event must not inspect any candle after the confirmation index.
- A later retest/fill must be simulated by the action builder, not by the detector.

## Event Fields And Metadata

The event dataclass must include at minimum:

- `event_id`
- `pattern_type`
- `direction`
- `pattern_status`
- `symbol`
- `timeframe`
- `timestamp`
- `start_index`
- `end_index`
- `liquidity_pool_index`
- `liquidity_pool_timestamp`
- `liquidity_pool_price`
- `liquidity_pool_source`
- `sweep_candle_index`
- `sweep_candle_timestamp`
- `sweep_extreme_price`
- `sweep_distance`
- `sweep_distance_atr`
- `sweep_distance_bps`
- `reclaim_candle_index`
- `reclaim_candle_timestamp`
- `reclaim_close`
- `reclaim_lag_bars`
- `displacement_candle_index`
- `displacement_direction`
- `displacement_range_atr`
- `displacement_body_ratio`
- `volume_ratio`
- `fvg_confluence_pass`
- `fvg_event_id`
- `fvg_zone_low`
- `fvg_zone_high`
- `order_block_confluence_pass`
- `order_block_event_id`
- `order_block_zone_low`
- `order_block_zone_high`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `pattern_score`
- `score_components`
- `score_component_sources`
- `score_limitations`
- `atr_metadata`
- `regime_metadata`
- `mtf_metadata`
- `reason`

Stable event ID:

- Build from symbol, timeframe, direction, liquidity pool timestamp/price, sweep timestamp/extreme, confirmation timestamp, and confluence type.
- Do not include future fill or exit data in `event_id`.

## Pattern Score

The first score is deterministic heuristic metadata, not calibrated alpha probability.

Default score components:

- sweep quality:
  - distance beyond pool is large enough but not extreme;
  - default weight `0.20`.
- reclaim quality:
  - reclaim is fast and closes decisively beyond the pool;
  - default weight `0.20`.
- displacement quality:
  - range ATR, body ratio, close location;
  - default weight `0.20`.
- volume quality:
  - prior-only volume ratio;
  - default weight `0.15`.
- FVG/OB confluence quality:
  - FVG, OB, or both;
  - default weight `0.15`.
- regime/tradability quality:
  - avoids poor-liquidity/wide-spread proxy conditions;
  - default weight `0.10`.

Default `minimum_pattern_score=0.70`.

Score metadata must explicitly say:

- score is heuristic;
- score is not calibrated probability;
- score must not be interpreted as live-trading confidence.

## Regime, Liquidity, Spread, And Session Gates

Use existing completed-candle metadata where available:

- market regime;
- volatility regime;
- liquidity regime;
- spread-proxy regime;
- session tag;
- weekday/weekend tag.

Default behavior:

- Do not block solely on session in the first version.
- Block when liquidity proxy is explicitly poor and `fail_closed_on_poor_liquidity=True`.
- Block when spread proxy is explicitly wide and `fail_closed_on_wide_spread=True`.
- If proxy metadata is missing, record `tradability_context_missing=True`.
- Missing proxy metadata should default to warn, not block, unless `fail_closed_on_missing_tradability_context=True` is explicitly enabled.

Multi-timeframe behavior:

- Use completed resampled base candles for first implementation if native higher-timeframe context is not available.
- Default MTF confirmation:
  - 15m trend is not strongly against the reversal;
  - optional 1h/4h context is metadata-only unless Task 265 is implemented.
- Record context source:
  - `resampled_completed_base_candles`;
  - or `native_postgres_higher_timeframe_candles` if Task 265 has been completed and this task explicitly wires it.
- Never use incomplete higher-timeframe candles.

## Entry Policy

Default entry policy:

- Do not enter at the first confirmation close by default.
- Build a retest entry plan from the confluence zone:
  - preferred level 1: FVG midpoint if FVG confluence exists;
  - preferred level 2: Order Block 0.5 to 0.618 mitigation level if OB confluence exists;
  - if both exist, choose the level with better net reward/risk and record the selected source.
- Default `entry_max_wait_bars=20`.
- Default trigger basis: candle touch of limit price with existing intrabar policy.
- Expire unfilled entries with reason `LIQUIDITY_SWEEP_RETEST_NOT_FILLED`.

Optional diagnostic modes:

- `market_on_reclaim_close`
- `market_on_displacement_close`
- `limit_at_fvg_midpoint`
- `limit_at_ob_618`
- `best_net_rr_between_fvg_midpoint_and_ob_618`

Only retest/limit modes should be considered promotion candidates unless evidence shows otherwise.

## Stop, Target, And Invalidation Policy

Default stop:

- Bullish: below sweep extreme minus `stop_buffer_atr_multiplier=0.10 * ATR`.
- Bearish: above sweep extreme plus `stop_buffer_atr_multiplier=0.10 * ATR`.
- If stop is not on the correct side of entry, skip with `LIQUIDITY_SWEEP_STOP_INVALID`.

Default target:

- Preferred target: nearest opposite liquidity pool detected before or at confirmation time.
- Fallback target: fixed `target_r_multiple=2.0`.
- Minimum target: must satisfy `min_gross_rr=1.2` and `min_net_rr=1.0` after costs.
- Record target source:
  - `OPPOSITE_LIQUIDITY_POOL`;
  - `FIXED_R_MULTIPLE`;
  - `COST_AWARE_REJECTED`.

Soft invalidation before entry:

- Bullish candidate invalidates if a completed candle closes below the sweep extreme before entry.
- Bearish candidate invalidates if a completed candle closes above the sweep extreme before entry.
- Opposite displacement before entry invalidates by default.

Post-entry exit:

- Use existing pattern exit simulation and intrabar sequencing policy.
- Same-candle stop/target ambiguity must use the repository's conservative intrabar policy.
- Record whether stop or target touched first under the chosen policy.

## Cost-Aware Reward/Risk Gate

Before emitting an entry action, calculate expected costs using the selected transaction cost profile.

Default cost settings:

- Use existing realistic crypto default profile unless CLI overrides are explicit.
- Liquidity role:
  - limit retest entries may default to maker only if current cost system explicitly supports maker semantics;
  - otherwise use taker to remain conservative.

Entry must be skipped when:

- expected net reward after fees/spread/slippage is <= 0;
- net RR < `min_net_rr`;
- expected reward bps < `min_net_reward_bps`;
- stop distance is too tight relative to estimated round-trip costs.

Default values:

- `min_net_rr=1.0`
- `min_net_reward_bps=8.0`
- `min_stop_cost_multiple=2.0`

Skip reason:

- `LIQUIDITY_SWEEP_COST_AWARE_RR_REJECTED`

## CLI Requirements

Add support for:

```bash
quant-bitcoin-strategy-backtest --pattern LIQUIDITY_SWEEP_REVERSAL
```

Add focused CLI flags only where needed:

- `--lsr-liquidity-lookback-bars`
- `--lsr-min-liquidity-pool-age-bars`
- `--lsr-min-sweep-atr-multiplier`
- `--lsr-min-sweep-bps`
- `--lsr-reclaim-max-bars`
- `--lsr-displacement-max-bars-after-sweep`
- `--lsr-min-displacement-body-ratio`
- `--lsr-min-displacement-atr-multiplier`
- `--lsr-min-volume-ratio`
- `--lsr-require-fvg-confluence`
- `--lsr-require-order-block-confluence`
- `--lsr-require-both-fvg-and-ob`
- `--lsr-entry-mode`
- `--lsr-entry-max-wait-bars`
- `--lsr-target-r-multiple`
- `--lsr-min-gross-rr`
- `--lsr-min-net-rr`
- `--lsr-min-net-reward-bps`
- `--lsr-enable-tradability-gates`
- `--lsr-enable-mtf-confirmation`
- `--lsr-mtf-timeframes`

Do not add broad, unused flags.

Defaults must be conservative and documented in output metadata.

## Initial Parameter Grid

After the base implementation passes tests, run only this bounded initial grid unless the owner assigns a separate sweep task:

Baseline variant:

- `entry_mode=best_net_rr_between_fvg_midpoint_and_ob_618`
- `min_sweep_atr_multiplier=0.05`
- `min_sweep_bps=2.0`
- `reclaim_max_bars=2`
- `min_volume_ratio=1.5`
- `min_net_rr=1.0`
- `target_r_multiple=2.0`
- tradability gates enabled
- MTF confirmation disabled first, then enabled as a comparison

Small comparison variants:

- V1: baseline.
- V2: baseline + MTF 15m confirmation.
- V3: baseline + MTF 15m,1h confirmation using completed resampled candles.
- V4: stricter volume ratio `2.0`.
- V5: require both FVG and OB confluence.
- V6: FVG-only confluence.
- V7: OB-only confluence.
- V8: zero-cost diagnostic version of the best realistic-cost variant.

Stop early rules:

- If a branch has zero fills, record it and do not expand that branch.
- If a branch is dominated by lower trade count and worse net PnL/drawdown than a less restrictive branch, record it as dominated.
- Do not keep adding variants after weak outcomes without a new task.

## Backtest Report Requirements

Implementation must produce a concise research summary in the task completion notes:

- command used;
- saved run ID;
- trade count;
- gross PnL;
- net PnL;
- final equity;
- total costs;
- win rate;
- profit factor if available;
- max drawdown if available;
- skip counts by reason;
- long/short split;
- session/liquidity/spread attribution if available;
- comparison to Task 274/275 baselines;
- whether costs destroyed the edge;
- whether results justify a separate WFO/OOS task.

No promotion is allowed from a single recent-window backtest.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Read this task file before coding.
- [x] Read `docs/15_RESEARCH_PROTOCOL.md`.
- [x] Read `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`.
- [x] Read `docs/18_INTRABAR_SEQUENCING_POLICY.md`.
- [x] Read `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`.
- [x] Read `docs/23_RISK_EXIT_REUSABLE_POLICY_BOUNDARY.md`.
- [x] Read `quant_bitcoin/indicators/atr.py`.
- [x] Read `quant_bitcoin/indicators/displacement_candle.py`.
- [x] Read `quant_bitcoin/indicators/pivots.py`.
- [x] Read `quant_bitcoin/indicators/support_resistance_zone.py`.
- [x] Read `quant_bitcoin/indicators/swing_structure.py`.
- [x] Read `quant_bitcoin/indicators/volume_ratio.py`.
- [x] Read `quant_bitcoin/indicators/market_regime.py`.
- [x] Read `quant_bitcoin/patterns/fair_value_gap.py`.
- [x] Read `quant_bitcoin/patterns/order_block.py`.
- [x] Read `quant_bitcoin/patterns/entry_simulation.py`.
- [x] Read `quant_bitcoin/patterns/exit_simulation.py`.
- [x] Read `quant_bitcoin/risk/exit_plan.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior will be introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Clearly record the next task.

# Acceptance Criteria

- `LIQUIDITY_SWEEP_REVERSAL` detector exists and emits deterministic bullish and bearish events from completed candles only.
- Detector rejects no-sweep, no-reclaim, weak-displacement, missing-confluence, and low-volume cases with explicit reasons or no-event behavior.
- Event metadata includes liquidity pool, sweep, reclaim, displacement, FVG/OB confluence, score, ATR, and regime/tradability fields.
- Stable event IDs do not depend on future entry/exit outcomes.
- Risk/exit plan places stop beyond the sweep extreme and target at opposite liquidity or fallback R multiple.
- Cost-aware RR gate blocks trades that are structurally positive gross but net-negative after fees/spread/slippage.
- CLI accepts `--pattern LIQUIDITY_SWEEP_REVERSAL` and records selected defaults/overrides in JSON metadata.
- Strategy backtest can persist at least one saved run or explicitly reports environment blockers.
- Initial bounded grid is run only after tests pass.
- Backtest summary compares results to recent FVG/OB baselines.
- No live trading, signed requests, order/account endpoints, API keys, or `.env` changes are introduced.

# Required Tests

## Unit Tests

- Bullish sell-side sweep + reclaim + displacement + FVG confluence emits one valid event.
- Bearish buy-side sweep + reclaim + displacement + OB confluence emits one valid event.
- Wick sweep without close reclaim emits no valid event.
- Reclaim without displacement emits no valid event.
- Displacement with insufficient prior-only volume ratio emits weak/no event according to config.
- Event timestamp is the confirmation candle timestamp.
- Adding future candles after confirmation does not change the emitted event ID or fields.
- Same input candles produce stable event IDs across runs.
- Missing required candle columns raise deterministic `ValueError`.
- Unsorted candle input raises deterministic `ValueError`.
- Pattern score component weights sum to the documented total and include limitations metadata.

## Integration Tests

- `strategy_for_pattern("LIQUIDITY_SWEEP_REVERSAL")` returns the new strategy.
- Pattern strategy `evaluate_at` works through the cache/context path without scanning future candles.
- Action builder creates retest entry, stop, target, and expiration actions.
- Stop invalid cases emit `LIQUIDITY_SWEEP_STOP_INVALID`.
- Cost-rejected cases emit `LIQUIDITY_SWEEP_COST_AWARE_RR_REJECTED`.
- CLI parser accepts the new pattern and focused `--lsr-*` flags.
- Strategy runner output JSON includes pattern metadata and cost gate metadata.
- A small synthetic backtest produces deterministic trades and net-cost accounting.

## Contract Tests

- Public pattern exports include `LiquiditySweepReversalConfig`, event dataclass, detector, and risk-exit config.
- CLI metadata documents default parameter values and whether tradability/MTF gates were enabled.
- API/persistence payload remains additive; no existing saved-run fields are removed or renamed.
- If docs/API schema changes, update `docs/api/API_CONTRACT.md` or the relevant command guide section.

## Safety Tests

- New detector, strategy, and tests do not import Binance execution clients.
- No test calls real exchange order/account endpoints.
- No API key, secret, signed request, or `.env` behavior is added.
- Strategy code does not fetch market data directly.
- Paper/backtest code remains offline and deterministic.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- No lookahead in detector, MTF context, entry simulation, or target selection.
- Cost/slippage/fill assumptions are explicit.
- Parameter grid was predeclared before running.
- Baseline comparison included.
- Weak or negative results are reported without retuning.

# Verification

Default focused verification:

```bash
pytest tests/patterns/test_liquidity_sweep_reversal.py \
  tests/patterns/test_liquidity_sweep_reversal_risk_exit.py \
  tests/strategies/test_pattern_strategies.py \
  tests/backtesting/test_pattern_action_builder.py \
  tests/backtesting/test_pattern_postgres_runner_cli.py \
  tests/safety/test_pattern_live_boundary.py -q
git diff --check
```

Full verification if focused tests pass:

```bash
pytest
git diff --check
```

Initial saved-run command family after implementation:

```bash
quant-bitcoin-strategy-backtest \
  --pattern LIQUIDITY_SWEEP_REVERSAL \
  --start-time 2026-05-25T00:00:00Z \
  --starting-cash 1000000 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10
```

Grid variants must be recorded with exact commands and saved run IDs in the task completion notes or a follow-up research note.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- saved backtest run IDs
- initial result comparison against Task 274/275 baselines
- Codex self-review result
- known limitations
- recommended next task

# Completion Summary (2026-05-29)

- Files changed for Task 276:
  - `quant_bitcoin/patterns/liquidity_sweep_reversal.py`
  - `quant_bitcoin/patterns/liquidity_sweep_reversal_risk_exit.py`
  - `quant_bitcoin/patterns/__init__.py`
  - `quant_bitcoin/strategies/patterns.py`
  - `quant_bitcoin/strategies/pattern_execution_policy.py`
  - `quant_bitcoin/strategies/pattern_explanations.py`
  - `quant_bitcoin/backtesting/fvg_detection_cache.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `quant_bitcoin/indicators/market_regime.py`
  - `tests/patterns/test_liquidity_sweep_reversal.py`
  - `tests/patterns/test_liquidity_sweep_reversal_risk_exit.py`
  - `tests/backtesting/test_liquidity_sweep_reversal_strategy.py`
  - project ledgers: `STATUS.md`, `PROJECT_HISTORY.md`, `BACKLOG.md`, this task file.
- Implementation summary:
  - Added deterministic offline-only `LIQUIDITY_SWEEP_REVERSAL` event detection from completed candles.
  - Added sweep-extreme risk/exit planning, default retest entry policy, strategy wiring, cached evaluate-at path, CLI `--lsr-*` flags, output metadata, and LSR-specific skip reasons.
  - Added a small market-regime performance fix by calculating spread proxy values once per call instead of once per row.
- Tests added or updated:
  - Added bullish/bearish detector, no-sweep, no-reclaim, weak-displacement, low-volume, stable ID/no-lookahead, metadata/score, risk-exit, strategy/action-builder, cost-rejection, stop-invalid, and CLI metadata tests.
- Tests run:
  - `pytest tests/indicators/test_market_regime.py tests/patterns/test_liquidity_sweep_reversal.py tests/patterns/test_liquidity_sweep_reversal_risk_exit.py tests/backtesting/test_liquidity_sweep_reversal_strategy.py tests/strategies/test_pattern_strategies.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/safety/test_pattern_live_boundary.py -q`
  - Result: 192 passed.
  - `git diff --check`
  - Result: passed.
- Saved backtest run IDs:
  - Run 114.
- Command used:

```bash
python - <<'PY'
from quant_bitcoin.backtesting.strategy_postgres_runner_cli import main
raise SystemExit(main([
    '--pattern', 'LIQUIDITY_SWEEP_REVERSAL',
    '--interval', '1m',
    '--start-time', '2026-05-20T00:00:00Z',
    '--starting-cash', '1000000',
    '--position-sizing-mode', 'cash_fraction',
    '--position-sizing-value', '0.10',
]))
PY
```

- Run 114 result:
  - Dataset: BTCUSDT 1m, 12,027 candles, 2026-05-20T00:00:00Z through 2026-05-28T08:26:00Z.
  - Effective starting cash: 666.67 USDT quote cash from default KRW 1,000,000 / 1500.
  - Candidates/actions emitted: 20.
  - Filled trades: 0.
  - Gross PnL: 0.0.
  - Net PnL: 0.0.
  - Final equity: 666.67 USDT.
  - Total costs: 0.0.
  - Win rate/profit factor: not available because no completed trades.
  - Max drawdown: 0.0.
  - Skip counts: 11 `LIQUIDITY_SWEEP_COST_AWARE_RR_REJECTED`, 9 `LIQUIDITY_SWEEP_RETEST_NOT_FILLED`.
  - Candidate side split: 13 SHORT, 7 LONG.
  - Session/liquidity/spread attribution: no completed trades, so attribution is empty.
- Baseline comparison:
  - Task 274 run 107: `ORDER_BLOCK` MTF branch, 14 trades, -1.79 net PnL.
  - Task 274 run 109: FVG + local OB confluence, 2 trades, -0.34 net PnL.
  - Task 275 run 113: local FVG OB confluence follow-up reduced trade count/loss versus default FVG.
  - Run 114 is not directly profitable or comparable on PnL because no trade passed retest and cost gates. It did avoid losses, but produced no exposure.
- Cost conclusion:
  - Realistic costs blocked 11 candidates before entry, and 9 more retests did not fill. Costs/filtering destroyed executable opportunity on this recent window.
- Known limitations:
  - The broader Task 276 V2-V8 grid was not run because the latest owner request was a single 1m backtest from 2026-05-20 onward.
  - No promotion is justified from a zero-fill recent-window run.
  - Native DB-backed 1h/4h context remains Task 265.
- Recommended next task:
  - Create/assign an LSR sensitivity task to run MTF 15m, MTF 15m/1h, stricter volume, both FVG+OB, FVG-only, OB-only, and zero-cost diagnostic variants against run 114.
