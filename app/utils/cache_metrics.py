"""
app/utils/cache_metrics.py
==========================
Lightweight cache hit/miss counter backed by Redis.
Falls back to process-local atomics if Redis is unavailable.

Usage:
    from app.utils.cache_metrics import record_hit, record_miss, get_metrics
    record_hit("item_detail")
    record_miss("item_list")
    print(get_metrics())
    # {"hits": 42, "misses": 8, "ratio": 0.84}
"""

import threading
from typing import Dict

# ── Process-local fallback counters (thread-safe) ────────────────────────────
_lock   = threading.Lock()
_local: Dict[str, int] = {"hits": 0, "misses": 0}


def _redis():
    """Return cache extension or None."""
    try:
        from app.extensions import cache
        cache.get("__cm_probe__")     # liveness check
        return cache
    except Exception:
        return None


def record_hit(namespace: str = "global") -> None:
    """Increment cache hit counter for the given namespace."""
    c = _redis()
    if c:
        try:
            c.inc(f"cache_metrics:{namespace}:hits")
            c.inc("cache_metrics:global:hits")
            return
        except Exception:
            pass
    with _lock:
        _local["hits"] += 1


def record_miss(namespace: str = "global") -> None:
    """Increment cache miss counter for the given namespace."""
    c = _redis()
    if c:
        try:
            c.inc(f"cache_metrics:{namespace}:misses")
            c.inc("cache_metrics:global:misses")
            return
        except Exception:
            pass
    with _lock:
        _local["misses"] += 1


def get_metrics(namespace: str = "global") -> dict:
    """
    Return hits, misses, and hit-ratio for the given namespace.
    Used by the /api/health/readiness endpoint for observability.
    """
    c = _redis()
    if c:
        try:
            hits   = int(c.get(f"cache_metrics:{namespace}:hits")   or 0)
            misses = int(c.get(f"cache_metrics:{namespace}:misses") or 0)
        except Exception:
            hits = misses = 0
    else:
        with _lock:
            hits   = _local["hits"]
            misses = _local["misses"]

    total = hits + misses
    return {
        "hits":   hits,
        "misses": misses,
        "total":  total,
        "ratio":  round(hits / total, 4) if total else 0.0,
    }
