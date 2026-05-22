# Goal

Make pattern entries conservative and configurable by filtering weak pattern events and fixing pattern position sizing behavior.

The canonical pattern strategy must not blindly enter every event that has a valid risk plan. It must respect pattern quality and sizing configuration.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/strategies/actions.py`
- all pattern detector files under `quant_bitcoin/patterns/`
- existing pattern strategy and backtesting tests

# Extracted Roles

- Owner role:
  - Pattern strategy configuration owner.
  - Owns event filtering and position-sizing intent before engine execution.
- Supporting roles:
  - Pattern detector role: supplies status, score, risk/reward, direction, and references.
  - Backtesting engine role: applies configured quantity when action quantity is absent.
  - CLI role: exposes safe filters where practical.
- Forbidden roles:
  - No new detector algorithms.
  - No performance optimization or parameter mining.
  - No live trading.
  - No portfolio optimization engine.
  - No margin model implementation.

# Context

Current pattern strategy code maps `BULLISH` to `LONG` and `BEARISH` to `SHORT`, creates a risk plan, and emits an entry action if the risk plan is valid. It can ignore `pattern_status` such as `WEAK`. Pattern actions may also hardcode `quantity=1.0`, which can bypass CLI `--trade-quantity` because the engine prioritizes action quantity over engine default quantity.

This creates two problems:

- Weak patterns can be traded by default.
- CLI trade quantity may not control pattern backtest sizing as expected.

# Scope

- Add deterministic pattern event filtering before entry action creation.
- Default behavior should require `pattern_status == VALID`.
- Add configuration for allowing `WEAK` events only when explicitly enabled.
- Add optional minimum pattern score where detector exposes `pattern_score`.
- Add optional minimum risk/reward where event exposes `risk_reward` or risk plan target metadata.
- Fix pattern action quantity behavior so CLI `--trade-quantity` is respected by default.
- Preserve explicit action quantity only when intentionally configured.

# Out of Scope

- Risk-based position sizing implementation unless minimal and explicitly configured.
- Kelly sizing, volatility targeting, portfolio-level sizing, or optimization.
- Detector threshold redesign.
- Full lifecycle orchestration.
- Transaction costs.

# Requirements

- Default pattern strategy behavior must skip non-`VALID` events.
- Skipped event metadata must include skip reason:
  - `PATTERN_STATUS_NOT_ALLOWED`
  - `PATTERN_SCORE_BELOW_MINIMUM`
  - `RISK_REWARD_BELOW_MINIMUM`
  - `RISK_PLAN_INVALID`
- Pattern action quantity should be `None` by default so the engine uses `StrategyEngineConfig.trade_quantity`.
- If explicit quantity override is configured, it must be visible in metadata and tests.
- CLI or strategy config should support:
  - allowed pattern statuses;
  - minimum pattern score;
  - minimum risk/reward;
  - optional explicit quantity override if needed.
- The implementation must not silently change RSI action sizing.

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

- A `WEAK` pattern event is skipped by default.
- A `WEAK` pattern event can be entered only when weak events are explicitly allowed.
- A valid event below minimum score is skipped.
- A valid event below minimum risk/reward is skipped when that filter is configured.
- Pattern actions use CLI `--trade-quantity` by default.
- Pattern action explicit quantity override works only when explicitly configured.
- Skipped events are not counted as filled trades.

# Required Tests

## Unit Tests

- Test `VALID` event passes default filter.
- Test `WEAK` event fails default filter.
- Test `WEAK` event passes when allowed.
- Test score filter.
- Test risk/reward filter.
- Test risk-plan invalid skip reason.
- Test action quantity defaults to `None` for pattern actions.
- Test engine uses `trade_quantity` when action quantity is absent.
- Test explicit quantity override metadata.

## Integration Tests

- Test canonical CLI `--trade-quantity` changes pattern execution quantity.
- Test weak-event fixture produces skip output by default.
- Test allowed-weak config produces entry output.

## Contract Tests

- Pattern detectors remain responsible only for event classification.
- Pattern strategy remains responsible for filtering and semantic actions.
- Engine remains responsible for applying quantities to portfolio state.

## Safety Tests

- No live order execution.
- No exchange calls.
- No API keys.

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
pytest
```

# Additional Verification

```bash
pytest tests/strategies/test_pattern_strategies.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
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
