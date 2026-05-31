"""Task 280 iterative cost-aware BTCUSDT 1m model runner.

This module is offline-only research code. It consumes local candles, emits
deterministic strategy actions, runs the existing strategy engine, and persists
completed backtests. It does not fetch market data, read secrets, call exchange
APIs, place orders, or manage live positions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
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
    PostgresBacktestResultRepository,
    PostgresCandleRepository,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
)


TASK_ID = "TASK_280"
DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
REPORT_PATH = Path("reports/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md")
SOURCE = "binance_spot"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
STARTING_CASH = 1_000_000.0


@dataclass(frozen=True)
class CostGateConfig:
    min_reward_cost_multiple: float = 3.0
    min_net_reward_bps: float = 10.0
    min_net_rr: float = 0.75


@dataclass(frozen=True)
class CandidateSpec:
    variant_id: str
    track: str
    description: str
    params: dict[str, Any]


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    start_time: str
    end_time: str
    run_group: str


@dataclass(frozen=True)
class RunRecord:
    variant_id: str
    track: str
    window_id: str
    run_group: str
    cash_fraction: float
    cost_profile: str
    run_id: int
    total_return: float
    net_pnl: float | None
    gross_pnl: float | None
    total_cost: float | None
    trade_count: int
    completed_round_trips: int
    largest_winner_contribution: float | None
    top_three_winner_contribution: float | None
    generated_entries: int
    cost_rejections: int
    signal_count: int
    final_equity: float


def cost_edge_decision(
    *,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    volatility_bps: float,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig = CostGateConfig(),
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

    fee_bps = cost_config.taker_fee_bps
    slippage_bps = effective_slippage_bps(cost_config, volatility_bps)
    one_side_cost_bps = fee_bps + cost_config.spread_bps + slippage_bps
    round_trip_cost_bps = 2.0 * one_side_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    reward_cost_multiple = None if round_trip_cost_bps <= 0 else gross_reward_bps / round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    blocked = (
        gross_reward_bps <= 0
        or gross_risk_bps <= 0
        or reward_cost_multiple is None
        or reward_cost_multiple < gate.min_reward_cost_multiple
        or net_reward_bps < gate.min_net_reward_bps
        or net_rr is None
        or net_rr < gate.min_net_rr
    )
    return {
        "schema_version": "task280_cost_edge_gate_v1",
        "blocked": bool(blocked),
        "block_reason": "TASK280_COST_EDGE_GATE_REJECTED" if blocked else None,
        "side": normalized_side,
        "entry_price": float(entry_price),
        "stop_price": float(stop_price),
        "target_price": float(target_price),
        "gross_reward_bps": float(gross_reward_bps),
        "gross_risk_bps": float(gross_risk_bps),
        "fee_bps": float(fee_bps),
        "spread_bps": float(cost_config.spread_bps),
        "slippage_bps": float(slippage_bps),
        "volatility_bps": float(volatility_bps),
        "estimated_round_trip_cost_bps": float(round_trip_cost_bps),
        "reward_cost_multiple": reward_cost_multiple,
        "net_reward_bps": float(net_reward_bps),
        "net_risk_bps": float(net_risk_bps),
        "net_rr": net_rr,
        "min_reward_cost_multiple": float(gate.min_reward_cost_multiple),
        "min_net_reward_bps": float(gate.min_net_reward_bps),
        "min_net_rr": float(gate.min_net_rr),
    }


def build_candidates(batch: str = "batch1") -> tuple[CandidateSpec, ...]:
    if batch == "batch9":
        return _build_batch9_candidates()
    if batch == "batch8":
        return _build_batch8_candidates()
    if batch == "batch7":
        return _build_batch7_candidates()
    if batch == "batch6":
        return _build_batch6_candidates()
    if batch == "batch5":
        return _build_batch5_candidates()
    if batch == "batch4":
        return _build_batch4_candidates()
    if batch == "batch3":
        return _build_batch3_candidates()
    if batch == "batch2":
        return _build_batch2_candidates()
    if batch != "batch1":
        raise ValueError("supported batches: batch1, batch2, batch3, batch4, batch5, batch6, batch7, batch8, batch9")
    candidates: list[CandidateSpec] = []
    for lookback in (30, 60, 120):
        for target_r in (3.0, 5.0, 8.0):
            for volume_ratio in (1.0, 1.4):
                candidates.append(
                    CandidateSpec(
                        variant_id=(
                            f"T280_B1_VCB_LB{lookback}_TR{_token(target_r)}_VOL{_token(volume_ratio)}"
                        ),
                        track="VOLATILITY_COMPRESSION_BREAKOUT",
                        description="Compression-to-expansion breakout with no-overlap stop/target/time exits.",
                        params={
                            "track": "volatility_compression_breakout",
                            "range_lookback": lookback,
                            "compression_window": max(20, lookback // 2),
                            "compression_max_bps": 45.0 if lookback == 60 else 75.0,
                            "expansion_atr_mult": 1.15,
                            "min_body_ratio": 0.45,
                            "min_volume_ratio": volume_ratio,
                            "target_r": target_r,
                            "stop_atr_mult": 0.25,
                            "max_hold_bars": 180 if lookback == 60 else 300,
                            "direction_mode": "both",
                        },
                    )
                )
    for vwap_window in (120, 240):
        for target_r in (2.0, 3.0, 5.0):
            for dev_atr in (0.25, 0.50):
                candidates.append(
                    CandidateSpec(
                        variant_id=(
                            f"T280_B1_VWAP_W{vwap_window}_TR{_token(target_r)}_DEV{_token(dev_atr)}"
                        ),
                        track="VWAP_RECLAIM",
                        description="Rolling VWAP deviation reclaim/rejection with structure stop and R target.",
                        params={
                            "track": "vwap_reclaim",
                            "vwap_window": vwap_window,
                            "deviation_atr": dev_atr,
                            "min_body_ratio": 0.25,
                            "min_volume_ratio": 0.9,
                            "target_r": target_r,
                            "stop_atr_mult": 0.15,
                            "max_hold_bars": 240,
                            "direction_mode": "both",
                        },
                    )
                )
    return tuple(candidates)


def _build_batch2_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for fast, slow in ((20, 120), (50, 240)):
        for target_r in (3.0, 5.0, 8.0):
            for pullback_atr in (0.25, 0.75):
                candidates.append(
                    CandidateSpec(
                        variant_id=f"T280_B2_TP_FAST{fast}_SLOW{slow}_TR{_token(target_r)}_PB{_token(pullback_atr)}",
                        track="TREND_PULLBACK_CONTINUATION",
                        description="Completed-candle EMA trend pullback rejection with wide R target.",
                        params={
                            "track": "trend_pullback_continuation",
                            "ema_fast": fast,
                            "ema_slow": slow,
                            "pullback_atr": pullback_atr,
                            "min_body_ratio": 0.20,
                            "min_volume_ratio": 0.75,
                            "target_r": target_r,
                            "stop_atr_mult": 0.10,
                            "max_hold_bars": 480,
                            "direction_mode": "both",
                        },
                    )
                )
    for lookback in (30, 60, 120):
        for target_r in (3.0, 5.0, 8.0):
            for min_body in (0.20, 0.40):
                candidates.append(
                    CandidateSpec(
                        variant_id=f"T280_B2_RFADE_LB{lookback}_TR{_token(target_r)}_BODY{_token(min_body)}",
                        track="FAILED_RANGE_FADE",
                        description="Failed rolling-range breakout fade with structure stop and R target.",
                        params={
                            "track": "failed_range_fade",
                            "range_lookback": lookback,
                            "min_body_ratio": min_body,
                            "min_volume_ratio": 0.75,
                            "target_r": target_r,
                            "stop_atr_mult": 0.10,
                            "max_hold_bars": 300,
                            "direction_mode": "both",
                        },
                    )
                )
    return tuple(candidates)


def _build_batch3_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for lookback in (30, 60, 120):
        for target_r in (8.0, 12.0, 16.0):
            for min_body in (0.15, 0.35):
                candidates.append(
                    CandidateSpec(
                        variant_id=f"T280_B3_RBC_LB{lookback}_TR{_token(target_r)}_BODY{_token(min_body)}",
                        track="RANGE_BREAKOUT_CONTINUATION",
                        description="Rolling range breakout continuation with completed-candle close confirmation.",
                        params={
                            "track": "range_breakout_continuation",
                            "range_lookback": lookback,
                            "min_body_ratio": min_body,
                            "min_volume_ratio": 0.50,
                            "target_r": target_r,
                            "stop_atr_mult": 0.10,
                            "max_hold_bars": 720,
                            "direction_mode": "both",
                        },
                    )
                )
    for fast, slow in ((20, 120), (50, 240)):
        for target_r in (8.0, 12.0, 16.0):
            candidates.append(
                CandidateSpec(
                    variant_id=f"T280_B3_EMAB_FAST{fast}_SLOW{slow}_TR{_token(target_r)}",
                    track="EMA_RANGE_BREAKOUT",
                    description="EMA-regime rolling range breakout continuation.",
                    params={
                        "track": "ema_range_breakout",
                        "range_lookback": 60,
                        "ema_fast": fast,
                        "ema_slow": slow,
                        "min_body_ratio": 0.15,
                        "min_volume_ratio": 0.50,
                        "target_r": target_r,
                        "stop_atr_mult": 0.10,
                        "max_hold_bars": 720,
                        "direction_mode": "both",
                    },
                )
            )
    return tuple(candidates)


def _build_batch4_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for lookback in (60, 120, 240):
        for target_r in (1.0, 2.0, 3.0):
            for max_hold in (720, 1440):
                candidates.append(
                    CandidateSpec(
                        variant_id=f"T280_B4_RBCW_LB{lookback}_TR{_token(target_r)}_H{max_hold}",
                        track="RANGE_BREAKOUT_WIDE_STOP",
                        description="Range breakout continuation with opposite-range stop and long time hold.",
                        params={
                            "track": "range_breakout_continuation",
                            "range_lookback": lookback,
                            "min_body_ratio": 0.10,
                            "min_volume_ratio": 0.40,
                            "target_r": target_r,
                            "stop_atr_mult": 0.25,
                            "stop_mode": "opposite_range",
                            "max_hold_bars": max_hold,
                            "direction_mode": "both",
                        },
                    )
                )
    for fast, slow in ((20, 120), (50, 240)):
        for target_r in (1.0, 2.0, 3.0):
            for max_hold in (720, 1440):
                candidates.append(
                    CandidateSpec(
                        variant_id=f"T280_B4_EMAW_FAST{fast}_SLOW{slow}_TR{_token(target_r)}_H{max_hold}",
                        track="EMA_BREAKOUT_WIDE_STOP",
                        description="EMA-regime breakout continuation with opposite-range stop and long time hold.",
                        params={
                            "track": "ema_range_breakout",
                            "range_lookback": 120,
                            "ema_fast": fast,
                            "ema_slow": slow,
                            "min_body_ratio": 0.10,
                            "min_volume_ratio": 0.40,
                            "target_r": target_r,
                            "stop_atr_mult": 0.25,
                            "stop_mode": "opposite_range",
                            "max_hold_bars": max_hold,
                            "direction_mode": "both",
                        },
                    )
                )
    return tuple(candidates)


def _build_batch5_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for entry_mode, track_name in (
        ("pullback", "REGIME_FIXED_TARGET_PULLBACK"),
        ("momentum", "REGIME_FIXED_TARGET_MOMENTUM"),
    ):
        for trend_window, threshold_bps in ((240, 30.0), (720, 50.0), (1440, 80.0)):
            for target_bps, stop_bps in ((120.0, 60.0), (180.0, 90.0), (250.0, 120.0)):
                for max_hold in (240, 720):
                    candidates.append(
                        CandidateSpec(
                            variant_id=(
                                f"T280_B5_{entry_mode.upper()}_TW{trend_window}_TH{_token(threshold_bps)}"
                                f"_TG{_token(target_bps)}_ST{_token(stop_bps)}_H{max_hold}"
                            ),
                            track=track_name,
                            description="Rolling-return EMA regime entry with fixed bps target/stop.",
                            params={
                                "track": "regime_fixed_target",
                                "entry_mode": entry_mode,
                                "trend_window": trend_window,
                                "trend_threshold_bps": threshold_bps,
                                "ema_fast": 50,
                                "ema_slow": 240 if trend_window <= 720 else 720,
                                "target_bps": target_bps,
                                "stop_bps": stop_bps,
                                "max_hold_bars": max_hold,
                                "min_body_ratio": 0.10,
                                "min_volume_ratio": 0.40,
                                "min_net_rr": 0.50,
                                "direction_mode": "both",
                            },
                        )
                    )
    return tuple(candidates)


def _build_batch6_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for entry_mode in ("impulse", "breakdown"):
        for trend_window, threshold_bps in ((240, 15.0), (720, 30.0), (1440, 50.0)):
            for target_bps, stop_bps in ((120.0, 60.0), (180.0, 90.0), (250.0, 120.0)):
                for max_hold in (120, 240, 720):
                    candidates.append(
                        CandidateSpec(
                            variant_id=(
                                f"T280_B6_{entry_mode.upper()}_TW{trend_window}_TH{_token(threshold_bps)}"
                                f"_TG{_token(target_bps)}_ST{_token(stop_bps)}_H{max_hold}"
                            ),
                            track=f"SHORT_REGIME_FIXED_TARGET_{entry_mode.upper()}",
                            description="Short-only down-regime fixed target/stop with impulse or range-breakdown entry.",
                            params={
                                "track": "regime_fixed_target",
                                "entry_mode": entry_mode,
                                "trend_window": trend_window,
                                "trend_threshold_bps": threshold_bps,
                                "ema_fast": 50,
                                "ema_slow": 240 if trend_window <= 720 else 720,
                                "range_lookback": 60,
                                "target_bps": target_bps,
                                "stop_bps": stop_bps,
                                "max_hold_bars": max_hold,
                                "min_body_ratio": 0.08,
                                "min_volume_ratio": 0.30,
                                "min_net_rr": 0.50,
                                "direction_mode": "short_only",
                            },
                        )
                    )
    return tuple(candidates)


def _build_batch7_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for entry_mode in ("impulse", "breakdown"):
        for confirm_window, confirm_bps in ((360, 20.0), (720, 40.0)):
            for target_bps, stop_bps in ((120.0, 60.0), (180.0, 90.0), (250.0, 120.0)):
                for max_hold in (120, 240, 720):
                    candidates.append(
                        CandidateSpec(
                            variant_id=(
                                f"T280_B7_{entry_mode.upper()}_CW{confirm_window}_CB{_token(confirm_bps)}"
                                f"_TG{_token(target_bps)}_ST{_token(stop_bps)}_H{max_hold}"
                            ),
                            track=f"CONFIRMED_SHORT_FIXED_TARGET_{entry_mode.upper()}",
                            description="Short-only down-regime entry with prior completed-window down confirmation.",
                            params={
                                "track": "regime_fixed_target",
                                "entry_mode": entry_mode,
                                "trend_window": 720,
                                "trend_threshold_bps": 20.0,
                                "confirmation_window": confirm_window,
                                "confirmation_threshold_bps": confirm_bps,
                                "ema_fast": 50,
                                "ema_slow": 240,
                                "range_lookback": 60,
                                "target_bps": target_bps,
                                "stop_bps": stop_bps,
                                "max_hold_bars": max_hold,
                                "min_body_ratio": 0.08,
                                "min_volume_ratio": 0.30,
                                "min_net_rr": 0.50,
                                "direction_mode": "short_only",
                            },
                        )
                    )
    return tuple(candidates)


def _build_batch8_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for signal_mode in ("momentum", "reversal"):
        for direction_mode in ("both", "short_only"):
            for block_minutes in (120, 180, 240):
                for target_bps, stop_bps in ((120.0, 80.0), (180.0, 120.0), (250.0, 160.0)):
                    candidates.append(
                        CandidateSpec(
                            variant_id=(
                                f"T280_B8_{signal_mode.upper()}_{direction_mode.upper()}_B{block_minutes}"
                                f"_TG{_token(target_bps)}_ST{_token(stop_bps)}"
                            ),
                            track=f"BLOCK_{signal_mode.upper()}_{direction_mode.upper()}",
                            description="Completed time-block return direction with fixed target/stop and block hold.",
                            params={
                                "track": "block_return_hold",
                                "signal_mode": signal_mode,
                                "direction_mode": direction_mode,
                                "block_minutes": block_minutes,
                                "prev_return_threshold_bps": 30.0,
                                "target_bps": target_bps,
                                "stop_bps": stop_bps,
                                "max_hold_bars": block_minutes,
                                "min_net_rr": 0.50,
                            },
                        )
                    )
    return tuple(candidates)


def _build_batch9_candidates() -> tuple[CandidateSpec, ...]:
    candidates: list[CandidateSpec] = []
    for entry_mode in ("pullback", "momentum"):
        for trend_window, threshold_bps in ((240, 15.0), (720, 30.0)):
            for confirmation_window, confirmation_bps in ((0, 0.0), (360, 20.0)):
                for target_bps, stop_bps in ((120.0, 60.0), (180.0, 90.0), (250.0, 120.0)):
                    candidates.append(
                        CandidateSpec(
                            variant_id=(
                                f"T280_B9_{entry_mode.upper()}_TW{trend_window}_TH{_token(threshold_bps)}"
                                f"_CW{confirmation_window}_TG{_token(target_bps)}_ST{_token(stop_bps)}"
                            ),
                            track=f"SHORT_ONLY_{entry_mode.upper()}_RETUNED",
                            description="Retuned short-only EMA pullback/momentum candidate without long-side drag.",
                            params={
                                "track": "regime_fixed_target",
                                "entry_mode": entry_mode,
                                "trend_window": trend_window,
                                "trend_threshold_bps": threshold_bps,
                                "confirmation_window": confirmation_window,
                                "confirmation_threshold_bps": confirmation_bps,
                                "ema_fast": 50,
                                "ema_slow": 240,
                                "range_lookback": 60,
                                "target_bps": target_bps,
                                "stop_bps": stop_bps,
                                "max_hold_bars": 720,
                                "min_body_ratio": 0.08,
                                "min_volume_ratio": 0.30,
                                "min_net_rr": 0.50,
                                "direction_mode": "short_only",
                            },
                        )
                    )
    return tuple(candidates)


def build_windows() -> tuple[WindowSpec, ...]:
    end = "2026-05-28T08:26:00Z"
    return (
        WindowSpec("owner_a", "2026-05-20T00:00:00Z", end, "owner"),
        WindowSpec("owner_b", "2026-05-25T00:00:00Z", end, "owner"),
        WindowSpec("oos_1", "2026-05-10T00:00:00Z", "2026-05-14T00:00:00Z", "oos"),
        WindowSpec("oos_2", "2026-05-14T00:00:00Z", "2026-05-18T00:00:00Z", "oos"),
    )


def generate_actions(
    candles: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig = CostGateConfig(),
) -> tuple[list[StrategyAction], dict[str, Any]]:
    frame = _enrich(candles)
    params = candidate.params
    gate = _candidate_gate(candidate, gate)
    track = str(params["track"])
    if track == "volatility_compression_breakout":
        return _generate_vcb_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "vwap_reclaim":
        return _generate_vwap_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "trend_pullback_continuation":
        return _generate_trend_pullback_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "failed_range_fade":
        return _generate_range_fade_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "range_breakout_continuation":
        return _generate_range_breakout_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "ema_range_breakout":
        return _generate_range_breakout_actions(frame, candidate, cost_config=cost_config, gate=gate, require_ema_regime=True)
    if track == "regime_fixed_target":
        return _generate_regime_fixed_target_actions(frame, candidate, cost_config=cost_config, gate=gate)
    if track == "block_return_hold":
        return _generate_block_return_hold_actions(frame, candidate, cost_config=cost_config, gate=gate)
    raise ValueError(f"unsupported Task 280 track: {track}")


def run_matrix(
    *,
    database_url: str,
    limit: int | None = None,
    batch: str = "batch1",
) -> list[RunRecord]:
    records: list[RunRecord] = []
    candidates = build_candidates(batch)
    windows = build_windows()
    cost_profile_key = "conservative_crypto_1m"
    cost_config = COST_PROFILES[cost_profile_key].config
    plan_count = 0
    for candidate in candidates:
        for window in windows:
            if window.run_group == "oos":
                continue
            plan_count += 1
            if limit is not None and plan_count > limit:
                write_report(records, planned_candidates=len(candidates), batch=batch)
                return records
            record = run_one(
                database_url=database_url,
                candidate=candidate,
                window=window,
                cash_fraction=0.10,
                cost_profile_key=cost_profile_key,
                cost_config=cost_config,
                run_group=window.run_group,
            )
            records.append(record)
    write_report(records, planned_candidates=len(candidates), batch=batch)
    return records


def run_one(
    *,
    database_url: str,
    candidate: CandidateSpec,
    window: WindowSpec,
    cash_fraction: float,
    cost_profile_key: str,
    cost_config: TransactionCostConfig,
    run_group: str,
) -> RunRecord:
    candles = _load_candles(database_url, window)
    actions, action_metadata = generate_actions(candles, candidate, cost_config=cost_config)
    config = StrategyEngineConfig(
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        transaction_cost_config=cost_config,
        default_liquidity_role=LiquidityRole.TAKER,
        allow_short=True,
        interval=INTERVAL,
        position_sizing=PositionSizingConfig(
            mode=PositionSizingMode.CASH_FRACTION,
            value=float(cash_fraction),
            insufficient_funds_policy=InsufficientFundsPolicy.RESIZE,
        ),
        short_exposure_mode=ShortExposureMode.CASH_BOUNDED,
        enforce_candle_continuity=True,
    )
    result = run_strategy_backtest_engine(candles, actions, config=config)
    research = {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "scope": "offline_backtest_research_only",
        "task_id": TASK_ID,
        "variant_id": candidate.variant_id,
        "window_id": window.window_id,
        "run_group": run_group,
        "batch": _candidate_batch(candidate),
    }
    if isinstance(result.summary.metadata, dict):
        result.summary.metadata["research"] = research
        result.summary.metadata["task280_action_generation"] = action_metadata
        result.summary.metadata["cost_profile"] = COST_PROFILES[cost_profile_key].to_metadata()
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=_dt(window.start_time),
        end_time=_dt(window.end_time),
        strategy_key="task280_cost_aware_multi_trade",
        strategy_name="TASK280_COST_AWARE_MULTI_TRADE_MODEL",
        strategy_version=f"task280_{_candidate_batch(candidate)}_v1",
        strategy_parameters={
            "candidate": candidate.variant_id,
            "track": candidate.track,
            "params": candidate.params,
            "cost_profile": COST_PROFILES[cost_profile_key].to_metadata(),
            "cost_profile_key": cost_profile_key,
            "cash_fraction": cash_fraction,
            "research": research,
        },
        starting_cash=STARTING_CASH,
        trade_quantity=1.0,
        engine_name="StrategyEngine",
        engine_version="strategy_engine_v1",
        run_metadata={
            "research": research,
            "cost_profile": COST_PROFILES[cost_profile_key].to_metadata(),
            "task280_action_generation": action_metadata,
        },
    )
    run_id = PostgresBacktestResultRepository(database_url).save_completed_backtest(payload)
    closing_net = _closing_net_pnls(result)
    contribution = trade_contribution_metrics(closing_net)
    return RunRecord(
        variant_id=candidate.variant_id,
        track=candidate.track,
        window_id=window.window_id,
        run_group=run_group,
        cash_fraction=cash_fraction,
        cost_profile=cost_profile_key,
        run_id=run_id,
        total_return=float(result.summary.total_return),
        net_pnl=_summary_float(result.summary.metadata, "net_pnl"),
        gross_pnl=_summary_float(result.summary.metadata, "gross_pnl"),
        total_cost=_summary_float_nested(result.summary.metadata, ("cost_summary", "total_cost")),
        trade_count=int(result.summary.trade_count),
        completed_round_trips=len(closing_net),
        largest_winner_contribution=contribution.largest_winner_contribution,
        top_three_winner_contribution=contribution.top_three_winner_contribution,
        generated_entries=int(action_metadata.get("generated_entries", 0)),
        cost_rejections=int(action_metadata.get("cost_rejections", 0)),
        signal_count=int(action_metadata.get("signal_count", 0)),
        final_equity=float(result.summary.final_equity),
    )


def write_report(records: Sequence[RunRecord], *, planned_candidates: int, batch: str) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task 280 Cost-Aware Multi-Trade Model Development",
        "",
        "Status: `IN_PROGRESS_RESEARCH_ONLY`",
        "",
        "## Iteration State",
        "",
        f"- Batch: `{batch}`",
        f"- Planned candidates in batch: `{planned_candidates}`",
        f"- Persisted runs in this invocation: `{len(records)}`",
        "- Loop policy: continue inside Task 280 until a candidate passes, a hard blocker appears, or the owner pauses.",
        "",
        "## Runs",
        "",
        "| Variant | Track | Window | Run | Return | Trips | Trades | Cost | Entries | Cost Rejects |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    record.variant_id,
                    record.track,
                    record.window_id,
                    str(record.run_id),
                    _pct(record.total_return),
                    str(record.completed_round_trips),
                    str(record.trade_count),
                    _money(record.total_cost),
                    str(record.generated_entries),
                    str(record.cost_rejections),
                ]
            )
            + " |"
        )
    owner_records = [r for r in records if r.run_group == "owner"]
    best = max(owner_records, key=lambda r: r.total_return, default=None)
    lines.extend(["", "## Current Best", ""])
    if best is None:
        lines.append("- No owner-window runs were persisted in this invocation.")
    else:
        lines.append(
            f"- Best single owner-window run so far in this invocation: run `{best.run_id}` "
            f"`{best.variant_id}` on `{best.window_id}` at `{_pct(best.total_return)}`."
        )
        lines.append("- This is not a final pass/fail report; continue the in-task loop.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def _generate_vcb_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    range_lookback = int(p["range_lookback"])
    compression_window = int(p["compression_window"])
    target_r = float(p["target_r"])
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    max_hold = int(p["max_hold_bars"])
    stop_atr_mult = float(p["stop_atr_mult"])
    actions: list[StrategyAction] = []
    index = max(range_lookback, compression_window, 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        entry = float(row["close"])
        atr = _positive(row.get("atr_prior"))
        if atr is None:
            index += 1
            continue
        compression_window = int(p["compression_window"])
        prior_high = float(row[f"range_high_prior_{range_lookback}"])
        prior_low = float(row[f"range_low_prior_{range_lookback}"])
        prior_range_bps = float(row[f"compression_range_bps_{compression_window}"])
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        side: str | None = None
        if (
            prior_range_bps <= float(p["compression_max_bps"])
            and float(row["range_bps"]) >= float(p["expansion_atr_mult"]) * float(row["atr_bps_prior"])
            and body_ratio >= min_body_ratio
            and volume_ratio >= min_volume_ratio
        ):
            if entry > prior_high and float(row["close"]) > float(row["open"]):
                side = "LONG"
            elif entry < prior_low and float(row["close"]) < float(row["open"]):
                side = "SHORT"
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            stop = min(float(row["low"]), entry - (atr * stop_atr_mult))
            risk = entry - stop
            target = entry + (risk * target_r)
        else:
            stop = max(float(row["high"]), entry + (atr * stop_atr_mult))
            risk = stop - entry
            target = entry - (risk * target_r)
        if risk <= 0 or target <= 0:
            index += 1
            continue
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_vwap_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    vwap_window = int(p["vwap_window"])
    target_r = float(p["target_r"])
    dev_atr = float(p["deviation_atr"])
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    max_hold = int(p["max_hold_bars"])
    stop_atr_mult = float(p["stop_atr_mult"])
    actions: list[StrategyAction] = []
    index = max(vwap_window, 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        prev = frame.iloc[index - 1]
        entry = float(row["close"])
        atr = _positive(row.get("atr_prior"))
        vwap = _positive(row.get(f"vwap_{vwap_window}_prior"))
        if atr is None or vwap is None:
            index += 1
            continue
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        side: str | None = None
        if body_ratio >= min_body_ratio and volume_ratio >= min_volume_ratio:
            lower_band = vwap - (atr * dev_atr)
            upper_band = vwap + (atr * dev_atr)
            if float(prev["close"]) < lower_band and entry > vwap and float(row["close"]) > float(row["open"]):
                side = "LONG"
            elif float(prev["close"]) > upper_band and entry < vwap and float(row["close"]) < float(row["open"]):
                side = "SHORT"
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            stop = min(float(row["low"]), vwap - (atr * stop_atr_mult))
            risk = entry - stop
            target = entry + (risk * target_r)
        else:
            stop = max(float(row["high"]), vwap + (atr * stop_atr_mult))
            risk = stop - entry
            target = entry - (risk * target_r)
        if risk <= 0 or target <= 0:
            index += 1
            continue
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_trend_pullback_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    fast = int(p["ema_fast"])
    slow = int(p["ema_slow"])
    pullback_atr = float(p["pullback_atr"])
    target_r = float(p["target_r"])
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    max_hold = int(p["max_hold_bars"])
    stop_atr_mult = float(p["stop_atr_mult"])
    actions: list[StrategyAction] = []
    index = max(slow, 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        entry = float(row["close"])
        atr = _positive(row.get("atr_prior"))
        ema_fast = _positive(row.get(f"ema_{fast}_prior"))
        ema_slow = _positive(row.get(f"ema_{slow}_prior"))
        if atr is None or ema_fast is None or ema_slow is None:
            index += 1
            continue
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        side: str | None = None
        if body_ratio >= min_body_ratio and volume_ratio >= min_volume_ratio:
            if (
                ema_fast < ema_slow
                and float(row["high"]) >= ema_fast - (atr * pullback_atr)
                and entry < ema_fast
                and float(row["close"]) < float(row["open"])
            ):
                side = "SHORT"
            elif (
                ema_fast > ema_slow
                and float(row["low"]) <= ema_fast + (atr * pullback_atr)
                and entry > ema_fast
                and float(row["close"]) > float(row["open"])
            ):
                side = "LONG"
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            stop = min(float(row["low"]), entry - (atr * stop_atr_mult))
            risk = entry - stop
            target = entry + (risk * target_r)
        else:
            stop = max(float(row["high"]), entry + (atr * stop_atr_mult))
            risk = stop - entry
            target = entry - (risk * target_r)
        if risk <= 0 or target <= 0:
            index += 1
            continue
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_range_fade_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    range_lookback = int(p["range_lookback"])
    target_r = float(p["target_r"])
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    max_hold = int(p["max_hold_bars"])
    stop_atr_mult = float(p["stop_atr_mult"])
    actions: list[StrategyAction] = []
    index = max(range_lookback, 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        entry = float(row["close"])
        atr = _positive(row.get("atr_prior"))
        if atr is None:
            index += 1
            continue
        prior_high = float(row[f"range_high_prior_{range_lookback}"])
        prior_low = float(row[f"range_low_prior_{range_lookback}"])
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        side: str | None = None
        if body_ratio >= min_body_ratio and volume_ratio >= min_volume_ratio:
            if float(row["high"]) > prior_high and entry < prior_high and float(row["close"]) < float(row["open"]):
                side = "SHORT"
            elif float(row["low"]) < prior_low and entry > prior_low and float(row["close"]) > float(row["open"]):
                side = "LONG"
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            stop = min(float(row["low"]), prior_low) - (atr * stop_atr_mult)
            risk = entry - stop
            target = entry + (risk * target_r)
        else:
            stop = max(float(row["high"]), prior_high) + (atr * stop_atr_mult)
            risk = stop - entry
            target = entry - (risk * target_r)
        if risk <= 0 or target <= 0:
            index += 1
            continue
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_range_breakout_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
    require_ema_regime: bool = False,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    range_lookback = int(p["range_lookback"])
    target_r = float(p["target_r"])
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    max_hold = int(p["max_hold_bars"])
    stop_atr_mult = float(p["stop_atr_mult"])
    stop_mode = str(p.get("stop_mode", "breakout_edge"))
    fast = int(p.get("ema_fast", 20))
    slow = int(p.get("ema_slow", 120))
    actions: list[StrategyAction] = []
    index = max(range_lookback, slow if require_ema_regime else 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        entry = float(row["close"])
        atr = _positive(row.get("atr_prior"))
        if atr is None:
            index += 1
            continue
        prior_high = float(row[f"range_high_prior_{range_lookback}"])
        prior_low = float(row[f"range_low_prior_{range_lookback}"])
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        side: str | None = None
        if body_ratio >= min_body_ratio and volume_ratio >= min_volume_ratio:
            if entry > prior_high and float(row["close"]) > float(row["open"]):
                side = "LONG"
            elif entry < prior_low and float(row["close"]) < float(row["open"]):
                side = "SHORT"
        if side is not None and require_ema_regime:
            ema_fast = _positive(row.get(f"ema_{fast}_prior"))
            ema_slow = _positive(row.get(f"ema_{slow}_prior"))
            if ema_fast is None or ema_slow is None:
                side = None
            elif side == "LONG" and not ema_fast > ema_slow:
                side = None
            elif side == "SHORT" and not ema_fast < ema_slow:
                side = None
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            if stop_mode == "opposite_range":
                stop = prior_low - (atr * stop_atr_mult)
            else:
                stop = min(float(row["low"]), prior_high) - (atr * stop_atr_mult)
            risk = entry - stop
            target = entry + (risk * target_r)
        else:
            if stop_mode == "opposite_range":
                stop = prior_high + (atr * stop_atr_mult)
            else:
                stop = max(float(row["high"]), prior_low) + (atr * stop_atr_mult)
            risk = stop - entry
            target = entry - (risk * target_r)
        if risk <= 0 or target <= 0:
            index += 1
            continue
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_regime_fixed_target_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    entry_mode = str(p["entry_mode"])
    trend_window = int(p["trend_window"])
    trend_threshold_bps = float(p["trend_threshold_bps"])
    fast = int(p["ema_fast"])
    slow = int(p["ema_slow"])
    target_bps = float(p["target_bps"])
    stop_bps = float(p["stop_bps"])
    max_hold = int(p["max_hold_bars"])
    range_lookback = int(p.get("range_lookback", 60))
    confirmation_window = int(p.get("confirmation_window", 0))
    confirmation_threshold_bps = float(p.get("confirmation_threshold_bps", 0.0))
    min_volume_ratio = float(p["min_volume_ratio"])
    min_body_ratio = float(p["min_body_ratio"])
    direction_mode = str(p.get("direction_mode", "both"))
    actions: list[StrategyAction] = []
    index = max(trend_window, slow, range_lookback, confirmation_window, 30)
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    while index < len(frame) - 2:
        row = frame.iloc[index]
        prev = frame.iloc[index - 1]
        entry = float(row["close"])
        past_close = _positive(frame.iloc[index - trend_window]["close"])
        ema_fast = _positive(row.get(f"ema_{fast}_prior"))
        ema_slow = _positive(row.get(f"ema_{slow}_prior"))
        prev_ema_fast = _positive(prev.get(f"ema_{fast}_prior"))
        if past_close is None or ema_fast is None or ema_slow is None or prev_ema_fast is None:
            index += 1
            continue
        trend_return_bps = ((entry / past_close) - 1.0) * 10_000.0
        body_ratio = float(row["body_ratio"])
        volume_ratio = float(row["volume_ratio_prior"])
        if body_ratio < min_body_ratio or volume_ratio < min_volume_ratio:
            index += 1
            continue
        allow_long = direction_mode in {"both", "long_only"}
        allow_short = direction_mode in {"both", "short_only"}
        up_regime = (
            allow_long
            and trend_return_bps >= trend_threshold_bps
            and entry > ema_slow
            and ema_fast > ema_slow
        )
        down_regime = (
            allow_short
            and trend_return_bps <= -trend_threshold_bps
            and entry < ema_slow
            and ema_fast < ema_slow
        )
        if confirmation_window > 0:
            confirmation_return = _positive_or_negative(row.get(f"return_bps_prior_{confirmation_window}"))
            if confirmation_return is None:
                index += 1
                continue
            if allow_long and up_regime and confirmation_return < confirmation_threshold_bps:
                up_regime = False
            if allow_short and down_regime and confirmation_return > -confirmation_threshold_bps:
                down_regime = False
        side: str | None = None
        if entry_mode == "pullback":
            if (
                down_regime
                and float(row["high"]) >= ema_fast
                and entry < ema_fast
                and float(row["close"]) < float(row["open"])
            ):
                side = "SHORT"
            elif (
                up_regime
                and float(row["low"]) <= ema_fast
                and entry > ema_fast
                and float(row["close"]) > float(row["open"])
            ):
                side = "LONG"
        elif entry_mode == "momentum":
            if (
                down_regime
                and float(prev["close"]) >= prev_ema_fast
                and entry < ema_fast
                and float(row["close"]) < float(row["open"])
            ):
                side = "SHORT"
            elif (
                up_regime
                and float(prev["close"]) <= prev_ema_fast
                and entry > ema_fast
                and float(row["close"]) > float(row["open"])
            ):
                side = "LONG"
        elif entry_mode == "impulse":
            if down_regime and entry < ema_fast and float(row["close"]) < float(row["open"]):
                side = "SHORT"
            elif up_regime and entry > ema_fast and float(row["close"]) > float(row["open"]):
                side = "LONG"
        elif entry_mode == "breakdown":
            prior_low = float(row[f"range_low_prior_{range_lookback}"])
            prior_high = float(row[f"range_high_prior_{range_lookback}"])
            if down_regime and entry < prior_low and float(row["close"]) < float(row["open"]):
                side = "SHORT"
            elif up_regime and entry > prior_high and float(row["close"]) > float(row["open"]):
                side = "LONG"
        else:
            raise ValueError(f"unsupported batch5 entry_mode: {entry_mode}")
        if side is None:
            index += 1
            continue
        signal_count += 1
        if side == "LONG":
            stop = entry * (1.0 - (stop_bps / 10_000.0))
            target = entry * (1.0 + (target_bps / 10_000.0))
        else:
            stop = entry * (1.0 + (stop_bps / 10_000.0))
            target = entry * (1.0 - (target_bps / 10_000.0))
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            index += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
        index = max(exit_index + 1, index + 1)
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "entry_mode": entry_mode,
        "trend_window": trend_window,
        "trend_threshold_bps": trend_threshold_bps,
        "confirmation_window": confirmation_window,
        "confirmation_threshold_bps": confirmation_threshold_bps,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _generate_block_return_hold_actions(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    *,
    cost_config: TransactionCostConfig,
    gate: CostGateConfig,
) -> tuple[list[StrategyAction], dict[str, Any]]:
    p = candidate.params
    signal_mode = str(p["signal_mode"])
    direction_mode = str(p["direction_mode"])
    block_minutes = int(p["block_minutes"])
    threshold_bps = float(p["prev_return_threshold_bps"])
    target_bps = float(p["target_bps"])
    stop_bps = float(p["stop_bps"])
    max_hold = int(p["max_hold_bars"])
    block_seconds = block_minutes * 60
    working = frame.copy(deep=False)
    timestamps = pd.to_datetime(working["timestamp"], utc=True)
    working = working.assign(
        _block_id=(timestamps.astype("int64") // (block_seconds * 1_000_000_000)).astype("int64")
    )
    grouped = working.groupby("_block_id", sort=True)
    block_first_close = grouped["close"].first().astype(float)
    block_last_close = grouped["close"].last().astype(float)
    block_return_bps = ((block_last_close / block_first_close) - 1.0) * 10_000.0
    block_start_indices = grouped.apply(lambda item: int(item.index[0]), include_groups=False).to_dict()
    actions: list[StrategyAction] = []
    signal_count = 0
    cost_rejections = 0
    generated_entries = 0
    for block_id in sorted(block_start_indices):
        prev_return = block_return_bps.get(block_id - 1)
        if prev_return is None or pd.isna(prev_return) or abs(float(prev_return)) < threshold_bps:
            continue
        index = int(block_start_indices[block_id])
        if index >= len(frame) - 2:
            continue
        row = frame.iloc[index]
        entry = float(row["close"])
        side: str | None = None
        if signal_mode == "momentum":
            side = "LONG" if float(prev_return) > 0 else "SHORT"
        elif signal_mode == "reversal":
            side = "SHORT" if float(prev_return) > 0 else "LONG"
        else:
            raise ValueError(f"unsupported block signal_mode: {signal_mode}")
        if direction_mode == "short_only" and side != "SHORT":
            continue
        if direction_mode == "long_only" and side != "LONG":
            continue
        signal_count += 1
        if side == "LONG":
            stop = entry * (1.0 - (stop_bps / 10_000.0))
            target = entry * (1.0 + (target_bps / 10_000.0))
        else:
            stop = entry * (1.0 + (stop_bps / 10_000.0))
            target = entry * (1.0 - (target_bps / 10_000.0))
        decision = cost_edge_decision(
            side=side,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            volatility_bps=float(row["range_bps"]),
            cost_config=cost_config,
            gate=gate,
        )
        if decision["blocked"]:
            cost_rejections += 1
            continue
        exit_index, exit_price, exit_reason = _resolve_exit(frame, index + 1, side, stop, target, max_hold)
        event_id = f"{candidate.variant_id}_{index}"
        actions.extend(_entry_exit_actions(frame, index, exit_index, side, entry, exit_price, event_id, candidate, decision, exit_reason))
        generated_entries += 1
    return actions, {
        "schema_version": "task280_action_generation_v1",
        "track": candidate.track,
        "variant_id": candidate.variant_id,
        "signal_mode": signal_mode,
        "direction_mode": direction_mode,
        "block_minutes": block_minutes,
        "prev_return_threshold_bps": threshold_bps,
        "signal_count": signal_count,
        "cost_rejections": cost_rejections,
        "generated_entries": generated_entries,
    }


def _entry_exit_actions(
    frame: pd.DataFrame,
    entry_index: int,
    exit_index: int,
    side: str,
    entry_price: float,
    exit_price: float,
    event_id: str,
    candidate: CandidateSpec,
    cost_decision: dict[str, Any],
    exit_reason: str,
) -> list[StrategyAction]:
    entry_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
    exit_type = StrategyActionType.EXIT_LONG if side == "LONG" else StrategyActionType.EXIT_SHORT
    stop_price = float(cost_decision["stop_price"])
    metadata = {
        "pattern_type": "TASK280_COST_AWARE_MULTI_TRADE",
        "pattern_event_id": event_id,
        "event_id": event_id,
        "position_side": side,
        "pattern_direction": "BULLISH" if side == "LONG" else "BEARISH",
        "strategy_variant_id": candidate.variant_id,
        "task280_track": candidate.track,
        "entry_price": entry_price,
        "risk_per_unit": abs(entry_price - stop_price),
        "cost_edge_gate": cost_decision,
    }
    return [
        StrategyAction(
            action_type=entry_type,
            timestamp=frame.iloc[entry_index]["timestamp"],
            reason="TASK280_SIGNAL_CONFIRMED",
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
            },
            requested_price=exit_price,
        ),
    ]


def _resolve_exit(
    frame: pd.DataFrame,
    start_index: int,
    side: str,
    stop: float,
    target: float,
    max_hold: int,
) -> tuple[int, float, str]:
    end = min(len(frame) - 1, start_index + max_hold)
    for index in range(start_index, end + 1):
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
            return index, stop, "TASK280_CONSERVATIVE_STOP_FIRST"
        if stop_hit:
            return index, stop, "TASK280_STOP"
        if target_hit:
            return index, target, "TASK280_TARGET"
    return end, float(frame.iloc[end]["close"]), "TASK280_TIME_STOP"


def _enrich(candles: pd.DataFrame) -> pd.DataFrame:
    frame = candles.copy(deep=True).reset_index(drop=True)
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = frame[col].astype(float)
    previous_close = frame["close"].shift(1)
    tr = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr_prior"] = tr.rolling(14, min_periods=14).mean().shift(1)
    frame["range_bps"] = ((frame["high"] - frame["low"]) / frame["close"]) * 10_000.0
    frame["atr_bps_prior"] = (frame["atr_prior"] / frame["close"]) * 10_000.0
    body = (frame["close"] - frame["open"]).abs()
    candle_range = (frame["high"] - frame["low"]).replace(0, pd.NA)
    frame["body_ratio"] = (body / candle_range).fillna(0.0)
    frame["volume_ratio_prior"] = frame["volume"] / frame["volume"].rolling(20, min_periods=20).mean().shift(1)
    for lookback in (30, 60, 120, 240):
        frame[f"range_high_prior_{lookback}"] = frame["high"].rolling(lookback, min_periods=lookback).max().shift(1)
        frame[f"range_low_prior_{lookback}"] = frame["low"].rolling(lookback, min_periods=lookback).min().shift(1)
    for window in (30, 60):
        high = frame["high"].rolling(window, min_periods=window).max().shift(1)
        low = frame["low"].rolling(window, min_periods=window).min().shift(1)
        frame[f"compression_range_bps_{window}"] = ((high - low) / frame["close"]) * 10_000.0
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    pv = typical * frame["volume"]
    for window in (120, 240):
        numerator = pv.rolling(window, min_periods=window).sum().shift(1)
        denominator = frame["volume"].rolling(window, min_periods=window).sum().shift(1)
        frame[f"vwap_{window}_prior"] = numerator / denominator
    for span in (20, 50, 120, 240):
        frame[f"ema_{span}_prior"] = frame["close"].ewm(span=span, adjust=False).mean().shift(1)
    for window in (360, 720):
        frame[f"return_bps_prior_{window}"] = (
            (frame["close"].shift(1) / frame["close"].shift(window + 1)) - 1.0
        ) * 10_000.0
    return frame


def _load_candles(database_url: str, window: WindowSpec) -> pd.DataFrame:
    candles = PostgresCandleRepository(database_url).load_standard_candles(
        source=SOURCE,
        symbol=SYMBOL,
        interval=INTERVAL,
        start_time=_dt(window.start_time),
        end_time=_dt(window.end_time),
    )
    frame = pd.DataFrame(candles)
    if frame.empty:
        raise RuntimeError(f"no candles for {window.window_id}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame[["timestamp", "open", "high", "low", "close", "volume"]]


def _closing_net_pnls(result: Any) -> list[float]:
    values: list[float] = []
    for execution in result.executions:
        action_type = str(getattr(execution, "action_type", ""))
        if action_type in {StrategyActionType.EXIT_LONG.value, StrategyActionType.EXIT_SHORT.value}:
            net = getattr(execution, "net_pnl", None)
            if net is not None:
                values.append(float(net))
    return values


def _summary_float(metadata: dict[str, Any], key: str) -> float | None:
    value = metadata.get(key) if isinstance(metadata, dict) else None
    return None if value is None else float(value)


def _summary_float_nested(metadata: dict[str, Any], path: tuple[str, ...]) -> float | None:
    current: Any = metadata
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return None if current is None else float(current)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _positive(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0 or pd.isna(number):
        return None
    return number


def _positive_or_negative(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def _candidate_gate(candidate: CandidateSpec, default_gate: CostGateConfig) -> CostGateConfig:
    return CostGateConfig(
        min_reward_cost_multiple=float(
            candidate.params.get("min_reward_cost_multiple", default_gate.min_reward_cost_multiple)
        ),
        min_net_reward_bps=float(candidate.params.get("min_net_reward_bps", default_gate.min_net_reward_bps)),
        min_net_rr=float(candidate.params.get("min_net_rr", default_gate.min_net_rr)),
    )


def _token(value: float) -> str:
    return str(value).replace(".", "P")


def _candidate_batch(candidate: CandidateSpec) -> str:
    if candidate.variant_id.startswith("T280_B9_"):
        return "batch9"
    if candidate.variant_id.startswith("T280_B8_"):
        return "batch8"
    if candidate.variant_id.startswith("T280_B7_"):
        return "batch7"
    if candidate.variant_id.startswith("T280_B6_"):
        return "batch6"
    if candidate.variant_id.startswith("T280_B5_"):
        return "batch5"
    if candidate.variant_id.startswith("T280_B4_"):
        return "batch4"
    if candidate.variant_id.startswith("T280_B3_"):
        return "batch3"
    if candidate.variant_id.startswith("T280_B2_"):
        return "batch2"
    return "batch1"


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:+.4f}pct"


def _money(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Task 280 iterative model batch.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", DATABASE_URL))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch", default="batch1")
    args = parser.parse_args(argv)
    records = run_matrix(database_url=args.database_url, limit=args.limit, batch=args.batch)
    print(f"wrote {REPORT_PATH} with {len(records)} persisted Task 280 runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
