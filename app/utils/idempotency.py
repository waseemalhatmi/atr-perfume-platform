import functools
from flask import request, jsonify
from app.extensions import cache
import logging

logger = logging.getLogger(__name__)

def idempotent(timeout=86400):
    """
    Enterprise Idempotency Middleware.
    Prevents duplicate POST/PUT requests using the 'Idempotency-Key' header.
    If the key was already seen, returns a 409 Conflict or the cached response.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            idempotency_key = request.headers.get('Idempotency-Key')
            if not idempotency_key:
                # If no key is provided, we just bypass (or we could enforce it)
                return func(*args, **kwargs)

            # To avoid key collision across different endpoints, prefix with path
            cache_key = f"idem:{request.path}:{idempotency_key}"
            
            cache_working = True
            try:
                # Check if we already processed this
                if cache.get(cache_key):
                    logger.warning(f"Idempotency hit! Duplicate request prevented for key: {idempotency_key}")
                    return jsonify({
                        "success": False, 
                        "error": "Duplicate request detected. Please wait or use a new Idempotency-Key."
                    }), 409

                # Mark as processed
                cache.set(cache_key, "processing", timeout=timeout)
            except Exception as e:
                logger.error(f"Redis Idempotency Check failed. Failing open: {e}")
                cache_working = False
            
            try:
                response = func(*args, **kwargs)
                return response
            except Exception:
                # If it failed, delete the key so they can retry
                if cache_working:
                    try:
                        cache.delete(cache_key)
                    except Exception as e:
                        logger.error(f"Redis Idempotency delete failed: {e}")
                raise
                
        return wrapper
    return decorator
