import secrets
from werkzeug.security import generate_password_hash
from flask import current_app, Blueprint, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, NewsletterSubscriber, db
from app import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ─── Helpers ────────────────────────────────────────────────────────────────

def _serialize_user(user):
    return {
        "id":       user.id,
        "email":    user.email,
        "is_admin": user.is_admin,
        "provider": user.provider,
        "is_subscribed": bool(
            user.newsletter_subscription and
            not user.newsletter_subscription.unsubscribed_at
        ),
    }

# ─── Routes ─────────────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@limiter.exempt
def me():
    """Return the currently logged-in user, or 401 if anonymous."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({"success": True, "data": _serialize_user(current_user)})


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "البريد الإلكتروني وكلمة المرور مطلوبان."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "البريد الإلكتروني أو كلمة المرور غير صحيحة."}), 401

    login_user(user, remember=data.get("remember", False))
    return jsonify({"success": True, "data": _serialize_user(user)})


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    wants_nl = bool(data.get("subscribe", False))

    if not email or not password:
        return jsonify({"success": False, "error": "البريد الإلكتروني وكلمة المرور مطلوبان."}), 400
    # NIST SP 800-63B minimum: 8 characters. 6 chars (~308B combos) is trivially
    # brute-forced. 8 chars with a 5/min rate limit still provides adequate protection.
    if len(password) < 8:
        return jsonify({"success": False, "error": "كلمة المرور يجب أن تكون 8 أحرف على الأقل."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "البريد الإلكتروني مسجل مسبقاً."}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if wants_nl:
        subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        if subscriber:
            subscriber.user_id = user.id
        else:
            db.session.add(NewsletterSubscriber(email=email, user_id=user.id, is_active=True))

    db.session.commit()
    login_user(user)
    return jsonify({"success": True, "data": _serialize_user(user)}), 201


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "تم تسجيل الخروج بنجاح."})


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """Return profile data including saved items."""
    saves = current_user.saves or []
    saved_items = []
    for save in saves:
        if save.target_type == "item" and save.item:
            item = save.item
            saved_items.append({
                "id":       item.id,
                "name":     item.name,
                "slug":     item.slug,
                "brand":    item.brand.name if item.brand else None,
                "category": item.category.name if item.category else None,
                "images":   [{"path": img.image_path} for img in item.images],
                "min_price": float(min(
                    (l.price for v in item.variants for l in v.store_links if l.is_active and l.price),
                    default=0
                )),
            })
    return jsonify({
        "success": True,
        "data": {
            "user":           _serialize_user(current_user),
            "saved_items":    saved_items,
            "saved_item_ids": [s.target_id for s in current_user.saves if s.target_type == 'item'],
            "alert_item_ids": [a.item_id for a in current_user.price_alerts if a.is_active],
        },
    })


@auth_bp.route("/update-password", methods=["POST"])
@login_required
def update_password():
    data             = request.get_json(silent=True) or {}
    old_password     = data.get("old_password", "")
    new_password     = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if current_user.provider:
        return jsonify({"success": False, "error": "حسابات Google لا تدعم تغيير كلمة المرور."}), 400
    if not current_user.check_password(old_password):
        return jsonify({"success": False, "error": "كلمة المرور الحالية غير صحيحة."}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "كلمة المرور الجديدة غير متطابقة."}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "كلمة المرور يجب أن تكون 6 أحرف على الأقل."}), 400

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "تم تحديث كلمة المرور بنجاح!"})


# ─── Google OAuth (keeps redirect flow, ends at React SPA) ──────────────────

@auth_bp.route("/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return current_app.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    import os
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    try:
        token = current_app.google.authorize_access_token()
    except Exception as e:
        current_app.logger.error("Google OAuth error: %s", e)
        return redirect(f"{frontend_url}/?auth_error=google_failed")

    user_info = current_app.google.get("userinfo").json()
    google_id  = user_info.get("id")
    email      = user_info.get("email")

    if not google_id or not email:
        return redirect(f"{frontend_url}/?auth_error=google_no_profile")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.provider  = "google"
            db.session.commit()
        else:
            user = User(email=email, google_id=google_id, provider="google",
                        password_hash=generate_password_hash(secrets.token_hex(32)))
            db.session.add(user)
            db.session.commit()

    login_user(user)
    return redirect(f"{frontend_url}/")
