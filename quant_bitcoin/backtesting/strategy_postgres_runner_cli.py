from __future__ import annotations
import argparse, json, os
from datetime import datetime, timezone
from typing import Any, Sequence
import pandas as pd
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.market_data.postgres_provider import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.runtime_logging import log_runtime_exception
from quant_bitcoin.backtesting.pattern_detection_cache import IndicatorCache, PatternEvaluationContext
from quant_bitcoin.strategies.patterns import FairValueGapStrategy, strategy_for_pattern
from quant_bitcoin.backtesting.strategy_engine import run_strategy_backtest_engine, StrategyEngineConfig

DEFAULT_DATABASE_URL="postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
DEFAULT_SOURCE="binance_spot"; DEFAULT_SYMBOL="BTCUSDT"; DEFAULT_INTERVAL="1m"; DEFAULT_STRATEGY="FAIR_VALUE_GAP"


def build_parser(prog:str, include_strategy:bool=True):
 p=argparse.ArgumentParser(prog=prog,description="Run strategy-level backtest from stored 1m candles.")
 p.add_argument("--database-url",default=os.environ.get("DATABASE_URL",DEFAULT_DATABASE_URL))
 p.add_argument("--source",default=os.environ.get("CANDLE_SOURCE",DEFAULT_SOURCE))
 p.add_argument("--symbol",default=os.environ.get("SYMBOL",DEFAULT_SYMBOL))
 p.add_argument("--interval",default=os.environ.get("INTERVAL",DEFAULT_INTERVAL))
 if include_strategy: p.add_argument("--strategy",default=DEFAULT_STRATEGY)
 p.add_argument("--pattern",default=None)
 p.add_argument("--start-time",type=_optional_timestamp,default=None)
 p.add_argument("--end-time",type=_optional_timestamp,default=None)
 p.add_argument("--starting-cash",type=float,default=10000.0)
 p.add_argument("--trade-quantity",type=float,default=1.0)
 p.add_argument("--no-persist",action="store_true")
 return p

def _optional_timestamp(v:str|None):
 if not v:return None
 return datetime.fromisoformat(v.replace('Z','+00:00')).astimezone(timezone.utc)

def _select(args): return (args.pattern or getattr(args,'strategy',None) or DEFAULT_STRATEGY).upper()

def _build_actions(candles:pd.DataFrame, strategy_key:str):
 s=strategy_for_pattern(strategy_key); acts=[]
 if isinstance(s, FairValueGapStrategy):
  cache=IndicatorCache.for_fvg(candles, s.detector_config); seen=set()
  for i in range(1,len(candles)+1):
   ctx=PatternEvaluationContext(candles=candles,current_index=i-1,indicator_cache=cache,seen_event_ids=seen)
   acts.extend(s.evaluate_at(ctx))
  return s,acts
 for i in range(1,len(candles)+1): acts.extend(s.evaluate(candles.iloc[:i]))
 return s,acts

def run(argv:Sequence[str]|None=None,*,prog='quant-bitcoin-strategy-backtest',include_strategy=True):
 args=build_parser(prog,include_strategy).parse_args(argv)
 provider=PostgresCandleDataProvider.from_database_url(args.database_url,source=args.source,symbol=args.symbol,interval=args.interval,start_time=args.start_time,end_time=args.end_time)
 candles=provider.load()
 if candles.empty:
  out={"strategy":{"name":f"{_select(args)}_PATTERN_STRATEGY","strategy_type":"single_pattern","pattern":_select(args)},"portfolio":{"starting_cash":args.starting_cash,"ending_cash":args.starting_cash,"ending_position":0.0,"final_equity":args.starting_cash,"total_return":0.0},"summary":{"trade_count":0,"buy_count":0,"sell_count":0,"max_drawdown":0.0},"executions":[],"events":[],"warnings":["candle_count = 0"]}
  print(json.dumps(out)); return 0
 strategy,actions=_build_actions(candles,_select(args));res=run_strategy_backtest_engine(candles,actions,config=StrategyEngineConfig(starting_cash=args.starting_cash,trade_quantity=args.trade_quantity))
 out={"strategy":{"name":strategy.strategy_name,"strategy_type":"single_pattern","pattern":strategy.strategy_key},"portfolio":{"starting_cash":res.summary.starting_cash,"ending_cash":res.summary.ending_cash,"ending_position":res.summary.ending_position,"final_equity":res.summary.final_equity,"total_return":res.summary.total_return},"summary":{"trade_count":res.summary.trade_count,"buy_count":res.summary.buy_count,"sell_count":res.summary.sell_count,"max_drawdown":res.summary.max_drawdown},"executions":[{"timestamp":e.timestamp.isoformat().replace('+00:00','Z') if hasattr(e.timestamp,'isoformat') else str(e.timestamp),"side":e.side,"price":e.price,"quantity":e.quantity,"reason":e.reason} for e in res.executions],"events":[],"warnings":[]}
 if not actions: out['warnings'].append('no strategy events')
 print(json.dumps(out)); return 0

def main(argv=None):
 try:return run(argv)
 except Exception as exc:
  log_runtime_exception(__name__,exc); return 1
