import functools
import logging
from app.extensions import cache

logger = logging.getLogger(__name__)

def redis_lock(lock_name: str, timeout: int = 60):
    """
    Enterprise-Grade Distributed Lock using Redis (via Flask-Caching's add method).
    Prevents duplicate background tasks from running simultaneously across multiple workers.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Dynamic lock key based on args (simple hash/string conversion)
            args_str = "_".join([str(a) for a in args])
            key = f"lock:{lock_name}:{args_str}"
            
            # Using cache.add for atomic check-and-set
            try:
                acquired = cache.add(key, "locked", timeout=timeout)
                if not acquired:
                    logger.info(f"Skipping task {func.__name__} - Lock '{key}' is already held.")
                    return None # Task is already running elsewhere
            except Exception as e:
                logger.error(f"Redis lock failed for {key}. Proceeding without lock (Fail Open). Error: {e}")
                acquired = True # Bypass lock

            try:
                if acquired:
                    logger.debug(f"Acquired lock '{key}' for {func.__name__}")
                return func(*args, **kwargs)
            finally:
                # Release the lock safely
                if acquired:
                    try:
                        cache.delete(key)
                        logger.debug(f"Released lock '{key}' for {func.__name__}")
                    except Exception as e:
                        logger.error(f"Failed to release Redis lock {key}: {e}")
                
        return wrapper
    return decorator
