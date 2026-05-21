# Task: Strategy-Level Backtest Orchestration

## Mode
Create/implement task definition for a future implementation request.

## Goal
Refactor the current pattern backtest workflow from pattern-level execution to strategy-level execution so the public backtest unit is a strategy selected by `--strategy`, not a raw pattern selected by `--pattern`.

## Source Requirement (Cleaned)
Introduce a strategy-level backtest orchestration model where:

- each implemented pattern can be wrapped by a corresponding strategy,
- the CLI selects a strategy using `--strategy`,
- existing pattern detectors and existing risk/exit planners remain reusable internal components,
- the backtest runner executes selected strategies,
- pattern-level selection is removed, deprecated, or retained only as an explicitly documented and tested backward-compatible alias,
- no live trading/order execution/API keys/`.env` handling/signed requests/account or order endpoints are introduced.

## Context and Problem Statement
The current PostgreSQL-backed pattern backtest workflow exposes low-level pattern identifiers directly (for example `FAIR_VALUE_GAP`, `ORDER_BLOCK`, `TRENDLINE_BREAK`, `CUP_AND_HANDLE`, `DIAMOND`, `ADAM_AND_EVE`) through `--pattern`.

That interface is conceptually too low-level. A pattern detector is an internal signal component. The executable and reportable entity for backtesting should be a strategy.

## Target Strategy Identifiers
Define initial one-pattern strategies for already implemented patterns:

- `FAIR_VALUE_GAP_STRATEGY`
- `TRENDLINE_BREAK_STRATEGY`
- `ORDER_BLOCK_STRATEGY`
- `CUP_AND_HANDLE_STRATEGY`
- `DIAMOND_STRATEGY`
- `ADAM_AND_EVE_STRATEGY`

Each initial strategy may wrap exactly one existing pattern detector plus its existing risk/exit planner.

## Conceptual Model

- Pattern detector: identifies market structures.
- Pattern risk/exit planner: converts detected events into risk/exit plans.
- Strategy: owns signal selection/filtering/entry/exit naming/reporting behavior.
- Backtest: executes one selected strategy across historical candles.
- CLI: selects a strategy and launches backtest execution.

## Dependencies
This task depends on behavior from existing pattern detection, pattern risk/exit planning, pattern strategy backtest, and PostgreSQL backtest CLI tasks, especially:

- `tasks/040_PATTERN_DETECTION_ENGINE.md`
- `tasks/041_TRENDLINE_BREAK_PATTERN_ENGINE.md`
- `tasks/042_ORDER_BLOCK_PATTERN_ENGINE.md`
- `tasks/043_CUP_AND_HANDLE_PATTERN_ENGINE.md`
- `tasks/044_DIAMOND_PATTERN_ENGINE.md`
- `tasks/045_ADAM_AND_EVE_PATTERN_ENGINE.md`
- `tasks/047_PATTERN_RISK_EXIT_PLAN_CONTRACT.md`
- `tasks/048_TRENDLINE_BREAK_RISK_EXIT_PLAN.md`
- `tasks/049_ORDER_BLOCK_RISK_EXIT_PLAN.md`
- `tasks/050_FAIR_VALUE_GAP_RISK_EXIT_PLAN.md`
- `tasks/051_CUP_AND_HANDLE_RISK_EXIT_PLAN.md`
- `tasks/052_DIAMOND_RISK_EXIT_PLAN.md`
- `tasks/053_ADAM_AND_EVE_RISK_EXIT_PLAN.md`
- `tasks/054_PATTERN_EXIT_SIMULATION_INTEGRATION.md`
- `tasks/055_PATTERN_STRATEGY_BACKTEST.md`
- `tasks/056_PATTERN_POSTGRES_BACKTEST_CLI.md`
- `tasks/058_PATTERN_BACKTEST_ALL_IMPLEMENTED_PATTERN_SELECTION.md`

## Extracted Roles and Responsibility Boundary

### Owner Role
Define and approve the public orchestration boundary so backtests are requested by strategy identity.

### Implementation Role
Refactor orchestration code and CLI wiring to strategy-level selection while preserving existing internal detector/planner reuse and existing safety boundaries.

### Forbidden Role Expansion
Do **not** introduce:

