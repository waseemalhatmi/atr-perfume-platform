from datetime import datetime, timedelta
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from app.models import View, Save, Item, db
from app.services.interest_service import handle_interaction_interest

def viewer_filter(query, user, ip_address):
    if user:
        return query.filter(View.user_id == user.id)
    return query.filter(
        View.user_id.is_(None),
        View.ip_address == ip_address
    )

def record_view(target, target_type, user=None, ip_address=None):
    if not user and not ip_address:
        return {'success': False, 'error': "couldn't detect user"}

    cutoff = datetime.utcnow() - timedelta(hours=24)

    # ── Fast-path: 24-hour dedup check (covered by ix_views_dedup index) ───────
    # This is NOT the sole guard against duplicates — the partial unique indexes
    # (uq_view_user / uq_view_ip) are the true last line of defence.
    # We keep this check so we return 'already viewed' quickly without attempting
    # an INSERT that we know will conflict.
    query = View.query.filter(
        View.target_type == target_type,
        View.target_id == target.id,
        View.created_at >= cutoff
    )
    query = viewer_filter(query, user, ip_address)
    if query.first():
        return {'success': False, 'error': "already viewed"}

    # ── Atomic INSERT with IntegrityError guard (Fix #7 — TOCTOU Race) ────────
    # Two concurrent requests can BOTH pass the check above before either inserts.
    # The IntegrityError catch ensures the unique partial index is the final arbiter.
    # If both threads insert simultaneously, the losing thread gets IntegrityError
    # and returns 'already viewed' safely — no duplicate row is ever committed.
    try:
        view = View(
            user_id=user.id if user else None,
            ip_address=ip_address,
            target_type=target_type,
            target_id=target.id
        )
        db.session.add(view)
        db.session.flush()  # Trigger constraint check before committing
    except IntegrityError:
        db.session.rollback()
        return {'success': False, 'error': "already viewed"}

    # ── Atomic SQL-level increment (Race Condition Fix) ────────────────────
    # Never read-modify-write counters in Python under concurrent load.
    # A single UPDATE...SET view_count = view_count + 1 is atomic at the DB level.
    db.session.execute(
        update(Item)
        .where(Item.id == target.id)
        .values(view_count=Item.view_count + 1)
        .execution_options(synchronize_session=False)
    )
    if user:
      handle_interaction_interest(
          user=user,
          target=target,
          action="view"
      )

    db.session.commit()
    return {
        'success': True,
        'status' : "viewed"
    }

def save_item(user, target_type, target_id):
    existing = Save.query.filter_by(
        user_id=user.id,
        target_type=target_type,
        target_id=target_id
    ).first()

    status = 'saved'

    if existing:
        db.session.delete(existing)
        status = 'unsaved'
    else:
        save = Save(
            user_id=user.id,
            target_type=target_type,
            target_id=target_id
        )
        db.session.add(save)

    return {"success": True, "status": status}
