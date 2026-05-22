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

    monkeypatch.setattr(strategy_postgres_runner_core, "strategy_for_pattern", lambda *_: StubStrategy())
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "build_pattern_trade_actions",
        lambda *args, **kwargs: [strategy_postgres_runner_cli.StrategyAction(strategy_postgres_runner_cli.StrategyActionType.EXIT_LONG, timestamp=candles.iloc[-1]["timestamp"], quantity=1.0, reason="TARGET_HIT")],
    )

    _, actions = strategy_postgres_runner_core._build_actions(candles, "STUB")
    assert actions
    assert any(a.action_type.name == "EXIT_LONG" for a in actions)
