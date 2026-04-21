from flask_login import current_user
from config import SOCIAL_LINKS


def get_user_context():
    is_authenticated = current_user.is_authenticated
    user_email = None
    is_subscribed = False

    if is_authenticated:
        user_email = current_user.email

        sub = getattr(current_user, "newsletter_subscription", None)
        if sub and not sub.unsubscribed_at:
            is_subscribed = True

    return {
        "is_authenticated": is_authenticated,
        "user_email": user_email,
        "is_subscribed": is_subscribed,
    }


def get_layout_context():
    """
    Header + footer + shared UI data
    """
    return {
        "footer_pages": [
            ('about', 'About Us'),
            ('contact', 'Contact'),
            ('privacy', 'Privacy Policy'),
            ('terms', 'Terms'),
            ('affiliate', 'Affiliate Disclosure'),
        ],

        "social_links": SOCIAL_LINKS,
    }


def get_global_context():
    """
    Single entry point for ALL shared template context
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
