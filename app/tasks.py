from celery import current_app as celery_app
from celery.exceptions import SoftTimeLimitExceeded, MaxRetriesExceededError
from app.utils.logger import get_logger

# Structured JSON logger — replaces stdlib logging.getLogger
log = get_logger(__name__)

# ─── Celery Tasks with Enterprise Reliability ─────────────────────────────

@celery_app.task(queue="failed_tasks")
def task_dead_letter(task_name: str, args: list, kwargs: dict, error: str):
    """Dead Letter Queue processor. Handles permanently failed tasks."""
    log.critical("dead_letter_queue", task_name=task_name, args=args, error=error)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=120
)
def task_refresh_item_recommendations(self, item_id: int):
    """
    Async Recommendation Generation Task.
    refresh_item_recommendations() uses flush() only — we commit here.
    """
    try:
        from app.extensions import db
        from app.services.discovery_service import refresh_item_recommendations

        log.info("task_started", task_name="refresh_recommendations", item_id=item_id)
        refresh_item_recommendations(item_id)
        try:
            db.session.commit()
        except Exception as commit_exc:
            db.session.rollback()
            raise commit_exc

        log.info("task_succeeded", task_name="refresh_recommendations", item_id=item_id)

    except SoftTimeLimitExceeded as exc:
        log.error("task_time_limit_exceeded", task_name="refresh_recommendations", item_id=item_id)
        raise self.retry(exc=exc)
    except MaxRetriesExceededError as exc:
        log.error("task_max_retries", task_name="refresh_recommendations", item_id=item_id)
        task_dead_letter.apply_async(
            args=[self.name, [item_id], {}, str(exc)],
            queue="failed_tasks"
        )
        raise
    except Exception as exc:
        log.warning("task_failed_retrying", task_name="refresh_recommendations", item_id=item_id, error=str(exc))
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            task_dead_letter.apply_async(
                args=[self.name, [item_id], {}, str(exc)],
                queue="failed_tasks"
            )
            raise


# ─── Nightly Maintenance: Views Table Archival ────────────────────────────
#
# WHY THIS EXISTS:
#   The `views` table grows at ~(DAU × avg_views_per_user) rows/day.
#   At 10k DAU × 10 views = 100k rows/day → 36.5M rows/year.
#   The deduplication query in record_view() only needs the LAST 24 HOURS.
#   The all-time aggregate is already stored durably in Item.view_count.
#   Therefore, rows older than 90 days are pure storage waste and slow queries.
#
# HOW BATCH DELETION WORKS:
#   A single DELETE of millions of rows holds an exclusive lock for its full
#   duration, blocking concurrent reads/writes. Batching (1000 rows per commit)
#   keeps each individual lock window tiny (~1ms), invisible to users.
#
# SCHEDULE: Registered in celery_ext.py beat_schedule → runs daily at 03:00 UTC.

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,   # 5 min between retries
    soft_time_limit=600,       # 10 min soft limit — commits progress, retries
    name="tasks.prune_old_views"
)
def task_prune_old_views(self, retention_days: int = 90, batch_size: int = 1000):
    """
    Nightly maintenance: deletes view rows older than `retention_days` days in batches.

    Args:
        retention_days: Rows older than this are deleted. Default: 90 days.
        batch_size: Number of rows deleted per DB commit. Default: 1000.

    Returns:
        dict: {"deleted": <total_rows_deleted>}
    """
    from datetime import datetime, timedelta
    from app.extensions import db
    from app.models import View

    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    total_deleted = 0

    log.info("task_started", task_name="prune_old_views", retention_days=retention_days)

    try:
        while True:
            # Fetch IDs of the oldest batch to avoid a single massive DELETE lock.
            # We SELECT first, then DELETE by ID — this pattern is the safest for
            # PostgreSQL because it uses the primary key index, not a sequential scan.
            ids = [
                row.id for row in
                View.query
                .filter(View.created_at < cutoff)
                .with_entities(View.id)
                .limit(batch_size)
                .all()
            ]
            if not ids:
                break  # No more rows to delete

            deleted = View.query.filter(
                View.id.in_(ids)
            ).delete(synchronize_session=False)
            db.session.commit()
            total_deleted += deleted

            log.info(
                "prune_batch_committed",
                task_name="prune_old_views",
                batch_deleted=deleted,
                total_deleted=total_deleted,
            )

        log.info(
            "task_succeeded",
            task_name="prune_old_views",
            total_deleted=total_deleted,
            retention_days=retention_days,
        )
        return {"deleted": total_deleted}

    except SoftTimeLimitExceeded:
        # Time limit hit — commit progress so far, retry will continue from cutoff
        db.session.commit()
        log.warning(
            "task_soft_limit_exceeded",
            task_name="prune_old_views",
            total_deleted_so_far=total_deleted,
        )
        raise self.retry()
    except Exception as exc:
        db.session.rollback()
        log.error("task_failed", task_name="prune_old_views", error=str(exc))
        raise self.retry(exc=exc)
