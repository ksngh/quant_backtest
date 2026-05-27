# quant_bitcoin

`quant_bitcoin` is a small Python project for Bitcoin quantitative-trading experiments. The current implementation focuses on offline and paper-only workflows: candle data loading, standard candle normalization, RSI and chart-pattern research strategies, historical backtesting, saved-run diagnostics/reporting, paper trade recording, Binance public historical candle downloading, and basic paper risk checks.

> **Safety status:** live trading and real Binance order execution are intentionally blocked. Pattern research outputs are backtest/paper-only. This project does not place real orders, does not sign exchange requests, and does not store or load API keys.

## Current scope

Implemented components:

- **Market data contract** using the standard candle fields `timestamp`, `open`, `high`, `low`, `close`, and `volume`.
- **CSV candle provider** for loading local CSV files into the standard candle schema.
- **Binance candle downloader** for public historical spot klines only; it normalizes responses to the standard candle schema and rejects order endpoints.
- **RSI strategy** that returns `BUY`, `SELL`, or `HOLD` signals from standard candle data.
- **Pattern research strategies** for supported chart-pattern experiments with explicit entry, risk, cost, no-lookahead, score, and diagnostics metadata.
- **FVG retest v2 research diagnostics** for saved-run inspection of multi-timeframe trend score, Fibonacci confluence, reaction-entry quality, liquidity-target metadata, and stop-mode selection. These are offline OHLCV-derived backtest diagnostics only.
- **FVG retest v2 WFO/OOS research protocol** for predeclared parameter ranges, realistic-cost validation, all-variant reporting, and research-only promotion/rejection notes.
- **Basic backtester** for a simple long-only, fixed-quantity historical simulation.
- **Canonical strategy-engine backtester** for strategy actions, long/short simulation, transaction costs, explicit position sizing, account-state metadata, and persisted graph-ready outputs.
- **Paper trader** for in-memory fake trade recording and paper cash/position updates.
- **Paper risk checker** for deterministic cash and position checks before paper trades.
- **PostgreSQL candle persistence** for Binance spot candle storage, restartable historical backfill, and public WebSocket closed-candle ingestion.
- **Read-only dashboard API/frontend** for inspecting saved simulated backtest results, diagnostics, assumptions, and research reports.

Out of scope unless a future approved task explicitly asks for it:

- Live trading or real order execution.
- API keys, signed requests, or tracked `.env` files.
- Real futures/margin trading, real leverage, portfolio optimization, schedulers, Streamlit, and machine learning.
- New dashboard/API behavior beyond the existing read-only saved-result viewer.
- Additional databases or Dockerized application services beyond the Task 014 local PostgreSQL developer service.

## Project layout

```text
quant_bitcoin/
  backtesting/        Basic backtest engine and result models.
  execution/          Paper-only execution simulation.
  indicators/         Offline technical-indicator helpers.
  market_data/        CSV provider, Binance public downloader, backfill, and WebSocket ingestion.
  patterns/           Offline chart-pattern detection and risk/exit planning.
  persistence/        PostgreSQL candle repository and ingestion checkpoint storage.
  risk/               Paper-only risk checks.
  strategies/         RSI and pattern strategy/action contracts.
docs/                 Architecture, data contract, workflow, and decision docs.
tasks/                Task definitions and completion criteria.
tests/                Unit, contract, and safety tests.
```

## Requirements

- Python 3.10 or newer.
- `pandas` for data handling.
- `psycopg` for PostgreSQL persistence.
- `websockets` for optional live public WebSocket connections.
- `pytest` for tests.

The package metadata is defined in `pyproject.toml`.

## Installation

From the repository root, create and activate a virtual environment, then install the project with test dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

## Local PostgreSQL for candle persistence

Task 014 adds local PostgreSQL support for persistence. The Docker Compose
service uses non-secret development defaults and loads the accepted schema from
the managed SQL command files in `db/init/`; the current source-of-truth schema
file is `db/init/001_schema.sql`. Do not commit `.env` files; override
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `POSTGRES_PORT` in your
shell when needed. Database command ownership, future existing-database change
files, and the runtime DML boundary are documented in
`docs/11_DATABASE_COMMAND_MANAGEMENT.md`.

