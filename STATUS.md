# Project Status

# Current Phase

Phase 61: Status Ledger Split Task Definition

# Current Step

Task STATUS_LEDGER_SPLIT task document creation.

# Current Goal

Define a task document to split the project status ledger into STATUS.md, PROJECT_HISTORY.md, and BACKLOG.md with clear responsibilities and boundaries.

# Current Active Task

Task document creation in progress: tasks/STATUS_LEDGER_SPLIT.md for status-ledger split planning only (no split execution yet).

# Last Completed Step

Task 058: Pattern Backtest All Implemented Pattern Selection implementation.

Implemented a focused pattern registry for `FAIR_VALUE_GAP`, `TRENDLINE_BREAK`, `ORDER_BLOCK`, `CUP_AND_HANDLE`, `DIAMOND`, and `ADAM_AND_EVE`, each reusing its existing detector and risk/exit planner with the shared `simulate_pattern_exit` workflow. The CLI keeps `FAIR_VALUE_GAP` as the default, accepts one supported `--pattern` per run, rejects unsupported or multiple selections before provider/backtest execution, emits deterministic strategy names and selected pattern identifiers, and remains limited to historical simulation over stored candles with no live trading or exchange order/account behavior. Updated README examples and tests; verified targeted pattern/CLI tests, full `pytest`, CLI `--help`, and `git diff --check`.

Previous completed step: Task 057 Pattern Backtest CLI clarity and pattern selection implementation.

Implemented explicit Fair Value Gap wording for `quant-bitcoin-pattern-backtest --help`, changed default JSON strategy metadata to `FAIR_VALUE_GAP_PATTERN_STRATEGY`, added a tested `--pattern FAIR_VALUE_GAP` selection seam with validation that rejects unsupported patterns before provider/backtest execution, and documented a safe README usage example. Verified targeted pattern backtest/CLI tests, full `pytest`, CLI `--help`, and `git diff --check`.

Previous completed step: Task 057 task document creation.

Created `tasks/057_PATTERN_BACKTEST_CLI_CLARITY_AND_PATTERN_SELECTION.md` to define future implementation work for clearer Fair Value Gap default CLI description/help text, `FAIR_VALUE_GAP_PATTERN_STRATEGY` JSON output naming, README usage documentation, and a tested pattern-selection seam for additional supported pattern backtests while preserving the no-live-trading safety boundary.

Previous completed step before Task 057: Task 056 Pattern PostgreSQL Backtest CLI implementation.

Implemented `quant-bitcoin-pattern-backtest` as a project script entrypoint backed by `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`. The CLI loads completed `1m` candles through `PostgresCandleDataProvider`, rejects non-`1m` intervals, delegates simulation to the Task 055 pattern strategy backtest workflow, and prints a deterministic JSON summary. Added fake-backed CLI wiring, help, empty-candle, entrypoint-registration, reuse-contract, and safety tests in `tests/backtesting/test_pattern_postgres_runner_cli.py`. Verified with targeted CLI tests, `python -m quant_bitcoin.backtesting.pattern_postgres_runner_cli --help`, and the full `pytest` suite. Direct `quant-bitcoin-pattern-backtest --help` could not be executed in this environment before package installation because the script was not installed; editable installation was blocked by package build dependency availability/network restrictions. The script registration is verified in `pyproject.toml`.

# Next Step

Recommended next task: owner review/approval to implement tasks/STATUS_LEDGER_SPLIT.md by performing the actual STATUS.md -> STATUS.md + PROJECT_HISTORY.md + BACKLOG.md split. Local Docker Compose runtime startup verification for Task 014/018 remains deferred to a Docker-capable developer environment.

# Parallel Work Status

Parallel work is not currently recommended.

Reason:
Task 060 is a task-definition step; implementation should wait for explicit owner approval before shared persistence changes.

# Phase Checklist

