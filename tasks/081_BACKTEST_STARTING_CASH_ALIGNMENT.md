# Task 081: Backtest Starting Cash Alignment

# Goal

Align backtest cash baseline semantics so backtest start/end cash handling matches the RSI backtest expectation, while allowing the owner to set the starting cash amount explicitly at run time.

# Source Requirement

Owner request (2026-05-21):
- Backtest currently records `start_cash` and `end_cash` as `0` in some paths.
- Backtest conditions should be aligned with RSI backtest semantics.
- Starting cash must be user-configurable so the owner can choose the amount.

# Extracted Roles

- Owner role: Backtest Engine, Backtest CLI/Runner, Persistence Mapping
- Supporting roles: Test Designer
- Forbidden roles: Live Execution, Binance order client, Frontend UI redesign, Strategy formula changes

# Scope

- Identify backtest paths where summary/persistence currently records placeholder-neutral `starting_cash=0` / `ending_cash=0`.
- Align starting cash behavior across applicable backtest execution paths and ensure user-provided starting cash is respected consistently.
- Ensure ending cash is recorded from actual simulation result rather than placeholder zeros for aligned paths.
- Keep contract-safe behavior for components intentionally designed as placeholder-only, but document and test chosen behavior explicitly.
- Update/extend tests for:
  - user-configured starting cash is applied consistently,
  - ending cash non-zero when simulation/trades imply non-zero,
  - backward-compatible explicit override behavior.

# Out of Scope

- Live trading
- Real Binance order execution
- Risk management redesign
- Fees/slippage model redesign beyond existing behavior
- Frontend UX changes unrelated to cash field semantics
- Broad API contract redesign unless required by this task’s acceptance criteria

# Implementation Assumptions

- "Align with RSI semantics" means matching initial-capital handling behavior, not forcing identical strategy logic.
- If a runner currently uses placeholder financial summaries due to missing equity/cash engine wiring, this task will either:
  - wire existing available values correctly, or
  - keep placeholder behavior only when truly unavoidable and clearly documented in tests/status.

# Acceptance Criteria

- Relevant backtest execution path(s) no longer emit unconditional `starting_cash=0` placeholders when starting cash is provided or configured.
- User-configured starting cash is reflected consistently in aligned path(s).
- `ending_cash` reflects simulation outcome for aligned path(s), not unconditional zero placeholders.
- Existing explicit `--starting-cash` (or equivalent input) override behavior remains valid where available.
- No live exchange order/account endpoints are called.

# Required Tests

- Unit tests for default/override starting cash behavior.
- Unit/integration tests for ending cash mapping in output payload/persistence mapping.
- Regression tests for existing CLI argument parsing and deterministic summary structure.
- Safety check: no live exchange API calls.

# Review Checklist

- Change is limited to assigned backtest cash alignment scope.
- No unrelated frontend/backend area scope expansion.
- No secrets/API keys introduced.
- No real order execution behavior introduced.
- Status/history/backlog updates performed when implementation is later executed.
