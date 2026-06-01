from __future__ import annotations

import json

import pandas as pd

from quant_bitcoin.backtesting import strategy_postgres_runner_cli
from quant_bitcoin.backtesting.strategy_postgres_runner_core import (
    _build_actions,
    _build_lookback_return_momentum_config,
    build_parser,
)
from quant_bitcoin.strategies.actions import StrategyActionType


class _FakeProvider:
    def __init__(self, candles: pd.DataFrame) -> None:
        self._candles = candles

    def load(self) -> pd.DataFrame:
        return self._candles


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-20T00:00:00Z", periods=4, freq="min"),
            "open": [100.0, 101.0, 101.5, 102.0],
            "high": [100.0, 101.0, 101.5, 102.0],
            "low": [100.0, 101.0, 101.5, 102.0],
            "close": [100.0, 101.0, 101.5, 102.0],
            "volume": [1.0, 1.0, 1.0, 1.0],
        }
    )


def test_build_actions_selects_lookback_return_momentum_strategy() -> None:
    strategy, actions = _build_actions(
        _candles(),
        "LOOKBACK_RETURN_MOMENTUM",
        lookback_return_momentum_config=_build_lookback_return_momentum_config(
            build_parser("test").parse_args(
                [
                    "--strategy",
                    "LOOKBACK_RETURN_MOMENTUM",
                    "--lookback-bars",
                    "1",
                    "--entry-threshold",
                    "0.001",
                    "--holding-bars",
                    "2",
                    "--take-profit-r",
                    "100.0",
                    "--no-persist",
                ]
            )
        ),
    )

    assert strategy.strategy_key == "LOOKBACK_RETURN_MOMENTUM"
    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    assert any(action.action_type is StrategyActionType.EXIT_LONG for action in actions)


def test_cli_parameter_overrides_flow_to_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: _FakeProvider(_candles()),
    )

    assert strategy_postgres_runner_cli.main(
        [
            "--strategy",
            "LOOKBACK_RETURN_MOMENTUM",
            "--lookback-bars",
            "1",
            "--entry-threshold",
            "0.001",
            "--holding-bars",
            "2",
            "--risk-distance-pct",
            "0.002",
            "--stop-loss-r",
            "1.0",
            "--take-profit-r",
            "100.0",
            "--cost-profile",
            "zero",
            "--no-persist",
        ]
    ) == 0

    output = json.loads(capsys.readouterr().out)
    metadata = output["summary"]["metadata"]["lookback_return_momentum"]
    assert output["strategy"]["strategy_key"] == "LOOKBACK_RETURN_MOMENTUM"
    assert output["strategy"]["strategy_type"] == "lookback_return_momentum"
    assert metadata["lookback_bars"] == 1
    assert metadata["entry_threshold"] == 0.001
    assert metadata["holding_bars"] == 2
    assert output["diagnostics"]["lookback_return_momentum"]["candidate_entry_count"] == 1


def test_cli_timeframe_defaults_are_available() -> None:
    parser = build_parser("test")

    args_1m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "1m", "--no-persist"])
    args_5m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "5m", "--no-persist"])
    args_15m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "15m", "--no-persist"])

    assert _build_lookback_return_momentum_config(args_1m).lookback_bars == 20
    assert _build_lookback_return_momentum_config(args_5m).lookback_bars == 12
    assert _build_lookback_return_momentum_config(args_15m).lookback_bars == 8
    assert _build_lookback_return_momentum_config(args_15m).holding_bars == 4
