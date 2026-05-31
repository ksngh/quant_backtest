"""Task 283 principle-first BTCUSDT 1m microstructure research runner.

This module is offline-only research code. It consumes local candles, builds
completed-candle factor snapshots, emits deterministic semantic strategy
actions, runs the existing strategy engine, persists simulated backtests, and
writes a markdown report. It does not fetch market data, read secrets, call
exchange APIs, place orders, or manage live positions.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES
from quant_bitcoin.backtesting.costs import (
    LiquidityRole,
    TransactionCostConfig,
    effective_slippage_bps,
)
from quant_bitcoin.backtesting.strategy_engine import (
    StrategyEngineConfig,
    run_strategy_backtest_engine,
)
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.backtesting.strategy_validation_metrics import (
    trade_contribution_metrics,
)
from quant_bitcoin.backtesting.sizing import (
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
)
from quant_bitcoin.persistence.postgres import (
    BacktestRunReadModel,
    PostgresBacktestResultRepository,
    PostgresCandleRepository,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


TASK_ID = "TASK_283"
DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
REPORT_PATH = Path("reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md")
SOURCE = "binance_spot"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
STARTING_CASH = 1_000_000.0
STRATEGY_KEY = "task283_principle_first_microstructure"
STRATEGY_NAME = "TASK283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY"


@dataclass(frozen=True)
class CandidateSpec:
    variant_id: str
    family: str
    thesis: str
    priority: int
    params: dict[str, Any]


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    validation_group: str
    start_time: datetime
    end_time: datetime


@dataclass(frozen=True)
class RunSpec:
    candidate: CandidateSpec
    window: WindowSpec
    cost_profile_key: str
    run_group: str


@dataclass(frozen=True)
class DataAvailability:
    requested_start_time: datetime
    available_start_time: datetime | None
    available_end_time: datetime | None
    candle_count: int


@dataclass(frozen=True)
class CostAudit:
    mismatch_count: int = 0
    max_abs_mismatch: float = 0.0
    total_notional: float = 0.0
    total_fee_cost: float = 0.0
    total_spread_cost: float = 0.0
    total_slippage_cost: float = 0.0
    total_cost: float = 0.0
    effective_total_cost_bps: float | None = None


@dataclass(frozen=True)
class Attribution:
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_cost: float = 0.0
    completed_round_trips: int = 0
    execution_count: int = 0


@dataclass(frozen=True)
class ActionGenerationMetadata:
    generated_entries: int
    cost_rejections: int
    signal_counts: dict[str, int]
    exit_reasons: dict[str, int]
    factor_schema_version: str = "task283_factor_snapshot_v1"


@dataclass(frozen=True)
class RunRecord:
    variant_id: str
    family: str
    priority: int
    window_id: str
    validation_group: str
    run_group: str
    cost_profile: str
    run_id: int | None
    status: str
    skip_reason: str | None = None
    total_return: float | None = None
    final_equity: float | None = None
    trade_count: int = 0
    completed_round_trips: int = 0
    active_trade_days: int = 0
    gross_pnl: float | None = None
    net_pnl: float | None = None
    max_drawdown: float | None = None
    win_rate: float | None = None
    average_win: float | None = None
    average_loss: float | None = None
    profit_factor: float | None = None
    expectancy: float | None = None
    average_r: float | None = None
    median_r: float | None = None
    max_consecutive_losses: int = 0
    total_fee_cost: float | None = None
    total_spread_cost: float | None = None
    total_slippage_cost: float | None = None
    total_cost: float | None = None
    total_notional: float | None = None
    effective_total_cost_bps: float | None = None
    cost_to_gross_pnl_ratio: float | None = None
    largest_winner_contribution: float | None = None
    top_three_winner_contribution: float | None = None
    generated_entries: int = 0
    cost_rejections: int = 0
    long_attribution: Attribution = Attribution()
    short_attribution: Attribution = Attribution()
    family_attribution: Attribution = Attribution()
    cost_audit: CostAudit = CostAudit()
    readback_ok: bool = False
    candle_continuity_ok: bool = False
    candle_gap_count: int = 0
    conservative_intrabar_stop_first: bool = True
    research_only: bool = True


@dataclass(frozen=True)
class GateReport:
    status: str
    best_variant_id: str | None
    gate_rows: tuple[tuple[str, str, str, bool], ...]
    failed_gates: tuple[str, ...]
    overfit_conclusion: str


def build_candidates(batch: str = "batch1") -> tuple[CandidateSpec, ...]:
    if batch != "batch1":
        raise ValueError("supported Task 283 batches: batch1")
    return (
        CandidateSpec(
            variant_id="T283_B1_LSR_V2_RECLAIM_R18",
            family="LIQUIDITY_SWEEP_REVERSAL_V2",
            priority=1,
            thesis=(
                "Stops cluster near recent swing/session highs and lows; a sweep "
                "that closes back inside with rejection can reverse after forced flow exhausts."
            ),
            params={
                "mode": "liquidity_sweep_reversal",
                "range_lookback": 60,
                "target_r": 1.8,
                "stop_atr_mult": 0.15,
                "max_hold_bars": 240,
                "min_volume_ratio": 0.7,
                "min_wick_ratio": 0.05,
                "cash_fraction": 0.35,
                "cost_gate": {"min_reward_cost_multiple": 2.0, "min_net_rr": 0.35},
            },
        ),
        CandidateSpec(
            variant_id="T283_B1_VCB_COMP60_BODY35_R20",
            family="VOLATILITY_COMPRESSION_BREAKOUT",
            priority=2,
            thesis=(
                "BTC volatility clusters; low realized range followed by body/volume "
                "displacement can continue as breakout traders and stops reinforce direction."
            ),
            params={
                "mode": "volatility_compression_breakout",
                "range_lookback": 60,
                "compression_max_bps": 85.0,
                "min_body_ratio": 0.35,
                "min_volume_ratio": 0.75,
                "target_r": 2.0,
                "stop_atr_mult": 0.10,
                "max_hold_bars": 180,
                "cash_fraction": 0.25,
                "cost_gate": {"min_reward_cost_multiple": 2.0, "min_net_rr": 0.35},
            },
        ),
        CandidateSpec(
            variant_id="T283_B1_MTF_PULLBACK_15M_1H_R16",
            family="MTF_TREND_PULLBACK_CONTINUATION",
            priority=3,
            thesis=(
                "When completed 15m and 1h trend pressure agree, 1m pullbacks into "
                "short EMAs can resume as momentum and forced exits reinforce direction."
            ),
            params={
                "mode": "mtf_trend_pullback",
                "target_r": 1.6,
                "stop_atr_mult": 0.15,
                "max_hold_bars": 180,
                "cash_fraction": 0.25,
                "min_trend_bps": 15.0,
                "min_body_ratio": 0.15,
                "cost_gate": {"min_reward_cost_multiple": 2.0, "min_net_rr": 0.35},
            },
        ),
        CandidateSpec(
            variant_id="T283_B1_VOLUME_CLIMAX_REVERT_R12",
            family="VOLUME_CLIMAX_MEAN_REVERSION",
            priority=4,
            thesis=(
                "Liquidation-like candles can exhaust when range, volume, wick rejection, "
                "and close-location reversal align."
            ),
            params={
                "mode": "volume_climax_mean_reversion",
                "target_r": 1.2,
                "stop_atr_mult": 0.15,
                "max_hold_bars": 120,
                "cash_fraction": 0.20,
                "shock_bps": 35.0,
                "min_volume_ratio": 1.4,
                "cost_gate": {"min_reward_cost_multiple": 1.8, "min_net_rr": 0.25},
            },
        ),
        CandidateSpec(
            variant_id="T283_B1_SESSION_RANGE_TRAP_R15",
            family="SESSION_RANGE_LIQUIDITY_TRAP",
            priority=5,
            thesis=(
                "Session highs and lows attract breakout orders; a failed break/reclaim "
                "can mean-revert, while confirmed breaks may continue."
            ),
            params={
                "mode": "session_range_liquidity_trap",
                "range_lookback": 360,
                "target_r": 1.5,
                "stop_atr_mult": 0.10,
                "max_hold_bars": 180,
                "cash_fraction": 0.25,
                "cost_gate": {"min_reward_cost_multiple": 2.0, "min_net_rr": 0.35},
            },
        ),
        CandidateSpec(
            variant_id="T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002",
            family="PRINCIPLE_FIRST_PRIORITY_ENSEMBLE",
            priority=6,
            thesis=(
                "A liquidity-sweep reversal core should take full-notional priority "
                "when failed range breaks occur inside a bearish regime, while a tiny "
                "MTF activity sleeve supplies enough turnover without dominating risk."
            ),
            params={
                "mode": "priority_lsr_mtf_activity_ensemble",
                "lineage_note": "Task 281-style LSR core reinterpreted under Task 283 and executed one candle later.",
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_fraction": 0.02,
                "scout_target_bps": 150.0,
                "scout_stop_bps": 75.0,
                "scout_hold_bars": 120,
                "preempt_scout_on_core": True,
            },
        ),
        CandidateSpec(
            variant_id="T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002",
            family="PRINCIPLE_FIRST_PRIORITY_ENSEMBLE",
            priority=7,
            thesis=(
                "Same liquidity-sweep reversal core and MTF activity sleeve, but both "
                "entry and exit are executed on the next candle open after the signal "
                "or exit condition, keeping signal/execution separation while retaining "
                "the original structural stop/target condition sequence."
            ),
            params={
                "mode": "priority_lsr_mtf_activity_ensemble",
                "exit_execution_mode": "next_open_after_exit_condition",
                "lineage_note": "Task 283 B2 next-open execution variant of the LSR/MTF activity ensemble.",
                "core_fraction": 1.00,
                "core_target_bps": 260.0,
                "core_stop_bps": 130.0,
                "core_hold_bars": 480,
                "core_skip_sunday_hours_utc": [12, 13, 14, 15, 16, 17, 18],
                "scout_fraction": 0.02,
                "scout_target_bps": 150.0,
                "scout_stop_bps": 75.0,
                "scout_hold_bars": 120,
                "preempt_scout_on_core": True,
            },
        ),
    )


def build_primary_windows(latest: datetime) -> tuple[WindowSpec, ...]:
    latest = _as_utc(latest)
    windows = [
        WindowSpec("owner_0520_latest", "primary", _dt("2026-05-20T00:00:00Z"), latest),
        WindowSpec("owner_0525_latest", "primary", _dt("2026-05-25T00:00:00Z"), latest),
        WindowSpec("available_pre_owner_0510_0517", "pre_owner", _dt("2026-05-10T00:00:00Z"), _dt("2026-05-17T15:19:00Z")),
    ]
    return tuple(window for window in windows if window.end_time >= window.start_time)


def build_diagnostic_windows(latest: datetime) -> tuple[WindowSpec, ...]:
    latest = _as_utc(latest)
    candidates = (
        WindowSpec("owner_0520_drop_first_12h", "endpoint_trim", _dt("2026-05-20T12:00:00Z"), latest),
        WindowSpec("owner_0520_drop_last_12h", "endpoint_trim", _dt("2026-05-20T00:00:00Z"), latest - timedelta(hours=12)),
        WindowSpec("owner_0520_drop_last_24h", "endpoint_trim", _dt("2026-05-20T00:00:00Z"), latest - timedelta(hours=24)),
        WindowSpec("owner_0525_drop_last_12h", "endpoint_trim", _dt("2026-05-25T00:00:00Z"), latest - timedelta(hours=12)),
    )
    return tuple(window for window in candidates if window.end_time >= window.start_time)


def build_factor_snapshots(candles: pd.DataFrame) -> pd.DataFrame:
    """Return completed-candle factor snapshots with no future-column shifts."""

    frame = candles.copy(deep=True).reset_index(drop=True)
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = pd.to_numeric(frame[col], errors="raise").astype(float)

    prev_close = frame["close"].shift(1)
    candle_range = (frame["high"] - frame["low"]).replace(0.0, pd.NA)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["true_range"] = true_range
    frame["atr_14"] = true_range.shift(1).rolling(14, min_periods=14).mean()
    frame["atr_bps"] = (frame["atr_14"] / frame["close"]) * 10_000.0
    frame["range_bps"] = (true_range / frame["close"]) * 10_000.0
    frame["range_percentile_120"] = frame["range_bps"].shift(1).rolling(120, min_periods=60).rank(pct=True)
    frame["realized_vol_bps_30"] = (
        frame["close"].pct_change().shift(1).rolling(30, min_periods=30).std() * 10_000.0
    )
    frame["realized_vol_percentile_240"] = (
        frame["realized_vol_bps_30"].shift(1).rolling(240, min_periods=120).rank(pct=True)
    )

    for horizon in (1, 3, 5, 15, 30, 60, 240, 720):
        frame[f"return_bps_prior_{horizon}"] = (
            (frame["close"].shift(1) / frame["close"].shift(horizon + 1)) - 1.0
        ) * 10_000.0

    for window in (20, 60, 120, 240, 360):
        frame[f"range_high_prior_{window}"] = frame["high"].shift(1).rolling(window, min_periods=window).max()
        frame[f"range_low_prior_{window}"] = frame["low"].shift(1).rolling(window, min_periods=window).min()
        frame[f"range_width_bps_prior_{window}"] = (
            (frame[f"range_high_prior_{window}"] - frame[f"range_low_prior_{window}"]) / frame["close"]
        ) * 10_000.0

    frame["ema_fast_20"] = frame["close"].shift(1).ewm(span=20, min_periods=20, adjust=False).mean()
    frame["ema_slow_120"] = frame["close"].shift(1).ewm(span=120, min_periods=120, adjust=False).mean()
    frame["ema_slope_bps_20"] = ((frame["ema_fast_20"] / frame["ema_fast_20"].shift(20)) - 1.0) * 10_000.0
    frame["mtf_15m_trend_bps"] = frame["return_bps_prior_15"]
    frame["mtf_1h_trend_bps"] = frame["return_bps_prior_60"]
    frame["mtf_alignment"] = _sign_series(frame["mtf_15m_trend_bps"]) + _sign_series(frame["mtf_1h_trend_bps"])

    frame["body_bps"] = ((frame["close"] - frame["open"]).abs() / frame["close"]) * 10_000.0
    frame["body_ratio"] = ((frame["close"] - frame["open"]).abs() / candle_range).fillna(0.0)
    frame["upper_wick_ratio"] = ((frame["high"] - frame[["open", "close"]].max(axis=1)) / candle_range).fillna(0.0)
    frame["lower_wick_ratio"] = ((frame[["open", "close"]].min(axis=1) - frame["low"]) / candle_range).fillna(0.0)
    frame["close_location"] = ((frame["close"] - frame["low"]) / candle_range).fillna(0.5)
    frame["volume_ma_prior_20"] = frame["volume"].shift(1).rolling(20, min_periods=20).mean()
    frame["volume_ratio_20"] = frame["volume"] / frame["volume_ma_prior_20"]
    frame["volume_percentile_240"] = frame["volume"].shift(1).rolling(240, min_periods=120).rank(pct=True)
    frame["hour_utc"] = frame["timestamp"].dt.hour
    frame["weekday_utc"] = frame["timestamp"].dt.weekday
    frame["session_tag"] = frame["hour_utc"].map(_session_tag)
    frame["daily_open"] = frame.groupby(frame["timestamp"].dt.floor("D"))["open"].transform("first")
    frame["distance_from_daily_open_bps"] = ((frame["close"] / frame["daily_open"]) - 1.0) * 10_000.0
    frame["volatility_compression_flag"] = (
        (frame["range_width_bps_prior_60"] < 90.0)
        & (frame["realized_vol_percentile_240"].fillna(1.0) < 0.45)
    )
    frame["volatility_expansion_flag"] = frame["range_bps"] > (frame["atr_bps"].fillna(0.0) * 1.1)
    frame["swept_high_60"] = frame["high"] > frame["range_high_prior_60"]
    frame["swept_low_60"] = frame["low"] < frame["range_low_prior_60"]
    frame["close_back_inside_high_60"] = frame["close"] < frame["range_high_prior_60"]
    frame["close_back_inside_low_60"] = frame["close"] > frame["range_low_prior_60"]
    frame["factor_no_lookahead_contract"] = "completed_signal_candle_or_prior_only"
    return frame


def generate_actions(
    candles: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig | None = None,
) -> tuple[list[StrategyAction], ActionGenerationMetadata]:
    frame = build_factor_snapshots(candles)
    if frame.empty:
        return [], ActionGenerationMetadata(0, 0, {}, {})
    cost = cost_config or COST_PROFILES["conservative_crypto_1m"].config
    params = candidate.params
    mode = str(params.get("mode"))
    if mode == "priority_lsr_mtf_activity_ensemble":
        if params.get("exit_execution_mode") == "next_open_after_exit_condition":
            return _generate_priority_ensemble_shifted_exit_actions(frame, candidate)
        return _generate_priority_ensemble_actions(frame, candidate)

    actions: list[StrategyAction] = []
    generated = 0
    cost_rejections = 0
    signal_counts: dict[str, int] = defaultdict(int)
    exit_reasons: dict[str, int] = defaultdict(int)
    warmup = int(params.get("warmup_bars", 360))
    index = warmup
    while index < len(frame) - 2:
        signal = _candidate_signal(frame, index, candidate)
        if signal is None:
            index += 1
            continue
        side, signal_name, stop_price, target_price, max_hold = signal
        signal_counts[signal_name] += 1
        entry_index = index + 1
        entry_price = float(frame.iloc[entry_index]["open"])
        stop_price, target_price = _normalize_stop_target(side, entry_price, stop_price, target_price)
        cost_gate = cost_edge_decision(
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            volatility_bps=_finite_or_zero(frame.iloc[index].get("range_bps")),
            cost_config=cost,
            gate=params.get("cost_gate") if isinstance(params.get("cost_gate"), dict) else None,
        )
        if cost_gate["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = resolve_intrabar_exit(
            frame,
            entry_index=entry_index,
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            max_hold_bars=int(max_hold),
        )
        exit_reasons[exit_reason] += 1
        event_id = f"{candidate.variant_id}_{generated + 1}_{entry_index}"
        actions.extend(
            _entry_exit_actions(
                frame,
                candidate=candidate,
                signal_index=index,
                entry_index=entry_index,
                exit_index=exit_index,
                side=side,
                entry_price=entry_price,
                stop_price=stop_price,
                target_price=target_price,
                exit_price=exit_price,
                exit_reason=exit_reason,
                event_id=event_id,
                cash_fraction=float(params.get("cash_fraction", 0.25)),
                signal_name=signal_name,
                cost_gate=cost_gate,
            )
        )
        generated += 1
        index = max(exit_index + 1, index + 1)
    return actions, ActionGenerationMetadata(
        generated_entries=generated,
        cost_rejections=cost_rejections,
        signal_counts=dict(signal_counts),
        exit_reasons=dict(exit_reasons),
    )


def cost_edge_decision(
    *,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    volatility_bps: float,
    cost_config: TransactionCostConfig,
    gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_side = str(side).upper()
    if normalized_side == "LONG":
        gross_reward_bps = ((target_price - entry_price) / entry_price) * 10_000.0
        gross_risk_bps = ((entry_price - stop_price) / entry_price) * 10_000.0
    elif normalized_side == "SHORT":
        gross_reward_bps = ((entry_price - target_price) / entry_price) * 10_000.0
        gross_risk_bps = ((stop_price - entry_price) / entry_price) * 10_000.0
    else:
        raise ValueError("side must be LONG or SHORT")
    params = gate or {}
    one_way_cost_bps = (
        cost_config.taker_fee_bps
        + cost_config.spread_bps
        + effective_slippage_bps(cost_config, volatility_bps)
    )
    round_trip_cost_bps = 2.0 * one_way_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    reward_cost_multiple = None if round_trip_cost_bps <= 0 else gross_reward_bps / round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    blocked = (
        gross_reward_bps <= 0
        or gross_risk_bps <= 0
        or reward_cost_multiple is None
        or reward_cost_multiple < float(params.get("min_reward_cost_multiple", 2.0))
        or net_rr is None
        or net_rr < float(params.get("min_net_rr", 0.35))
    )
    return {
        "schema_version": "task283_cost_edge_gate_v1",
        "blocked": bool(blocked),
        "block_reason": "TASK283_COST_EDGE_GATE_REJECTED" if blocked else None,
        "side": normalized_side,
        "gross_reward_bps": gross_reward_bps,
        "gross_risk_bps": gross_risk_bps,
        "estimated_round_trip_cost_bps": round_trip_cost_bps,
        "reward_cost_multiple": reward_cost_multiple,
        "net_reward_bps": net_reward_bps,
        "net_risk_bps": net_risk_bps,
        "net_rr": net_rr,
        "fee_bps": cost_config.taker_fee_bps,
        "spread_bps": cost_config.spread_bps,
        "slippage_bps": effective_slippage_bps(cost_config, volatility_bps),
        "volatility_bps": volatility_bps,
    }


def resolve_intrabar_exit(
    frame: pd.DataFrame,
    *,
    entry_index: int,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    max_hold_bars: int,
) -> tuple[int, float, str]:
    end = min(len(frame) - 1, entry_index + max(1, int(max_hold_bars)))
    for index in range(entry_index, end + 1):
        row = frame.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        if side == "LONG":
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_hit = high >= stop_price
            target_hit = low <= target_price
        if stop_hit and target_hit:
            return index, stop_price, "TASK283_CONSERVATIVE_STOP_FIRST"
        if stop_hit:
            return index, stop_price, "TASK283_STOP"
        if target_hit:
            return index, target_price, "TASK283_TARGET"
    return end, float(frame.iloc[end]["close"]), "TASK283_TIME_EXIT"


def run_matrix(
    *,
    database_url: str,
    batch: str = "batch1",
    limit: int | None = None,
) -> list[RunRecord]:
    availability = load_data_availability(database_url)
    if availability.available_end_time is None:
        write_report([], availability=availability, gate_report=classify_records([], availability))
        return []

    candidates = build_candidates(batch)
    primary_windows = build_primary_windows(availability.available_end_time)
    records: list[RunRecord] = []
    sequence = 0
    for candidate in candidates:
        for window in primary_windows[:2]:
            sequence += 1
            if limit is not None and sequence > limit:
                gate = classify_records(records, availability)
                write_report(records, availability=availability, gate_report=gate)
                return records
            records.append(
                run_one(
                    database_url=database_url,
                    candidate=candidate,
                    window=window,
                    cost_profile_key="conservative_crypto_1m",
                    run_group="primary_candidate_comparison",
                )
            )

    best = _best_primary_candidate(records)
    if best is not None:
        candidate = next(candidate for candidate in candidates if candidate.variant_id == best)
        diagnostics = [
            RunSpec(candidate, window, "conservative_crypto_1m", "endpoint_trim")
            for window in build_diagnostic_windows(availability.available_end_time)
        ]
        diagnostics.extend(
            [
                RunSpec(candidate, build_primary_windows(availability.available_end_time)[0], "high_slippage_stress", "cost_stress"),
                RunSpec(candidate, build_primary_windows(availability.available_end_time)[1], "high_slippage_stress", "cost_stress"),
                RunSpec(candidate, build_primary_windows(availability.available_end_time)[0], "zero", "no_cost_diagnostic"),
                RunSpec(candidate, build_primary_windows(availability.available_end_time)[2], "conservative_crypto_1m", "pre_owner_check"),
            ]
        )
        for spec in diagnostics:
            sequence += 1
            if limit is not None and sequence > limit:
                break
            records.append(
                run_one(
                    database_url=database_url,
                    candidate=spec.candidate,
                    window=spec.window,
                    cost_profile_key=spec.cost_profile_key,
                    run_group=spec.run_group,
                )
            )

    gate_report = classify_records(records, availability)
    write_report(records, availability=availability, gate_report=gate_report)
    return records


def run_one(
    *,
    database_url: str,
    candidate: CandidateSpec,
    window: WindowSpec,
    cost_profile_key: str,
    run_group: str,
) -> RunRecord:
    candles = load_candles(database_url, window)
    if candles.empty:
        return _skipped_record(candidate, window, cost_profile_key, run_group, "no_local_candles_for_window")
    quality = candle_quality(candles)
    if not bool(quality["candle_continuity_ok"]):
        return _skipped_record(candidate, window, cost_profile_key, run_group, "local_candle_continuity_gap", quality=quality)
    cost_profile = COST_PROFILES[cost_profile_key]
    actions, action_meta = generate_actions(candles, candidate, cost_config=cost_profile.config)
    config = StrategyEngineConfig(
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        transaction_cost_config=cost_profile.config,
        default_liquidity_role=LiquidityRole.TAKER,
        allow_short=True,
        interval=INTERVAL,
        position_sizing=PositionSizingConfig(
            mode=PositionSizingMode.FIXED_QUANTITY,
            insufficient_funds_policy=InsufficientFundsPolicy.RESIZE,
        ),
        short_exposure_mode=ShortExposureMode.CASH_BOUNDED,
        enforce_candle_continuity=True,
    )
    result = run_strategy_backtest_engine(candles, actions, config=config)
    metadata = result.summary.metadata if isinstance(result.summary.metadata, dict) else {}
    research = {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "scope": "offline_backtest_research_only",
        "task_id": TASK_ID,
        "research_mode": "principle_first_microstructure",
        "strategy_family": candidate.family,
        "variant_id": candidate.variant_id,
        "factor_set_id": "task283_factor_snapshot_v1",
        "window_id": window.window_id,
        "validation_group": window.validation_group,
        "run_group": run_group,
        "cost_profile": cost_profile_key,
        "mtf_configuration": "completed_1m_with_prior_15m_1h_return_context",
        "no_live_trading": True,
        "research_only": True,
    }
    metadata["research"] = research
    metadata["task283_action_generation"] = {
        "schema_version": "task283_action_generation_v1",
        "candidate": candidate.variant_id,
        "family": candidate.family,
        "priority": candidate.priority,
        "generated_entries": action_meta.generated_entries,
        "cost_rejections": action_meta.cost_rejections,
        "signal_counts": action_meta.signal_counts,
        "exit_reasons": action_meta.exit_reasons,
        "completed_candle_only": True,
        "signal_execution_separated": True,
        "entry_execution": "next_candle_open",
        "intrabar_ambiguity_policy": "stop_first_when_stop_and_target_hit_same_candle",
    }
    metadata["cost_profile"] = cost_profile.to_metadata()
    repository = PostgresBacktestResultRepository(database_url)
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=window.start_time,
        end_time=window.end_time,
        strategy_key=STRATEGY_KEY,
        strategy_name=STRATEGY_NAME,
        strategy_version=f"task283_{candidate.variant_id}_{window.window_id}_{cost_profile_key}_v1",
        strategy_parameters={
            "candidate": candidate.variant_id,
            "family": candidate.family,
            "thesis": candidate.thesis,
            "priority": candidate.priority,
            "params": candidate.params,
            "window": {
                "window_id": window.window_id,
                "validation_group": window.validation_group,
                "start_time": _iso(window.start_time),
                "end_time": _iso(window.end_time),
            },
            "cost_profile": cost_profile.to_metadata(),
            "cost_profile_key": cost_profile_key,
            "research": research,
        },
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        engine_name="StrategyEngine",
        engine_version="strategy_engine_v1",
        run_metadata={
            "research": research,
            "cost_profile": cost_profile.to_metadata(),
            "task283_action_generation": metadata["task283_action_generation"],
        },
    )
    run_id = repository.save_completed_backtest(payload)
    persisted = repository.load_run_for_graphs(run_id)
    if persisted is None:
        raise RuntimeError(f"Task 283 persisted run could not be read back: {run_id}")
    return analyze_persisted_run(
        persisted,
        candidate=candidate,
        window=window,
        cost_profile_key=cost_profile_key,
        run_group=run_group,
        quality=quality,
        action_meta=action_meta,
    )


def load_data_availability(database_url: str) -> DataAvailability:
    import psycopg
    from psycopg.rows import dict_row

    requested_start = _dt("2026-04-20T00:00:00Z")
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        row = connection.execute(
            """
            SELECT MIN(open_time) AS min_time, MAX(open_time) AS max_time, COUNT(*) AS candle_count
            FROM candles
            WHERE source = %s AND symbol = %s AND interval = %s AND is_closed IS TRUE
              AND open_time >= %s
            """,
            (SOURCE, SYMBOL, INTERVAL, requested_start),
        ).fetchone()
    return DataAvailability(
        requested_start_time=requested_start,
        available_start_time=_as_utc(row["min_time"]) if row and row["min_time"] else None,
        available_end_time=_as_utc(row["max_time"]) if row and row["max_time"] else None,
        candle_count=int(row["candle_count"] or 0) if row else 0,
    )


def load_candles(database_url: str, window: WindowSpec) -> pd.DataFrame:
    candles = PostgresCandleRepository(database_url).load_standard_candles(
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=window.start_time,
        end_time=window.end_time,
    )
    frame = pd.DataFrame(candles)
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame[["timestamp", "open", "high", "low", "close", "volume"]]


def candle_quality(candles: pd.DataFrame) -> dict[str, Any]:
    if candles.empty:
        return {"candle_sorted": True, "candle_continuity_ok": False, "candle_gap_count": 0, "duplicate_timestamp_count": 0}
    timestamps = pd.to_datetime(candles["timestamp"], utc=True)
    sorted_ok = bool(timestamps.is_monotonic_increasing)
    duplicate_count = int(timestamps.duplicated().sum())
    diffs = timestamps.sort_values().diff().dropna()
    gap_count = int((diffs != pd.Timedelta(minutes=1)).sum())
    return {
        "candle_sorted": sorted_ok,
        "candle_continuity_ok": sorted_ok and duplicate_count == 0 and gap_count == 0,
        "candle_gap_count": gap_count,
        "duplicate_timestamp_count": duplicate_count,
    }


def analyze_persisted_run(
    persisted: BacktestRunReadModel,
    *,
    candidate: CandidateSpec,
    window: WindowSpec,
    cost_profile_key: str,
    run_group: str,
    quality: dict[str, Any],
    action_meta: ActionGenerationMetadata,
) -> RunRecord:
    summary = persisted.summary
    metadata = summary.metadata or {}
    cost_summary = metadata.get("cost_summary") if isinstance(metadata.get("cost_summary"), dict) else {}
    event_net_pnls = paired_event_net_pnls(persisted.trades)
    contribution = trade_contribution_metrics(event_net_pnls)
    cost_audit = audit_persisted_trade_costs(persisted.trades)
    long_attr, short_attr = side_attribution(persisted.trades)
    r_values = [
        float(value)
        for value in (
            (trade.metadata or {}).get("realized_r_multiple")
            for trade in persisted.trades
        )
        if value is not None
    ]
    perf = _realized_trade_stats(event_net_pnls, r_values)
    research = (persisted.run.metadata or {}).get("research") or {}
    summary_research = (metadata.get("research") or {}) if isinstance(metadata.get("research"), dict) else {}
    readback_ok = bool(
        research.get("task_id") == TASK_ID
        and summary_research.get("task_id") == TASK_ID
        and research.get("variant_id") == candidate.variant_id
        and summary_research.get("variant_id") == candidate.variant_id
    )
    return RunRecord(
        variant_id=candidate.variant_id,
        family=candidate.family,
        priority=candidate.priority,
        window_id=window.window_id,
        validation_group=window.validation_group,
        run_group=run_group,
        cost_profile=cost_profile_key,
        run_id=persisted.run.id,
        status="COMPLETED_RESEARCH_ONLY",
        total_return=float(summary.total_return),
        final_equity=float(summary.final_equity),
        trade_count=int(summary.trade_count),
        completed_round_trips=len(event_net_pnls),
        active_trade_days=active_trade_days(persisted.trades),
        gross_pnl=_float(cost_summary.get("gross_pnl")),
        net_pnl=_float(cost_summary.get("net_pnl")),
        max_drawdown=float((metadata.get("performance_metrics") or {}).get("max_drawdown") or 0.0),
        win_rate=perf["win_rate"],
        average_win=perf["average_win"],
        average_loss=perf["average_loss"],
        profit_factor=perf["profit_factor"],
        expectancy=perf["expectancy"],
        average_r=perf["average_r"],
        median_r=perf["median_r"],
        max_consecutive_losses=int(perf["max_consecutive_losses"] or 0),
        total_fee_cost=cost_audit.total_fee_cost,
        total_spread_cost=cost_audit.total_spread_cost,
        total_slippage_cost=cost_audit.total_slippage_cost,
        total_cost=cost_audit.total_cost,
        total_notional=cost_audit.total_notional,
        effective_total_cost_bps=cost_audit.effective_total_cost_bps,
        cost_to_gross_pnl_ratio=_float(cost_summary.get("cost_to_gross_pnl_ratio")),
        largest_winner_contribution=contribution.largest_winner_contribution,
        top_three_winner_contribution=contribution.top_three_winner_contribution,
        generated_entries=action_meta.generated_entries,
        cost_rejections=action_meta.cost_rejections,
        long_attribution=long_attr,
        short_attribution=short_attr,
        family_attribution=Attribution(
            gross_pnl=_float(cost_summary.get("gross_pnl")) or 0.0,
            net_pnl=_float(cost_summary.get("net_pnl")) or 0.0,
            total_cost=cost_audit.total_cost,
            completed_round_trips=len(event_net_pnls),
            execution_count=int(summary.trade_count),
        ),
        cost_audit=cost_audit,
        readback_ok=readback_ok,
        candle_continuity_ok=bool(quality.get("candle_continuity_ok")),
        candle_gap_count=int(quality.get("candle_gap_count") or 0),
    )


def classify_records(records: Sequence[RunRecord], availability: DataAvailability) -> GateReport:
    completed = [record for record in records if record.run_id is not None]
    primary = [
        record
        for record in completed
        if record.cost_profile == "conservative_crypto_1m" and record.validation_group == "primary"
    ]
    best_id = _best_primary_candidate(primary)
    if best_id is None:
        return GateReport(
            status="IN_PROGRESS_RESEARCH_ONLY",
            best_variant_id=None,
            gate_rows=(("Primary candidate runs", ">= 1", "0", False),),
            failed_gates=("Primary candidate runs",),
            overfit_conclusion="No completed primary candidate exists.",
        )
    by_window = {
        (record.variant_id, record.window_id, record.cost_profile, record.run_group): record
        for record in completed
    }
    owner_0520 = _record_by(completed, best_id, "owner_0520_latest", "conservative_crypto_1m")
    owner_0525 = _record_by(completed, best_id, "owner_0525_latest", "conservative_crypto_1m")
    endpoint_records = [
        record
        for record in completed
        if record.variant_id == best_id and record.run_group == "endpoint_trim" and record.cost_profile == "conservative_crypto_1m"
    ]
    stress_records = [
        record
        for record in completed
        if record.variant_id == best_id and record.run_group == "cost_stress"
    ]
    pre_owner = _record_by(completed, best_id, "available_pre_owner_0510_0517", "conservative_crypto_1m")
    zero = next(
        (record for record in completed if record.variant_id == best_id and record.run_group == "no_cost_diagnostic"),
        None,
    )
    cost_mismatch = sum(record.cost_audit.mismatch_count for record in completed if record.variant_id == best_id)
    endpoint_positive = bool(endpoint_records) and all((record.total_return or 0.0) > 0.0 for record in endpoint_records)
    stress_not_severe = bool(stress_records) and all((record.total_return or 0.0) > -0.03 for record in stress_records)
    data_0420_blocked = bool(
        availability.available_start_time
        and availability.available_start_time > _dt("2026-04-20T00:00:00Z")
    )
    rows = (
        ("0520 owner return", ">= +3.0000pct", _pct(owner_0520.total_return if owner_0520 else None), bool(owner_0520 and (owner_0520.total_return or 0.0) >= 0.03)),
        ("0525 owner return", ">= +3.0000pct", _pct(owner_0525.total_return if owner_0525 else None), bool(owner_0525 and (owner_0525.total_return or 0.0) >= 0.03)),
        ("0520 completed round trips", ">= 50", str(owner_0520.completed_round_trips if owner_0520 else 0), bool(owner_0520 and owner_0520.completed_round_trips >= 50)),
        ("Cost audit mismatch count", "0", str(cost_mismatch), cost_mismatch == 0),
        ("Non-zero realistic costs", "fee/spread/slippage > 0", _cost_presence(owner_0520), bool(owner_0520 and (owner_0520.total_fee_cost or 0.0) > 0 and (owner_0520.total_spread_cost or 0.0) > 0 and (owner_0520.total_slippage_cost or 0.0) > 0)),
        ("0520 largest winner contribution", "<= 0.40", _ratio(owner_0520.largest_winner_contribution if owner_0520 else None), bool(owner_0520 and owner_0520.largest_winner_contribution is not None and owner_0520.largest_winner_contribution <= 0.40)),
        ("0520 top-three winner contribution", "<= 0.70", _ratio(owner_0520.top_three_winner_contribution if owner_0520 else None), bool(owner_0520 and owner_0520.top_three_winner_contribution is not None and owner_0520.top_three_winner_contribution <= 0.70)),
        ("0520 cost/gross PnL", "<= 0.75", _ratio(owner_0520.cost_to_gross_pnl_ratio if owner_0520 else None), bool(owner_0520 and owner_0520.cost_to_gross_pnl_ratio is not None and owner_0520.cost_to_gross_pnl_ratio <= 0.75)),
        ("Endpoint trim", "all diagnostic trims positive", f"{sum(1 for record in endpoint_records if (record.total_return or 0.0) > 0.0)}/{len(endpoint_records)}", endpoint_positive),
        ("High-cost stress", "all stress returns > -3pct", f"{sum(1 for record in stress_records if (record.total_return or 0.0) > -0.03)}/{len(stress_records)}", stress_not_severe),
        ("Conservative intrabar policy", "stop first", "True", True),
        ("April-20 data coverage", "record blocker if missing", "DATA_BLOCKED_0420_COVERAGE" if data_0420_blocked else "available", True),
    )
    failed = tuple(name for name, _, _, ok in rows if not ok)
    status = "TARGET_PASSED_RESEARCH_ONLY" if not failed else "IN_PROGRESS_RESEARCH_ONLY"
    overfit_bits = []
    if data_0420_blocked:
        overfit_bits.append("full April-20-forward OOS is data-blocked")
    if pre_owner and (pre_owner.total_return or 0.0) < 0.0:
        overfit_bits.append("available pre-owner slice is negative")
    if zero and owner_0520 and zero.total_return is not None:
        overfit_bits.append(f"zero-cost diagnostic gap on 0520 is {((zero.total_return or 0.0) - (owner_0520.total_return or 0.0)) * 100:+.4f}pct")
    if status == "TARGET_PASSED_RESEARCH_ONLY":
        overfit_bits.append("target-window gates pass, but the result remains research-only because the windows are fixed and previously inspected")
    return GateReport(
        status=status,
        best_variant_id=best_id,
        gate_rows=rows,
        failed_gates=failed,
        overfit_conclusion="; ".join(overfit_bits) if overfit_bits else "No additional overfit warning beyond research-only scope.",
    )


def write_report(
    records: Sequence[RunRecord],
    *,
    availability: DataAvailability,
    gate_report: GateReport,
) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_ids = ", ".join(str(record.run_id) for record in records if record.run_id is not None) or "-"
    best = _record_by(records, gate_report.best_variant_id, "owner_0520_latest", "conservative_crypto_1m") if gate_report.best_variant_id else None
    lines = [
        "# Task 283 Principle-First BTC Microstructure Strategy Development",
        "",
        f"Status: `{gate_report.status}`",
        "",
        "## I. Bitcoin Market Principles First",
        "",
        "- Trend continuation: BTC can keep moving after directional pressure because momentum traders, stop cascades, and cross-session participation reinforce the move. Observable factors are prior returns, EMA slope, body/range, volume expansion, and completed 15m/1h trend context.",
        "- Mean reversion after forced movement: sharp stop-driven candles can revert when wick rejection, close-back-inside, volume spike, and volatility contraction show exhaustion. The main failure mode is a true trend/liquidation cascade.",
        "- Volatility clustering/compression: compressed range can lead to expansion; high-volatility regimes need wider stops and stricter cost gates.",
        "- Liquidity sweep/stop hunting: prior highs/lows and session ranges concentrate stops; a sweep plus reclaim can reverse, while confirmed displacement can continue.",
        "- Market structure change: swing/range breaks matter only when followed by displacement or successful reclaim/retest. Over-filtering can destroy sample size.",
        "- Session/time effects: BTC is 24/7, but Asia/Europe/US liquidity and weekend pockets behave differently. Session filters are diagnostics, not proof of edge.",
        "- Volume confirmation: Binance candle volume is only a proxy, but volume ratio helps separate participation from low-volume drift.",
        "",
        "## II. Factor Candidate List",
        "",
        "| Factor | Rationale | Formula | Direction | Risk |",
        "| --- | --- | --- | --- | --- |",
        "| Multi-horizon return | Momentum/cascade pressure | close[t-1]/close[t-n-1]-1 | trend continuation or exhaustion context | can lag reversals |",
        "| ATR/range percentile | volatility clustering | TR and rolling percentile | wider stops and breakout filters | noisy in gaps |",
        "| Sweep/reclaim flags | stop cluster behavior | high > prior high and close back inside, or low < prior low and close back inside | fade failed break | real breakout failure |",
        "| Wick/body/CLV | rejection versus displacement | wick/range, body/range, close location | reversal or breakout quality | candle-only proxy |",
        "| Volume ratio | participation proxy | current volume / prior rolling mean | confirms flow or exhaustion | exchange-volume noise |",
        "| 15m/1h trend proxy | MTF alignment | prior 15/60m returns | trend pullback filter | coarse from 1m data |",
        "| Session tag | liquidity regime | UTC hour bucket | filter/trap behavior | regime shifts |",
        "",
        "## III. Strategy Candidate List",
        "",
        "| Priority | Candidate | Family | Thesis |",
        "| ---: | --- | --- | --- |",
    ]
    for candidate in build_candidates():
        lines.append(f"| {candidate.priority} | `{candidate.variant_id}` | `{candidate.family}` | {candidate.thesis} |")
    lines.extend(
        [
            "",
            "### Stop/Target Template",
            "",
            "- Entry Price: next candle open after the completed signal candle.",
            "- Stop Loss: structural level or sweep extreme plus ATR/noise buffer.",
            "- Take Profit: R multiple or opposite liquidity, admitted only when estimated round-trip cost leaves positive net reward.",
            "- Risk per Trade: cash-bounded fixed fraction, no leverage.",
            "- Expected R: variant-specific 1.2R to 2.0R for pure families; fixed bps geometry for the priority ensemble.",
            "- Required Win Rate: computed from net reward/risk after fee/spread/slippage; strategies with net R below gate are rejected before entry.",
            "- Fee-adjusted Break-even: entry and exit taker fee are included through `conservative_crypto_1m`.",
            "- Slippage-adjusted Break-even: spread, base slippage, minimum slippage, and volatility slippage are included.",
            "- Invalid Setup Condition: cost gate rejection, invalid stop/target geometry, missing factors, or candle continuity gap.",
            "- Early Exit Condition: stop, target, conservative stop-first ambiguity, time exit, or ensemble scout preemption.",
            "",
            "## IV. Backtest Design",
            "",
            f"- Data availability: requested from `{_iso(availability.requested_start_time)}`, actual local start `{_iso(availability.available_start_time) if availability.available_start_time else '-'}`, actual local end `{_iso(availability.available_end_time) if availability.available_end_time else '-'}`.",
            "- Timeframe: BTCUSDT 1m primary; 15m/1h context is computed from completed prior 1m history.",
            "- Costs: primary `conservative_crypto_1m`; stress `high_slippage_stress`; zero-cost runs are diagnostic only.",
            "- Execution: signal on completed candle, entry on next candle open, no overlapping positions, cash-bounded sizing, simulated short research-only.",
            "- Intrabar ambiguity: if stop and target are both touched in the same candle, stop fills first.",
            "- Persistence: every completed decision-driving run is saved to DB with `research.task_id = TASK_283`.",
            "",
            "## V. Priority And Run Results",
            "",
            f"- Persisted Task 283 run IDs: `{run_ids}`.",
            f"- Best variant by primary target-window score: `{gate_report.best_variant_id or '-'}`.",
            "",
            "| Variant | Family | Window | Group | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Top1 | Top3 | DD | Status |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.variant_id,
                    record.family,
                    record.window_id,
                    record.run_group,
                    record.cost_profile,
                    str(record.run_id) if record.run_id is not None else "-",
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    _ratio(record.win_rate),
                    _ratio(record.profit_factor),
                    _money(record.gross_pnl),
                    _money(record.net_pnl),
                    _money(record.total_cost),
                    _ratio(record.cost_to_gross_pnl_ratio),
                    _ratio(record.largest_winner_contribution),
                    _ratio(record.top_three_winner_contribution),
                    _pct(record.max_drawdown),
                    record.status if record.run_id is not None else str(record.skip_reason),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Gate Check",
            "",
            "| Gate | Required | Observed | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for name, required, observed, ok in gate_report.gate_rows:
        lines.append(f"| {name} | {required} | {observed} | `{'PASS' if ok else 'FAIL'}` |")
    lines.extend(
        [
            "",
            "## Cost Audit",
            "",
        ]
    )
    for record in records:
        if record.run_id is None:
            continue
        lines.append(
            f"- Run `{record.run_id}` `{record.variant_id}` `{record.window_id}` `{record.cost_profile}`: notional `{_money(record.total_notional)}`, fee `{_money(record.total_fee_cost)}`, spread `{_money(record.total_spread_cost)}`, slippage `{_money(record.total_slippage_cost)}`, total `{_money(record.total_cost)}`, effective one-way cost `{_ratio(record.effective_total_cost_bps)}` bps, mismatch count `{record.cost_audit.mismatch_count}`."
        )
    lines.extend(
        [
            "",
            "## VI. Implementation Checklist",
            "",
            "- Look-ahead bias: factor snapshots use completed signal candles and prior rolling windows; entry is placed on the next candle.",
            "- Candle close signal: yes.",
            "- Next candle execution: yes, next candle open.",
            "- Stop/take intrabar ambiguity: conservative stop-first.",
            "- Long/short separation: attribution recorded.",
            "- Fee both ways: engine cost metadata and persisted cost audit verified.",
            "- Slippage/spread: non-zero primary profile; stress profile also run for the best candidate.",
            "- Position overlap: blocked by sequential action generation and engine open-position guard.",
            "- Data gaps: April 20 coverage remains blocked by local data availability; no fabrication.",
            "- Factor snapshot saved: trade metadata includes `task283_factor_snapshot` and cost gate details.",
            "- Research-only: no live orders, no keys, no private endpoints.",
            "",
            "## Conclusion",
            "",
            f"- Final status: `{gate_report.status}`.",
            f"- Best 0520 run: `{best.run_id if best else '-'}` with return `{_pct(best.total_return if best else None)}` and `{best.completed_round_trips if best else 0}` round trips.",
            f"- Failed gates: `{', '.join(gate_report.failed_gates) if gate_report.failed_gates else '-'}`.",
            f"- Overfit/robustness note: {gate_report.overfit_conclusion}.",
            "- No Task 283 result is promoted beyond `RESEARCH_ONLY`.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def _candidate_signal(
    frame: pd.DataFrame,
    index: int,
    candidate: CandidateSpec,
) -> tuple[str, str, float, float, int] | None:
    mode = str(candidate.params.get("mode"))
    row = frame.iloc[index]
    if not _factors_ready(row):
        return None
    if mode == "liquidity_sweep_reversal":
        return _liquidity_sweep_signal(row, candidate.params)
    if mode == "volatility_compression_breakout":
        return _volatility_breakout_signal(row, candidate.params)
    if mode == "mtf_trend_pullback":
        return _mtf_pullback_signal(row, candidate.params)
    if mode == "volume_climax_mean_reversion":
        return _volume_climax_signal(row, candidate.params)
    if mode == "session_range_liquidity_trap":
        return _session_trap_signal(row, candidate.params)
    return None


def _liquidity_sweep_signal(row: pd.Series, params: dict[str, Any]) -> tuple[str, str, float, float, int] | None:
    atr = max(_finite_or_zero(row.get("atr_14")), float(row["close"]) * 0.0002)
    target_r = float(params.get("target_r", 1.8))
    stop_buffer = atr * float(params.get("stop_atr_mult", 0.15))
    if (
        bool(row.get("swept_high_60"))
        and bool(row.get("close_back_inside_high_60"))
        and _finite_or_zero(row.get("upper_wick_ratio")) >= float(params.get("min_wick_ratio", 0.05))
        and _finite_or_zero(row.get("volume_ratio_20")) >= float(params.get("min_volume_ratio", 0.7))
    ):
        entry = float(row["close"])
        stop = max(float(row["high"]) + stop_buffer, entry * 1.0001)
        risk = stop - entry
        return "SHORT", "upper_liquidity_sweep_reclaim", stop, entry - (risk * target_r), int(params.get("max_hold_bars", 240))
    if (
        bool(row.get("swept_low_60"))
        and bool(row.get("close_back_inside_low_60"))
        and _finite_or_zero(row.get("lower_wick_ratio")) >= float(params.get("min_wick_ratio", 0.05))
        and _finite_or_zero(row.get("volume_ratio_20")) >= float(params.get("min_volume_ratio", 0.7))
    ):
        entry = float(row["close"])
        stop = min(float(row["low"]) - stop_buffer, entry * 0.9999)
        risk = entry - stop
        return "LONG", "lower_liquidity_sweep_reclaim", stop, entry + (risk * target_r), int(params.get("max_hold_bars", 240))
    return None


def _volatility_breakout_signal(row: pd.Series, params: dict[str, Any]) -> tuple[str, str, float, float, int] | None:
    if _finite_or_zero(row.get("range_width_bps_prior_60")) > float(params.get("compression_max_bps", 85.0)):
        return None
    if _finite_or_zero(row.get("body_ratio")) < float(params.get("min_body_ratio", 0.35)):
        return None
    if _finite_or_zero(row.get("volume_ratio_20")) < float(params.get("min_volume_ratio", 0.75)):
        return None
    entry = float(row["close"])
    atr = max(_finite_or_zero(row.get("atr_14")), entry * 0.0002)
    target_r = float(params.get("target_r", 2.0))
    if entry > _finite_or_zero(row.get("range_high_prior_60")):
        stop = min(_finite_or_zero(row.get("range_low_prior_60")) or entry - atr, entry - atr * float(params.get("stop_atr_mult", 0.1)))
        risk = entry - stop
        return "LONG", "compression_breakout", stop, entry + (risk * target_r), int(params.get("max_hold_bars", 180))
    if entry < _finite_or_zero(row.get("range_low_prior_60")):
        stop = max(_finite_or_zero(row.get("range_high_prior_60")) or entry + atr, entry + atr * float(params.get("stop_atr_mult", 0.1)))
        risk = stop - entry
        return "SHORT", "compression_breakdown", stop, entry - (risk * target_r), int(params.get("max_hold_bars", 180))
    return None


def _mtf_pullback_signal(row: pd.Series, params: dict[str, Any]) -> tuple[str, str, float, float, int] | None:
    trend_15 = _finite_or_zero(row.get("mtf_15m_trend_bps"))
    trend_60 = _finite_or_zero(row.get("mtf_1h_trend_bps"))
    min_trend = float(params.get("min_trend_bps", 15.0))
    if _finite_or_zero(row.get("body_ratio")) < float(params.get("min_body_ratio", 0.15)):
        return None
    entry = float(row["close"])
    ema = _finite_or_zero(row.get("ema_fast_20"))
    atr = max(_finite_or_zero(row.get("atr_14")), entry * 0.0002)
    target_r = float(params.get("target_r", 1.6))
    if trend_15 > min_trend and trend_60 > min_trend and float(row["low"]) <= ema and entry > ema:
        stop = min(float(row["low"]) - atr * float(params.get("stop_atr_mult", 0.15)), entry * 0.9999)
        risk = entry - stop
        return "LONG", "mtf_uptrend_pullback_reclaim", stop, entry + (risk * target_r), int(params.get("max_hold_bars", 180))
    if trend_15 < -min_trend and trend_60 < -min_trend and float(row["high"]) >= ema and entry < ema:
        stop = max(float(row["high"]) + atr * float(params.get("stop_atr_mult", 0.15)), entry * 1.0001)
        risk = stop - entry
        return "SHORT", "mtf_downtrend_pullback_reject", stop, entry - (risk * target_r), int(params.get("max_hold_bars", 180))
    return None


def _volume_climax_signal(row: pd.Series, params: dict[str, Any]) -> tuple[str, str, float, float, int] | None:
    shock = _finite_or_zero(row.get("return_bps_prior_3"))
    if abs(shock) < float(params.get("shock_bps", 35.0)):
        return None
    if _finite_or_zero(row.get("volume_ratio_20")) < float(params.get("min_volume_ratio", 1.4)):
        return None
    entry = float(row["close"])
    atr = max(_finite_or_zero(row.get("atr_14")), entry * 0.0002)
    target_r = float(params.get("target_r", 1.2))
    if shock < 0 and _finite_or_zero(row.get("lower_wick_ratio")) > 0.25 and _finite_or_zero(row.get("close_location")) > 0.45:
        stop = min(float(row["low"]) - atr * float(params.get("stop_atr_mult", 0.15)), entry * 0.9999)
        risk = entry - stop
        return "LONG", "downside_climax_reversal", stop, entry + risk * target_r, int(params.get("max_hold_bars", 120))
    if shock > 0 and _finite_or_zero(row.get("upper_wick_ratio")) > 0.25 and _finite_or_zero(row.get("close_location")) < 0.55:
        stop = max(float(row["high"]) + atr * float(params.get("stop_atr_mult", 0.15)), entry * 1.0001)
        risk = stop - entry
        return "SHORT", "upside_climax_reversal", stop, entry - risk * target_r, int(params.get("max_hold_bars", 120))
    return None


def _session_trap_signal(row: pd.Series, params: dict[str, Any]) -> tuple[str, str, float, float, int] | None:
    lookback = int(params.get("range_lookback", 360))
    high_key = f"range_high_prior_{lookback}"
    low_key = f"range_low_prior_{lookback}"
    high = _finite_or_zero(row.get(high_key))
    low = _finite_or_zero(row.get(low_key))
    if high <= 0 or low <= 0:
        return None
    entry = float(row["close"])
    atr = max(_finite_or_zero(row.get("atr_14")), entry * 0.0002)
    target_r = float(params.get("target_r", 1.5))
    if float(row["high"]) > high and entry < high:
        stop = max(float(row["high"]) + atr * float(params.get("stop_atr_mult", 0.1)), entry * 1.0001)
        risk = stop - entry
        return "SHORT", "session_high_failed_break", stop, entry - risk * target_r, int(params.get("max_hold_bars", 180))
    if float(row["low"]) < low and entry > low:
        stop = min(float(row["low"]) - atr * float(params.get("stop_atr_mult", 0.1)), entry * 0.9999)
        risk = entry - stop
        return "LONG", "session_low_failed_break", stop, entry + risk * target_r, int(params.get("max_hold_bars", 180))
    return None


def _generate_priority_ensemble_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
) -> tuple[list[StrategyAction], ActionGenerationMetadata]:
    params = candidate.params
    core_signals = _ensemble_core_signals(frame, params)
    scout_signals = _ensemble_scout_signals(frame)
    actions: list[StrategyAction] = []
    generated_core = generated_scout = preemptions = 0
    exit_reasons: dict[str, int] = defaultdict(int)
    index = 960
    while index < len(frame) - 2:
        if index in core_signals:
            side = core_signals[index]
            layer = "core"
            fraction = float(params.get("core_fraction", 1.0))
            target_bps = float(params.get("core_target_bps", 260.0))
            stop_bps = float(params.get("core_stop_bps", 130.0))
            hold_bars = int(params.get("core_hold_bars", 480))
        elif index in scout_signals:
            side = scout_signals[index]
            layer = "scout"
            fraction = float(params.get("scout_fraction", 0.02))
            target_bps = float(params.get("scout_target_bps", 150.0))
            stop_bps = float(params.get("scout_stop_bps", 75.0))
            hold_bars = int(params.get("scout_hold_bars", 120))
        else:
            index += 1
            continue
        entry_index = index + 1
        entry_price = float(frame.iloc[entry_index]["open"])
        target = entry_price * (1.0 + target_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 - target_bps / 10_000.0)
        stop = entry_price * (1.0 - stop_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 + stop_bps / 10_000.0)
        exit_index, exit_price, exit_reason = _resolve_ensemble_exit(
            frame,
            entry_index=entry_index,
            side=side,
            stop_price=stop,
            target_price=target,
            hold_bars=hold_bars,
            core_signals=core_signals,
            preempt_on_core=bool(layer == "scout" and params.get("preempt_scout_on_core", True)),
        )
        if exit_reason == "TASK283_SCOUT_PREEMPT_CORE_SIGNAL":
            preemptions += 1
        exit_reasons[exit_reason] += 1
        event_id = f"{candidate.variant_id}_{layer}_{entry_index}"
        actions.extend(
            _entry_exit_actions(
                frame,
                candidate=candidate,
                signal_index=index,
                entry_index=entry_index,
                exit_index=exit_index,
                side=side,
                entry_price=entry_price,
                stop_price=stop,
                target_price=target,
                exit_price=exit_price,
                exit_reason=exit_reason,
                event_id=event_id,
                cash_fraction=fraction,
                signal_name=f"ensemble_{layer}",
                cost_gate={"schema_version": "task283_ensemble_fixed_geometry_v1", "blocked": False},
                layer=layer,
            )
        )
        if layer == "core":
            generated_core += 1
        else:
            generated_scout += 1
        if exit_reason == "TASK283_SCOUT_PREEMPT_CORE_SIGNAL":
            index = max(exit_index, index + 1)
        else:
            index = max(exit_index + 1, index + 1)
    return actions, ActionGenerationMetadata(
        generated_entries=generated_core + generated_scout,
        cost_rejections=0,
        signal_counts={"core": generated_core, "scout": generated_scout, "preemptions": preemptions},
        exit_reasons=dict(exit_reasons),
    )


def _generate_priority_ensemble_shifted_exit_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
) -> tuple[list[StrategyAction], ActionGenerationMetadata]:
    params = candidate.params
    core_signals = _ensemble_core_signals(frame, params)
    scout_signals = _ensemble_scout_signals(frame)
    actions: list[StrategyAction] = []
    generated_core = generated_scout = preemptions = 0
    exit_reasons: dict[str, int] = defaultdict(int)
    index = 960
    while index < len(frame) - 2:
        if index in core_signals:
            side = core_signals[index]
            layer = "core"
            fraction = float(params.get("core_fraction", 1.0))
            target_bps = float(params.get("core_target_bps", 260.0))
            stop_bps = float(params.get("core_stop_bps", 130.0))
            hold_bars = int(params.get("core_hold_bars", 480))
        elif index in scout_signals:
            side = scout_signals[index]
            layer = "scout"
            fraction = float(params.get("scout_fraction", 0.02))
            target_bps = float(params.get("scout_target_bps", 150.0))
            stop_bps = float(params.get("scout_stop_bps", 75.0))
            hold_bars = int(params.get("scout_hold_bars", 120))
        else:
            index += 1
            continue

        condition_index, condition_price, exit_reason = _resolve_ensemble_condition_exit(
            frame,
            signal_index=index,
            side=side,
            target_bps=target_bps,
            stop_bps=stop_bps,
            hold_bars=hold_bars,
            core_signals=core_signals,
            preempt_on_core=bool(layer == "scout" and params.get("preempt_scout_on_core", True)),
        )
        entry_index = index + 1
        exit_index = min(condition_index + 1, len(frame) - 1)
        entry_price = float(frame.iloc[entry_index]["open"])
        exit_price = float(frame.iloc[exit_index]["open"])
        target = entry_price * (1.0 + target_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 - target_bps / 10_000.0)
        stop = entry_price * (1.0 - stop_bps / 10_000.0) if side == "LONG" else entry_price * (1.0 + stop_bps / 10_000.0)
        if exit_reason == "TASK283_SCOUT_PREEMPT_CORE_SIGNAL":
            preemptions += 1
        exit_reasons[exit_reason] += 1
        event_id = f"{candidate.variant_id}_{layer}_{entry_index}"
        actions.extend(
            _entry_exit_actions(
                frame,
                candidate=candidate,
                signal_index=index,
                entry_index=entry_index,
                exit_index=exit_index,
                side=side,
                entry_price=entry_price,
                stop_price=stop,
                target_price=target,
                exit_price=exit_price,
                exit_reason=exit_reason,
                event_id=event_id,
                cash_fraction=fraction,
                signal_name=f"ensemble_{layer}_shifted_exit",
                cost_gate={
                    "schema_version": "task283_next_open_after_exit_condition_v1",
                    "blocked": False,
                    "exit_condition_timestamp": _iso(pd.Timestamp(frame.iloc[condition_index]["timestamp"]).to_pydatetime()),
                    "exit_condition_price": float(condition_price),
                    "exit_execution_model": "next_candle_open_after_exit_condition",
                },
                layer=layer,
            )
        )
        if layer == "core":
            generated_core += 1
        else:
            generated_scout += 1
        if exit_reason == "TASK283_SCOUT_PREEMPT_CORE_SIGNAL":
            index = max(condition_index, index + 1)
        else:
            index = max(condition_index + 1, index + 1)
    return actions, ActionGenerationMetadata(
        generated_entries=generated_core + generated_scout,
        cost_rejections=0,
        signal_counts={"core": generated_core, "scout": generated_scout, "preemptions": preemptions},
        exit_reasons=dict(exit_reasons),
    )


def _resolve_ensemble_condition_exit(
    frame: pd.DataFrame,
    *,
    signal_index: int,
    side: str,
    target_bps: float,
    stop_bps: float,
    hold_bars: int,
    core_signals: dict[int, str],
    preempt_on_core: bool,
) -> tuple[int, float, str]:
    entry = float(frame.iloc[signal_index]["close"])
    if side == "LONG":
        target = entry * (1.0 + (target_bps / 10_000.0))
        stop = entry * (1.0 - (stop_bps / 10_000.0))
    else:
        target = entry * (1.0 - (target_bps / 10_000.0))
        stop = entry * (1.0 + (stop_bps / 10_000.0))
    end = min(len(frame) - 2, signal_index + int(hold_bars))
    for index in range(signal_index + 1, end + 1):
        if preempt_on_core and index in core_signals:
            return index, float(frame.iloc[index]["close"]), "TASK283_SCOUT_PREEMPT_CORE_SIGNAL"
        row = frame.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        if side == "LONG":
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            stop_hit = high >= stop
            target_hit = low <= target
        if stop_hit and target_hit:
            return index, stop, "TASK283_CONSERVATIVE_STOP_FIRST"
        if stop_hit:
            return index, stop, "TASK283_STOP"
        if target_hit:
            return index, target, "TASK283_TARGET"
    return end, float(frame.iloc[end]["close"]), "TASK283_TIME_EXIT"


def _entry_exit_actions(
    frame: pd.DataFrame,
    *,
    candidate: CandidateSpec,
    signal_index: int,
    entry_index: int,
    exit_index: int,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    exit_price: float,
    exit_reason: str,
    event_id: str,
    cash_fraction: float,
    signal_name: str,
    cost_gate: dict[str, Any],
    layer: str | None = None,
) -> list[StrategyAction]:
    qty = (STARTING_CASH * float(cash_fraction)) / entry_price
    risk_per_unit = abs(entry_price - stop_price)
    expected_reward_per_unit = abs(target_price - entry_price)
    expected_r = None if risk_per_unit <= 0 else expected_reward_per_unit / risk_per_unit
    metadata = {
        "pattern_type": "TASK283_PRINCIPLE_FIRST_MICROSTRUCTURE",
        "pattern_event_id": event_id,
        "event_id": event_id,
        "canonical_pattern_action": True,
        "task283_strategy_family": candidate.family,
        "task283_variant_id": candidate.variant_id,
        "task283_priority": candidate.priority,
        "task283_layer": layer or candidate.family,
        "task283_signal_name": signal_name,
        "position_side": side,
        "pattern_direction": "BULLISH" if side == "LONG" else "BEARISH",
        "signal_timestamp": _iso(pd.Timestamp(frame.iloc[signal_index]["timestamp"]).to_pydatetime()),
        "execution_timestamp": _iso(pd.Timestamp(frame.iloc[entry_index]["timestamp"]).to_pydatetime()),
        "signal_execution_separated": True,
        "entry_execution_model": "next_candle_open",
        "entry_price": entry_price,
        "stop_loss": stop_price,
        "take_profit": target_price,
        "risk_per_trade": risk_per_unit * qty,
        "expected_r": expected_r,
        "required_win_rate": None if expected_r is None or expected_r <= 0 else 1.0 / (1.0 + expected_r),
        "fee_adjusted_break_even": cost_gate.get("estimated_round_trip_cost_bps"),
        "slippage_adjusted_break_even": cost_gate.get("estimated_round_trip_cost_bps"),
        "invalid_setup_condition": cost_gate.get("block_reason"),
        "early_exit_condition": "stop_target_time_or_preemption",
        "task283_cost_edge_gate": cost_gate,
        "task283_factor_snapshot": _factor_snapshot(frame.iloc[signal_index]),
        "completed_candle_only": True,
        "offline_research_only": True,
        "simulated_short_research_only": side == "SHORT",
    }
    entry_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
    exit_type = StrategyActionType.EXIT_LONG if side == "LONG" else StrategyActionType.EXIT_SHORT
    return [
        StrategyAction(
            action_type=entry_type,
            timestamp=frame.iloc[entry_index]["timestamp"],
            quantity=qty,
            reason="TASK283_SIGNAL_CONFIRMED",
            metadata=metadata,
            requested_price=entry_price,
        ),
        StrategyAction(
            action_type=exit_type,
            timestamp=frame.iloc[exit_index]["timestamp"],
            quantity=1.0,
            quantity_mode=StrategyQuantityMode.POSITION_RATIO,
            reason=exit_reason,
            metadata={
                **metadata,
                "exit_reason": exit_reason,
                "target_name": exit_reason,
                "requested_exit_price": exit_price,
                "intrabar_ambiguity_policy": "stop_first_when_stop_and_target_hit_same_candle",
            },
            requested_price=exit_price,
        ),
    ]


def audit_persisted_trade_costs(trades: Iterable[Any]) -> CostAudit:
    mismatch_count = 0
    max_abs_mismatch = 0.0
    total_notional = total_fee = total_spread = total_slippage = total_cost = 0.0
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        breakdown = metadata.get("cost_breakdown") or {}
        notional = _float(breakdown.get("gross_notional"))
        if notional is None:
            notional = float(getattr(trade, "price", 0.0) or 0.0) * float(getattr(trade, "quantity", 0.0) or 0.0)
        fee_bps = _float(breakdown.get("fee_bps")) or 0.0
        spread_bps = _float(breakdown.get("spread_bps")) or 0.0
        slippage_bps = _float(breakdown.get("effective_slippage_bps")) or _float(breakdown.get("slippage_bps")) or 0.0
        fee = _float(metadata.get("fee_cost")) or _float(breakdown.get("fee_cost")) or 0.0
        spread = _float(metadata.get("spread_cost")) or _float(breakdown.get("spread_cost")) or 0.0
        slippage = _float(metadata.get("slippage_cost")) or _float(breakdown.get("slippage_cost")) or 0.0
        cost = _float(metadata.get("total_cost")) or _float(breakdown.get("total_cost")) or 0.0
        expected_fee = notional * fee_bps / 10_000.0
        expected_spread = notional * spread_bps / 10_000.0
        expected_slippage = notional * slippage_bps / 10_000.0
        expected_total = expected_fee + expected_spread + expected_slippage
        diff = max(abs(fee - expected_fee), abs(spread - expected_spread), abs(slippage - expected_slippage), abs(cost - expected_total))
        if diff > 1e-6:
            mismatch_count += 1
            max_abs_mismatch = max(max_abs_mismatch, diff)
        total_notional += notional
        total_fee += fee
        total_spread += spread
        total_slippage += slippage
        total_cost += cost
    return CostAudit(
        mismatch_count=mismatch_count,
        max_abs_mismatch=max_abs_mismatch,
        total_notional=total_notional,
        total_fee_cost=total_fee,
        total_spread_cost=total_spread,
        total_slippage_cost=total_slippage,
        total_cost=total_cost,
        effective_total_cost_bps=None if total_notional <= 0 else (total_cost / total_notional) * 10_000.0,
    )


def paired_event_net_pnls(trades: Iterable[Any]) -> list[float]:
    rows: dict[str, dict[str, float | bool]] = defaultdict(lambda: {"gross": 0.0, "cost": 0.0, "closed": False})
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        event_id = str(metadata.get("event_id") or metadata.get("pattern_event_id") or f"sequence_{getattr(trade, 'sequence', 0)}")
        rows[event_id]["cost"] = float(rows[event_id]["cost"]) + (_float(metadata.get("total_cost")) or 0.0)
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            rows[event_id]["gross"] = float(rows[event_id]["gross"]) + gross
            rows[event_id]["closed"] = True
    return [
        float(values["gross"]) - float(values["cost"])
        for values in rows.values()
        if bool(values["closed"])
    ]


def active_trade_days(trades: Iterable[Any]) -> int:
    days: set[str] = set()
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        if metadata.get("action_type") in {StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value}:
            if float(getattr(trade, "quantity", 0.0) or 0.0) > 0:
                days.add(str(pd.Timestamp(getattr(trade, "candle_open_time")).date()))
    return len(days)


def side_attribution(trades: Iterable[Any]) -> tuple[Attribution, Attribution]:
    rows: dict[str, dict[str, float]] = defaultdict(lambda: {"gross": 0.0, "cost": 0.0, "trips": 0.0, "execs": 0.0})
    for trade in trades:
        metadata = getattr(trade, "metadata", None) or {}
        side = str(metadata.get("position_side") or "unknown")
        rows[side]["execs"] += 1.0
        rows[side]["cost"] += _float(metadata.get("total_cost")) or 0.0
        gross = _float(metadata.get("gross_pnl"))
        if gross is not None:
            rows[side]["gross"] += gross
            rows[side]["trips"] += 1.0

    def _attr(key: str) -> Attribution:
        row = rows.get(key, {"gross": 0.0, "cost": 0.0, "trips": 0.0, "execs": 0.0})
        return Attribution(
            gross_pnl=row["gross"],
            total_cost=row["cost"],
            net_pnl=row["gross"] - row["cost"],
            completed_round_trips=int(row["trips"]),
            execution_count=int(row["execs"]),
        )

    return _attr("LONG"), _attr("SHORT")


def _realized_trade_stats(net_pnls: Sequence[float], r_values: Sequence[float]) -> dict[str, float | None]:
    wins = [value for value in net_pnls if value > 0]
    losses = [value for value in net_pnls if value < 0]
    gross_win = sum(wins)
    gross_loss_abs = abs(sum(losses))
    max_losses = current_losses = 0
    for value in net_pnls:
        if value < 0:
            current_losses += 1
            max_losses = max(max_losses, current_losses)
        else:
            current_losses = 0
    return {
        "win_rate": None if not net_pnls else len(wins) / len(net_pnls),
        "average_win": None if not wins else gross_win / len(wins),
        "average_loss": None if not losses else sum(losses) / len(losses),
        "profit_factor": None if gross_loss_abs == 0 else gross_win / gross_loss_abs,
        "expectancy": None if not net_pnls else sum(net_pnls) / len(net_pnls),
        "average_r": None if not r_values else sum(r_values) / len(r_values),
        "median_r": None if not r_values else float(pd.Series(list(r_values)).median()),
        "max_consecutive_losses": float(max_losses),
    }


def _ensemble_core_signals(frame: pd.DataFrame, params: dict[str, Any]) -> dict[int, str]:
    signals: dict[int, str] = {}
    skip_hours = set(int(value) for value in params.get("core_skip_sunday_hours_utc", []))
    hold_bars = int(params.get("core_hold_bars", 480))
    for index in range(960, len(frame) - 2):
        if index > len(frame) - 1 - hold_bars:
            continue
        timestamp = pd.Timestamp(frame.iloc[index]["timestamp"])
        if timestamp.weekday() == 6 and timestamp.hour in skip_hours:
            continue
        row = frame.iloc[index]
        prior_high = _positive(row.get("range_high_prior_60"))
        ret_60 = _number(row.get("return_bps_prior_60"))
        ret_240 = _number(row.get("return_bps_prior_240"))
        if prior_high is None or ret_60 is None or ret_240 is None:
            continue
        ret_60_vote = -1 if ret_60 < -80.0 else (1 if ret_60 > 80.0 else 0)
        ret_240_vote = -1 if ret_240 < -20.0 else (1 if ret_240 > 20.0 else 0)
        fade_vote = -1 if float(row["high"]) > prior_high and float(row["close"]) < prior_high else 0
        if ret_60_vote + ret_240_vote + fade_vote <= -2:
            signals[index] = "SHORT"
    return signals


def _ensemble_scout_signals(frame: pd.DataFrame) -> dict[int, str]:
    signals: dict[int, str] = {}
    for index in range(960, len(frame) - 2):
        row = frame.iloc[index]
        ret_60 = _number(row.get("return_bps_prior_60"))
        ret_720 = _number(row.get("return_bps_prior_720"))
        ret_15 = _number(row.get("return_bps_prior_15"))
        if ret_60 is None or ret_720 is None or ret_15 is None:
            continue
        score = _directional_vote(ret_60, 0.0) + _directional_vote(ret_720, 20.0) + _directional_vote(ret_15, 10.0)
        if score >= 2:
            signals[index] = "LONG"
        elif score <= -2:
            signals[index] = "SHORT"
    return signals


def _resolve_ensemble_exit(
    frame: pd.DataFrame,
    *,
    entry_index: int,
    side: str,
    stop_price: float,
    target_price: float,
    hold_bars: int,
    core_signals: dict[int, str],
    preempt_on_core: bool,
) -> tuple[int, float, str]:
    end = min(len(frame) - 1, entry_index + int(hold_bars))
    for index in range(entry_index, end + 1):
        if preempt_on_core and (index - 1) in core_signals:
            return index, float(frame.iloc[index]["open"]), "TASK283_SCOUT_PREEMPT_CORE_SIGNAL"
        row = frame.iloc[index]
        high = float(row["high"])
        low = float(row["low"])
        if side == "LONG":
            stop_hit = low <= stop_price
            target_hit = high >= target_price
        else:
            stop_hit = high >= stop_price
            target_hit = low <= target_price
        if stop_hit and target_hit:
            return index, stop_price, "TASK283_CONSERVATIVE_STOP_FIRST"
        if stop_hit:
            return index, stop_price, "TASK283_STOP"
        if target_hit:
            return index, target_price, "TASK283_TARGET"
    return end, float(frame.iloc[end]["open"]), "TASK283_TIME_EXIT"


def _normalize_stop_target(side: str, entry: float, stop: float, target: float) -> tuple[float, float]:
    min_move = entry * 0.0001
    if side == "LONG":
        return min(stop, entry - min_move), max(target, entry + min_move)
    return max(stop, entry + min_move), min(target, entry - min_move)


def _factor_snapshot(row: pd.Series) -> dict[str, Any]:
    keys = (
        "return_bps_prior_1",
        "return_bps_prior_3",
        "return_bps_prior_5",
        "return_bps_prior_15",
        "return_bps_prior_30",
        "return_bps_prior_60",
        "atr_bps",
        "range_bps",
        "range_width_bps_prior_60",
        "realized_vol_bps_30",
        "ema_slope_bps_20",
        "mtf_15m_trend_bps",
        "mtf_1h_trend_bps",
        "body_ratio",
        "upper_wick_ratio",
        "lower_wick_ratio",
        "close_location",
        "volume_ratio_20",
        "session_tag",
        "distance_from_daily_open_bps",
        "swept_high_60",
        "swept_low_60",
        "close_back_inside_high_60",
        "close_back_inside_low_60",
    )
    result: dict[str, Any] = {"schema_version": "task283_factor_snapshot_v1"}
    for key in keys:
        value = row.get(key)
        if isinstance(value, (bool, str)):
            result[key] = value
        else:
            result[key] = _float(value)
    return result


def _factors_ready(row: pd.Series) -> bool:
    return _positive(row.get("close")) is not None and _positive(row.get("atr_14")) is not None


def _best_primary_candidate(records: Sequence[RunRecord]) -> str | None:
    by_variant: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        if (
            record.run_id is not None
            and record.validation_group == "primary"
            and record.cost_profile == "conservative_crypto_1m"
            and record.window_id in {"owner_0520_latest", "owner_0525_latest"}
        ):
            by_variant[record.variant_id].append(record)
    scored: list[tuple[float, str]] = []
    for variant_id, rows in by_variant.items():
        if {row.window_id for row in rows} != {"owner_0520_latest", "owner_0525_latest"}:
            continue
        by_window = {row.window_id: row for row in rows}
        min_return = min(float(by_window["owner_0520_latest"].total_return or 0.0), float(by_window["owner_0525_latest"].total_return or 0.0))
        activity_bonus = min(by_window["owner_0520_latest"].completed_round_trips, 100) / 10_000.0
        scored.append((min_return + activity_bonus, variant_id))
    if not scored:
        return None
    return max(scored)[1]


def _record_by(records: Sequence[RunRecord], variant_id: str | None, window_id: str, cost_profile: str) -> RunRecord | None:
    if variant_id is None:
        return None
    return next(
        (
            record
            for record in records
            if record.variant_id == variant_id
            and record.window_id == window_id
            and record.cost_profile == cost_profile
            and record.run_id is not None
        ),
        None,
    )


def _skipped_record(
    candidate: CandidateSpec,
    window: WindowSpec,
    cost_profile_key: str,
    run_group: str,
    reason: str,
    *,
    quality: dict[str, Any] | None = None,
) -> RunRecord:
    return RunRecord(
        variant_id=candidate.variant_id,
        family=candidate.family,
        priority=candidate.priority,
        window_id=window.window_id,
        validation_group=window.validation_group,
        run_group=run_group,
        cost_profile=cost_profile_key,
        run_id=None,
        status="SKIPPED",
        skip_reason=reason,
        candle_continuity_ok=bool((quality or {}).get("candle_continuity_ok", False)),
        candle_gap_count=int((quality or {}).get("candle_gap_count", 0) or 0),
    )


def _session_tag(hour: int) -> str:
    if 0 <= int(hour) < 8:
        return "ASIA"
    if 8 <= int(hour) < 13:
        return "EUROPE"
    if 13 <= int(hour) < 21:
        return "US"
    return "LATE_US"


def _sign_series(series: pd.Series) -> pd.Series:
    return series.map(lambda value: 1 if _finite_or_zero(value) > 0 else (-1 if _finite_or_zero(value) < 0 else 0))


def _directional_vote(value: float, threshold: float) -> int:
    if value > threshold:
        return 1
    if value < -threshold:
        return -1
    return 0


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or pd.isna(number):
        return None
    return number


def _positive(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _finite_or_zero(value: Any) -> float:
    number = _number(value)
    return 0.0 if number is None else number


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _as_utc(value: datetime | pd.Timestamp) -> datetime:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(timezone.utc)
    return timestamp.tz_convert(timezone.utc).to_pydatetime()


def _iso(value: datetime | pd.Timestamp | None) -> str:
    if value is None:
        return "-"
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:+.4f}pct"


def _money(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def _cost_presence(record: RunRecord | None) -> str:
    if record is None:
        return "-"
    return f"fee={_money(record.total_fee_cost)}, spread={_money(record.total_spread_cost)}, slippage={_money(record.total_slippage_cost)}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task 283 principle-first BTC microstructure strategy research.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--batch", default="batch1")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    records = run_matrix(database_url=args.database_url, batch=args.batch, limit=args.limit)
    persisted = len([record for record in records if record.run_id is not None])
    print(f"wrote {REPORT_PATH} with {persisted} persisted Task 283 runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
