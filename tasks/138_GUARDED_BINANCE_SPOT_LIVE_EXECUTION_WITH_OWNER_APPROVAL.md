# Goal

Add a guarded Binance Spot live execution path for long-only trading after explicit owner approval, using the existing canonical execution interface, spot product policy, real fee/slippage reconciliation, and strict safety guardrails.

This task is intentionally last in the sequence. It must not be executed unless the owner explicitly approves live order execution in the assigned work context.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `quant_bitcoin/execution/`
- `quant_bitcoin/risk/`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/market_data/`
- `quant_bitcoin/persistence/`
- `tests/execution/`
- `tasks/132_CANONICAL_ORDER_INTENT_AND_PAPER_EXECUTION.md`
- `tasks/134_SHORT_PRODUCT_MODEL_POLICY_AND_LIVE_BOUNDARY.md`
- `tasks/135_BINANCE_SPOT_TESTNET_EXECUTION_CLIENT.md`
- `tasks/136_REAL_FEE_AND_SLIPPAGE_RECONCILIATION.md`
- current Binance Spot API documentation before implementation

# Extracted Roles

- Owner role:
  - Live spot execution owner.
  - Owns live endpoint gating, kill switch, max-notional constraints, long-only spot policy, and explicit owner approval records.
- Supporting roles:
  - Risk role: blocks unsafe order intents.
  - Product policy role: blocks shorts for spot.
  - Execution reconciliation role: records fills and actual costs.
  - Runtime role: supplies validated order intents.
- Forbidden roles:
  - No margin trading.
  - No futures trading.
  - No short spot entry.
  - No live trading by default.
  - No committed credentials.
  - No hidden enablement through environment defaults.

# Context

The project currently blocks live trading by design. A live path can only be considered after paper mode, real-time runner, short product policy, testnet execution, and fee/slippage reconciliation are complete. Even then, live spot must be long-only and guarded by explicit owner approval plus runtime safety controls.

# Scope

- Add live spot execution client or extend testnet client with a separately gated live mode.
- Require explicit live enablement through a non-default configuration value.
- Require owner approval record in task/status docs before implementation.
- Enforce spot long-only policy.
- Add kill switch.
- Add max order notional guard.
- Add max daily notional or max daily loss guard where practical.
- Add duplicate client-order-id protection.
- Add structured logging of every live order intent and execution report.
- Add startup readiness checks that fail closed.
- Add tests proving live mode is disabled by default.

# Out of Scope

- Margin execution.
- Futures execution.
- Leverage.
- Borrow/funding/liquidation models.
- Multi-symbol portfolio execution.
- Autonomous unattended deployment.
- Strategy profitability guarantees.

# Requirements

- Live trading must be disabled by default.
- `ENABLE_LIVE_TRADING` or equivalent must not default to true.
- Live mode must require explicit owner approval recorded in task/status docs before code execution.
- Live endpoint base URL must be explicitly configured and tested separately from testnet.
- The client must fail closed if credentials are missing.
- The client must fail closed if kill switch is active.
- The client must reject `ENTER_SHORT` and `EXIT_SHORT` in spot live mode.
- The client must reject orders over max notional.
- The client must reject duplicate client order ids or make idempotency explicit.
- Runtime logs must include order intent id, action type, position side, execution side, requested quantity, reference price, and result status.
- Ordinary test suite must not make live network calls.

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

- Live spot execution path exists only behind explicit gating.
- Live mode is disabled by default.
- Tests prove no live order can be submitted without explicit enablement.
- Kill switch blocks order submission.
- Max notional guard blocks oversized order intent.
- Spot short intent is blocked.
- Duplicate order id behavior is deterministic.
- Execution reports are captured for live orders when the client is used.
- No margin/futures endpoint is added.

# Required Tests

## Unit Tests

- Test live mode disabled by default.
- Test missing explicit enablement blocks order submission.
- Test kill switch blocks order submission.
- Test max order notional guard.
- Test duplicate client order id guard.
- Test spot `ENTER_SHORT` is blocked.
- Test live credential missing errors fail closed.
- Test live endpoint allowlist rejects unknown path.

## Integration Tests

- Test fake live HTTP client receives no call when disabled.
- Test fake live HTTP client receives expected signed request when explicitly enabled in test context.
- Test real-time runner can be wired to live client only when all guards pass in mocked mode.

## Contract Tests

- Strategy layer does not import live client.
- Market-data layer does not import live client.
- Product policy blocks unsupported spot shorts before request signing.
- Reconciliation receives live execution reports without submitting additional orders.

## Safety Tests

- No real network calls in ordinary tests.
- No committed API keys.
- No `.env` files committed or generated.
- No default live enablement.
- No margin/futures endpoints.
- No short live spot orders.

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

Additional verification:

```bash
pytest tests/execution
pytest tests/market_data
pytest tests/backtesting/test_strategy_engine_accounting.py
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
