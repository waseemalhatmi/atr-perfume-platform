from flask import Flask
from celery import Celery

# ── Global Singleton Celery Instance (Fix #1, #2) ──────────────────────────
# This allows 'main.py' and 'tasks.py' to import a consistent app instance.
celery_app = Celery(__name__)

def init_celery(app: Flask):
    """
    Enterprise-Grade Celery Initialization.
    Injects Flask app context into Celery tasks and syncs configuration.
    """
    global celery_app
    
    # Configure broker/backend from Flask config
    broker_url = app.config.get("REDIS_URL", "redis://localhost:6379/0")

    # Fix: Celery's Redis backend is strict about rediss:// URLs.
    # It requires the ssl_cert_reqs parameter inside the URL string itself.
    if broker_url and broker_url.startswith("rediss://") and "ssl_cert_reqs" not in broker_url:
        sep = "&" if "?" in broker_url else "?"
        broker_url = f"{broker_url}{sep}ssl_cert_reqs=none"
    
    celery_app.conf.update(
        broker_url=broker_url,
        result_backend=broker_url,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_time_limit=300,
        task_soft_time_limit=240,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_max_memory_per_child=256000,
        task_routes={
            'app.tasks.*': {'queue': 'default'},
        }
    )

    # Handle SSL/TLS for rediss:// (Fix for Upstash/Cloud Redis)
    if broker_url and broker_url.startswith("rediss://"):
        celery_app.conf.broker_use_ssl = {
            'ssl_cert_reqs': None # Trust self-signed/cloud certs
        }
        celery_app.conf.redis_backend_use_ssl = {
            'ssl_cert_reqs': None
        }

    # Inject Flask context into tasks
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    app.extensions["celery"] = celery_app
    
    # ── Celery Beat Schedule (Periodic Tasks) ─────────────────────────────────
    from celery.schedules import crontab
    celery_app.conf.beat_schedule = {
        "nightly-prune-old-views": {
            "task":     "tasks.prune_old_views",
            "schedule": crontab(hour=3, minute=0),
            "kwargs":   {"retention_days": 90, "batch_size": 1000},
        },
        "nightly-sync-all-feeds": {
            "task":     "tasks.sync_all_feeds",
            "schedule": crontab(hour=2, minute=0),
        },
        "record-daily-prices": {
            "task":     "tasks.record_daily_prices",
            "schedule": crontab(hour=4, minute=0),
        },
        "nightly-download-images": {
            "task":     "tasks.download_remote_images",
            "schedule": crontab(hour=5, minute=0),
        },
    }

    return celery_app


