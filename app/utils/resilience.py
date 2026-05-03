"""
app/utils/resilience.py
=======================
Enterprise-grade resilience utilities.

Circuit Breaker is now Redis-based (distributed) so state is shared
across all Gunicorn workers. Falls back to in-process memory
automatically if Redis/cache is unavailable (Fail-Open strategy).
"""

import time
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """
    Distributed Circuit Breaker with Redis-backed shared state.

    State machine (shared across ALL workers via Redis):
        CLOSED   → normal operation
        OPEN     → fast-fail, no calls allowed
        HALF_OPEN → one probe call to test recovery

    Redis keys (all prefixed with "circuit:{name}:"):
        :state      → "CLOSED" | "OPEN" | "HALF_OPEN"
        :failures   → integer failure count
        :last_fail  → unix timestamp of last failure (as string)

    Falls back to in-memory counters transparently if Redis
    is unavailable, preserving the original single-worker behaviour.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 name: str = "default"):
        self.name             = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout

        # ── In-memory fallback (single-worker / Redis-down) ──────────────────
        self._local_state     = "CLOSED"
        self._local_failures  = 0
        self._local_last_fail = 0.0

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _cache(self):
        """Return the Flask-Caching instance or None if unavailable."""
        try:
            from app.extensions import cache
            # Lightweight liveness probe
            cache.get("__cb_probe__")
            return cache
        except Exception:
            return None

    def _k(self, suffix: str) -> str:
        return f"circuit:{self.name}:{suffix}"

    def _get_state(self) -> str:
        c = self._cache()
        if c:
            return c.get(self._k("state")) or "CLOSED"
        return self._local_state

    def _set_state(self, state: str):
        c = self._cache()
        if c:
            # TTL slightly longer than recovery_timeout so key doesn't vanish prematurely
            c.set(self._k("state"), state, timeout=self.recovery_timeout * 3 + 60)
        else:
            self._local_state = state

    def _get_failures(self) -> int:
        c = self._cache()
        if c:
            val = c.get(self._k("failures"))
            return int(val) if val is not None else 0
        return self._local_failures

    def _inc_failures(self) -> int:
        c = self._cache()
        if c:
            try:
                new_val = c.inc(self._k("failures"))
                if new_val == 1:
                    # First failure — set TTL so key doesn't live forever
                    c.expire(self._k("failures"), self.recovery_timeout * 3)
                return new_val
            except Exception:
                pass
        self._local_failures += 1
        return self._local_failures

    def _reset_failures(self):
        c = self._cache()
        if c:
            c.set(self._k("failures"), 0, timeout=self.recovery_timeout * 3)
        else:
            self._local_failures = 0

    def _get_last_fail(self) -> float:
        c = self._cache()
        if c:
            val = c.get(self._k("last_fail"))
            return float(val) if val else 0.0
        return self._local_last_fail

    def _set_last_fail(self, ts: float):
        c = self._cache()
        if c:
            c.set(self._k("last_fail"), str(ts),
                  timeout=self.recovery_timeout * 3 + 60)
        else:
            self._local_last_fail = ts

    # ── Decorator ────────────────────────────────────────────────────────────

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            state = self._get_state()

            if state == "OPEN":
                if time.time() - self._get_last_fail() > self.recovery_timeout:
                    self._set_state("HALF_OPEN")
                    state = "HALF_OPEN"
                    logger.info(
                        f"[CircuitBreaker:{self.name}] Entering HALF_OPEN "
                        f"(recovery probe for {func.__name__})."
                    )
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Call to {func.__name__} blocked."
                    )

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                failures = self._inc_failures()
                self._set_last_fail(time.time())
                if state == "HALF_OPEN" or failures >= self.failure_threshold:
                    self._set_state("OPEN")
                    logger.error(
                        f"[CircuitBreaker:{self.name}] OPEN. "
                        f"failures={failures}, last_error={exc}"
                    )
                raise

            # ── Success path ─────────────────────────────────────────────────
            if state == "HALF_OPEN":
                logger.info(
                    f"[CircuitBreaker:{self.name}] Probe succeeded. "
                    f"Now CLOSED."
                )
            self._reset_failures()
            self._set_state("CLOSED")
            return result

        return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0,
          backoff: float = 2.0, exceptions=(Exception,)):
    """
    Exponential backoff retry decorator.
    Unchanged — no distributed state needed here.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            f"[retry] {func.__name__} failed after "
                            f"{max_attempts} attempts. Last error: {exc}"
                        )
                        raise
                    logger.warning(
                        f"[retry] {func.__name__} attempt {attempt}/"
                        f"{max_attempts} failed: {exc}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
        return wrapper
    return decorator


# ── Global singleton instances ────────────────────────────────────────────────
# Named instances so Redis keys are human-readable (circuit:ai:state, etc.)
ai_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120, name="ai")
db_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30,  name="db")
