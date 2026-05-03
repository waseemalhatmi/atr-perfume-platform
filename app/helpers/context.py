# app/helpers/context.py
import time
from flask_login import current_user
from app.models import Setting
from sqlalchemy.exc import SQLAlchemyError

# ============================================================
# SETTINGS CACHE — Avoid DB hit on EVERY request
# TTL: 5 minutes (300 seconds). Settings rarely change.
# ============================================================
_settings_cache = {
    "data": None,
    "expires_at": 0
}
_SETTINGS_TTL = 300  # 5 minutes

def get_user_context():
    is_authenticated = current_user.is_authenticated
    user_email = None
    is_subscribed = False
    is_admin = False

    if is_authenticated:
        user_email = current_user.email
        is_admin = getattr(current_user, 'is_admin', False)

        sub = getattr(current_user, "newsletter_subscription", None)
        if sub and not sub.unsubscribed_at:
            is_subscribed = True

    return {
        "is_authenticated": is_authenticated,
        "user_email": user_email,
        "is_subscribed": is_subscribed,
        "is_admin": is_admin
    }

def get_site_settings():
    """Fetch all settings from DB with in-memory TTL cache."""
    now = time.time()
    
    if _settings_cache["data"] is not None and now < _settings_cache["expires_at"]:
        return _settings_cache["data"]
    
    try:
        all_settings = Setting.query.all()
        result = {s.key: s.value for s in all_settings}
    except SQLAlchemyError:
        result = {}
    
    _settings_cache["data"] = result
    _settings_cache["expires_at"] = now + _SETTINGS_TTL
    
    return result

def invalidate_settings_cache():
    """Call this after admin updates site settings."""
    _settings_cache["data"] = None
    _settings_cache["expires_at"] = 0

# ============================================================
# LAYOUT CACHE — Footer links, social links (almost never change)
# ============================================================
_layout_cache = {
    "data": None,
    "expires_at": 0
}
_LAYOUT_TTL = 600  # 10 minutes

def get_layout_context():
    """
    Header + footer + shared UI data (cached)
    """
    now = time.time()
    
    if _layout_cache["data"] is not None and now < _layout_cache["expires_at"]:
        return _layout_cache["data"]
    
    settings = get_site_settings()
    
    result = {
        "footer_pages": [
            ('about', 'About Us'),
            ('contact', 'Contact'),
            ('privacy', 'Privacy Policy'),
            ('terms', 'Terms'),
            ('affiliate', 'Affiliate Disclosure'),
        ],
        "social_links": {
            "instagram": settings.get('instagram_link', '#'),
            "whatsapp": f"https://wa.me/{settings.get('whatsapp_number', '').replace('+', '')}" if settings.get('whatsapp_number') else "#"
        },
        "site_settings": settings,
        "site_name": settings.get('site_name', 'Atr')
    }
    
    _layout_cache["data"] = result
    _layout_cache["expires_at"] = now + _LAYOUT_TTL
    
    return result

def invalidate_layout_cache():
    """Call this after admin updates layout-related settings."""
    _layout_cache["data"] = None
    _layout_cache["expires_at"] = 0
    invalidate_settings_cache()

def get_global_context():
    """
    Single entry point for ALL shared template context.
    Layout data is cached; user data is per-request (must be).
    """
    return {
        **get_user_context(),
        **get_layout_context(),
    }

def get_newsletter_context():
    is_authenticated = current_user.is_authenticated
    is_subscribed = (
        is_authenticated
        and current_user.newsletter_subscription
        and not current_user.newsletter_subscription.unsubscribed_at
    )
    return {
        'is_authenticated': is_authenticated,
        'is_subscribed': is_subscribed
    }