- [x] Step 1.1: Create Codex workflow documentation
- [x] Python project setup complete and verified
- [x] Market data contract complete and verified
- [x] CSV data provider complete and verified
- [x] Parallel work rules reviewed after foundation completion
- [x] RSI strategy complete and verified
- [x] Basic backtest complete and verified
- [x] Paper trader complete and verified
- [x] Binance candle downloader complete and verified
- [x] Next task document selected or created
- [x] Improved backtesting complete and verified
- [x] Paper trading with state task document selected or created
- [x] Paper trading with state complete and verified
- [x] Later risk management task document selected or created
- [x] First concrete risk-management implementation task defined
- [x] Basic paper risk checks complete and verified
- [x] Later live trading safety-gates task document selected or created
- [x] Live trading safety gates defined
- [x] Live trading implementation blocker documented
- [x] Persistence schema design task document selected or created
- [x] Persistence schema design documented
- [x] Codex command consistency guide documented
- [x] Task 014: PostgreSQL Binance Backfill approved for implementation
- [x] Task 014: PostgreSQL Binance Backfill accepted for current cloud workflow with non-Docker verification
- [ ] Task 014: PostgreSQL Binance Backfill optional local Docker runtime startup verified
- [x] Task 015: Binance WebSocket Candle Ingestion approved for implementation
- [x] Task 015: Binance WebSocket Candle Ingestion complete and verified
- [x] Task 017: WebSocket Ingestion Readiness task document selected or created
- [x] Task 017: WebSocket Ingestion Readiness complete and verified
- [x] Task 018: Docker WebSocket Ingestion Service task document selected or created
- [x] Task 018: Docker WebSocket Ingestion Service complete and verified
- [x] Task 019: PostgreSQL Candle Data Provider for Backtesting task document selected or created
- [x] Task 019: PostgreSQL Candle Data Provider for Backtesting approved for implementation
- [x] Task 019: PostgreSQL Candle Data Provider for Backtesting complete and verified
- [x] Task 020: PostgreSQL Backtest Runner task document selected or created
- [x] Task 020: PostgreSQL Backtest Runner approved for implementation
- [x] Task 020: PostgreSQL Backtest Runner complete and verified
- [x] Task 021: Graph-Ready Backtest Persistence Schema task document created
- [x] Task 022: PostgreSQL Backtest Result Persistence task document created
- [x] Task 023: Backtest Result Read Model for Graphs task document created
- [x] Task 021: Graph-Ready Backtest Persistence Schema accepted
- [x] Task 022: PostgreSQL Backtest Result Persistence complete and verified
- [x] Task 023: Backtest Result Read Model for Graphs approved for implementation by owner prompt on 2026-05-16
- [x] Task 023: Backtest Result Read Model for Graphs complete and verified
- [x] Task 024: Database Schema Command Management task document created
- [x] Task 024: Database Schema Command Management approved for implementation by owner prompt on 2026-05-16
- [x] Task 024: Database Schema Command Management complete and verified
- [x] Task 025: WebSocket Unbounded Ingestion Service task document created
- [x] Task 025: WebSocket Unbounded Ingestion Service approved for implementation by owner prompt on 2026-05-16
- [x] Task 025: WebSocket Unbounded Ingestion Service complete and verified
- [x] Task 025: Indicator Document Intake Process task document created
- [x] First owner-provided indicator document saved under `tasks/indicators/`
- [x] Task 027: Bid-Ask Spread implementation task document created
- [x] Task 028: Pivot High / Pivot Low implementation task document created
- [x] Task 029: Swing Structure implementation task document created
- [x] Task 029: Swing Structure complete and verified
- [x] Task 030: ATR implementation task document created
- [x] Task 030: ATR complete and verified
- [x] Task 031: Volume Ratio implementation task document created
- [x] Task 031: Volume Ratio complete and verified
- [x] Task 032: Support / Resistance Zone implementation task document created
- [x] Task 032: Support / Resistance Zone complete and verified
- [x] Task 033: Displacement Candle implementation task document created
- [x] Task 033: Displacement Candle complete and verified
- [x] Task 034: Trendline Break Pattern task document created
- [x] Trendline Break Pattern mechanical definition drafted
- [x] Owner-provided Trendline Break Pattern source requirement saved under `tasks/patterns/trendline_break_pattern.md`
- [x] Task 035: Order Block Pattern task document created
- [x] Order Block Pattern mechanical definition drafted
- [x] Owner-provided Order Block Pattern source requirement saved under `tasks/patterns/order_block_pattern.md`
- [x] Task 036: Fair Value Gap Pattern task document created
- [x] Fair Value Gap Pattern mechanical definition updated from owner-provided final document
- [x] Owner-provided Fair Value Gap Pattern source requirement saved under `tasks/patterns/fair_value_gap_pattern.md`
- [x] Task 037: Cup and Handle Pattern task document created
- [x] Cup and Handle Pattern mechanical definition updated from owner-provided final document
- [x] Owner-provided Cup and Handle Pattern source requirement saved under `tasks/patterns/cup_and_handle_pattern.md`
- [x] Task 038: Diamond Pattern task document created
- [x] Diamond Pattern mechanical definition updated from owner-provided final document
- [x] Owner-provided Diamond Pattern source requirement saved under `tasks/patterns/diamond_pattern.md`
- [x] Task 038: Diamond Pattern mechanical definition review completed
- [x] Task 039: Adam and Eve Pattern task document created
- [x] Adam and Eve Pattern mechanical definition updated from owner-provided final document
- [x] Owner-provided Adam and Eve Pattern source requirement saved under `tasks/patterns/adam_and_eve_pattern.md`
- [x] Task 040: Pattern Detection Engine implementation task document created
- [x] Task 040: Pattern Detection Engine first Fair Value Gap implementation complete and verified
- [x] Task 041: Trendline Break Pattern Detection Engine implementation task document created
- [x] Task 041: Trendline Break Pattern Detection Engine implementation complete and verified
- [x] Task 042: Order Block Pattern Detection Engine implementation task document created
- [x] Task 042: Order Block Pattern Detection Engine implementation complete and verified
- [x] Task 043: Cup and Handle Pattern Detection Engine implementation task document created
- [x] Task 043: Cup and Handle Pattern Detection Engine implementation complete and verified
- [x] Task 044: Diamond Pattern Detection Engine implementation task document created
- [x] Task 044: Diamond Pattern Detection Engine implementation complete and verified
- [x] Task 045: Adam and Eve Pattern Detection Engine implementation task document created
- [x] Task 045: Adam and Eve Pattern Detection Engine implementation complete and verified
- [x] Task 046: Indicator And Pattern Review Documents task document created
- [x] Task 046: Indicator And Pattern Review Documents documentation complete and verified
- [x] Owner-provided Pattern Risk / Exit Management source requirement saved under `tasks/patterns/risk_exit_management.md`
- [x] Task 047: Pattern Risk / Exit Plan Contract task document created
- [x] Task 047: Pattern Risk / Exit Plan Contract implementation complete and verified
- [x] Task 048: Trendline Break Risk / Exit Plan task document created
- [x] Task 048: Trendline Break Risk / Exit Plan implementation complete and verified
- [x] Task 049: Order Block Risk / Exit Plan task document created
- [x] Task 049: Order Block Risk / Exit Plan implementation complete and verified
- [x] Task 050: Fair Value Gap Risk / Exit Plan task document created
- [x] Task 050: Fair Value Gap Risk / Exit Plan implementation complete and verified
- [x] Task 051: Cup And Handle Risk / Exit Plan task document created
- [x] Task 051: Cup And Handle Risk / Exit Plan implementation complete and verified
- [x] Task 052: Diamond Risk / Exit Plan task document created
- [x] Task 052: Diamond Risk / Exit Plan implementation complete and verified
- [x] Task 053: Adam And Eve Risk / Exit Plan task document created
- [x] Task 053: Adam And Eve Risk / Exit Plan implementation complete and verified
- [x] Task 054: Pattern Exit Simulation Integration task document created
- [x] Task 054: Pattern Exit Simulation Integration implementation complete and verified
- [x] Task 055: Pattern Strategy Backtest task document created
- [x] Task 055: Pattern Strategy Backtest approved for implementation by owner prompt on 2026-05-18
- [x] Task 055: Pattern Strategy Backtest implementation complete and verified
- [x] Task 056: Pattern PostgreSQL Backtest CLI task document created
- [x] Task 056: Pattern PostgreSQL Backtest CLI approved for implementation by owner prompt on 2026-05-18
- [x] Task 056: Pattern PostgreSQL Backtest CLI implementation complete and verified
- [x] Task 057: Pattern Backtest CLI clarity and pattern selection task document created
- [x] Task 057: Pattern Backtest CLI clarity and pattern selection implementation complete and verified
- [x] Task 058: Pattern Backtest All Implemented Pattern Selection task document created
- [x] Task 058: Pattern Backtest All Implemented Pattern Selection implementation complete and verified
- [x] Task 059: Error Logging task document created
- [x] Task 059: Runtime error logging implementation complete and verified
- [x] Task 060: Backtest Result Full Persistence task document created

