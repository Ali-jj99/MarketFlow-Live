"""
Simple in-memory TTL cache.

Used to store the last known market prices so the dashboard can continue
showing data when an external API is rate-limited or unreachable.
"""

import time
from typing import Any

_cache: dict[str, dict] = {}

TTL: int = 60


def get_cached(key: str) -> tuple[Any | None, bool]:
    """
    Return (data, is_stale).
    is_stale=False  → data is fresh (within TTL)
    is_stale=True   → data is expired OR key was never set
    """
    entry = _cache.get(key)
    if entry is None:
        return None, True
    age = time.time() - entry["timestamp"]
    return entry["data"], age > TTL


def set_cached(key: str, data: Any) -> None:
    """Store data with the current timestamp."""
    _cache[key] = {"data": data, "timestamp": time.time()}


def get_stale(key: str) -> Any | None:
    """
    Return whatever is in the cache for key, regardless of age.
    Returns None if key has never been set.
    Used as a last-resort fallback when a live call fails.
    """
    entry = _cache.get(key)
    return entry["data"] if entry else None
