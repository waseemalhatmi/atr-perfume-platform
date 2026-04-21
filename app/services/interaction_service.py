from datetime import datetime, timedelta
from app.models import View, Save, db
from app.services.interest_service import handle_interaction_interest

def viewer_filter(query, user, ip_address):
    if user:
        return query.filter(View.user_id == user.id)
    return query.filter(
        View.user_id.is_(None),
        View.ip_address == ip_address
    )

def record_view(
    target,
    target_type,
    user=None,
    ip_address=None
):
    
    if not user and not ip_address:
        return {
            'success': False,
            'error' : "couldn't detect user"
        }
    
    cutoff = datetime.utcnow() - timedelta(hours=24)

    query = View.query.filter(
        View.target_type == target_type,
        View.target_id == target.id,
        View.created_at > cutoff
    )

    query = viewer_filter(query, user, ip_address)

    if query.first():
        return {
            'success': False,
            'error' : "already viewed"
        }

    view = View(
        user_id=user.id if user else None,
        ip_address=ip_address,
        target_type=target_type,
        target_id=target.id
    )
    db.session.add(view)

    target.view_count = (target.view_count or 0) + 1
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
