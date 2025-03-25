"""Cache key generation utilities."""

import hashlib
import json
from datetime import datetime
from typing import Any


def generate_cache_key(endpoint: str, params: dict[str, Any]) -> str:
    """Generate a cache key from endpoint and parameters.

    Args:
        endpoint: The API endpoint name
        params: The parameters passed to the endpoint

    Returns:
        A deterministic hash string representing the endpoint + parameters
    """
    # Normalize parameters
    normalized = {k: _normalize_value(v) for k, v in params.items() if v is not None}

    # Sort for consistency and convert to string
    param_str = json.dumps(normalized, sort_keys=True)

    # Generate key as SHA-256 hash
    return hashlib.sha256(f"{endpoint}:{param_str}".encode()).hexdigest()


def _normalize_value(value: Any) -> Any:
    """Normalize a value for consistent cache key generation.

    Args:
        value: The value to normalize

    Returns:
        A normalized version of the value suitable for consistent serialization
    """
    # Handle None
    if value is None:
        return None

    # Handle dictionaries
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in value.items() if v is not None}

    # Handle lists/tuples
    if isinstance(value, (list, tuple)):
        return [_normalize_value(v) for v in value]

    # Handle datetime objects
    if isinstance(value, datetime):
        return value.isoformat()

    # Handle basic types
    if isinstance(value, (str, int, float, bool)):
        return value

    # Convert other types to string
    return str(value)
