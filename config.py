# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "atri-perfume-2025-static-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "atri.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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



# ================================================
SOCIAL_LINKS = [
  ("facebook", "https://facebook.com/atri"),
  ("youtube", "https://youtube.com/atri"),
  ("twitter", "https://twitter.com/atri"),
  ("instagram", "https://instagram.com/atri"),
]
