from flask import Flask

def init_celery(app: Flask):
    """
    Enterprise-Grade Celery Initialization.
    Injects Flask app context into Celery tasks.
    """
    from celery import Celery

    celery_app = Celery(
        app.import_name,
        broker=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
        backend=app.config.get("REDIS_URL", "redis://localhost:6379/0")
    )

    celery_app.conf.update(app.config)

    # Enterprise Queue Management (Fix #1, #2, #13)
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_time_limit=300, # Hard timeout (killed) - Fix #1
        task_soft_time_limit=240, # Soft timeout (exception raised)
        task_acks_late=True, # Ensure no task is lost if worker crashes
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1, # Fair dispatch - Fix #1
        worker_max_tasks_per_child=1000, # Fix #13: Prevent memory leaks by restarting workers
        worker_max_memory_per_child=256000, # 256MB per worker child max
        task_routes={
            'app.tasks.*': {'queue': 'default'},
            'dead_letter.*': {'queue': 'failed_tasks'} # Fix #2: Dead Letter Queue definition
        }
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    app.extensions["celery"] = celery_app

    # ── Celery Beat Schedule (Periodic Tasks) ─────────────────────────────────
    # Requires a beat worker: celery -A celery_worker.celery beat --loglevel=info
    from celery.schedules import crontab
    celery_app.conf.beat_schedule = {
        # Runs every night at 03:00 UTC — low-traffic window.
        # Deletes view rows older than 90 days in batches of 1000 to keep the
        # views table bounded and dedup queries fast at any user scale.
        "nightly-prune-old-views": {
            "task":     "tasks.prune_old_views",
            "schedule": crontab(hour=3, minute=0),
            "kwargs":   {"retention_days": 90, "batch_size": 1000},
        },
    }

    return celery_app