Start local PostgreSQL from the repository root:

```bash
docker compose up -d postgres
```

For one-command dashboard local startup (PostgreSQL + backend API + frontend UI):

```bash
docker compose up --build
```

Then open:

- Frontend UI: `http://localhost:3000`
- Backend API health: `http://localhost:8000/api/health`

Notes:

- The frontend container uses `NEXT_PUBLIC_BACKTEST_API_BASE_URL=http://backend:8000` by default for in-network service discovery.
- The optional WebSocket ingestor is excluded by default and can be started only when needed with `--profile ingestion`.

The matching development database URL is:

```text
postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin
```

Optional PostgreSQL integration tests use `QUANT_BITCOIN_TEST_DATABASE_URL`. The
ordinary unit test suite does not require Docker, a running PostgreSQL server, or
real Binance availability; network calls are mocked in ordinary tests.

Docker Compose is optional local developer verification only. If Docker is not
available in an environment, skip runtime startup there; it can be verified later
in a Docker-capable local environment.

### Backfill public Binance 1-minute candles

The recommended local path is to run the packaged CLI from the repository root
after installing the project and starting local PostgreSQL:

```bash
python -m pip install -e '.[test]'
docker compose up -d postgres
quant-bitcoin-binance-backfill
```

With the default Docker Compose database, the CLI connects to:

```text
postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin
```

The default command initializes the PostgreSQL schema if needed, backfills
`BTCUSDT` `1m` candles from the latest stored candle or Binance's earliest
available candle, persists only closed candles, and prints a JSON summary such as
`stored_candles` and `pages_fetched`. Re-running the command is safe because the
repository writes candles by the duplicate-safe
`source + symbol + interval + open_time` uniqueness rule.

Common bounded examples:

```bash
# Backfill a specific UTC date range.
quant-bitcoin-binance-backfill \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z

# Use an explicit database URL and skip schema initialization if already managed.
quant-bitcoin-binance-backfill \
  --database-url postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin \
  --no-initialize-schema
```

Useful CLI options and matching environment variables:

| Option | Environment variable | Default |
| --- | --- | --- |
| `--database-url` | `DATABASE_URL` | Local Docker Compose PostgreSQL URL. |
| `--symbol` | `SYMBOL` | `BTCUSDT` |
| `--interval` | `INTERVAL` | `1m` |
| `--start-time` | `BACKFILL_START_TIME` | Resume after latest stored candle, or start from earliest available candle. |
| `--end-time` | `BACKFILL_END_TIME` | Latest closed candle at runtime. |
| `--limit` | `BACKFILL_LIMIT` | `1000` |
| `--base-url` | `BINANCE_MARKET_DATA_BASE_URL` | Binance public market-data REST base URL. |
| `--timeout-seconds` | `BACKFILL_TIMEOUT_SECONDS` | `10.0` |
| `--max-retries` | `BACKFILL_MAX_RETRIES` | `3` |

`--start-time` and `--end-time` accept UTC ISO-8601 values such as
`2024-01-01T00:00:00Z` or millisecond timestamps. Do not commit `.env` files;
set overrides in your shell or local process manager instead. The backfill uses
Binance public spot kline data only and does not require API keys, signed
requests, or order endpoints.

The same behavior can be invoked from Python when embedding the workflow:

```python
from quant_bitcoin.market_data import BinanceHistoricalBackfiller
from quant_bitcoin.persistence import PostgresCandleRepository

repository = PostgresCandleRepository(
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
repository.initialize_schema()

result = BinanceHistoricalBackfiller(repository).run(symbol="BTCUSDT", interval="1m")
print(result.stored_candles)
```

## Run an RSI backtest from PostgreSQL candles

After PostgreSQL already contains closed candles, run the short packaged
backtest command from the repository root:

