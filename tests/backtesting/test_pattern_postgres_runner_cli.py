from __future__ import annotations
import json
from types import SimpleNamespace
import pandas as pd
import pytest
from quant_bitcoin.backtesting import strategy_postgres_runner_cli, pattern_postgres_runner_cli
from quant_bitcoin.backtesting import strategy_postgres_runner_core
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus, PatternEntryTrigger
from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan, RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType

class FakeProvider:
    def __init__(self, candles: pd.DataFrame): self._c=candles
    def load(self)->pd.DataFrame: return self._c

def make_candles():
    return pd.DataFrame({"timestamp":pd.date_range("2026-05-18",periods=3,freq="min",tz="UTC"),"open":[100,101,102],"high":[101,102,103],"low":[99,100,101],"close":[100,101,102],"volume":[1,1,1]})


def make_loss_guard_candles():
    return pd.DataFrame({"timestamp":pd.date_range("2026-05-18",periods=3,freq="min",tz="UTC"),"open":[100,90,90],"high":[101,91,91],"low":[99,89,89],"close":[100,90,90],"volume":[1000,1000,1000]})


def _valid_risk_plan() -> RiskExitPlan:
    return RiskExitPlan(
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


class _SizingStubStrategy:
    strategy_key = "STUB"
    strategy_name = "STUB_PATTERN"

    def __init__(self, entry_filter_config=None):
        self.entry_filter_config = entry_filter_config

    def evaluate(self, candles_so_far, portfolio_state=None):
        if len(candles_so_far) != 1:
            return []
        quantity = getattr(self.entry_filter_config, "quantity_override", None)
        return [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=candles_so_far.iloc[-1]["timestamp"],
                quantity=quantity,
                reason="PATTERN_CONFIRMED",
                metadata={
                    "position_side": "LONG",
                    "risk_plan": _valid_risk_plan(),
                    "event_id": "sizing-event",
                    "pattern_type": self.strategy_key,
                    "entry_reference": 100.5,
                    "zone_mid": 100.5,
                    "zone_low": 99.5,
                    "zone_high": 101.5,
                },
            )
        ]


class _FvgEntryStubStrategy(_SizingStubStrategy):
    strategy_key = "FAIR_VALUE_GAP"
    strategy_name = "FAIR_VALUE_GAP_PATTERN_STRATEGY"


class _OrderBlockEntryStubStrategy(_SizingStubStrategy):
    strategy_key = "ORDER_BLOCK"
    strategy_name = "ORDER_BLOCK_PATTERN_STRATEGY"


class _TrendlineEntryStubStrategy(_SizingStubStrategy):
    strategy_key = "TRENDLINE_BREAK"
    strategy_name = "TRENDLINE_BREAK_PATTERN_STRATEGY"


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


def test_strategy_output_events_include_score_metadata():
    events = strategy_postgres_runner_core._serialize_events(
        [
            SimpleNamespace(
                pattern_event_id="e1",
                timestamp=pd.Timestamp("2026-05-18T00:00:00Z"),
                action_type="ENTER_LONG",
                position_signal="LONG_ENTRY",
                position_side="LONG",
                execution_side="BUY",
                reason="PATTERN_CONFIRMED",
                exit_reason=None,
                metadata={
                    "pattern_type": "FAIR_VALUE_GAP",
                    "pattern_direction": "BULLISH",
                    "pattern_status": "VALID",
                    "pattern_score": 0.75,
                    "score_components": {"gap_quality": {"raw_score": 1.0}},
                    "score_calibration": {"is_calibrated_probability": False},
                },
            )
        ]
    )

    assert events[0]["pattern_score"] == 0.75
    assert events[0]["score_components"]["gap_quality"]["raw_score"] == 1.0
    assert events[0]["score_calibration"]["is_calibrated_probability"] is False


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


def test_expand_raw_actions_passes_raw_quantity_to_pattern_builder(monkeypatch):
    candles = make_candles()
    captured = {}

    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=candles.iloc[0]["timestamp"],
        quantity=0.02,
        reason="PATTERN_CONFIRMED",
        metadata={"position_side": "LONG", "risk_plan": _valid_risk_plan(), "event_id": "e1"},
    )

    def fake_builder(*args, **kwargs):
        captured["entry_quantity"] = kwargs.get("entry_quantity")
        return [raw]

    monkeypatch.setattr(strategy_postgres_runner_core, "build_pattern_trade_actions", fake_builder)

    expanded = strategy_postgres_runner_core._expand_raw_actions([raw], candles, 1)
    assert expanded == [raw]
    assert captured["entry_quantity"] == 0.02


