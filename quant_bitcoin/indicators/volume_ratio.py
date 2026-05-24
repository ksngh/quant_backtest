"""Volume Ratio indicator calculation.

This module consumes already-provided candle volume data and emits deterministic
relative-volume rows. It does not fetch market data, read secrets, call exchange
APIs, place orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import median
from typing import Any

import pandas as pd

REQUIRED_VOLUME_RATIO_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "volume",
)

VOLUME_RATIO_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "volume",
    "average_volume",
    "volume_ratio",
    "minimum_volume_ratio_for_confirmation",
    "volume_confirmation",
    "volume_status",
    "is_valid",
)


class VolumeStatus(Enum):
    """Volume-ratio classifications."""

    HIGH = "HIGH"
    INCREASED = "INCREASED"
    NORMAL = "NORMAL"
    LOW = "LOW"
    INVALID = "INVALID"


class VolumeAverageMethod(Enum):
    """Supported volume baseline methods."""

    MEAN = "MEAN"
    MEDIAN = "MEDIAN"


class VolumeRatioBaselineMode(Enum):
    """Supported volume-ratio rolling baseline timing modes."""

    CURRENT_INCLUSIVE = "CURRENT_INCLUSIVE"
    PRIOR_ONLY = "PRIOR_ONLY"


class VolumeInputMode(Enum):
    """Supported activity inputs for volume-ratio calculations."""

    BASE_VOLUME = "BASE_VOLUME"
    QUOTE_VOLUME_IF_AVAILABLE = "QUOTE_VOLUME_IF_AVAILABLE"
    TRADING_VALUE = "TRADING_VALUE"


@dataclass(frozen=True)
class VolumeRatioConfig:
    """Configuration for deterministic Volume Ratio calculation."""

    window: int = 20
    minimum_volume_ratio_for_confirmation: float = 1.5
    high_volume_ratio_threshold: float = 2.0
    low_volume_ratio_threshold: float = 0.5
    require_full_window: bool = True
    reject_zero_average_volume: bool = True
    average_method: VolumeAverageMethod | str = VolumeAverageMethod.MEAN
    baseline_mode: VolumeRatioBaselineMode | str = (
        VolumeRatioBaselineMode.CURRENT_INCLUSIVE
    )
    volume_input_mode: VolumeInputMode | str = VolumeInputMode.BASE_VOLUME
    baseline_includes_current: bool | None = None

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError("window must be at least 1")
        if self.minimum_volume_ratio_for_confirmation < 0:
            raise ValueError(
                "minimum_volume_ratio_for_confirmation must be non-negative"
            )
        if self.high_volume_ratio_threshold < 0:
            raise ValueError("high_volume_ratio_threshold must be non-negative")
        if self.low_volume_ratio_threshold < 0:
            raise ValueError("low_volume_ratio_threshold must be non-negative")
        if (
            self.low_volume_ratio_threshold
            > self.minimum_volume_ratio_for_confirmation
        ):
            raise ValueError(
                "low_volume_ratio_threshold must be less than or equal to "
                "minimum_volume_ratio_for_confirmation"
            )
        if (
            self.minimum_volume_ratio_for_confirmation
            > self.high_volume_ratio_threshold
        ):
            raise ValueError(
                "minimum_volume_ratio_for_confirmation must be less than or "
                "equal to high_volume_ratio_threshold"
            )
        _coerce_average_method(self.average_method)
        _coerce_baseline_mode(self)
        _coerce_volume_input_mode(self.volume_input_mode)


def calculate_volume_ratio(
    candles: pd.DataFrame, config: VolumeRatioConfig | None = None
) -> pd.DataFrame:
    """Return Volume Ratio rows for already-provided candle volume data.

    The returned frame has one row per input candle and includes current volume,
    the rolling baseline average volume, volume ratio, confirmation flag,
    status, and validity. With the default ``require_full_window`` setting, rows
    before the configured warm-up window are returned as invalid rows with
    ``volume_status`` set to ``INVALID``.

    The rolling baseline includes the current candle, matching the owner-provided
    mechanical definition and pseudocode for the latest snapshot.

    Args:
        candles: Candle data containing symbol, timestamp, and volume columns.
        config: Volume Ratio calculation configuration. Defaults to
            ``VolumeRatioConfig()``.

    Raises:
        ValueError: If required columns are missing, numeric values are
            non-numeric, or configuration values are invalid.
    """

    volume_config = config or VolumeRatioConfig()
    _validate_candles(candles)

    if candles.empty:
        baseline_mode = _coerce_baseline_mode(volume_config)
        input_mode = _coerce_volume_input_mode(volume_config.volume_input_mode)
        selected_column = (
            "trading_value"
            if input_mode == VolumeInputMode.TRADING_VALUE
            else "volume"
        )
        return _empty_volume_ratio_frame(
            volume_config,
            baseline_mode,
            input_mode,
            selected_column,
        )

    input_mode = _coerce_volume_input_mode(volume_config.volume_input_mode)
    baseline_mode = _coerce_baseline_mode(volume_config)
    volume, selected_volume_column = _select_volume_input(candles, input_mode)
    rows: list[dict[str, Any]] = []

    for position, (_, candle) in enumerate(candles.iterrows()):
        current_volume = _optional_float(volume.iloc[position])
        end_position = (
            position + 1
            if baseline_mode == VolumeRatioBaselineMode.CURRENT_INCLUSIVE
            else position
        )
        start_position = max(0, end_position - volume_config.window)
        window_values = [
            _optional_float(value) for value in volume.iloc[start_position:end_position]
        ]
        has_full_window = len(window_values) == volume_config.window

        if (
            current_volume is None
            or any(value is None for value in window_values)
            or any(value is not None and value < 0 for value in window_values)
            or (volume_config.require_full_window and not has_full_window)
        ):
            rows.append(_invalid_row(candle, current_volume, volume_config))
            continue

        numeric_window_values = [value for value in window_values if value is not None]
        average_volume = _calculate_average_volume(
            numeric_window_values,
            _coerce_average_method(volume_config.average_method),
        )

        if average_volume == 0:
            rows.append(_invalid_row(candle, current_volume, volume_config))
            continue

        volume_ratio = current_volume / average_volume
        volume_confirmation = (
            volume_ratio >= volume_config.minimum_volume_ratio_for_confirmation
        )
        volume_status = classify_volume_status(volume_ratio, volume_config)

        rows.append(
            {
                "symbol": candle["symbol"],
                "timestamp": candle["timestamp"],
                "volume": current_volume,
                "average_volume": average_volume,
                "volume_ratio": volume_ratio,
                "minimum_volume_ratio_for_confirmation": (
                    volume_config.minimum_volume_ratio_for_confirmation
                ),
                "volume_confirmation": bool(volume_confirmation),
                "volume_status": volume_status,
                "is_valid": True,
            }
        )

    result = pd.DataFrame(rows, columns=VOLUME_RATIO_OUTPUT_COLUMNS)
    result.attrs["volume_ratio_metadata"] = _volume_ratio_config_metadata(
        volume_config,
        baseline_mode,
        input_mode,
        selected_volume_column,
    )
    return result


def classify_volume_status(
    volume_ratio: float | None,
    config: VolumeRatioConfig | None = None,
) -> str:
    """Classify a volume ratio into HIGH, INCREASED, NORMAL, LOW, or INVALID."""

    volume_config = config or VolumeRatioConfig()
    if volume_ratio is None:
        return VolumeStatus.INVALID.value
    if volume_ratio >= volume_config.high_volume_ratio_threshold:
        return VolumeStatus.HIGH.value
    if volume_ratio >= volume_config.minimum_volume_ratio_for_confirmation:
        return VolumeStatus.INCREASED.value
    if volume_ratio <= volume_config.low_volume_ratio_threshold:
        return VolumeStatus.LOW.value
    return VolumeStatus.NORMAL.value


def calculate_volume_ratio_snapshot(
    candles: pd.DataFrame,
    config: VolumeRatioConfig | None = None,
    *,
    include_timing_metadata: bool = False,
) -> dict[str, Any]:
    """Return the latest Volume Ratio output row as a dictionary."""

    volume_config = config or VolumeRatioConfig()
    volume_ratio_rows = calculate_volume_ratio(candles, config)
    if volume_ratio_rows.empty:
        snapshot = {column: None for column in VOLUME_RATIO_OUTPUT_COLUMNS}
    else:
        snapshot = volume_ratio_rows.iloc[-1].to_dict()
    if volume_ratio_rows.attrs.get("volume_ratio_metadata") is not None:
        snapshot["metadata"] = volume_ratio_rows.attrs["volume_ratio_metadata"]
    if include_timing_metadata:
        snapshot["timing"] = volume_ratio_timing_metadata(volume_config)
    return snapshot


def volume_ratio_timing_metadata(
    config: VolumeRatioConfig | None = None,
) -> dict[str, Any]:
    """Return Volume Ratio timing semantics without changing the output frame schema."""

    volume_config = config or VolumeRatioConfig()
    baseline_mode = _coerce_baseline_mode(volume_config)
    input_mode = _coerce_volume_input_mode(volume_config.volume_input_mode)
    includes_current = baseline_mode == VolumeRatioBaselineMode.CURRENT_INCLUSIVE
    return {
        "schema_version": "indicator_timing_metadata_v1",
        "indicator": "VOLUME_RATIO",
        "current_candle_included": includes_current,
        "requires_closed_candle": includes_current,
        "warmup_period": int(volume_config.window if includes_current else volume_config.window + 1),
        "confirmation_delay": 0,
        "baseline_mode": baseline_mode.value,
        "volume_input_mode": input_mode.value,
        "safe_usage": (
            "after_close_completed_candle_signal"
            if includes_current
            else "pre_close_or_intrabar_baseline_with_current_volume_excluded"
        ),
    }


def _validate_candles(candles: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REQUIRED_VOLUME_RATIO_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(f"missing required Volume Ratio columns: {joined}")


def _calculate_average_volume(
    values: list[float], average_method: VolumeAverageMethod
) -> float:
    if average_method == VolumeAverageMethod.MEDIAN:
        return float(median(values))
    return float(sum(values) / len(values))


def _invalid_row(
    candle: pd.Series, current_volume: float | None, config: VolumeRatioConfig
) -> dict[str, Any]:
    return {
        "symbol": candle["symbol"],
        "timestamp": candle["timestamp"],
        "volume": current_volume,
        "average_volume": None,
        "volume_ratio": None,
        "minimum_volume_ratio_for_confirmation": (
            config.minimum_volume_ratio_for_confirmation
        ),
        "volume_confirmation": False,
        "volume_status": VolumeStatus.INVALID.value,
        "is_valid": False,
    }


def _empty_volume_ratio_frame(
    config: VolumeRatioConfig,
    baseline_mode: VolumeRatioBaselineMode,
    input_mode: VolumeInputMode,
    selected_volume_column: str,
) -> pd.DataFrame:
    frame = pd.DataFrame(columns=VOLUME_RATIO_OUTPUT_COLUMNS)
    frame.attrs["volume_ratio_metadata"] = _volume_ratio_config_metadata(
        config,
        baseline_mode,
        input_mode,
        selected_volume_column,
    )
    return frame


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _coerce_average_method(
    average_method: VolumeAverageMethod | str,
) -> VolumeAverageMethod:
    if isinstance(average_method, VolumeAverageMethod):
        return average_method
    try:
        return VolumeAverageMethod(str(average_method).upper())
    except ValueError as exc:
        allowed = ", ".join(method.value for method in VolumeAverageMethod)
        raise ValueError(f"average_method must be one of: {allowed}") from exc


def _coerce_baseline_mode(config: VolumeRatioConfig) -> VolumeRatioBaselineMode:
    if config.baseline_includes_current is not None:
        return (
            VolumeRatioBaselineMode.CURRENT_INCLUSIVE
            if config.baseline_includes_current
            else VolumeRatioBaselineMode.PRIOR_ONLY
        )
    if isinstance(config.baseline_mode, VolumeRatioBaselineMode):
        return config.baseline_mode
    try:
        return VolumeRatioBaselineMode(str(config.baseline_mode).upper())
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in VolumeRatioBaselineMode)
        raise ValueError(f"baseline_mode must be one of: {allowed}") from exc


def _coerce_volume_input_mode(
    volume_input_mode: VolumeInputMode | str,
) -> VolumeInputMode:
    if isinstance(volume_input_mode, VolumeInputMode):
        return volume_input_mode
    try:
        return VolumeInputMode(str(volume_input_mode).upper())
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in VolumeInputMode)
        raise ValueError(f"volume_input_mode must be one of: {allowed}") from exc


def _select_volume_input(
    candles: pd.DataFrame, input_mode: VolumeInputMode
) -> tuple[pd.Series, str]:
    if input_mode == VolumeInputMode.QUOTE_VOLUME_IF_AVAILABLE and "quote_volume" in candles.columns:
        return pd.to_numeric(candles["quote_volume"], errors="raise"), "quote_volume"
    if input_mode == VolumeInputMode.TRADING_VALUE:
        if "close" not in candles.columns:
            raise ValueError(
                "close column is required when volume_input_mode is TRADING_VALUE"
            )
        close = pd.to_numeric(candles["close"], errors="raise")
        volume = pd.to_numeric(candles["volume"], errors="raise")
        return close * volume, "trading_value"
    return pd.to_numeric(candles["volume"], errors="raise"), "volume"


def _volume_ratio_config_metadata(
    config: VolumeRatioConfig,
    baseline_mode: VolumeRatioBaselineMode,
    input_mode: VolumeInputMode,
    selected_volume_column: str,
) -> dict[str, Any]:
    return {
        "schema_version": "volume_ratio_config_metadata_v1",
        "baseline_mode": baseline_mode.value,
        "volume_input_mode": input_mode.value,
        "selected_volume_column": selected_volume_column,
        "window": int(config.window),
        "average_method": _coerce_average_method(config.average_method).value,
        "minimum_volume_ratio_for_confirmation": float(
            config.minimum_volume_ratio_for_confirmation
        ),
    }
