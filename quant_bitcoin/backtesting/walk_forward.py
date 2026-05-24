from __future__ import annotations

from dataclasses import dataclass, asdict
from random import Random
from statistics import mean, median
from typing import Any, Callable, Sequence

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.patterns import PatternEntryFilterConfig, strategy_for_pattern
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
                        "expectancy": _expectancy(result.summary.metadata),
                    },
                    "diagnostics": _fold_diagnostics(result.summary.metadata),
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


def build_pattern_action_builder(
    *,
    pattern: str,
    entry_filter_config: PatternEntryFilterConfig | None = None,
    entry_mode: PatternEntryMode | str = PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
    entry_config: PatternEntryConfig | None = None,
    entry_custom_price: float | None = None,
) -> ActionBuilder:
    pattern_entry_mode = _pattern_entry_mode(entry_mode)
    pattern_entry_config = entry_config or PatternEntryConfig()

    def _builder(train: pd.DataFrame, test: pd.DataFrame, fold: WalkForwardFold) -> Sequence[StrategyAction]:
        strategy = strategy_for_pattern(pattern, entry_filter_config=entry_filter_config)
        actions: list[StrategyAction] = []
        seen_event_ids: set[str] = set()
        for position_index in range(len(test)):
            history = pd.concat([train, test.iloc[: position_index + 1]], ignore_index=True)
            raw_actions = strategy.evaluate(history)
            for raw_action in raw_actions:
                event_id = str((raw_action.metadata or {}).get("pattern_event_id") or "")
                if event_id and event_id in seen_event_ids:
                    continue
                if event_id:
                    seen_event_ids.add(event_id)
                actions.extend(
                    _expand_pattern_walk_forward_action(
                        raw_action,
                        history.iloc[-1],
                        test.iloc[position_index + 1 :],
                        entry_mode=pattern_entry_mode,
                        entry_config=pattern_entry_config,
                        entry_custom_price=entry_custom_price,
                    )
                )
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
        "expectancy": _distribution(_summary_values(fold_results, "expectancy")),
        "trade_count": _distribution(_summary_values(fold_results, "trade_count")),
        "max_drawdown": _distribution(_summary_values(fold_results, "max_drawdown")),
        "pattern_fold_stability": _pattern_fold_stability(fold_results),
    }


def _expand_pattern_walk_forward_action(
    action: StrategyAction,
    confirmation_candle: pd.Series,
    future_test_candles: pd.DataFrame,
    *,
    entry_mode: PatternEntryMode,
    entry_config: PatternEntryConfig,
    entry_custom_price: float | None,
) -> list[StrategyAction]:
    metadata = action.metadata or {}
    if action.action_type not in {StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT}:
        return [action]
    risk_plan = metadata.get("risk_plan")
    position_side = metadata.get("position_side")
    if risk_plan is None or position_side not in {"LONG", "SHORT"} or getattr(risk_plan, "status", None) != RiskExitPlanStatus.VALID:
        return [StrategyAction(StrategyActionType.SKIP, action.timestamp, quantity=0.0, reason="RISK_PLAN_INVALID", metadata=dict(metadata))]
    event = type("PatternEventProxy", (), metadata)()
    return build_pattern_trade_actions(
        event,
        risk_plan,
        future_test_candles,
        entry_action_timestamp=action.timestamp,
        confirmation_candle=confirmation_candle,
        position_side=str(position_side),
        entry_quantity=action.quantity,
        entry_mode=entry_mode,
        entry_config=entry_config,
        entry_custom_price=entry_custom_price,
    )


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


def _fold_diagnostics(summary_metadata: dict[str, Any]) -> dict[str, object]:
    attribution = summary_metadata.get("trade_attribution") if isinstance(summary_metadata, dict) else None
    cost_summary = summary_metadata.get("cost_summary") if isinstance(summary_metadata, dict) else None
    performance_diagnostics = summary_metadata.get("performance_diagnostics") if isinstance(summary_metadata, dict) else None
    risk_exit_audit = summary_metadata.get("risk_exit_audit") if isinstance(summary_metadata, dict) else None
    score_calibration = summary_metadata.get("score_calibration") if isinstance(summary_metadata, dict) else None
    return {
        "trade_attribution": attribution,
        "cost_summary": cost_summary,
        "performance_diagnostics": performance_diagnostics,
        "risk_exit_audit": risk_exit_audit,
        "score_calibration": score_calibration,
    }


def _expectancy(summary_metadata: dict[str, Any]) -> float | None:
    attribution = summary_metadata.get("trade_attribution") if isinstance(summary_metadata, dict) else None
    if not isinstance(attribution, dict):
        return None
    trade_metrics = attribution.get("trade_metrics")
    if not isinstance(trade_metrics, dict):
        return None
    value = trade_metrics.get("expectancy")
    return float(value) if value is not None else None


def _pattern_fold_stability(fold_results: Sequence[dict[str, object]]) -> dict[str, object]:
    pattern_counts: dict[str, dict[str, int]] = {}
    for fold in fold_results:
        diagnostics = fold.get("diagnostics")
        if not isinstance(diagnostics, dict):
            continue
        attribution = diagnostics.get("trade_attribution")
        if not isinstance(attribution, dict):
            continue
        groups = attribution.get("attribution")
        if not isinstance(groups, dict):
            continue
        by_pattern = groups.get("by_pattern_type")
        if not isinstance(by_pattern, dict):
            continue
        for pattern_key, metrics in by_pattern.items():
            if not isinstance(metrics, dict):
                continue
            completed = int(metrics.get("completed_trade_count") or 0)
            entry = pattern_counts.setdefault(str(pattern_key), {"active_fold_count": 0, "completed_trade_count": 0})
            if completed > 0:
                entry["active_fold_count"] += 1
                entry["completed_trade_count"] += completed
    return {
        "patterns": pattern_counts,
        "pattern_count": len(pattern_counts),
    }


def _pattern_entry_mode(value: PatternEntryMode | str) -> PatternEntryMode:
    if isinstance(value, PatternEntryMode):
        return value
    return PatternEntryMode(str(value).upper().replace("-", "_"))


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