```bash
quant-bitcoin-strategy-backtest
```

`quant-bitcoin-postgres-backtest` remains available as a compatibility alias;
prefer `quant-bitcoin-strategy-backtest` for new scripts and automation.

The command reads candles through `PostgresCandleDataProvider`, runs the
existing `RsiStrategy` through the canonical strategy-engine backtest path,
saves the completed simulated backtest result to PostgreSQL, and prints
deterministic JSON containing the input stream, strategy parameters, summary,
simulated trades, and saved `backtest_run_id`. It does not call Binance, place real orders, use API keys,
or call exchange account endpoints.

Saved runs use the graph-ready Task 021 schema in `strategy_configs`,
`backtest_runs`, `backtest_results`, `backtest_trades`, and
`backtest_graph_points`. The write is transactional for each run: strategy
metadata, run metadata, summary metrics, deterministic trade rows, and ordered
graph points are committed together or rolled back together. Re-running the same
deterministic backtest replaces the prior saved rows for the same `run_key`.
Use `--no-persist` only when you want to inspect stdout JSON without saving
simulated result rows.

Canonical strategy runs also emit and persist `reproducibility` metadata. This
includes dataset identity, requested and actual candle ranges, candle count,
candle quality summary, candle-content hash, strategy/config hashes, engine
version, sizing/cost assumptions, and explicit `null` seed slots for validation
workflows that do not provide a seed. Volatile runtime timings stay outside the
deterministic `run_key`, and database URLs or other sensitive values are redacted
before they can appear in JSON output or persisted run metadata.

If PostgreSQL is empty, populate it first with the accepted Task 014 backfill
workflow:

```bash
docker compose up -d postgres
quant-bitcoin-binance-backfill \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z
quant-bitcoin-strategy-backtest \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z
```

Common backtest options and matching environment variables:

| Option | Environment variable | Default |
| --- | --- | --- |
| `--database-url` | `DATABASE_URL` | Local Docker Compose PostgreSQL URL. |
| `--source` | `CANDLE_SOURCE` | `binance_spot` |
| `--symbol` | `SYMBOL` | `BTCUSDT` |
| `--interval` | `INTERVAL` | `1m` |
| `--start-time` | `BACKTEST_START_TIME` | No lower bound. |
| `--end-time` | `BACKTEST_END_TIME` | No upper bound. |
| `--starting-cash` | `BACKTEST_STARTING_CASH` | `10000.0` |
| `--trade-quantity` | `BACKTEST_TRADE_QUANTITY` | `1.0` |
| `--position-sizing-mode` | None | `fixed_quantity` |
| `--position-sizing-value` | None | unset |
| `--insufficient-funds-policy` | None | `resize` |
| `--short-exposure-mode` | None | `cash_bounded` |
| `--simulated-margin-leverage` | None | unset |
| `--insufficient-margin-policy` | None | `block` |
| `--rsi-window` | `BACKTEST_RSI_WINDOW` | `14` |
| `--rsi-buy-threshold` | `BACKTEST_RSI_BUY_THRESHOLD` | `30.0` |
| `--rsi-sell-threshold` | `BACKTEST_RSI_SELL_THRESHOLD` | `70.0` |
| `--no-persist` | None | Persist simulated results by default. |

`--start-time` and `--end-time` accept UTC ISO-8601 values such as
`2024-01-01T00:00:00Z`. Do not commit `.env` files; set overrides in your shell
or local process manager instead.


## Run a pattern backtest from PostgreSQL candles

`quant-bitcoin-pattern-backtest` is a compatibility alias that routes to the
canonical strategy-engine CLI path. Prefer `quant-bitcoin-strategy-backtest`
for new automation and scripts.

After PostgreSQL already contains stored closed `BTCUSDT` `1m` candles, run
the default Fair Value Gap pattern strategy backtest with an explicit safe UTC
time window:

```bash
quant-bitcoin-strategy-backtest \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z
```

