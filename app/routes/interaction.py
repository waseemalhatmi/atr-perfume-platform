from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    abort
)
from flask_login import (
    login_required,
    current_user
)
from app.helpers.context import get_newsletter_context
from app.services.interest_service import handle_interaction_interest
from app.utils.parsing import parse_target_type, parse_interaction_type
from app.constants import INTERACTION_TYPE
from app.models import (
    NewsletterSubscriber,
    Item,
    Save,
    ItemClick,
    ItemStoreLink,
    PriceAlert,
    db
)
from app import limiter
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
from datetime import datetime, timedelta

interaction_bp = Blueprint('interaction', __name__)

from app.utils.idempotency import idempotent

@interaction_bp.route('/subscribe', methods=['POST'])
@limiter.limit("20 per hour;5 per minute")
@idempotent(timeout=3600)
def subscribe():
    message = None
    try:
        mode = request.form.get('mode')
        email = None
        user_id = None
        # Guest user
        if not current_user.is_authenticated:
            if mode == 'account':
                message = 'You must be logged in to use account subscription.'
            else:
                email = request.form.get('email')
        # Logged-in user
        else:
            if mode not in ('guest', 'account'):
                message = 'Invalid subscription mode.'
            else:
                emails = request.form.getlist('email')
                guest_email = emails[0] if len(emails) > 0 else None
                curr_email = emails[1] if len(emails) > 1 else None
                
                if mode == 'guest' and not guest_email:
                    message = 'Please, fill in this field.'
                else:
                    if mode == 'account':
                        email = curr_email
                        user_id = current_user.id
                    else:
                        email = guest_email
        # Stop early if error happened
        if message:
            return jsonify({
                'success': False,
                'error': message
                })
        # Check if email belongs to another user
        from app.models import User
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and (not current_user.is_authenticated or existing_user.id != current_user.id):
            return jsonify({
                'success': False,
                'error': 'This email is registered by another user. Please use your own account to subscribe.'
                })
        # Check existing subscription
        subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        if subscriber and not subscriber.unsubscribed_at:
            return jsonify({
                'success': False,
                'error': 'This email is already subscribed.'
                })
        # Re-subscribe or create
        if subscriber:
            subscriber.unsubscribed_at = None
            if user_id:
                subscriber.user_id = user_id
        else:
            subscriber = NewsletterSubscriber(
                email=email,
                user_id=user_id,
                is_active=True
            )
            db.session.add(subscriber)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'You have subscribed to the newsletter 📬'
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Subscription failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ أثناء معالجة الطلب. يرجى المحاولة لاحقاً.'
            })

@interaction_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    subscriber = current_user.newsletter_subscription
    if not subscriber or subscriber.unsubscribed_at:
        return jsonify({
            'success': False,
            'error': 'You are not subscribed.'
            })
    subscriber.unsubscribed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'You have unsubscribed from the newsletter.'
    })

@interaction_bp.route("/check-save-batch")
@login_required
def check_save_batch():
    """
    FIXED: Was N+1 (2 queries per item). Now uses 2 batch IN queries total.
    """
    target_types = request.args.getlist("type")
    target_ids   = request.args.getlist("id")

    if len(target_types) != len(target_ids):
        abort(400, "Mismatched parameters")

    # ── Parse and validate all inputs first ──────────────────────────────────
    parsed = []
    for t_str, id_str in zip(target_types, target_ids):
        try:
            target_type = parse_target_type(t_str)
            target_id   = int(id_str)
        except (ValueError, TypeError):
            continue
        parsed.append((t_str, id_str, target_type, target_id))

    if not parsed:
        return jsonify({})

    all_ids = [p[3] for p in parsed]

    # ── 1 query: verify which item IDs actually exist ─────────────────────────
    existing_ids = {
        row.id for row in
        Item.query.filter(Item.id.in_(all_ids)).with_entities(Item.id).all()
    }

    # ── 1 query: fetch all saves for this user in one shot ────────────────────
    saved_set = {
        (s.target_type, s.target_id)
        for s in Save.query.filter(
            Save.user_id    == current_user.id,
            Save.target_id.in_(all_ids),
        ).all()
    }

    # ── Build response ────────────────────────────────────────────────────────
    result = {}
    for t_str, id_str, target_type, target_id in parsed:
        if target_id not in existing_ids:
            continue
        if (target_type, target_id) in saved_set:
            result[f"{t_str}:{id_str}"] = True

    return jsonify(result)


