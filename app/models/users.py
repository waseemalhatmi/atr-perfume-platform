from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app.extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    provider = db.Column(db.String(50), nullable=True)  # 'google' or 'local'
    is_admin = db.Column(db.Boolean, default=False)
    # Fix #15: server_default ensures timestamp is set by PostgreSQL, not Python.
    # Python's datetime.utcnow() is timezone-naive and skipped in bulk inserts.
    # server_default=db.func.now() is timezone-aware and always set by the DB.
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    
    # Relationships
    newsletter_subscription = db.relationship(
        "NewsletterSubscriber",
        back_populates="user",
        uselist=False
    )
    views = db.relationship("View", back_populates="user", cascade="all, delete-orphan")
    saves = db.relationship(
        "Save",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    user_interests = db.relationship(
        "UserInterest",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    item_clicks = db.relationship("ItemClick", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    __table_args__ = (
        db.CheckConstraint(
            "(google_id IS NULL AND provider IS NULL) OR (google_id IS NOT NULL AND provider IS NOT NULL)",
            name="ck_google_user"
        ),
    )
    def __repr__(self):
        return f'<User {self.email}>'

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    is_active = db.Column(db.Boolean, default=False)
    subscribed_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship("User", back_populates="newsletter_subscription")
    
    def __repr__(self):
        return f'<NewsletterSubscriber {self.email}>'