The default pattern selection remains `FAIR_VALUE_GAP`; use `--pattern FAIR_VALUE_GAP`
when you want to spell out the default explicitly. You can also select one
supported implemented detector/risk-exit pair, for example an Order Block
historical simulation:

```bash
quant-bitcoin-strategy-backtest \
  --pattern ORDER_BLOCK \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z
```

Supported `--pattern` values are: `FAIR_VALUE_GAP`, `TRENDLINE_BREAK`,
`ORDER_BLOCK`, `CUP_AND_HANDLE`, `DIAMOND`, and `ADAM_AND_EVE`. The command
supports one selected pattern per run; multiple `--pattern` values and
unsupported pattern names fail before the provider or backtest runner is
invoked. Output is deterministic JSON with strategy metadata such as
`FAIR_VALUE_GAP_PATTERN_STRATEGY`, `ORDER_BLOCK_PATTERN_STRATEGY`, and the
selected pattern list.

FVG entry-mode experiments are explicit CLI options. The default remains
`market_on_confirmation_close`, which models momentum continuation after the
confirmation candle. Retest modes such as `limit_at_entry_reference`,
`limit_at_pattern_midpoint`, and `limit_at_pattern_boundary` model imbalance
rebalancing entries and can miss trades when price does not revisit the selected
level. Use `--fvg-entry-max-wait-bars` and `--fvg-entry-expire-status` to bound
limit-entry waiting, and `--compare-fvg-entry-modes` to include a read-only JSON
comparison of fill rate, trade count, hit rate, average R, expectancy,
MFE/MAE, average bars waited, and missed-trade count. These options are
backtest research controls only and do not place orders.

FVG retest v2 diagnostics are also opt-in: `--enable-fvg-v2` records the
experimental scope, `--fvg-entry-trigger` selects touch or reaction-trigger
retest behavior, and companion flags record trend-score, Fibonacci confluence,
liquidity-target, and stop-mode research settings in JSON diagnostics. Parameter
grid runs can enumerate these settings; they do not pick winners automatically.
The multi-timeframe trend score uses completed higher-timeframe candles only,
and the Fibonacci/liquidity/stop-mode fields remain offline research metadata,
not live trading approval.

FVG retest v2 WFO/OOS evaluation is governed by
`docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md`. The protocol requires
predeclared parameter ranges, realistic-cost evidence, all-variant reporting,
and locked holdout discipline before any future paper-only decision task.

Canonical strategy runs also expose opt-in workflow controls:
`--enforce-candle-continuity` rejects interval gaps during candle loading,
`--enable-market-regime` tags executions for regime attribution, and
`--max-account-drawdown`, `--max-consecutive-losses`, and `--max-daily-loss`
enable deterministic backtest-only entry guardrails. These settings are recorded
in strategy parameters and summary metadata. They are not live risk controls.

Transaction-cost profiles can be selected with `--cost-profile`. Supported
static presets are `zero`, `binance_spot_taker_baseline`,
`conservative_crypto_1m`, and `high_slippage_stress`. Manual bps flags still
work when no profile is selected; combining a profile with manual bps requires
`--allow-cost-profile-overrides`. Profiles are offline assumptions only and do
not query exchange fee tiers or account endpoints. Use `--strict-cost-mode` to
block zero-cost 1m pattern runs, and `--cost-sensitivity-report` to include a
deterministic zero/baseline/conservative/stress cost comparison.

This is a historical simulation over stored standard candles only. It does not
place orders, does not call exchange order or account endpoints, does not sign
requests, and does not require API keys or `.env` files.

### Strategy-engine sizing, cash, and short simulation

The canonical strategy engine supports three backtest-only sizing modes:

- `fixed_quantity`: use an action quantity when present, otherwise use
  `--trade-quantity`.
- `cash_fraction`: size entries from a fraction of available cash.
- `target_notional`: size entries from a quote-currency notional target.

