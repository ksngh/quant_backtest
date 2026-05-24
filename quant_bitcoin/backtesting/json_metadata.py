from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import math
from typing import Any

import pandas as pd

from quant_bitcoin.persistence import canonical_hash


def json_ready_dict(value: Any) -> dict[str, Any]:
    ready = json_ready(value)
    return ready if isinstance(ready, dict) else {}


def json_ready(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return _format_datetime(_to_datetime(value))
    if isinstance(value, datetime):
        return _format_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return json_ready(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [json_ready(item) for item in sorted(value, key=repr)]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return json_ready(value.item())
        except (TypeError, ValueError):
            pass
    return str(value)


def metadata_hash(value: Any) -> str:
    ready = json_ready(value)
    payload = ready if isinstance(ready, dict) else {"value": ready}
    return canonical_hash(payload)


def _to_datetime(value: Any) -> datetime:
    return value.to_pydatetime() if hasattr(value, "to_pydatetime") else value


def _format_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
