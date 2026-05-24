from __future__ import annotations

from dataclasses import dataclass, asdict
from random import Random
from statistics import mean, median
from typing import Any, Callable, Sequence

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.rsi_actions import RsiActionStrategy


@dataclass(frozen=True)
class WalkForwardConfig:
    train_window: pd.Timedelta | str
    test_window: pd.Timedelta | str
    step_size: pd.Timedelta | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "train_window", _timedelta(self.train_window, "train_window"))
        object.__setattr__(self, "test_window", _timedelta(self.test_window, "test_window"))
        object.__setattr__(self, "step_size", _timedelta(self.step_size, "step_size"))


@dataclass(frozen=True)
class WalkForwardFold:
    fold_index: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp

    def to_metadata(self) -> dict[str, object]:
        payload = asdict(self)
        for key in ("train_start", "train_end", "test_start", "test_end"):
            payload[key] = _iso(payload[key])
        return payload


ActionBuilder = Callable[[pd.DataFrame, pd.DataFrame, WalkForwardFold], Sequence[StrategyAction]]


def generate_walk_forward_folds(
    *,
    start: Any,
    end: Any,
    config: WalkForwardConfig,
) -> tuple[WalkForwardFold, ...]:
    start_ts = _timestamp(start)
    end_ts = _timestamp(end)
    if end_ts <= start_ts:
        raise ValueError("end must be after start")

    folds: list[WalkForwardFold] = []
    train_start = start_ts
    fold_index = 1
    while True:
        train_end = train_start + config.train_window
        test_start = train_end
        test_end = test_start + config.test_window
        if test_end > end_ts:
            break
        folds.append(
            WalkForwardFold(
                fold_index=fold_index,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        fold_index += 1
        train_start = train_start + config.step_size
    return tuple(folds)


def run_walk_forward_validation(
    candles: pd.DataFrame,
    *,
    config: WalkForwardConfig,
    action_builder: ActionBuilder,
    engine_config: StrategyEngineConfig | None = None,
    strategy_parameters: dict[str, Any] | None = None,
) -> dict[str, object]:
    frame = _normalized_candles(candles)
    if frame.empty:
        raise ValueError("candles must not be empty")
    folds = generate_walk_forward_folds(
        start=frame.iloc[0]["timestamp"],
        end=frame.iloc[-1]["timestamp"] + _minimum_timestamp_step(frame),
        config=config,
    )
    fold_results: list[dict[str, object]] = []
    for fold in folds:
        train = _slice(frame, fold.train_start, fold.train_end)
        test = _slice(frame, fold.test_start, fold.test_end)
        if test.empty:
            fold_results.append(_failed_fold(fold, train, test, "EMPTY_TEST_WINDOW"))
            continue
        try:
            actions = tuple(action_builder(train, test, fold))
            result = run_strategy_backtest_engine(test, list(actions), config=engine_config)
            status = "NO_FILLS" if result.summary.trade_count == 0 else "OK"
            fold_results.append(
                {
                    **fold.to_metadata(),
                    "status": status,
                    "train_candle_count": len(train),
                    "test_candle_count": len(test),
                    "action_count": len(actions),
                    "strategy_parameters": dict(strategy_parameters or {}),
                    "summary": {
                        "total_return": result.summary.total_return,
                        "net_pnl": result.summary.net_pnl,
                        "trade_count": result.summary.trade_count,
                        "max_drawdown": result.summary.max_drawdown,
                        "final_equity": result.summary.final_equity,
                    },
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through failure count behavior
            fold_results.append(_failed_fold(fold, train, test, str(exc)))
    return {
        "schema_version": "walk_forward_validation_v1",
        "config": {
            "train_window": str(config.train_window),
            "test_window": str(config.test_window),
            "step_size": str(config.step_size),
        },
        "folds": fold_results,
        "aggregate": aggregate_fold_metrics(fold_results),
    }


def build_rsi_action_builder(
    *,
    window: int = 14,
    buy_threshold: float = 30.0,
    sell_threshold: float = 70.0,
) -> ActionBuilder:
    strategy = RsiActionStrategy(
        window=window,
        buy_threshold=buy_threshold,
        sell_threshold=sell_threshold,
    )

    def _builder(train: pd.DataFrame, test: pd.DataFrame, fold: WalkForwardFold) -> Sequence[StrategyAction]:
        position = 0.0
        actions: list[StrategyAction] = []
        for position_index in range(len(test)):
            history = pd.concat([train, test.iloc[: position_index + 1]], ignore_index=True)
            emitted = strategy.evaluate(history, portfolio_state={"position": position})
            for action in emitted:
                if action.action_type == StrategyActionType.ENTER_LONG:
                    position = 1.0
                elif action.action_type == StrategyActionType.EXIT_LONG:
                    position = 0.0
                actions.append(action)
        return actions

    return _builder


def aggregate_fold_metrics(fold_results: Sequence[dict[str, object]]) -> dict[str, object]:
    failures = [fold for fold in fold_results if str(fold.get("status")) not in {"OK", "NO_FILLS"}]
    no_fill_count = len([fold for fold in fold_results if fold.get("status") == "NO_FILLS"])
    return {
        "fold_count": len(fold_results),
        "failure_count": len(failures),
        "no_fill_fold_count": no_fill_count,
        "positive_fold_ratio": _positive_fold_ratio(fold_results),
        "total_return": _distribution(_summary_values(fold_results, "total_return")),
        "net_pnl": _distribution(_summary_values(fold_results, "net_pnl")),
        "trade_count": _distribution(_summary_values(fold_results, "trade_count")),
        "max_drawdown": _distribution(_summary_values(fold_results, "max_drawdown")),
    }


def monte_carlo_trade_return_bootstrap(
    trade_returns: Sequence[float],
    *,
    iterations: int = 1000,
    seed: int = 0,
    sample_size: int | None = None,
) -> dict[str, object]:
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    returns = [float(value) for value in trade_returns]
    if not returns:
        return {
            "schema_version": "trade_return_bootstrap_v1",
            "seed": seed,
            "iterations": iterations,
            "sample_size": 0,
            "sample_totals": (),
            "distribution": _distribution(()),
            "warning": "no trade returns supplied",
        }
    size = sample_size if sample_size is not None else len(returns)
    if size < 1:
        raise ValueError("sample_size must be at least 1")
    rng = Random(seed)
    sample_totals = tuple(
        sum(rng.choice(returns) for _ in range(size))
        for _ in range(iterations)
    )
    return {
        "schema_version": "trade_return_bootstrap_v1",
        "seed": seed,
        "iterations": iterations,
        "sample_size": size,
        "sample_totals": sample_totals,
        "distribution": _distribution(sample_totals),
    }


def _summary_values(fold_results: Sequence[dict[str, object]], key: str) -> tuple[float, ...]:
    values: list[float] = []
    for fold in fold_results:
        summary = fold.get("summary")
        if not isinstance(summary, dict):
            continue
        value = summary.get(key)
        if value is not None:
            values.append(float(value))
    return tuple(values)


def _distribution(values: Sequence[float]) -> dict[str, float | int | None]:
    numeric = sorted(float(value) for value in values)
    if not numeric:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None, "iqr": None}
    return {
        "count": len(numeric),
        "mean": mean(numeric),
        "median": median(numeric),
        "min": numeric[0],
        "max": numeric[-1],
        "iqr": _percentile(numeric, 0.75) - _percentile(numeric, 0.25),
    }


def _positive_fold_ratio(fold_results: Sequence[dict[str, object]]) -> float | None:
    values = _summary_values(fold_results, "total_return")
    if not values:
        return None
    return len([value for value in values if value > 0]) / len(values)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if len(values) == 1:
        return float(values[0])
    position = (len(values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return float(values[lower] * (1 - weight) + values[upper] * weight)


def _failed_fold(fold: WalkForwardFold, train: pd.DataFrame, test: pd.DataFrame, reason: str) -> dict[str, object]:
    return {
        **fold.to_metadata(),
        "status": "FAILED",
        "reason": reason,
        "train_candle_count": len(train),
        "test_candle_count": len(test),
        "action_count": 0,
    }


def _normalized_candles(candles: pd.DataFrame) -> pd.DataFrame:
    if "timestamp" not in candles.columns:
        raise ValueError("candles must include timestamp")
    frame = candles.copy(deep=True)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.sort_values("timestamp").reset_index(drop=True)


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame[(frame["timestamp"] >= start) & (frame["timestamp"] < end)].reset_index(drop=True)


def _minimum_timestamp_step(frame: pd.DataFrame) -> pd.Timedelta:
    if len(frame) < 2:
        return pd.Timedelta(1, unit="ns")
    deltas = frame["timestamp"].sort_values().diff().dropna()
    if deltas.empty:
        return pd.Timedelta(1, unit="ns")
    return deltas.min()


def _timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _timedelta(value: pd.Timedelta | str, name: str) -> pd.Timedelta:
    delta = pd.Timedelta(value)
    if delta <= pd.Timedelta(0):
        raise ValueError(f"{name} must be positive")
    return delta


def _iso(timestamp: pd.Timestamp) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")
