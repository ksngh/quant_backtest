# Task 260: FVG V2 Channel Owner Profile Defaults

# Goal

Make the current owner-approved FVG v2 channel research settings usable as the default strategy-backtest profile, so the owner can run the canonical command with far fewer flags while preserving explicit, auditable CLI metadata.

# Source Requirement

Owner clarified after Task 259:

```text
자 아주좋아... 이걸 default로 쓸 수 있도록 해줘. 지금 이 설정을.
```

Clean requirement:

- Promote the current owner FVG v2 channel command settings into a default or default profile for `quant-bitcoin-strategy-backtest`.
- Reduce the required command to the minimal owner-facing form.
- Preserve safety boundaries: this remains offline backtesting/research only and must not introduce live trading behavior.

# Extracted Roles

- Owner role:
  - Approves the current FVG v2 channel settings as the desired default workflow.
- Supporting roles:
  - CLI role: owns parser defaults, profile/preset selection, help text, and metadata emission.
  - Strategy runner role: wires defaults into existing FVG v2 channel config without bypassing existing validation.
  - Documentation role: updates command examples and explains the new minimal command.
  - Test role: verifies parser defaults and emitted metadata.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, account endpoints, or exchange order endpoints.
  - Do not change strategy math beyond default configuration wiring.
  - Do not make `--start-time 2026-05-28T00:00:00Z` a global default; date ranges remain dataset/run-specific.
  - Do not make hidden behavior unauditable; defaults must be visible in strategy parameters/summary metadata.

# Context

Current owner-approved command after Tasks 257-259 is:

```bash
quant-bitcoin-strategy-backtest \
  --pattern FAIR_VALUE_GAP \
  --start-time 2026-05-28T00:00:00Z \
  --cost-profile conservative_crypto_1m \
  --enable-fvg-v2 \
  --enable-fvg-v2-channel \
  --fvg-channel-standalone-scan \
  --fvg-channel-window 20 \
  --fvg-channel-max-wait-bars 5 \
  --fvg-use-trend-score \
  --fvg-use-fibonacci-confluence \
  --fvg-stop-mode wider_of_fvg_and_swing \
  --enforce-candle-continuity \
  --enable-market-regime \
  --starting-cash 1000000 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10
```

The following flags are candidates for the new default owner FVG channel profile:

- `--pattern FAIR_VALUE_GAP`
- `--cost-profile conservative_crypto_1m`
- `--enable-fvg-v2`
- `--enable-fvg-v2-channel`
- `--fvg-channel-standalone-scan`
- `--fvg-channel-window 20`
- `--fvg-channel-max-wait-bars 5`
- `--fvg-use-trend-score`
- `--fvg-use-fibonacci-confluence`
- `--fvg-stop-mode wider_of_fvg_and_swing`
- `--enforce-candle-continuity`
- `--enable-market-regime`
- `--starting-cash 1000000`
- `--position-sizing-mode cash_fraction`
- `--position-sizing-value 0.10`

The following should remain explicit per run:

- `--start-time`
- `--end-time`
- data source, symbol, and interval unless an existing project default already applies.

# Scope

- Decide and implement one explicit defaulting mechanism:
  - Preferred: make these the defaults for `quant-bitcoin-strategy-backtest` when `--pattern FAIR_VALUE_GAP` is selected and no conflicting override is provided.
  - Acceptable alternative if safer: add an owner profile flag such as `--profile owner_fvg_v2_channel` and document it as the project default command path.
- Preserve explicit CLI overrides for every defaulted field.
- Ensure defaulted values appear in emitted strategy config/summary metadata.
- Update parser/help text and README command examples.
- Add tests proving the minimal command receives the owner-approved defaults.
- Add tests proving explicit overrides still work.

# Out of Scope

- No live trading.
- No exchange account/order endpoints.
- No credentials or `.env` changes.
- No strategy math changes.
- No frontend dashboard changes except documentation if needed.
- No database schema migration.
- No default `start-time` or fixed date range.

# Requirements

- The minimal owner command should be documented. Expected shape:

```bash
quant-bitcoin-strategy-backtest \
  --start-time 2026-05-28T00:00:00Z
```

- If the implementation keeps `--pattern FAIR_VALUE_GAP` explicit for clarity, document the minimal command as:

```bash
quant-bitcoin-strategy-backtest \
  --pattern FAIR_VALUE_GAP \
  --start-time 2026-05-28T00:00:00Z
```

- The defaulted run must behave as if these settings were supplied:
  - `cost_profile=conservative_crypto_1m`
  - FVG v2 enabled
  - FVG v2 channel enabled
  - standalone channel scan enabled
  - channel window `20`
  - channel max wait bars `5`
  - trend score enabled
  - Fibonacci confluence enabled
  - stop mode `wider_of_fvg_and_swing`
  - candle continuity enforced
  - market regime enabled
  - starting cash `1000000`
  - position sizing mode `cash_fraction`
  - position sizing value `0.10`
- `--start-time` must remain explicit and must not be hardcoded.
- Existing explicit overrides must still win.
- Metadata must make the applied profile/default values visible.
- Safety boundaries must remain unchanged.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `tests/backtesting/test_pattern_postgres_runner_cli.py`.
- [x] Read relevant README command sections.
- [x] Confirm whether defaulting is global or profile-based before coding.
- [x] Record assumptions, blockers, or unclear status items before coding.

Implementation note: defaulting is applied as an owner FVG profile after CLI
parse only when the selected pattern is `FAIR_VALUE_GAP`; other patterns keep
their prior parser defaults. Explicit flags and new disable/no flags override
the owner profile.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] Minimal command applies the owner FVG v2 channel defaults.
- [x] Explicit CLI overrides still override the defaults.
- [x] Strategy config/summary metadata shows the applied owner/default profile.
- [x] Tests cover parser/config defaults.
- [x] Tests cover at least one explicit override.
- [x] README documents the new minimal command and the expanded equivalent settings.
- [x] No live trading behavior or exchange order/account endpoint behavior is introduced.

# Required Tests

## Unit Tests

- [x] Parser/default construction test for the minimal command.
- [x] Override test for at least:
  - `--cost-profile`
  - `--position-sizing-mode` / `--position-sizing-value`
  - `--fvg-channel-standalone-scan` behavior if a disabling mechanism is needed.

## Integration Tests

- [x] Existing FVG channel CLI metadata tests should pass.
- [x] Add or update CLI metadata test proving the default profile reaches the action builder/config metadata.

## Contract Tests

- [x] Update API/README docs if metadata field names change.
- [x] No database schema change expected.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_fvg_channel.py -q
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
