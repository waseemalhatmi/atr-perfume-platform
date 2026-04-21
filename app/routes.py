# app/routes.py
from flask import (
    current_app,
    Blueprint,
    render_template,
    abort,
    request,
    flash,
    redirect,
    url_for,
    jsonify
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from app.helpers.context import get_global_context, get_newsletter_context
from app.services.mailer import send_admin_email
from app.constants import TargetType, INTERACTION_TYPE
from app.services.pages_content import PAGES_CONTENT
from app.services.store_service import prepare_store_links
from app.services.interaction_service import *
from app.services.interest_service import (
    handle_interaction_interest,
)
from app.services.item_service import filter_items_by_country
from app.services.search_service import search_items
from app.services.price_service import get_item_price_history, record_daily_prices
from app.services.discovery_service import get_perfume_clones
from app.utils.parsing import parse_target_type, parse_interaction_type
from app.utils.request import get_client_ip, get_country
from sqlalchemy import func, or_

from datetime import datetime, timedelta
from app.models import (
    Section,
    Category,
    Brand,
    Topic,
    User,
    NewsletterSubscriber,
    Item,
    ItemVariant,
    Save,
    ItemClick,
    ItemStoreLink,
    ContactMessage,
    PriceAlert,
    PriceHistory,
    Notification,
    db)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
bp = Blueprint('main', __name__, static_folder='static')
# ------------------------
# Login route
# ------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        wants_newsletter = request.form.get('subscribe') is not None
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('main.register'))
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        newsletter_msg = None
        subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
        if subscriber:
            subscriber.user_id = user.id
            if wants_newsletter:
                newsletter_msg = 'Your existing newsletter subscription was linked 🎯'
            else:
                newsletter_msg = 'You already have subscribed to the newsletter with this email before'
        if wants_newsletter and not subscriber:
            db.session.add(NewsletterSubscriber(
                email=email,
                user_id=user.id,
                is_active=False
            ))
            newsletter_msg = 'You\'ve been subscribed to the newsletter 📬'
        db.session.commit()
        login_user(user)
        flash('Registration completed successfully 🎉', 'success')
        if newsletter_msg:
            flash(newsletter_msg, 'info')
        return redirect(url_for('main.home'))
    return render_template('register.html')

# Logout route

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))

# ================= USER DASHBOARD (PROFILE) =================
@bp.route('/profile')
@login_required
def profile():
    # Gather saved items (Wishlist)
    saves = current_user.saves
    saved_items = [save.item for save in saves if save.target_type == 'item' and save.item]
    
    return render_template('profile.html', saved_items=saved_items)

@bp.route('/profile/update-password', methods=['POST'])
@login_required
def update_password():
    data = request.form
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not current_user.provider:  # Only for local accounts
        if not current_user.check_password(old_password):
            flash("كلمة المرور الحالية غير صحيحة", "error")
            return redirect(url_for('main.profile', tab='settings'))
            
        if new_password != confirm_password:
            flash("كلمة المرور الجديدة غير متطابقة", "error")
            return redirect(url_for('main.profile', tab='settings'))
            
        if len(new_password) < 6:
            flash("كلمة المرور يجب أن تكون 6 أحرف على الأقل", "error")
            return redirect(url_for('main.profile', tab='settings'))
            
        current_user.set_password(new_password)
        db.session.commit()
        flash("تم تحديث كلمة المرور بنجاح!", "success")

    return redirect(url_for('main.profile', tab='settings'))

# ------------------------
# Specifying Country Using Cookies
@bp.route("/set-country", methods=["POST"])
def set_country():
    country = request.json.get("country")

    response = jsonify({"success": True})

    if country:
        response.set_cookie("country", country.lower(), max_age=60*60*24*365)
    else:
        # clear cookie if user selects "All"
        response.delete_cookie("country")

    return response
# Subscribe route
# ------------------------

@bp.route('/subscribe', methods=['POST'])
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
                guest_email, curr_email = request.form.getlist('email')
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
            'message': 'You have subscribed to the newsletter 📬',
            'html': render_template(
                    'partials/newsletter-block.html',
                    **get_newsletter_context()
                )
            })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again.'
            })

