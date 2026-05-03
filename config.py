# config.py
import os
import sys
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
_IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"

# ── SECRET_KEY Validation ─────────────────────────────────────────────────────
_secret_key = os.environ.get("SECRET_KEY")

if not _secret_key:
    if _IS_PRODUCTION:
        # In production: HARD FAIL — do not start with a random key
        print("\n🔴 FATAL: SECRET_KEY is not set in production environment!")
        print("   Set SECRET_KEY in your environment variables and restart.\n")
        sys.exit(1)
    else:
        # In development: use random key with clear warning
        _secret_key = secrets.token_hex(32)
        print("\n⚠️  WARNING: No SECRET_KEY set in environment!")
        print("   Using a random key — sessions will reset on every restart.")
        print("   Add SECRET_KEY=<value> to your .env file.\n")
elif _secret_key == "atri-luxury-perfume-production-key-2025":
    # Detect the known-compromised default key
    print("\n🔴 SECURITY WARNING: You are using the known-compromised SECRET_KEY!")
    print("   This key has been exposed publicly. Generate a new one:")
    print("   python -c \"import secrets; print(secrets.token_hex(32))\"")
    if _IS_PRODUCTION:
        sys.exit(1)

# ── ENVIRONMENT VALIDATION (Fix #14) ─────────────────────────────────────────
if _IS_PRODUCTION:
    if not os.environ.get("DATABASE_URL"):
        print("\n🔴 FATAL: DATABASE_URL is missing in production environment!")
        sys.exit(1)
        
    if not os.environ.get("REDIS_URL"):
        print("\n🔴 FATAL: REDIS_URL is missing in production environment!")
        print("   Redis is REQUIRED for queuing, caching, and locking in production.\n")
        sys.exit(1)

    # Fix #2: Require explicit confirmation that HTTPS is enabled in production
    if os.environ.get("HTTPS_ENABLED", "False").lower() != "true":
        print("\n🔴 FATAL: HTTPS_ENABLED=True is required in production!")
        print("   Production session cookies are strictly set to SECURE.")
        print("   If you don't run HTTPS, users won't be able to log in.")
        print("   Set HTTPS_ENABLED=True in your .env if your reverse proxy handles SSL.\n")
        sys.exit(1)

_ratelimit_uri = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
if _IS_PRODUCTION and _ratelimit_uri == "memory://":
    print("\n🟠 WARNING: RATELIMIT_STORAGE_URI=memory:// in production!")
    print("   Rate limiting will NOT work correctly with multiple workers.")
    print("   Set RATELIMIT_STORAGE_URI=redis://localhost:6379/0\n")

class Config:
    SECRET_KEY = _secret_key

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "atri.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    MAX_IMAGE_UPLOAD_SIZE = int(os.environ.get("MAX_IMAGE_UPLOAD_SIZE", 5 * 1024 * 1024))

    # ── Session Cookie Security (Fix #2) ──────────────────────────────────────
    # Always secure in production, regardless of any other settings.
    SESSION_COOKIE_HTTPONLY = True       # Prevent JS access to session cookie
    SESSION_COOKIE_SAMESITE = "Lax"     # CSRF protection
    SESSION_COOKIE_SECURE = True if _IS_PRODUCTION else False  # Force True in Prod
    PERMANENT_SESSION_LIFETIME = 86400   # 24 hours

    # DB connection pool — optimized for multi-worker production
    # Fix #12: Database Hardening (Timeout & Pool Tuning)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": int(os.environ.get("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 20)),
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),
        "connect_args": {
            # Kill queries that take longer than 15 seconds to prevent DB lockup
            "options": "-c statement_timeout=15000"
        }
    }

    # Google OAuth — must come from environment only
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Mail settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME")
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "True") == "True"

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "support@atri.com")

    # Gemini AI
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL")

    # Rate limiting — MUST use Redis in production
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True") == "True"
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URI = _ratelimit_uri
    RATELIMIT_SWALLOW_ERRORS = True # Fix #4: If Redis fails, Rate Limiter fails OPEN to avoid downtime


# ── Social Links (non-sensitive, OK to be in code) ───────────────────────────
SOCIAL_LINKS = [
    ("facebook", "https://facebook.com/atri"),
    ("youtube", "https://youtube.com/atri"),
    ("twitter", "https://twitter.com/atri"),
    ("instagram", "https://instagram.com/atri"),
]
