from __future__ import annotations
import json
import pandas as pd
from quant_bitcoin.backtesting import strategy_postgres_runner_cli, pattern_postgres_runner_cli
from quant_bitcoin.backtesting import strategy_postgres_runner_core

class FakeProvider:
    def __init__(self, candles: pd.DataFrame): self._c=candles
    def load(self)->pd.DataFrame: return self._c

def make_candles():
    return pd.DataFrame({"timestamp":pd.date_range("2026-05-18",periods=3,freq="min",tz="UTC"),"open":[100,101,102],"high":[101,102,103],"low":[99,100,101],"close":[100,101,102],"volume":[1,1,1]})

def test_strategy_cli_empty_candles_warning(monkeypatch,capsys):
    monkeypatch.setattr(strategy_postgres_runner_cli.PostgresCandleDataProvider,'from_database_url',lambda *a,**k:FakeProvider(make_candles().iloc[0:0]))
    assert strategy_postgres_runner_cli.main(["--no-persist"])==0
    out=json.loads(capsys.readouterr().out)
    assert out['warnings']==['candle_count = 0']

def test_pattern_cli_compatibility_alias(monkeypatch,capsys):
    monkeypatch.setattr(strategy_postgres_runner_cli.PostgresCandleDataProvider,'from_database_url',lambda *a,**k:FakeProvider(make_candles()))
    assert pattern_postgres_runner_cli.main(["--pattern","FAIR_VALUE_GAP","--no-persist"])==0
    out=json.loads(capsys.readouterr().out)
    assert out['strategy']['pattern']=='FAIR_VALUE_GAP'
    assert 'portfolio' in out and 'summary' in out


def test_build_actions_uses_canonical_pattern_action_builder(monkeypatch):
    candles = make_candles()

    class StubStrategy:
        strategy_key = "STUB"
        strategy_name = "STUB_PATTERN"

        def evaluate(self, candles_so_far, portfolio_state=None):
            from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan, RiskExitPlanStatus
            from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType

            risk_plan = RiskExitPlan(
                direction=RiskExitDirection.LONG,
                entry_price=100.0,
                structural_stop=99.0,
                atr=1.0,
                atr_buffer_multiplier=0.0,
                atr_buffer=0.0,
                stop_price=99.0,
                risk_per_unit=1.0,
                targets=(),
                status=RiskExitPlanStatus.VALID,
            )
            return [
                StrategyAction(
                    StrategyActionType.ENTER_LONG,
                    timestamp=candles_so_far.iloc[-1]["timestamp"],
                    quantity=1.0,
                    reason="PATTERN_CONFIRMED",
                    metadata={"position_side": "LONG", "risk_plan": risk_plan, "event_id": "e1"},
                )
            ]

    monkeypatch.setattr(strategy_postgres_runner_core, "strategy_for_pattern", lambda *args, **kwargs: StubStrategy())
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "build_pattern_trade_actions",
        lambda *args, **kwargs: [strategy_postgres_runner_cli.StrategyAction(strategy_postgres_runner_cli.StrategyActionType.EXIT_LONG, timestamp=candles.iloc[-1]["timestamp"], quantity=1.0, reason="TARGET_HIT")],
    )

    _, actions = strategy_postgres_runner_core._build_actions(candles, "STUB")
    assert actions
    assert any(a.action_type.name == "EXIT_LONG" for a in actions)


def test_build_transaction_cost_config_from_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(
        [
            "--maker-fee-bps",
            "1.5",
            "--taker-fee-bps",
            "7.0",
            "--spread-bps",
            "2.0",
            "--slippage-bps",
            "3.0",
            "--minimum-slippage-bps",
            "0.5",
            "--volatility-slippage-multiplier",
            "4.0",
            "--liquidity-role",
            "maker",
            "--no-persist",
        ]
    )
    config, liquidity_role = strategy_postgres_runner_core._build_transaction_cost_config(args)
    assert config.maker_fee_bps == 1.5
    assert config.taker_fee_bps == 7.0
    assert config.spread_bps == 2.0
    assert config.slippage_bps == 3.0
    assert config.minimum_slippage_bps == 0.5
    assert config.volatility_slippage_multiplier == 4.0
    assert liquidity_role.value == "MAKER"


def test_strategy_cli_output_includes_short_model_limitations(monkeypatch, capsys):
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-18", periods=2, freq="min", tz="UTC"),
            "open": [100, 90],
            "high": [101, 91],
            "low": [99, 89],
            "close": [100, 90],
            "volume": [1, 1],
        }
    )
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda *_: (
            type("StubStrategy", (), {"strategy_key": "STUB", "strategy_name": "STUB_PATTERN"})(),
            [
                strategy_postgres_runner_cli.StrategyAction(
                    strategy_postgres_runner_cli.StrategyActionType.ENTER_SHORT,
                    timestamp=candles.iloc[0]["timestamp"],
                    quantity=1.0,
                ),
                strategy_postgres_runner_cli.StrategyAction(
                    strategy_postgres_runner_cli.StrategyActionType.EXIT_SHORT,
                    timestamp=candles.iloc[1]["timestamp"],
                    quantity=1.0,
                ),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    out = json.loads(capsys.readouterr().out)
    limitations = out["summary"]["metadata"]["limitations"]
    assert "No borrow fees modeled" in limitations
    assert "No futures funding modeled" in limitations
    assert "No maintenance margin or liquidation model" in limitations


def test_build_pattern_entry_filter_config_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--allow-weak-pattern-events", "--min-pattern-score", "0.8", "--min-risk-reward", "1.5", "--pattern-quantity-override", "3", "--no-persist"])
    cfg = strategy_postgres_runner_core._build_pattern_entry_filter_config(args)
    assert "VALID" in cfg.allowed_statuses and "WEAK" in cfg.allowed_statuses
    assert cfg.minimum_pattern_score == 0.8
    assert cfg.minimum_risk_reward == 1.5
    assert cfg.quantity_override == 3


def test_profile_output_contains_timing_keys(monkeypatch, capsys):
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        'from_database_url',
        lambda *a, **k: FakeProvider(make_candles()),
    )
    assert strategy_postgres_runner_cli.main(["--no-persist", "--profile", "--pattern", "FAIR_VALUE_GAP"]) == 0
    out = json.loads(capsys.readouterr().out)
    profile = out["profiling"]
    for key in [
        "total_elapsed_ms",
        "load_candles_ms",
        "build_actions_ms",
        "run_engine_ms",
        "persist_ms",
        "json_output_ms",
    ]:
        assert key in profile
    assert profile["pattern_timings"][0]["pattern_key"] == "FAIR_VALUE_GAP"
    assert "top_functions" in profile


def test_no_persist_output_contains_runtime_metadata(monkeypatch, capsys):
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(make_candles()),
    )
    assert strategy_postgres_runner_cli.main(["--no-persist", "--pattern", "FAIR_VALUE_GAP"]) == 0
    out = json.loads(capsys.readouterr().out)
    runtime = out["runtime"]
    assert runtime["runtime_schema_version"] == "v1"
    assert runtime["strategy_key"] == "FAIR_VALUE_GAP"
    assert "total_elapsed_ms" in runtime
    assert "pattern_timings" in runtime