def test_expand_raw_actions_passes_actual_confirmation_candle_to_pattern_builder(monkeypatch):
    candles = make_candles()
    captured = {}
    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=candles.iloc[1]["timestamp"],
        metadata={"position_side": "LONG", "risk_plan": _valid_risk_plan(), "event_id": "e1"},
    )

    def fake_builder(*args, **kwargs):
        captured["confirmation_close"] = float(kwargs["confirmation_candle"]["close"])
        return [raw]

    monkeypatch.setattr(strategy_postgres_runner_core, "build_pattern_trade_actions", fake_builder)

    strategy_postgres_runner_core._expand_raw_actions([raw], candles, 2)
    assert captured["confirmation_close"] == 101.0


def test_expand_raw_actions_wires_soft_invalidation_to_builder(monkeypatch):
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-18", periods=2, freq="min", tz="UTC"),
            "open": [100.0, 99.0],
            "high": [101.0, 100.0],
            "low": [99.0, 98.0],
            "close": [100.0, 98.5],
            "volume": [1.0, 1.0],
        }
    )
    raw = StrategyAction(
        StrategyActionType.ENTER_LONG,
        timestamp=candles.iloc[0]["timestamp"],
        metadata={
            "position_side": "LONG",
            "risk_plan": RiskExitPlan(
                direction=RiskExitDirection.LONG,
                entry_price=100.0,
                structural_stop=90.0,
                atr=1.0,
                atr_buffer_multiplier=0.0,
                atr_buffer=0.0,
                stop_price=90.0,
                risk_per_unit=10.0,
                targets=(),
                status=RiskExitPlanStatus.VALID,
            ),
            "event_id": "fvg-1",
            "pattern_type": "FAIR_VALUE_GAP",
            "zone_mid": 99.0,
            "zone_low": 98.0,
            "zone_high": 101.0,
        },
    )

    expanded = strategy_postgres_runner_core._expand_raw_actions([raw], candles, 1)

    assert [action.action_type for action in expanded] == [
        StrategyActionType.ENTER_LONG,
        StrategyActionType.EXIT_LONG,
    ]
    assert expanded[-1].metadata["exit_reason"] == "SOFT_INVALIDATION"
    assert expanded[-1].metadata["exit_metadata"]["rule"] == "fvg_midpoint_reaction_failure"
    assert expanded[-1].metadata["exit_metadata"]["favorable_close_condition"] == "close > fvg_midpoint"


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


def test_cost_profile_config_from_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--cost-profile", "binance_spot_taker_baseline", "--no-persist"])
    config, _ = strategy_postgres_runner_core._build_transaction_cost_config(args)

    assert config.taker_fee_bps == 10.0
    assert config.spread_bps == 1.0
    assert config.slippage_bps == 1.0


def test_fvg_order_block_confluence_cli_metadata_from_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(
        [
            "--pattern",
            "FAIR_VALUE_GAP",
            "--fvg-require-order-block-confluence",
            "--fvg-order-block-confluence-lookback-bars",
            "7",
            "--fvg-order-block-confluence-mode",
            "entry_price_inside_ob",
            "--fvg-order-block-confluence-source",
            "historical_detector",
            "--fvg-local-order-block-break-mode",
            "break_previous_body",
            "--fvg-order-block-require-fresh",
            "--no-persist",
        ]
    )

    metadata = strategy_postgres_runner_core._build_fvg_order_block_confluence_config(args).to_metadata()

    assert metadata["enabled"] is True
    assert metadata["source"] == "HISTORICAL_DETECTOR"
    assert metadata["local_break_mode"] == "BREAK_PREVIOUS_BODY"
    assert metadata["lookback_bars"] == 7
    assert metadata["mode"] == "ENTRY_PRICE_INSIDE_OB"
    assert metadata["require_fresh"] is True
    assert metadata["default_behavior_preserved"] is False


def test_cost_profile_rejects_manual_conflict_without_override():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--cost-profile", "conservative_crypto_1m", "--taker-fee-bps", "1", "--no-persist"])

    try:
        strategy_postgres_runner_core._build_transaction_cost_config(args)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "--allow-cost-profile-overrides" in str(exc)


def test_cost_profile_override_is_deterministic():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--cost-profile",
        "conservative_crypto_1m",
        "--taker-fee-bps",
        "1",
        "--allow-cost-profile-overrides",
        "--no-persist",
    ])
    config, _ = strategy_postgres_runner_core._build_transaction_cost_config(args)

    assert config.taker_fee_bps == 1.0
    assert config.spread_bps == 3.0


def test_order_block_defaults_to_realistic_cost_profile():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--pattern", "ORDER_BLOCK", "--no-persist"])
    config, _ = strategy_postgres_runner_core._build_transaction_cost_config(args)
    workflow = strategy_postgres_runner_core._workflow_settings_metadata(
        args,
        strategy_postgres_runner_core._build_guardrail_config(args),
    )

    assert args.cost_profile == "conservative_crypto_1m"
    assert config.taker_fee_bps == 10.0
    assert config.spread_bps == 3.0
    assert workflow["owner_order_block_default_profile"]["enabled"] is True
    assert "cost_profile" in workflow["owner_order_block_default_profile"]["defaulted_fields"]
    assert args.ob_risk_exit_mode == "previous_candle_1r"
    assert "ob_risk_exit_mode" in workflow["owner_order_block_default_profile"]["defaulted_fields"]
    assert workflow["order_block_risk_exit"]["mode"] == "PREVIOUS_CANDLE_1R"