Action-level quantities take precedence over engine-level sizing. When a long
entry or default cash-bounded short entry asks for more exposure than the
starting cash can support, the default behavior is to resize the fill; set
`--insufficient-funds-policy block` to block instead. This prevents a
`10_000` cash run from silently opening a full `1 BTC` exposure at an
`80_000` BTC price.

Short simulation is not spot execution. The default `cash_bounded` mode limits
short exposure by cash/buying power and must not be read as a real spot short
order capability. Explicit `simulated_margin` mode is backtest-only and
requires `--simulated-margin-leverage`; it checks initial margin as
`notional / leverage`.

By default, borrow fees, futures funding, maintenance margin, and liquidation
remain unmodeled and JSON output records that under `short_economics`, adding a
`short_economics_simulation_only` warning when short results are present. For
research runs, `ShortEconomicsConfig(enabled=True, ...)` can add deterministic
borrow/funding carrying-cost deductions and diagnostic-only maintenance /
liquidation flags. These diagnostics do not auto-close positions, submit
exchange orders, or imply real margin/futures account support.

Result fields distinguish cash balance from free cash:

- `cash_after` / `ending_cash` are cash-balance fields and can include
  short-sale proceeds.
- `free_cash_after`, `margin_used_after`, and
  `short_proceeds_locked_after` are additive metadata for spendable cash and
  simulated short state.
- `equity_after` / `final_equity` are the net account value fields when a
  position is open.

## Read saved backtest results for graph inputs

Future graphing workflows should read persisted simulated output through the
read-only `PostgresBacktestResultRepository` methods instead of re-running a
strategy, a backtest engine, or market-data providers. Load one saved completed
run by id with `load_run_for_graphs(backtest_run_id)`. The method returns
`None` when no completed persisted run with that id and summary row exists; it
does not synthesize missing data.

The returned `BacktestRunReadModel` has this shape:

- `run`: run metadata such as id, deterministic `run_key`, engine name/version,
  candle source, symbol, interval, requested and actual candle time ranges,
  candle count, starting cash, trade quantity, status, metadata, and creation /
  completion timestamps.
- `strategy_config`: saved strategy key, name, version, canonical parameters,
  parameter hash, and optional metadata.
- `summary`: persisted summary metrics including starting cash, ending cash,
  ending position, final price, final equity, total return, trade count, buy
  count, sell count, metadata, account-state semantics, and creation
  timestamp.
- `trades`: simulated trade rows ordered by `sequence ASC` for deterministic
  marker overlays. Each row includes candle timestamp, signal, price, quantity,
  cash after, position after, and optional metadata. New strategy-engine runs
  include additive free-cash, margin-used, locked-short-proceeds, and
  cash-semantics metadata.
- `graph_points`: dense graph-ready rows ordered by `candle_open_time ASC,
  sequence ASC`. Each point includes close price, cash, position, equity, and
  nullable trade marker fields (`trade_id` and `signal`). New strategy-engine
  runs include additive account-state metadata for display.

Use `list_completed_runs(...)` to select recent graph inputs. It returns
newest completed runs first and includes the associated strategy config id, key,
name, version, canonical parameters, and parameter hash so future strategy
variants can be distinguished before loading the full run. It can filter by
source, symbol, interval, and actual persisted candle time range. These read
methods are intentionally read-only: they issue SELECT queries against saved
Task 021/022 tables and do
not call Binance, exchange account APIs, order endpoints, `RsiStrategy`, or
`BasicBacktester`.

Saved-run detail responses may also include read-only research metadata for the
dashboard: performance diagnostics, timing diagnostics, risk/exit audit, score
calibration, tradability proxy attribution, and a compact
`backtest_research_report_v1` JSON/markdown note. These artifacts summarize
already persisted rows only. They do not rerun strategies, mutate parameters,
place orders, call account endpoints, or expose API keys/database credentials.

### Ingest public Binance WebSocket closed candles

```python
import asyncio

from quant_bitcoin.market_data import BinanceWebSocketCandleIngestor
from quant_bitcoin.persistence import PostgresCandleRepository

repository = PostgresCandleRepository(
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
repository.initialize_schema()

asyncio.run(
    BinanceWebSocketCandleIngestor(repository).run(symbol="BTCUSDT", interval="1m")
)
```

