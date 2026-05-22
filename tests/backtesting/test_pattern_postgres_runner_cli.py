from __future__ import annotations
import json
import pandas as pd
from quant_bitcoin.backtesting import strategy_postgres_runner_cli, pattern_postgres_runner_cli

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