def test_order_block_cost_profile_zero_override_is_preserved():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--pattern", "ORDER_BLOCK", "--cost-profile", "zero", "--no-persist"])
    config, _ = strategy_postgres_runner_core._build_transaction_cost_config(args)

    assert args.cost_profile == "zero"
    assert config.taker_fee_bps == 0.0
    assert args.owner_order_block_default_profile["explicit_fields"] == ["cost_profile"]


def test_order_block_manual_cost_flag_skips_default_profile():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--pattern", "ORDER_BLOCK", "--taker-fee-bps", "0", "--no-persist"])
    config, _ = strategy_postgres_runner_core._build_transaction_cost_config(args)

    assert args.cost_profile is None
    assert config.taker_fee_bps == 0.0
    assert args.owner_order_block_default_profile["skipped_fields"] == ["cost_profile"]


def test_order_block_risk_exit_mode_compatibility_override_is_preserved():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--pattern", "ORDER_BLOCK", "--ob-risk-exit-mode", "zone_structural_2r", "--no-persist"])
    config = strategy_postgres_runner_core._build_order_block_risk_exit_config(args)

    assert config.mode == "ZONE_STRUCTURAL_2R"
    assert config.to_metadata()["enabled"] is False
    assert args.owner_order_block_default_profile["explicit_fields"] == ["ob_risk_exit_mode"]


def test_order_block_volume_config_builder_preserves_and_overrides_defaults():
    parser = strategy_postgres_runner_core.build_parser("x")
    default_args = parser.parse_args(["--pattern", "ORDER_BLOCK", "--no-persist"])
    override_args = parser.parse_args(
        [
            "--pattern",
            "ORDER_BLOCK",
            "--ob-min-volume-ratio",
            "2.0",
            "--ob-weak-volume-ratio",
            "1.1",
            "--enable-ob-entry-volume-filter",
            "--ob-entry-volume-window",
            "7",
            "--ob-min-entry-volume-ratio",
            "1.8",
            "--enable-ob-mtf-filter",
            "--ob-mtf-timeframes",
            "15m,1h",
            "--no-persist",
        ]
    )

    default_config = strategy_postgres_runner_core._build_order_block_config(default_args)
    override_config = strategy_postgres_runner_core._build_order_block_config(override_args)
    entry_volume = strategy_postgres_runner_core._build_order_block_entry_volume_filter_config(override_args)
    mtf = strategy_postgres_runner_core._build_order_block_mtf_filter_config(override_args)
    risk_exit = strategy_postgres_runner_core._build_order_block_risk_exit_config(default_args)

    assert default_config.minimum_volume_ratio == 1.5
    assert default_config.weak_volume_ratio == 1.3
    assert override_config.minimum_volume_ratio == 2.0
    assert override_config.weak_volume_ratio == 1.1
    assert entry_volume.enabled is True
    assert entry_volume.window == 7
    assert risk_exit.mode == "PREVIOUS_CANDLE_1R"
    assert entry_volume.minimum_volume_ratio == 1.8
    assert mtf.enabled is True
    assert mtf.timeframes == ("15m", "1h")


