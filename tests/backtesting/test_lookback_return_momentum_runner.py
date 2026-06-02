from __future__ import annotations

import json

import pandas as pd

from quant_bitcoin.backtesting import strategy_postgres_runner_cli
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.pattern_action_builder import CostAwareEntryFilterConfig
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
            "high": [101.0, 102.0, 102.5, 103.0],
            "low": [99.0, 100.0, 100.5, 101.0],
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
                    "--atr-period",
                    "1",
                    "--take-profit-atr-multiple",
                    "100.0",
                    "--no-persist",
                ]
            )
        ),
    )

    assert strategy.strategy_key == "LOOKBACK_RETURN_MOMENTUM"
    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    assert any(action.action_type is StrategyActionType.EXIT_LONG for action in actions)


def test_build_actions_applies_cost_aware_filter_to_lookback_return_momentum() -> None:
    _, actions = _build_actions(
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
                    "--atr-period",
                    "1",
                    "--no-persist",
                ]
            )
        ),
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            enabled=True,
            min_net_reward_bps=0.0,
            min_net_rr=1.0,
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=20.0),
            liquidity_role=LiquidityRole.TAKER,
            cost_profile_name="unit_test",
        ),
    )

    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].metadata["cost_aware_entry_filter"]["blocked"] is True


def test_build_actions_applies_minimum_atr_bps_filter_to_lookback_return_momentum() -> None:
    _, actions = _build_actions(
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
                    "--atr-period",
                    "1",
                    "--minimum-atr-bps",
                    "250.0",
                    "--no-persist",
                ]
            )
        ),
    )

    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].reason == "ATR_TOO_SMALL_FOR_COST"
    assert actions[0].metadata["minimum_atr_bps_filter"]["blocked"] is True


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
            "--atr-period",
            "1",
            "--stop-loss-atr-multiple",
            "1.0",
            "--take-profit-atr-multiple",
            "100.0",
            "--minimum-atr-bps",
            "10.0",
            "--cost-profile",
            "zero",
            "--enable-cost-aware-entry-filter",
            "--min-net-reward-bps",
            "0.0",
            "--min-net-rr",
            "1.0",
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
    assert metadata["risk_distance_mode"] == "atr"
    assert metadata["atr_period"] == 1
    assert metadata["take_profit_atr_multiple"] == 100.0
    assert metadata["minimum_atr_bps"] == 10.0
    assert output["diagnostics"]["lookback_return_momentum"]["candidate_entry_count"] == 1
    assert output["diagnostics"]["lookback_return_momentum"]["accepted_entry_count"] == 1
    assert output["diagnostics"]["lookback_return_momentum"]["cost_aware_blocked_entry_count"] == 0
    assert output["diagnostics"]["lookback_return_momentum"]["atr_too_small_blocked_entry_count"] == 0
    minimum_filter_metadata = output["executions"][0]["metadata"]["minimum_atr_bps_filter"]
    assert minimum_filter_metadata["enabled"] is True
    assert minimum_filter_metadata["blocked"] is False
    assert minimum_filter_metadata["minimum_atr_bps"] == 10.0
    filter_metadata = output["executions"][0]["metadata"]["cost_aware_entry_filter"]
    assert filter_metadata["enabled"] is True
    assert filter_metadata["blocked"] is False


def test_cli_v2_zero_cost_run_records_version_and_disabled_cost_gate(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: _FakeProvider(_candles()),
    )

    assert strategy_postgres_runner_cli.main(
        [
            "--strategy",
            "LOOKBACK_RETURN_MOMENTUM",
            "--lookback-return-momentum-version",
            "v2",
            "--lookback-bars",
            "1",
            "--entry-threshold",
            "0.001",
            "--holding-bars",
            "2",
            "--atr-period",
            "1",
            "--cost-profile",
            "zero",
            "--no-persist",
        ]
    ) == 0

    output = json.loads(capsys.readouterr().out)
    summary_metadata = output["summary"]["metadata"]
    lrm_metadata = summary_metadata["lookback_return_momentum"]
    cost_profile_metadata = summary_metadata["cost_profile"]
    cost_gate_metadata = summary_metadata["cost_aware_entry_filter"]

    assert output["reproducibility"]["strategy"]["version"] == "v2"
    assert lrm_metadata["strategy_version"] == "v2"
    assert cost_profile_metadata["profile_key"] == "zero"
    assert cost_profile_metadata["zero_cost_profile"] is True
    assert cost_gate_metadata["enabled"] is False
    assert output["summary"]["trade_count"] > 0
    assert all(execution["total_cost"] == 0.0 for execution in output["executions"])
    assert output["executions"][0]["metadata"]["strategy_version"] == "v2"


def test_cli_timeframe_defaults_are_available() -> None:
    parser = build_parser("test")

    args_1m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "1m", "--no-persist"])
    args_5m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "5m", "--no-persist"])
    args_15m = parser.parse_args(["--strategy", "LOOKBACK_RETURN_MOMENTUM", "--interval", "15m", "--no-persist"])

    assert _build_lookback_return_momentum_config(args_1m).lookback_bars == 20
    assert _build_lookback_return_momentum_config(args_5m).lookback_bars == 12
    assert _build_lookback_return_momentum_config(args_15m).lookback_bars == 8
    assert _build_lookback_return_momentum_config(args_15m).holding_bars == 4
    assert _build_lookback_return_momentum_config(args_15m).risk_distance_mode == "atr"
    assert _build_lookback_return_momentum_config(args_15m).atr_period == 14
    assert _build_lookback_return_momentum_config(args_15m).minimum_atr_bps == 0.0