@bp.route('/unsubscribe', methods=['POST'])
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
        'message': 'You have unsubscribed from the newsletter.',
        'html': render_template(
                'partials/newsletter-block.html',
                **get_newsletter_context()
            )
        })

# ============== SEARCH LOGIC ================
@bp.route('/search', methods=['GET'])
def search():
    q = request.args.get('q')
    if not q:
        q = request.args.get('query', '').strip()
    else:
        q = q.strip()

    items = search_items(q)

    return render_template(
        'search-page.html',
        search_results=items,
        query=q,
        country=get_country()
    )

@bp.app_context_processor
def inject_global_context():
    return get_global_context()

@bp.route('/')
def home():
    # --- DB-backed items (perfumes) ---
    p_query = Item.query.options(
        db.joinedload(Item.brand),
        db.joinedload(Item.category),
        db.joinedload(Item.images)
    )

    items = p_query.limit(20).all()
    
    return render_template(
        "index.html",
        items=items
    )

@bp.route('/about')
def about():
    return render_template('about.html', cover_cards=PAGES_CONTENT.get('about', []))

@bp.route('/contact')
def contact():
    return render_template('contact.html', contact_cards=PAGES_CONTENT.get('contact', []))

@bp.route("/contact", methods=["POST"])
def send_contact_message():
    data = {k: request.form.get(k, "").strip() for k in
            ("name", "email", "subject", "message")}

    if not all(data.values()):
        return jsonify({
            "success": False,
            "error": "One or more fields are empty!!"
            })

    msg = ContactMessage(
        **data,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    db.session.add(msg)
    db.session.commit()

    send_admin_email(data)  # wrapped function

    current_app.logger.info(
        "Contact message saved (id=%s) from %s",
        msg.id, data["email"]
    )

    return jsonify({
        "success": True,
        "message": "Message sent successfully!!"
        })

@bp.route('/privacy')
def privacy():
    return render_template('privacy.html', content=PAGES_CONTENT.get('privacy'))

@bp.route('/terms')
def terms():
    return render_template('terms.html', content=PAGES_CONTENT.get('terms'))

@bp.route('/affiliate')
def affiliate():
    return render_template('affiliate.html', content=PAGES_CONTENT.get('affiliate'))

@bp.route("/items")
def items():
    query = Item.query.options(
        db.joinedload(Item.brand),
        db.joinedload(Item.category),
        db.joinedload(Item.images)
    )

    # Filtering by Category
    category_ids = request.args.getlist('category')
    if category_ids:
        query = query.filter(Item.category_id.in_(category_ids))

    # Filtering by Brand
    brand_ids = request.args.getlist('brand')
    if brand_ids:
        query = query.filter(Item.brand_id.in_(brand_ids))
        
    # Sorting
    sort_by = request.args.get('sort')
    if sort_by == 'newest':
        query = query.order_by(Item.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Item.created_at.asc())
    else:
        query = query.order_by(Item.created_at.desc()) # Default sort

    prods = query.limit(50).all()
    
    # Get filters data for sidebar
    categories = Category.query.order_by(Category.name).all()
    brands = Brand.query.order_by(Brand.name).all()

    # Preserve selected filters to check inputs
    selected_categories = category_ids
    selected_brands = brand_ids

    return render_template('items-page.html',
                           category='جميع العطور',
                           items=prods,
                           categories=categories,
                           brands=brands,
                           selected_categories=selected_categories,
                           selected_brands=selected_brands,
                           current_sort=sort_by)

@bp.route("/check-save-batch")
@login_required
def check_save_batch():
    target_types = request.args.getlist("type")
    target_ids = request.args.getlist("id")
    if len(target_types) != len(target_ids):
        abort(400, "Mismatched parameters")
    result = {}
    for t_str, id_str in zip(target_types, target_ids):
        try:
            target_type = parse_target_type(t_str)
        except ValueError:
            continue
        try:
            target_id = int(id_str)
        except (TypeError, ValueError):
            continue
        target = Item.query.get(target_id)
        if not target:
            continue
        saved = Save.query.filter_by(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id
        ).first()
        if saved:
            result[f"{t_str}:{id_str}"] = True
    return jsonify(result)

@bp.route("/item-click/<int:link_id>", methods=["POST"])
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
            # 🔢 increment item click_count once per 24h
            link.item.click_count = (link.item.click_count or 0) + 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Click tracking failed:", e)
    # Optional: user interaction tracking — fully isolated
    if current_user.is_authenticated:
        try:
            handle_interaction_interest(
                user=current_user,
                target=link.item,
                action="item_click"
            )
        except Exception as e:
            print("Interaction tracking failed:", e)
    return jsonify({"redirect_url": link.affiliate_url})

# ================= LUXURY FEATURES =================

@bp.route("/alerts/subscribe", methods=["POST"])
def subscribe_price_alert():
    data = request.json or request.form
    email = data.get('email', '').strip()
    item_id = data.get('item_id')
    target_price = data.get('target_price')

    if not all([email, item_id, target_price]):
        return jsonify({"success": False, "error": "المعلومات ناقصة لمعالجة الطلب"}), 400

    try:
        target_price = float(target_price)
    except ValueError:
        return jsonify({"success": False, "error": "السعر المستهدف غير صالح"}), 400

    existing = PriceAlert.query.filter_by(email=email, item_id=item_id, is_active=True).first()
    if existing:
        existing.target_price = target_price
        db.session.commit()
        return jsonify({"success": True, "message": "تم تحديث التنبيه بنجاح!"})

    user_id = current_user.id if current_user.is_authenticated else None
    alert = PriceAlert(
        email=email,
        item_id=item_id,
        user_id=user_id,
        target_price=target_price
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({"success": True, "message": "تم تسجيل التنبيه! سنراسلك فور انخفاض السعر."})


@bp.route("/quiz/recommend", methods=["POST"])
def quiz_recommend():
    data = request.json or {}
    
    # 1. Capture expanded inputs
    gender = data.get('gender', '')      # رجالي, نسائي, للجنسين
    apparel = data.get('apparel', '')    # suit, casual, sport
    activity = data.get('activity', '')  # office, outdoor, nightout
    weather = data.get('weather', '')    # cold, hot
    vibe = data.get('vibe', '')          # mysterious, bold, clean, sweet
    
    # 2. Define Keyword Weighting Map
    weights = []
    
    # Simple direct filters
    if gender == 'نسائي': weights.append('نسائ')
    elif gender == 'رجالي': weights.append('رجالي')
    
    # Style/Apparel mappings
    if apparel == 'suit': weights.extend(['فخم', 'رسمي', 'أنيق', 'Luxury', 'Elegant'])
    elif apparel == 'casual': weights.extend(['يومي', 'كاجوال', 'منعش', 'Daily', 'Casual'])
    elif apparel == 'sport': weights.extend(['رياضي', 'نشاط', 'Sport', 'Fresh'])
    
    # Activity mappings
    if activity == 'office': weights.extend(['هادئ', 'نظيف', 'الدوام', 'Office', 'Professional'])
    elif activity == 'outdoor': weights.extend(['صيفي', 'خارجية', 'Summer', 'Outdoor'])
    elif activity == 'nightout': weights.extend(['سهرة', 'حفلة', 'جذاب', 'Night', 'Clubbing'])
    
    # Weather mappings
    if weather == 'cold': weights.extend(['عود', 'خشب', 'دافئ', 'Winter', 'Oud', 'Warm'])
    elif weather == 'hot': weights.extend(['حمضيات', 'بحر', 'انتعاش', 'Summer', 'Citrus', 'Oceanic'])
    
    # Vibe mappings
    if vibe == 'mysterious': weights.extend(['غامض', 'بخور', 'جلد', 'Mysterious', 'Smoky'])
    elif vibe == 'bold': weights.extend(['قوي', 'جريء', 'توابل', 'Bold', 'Strong'])
    elif vibe == 'clean': weights.extend(['مسك', 'بودرة', 'Clean', 'Musk', 'Powdery'])
    
    # 3. Fetch Items and Score them
    items = Item.query.options(db.joinedload(Item.images), db.joinedload(Item.brand)).all()
    scored_items = []
    
    for item in items:
        score = 0
        desc = (item.description or "").lower()
        name = item.name.lower()
        
        # Gender is a critical filter
        if gender == 'نسائي' and 'رجالي' in desc and 'نسائ' not in desc: continue
        if gender == 'رجالي' and 'نسائ' in desc and 'رجالي' not in desc: continue
        
        for kw in weights:
            if kw.lower() in desc or kw.lower() in name:
                score += 1
        
        if score > 0:
            scored_items.append((item, score))
            
    # Sort by score and pick top 3
    scored_items.sort(key=lambda x: x[1], reverse=True)
    results = [s[0] for s in scored_items[:3]]
    
    # Fallback if no specific matches
    if not results:
        results = Item.query.options(db.joinedload(Item.images), db.joinedload(Item.brand)).order_by(db.func.random()).limit(3).all()

    html = render_template('partials/quiz-results.html', items=results)
    return jsonify({"success": True, "html": html})

# --- Price & Notification APIs ---

@bp.route("/api/items/<int:item_id>/price-history")
def api_price_history(item_id):
    history = get_item_price_history(item_id)
    return jsonify(history)

@bp.route("/api/notifications")
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()
    
    return jsonify({
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
            } for n in notifications
        ]
    })