def test_owner_fvg_v2_channel_defaults_apply_to_minimal_cli_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--no-persist"])

    assert strategy_postgres_runner_core._select_strategy_key(args) == "FAIR_VALUE_GAP"
    assert args.start_time is None
    assert args.cost_profile == "conservative_crypto_1m"
    assert args.enable_fvg_v2 is True
    assert args.enable_fvg_v2_channel is True
    assert args.fvg_channel_standalone_scan is True
    assert args.fvg_channel_window == 20
    assert args.fvg_channel_max_wait_bars == 5
    assert args.enable_fvg_close_volume_filter is True
    assert args.fvg_close_volume_window == 20
    assert args.fvg_min_close_volume_ratio == 2.0
    assert args.fvg_close_volume_baseline_mode == "prior_only"
    assert args.fvg_close_volume_input_mode == "base_volume"
    assert args.fvg_use_trend_score is True
    assert args.fvg_use_fibonacci_confluence is True
    assert args.fvg_stop_mode == "wider_of_fvg_and_swing"
    assert args.enforce_candle_continuity is True
    assert args.enable_market_regime is True
    assert args.starting_cash == 1_000_000.0
    assert args.starting_cash_currency == "KRW"
    assert args.krw_per_usdt == 1500.0
    assert args.position_sizing_mode == "cash_fraction"
    assert args.position_sizing_value == 0.10

    channel = strategy_postgres_runner_core._build_fvg_channel_config(args)
    close_volume = strategy_postgres_runner_core._build_close_volume_entry_filter_config(args)
    sizing = strategy_postgres_runner_core._build_position_sizing_config(args)
    workflow = strategy_postgres_runner_core._workflow_settings_metadata(
        args,
        strategy_postgres_runner_core._build_guardrail_config(args),
    )

    assert channel.enabled is True
    assert channel.window == 20
    assert channel.max_wait_bars == 5
    assert channel.standalone_scan_enabled is True
    assert close_volume.enabled is True
    assert close_volume.window == 20
    assert close_volume.minimum_volume_ratio == 2.0
    assert close_volume.low_volume_ratio_threshold == 0.5
    assert close_volume.baseline_mode == "PRIOR_ONLY"
    assert close_volume.applies_to_side == "ALL"
    assert close_volume.to_metadata()["applies_to_sides"] == ["LONG", "SHORT"]
    assert sizing.mode.value == "CASH_FRACTION"
    assert sizing.value == 0.10
    assert workflow["owner_default_profile"]["enabled"] is True
    assert workflow["owner_default_profile"]["profile_key"] == "owner_fvg_v2_channel_default_v1"
    assert "start_time" not in workflow["owner_default_profile"]["defaulted_fields"]


def test_cash_denomination_metadata_converts_krw_to_usdt():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(
        [
            "--starting-cash",
            "1000000",
            "--starting-cash-currency",
            "KRW",
            "--quote-currency",
            "USDT",
            "--krw-per-usdt",
            "1350",
            "--no-persist",
        ]
    )

    metadata = strategy_postgres_runner_core._build_cash_denomination_metadata(args)

    assert metadata["source_starting_cash"] == 1_000_000.0
    assert metadata["source_currency"] == "KRW"
    assert metadata["quote_currency"] == "USDT"
    assert metadata["effective_quote_starting_cash"] == pytest.approx(740.7407407407)
    assert metadata["converted"] is True
    assert metadata["conversion_source"] == "manual_cli_krw_per_usdt"
    assert metadata["live_fx_lookup_used"] is False


def test_cash_denomination_default_krw_uses_default_manual_rate():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--starting-cash", "1000000", "--no-persist"])

    metadata = strategy_postgres_runner_core._build_cash_denomination_metadata(args)

    assert metadata["source_currency"] == "KRW"
    assert metadata["quote_currency"] == "USDT"
    assert metadata["conversion_rate"] == 1500.0
    assert metadata["effective_quote_starting_cash"] == pytest.approx(666.6666666667)


def test_pattern_cli_krw_starting_cash_uses_converted_quote_cash(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _SizingStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main(
        [
            "--no-persist",
            "--starting-cash",
            "1000000",
            "--starting-cash-currency",
            "KRW",
            "--krw-per-usdt",
            "1000",
            "--position-sizing-mode",
            "cash_fraction",
            "--position-sizing-value",
            "0.10",
            "--cost-profile",
            "zero",
            "--disable-fvg-v2-channel",
            "--disable-fvg-channel-standalone-scan",
            "--disable-fvg-close-volume-filter",
        ]
    ) == 0
    out = json.loads(capsys.readouterr().out)

    assert out["portfolio"]["starting_cash"] == pytest.approx(1000.0)
    assert out["cash_denomination"]["source_currency"] == "KRW"
    assert out["cash_denomination"]["effective_quote_starting_cash"] == pytest.approx(1000.0)
    assert out["summary"]["metadata"]["cash_denomination"]["source_starting_cash"] == 1_000_000.0
    assert out["executions"][0]["quantity"] == pytest.approx(1.0)


def test_owner_fvg_v2_channel_defaults_preserve_explicit_overrides():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--cost-profile",
        "zero",
        "--disable-fvg-v2-channel",
        "--disable-fvg-channel-standalone-scan",
        "--disable-fvg-close-volume-filter",
        "--fvg-min-close-volume-ratio",
        "1.25",
        "--position-sizing-mode",
        "target_notional",
        "--position-sizing-value",
        "1000",
        "--no-enforce-candle-continuity",
        "--disable-market-regime",
        "--no-persist",
    ])

    channel = strategy_postgres_runner_core._build_fvg_channel_config(args)
    close_volume = strategy_postgres_runner_core._build_close_volume_entry_filter_config(args)
    sizing = strategy_postgres_runner_core._build_position_sizing_config(args)
    workflow = strategy_postgres_runner_core._workflow_settings_metadata(
        args,
        strategy_postgres_runner_core._build_guardrail_config(args),
    )

    assert args.cost_profile == "zero"
    assert channel.enabled is False
    assert channel.standalone_scan_enabled is False
    assert close_volume.enabled is False
    assert close_volume.minimum_volume_ratio == 1.25
    assert sizing.mode.value == "TARGET_NOTIONAL"
    assert sizing.value == 1000
    assert args.enforce_candle_continuity is False
    assert args.enable_market_regime is False
    assert workflow["owner_default_profile"]["enabled"] is True
    assert "cost_profile" in workflow["owner_default_profile"]["explicit_fields"]
    assert "enable_fvg_close_volume_filter" in workflow["owner_default_profile"]["explicit_fields"]
    assert "position_sizing_mode" in workflow["owner_default_profile"]["explicit_fields"]


