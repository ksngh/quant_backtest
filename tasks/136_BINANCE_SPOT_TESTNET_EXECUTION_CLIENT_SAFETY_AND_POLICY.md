# Goal

Add a Binance Spot testnet execution client behind the canonical execution interface, with endpoint allowlisting, credential policy, deterministic safety checks, and long-only spot behavior.

This task enables testnet orders only. It must not enable live trading.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/execution/`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/risk/`
- `quant_bitcoin/runtime_logging.py`
- `pyproject.toml`
- `tests/execution/`
- `tasks/132_CANONICAL_ORDER_INTENT_AND_PAPER_EXECUTION.md`
- `tasks/134_SHORT_PRODUCT_MODEL_POLICY_AND_LIVE_BOUNDARY.md`
- current Binance Spot API and Spot Testnet documentation before implementation

# Extracted Roles

- Owner role:
  - Testnet execution owner.
  - Owns signed testnet order submission, endpoint allowlist, credential loading, and execution report mapping.
- Supporting roles:
  - Order-intent role: supplies validated intent.
  - Risk role: approves or blocks intents before execution.
  - Product policy role: blocks unsupported short intents for spot.
- Forbidden roles:
  - No live Binance endpoint.
  - No live order execution.
  - No margin/futures endpoints.
  - No committed secrets or `.env` files.
  - No default live trading flag.

# Context

The project currently blocks real Binance order execution. Before any live account integration, testnet execution should be introduced behind a clear interface. The client must be safe by construction: testnet URL only, explicit credentials, endpoint allowlist, no live host fallback, no short spot entry.

# Scope

- Add `BinanceSpotTestnetExecutionClient` or equivalent.
- Implement signed request creation for testnet order endpoints only.
- Implement endpoint allowlist for required testnet endpoints.
- Load API key/secret from environment variables only.
- Reject missing credentials with explicit errors.
- Convert `OrderIntent` to Binance Spot testnet order request.
- Convert Binance testnet response to `ExecutionReport`.
- Support market and/or limit orders according to owner-approved scope.
- Enforce spot product policy: long-only, no `ENTER_SHORT`.
- Add request-signing tests without real network calls.
- Add fake HTTP client tests.

# Out of Scope

- Live Binance orders.
- Margin or futures trading.
- Account balance reconciliation unless required for basic safety precheck.
- Fill history polling beyond response mapping.
- Actual fee/slippage reconciliation beyond response fields.
- Deployment or scheduler setup.

# Requirements

- The client must default to Binance Spot testnet base URL only.
- The client must not accept live base URL unless this is explicitly rejected or separately gated for a later live task.
- Credentials must be read from environment variables such as `BINANCE_TESTNET_API_KEY` and `BINANCE_TESTNET_API_SECRET`.
- The code must not commit or generate `.env` files.
- All signed request tests must use fake credentials.
- Endpoint allowlist must reject unknown paths.
- `ENTER_SHORT` must be blocked before request creation.
- Request payload must include deterministic client order id where supported.
- Network tests must be mocked unless a separate explicit integration-test flag is set.

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

- A testnet execution client exists behind the canonical execution interface.
- Fake HTTP tests verify signed request parameters.
- Unknown endpoints are rejected.
- Live Binance URL is not used by default and cannot be silently selected.
- Missing credentials fail clearly.
- Spot short intent is blocked and never becomes a Binance `SELL` order.
- No live order functionality is added.

# Required Tests

## Unit Tests

- Test HMAC signature generation with fake values.
- Test timestamp/recvWindow parameter inclusion.
- Test endpoint allowlist rejects unknown path.
- Test missing testnet API key fails.
- Test missing testnet API secret fails.
- Test live URL is rejected or unavailable in this client.
- Test `ENTER_LONG` maps to spot BUY request.
- Test `EXIT_LONG` maps to spot SELL request.
- Test `ENTER_SHORT` is blocked before request creation.

## Integration Tests

- Test fake HTTP client receives expected request.
- Test fake response maps to `ExecutionReport`.
- Test runtime runner can use the testnet client in mocked mode.

## Contract Tests

- Client implements the canonical execution interface.
- Strategy layer does not import Binance client.
- Market-data layer does not import Binance execution client.

## Safety Tests

- No live Binance URL in default config.
- No `.env` file creation.
- No API key committed in tests.
- No real network call in ordinary test suite.
- No margin/futures endpoint path.

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
