# Goal

Add stronger liquidity, spread-proxy, and session feature tagging so bad performance can be analyzed against tradability and time-of-day conditions.

# Source Requirement

Current market regime uses OHLCV-derived trading value and high-low spread proxy. The backlog still lists liquidity indicator and bid-ask spread indicator candidates. Poor performance may concentrate in low-liquidity sessions or wide-range candles where fills are unrealistic.

# Extracted Roles

- Owner role:
  - Tradability research feature owner.
- Supporting roles:
  - Indicator role.
  - Backtest attribution role.
  - Frontend diagnostics role.
- Forbidden roles:
  - No real exchange account/order calls.
  - No live order book subscription.
  - No hardcoded API keys.

# Context

OHLCV-only strategies can look bad or misleading if entries occur during illiquid/wide-spread conditions. Even without full order book data, better proxies can help:
- quote volume,
- dollar volume percentile,
- high-low range percentile,
- wick ratio,
- session/time-of-day,
- weekend/weekday,
- volatility-liquidity interaction.

# Scope

- Add indicator outputs for:
  - quote/dollar volume percentile,
  - rolling liquidity z-score,
  - range-spread proxy percentile,
  - wick-dominance proxy,
  - session tag: Asia/EU/US/overlap if UTC-based approximation is acceptable,
  - weekday/weekend tag.
- Add metadata caveats that these are proxies, not true bid-ask/order-book spread.
- Wire optional tags into engine `market_regime_by_timestamp` or a related metadata map.
- Add attribution by session/liquidity/spread regime.
- Add frontend display under diagnostics.

# Out of Scope

- No live order book data.
- No Binance network call.
- No external API dependency.
- No trading rule changes unless a later task uses filters.

# Requirements

- Feature computation is pure and deterministic.
- Proxy nature is documented.
- Attribution can group by session and liquidity regime.
- Dashboard can show if losses concentrate in poor-liquidity/wide-proxy regimes.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- All liquidity/spread features are OHLCV-derived proxies; no order book, exchange, network, or account data is used.
- Feature tags are diagnostics/attribution metadata only and must not filter trades or change strategy behavior.
- UTC session buckets are approximate research tags, not venue-specific session truth.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Tests for session classification.
- Tests for liquidity percentile and range-spread proxy.
- Attribution by session/liquidity works with synthetic data.
- Docs note limitations.

# Required Tests

## Unit Tests

- Indicator feature calculations.
- Timezone/UTC session classification.

## Integration Tests

- Engine metadata tagging with new features.
- Frontend build.

## Contract Tests

- Docs/API mention proxy semantics.

## Safety Tests

- No network calls.

# Verification

Default:

```bash
pytest tests/indicators tests/backtesting/test_performance_metrics.py
npm --prefix frontend run build
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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

# Completion Summary

- Files changed:
  - `quant_bitcoin/indicators/market_regime.py`
  - `quant_bitcoin/indicators/__init__.py`
  - `quant_bitcoin/backtesting/strategy_engine.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `quant_bitcoin/backtesting/performance_metrics.py`
  - `tests/indicators/test_market_regime.py`
  - `tests/backtesting/test_performance_metrics.py`
  - `tests/backtesting/test_strategy_engine.py`
  - `frontend/src/app/page.tsx`
  - `docs/api/API_CONTRACT.md`
- Implementation summary:
  - Added OHLCV-derived trading-value percentile, liquidity z-score, range-spread proxy percentile, wick-dominance proxy, UTC session tag, and weekday/weekend tag.
  - Propagated proxy tags through optional engine `market_regime_by_timestamp` metadata without changing fills or strategy behavior.
  - Extended trade attribution with `by_liquidity_regime`, `by_spread_regime`, and `by_weekday_tag` groups, while retaining `by_session`.
  - Added a read-only frontend Tradability Diagnostics panel and API proxy caveat documentation.
- Tests added or updated:
  - Added session/weekday, percentile, proxy, engine tagging, and attribution grouping assertions.
- Tests run:
  - `pytest tests/indicators tests/backtesting/test_performance_metrics.py tests/backtesting/test_strategy_engine.py`
  - `npm --prefix frontend run build`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed within Task 185; no network calls, exchange endpoints, API keys, live order book, trading filters, or strategy behavior changes were added.
- Known limitations:
  - Liquidity and spread values are candle-derived proxies only, not bid-ask or order-book measurements.
- Recommended next task:
  - Task 186.