def test_build_position_sizing_and_margin_config_from_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(
        [
            "--position-sizing-mode",
            "target_notional",
            "--position-sizing-value",
            "2500",
            "--insufficient-funds-policy",
            "block",
            "--short-exposure-mode",
            "simulated_margin",
            "--simulated-margin-leverage",
            "10",
            "--no-persist",
        ]
    )
    sizing = strategy_postgres_runner_core._build_position_sizing_config(args)
    short_mode, margin = strategy_postgres_runner_core._build_simulated_margin_config(args)
    assert sizing.mode.value == "TARGET_NOTIONAL"
    assert sizing.value == 2500
    assert sizing.insufficient_funds_policy.value == "BLOCK"
    assert short_mode.value == "SIMULATED_MARGIN"
    assert margin.enabled is True
    assert margin.leverage == 10


def test_cash_fraction_position_sizing_requires_value():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--position-sizing-mode", "cash_fraction", "--no-persist"])
    try:
        strategy_postgres_runner_core._build_position_sizing_config(args)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "requires --position-sizing-value" in str(exc)


def test_simulated_margin_mode_requires_leverage():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--short-exposure-mode", "simulated_margin", "--no-persist"])
    try:
        strategy_postgres_runner_core._build_simulated_margin_config(args)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "requires --simulated-margin-leverage" in str(exc)


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
        lambda *_, **__: (
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


def test_strategy_cli_output_includes_sizing_and_margin_metadata(monkeypatch, capsys):
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-18", periods=1, freq="min", tz="UTC"),
            "open": [80000],
            "high": [80000],
            "low": [80000],
            "close": [80000],
            "volume": [1],
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
        lambda *_, **__: (
            type("StubStrategy", (), {"strategy_key": "STUB", "strategy_name": "STUB_PATTERN"})(),
            [
                strategy_postgres_runner_cli.StrategyAction(
                    strategy_postgres_runner_cli.StrategyActionType.ENTER_SHORT,
                    timestamp=candles.iloc[0]["timestamp"],
                    quantity=1.0,
                ),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--starting-cash",
        "10000",
        "--starting-cash-currency",
        "USDT",
        "--position-sizing-mode",
        "fixed_quantity",
        "--cost-profile",
        "zero",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    metadata = out["summary"]["metadata"]
    assert metadata["position_sizing"]["mode"] == "FIXED_QUANTITY"
    assert metadata["short_exposure_policy"]["mode"] == "CASH_BOUNDED"
    assert out["executions"][0]["quantity"] == 0.125
    assert out["executions"][0]["position_signal"] == "SHORT_ENTRY"
    assert out["executions"][0]["execution_side"] == "SELL"
    assert out["executions"][0]["cash_balance_after"] == 20000
    assert out["executions"][0]["free_cash_after"] == 0
    assert out["executions"][0]["short_collateral_locked_after"] == 10000


def test_pattern_cli_cash_fraction_uses_engine_sizing_when_no_override(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _SizingStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--starting-cash",
        "10000",
        "--starting-cash-currency",
        "USDT",
        "--position-sizing-mode",
        "cash_fraction",
        "--position-sizing-value",
        "0.25",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    execution = out["executions"][0]
    assert execution["quantity"] == 25.0
    assert execution["metadata"]["position_sizing_source"] == "ENGINE_CONFIG"
    assert execution["metadata"]["entry_quantity_source"] == "ENGINE_CONFIG"
    assert execution["metadata"]["engine_sizing_allowed"] is True


def test_pattern_cli_output_preserves_million_starting_cash(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _SizingStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--starting-cash",
        "1000000",
        "--starting-cash-currency",
        "USDT",
        "--position-sizing-mode",
        "cash_fraction",
        "--position-sizing-value",
        "0.10",
    ]) == 0
    out = json.loads(capsys.readouterr().out)

    assert out["portfolio"]["starting_cash"] == 1_000_000.0
    assert out["executions"][0]["metadata"]["position_sizing_value"] == 0.10


def test_pattern_cli_target_notional_uses_engine_sizing_when_no_override(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _SizingStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--starting-cash",
        "10000",
        "--starting-cash-currency",
        "USDT",
        "--position-sizing-mode",
        "target_notional",
        "--position-sizing-value",
        "1000",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    execution = out["executions"][0]
    assert execution["quantity"] == 10.0
    assert execution["notional"] == 1000.0
    assert execution["metadata"]["position_sizing_source"] == "ENGINE_CONFIG"


def test_pattern_cli_quantity_override_precedes_engine_sizing(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _SizingStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist", "--position-sizing-mode", "cash_fraction", "--position-sizing-value", "0.25", "--pattern-quantity-override", "0.02"]) == 0
    out = json.loads(capsys.readouterr().out)
    execution = out["executions"][0]
    assert execution["quantity"] == 0.02
    assert execution["metadata"]["position_sizing_source"] == "ACTION_QUANTITY"
    assert execution["metadata"]["entry_quantity_source"] == "ACTION_OVERRIDE"
    assert execution["metadata"]["pattern_quantity_override"] == 0.02


def test_build_pattern_entry_filter_config_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args(["--allow-weak-pattern-events", "--min-pattern-score", "0.8", "--min-risk-reward", "1.5", "--pattern-quantity-override", "3", "--no-persist"])
    cfg = strategy_postgres_runner_core._build_pattern_entry_filter_config(args)
    assert "VALID" in cfg.allowed_statuses and "WEAK" in cfg.allowed_statuses
    assert cfg.minimum_pattern_score == 0.8
    assert cfg.minimum_risk_reward == 1.5
    assert cfg.quantity_override == 3


def test_build_fvg_entry_config_args():
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--fvg-entry-mode",
        "limit_at_pattern_midpoint",
        "--fvg-entry-max-wait-bars",
        "3",
        "--fvg-entry-expire-status",
        "cancelled",
        "--fvg-entry-trigger",
        "touch_and_reaction_close",
        "--no-persist",
    ])

    mode = strategy_postgres_runner_core._selected_fvg_entry_mode(args)
    config = strategy_postgres_runner_core._selected_fvg_entry_config(args)

    assert mode is PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT
    assert config == PatternEntryConfig(
        max_wait_bars=3,
        expire_status=PatternEntryStatus.CANCELLED,
        entry_trigger=PatternEntryTrigger.TOUCH_AND_REACTION_CLOSE,
    )
    metadata = strategy_postgres_runner_core._build_fvg_entry_metadata(mode, config, None)
    assert metadata["entry_trigger"] == "TOUCH_AND_REACTION_CLOSE"


def test_fvg_v2_cli_metadata_records_research_controls() -> None:
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--enable-fvg-v2",
        "--disable-fvg-v2-channel",
        "--disable-fvg-channel-standalone-scan",
        "--fvg-use-trend-score",
        "--fvg-trend-fast-period",
        "5",
        "--fvg-trend-slow-period",
        "13",
        "--fvg-use-fibonacci-confluence",
        "--fvg-require-liquidity-target",
        "--fvg-stop-mode",
        "wider_of_fvg_and_swing",
        "--fvg-entry-trigger",
        "touch_and_reaction_close",
        "--no-persist",
    ])

    metadata = strategy_postgres_runner_core._build_fvg_v2_metadata(args)

    assert metadata["schema_version"] == "fvg_retest_v2_settings_v1"
    assert metadata["enabled"] is True
    assert metadata["trend_score"]["fast_period"] == 5
    assert metadata["trend_score"]["slow_period"] == 13
    assert metadata["fibonacci_confluence"]["enabled"] is True
    assert metadata["liquidity_targets"]["require_liquidity_target"] is True
    assert metadata["stop_mode"] == "WIDER_OF_FVG_AND_SWING"
    assert metadata["entry_trigger"] == "TOUCH_AND_REACTION_CLOSE"
    assert metadata["parallel_channel"]["enabled"] is False
    assert metadata["parallel_channel"]["standalone_scan_enabled"] is False
    assert metadata["parallel_channel"]["atr_used_for_stop_or_target"] is False
    assert metadata["close_volume_entry_filter"]["enabled"] is True
    assert metadata["close_volume_entry_filter"]["applies_to_side"] == "ALL"
    assert metadata["close_volume_entry_filter"]["applies_to_sides"] == ["LONG", "SHORT"]


def test_fvg_v2_channel_cli_metadata_enables_parallel_channel() -> None:
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--enable-fvg-v2-channel",
        "--fvg-channel-window",
        "12",
        "--fvg-channel-max-wait-bars",
        "5",
        "--fvg-channel-standalone-scan",
        "--no-persist",
    ])

    metadata = strategy_postgres_runner_core._build_fvg_v2_metadata(args)

    assert metadata["enabled"] is True
    assert metadata["parallel_channel"]["enabled"] is True
    assert metadata["parallel_channel"]["window"] == 12
    assert metadata["parallel_channel"]["max_wait_bars"] == 5
    assert metadata["parallel_channel"]["standalone_scan_enabled"] is True
    assert metadata["parallel_channel"]["scan_semantics"] == "fvg_event_expansion_plus_standalone_visible_prefix_scan"
    assert metadata["parallel_channel"]["stop_target_policy"] == "PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1"
    assert metadata["parallel_channel"]["channel_target_policy"] == "PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1"
    assert metadata["parallel_channel"]["atr_used_for_stop_or_target"] is False