The WebSocket ingestor subscribes to Binance public spot kline streams, persists
only closed `BTCUSDT` `1m` candles, and relies on the PostgreSQL duplicate-safe
`source + symbol + interval + open_time` uniqueness rule. It does not perform
historical REST gap fill on startup; run the Task 014 backfill first whenever
historical completeness after downtime is required. Ordinary tests mock the
WebSocket connector and do not require real Binance availability.

The ingestion CLI defaults to unbounded long-running mode. Leave
`INGEST_MAX_MESSAGES` unset, empty, `0`, `none`, `null`, or `unbounded` to
keep running until the process is stopped or reconnects fail. Use `--max-messages <positive
integer>` or a positive `INGEST_MAX_MESSAGES` value for bounded smoke checks.
Use `--no-max-messages` to force unbounded mode even when `INGEST_MAX_MESSAGES`
is set in the environment.

## Running tests

```bash
pytest
```

The test suite is expected to run without real API keys and without calling real exchange order endpoints.

## Standard candle schema

All strategy and backtest code expects standard candle data with these columns:

| Column | Meaning |
| --- | --- |
| `timestamp` | Candle open time. |
| `open` | First traded price in the candle interval. |
| `high` | Highest traded price in the candle interval. |
| `low` | Lowest traded price in the candle interval. |
| `close` | Last traded price in the candle interval. |
| `volume` | Traded volume in the candle interval. |

Rows must be sorted by `timestamp` ascending. Price and volume fields must be numeric.

## Usage examples

### Load candles from CSV

```python
from quant_bitcoin.market_data import CsvCandleDataProvider

provider = CsvCandleDataProvider("data/btcusdt_1m.csv")
candles = provider.load()
```

The CSV provider normalizes column names and returns only the standard candle fields.

### Load candles from PostgreSQL for backtesting

After PostgreSQL has been populated by the Binance backfill or WebSocket
ingestion workflow, use `PostgresCandleDataProvider` to read stored `candles`
rows into the same standard candle schema used by CSV-backed backtests:

```python
from datetime import datetime, timezone

from quant_bitcoin.backtesting.basic import BasicBacktester
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.persistence import PostgresCandleRepository
from quant_bitcoin.strategies import RsiStrategy

repository = PostgresCandleRepository(
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
provider = PostgresCandleDataProvider(
    repository,
    symbol="BTCUSDT",
    interval="1m",
    start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
    end_time=datetime(2024, 1, 2, tzinfo=timezone.utc),
)
candles = provider.load()

strategy = RsiStrategy(window=14)
result = BasicBacktester(starting_cash=10_000, trade_quantity=0.01).run(
    candles, strategy
)
print(result.summary)
```

The PostgreSQL provider maps `candles.open_time` to `timestamp`, returns only
`timestamp`, `open`, `high`, `low`, `close`, and `volume`, and sorts rows by
`timestamp` ascending before backtesting.

### Generate an RSI signal

```python
from quant_bitcoin.strategies import RsiSignalMode, RsiSmoothingMethod, RsiStrategy

strategy = RsiStrategy(window=14, buy_threshold=30.0, sell_threshold=70.0)
signal = strategy.generate_signal(candles)

crossing_strategy = RsiStrategy(
    window=14,
    buy_threshold=30.0,
    sell_threshold=70.0,
    smoothing_method=RsiSmoothingMethod.WILDER,
    signal_mode=RsiSignalMode.CROSSING,
)
```

The default RSI contract remains the original simple rolling RSI with latest-level
thresholds: RSI at or below the buy threshold returns `BUY`, RSI at or above the
sell threshold returns `SELL`, and repeated level signals are expected until a
caller or backtest engine de-duplicates by position state. `RsiSignalMode.CROSSING`
is opt-in and emits only when RSI newly crosses a threshold, which helps avoid
repeated oversold/overbought setup artifacts for callers that do not hold
position state. `RsiSmoothingMethod.WILDER` is also opt-in; the default remains
the simple rolling method for backward compatibility.

