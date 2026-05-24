from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig
from quant_bitcoin.backtesting.walk_forward import (
    WalkForwardConfig,
    aggregate_fold_metrics,
    build_pattern_action_builder,
    generate_walk_forward_folds,
    monte_carlo_trade_return_bootstrap,
    run_walk_forward_validation,
)
from quant_bitcoin.backtesting import walk_forward_cli
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles(periods: int = 8) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01T00:00:00Z", periods=periods, freq="min"),
            "open": [100.0 + i for i in range(periods)],
            "high": [101.0 + i for i in range(periods)],
            "low": [99.0 + i for i in range(periods)],
            "close": [100.0 + i for i in range(periods)],
            "volume": [10.0] * periods,
        }
    )


def _pattern_fixture(pattern: str) -> pd.DataFrame:
    rows = [
        {
            "timestamp": pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(minutes=index),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        for index in range(20)
    ]
    if pattern == "FAIR_VALUE_GAP":
        rows.extend(
            [
                {"timestamp": pd.Timestamp("2026-01-01T00:20:00Z"), "open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0, "volume": 100.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:21:00Z"), "open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:22:00Z"), "open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0, "volume": 100.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:23:00Z"), "open": 103.0, "high": 106.0, "low": 102.0, "close": 105.0, "volume": 100.0},
            ]
        )
    elif pattern == "ORDER_BLOCK":
        rows.extend(
            [
                {"timestamp": pd.Timestamp("2026-01-01T00:20:00Z"), "open": 100.0, "high": 100.0, "low": 99.0, "close": 99.2, "volume": 100.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:21:00Z"), "open": 99.2, "high": 110.0, "low": 98.0, "close": 109.5, "volume": 500.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:22:00Z"), "open": 109.5, "high": 111.0, "low": 109.0, "close": 110.0, "volume": 100.0},
                {"timestamp": pd.Timestamp("2026-01-01T00:23:00Z"), "open": 110.0, "high": 111.0, "low": 109.5, "close": 110.5, "volume": 100.0},
            ]
        )
    else:
        raise ValueError(pattern)
    return pd.DataFrame(rows)


def test_generate_walk_forward_folds_uses_deterministic_utc_boundaries() -> None:
    folds = generate_walk_forward_folds(
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T00:08:00Z",
        config=WalkForwardConfig("3min", "2min", "2min"),
    )

    assert len(folds) == 2
    assert folds[0].to_metadata()["train_start"] == "2026-01-01T00:00:00Z"
    assert folds[0].to_metadata()["test_start"] == "2026-01-01T00:03:00Z"
    assert folds[1].to_metadata()["train_start"] == "2026-01-01T00:02:00Z"
    assert folds[1].to_metadata()["test_end"] == "2026-01-01T00:07:00Z"


def test_aggregate_fold_metrics_reports_distribution_and_failures() -> None:
    aggregate = aggregate_fold_metrics(
        [
            {"status": "OK", "summary": {"total_return": 0.1, "net_pnl": 10.0, "trade_count": 2, "max_drawdown": -0.01}},
            {"status": "NO_FILLS", "summary": {"total_return": 0.0, "net_pnl": 0.0, "trade_count": 0, "max_drawdown": 0.0}},
            {"status": "FAILED", "reason": "bad fold"},
        ]
    )

    assert aggregate["fold_count"] == 3
    assert aggregate["failure_count"] == 1
    assert aggregate["no_fill_fold_count"] == 1
    assert aggregate["positive_fold_ratio"] == 0.5
    assert aggregate["total_return"]["max"] == 0.1


def test_monte_carlo_bootstrap_is_deterministic_for_seed() -> None:
    first = monte_carlo_trade_return_bootstrap([1.0, -0.5, 2.0], iterations=5, seed=42)
    second = monte_carlo_trade_return_bootstrap([1.0, -0.5, 2.0], iterations=5, seed=42)
    different = monte_carlo_trade_return_bootstrap([1.0, -0.5, 2.0], iterations=5, seed=43)

    assert first == second
    assert first["sample_totals"] != different["sample_totals"]
    assert first["distribution"]["count"] == 5
    with pytest.raises(ValueError, match="iterations"):
        monte_carlo_trade_return_bootstrap([1.0], iterations=0)