def test_fvg_inverse_direction_cli_metadata_records_research_mode() -> None:
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--pattern",
        "FAIR_VALUE_GAP",
        "--fvg-inverse-direction",
        "--no-persist",
    ])

    direction = strategy_postgres_runner_core._build_fvg_direction_metadata(args.fvg_inverse_direction)
    v2_metadata = strategy_postgres_runner_core._build_fvg_v2_metadata(args)

    assert direction["schema_version"] == "fvg_direction_mode_config_v1"
    assert direction["mode"] == "INVERSE_CONTRARIAN"
    assert direction["inverse_direction_enabled"] is True
    assert direction["default_behavior_preserved"] is False
    assert v2_metadata["direction"]["mode"] == "INVERSE_CONTRARIAN"


def test_research_metadata_cli_records_task_variant_and_window() -> None:
    parser = strategy_postgres_runner_core.build_parser("x")
    args = parser.parse_args([
        "--research-task-id",
        "TASK_279",
        "--research-variant-id",
        "T279_TEST_VARIANT",
        "--research-window-id",
        "owner_a",
        "--research-run-group",
        "validation_matrix",
        "--no-persist",
    ])

    metadata = strategy_postgres_runner_core._build_research_metadata(args)

    assert metadata == {
        "schema_version": "research_run_metadata_v1",
        "enabled": True,
        "task_id": "TASK_279",
        "variant_id": "T279_TEST_VARIANT",
        "window_id": "owner_a",
        "run_group": "validation_matrix",
        "scope": "offline_backtest_research_only",
    }