# Open Questions

- Has the project owner explicitly approved live trading and real order execution?
- What credential policy should be used for API keys and secrets?
- Should future live trading use Binance testnet/sandbox first?
- What real-order endpoints, if any, are allowed?
- What kill-switch or disable mechanism is required?
- Task 024 decided the concrete PostgreSQL command-management path: `db/init/001_schema.sql` is the source-of-truth first-start schema DDL, `db/changes/` is reserved for future existing-database state-change SQL, repository initialization executes managed command files, and runtime persistence DML remains application-owned.
- Task 025 defines the indicator document intake process. Future owner-provided indicator documents should be saved under `tasks/indicators/<INDICATOR_KEY>.md`, and concrete indicator code must wait for an explicit indicator-specific implementation task. Pattern definition documents may be saved under `tasks/patterns/` when explicitly assigned by the owner.
- Tasks 027-033 define planned implementation tasks for the remaining indicator/filter modules. Task 028 Pivot High / Pivot Low, Task 029 Swing Structure, Task 030 ATR, Task 031 Volume Ratio, Task 032 Support / Resistance Zone, and Task 033 Displacement Candle have deterministic implementations pending review. Task 034 has been restored as the Trendline Break Pattern mechanical-definition task, Task 035 has been restored as the Order Block Pattern mechanical-definition task, Task 036 has been restored as the Fair Value Gap Pattern mechanical-definition task, Task 037 has been created as the Cup and Handle Pattern mechanical-definition task, Task 038 has been created as the Diamond Pattern mechanical-definition task and reviewed by the owner, and Task 039 has been created as the Adam and Eve Pattern mechanical-definition task and updated from the owner-provided final document. The Trendline Break, Order Block, Fair Value Gap, Cup and Handle, Diamond, and Adam and Eve patterns are documented as mechanical definitions. Task 040 implemented the first pattern detection engine batch focused on Fair Value Gap detection. Task 041 implemented the next pattern detection engine batch focused on Trendline Break detection. Task 042 implemented the next pattern detection engine batch focused on Order Block detection. Task 043 implemented the next pattern detection engine batch focused on Cup and Handle detection. Task 044 implemented the next pattern detection engine batch focused on Diamond Pattern detection. Task 045 implemented the next pattern detection engine batch focused on Adam and Eve Pattern detection. Task 046 completed the documentation-only review assignment for current indicator structure, pattern algorithms, and indicator/pattern class usage. Task 047 now defines the required first implementation step for a shared pattern risk/exit contract. Tasks 048-053 define dependent pattern-specific stop-loss/take-profit planner tasks for Trendline Break, Order Block, Fair Value Gap, Cup and Handle, Diamond, and Adam and Eve. Task 054 completed exit-simulation integration. Task 055 completed the first pattern strategy backtest integration for Fair Value Gap entries, valid FVG risk/exit plans, duplicate event prevention, and Task 054 exit simulation. Task 056 implemented a `quant-bitcoin-pattern-backtest` CLI that loads PostgreSQL-backed `1m` candles through the existing provider and reuses the Task 055 pattern strategy backtest without adding live trading, order execution, scheduler, dashboard, or schema-redesign behavior. Task 057 clarified the CLI as the default Fair Value Gap pattern strategy backtest, changed default JSON strategy metadata to `FAIR_VALUE_GAP_PATTERN_STRATEGY`, documented safe README usage, and added the first tested FVG-only `--pattern FAIR_VALUE_GAP` selection seam while rejecting unsupported patterns before execution. Task 058 expanded that seam to every safely wireable already-implemented detector plus risk/exit planner pair while keeping `FAIR_VALUE_GAP` as the default, rejecting unsupported or multiple selections before execution, preserving deterministic JSON metadata, and preserving safety boundaries. Task 059 completed runtime exception logging for supported CLI entrypoints. Task 060 now defines the next scoped work item: full persistence of backtest results across supported backtest execution paths, pending explicit implementation approval. Current pattern strategy assumptions are: Fair Value Gap remains the default selection, one explicit supported pattern is selected per run, one simulated open position is open at a time, entry occurs on the pattern confirmation candle, exit evaluation starts on the next completed candle, and same-candle eligible events are ordered by pattern type, direction, then event id. Liquidity and bid-ask spread filters remain unavailable as reusable modules, so future pattern detectors and risk/exit planners must handle those filters explicitly rather than silently approximating them.
- Docker is not installed in the current cloud environment. Local PostgreSQL and WebSocket ingestor container startup are intentionally skipped here and remain optional local developer verification.

# Blockers

- Live trading implementation is blocked until explicit human approval, credential policy, sandbox/testnet policy, real-order endpoint allowlist, kill-switch design, and safety tests are documented.

# Rules for Next Codex Task

- Read `AGENTS.md` before working.
- Read this `STATUS.md` before starting implementation tasks.
- Use `docs/10_CODEX_COMMAND_GUIDE.md` for consistent command handling and reusable prompt formats.
- Read the assigned task file before coding.
- Do not implement application code unless the assigned task explicitly requires it.
- Do not create trading logic unless the assigned task explicitly requires it.
- Do not mark a phase or step complete unless acceptance criteria and verification are satisfied.
- Update this file when the project phase, step, goal, active task, blocker, open question, or completion state changes.

# Status Update Rule

Codex must update `STATUS.md` whenever project state changes. If state is uncertain, Codex must leave the item open and record the uncertainty under Open Questions or Blockers.
