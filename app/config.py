# config.py
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Warn if using default secret key
_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    print("\n⚠️  WARNING: No SECRET_KEY set in environment!")
    print("   Using a random key (sessions will reset on restart).")
    print("   Set SECRET_KEY in your .env file for production.\n")

class Config:
    SECRET_KEY = _secret_key
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "atri.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    MAX_IMAGE_UPLOAD_SIZE = int(os.environ.get("MAX_IMAGE_UPLOAD_SIZE", 5 * 1024 * 1024))
    
    # Secure session cookies
    SESSION_COOKIE_HTTPONLY = True      # Prevent JS access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in prod
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Enable automatic DB connection pinging and active recycling to prevent timeout errors
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800, # Recycle connections every 30 minutes
    }

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # ============ Those Were Added When Working On The Contact Form =============
    # Mail settings (Gmail example, adjust if using another provider)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")  # your email
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")  # app password
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "support@atri.com")
    MAIL_ENABLED = True  # you can disable in dev with False

    # Rate limiting (use Redis in production for multi-worker consistency)
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True") == "True"
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")



# ================================================
SOCIAL_LINKS = [
  ("facebook", "https://facebook.com/atri"),
  ("youtube", "https://youtube.com/atri"),
  ("twitter", "https://twitter.com/atri"),
  ("instagram", "https://instagram.com/atri"),
]