def test_fvg_inverse_direction_is_rejected_for_non_fvg_pattern() -> None:
    with pytest.raises(ValueError, match="only supported"):
        strategy_postgres_runner_core.run([
            "--pattern",
            "ORDER_BLOCK",
            "--fvg-inverse-direction",
            "--no-persist",
        ])


def test_fvg_entry_mode_cli_output_contains_fill_diagnostics(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _FvgEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "FAIR_VALUE_GAP",
        "--disable-fvg-v2-channel",
        "--disable-fvg-channel-standalone-scan",
        "--fvg-entry-mode",
        "limit_at_pattern_midpoint",
        "--fvg-entry-max-wait-bars",
        "2",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    execution = out["executions"][0]
    diagnostics = out["diagnostics"]["fvg_entry_mode"]

    assert execution["metadata"]["entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert execution["metadata"]["fill_price_source"] == "PATTERN_MIDPOINT"
    assert execution["metadata"]["bars_waited"] == 1
    assert diagnostics["selected_entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert diagnostics["fill_rate"] == 1.0
    assert out["summary"]["metadata"]["fvg_entry_mode"]["filled_entry_count"] == 1


def test_fvg_v2_cli_output_contains_diagnostics(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _FvgEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "FAIR_VALUE_GAP",
        "--enable-fvg-v2",
        "--fvg-entry-mode",
        "limit_at_pattern_midpoint",
        "--fvg-entry-trigger",
        "touch_and_reaction_close",
    ]) == 0
    out = json.loads(capsys.readouterr().out)

    diagnostics = out["diagnostics"]["fvg_retest_v2"]
    assert diagnostics["schema_version"] == "fvg_retest_v2_diagnostics_v1"
    assert diagnostics["settings"]["enabled"] is True
    assert diagnostics["entry_trigger"] == "TOUCH_AND_REACTION_CLOSE"
    assert "fvg_retest_v2_experimental_scope" in out["warnings"]


def test_fvg_entry_mode_comparison_output_contains_modes(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _FvgEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "FAIR_VALUE_GAP",
        "--compare-fvg-entry-modes",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    comparison = out["diagnostics"]["fvg_entry_mode_comparison"]

    assert comparison["schema_version"] == "fvg_entry_mode_comparison_v1"
    assert "MARKET_ON_CONFIRMATION_CLOSE" in comparison["modes"]
    assert "LIMIT_AT_PATTERN_MIDPOINT" in comparison["modes"]
    assert comparison["modes"]["MARKET_ON_CONFIRMATION_CLOSE"]["economic_interpretation"] == "chase_momentum_after_confirmation"
    assert comparison["modes"]["LIMIT_AT_PATTERN_MIDPOINT"]["economic_interpretation"] == "imbalance_retest_or_rebalancing_entry"
    assert "LIMIT_AT_PATTERN_NEAR_BOUNDARY" in comparison["modes"]
    assert "LIMIT_AT_PATTERN_FAR_BOUNDARY" in comparison["modes"]


def test_order_block_entry_mode_comparison_output_contains_618_mode(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _OrderBlockEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "ORDER_BLOCK",
        "--compare-pattern-entry-modes",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    comparison = out["diagnostics"]["pattern_entry_mode_comparison"]

    assert comparison["schema_version"] == "pattern_entry_mode_comparison_v1"
    assert comparison["pattern_key"] == "ORDER_BLOCK"
    assert "LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT" in comparison["modes"]
    assert comparison["modes"]["MARKET_ON_CONFIRMATION_CLOSE"]["entry_style"] == "CHASE_OR_MOMENTUM"
    assert comparison["modes"]["LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT"]["entry_mode_hypothesis"] == "RETEST_ORDER_BLOCK_618_RETRACEMENT"


def test_pattern_entry_mode_rejects_unsupported_combination_before_provider_load() -> None:
    try:
        strategy_postgres_runner_core.run([
            "--no-persist",
            "--pattern",
            "DIAMOND",
            "--pattern-entry-mode",
            "limit_at_pattern_midpoint",
        ])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "not supported for DIAMOND" in str(exc)


def test_order_block_pattern_policy_metadata_in_cli_output(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _OrderBlockEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "ORDER_BLOCK",
        "--pattern-entry-mode",
        "market_on_next_open",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    policy = out["diagnostics"]["pattern_execution_policy"]

    assert policy["pattern_key"] == "ORDER_BLOCK"
    assert policy["policy_key"] == "ORDER_BLOCK_ZONE_RETEST"
    assert policy["selected_entry_mode"] == "MARKET_ON_NEXT_OPEN"
    assert out["executions"][0]["metadata"]["pattern_execution_policy_key"] == "ORDER_BLOCK_ZONE_RETEST"


def test_trendline_break_pattern_policy_metadata_in_cli_output(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "strategy_for_pattern",
        lambda *args, **kwargs: _TrendlineEntryStubStrategy(kwargs.get("entry_filter_config")),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--pattern",
        "TRENDLINE_BREAK",
        "--pattern-entry-mode",
        "limit_at_entry_reference",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    policy = out["summary"]["metadata"]["pattern_execution_policy"]

    assert policy["pattern_key"] == "TRENDLINE_BREAK"
    assert policy["policy_key"] == "TRENDLINE_BREAKOUT_CONFIRMATION"
    assert policy["selected_entry_mode"] == "LIMIT_AT_ENTRY_REFERENCE"


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


def test_cli_output_contains_cost_profile_metadata(monkeypatch, capsys):
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(make_candles()),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist", "--cost-profile", "high_slippage_stress"]) == 0
    out = json.loads(capsys.readouterr().out)
    profile = out["summary"]["metadata"]["cost_profile"]
    assert profile["profile_key"] == "high_slippage_stress"
    assert profile["slippage_bps"] == 20.0
    assert profile["zero_cost_profile"] is False


def test_cli_passes_continuity_flag_to_provider(monkeypatch, capsys):
    captured = {}

    def fake_provider(*args, **kwargs):
        captured["enforce_continuity"] = kwargs.get("enforce_continuity")
        return FakeProvider(make_candles())

    monkeypatch.setattr(strategy_postgres_runner_cli.PostgresCandleDataProvider, "from_database_url", fake_provider)
    assert strategy_postgres_runner_cli.main(["--no-persist", "--enforce-candle-continuity"]) == 0
    json.loads(capsys.readouterr().out)
    assert captured["enforce_continuity"] is True


def test_cli_guardrail_blocks_after_consecutive_loss(monkeypatch, capsys):
    candles = make_loss_guard_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda *_, **__: (
            type("StubStrategy", (), {"strategy_key": "STUB", "strategy_name": "STUB_PATTERN"})(),
            [
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
                StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[2]["timestamp"], quantity=1.0),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist", "--max-consecutive-losses", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["executions"][-1]["reason"] == "RISK_GUARD_MAX_CONSECUTIVE_LOSSES"
    assert out["summary"]["metadata"]["guardrails"]["max_consecutive_losses"] == 1


def test_cli_market_regime_enabled_adds_execution_metadata(monkeypatch, capsys):
    candles = make_candles()
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *a, **k: FakeProvider(candles),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda *_, **__: (
            type("StubStrategy", (), {"strategy_key": "STUB", "strategy_name": "STUB_PATTERN"})(),
            [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0)],
        ),
    )

    assert strategy_postgres_runner_cli.main([
        "--no-persist",
        "--enable-market-regime",
        "--market-regime-window",
        "1",
        "--market-regime-min-trading-value",
        "1",
    ]) == 0
    out = json.loads(capsys.readouterr().out)
    metadata = out["executions"][0]["metadata"]
    assert metadata["market_regime"] != "UNKNOWN"
    assert out["summary"]["metadata"]["workflow_settings"]["market_regime_enabled"] is True
