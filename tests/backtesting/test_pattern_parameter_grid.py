from __future__ import annotations

import json

import pandas as pd
import pytest

from quant_bitcoin.backtesting.pattern_parameter_grid import (
    PatternParameterGridConfig,
    expand_parameter_grid,
    pattern_parameter_hash,
    run_pattern_parameter_grid,
)
from quant_bitcoin.backtesting import pattern_parameter_grid_cli


def _candles() -> pd.DataFrame:
    rows = []
    price = 100.0
    for index in range(12):
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": f"2026-05-24T00:{index:02d}:00Z",
                "open": price,
                "high": price + 2.0,
                "low": price - 2.0,
                "close": price + 1.0,
                "volume": 1000.0 + index,
            }
        )
        price += 0.5
    return pd.DataFrame(rows)


def test_parameter_grid_expansion_respects_max_combinations() -> None:
    with pytest.raises(ValueError, match="parameter grid has 4 combinations"):
        expand_parameter_grid(
            {
                "entry.mode": ("market_on_confirmation_close", "limit_at_entry_reference"),
                "cost.profile": ("zero", "conservative_crypto_1m"),
            },
            max_combinations=3,
        )


def test_parameter_hash_stable_for_same_parameter_set() -> None:
    first = pattern_parameter_hash({"entry.mode": "market_on_confirmation_close", "cost.profile": "zero"})
    second = pattern_parameter_hash({"cost.profile": "zero", "entry.mode": "market_on_confirmation_close"})

    assert first == second


def test_fvg_two_mode_entry_comparison_returns_two_rows() -> None:
    payload = run_pattern_parameter_grid(
        _candles(),
        pattern="FAIR_VALUE_GAP",
        grid={"entry.mode": ("market_on_confirmation_close", "limit_at_entry_reference")},
        config=PatternParameterGridConfig(max_combinations=2),
    )

    assert payload["schema_version"] == "pattern_parameter_grid_v1"
    assert payload["combination_count"] == 2
    assert [row["parameters"]["entry.mode"] for row in payload["rows"]] == [
        "market_on_confirmation_close",
        "limit_at_entry_reference",
    ]
    assert all(row["parameter_hash"] for row in payload["rows"])
    assert all(row["status"] in {"OK", "NO_FILLS"} for row in payload["rows"])
    assert all(row["metrics"] is not None for row in payload["rows"])


def test_trendline_fixture_runs_single_grid_row() -> None:
    payload = run_pattern_parameter_grid(
        _candles(),
        pattern="TRENDLINE_BREAK",
        grid={"entry.mode": ("market_on_confirmation_close",)},
        config=PatternParameterGridConfig(max_combinations=1),
    )

    assert payload["combination_count"] == 1
    assert payload["rows"][0]["status"] in {"OK", "NO_FILLS"}
    assert payload["rows"][0]["metrics"] is not None


def test_repeated_runs_are_stable() -> None:
    grid = {
        "entry.mode": ("market_on_confirmation_close", "limit_at_entry_reference"),
        "cost.profile": ("zero",),
    }
    first = run_pattern_parameter_grid(
        _candles(),
        pattern="FAIR_VALUE_GAP",
        grid=grid,
        config=PatternParameterGridConfig(max_combinations=2, dry_run=True),
    )
    second = run_pattern_parameter_grid(
        _candles(),
        pattern="FAIR_VALUE_GAP",
        grid=grid,
        config=PatternParameterGridConfig(max_combinations=2, dry_run=True),
    )

    assert first == second


def test_fvg_v2_grid_can_enumerate_entry_trigger_and_stop_mode() -> None:
    payload = run_pattern_parameter_grid(
        _candles(),
        pattern="FAIR_VALUE_GAP",
        grid={
            "entry.mode": ("limit_at_pattern_midpoint",),
            "entry.trigger": ("touch", "touch_and_reaction_close"),
            "risk.stop_mode": ("fvg_boundary_atr_buffer", "wider_of_fvg_and_swing"),
        },
        config=PatternParameterGridConfig(max_combinations=4, dry_run=True),
    )

    assert payload["combination_count"] == 4
    assert [row["status"] for row in payload["rows"]] == ["DRY_RUN"] * 4
    assert {row["parameters"]["entry.trigger"] for row in payload["rows"]} == {
        "touch",
        "touch_and_reaction_close",
    }


def test_warning_emitted_when_grid_reaches_warning_threshold() -> None:
    payload = run_pattern_parameter_grid(
        _candles(),
        pattern="FAIR_VALUE_GAP",
        grid={"entry.mode": ("market_on_confirmation_close", "limit_at_entry_reference")},
        config=PatternParameterGridConfig(max_combinations=2, warning_combinations=2, dry_run=True),
    )

    assert payload["warnings"]
    assert "large parameter grid" in payload["warnings"][0]


def test_cli_invalid_parameter_path_fails_clearly(tmp_path, capsys) -> None:
    csv_path = tmp_path / "candles.csv"
    _candles().to_csv(csv_path, index=False)

    with pytest.raises(SystemExit) as exc:
        pattern_parameter_grid_cli.main(
            [
                "--csv",
                str(csv_path),
                "--pattern",
                "FAIR_VALUE_GAP",
                "--dry-run",
                "--param",
                "bad.path=1",
            ]
        )

    assert exc.value.code == 2
    assert "unsupported parameter path: bad.path" in capsys.readouterr().err


def test_cli_dry_run_outputs_json_rows(tmp_path, capsys) -> None:
    csv_path = tmp_path / "candles.csv"
    _candles().to_csv(csv_path, index=False)

    assert pattern_parameter_grid_cli.main(
        [
            "--csv",
            str(csv_path),
            "--pattern",
            "FAIR_VALUE_GAP",
            "--dry-run",
            "--param",
            "entry.mode=market_on_confirmation_close,limit_at_entry_reference",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["dry_run"] is True
    assert len(payload["rows"]) == 2
    assert {row["status"] for row in payload["rows"]} == {"DRY_RUN"}