@interaction_bp.route("/item-click/<int:link_id>", methods=["POST"])
@limiter.limit("120 per hour; 10 per minute")
def item_click(link_id):
    link = ItemStoreLink.query.get_or_404(link_id)
    user_id = current_user.id if current_user.is_authenticated else None
    ip_address = request.remote_addr if not user_id else None
    last_24h = datetime.utcnow() - timedelta(hours=24)
    # 🔒 Deduplicate click
    existing = ItemClick.query.filter(
        ItemClick.item_store_link_id == link.id,
        ItemClick.created_at >= last_24h,
        (
            ItemClick.user_id == user_id
            if user_id else
            ItemClick.ip_address == ip_address
        )
    ).first()
    if not existing:
        try:
            click = ItemClick(
                item_store_link_id=link.id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=request.headers.get("User-Agent"),
                referrer=request.referrer,
                country=request.headers.get("CF-IPCountry")
            )
            db.session.add(click)
            # ── Atomic SQL-level increment (Race Condition Fix) ───────────────
            # Use link.variant.item_id (FK integer) to avoid loading the full
            # Item object into memory just to read and rewrite a counter.
            db.session.execute(
                update(Item)
                .where(Item.id == link.variant.item_id)
                .values(click_count=Item.click_count + 1)
                .execution_options(synchronize_session=False)
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Click tracking failed for link_id {link_id}: {str(e)}")
    # Optional: user interaction tracking — fully isolated
    if current_user.is_authenticated:
        try:
            handle_interaction_interest(
                user=current_user,
                target=link.variant.item,
                action="item_click"
            )
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Interaction tracking interest failed: {str(e)}")
    return jsonify({"redirect_url": link.affiliate_url})

@interaction_bp.route("/handle-interaction", methods=["POST"])
@login_required
@limiter.limit("30 per minute")
def handle_interaction():
    from app.services.interaction_service import save_item
    try:
        target_type = parse_target_type(request.form.get("type"))
        target_id = int(request.form.get("id"))
        interaction_type = parse_interaction_type(request.form.get("interaction_type"))
        
        target = Item.query.get_or_404(target_id)
        
        result = None
        if interaction_type == INTERACTION_TYPE.SAVE:
            result = save_item(current_user, target_type, target_id)
        
        if not result or not result.get("success"): return jsonify(result or {"success": False}), 400
        
        handle_interaction_interest(user=current_user, target=target, action="save")
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception("Interaction failed")
        abort(500, "Interaction failed")

@interaction_bp.route("/alerts/subscribe", methods=["POST"])
@limiter.limit("20 per hour;5 per minute")
def subscribe_price_alert():
    data = request.json or request.form
    
    # 1. Email Handling (Optional if logged in)
    email = data.get('email', '').strip()
    if not email and current_user.is_authenticated:
        email = current_user.email
        
    item_id = data.get('item_id')
    target_price = data.get('target_price')

    if not all([email, item_id, target_price]):
        return jsonify({"success": False, "error": "المعلومات ناقصة لمعالجة الطلب"}), 400

    try:
        target_price = float(target_price)
    except ValueError:
        return jsonify({"success": False, "error": "السعر المستهدف غير صالح"}), 400

    from app.models import Notification, Item

    # 2. Update or Create Alert
    existing = PriceAlert.query.filter_by(email=email, item_id=item_id, is_active=True).first()
    item = Item.query.get(item_id)
    item_name = item.name if item else "العطر"
    
    if existing:
        existing.target_price = target_price
        
        # Add Notification if logged in
        if current_user.is_authenticated:
            notif = Notification(
                user_id=current_user.id,
                title="تحديث تنبيه السعر 🔔",
                message=f"تم تحديث السعر المستهدف لـ {item_name} إلى {target_price} ر.س",
                link=f"/items/{item_id}"
            )
            db.session.add(notif)
            
        db.session.commit()
        return jsonify({"success": True, "message": "تم تحديث التنبيه بنجاح!"})

    # New Alert
    user_id = current_user.id if current_user.is_authenticated else None
    alert = PriceAlert(
        email=email,
        item_id=item_id,
        user_id=user_id,
        target_price=target_price
    )
    db.session.add(alert)
    
    # Add Notification if logged in
    if current_user.is_authenticated:
        notif = Notification(
            user_id=current_user.id,
            title="تنبيه سعر جديد 🎯",
            message=f"سنقوم بإعلامك فور انخفاض سعر {item_name} إلى {target_price} ر.س أو أقل.",
            link=f"/items/{item_id}"
        )
        db.session.add(notif)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Price alert subscription failed: {str(e)}")
        return jsonify({"success": False, "error": "حدث خطأ في قاعدة البيانات"}), 500

    return jsonify({"success": True, "message": "تم تسجيل التنبيه! سنراسلك فور انخفاض السعر."})

@interaction_bp.route("/api/alerts/item/<int:item_id>", methods=["DELETE"])
@login_required
def delete_price_alert(item_id):
    alert = PriceAlert.query.filter_by(user_id=current_user.id, item_id=item_id, is_active=True).first()
    if not alert:
        return jsonify({"success": False, "error": "لا يوجد تنبيه نشط لهذا العطر"}), 404
    
    alert.is_active = False
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"success": False, "error": "حدث خطأ أثناء إلغاء التنبيه"}), 500
        
    return jsonify({"success": True, "message": "تم إلغاء التنبيه بنجاح"})

# ── Notifications API ─────────────────────────────────────────────────────────

@interaction_bp.route("/api/notifications", methods=["GET"])
@login_required
def get_notifications():
    from app.models import Notification
    
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    # Cap per_page to avoid abuse
    per_page = min(per_page, 50)
    
    pagination = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
        
    data = [{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "link": n.link,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in pagination.items]
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    return jsonify({
        "success": True, 
        "data": data, 
        "unread_count": unread_count,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    })

@interaction_bp.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def read_notification(notif_id):
    from app.models import Notification
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({"success": True})

@interaction_bp.route("/api/notifications/read-all", methods=["POST"])
@login_required
def read_all_notifications():
    from app.models import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})
