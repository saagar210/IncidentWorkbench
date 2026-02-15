"""Utility functions."""

import json
from datetime import datetime
from typing import Any


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    return dt.isoformat()


def deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize ISO format string to datetime."""
    return datetime.fromisoformat(dt_str)


def json_dumps(obj: Any) -> str:
    """Serialize object to JSON with datetime support."""
    return json.dumps(obj, default=serialize_datetime)


def json_loads(s: str) -> Any:
    """Deserialize JSON string to object."""
    return json.loads(s)
