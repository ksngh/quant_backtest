from __future__ import annotations

from datetime import datetime, timezone

from quant_bitcoin.execution import PaperExecutionClient, RealtimeCandleCloseRunner
from quant_bitcoin.persistence import SOURCE_BINANCE_SPOT
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType

OPEN_TIME_MS = 1_704_067_200_000


class InMemoryRealtimeRepository:
    def __init__(self) -> None:
        self.rows = {}
        self.upsert_calls = 0
        self.load_calls = []

    def upsert_candles(self, candles):
        self.upsert_calls += 1
        for candle in candles:
            self.rows[(candle.source, candle.symbol, candle.interval, candle.open_time)] = candle
        return len(candles)

    def load_standard_candles(self, **kwargs):
        self.load_calls.append(kwargs)
        return [
            {
                "timestamp": candle.open_time,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            }
            for candle in sorted(self.rows.values(), key=lambda value: value.open_time)
        ]


def sample_message(*, closed: bool = True):
    return {
        "e": "kline",
        "E": OPEN_TIME_MS + 60_000,
        "s": "BTCUSDT",
        "k": {
            "t": OPEN_TIME_MS,
            "T": OPEN_TIME_MS + 59_999,
            "s": "BTCUSDT",
            "i": "1m",
            "o": "100.00",
            "c": "105.00",
            "h": "106.00",
            "l": "99.00",
            "v": "1.0",
            "n": 1,
            "x": closed,
            "q": "105.00",
            "V": "0.5",
            "Q": "52.5",
        },
    }


def test_runner_ignores_open_in_progress_candle_event() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)
    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=lambda candles: [],
        execution_client=client,
    )

    output = runner.process_kline_message(sample_message(closed=False))

    assert output.triggered is False
    assert repository.upsert_calls == 0
    assert client.reports == []


def test_closed_candle_triggers_strategy_once_and_uses_stored_candles() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)

    def strategy(candles):
        assert len(candles) == 1
        return [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=candles.iloc[-1]["timestamp"],
                quantity=1,
            )
        ]

    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=strategy,
        execution_client=client,
        dry_run=True,
    )

    output = runner.process_kline_message(sample_message())

    assert output.triggered is True
    assert output.candle_identity["source"] == SOURCE_BINANCE_SPOT
    assert output.candle_identity["open_time"] == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert len(output.actions) == 1
    assert output.order_intents[0].execution_side == "BUY"
    assert output.execution_reports[0].status == "DRY_RUN"
    assert repository.load_calls[0]["end_time"] == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_duplicate_closed_candle_does_not_create_duplicate_execution() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)
    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=lambda candles: [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[-1]["timestamp"], quantity=1)
        ],
        execution_client=client,
        dry_run=True,
    )

    first = runner.process_kline_message(sample_message())
    second = runner.process_kline_message(sample_message())

    assert first.triggered is True
    assert second.triggered is False
    assert len(first.execution_reports) == 1
    assert second.execution_reports == ()


def test_dry_run_mode_does_not_mutate_paper_balances() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)
    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=lambda candles: [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[-1]["timestamp"], quantity=1)
        ],
        execution_client=client,
        dry_run=True,
    )

    output = runner.process_kline_message(sample_message())

    assert output.execution_reports[0].status == "DRY_RUN"
    assert client.cash_balance == 1000
    assert client.positions == {}


def test_paper_mode_records_execution_report() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)
    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=lambda candles: [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[-1]["timestamp"], quantity=1)
        ],
        execution_client=client,
        dry_run=False,
    )

    output = runner.process_kline_message(sample_message())

    assert output.execution_reports[0].status == "FILLED"
    assert output.execution_quality[0].fill_vwap == 105
    assert output.execution_quality[0].reference_price == 105
    assert client.cash_balance == 895
    assert client.positions == {"BTCUSDT": 1.0}


def test_realtime_runner_paper_spot_mode_blocks_short_intent() -> None:
    repository = InMemoryRealtimeRepository()
    client = PaperExecutionClient(cash_balance=1000)
    runner = RealtimeCandleCloseRunner(
        repository=repository,
        strategy_key="TEST",
        strategy=lambda candles: [
            StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=candles.iloc[-1]["timestamp"], quantity=1)
        ],
        execution_client=client,
        dry_run=False,
    )

    output = runner.process_kline_message(sample_message())

    assert output.order_intents[0].execution_side == "SELL"
    assert output.execution_reports[0].status == "REJECTED"
    assert output.execution_reports[0].reason == "SHORT_NOT_SUPPORTED_FOR_SPOT"
    assert client.positions == {}
