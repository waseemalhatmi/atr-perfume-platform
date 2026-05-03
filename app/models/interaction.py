from datetime import datetime
from app.extensions import db

class View(db.Model):
    __tablename__ = "views"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    target_type = db.Column(db.String(50), nullable=False, default='item')
    target_id = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    @property
    def target(self):
        return self.item
    user = db.relationship("User", back_populates="views")
    item = db.relationship(
        "Item",
        primaryjoin="and_(foreign(View.target_id) == Item.id, View.target_type == 'item')",
        back_populates="views",
        viewonly=True,
        lazy="selectin"
    )
    __table_args__ = (
        # Fast lookup for the 24-hour dedup query in record_view():
        # WHERE target_type=? AND target_id=? AND created_at > cutoff
        db.Index("idx_views_target", "target_type", "target_id"),
        db.Index("ix_views_dedup", "target_type", "target_id", "created_at"),
        db.CheckConstraint(
            "(user_id IS NOT NULL AND ip_address IS NULL) OR "
            "(user_id IS NULL AND ip_address IS NOT NULL)",
            name="ck_view_one_identity"
        ),
        # ── Fix: Replace broken UniqueConstraint with two PARTIAL unique indexes ──
        # WHY the old UniqueConstraint(user_id, ip_address, target_type, target_id) NEVER fired:
        #   PostgreSQL treats NULL != NULL in unique constraints.
        #   Every row has either user_id=NULL or ip_address=NULL.
        #   A composite constraint with any NULL column is always considered distinct.
        #   Result: unlimited duplicate rows for the same user/IP + target.
        #
        # FIX: Two separate partial indexes, each covering only non-NULL rows:
        #   - uq_view_user: unique per authenticated user per target
        #   - uq_view_ip:   unique per guest IP per target
        # These require a migration (see: d8b21c4f9a63_fix_view_unique_indexes.py)
        db.Index(
            "uq_view_user",
            "user_id", "target_type", "target_id",
            unique=True,
            postgresql_where=db.text("user_id IS NOT NULL"),
        ),
        db.Index(
            "uq_view_ip",
            "ip_address", "target_type", "target_id",
            unique=True,
            postgresql_where=db.text("ip_address IS NOT NULL"),
        ),
    )

class Save(db.Model):
    __tablename__ = "saves"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    target_type = db.Column(db.String(50), nullable=False, default='item')
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship(
        "Item",
        primaryjoin="and_(foreign(Save.target_id) == Item.id, Save.target_type == 'item')",
        viewonly=True,
        lazy="select"
    )
    @property
    def target(self):
        return self.item
    __table_args__ = (
        db.UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_save"),
        db.Index("ix_save_target", "target_type", "target_id"),
    )
    user = db.relationship("User", back_populates="saves")

class ItemClick(db.Model):
    __tablename__ = "item_clicks"
    id = db.Column(db.Integer, primary_key=True)
    item_store_link_id = db.Column(
        db.Integer,
        db.ForeignKey("item_store_links.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.Text)
    country = db.Column(db.String(50))
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        index=True
    )
    user = db.relationship("User", back_populates="item_clicks")
    item_store_link = db.relationship("ItemStoreLink")
    __table_args__ = (
        db.Index("ix_item_click_link", "item_store_link_id"),
        db.Index("ix_item_click_user", "user_id"),
    )

class UserInterest(db.Model):
    __tablename__ = "user_interests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = db.Column(db.String(50), nullable=False, default='item')
    target_id = db.Column(db.Integer, nullable=False)
    interaction_count = db.Column(db.Integer, default=0)
    last_interaction_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", back_populates="user_interests")
    entity_scores = db.relationship("UserEntityInterest", back_populates="user_interest", cascade="all, delete-orphan")
    __table_args__ = (
        db.UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_target"),
        db.Index("ix_user_interest_user_target", "user_id", "target_type", "target_id"),
    )

class UserEntityInterest(db.Model):
    __tablename__ = "user_entity_interests"
    id = db.Column(db.Integer, primary_key=True)
    user_interest_id = db.Column(db.Integer, db.ForeignKey("user_interests.id", ondelete="CASCADE"), nullable=False)
    brand_id = db.Column(db.Integer, nullable=True)
    category_id = db.Column(db.Integer, nullable=True)
    topic_id = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Float, default=0.0)
    user_interest = db.relationship("UserInterest", back_populates="entity_scores")
    __table_args__ = (
        db.CheckConstraint(
            "(brand_id IS NOT NULL) OR (category_id IS NOT NULL) OR (topic_id IS NOT NULL)",
            name="ck_entity_reference"
        ),
        db.Index("ix_user_entity_interest_ref", "brand_id", "category_id", "topic_id"),
    )

class ContactMessage(db.Model):
    # ── Fix: Added __tablename__ to prevent SQLAlchemy auto-naming ambiguity ───────
    # Without __tablename__, SQLAlchemy generates 'contact_message' automatically.
    # Explicit declaration prevents silent mismatches if the class is renamed.
    __tablename__ = "contact_message"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    __table_args__ = (
        # Admin panel filters: unread messages list (most common query)
        db.Index("ix_contact_is_read", "is_read"),
        # Support ticket lookup by email
        db.Index("ix_contact_email", "email"),
        # Chronological sorting (admin inbox view)
        db.Index("ix_contact_created_at", "created_at"),
    )

class PriceAlert(db.Model):
    __tablename__ = "price_alerts"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    item = db.relationship("Item", backref=db.backref("alerts", cascade="all, delete-orphan"))
    user = db.relationship("User", backref="price_alerts")
    __table_args__ = (
        # Covers: PriceAlert.query.filter_by(email=X, item_id=Y, is_active=True)
        # This exact query runs on every price alert subscription POST request.
        # Without this index, it's a full table scan on every subscription.
        db.Index("ix_price_alert_lookup", "email", "item_id", "is_active"),
    )

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    user = db.relationship("User", back_populates="notifications")

class QuizLog(db.Model):
    __tablename__ = "quiz_logs"
    id = db.Column(db.Integer, primary_key=True)
    # Fix #16: ondelete='SET NULL' — without this, deleting a user raises a FK
    # violation and the DELETE is blocked (PostgreSQL default is RESTRICT).
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    gender = db.Column(db.String(50))
    apparel = db.Column(db.String(50))
    activity = db.Column(db.String(50))
    weather = db.Column(db.String(50))
    vibe = db.Column(db.String(50))
    recommended_items = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    user = db.relationship("User", backref="quiz_logs")

class ComparisonLog(db.Model):
    __tablename__ = "comparison_logs"
    id = db.Column(db.Integer, primary_key=True)
    # Fix #16: ondelete='SET NULL' — without this, deleting a user raises a FK
    # violation and the DELETE is blocked (PostgreSQL default is RESTRICT).
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    item_ids = db.Column(db.JSON, nullable=False)  # List of compared item IDs
    winner_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref="comparison_logs")
    winner = db.relationship("Item", foreign_keys=[winner_id])