RSI is a mean-reversion indicator, not a validated standalone alpha model. It
does not include trend/regime filters by default and should be evaluated with
out-of-sample validation before being treated as economically meaningful. The
RSI strategy consumes standard candle data only. It does not fetch data, decide
quantity, or place orders.

### Run a basic backtest

```python
from quant_bitcoin.backtesting.basic import BasicBacktester
from quant_bitcoin.strategies import RsiStrategy

strategy = RsiStrategy(window=14, buy_threshold=30.0, sell_threshold=70.0)
backtester = BasicBacktester(starting_cash=10_000.0, trade_quantity=0.01)
result = backtester.run(candles, strategy)

print(result.summary.final_equity)
print(result.summary.total_return)
```

The basic backtester is intentionally small: it runs a long-only, fixed-quantity simulation and does not model fees, slippage, optimization, or live execution.

### Record paper trades

```python
from quant_bitcoin.execution import PaperTrader
from quant_bitcoin.strategies import Signal

trader = PaperTrader(cash_balance=1_000.0)
trade = trader.apply_signal(
    symbol="BTCUSDT",
    signal=Signal.BUY,
    quantity=0.01,
    price=50_000.0,
)
```

`PaperTrader` records fake trades and updates local paper state only. It never calls exchange APIs.

### Check paper risk before a paper trade

```python
from quant_bitcoin.risk import PaperRiskChecker
from quant_bitcoin.strategies import Signal

checker = PaperRiskChecker()
decision = checker.check(
    symbol="BTCUSDT",
    signal=Signal.BUY,
    quantity=0.01,
    price=50_000.0,
    cash_balance=1_000.0,
    current_position=0.0,
)

if decision.approved:
    print("paper trade approved")
else:
    print(decision.reason)
```

The risk checker is paper-only and deterministic. It does not mutate state or call exchanges.

### Download public Binance historical candles

```python
from quant_bitcoin.market_data import BinanceCandleDownloader

downloader = BinanceCandleDownloader()
candles = downloader.fetch_historical_candles(
    symbol="BTCUSDT",
    interval="1m",
    limit=100,
)
```

The downloader uses Binance public kline data only and returns the standard candle schema. It must not be used for order execution.

## Safety rules

This repository is designed to keep strategy research and paper workflows separate from live execution.

- Strategy code returns signals only; it must not place orders.
- Market-data code may fetch or load candles; it must not execute trades.
- Backtests simulate historical execution only; they must not call live exchange order APIs.
- Paper trading records fake trades only; it must not call real exchange order APIs.
- Binance downloading, backfill, and WebSocket ingestion are limited to public candle data.
- Live trading remains blocked until a future human-approved task documents credential handling, sandbox/testnet policy, endpoint allowlist, kill switch behavior, and safety tests.
- `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md` records the current execution-readiness gaps and the checklist required before Task 138 can be unblocked.

## Documentation

Important project documents:

- `AGENTS.md` — working rules and project safety constraints.
- `STATUS.md` — current phase, blockers, and next-step ledger.
- `docs/04_DATA_CONTRACT.md` — standard candle data contract.
- `docs/03_ARCHITECTURE_RULES.md` — role ownership and architecture boundaries.
- `docs/09_DECISIONS.md` — accepted architecture decisions.
- `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md` — live-execution readiness audit and blockers.
- `tasks/012_LIVE_TRADING_IMPLEMENTATION_BLOCKER.md` — current live-trading blocker.

## Development notes

Before adding implementation changes:

1. Read `AGENTS.md` and `STATUS.md`.
2. Read the relevant task document under `tasks/`.
3. Keep changes small and within the assigned role boundary.
4. Add or update tests for implementation behavior.
5. Run `pytest` when possible.
6. Perform the Codex self-review checklist in `reviews/CODEX_SELF_REVIEW.md`.
