"""Convert Python/pandas/numpy values to JSON-serializable form for JSON columns."""
from datetime import datetime, date
from typing import Any
import numpy as np
import pandas as pd


def _is_na_like(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and np.isnan(v):
        return True
    try:
        return pd.isna(v)
    except (TypeError, ValueError):
        return False


def to_json_safe(value: Any) -> Any:
    """
    Recursively convert a value to something JSON-serializable.
    Handles datetime, date, numpy/pandas scalar types, NaN, and nested dicts/lists.
    """
    if value is None:
        return None
    if _is_na_like(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat() if pd.notna(value) else None
    if isinstance(value, np.datetime64):
        try:
            return pd.Timestamp(value).isoformat()
        except Exception:
            return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return None if _is_na_like(value) else float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return [to_json_safe(x) for x in value.tolist()]
    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_safe(x) for x in value]
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and (_is_na_like(value)):
            return None
        return value
    # fallback: try to coerce to string to avoid breaking on unknown types
    try:
        return str(value)
    except Exception:
        return None