@bp.route("/api/notifications/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    notification = Notification.query.filter_by(
        id=notif_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    return jsonify({"success": True})

# --- For Testing: Run Price Tracker ---
@bp.route("/admin/run-price-tracker")
@login_required
def admin_run_price_tracker():
    # Only allow for admin (checking email for now)
    if current_user.email != "admin@atr.com": # Replace with your admin logic
         # flash("Unauthorized", "error")
         # return redirect(url_for('main.home'))
         pass # Allow for dev testing
         
    count, alerts = record_daily_prices()
    return jsonify({"recorded": count, "alerts_triggered": alerts})

# ===================================================

@bp.route("/item/<int:item_id>/view_full_specs", methods=["POST"])
def view_full_specs(item_id):
    item = Item.query.get_or_404(item_id)
    html = render_template(
        "components/features/full-details.html",  # fixed: was full-specs.html (doesn't exist)
        full_details=item.full_details             # fixed: was item.full_specs (doesn't exist)
    )
    return jsonify({
        "html": html
    })

@bp.route("/items/<int:item_id>")
def item_page(item_id):
    item = Item.query.options(
        db.selectinload(Item.variants)
            .selectinload(ItemVariant.store_links)
            .selectinload(ItemStoreLink.store),
        db.selectinload(Item.images)
    ).get_or_404(item_id)

    user = current_user if current_user.is_authenticated else None
    ip = None if user else get_client_ip()
    record_view(
        item,
        TargetType.PRODUCT,
        user,
        ip)
    
    # Fetch clones for current item
    clones = get_perfume_clones(item_id, limit=4)

    return render_template(
        "item-page.html",
        item=item,
        clones=clones
    )

@bp.route("/handle-interaction", methods=["POST"])
@login_required
def handle_interaction():
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
        current_app.logger.exception("Interaction failed")
        abort(500, "Interaction failed")


# ============================================================
# Google OAuth Routes
# ============================================================

@bp.route('/login/google')
def google_login():
    """Redirect the user to Google's OAuth consent screen."""
    redirect_uri = url_for('main.google_callback', _external=True)
    return current_app.google.authorize_redirect(redirect_uri)


@bp.route('/google/callback')
def google_callback():
    """Handle the OAuth2 callback from Google."""
    try:
        token = current_app.google.authorize_access_token()
    except Exception as e:
        current_app.logger.error("Google OAuth token error: %s", e)
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('main.login'))

    # Fetch the user profile from Google
    user_info = current_app.google.get('userinfo').json()
    google_id = user_info.get('id')
    email = user_info.get('email')

    if not google_id or not email:
        flash('Could not retrieve account information from Google.', 'error')
        return redirect(url_for('main.login'))

    # Find existing user by google_id or email
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account to Google
            user.google_id = google_id
            user.provider = 'google'
            db.session.commit()
        else:
            # Create a new account
            user = User(
                email=email,
                google_id=google_id,
                provider='google',
                password_hash='google-oauth-no-password'
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully via Google! 🎉', 'success')

    login_user(user)
    flash(f'Welcome back, {email}! 👋', 'success')
    return redirect(url_for('main.home'))

@bp.route('/ui-test')
def ui_test():
    """Temporary route to visualize and test UI components."""
    return render_template('ui-test.html')

