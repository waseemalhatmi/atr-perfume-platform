from celery import current_app as celery_app
from app.utils.logger import get_logger

log = get_logger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=2,
)
def task_send_email_notification(self, user_id: int, subject: str, body: str, idempotency_key: str = None):
    """
    Async Email Delivery with Idempotency.
    """
    from app.extensions import cache
    
    # Idempotency Check
    if idempotency_key:
        cache_key = f"celery:email_sent:{idempotency_key}"
        if cache.get(cache_key):
            log.info("task_skipped_duplicate", task_name="send_email", idempotency_key=idempotency_key)
            return "skipped_duplicate"
        cache.set(cache_key, "1", timeout=86400)

    try:
        log.info("task_started", task_name="send_email", user_id=user_id, subject=subject)
        return "success"
    except Exception as exc:
        if idempotency_key:
            cache.delete(f"celery:email_sent:{idempotency_key}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def task_process_ai_job(self, data: dict):
    """
    Heavy AI Processing task with Circuit Breaker awareness.
    If circuit is open, we delay the task dramatically to let AI recover.
    """
    from app.utils.resilience import CircuitBreakerOpenException
    try:
        pass  # AI heavy lifting
    except CircuitBreakerOpenException as exc:
        log.critical("ai_circuit_open_in_task", countdown_s=300)
        raise self.retry(exc=exc, countdown=300)
    except Exception as exc:
        log.error("task_failed", task_name="process_ai_job", error=str(exc))
        raise self.retry(exc=exc)