- live trading,
- real exchange order execution,
- account/order endpoints,
- API-key or `.env` behavior,
- shared contract redesign beyond what is minimally required for strategy-selection orchestration,
- unrelated architecture expansion (scheduler/dashboard/FastAPI/Streamlit/Docker/ML/futures/leverage/portfolio optimization).

If strategy-level orchestration requires breaking shared contracts, stop and report before implementation.

## Scope

- Add a strategy registry (or equivalent deterministic mapping) for backtest orchestration.
- Move public CLI selection from `--pattern` to `--strategy`.
- Ensure the backtest runner executes selected strategies.
- Keep existing detectors and pattern risk/exit planners as internal reusable components.
- Define deterministic strategy metadata and names in outputs.
- Decide and implement one of the following for `--pattern`:
  - removal, or
  - documented deprecation path, or
  - documented backward-compatible alias to `--strategy`.
- Update docs and tests so the new public contract is explicit.

## Out of Scope

- New live-trading or paper-trading behavior.
- Exchange account/order integration.
- New detector algorithms.
- New risk model architecture.
- Persistence/database redesign beyond what is needed for strategy selection wiring.

## Required CLI Direction
Public CLI concept changes from pattern selection:

```bash
quant-bitcoin-pattern-backtest --pattern ORDER_BLOCK
```

to strategy selection:

```bash
quant-bitcoin-pattern-backtest --strategy ORDER_BLOCK_STRATEGY
```

If `--pattern` remains temporarily, it must be explicitly treated as compatibility behavior and covered by tests/documentation.

## Requirements

1. Introduce explicit strategy identifiers for all currently implemented one-pattern strategies listed above.
2. Backtest orchestration must resolve selected strategy -> detector/planner/execution configuration deterministically.
3. Backtest output must include selected strategy identity and use stable naming.
4. Existing internal pattern detector and risk/exit planner modules must be reused rather than duplicated.
5. Unsupported strategy identifiers must fail fast with clear errors before provider/backtest execution.
6. If backward compatibility for `--pattern` is kept, precedence and conflict rules with `--strategy` must be deterministic and tested.
7. No silent fallback from unsupported strategies to defaults.
8. Preserve existing no-live-trading safety boundary.

## Design Expectations for Future Composite Strategies
The strategy registry/orchestration design should allow future additions without redesign, including:

- multi-pattern confluence,
- trend-following strategies,
- reversal strategies,
- volatility-filtered pattern strategies,
- regime-filtered strategies.

This task does **not** need to implement these composites now, only preserve a clean extension path.

## Acceptance Criteria

- CLI supports `--strategy` selection and runs backtests by strategy identity.
- Initial strategy identifiers listed in this task are selectable and executed deterministically.
- Existing detectors/planners remain internal reusable components.
- Unsupported strategy names fail clearly and early.
- If `--pattern` is retained, behavior is explicitly documented and tested as compatibility mode.
- No live trading or exchange order/account endpoint behavior is introduced.

## Verification Plan (for implementation phase)

- Unit tests for strategy registry resolution and validation.
- CLI argument parsing tests for `--strategy` and compatibility behavior (if any).
- Integration-style backtest tests proving deterministic strategy selection and metadata output.
- Safety checks ensuring no exchange order/account endpoint usage is introduced.
- Documentation consistency check.

Suggested commands:

- `pytest tests/backtesting`
- `pytest tests/cli`
- `git diff --check`

(adjust test paths to actual repository layout).

## Relevant Files for Future Implementation

- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/patterns/`
- `tests/backtesting/test_pattern_strategy_backtest.py`
- `tests/backtesting/test_pattern_postgres_runner_cli.py`
- `README.md`
- `STATUS.md`

## Open Questions To Resolve During Implementation

- Should `--pattern` be removed immediately or kept as a deprecated alias?
- If both `--strategy` and `--pattern` are provided, what is the deterministic rule (error vs precedence)?
- Which module should own the strategy registry to avoid circular dependencies?
- What default strategy (if any) should be selected when `--strategy` is omitted?

## Completion Checklist (for implementation phase)

- [ ] Implement only strategy-level orchestration scope.
- [ ] Keep changes limited to orchestration, CLI, tests, and required docs.
- [ ] Add/update tests for parser behavior, selection validation, and runner metadata.
- [ ] Run verification commands.
- [ ] Run Codex self-review using `reviews/CODEX_SELF_REVIEW.md`.
- [ ] Update `STATUS.md` if active state changes.
- [ ] Document known limitations and recommended next step.