def test_run_walk_forward_validation_with_synthetic_actions() -> None:
    candles = _candles()

    def action_builder(train, test, fold):
        return [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=test.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=test.iloc[-1]["timestamp"], quantity=1.0),
        ]

    payload = run_walk_forward_validation(
        candles,
        config=WalkForwardConfig("3min", "2min", "2min"),
        action_builder=action_builder,
        engine_config=StrategyEngineConfig(starting_cash=10000.0),
        strategy_parameters={"name": "synthetic"},
    )

    assert payload["schema_version"] == "walk_forward_validation_v1"
    assert len(payload["folds"]) == 2
    assert payload["folds"][0]["status"] == "OK"
    assert payload["folds"][0]["summary"]["trade_count"] == 2
    assert payload["aggregate"]["failure_count"] == 0


def test_run_walk_forward_validation_reports_no_fill_folds() -> None:
    payload = run_walk_forward_validation(
        _candles(),
        config=WalkForwardConfig("3min", "2min", "2min"),
        action_builder=lambda train, test, fold: [],
        engine_config=StrategyEngineConfig(starting_cash=10000.0),
    )

    assert payload["folds"][0]["status"] == "NO_FILLS"
    assert payload["aggregate"]["no_fill_fold_count"] == 2


def test_pattern_action_builder_uses_train_plus_current_test_prefix() -> None:
    candles = _pattern_fixture("FAIR_VALUE_GAP")
    train = candles.iloc[:20]
    fold = generate_walk_forward_folds(
        start=candles.iloc[0]["timestamp"],
        end=candles.iloc[-1]["timestamp"] + pd.Timedelta(minutes=1),
        config=WalkForwardConfig("20min", "4min", "4min"),
    )[0]
    builder = build_pattern_action_builder(pattern="FAIR_VALUE_GAP")

    assert builder(train, candles.iloc[20:22], fold) == []
    actions = builder(train, candles.iloc[20:24], fold)

    assert actions
    assert actions[0].metadata["pattern_type"] == "FAIR_VALUE_GAP"
    assert actions[0].timestamp == candles.iloc[22]["timestamp"]


def test_walk_forward_validation_runs_pattern_fixture_without_no_fills() -> None:
    payload = run_walk_forward_validation(
        _pattern_fixture("FAIR_VALUE_GAP"),
        config=WalkForwardConfig("20min", "4min", "4min"),
        action_builder=build_pattern_action_builder(pattern="FAIR_VALUE_GAP"),
        engine_config=StrategyEngineConfig(starting_cash=10000.0),
        strategy_parameters={"strategy": "pattern", "pattern": "FAIR_VALUE_GAP"},
    )

    assert payload["folds"][0]["status"] == "OK"
    assert payload["folds"][0]["action_count"] >= 1
    assert "trade_attribution" in payload["folds"][0]["diagnostics"]
    assert payload["aggregate"]["expectancy"]["count"] == 0


def test_walk_forward_cli_outputs_pattern_json_for_fvg_and_order_block(tmp_path, capsys) -> None:
    for pattern in ("FAIR_VALUE_GAP", "ORDER_BLOCK"):
        path = tmp_path / f"{pattern}.csv"
        _pattern_fixture(pattern).to_csv(path, index=False)

        exit_code = walk_forward_cli.main(
            [
                "--csv",
                str(path),
                "--train-window",
                "20min",
                "--test-window",
                "4min",
                "--step-size",
                "4min",
                "--strategy",
                "pattern",
                "--pattern",
                pattern,
                "--min-pattern-score",
                "0",
                "--monte-carlo-iterations",
                "2",
            ]
        )
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert payload["folds"][0]["strategy_parameters"]["strategy"] == "pattern"
        assert payload["folds"][0]["strategy_parameters"]["pattern"] == pattern
        assert payload["folds"][0]["status"] == "OK"


def test_walk_forward_cli_outputs_deterministic_json(tmp_path, capsys) -> None:
    path = tmp_path / "candles.csv"
    _candles(12).to_csv(path, index=False)

    exit_code = walk_forward_cli.main(
        [
            "--csv",
            str(path),
            "--train-window",
            "4min",
            "--test-window",
            "3min",
            "--step-size",
            "3min",
            "--rsi-window",
            "2",
            "--rsi-buy-threshold",
            "60",
            "--rsi-sell-threshold",
            "80",
            "--monte-carlo-seed",
            "7",
            "--monte-carlo-iterations",
            "3",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "walk_forward_validation_v1"
    assert payload["config"]["train_window"] == "0 days 00:04:00"
    assert payload["monte_carlo"]["seed"] == 7
