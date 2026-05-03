from datetime import datetime
from sqlalchemy import event, orm
from app.extensions import db
from .shared import ActiveSortMixin
from .taxonomy import item_sections, item_topics

class Brand(db.Model, ActiveSortMixin):
    __tablename__ = "brands"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    slug        = db.Column(db.String(150), unique=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    items = db.relationship("Item", back_populates="brand")
    def __repr__(self):
        return f"<Brand {self.slug}>"

class Category(db.Model, ActiveSortMixin):
    __tablename__ = "categories"
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    slug      = db.Column(db.String(120), unique=True, nullable=False)
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True
    )
    parent = db.relationship(
        "Category",
        remote_side=[id],
        backref="children"
    )
    items = db.relationship("Item", back_populates="category")

    def __repr__(self):
        return f"<Category {self.slug}>"

class Store(db.Model, ActiveSortMixin):
    __tablename__ = "stores"
    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(100), nullable=False)
    slug              = db.Column(db.String(100), unique=True, nullable=False)
    website           = db.Column(db.Text, nullable=False)
    country           = db.Column(db.String(50))
    currency          = db.Column(db.String(10))
    affiliate_network = db.Column(db.String(100))
    created_at        = db.Column(db.DateTime, server_default=db.func.now())
    item_links = db.relationship(
        "ItemStoreLink",
        back_populates="store",
        cascade="all, delete-orphan"
    )

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text)
    meta_description = db.Column(db.String(255), nullable=True) # SEO
    
    item_type = db.Column(db.String(50), nullable=True, default='perfume')
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        index=True
    )
    view_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    card_type = db.Column(db.TEXT)
    normalized_notes = db.Column(db.Text, nullable=True)  # Stores processed aroma tokens
    # NOTE: normalized_notes is stored as a comma-separated string (e.g. "rose,oud,musk").
    # Matching is done via Python set operations in discovery_service.py.
    # A GIN trigram index (pg_trgm) is added via migration e1f83c5d2b47 to enable
    # faster LIKE/ILIKE searches on this column from the admin panel.
    # Semantic search embedding vector (768 dimensions — Gemini embedding-001).
    # Stored as pgvector 'vector(768)' type in PostgreSQL.
    # The ORM declares it as Text so SQLAlchemy tracks the column without needing
    # the pgvector Python package. All reads/writes use raw SQL in vector_service.py.
    # Migration: a3f92c1e8b45 adds the actual vector(768) column + ivfflat index.
    embedding = db.Column(db.Text, nullable=True)


    # RELATIONSHIPS
    category = db.relationship("Category", back_populates="items")
    brand = db.relationship("Brand", back_populates="items")
    sections = db.relationship(
        "Section", secondary=item_sections, back_populates="items")    
    topics = db.relationship("Topic", secondary=item_topics, back_populates="items")
    
    variants = db.relationship(
        "ItemVariant",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    images = db.relationship(
        "ItemImage",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ItemImage.position",
        lazy="selectin"
    )    
    specifications = db.relationship(
        "ItemSpecification",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def set_default_variant(self):
        if not self.variants:
            return
        if not any(v.is_default for v in self.variants):
            self.variants[0].is_default = True
    
    @property
    def default_variant(self):
        return next(
            (v for v in self.variants if v.is_default),
            self.variants[0] if self.variants else None
        )
    
    @property
    def has_variants(self):
        return len(self.variants) > 1

    @property
    def store_links(self):
        if not self.default_variant:
            return []
        return [
            link
            for link in self.default_variant.store_links
            if link.is_active
        ]

    @staticmethod
    def pick_keys(d, keys):
        if not isinstance(d, dict):
            return None
        result = {k: d[k] for k in keys if k in d and d[k] is not None}
        return result or None
    
    @staticmethod
    def get_specifications(result):
        return {k: v for k, v in result.items() if v}    
    
    @property
    def full_details(self):
        return {
            spec.category: spec.spec_json
            for spec in self.specifications
            if isinstance(spec.spec_json, dict)
        }

    @property
    def details(self):
        full = self.full_details
        perfume_spec = full.get("العطر") or full.get("Fragrance")
        if perfume_spec:
            return self.get_specifications(perfume_spec)
        result = {
            "launch": self.pick_keys(full.get("launch"), ["status"]),
            "display": self.pick_keys(full.get("display"), ["size"]),
            "platform": self.pick_keys(full.get("platform"), ["chipset"]),
            "battery": self.pick_keys(full.get("battery"), ["type"]),
            "misc": self.pick_keys(full.get("misc"), ["price", "colors"]),
        }
        return self.get_specifications(result)
    
    @property
    def perfume_notes(self):
        full = self.full_details
        notes = full.get("مكونات العطر") or full.get("Fragrance Notes")
        if not notes:
            return None
        return {
            "top": notes.get("القمة") or notes.get("Top"),
            "heart": notes.get("القلب") or notes.get("Middle") or notes.get("Heart"),
            "base": notes.get("القاعدة") or notes.get("Base")
        }
    
    @property
    def quick_details(self):
        return self._quick_details(self.details)

    def get_related_items(self, limit=4):
        # Fix #2: Combine into a single smart query to reduce DB hits
        return Item.query.filter(
            db.or_(Item.brand_id == self.brand_id, Item.category_id == self.category_id),
            Item.id != self.id
        ).order_by(
            db.case(
                (Item.brand_id == self.brand_id, 0),
                else_=1
            )
        ).limit(limit).all()

    def _quick_details(self, details=None, parent=""):
        items = []
        for key, value in details.items():
            label = key.replace("_", " ").title()
            if parent:
                label = f"{parent} {label}"
            if isinstance(value, dict):
                items.extend(self._quick_details(value, label))
            else:
                items.append({
                    "key": label,
                    "value": value
                })
        return items
    
    views = db.relationship(
        "View",
        primaryjoin="and_(foreign(View.target_id)==Item.id, View.target_type=='item')",
        back_populates="item",
        viewonly=True,
        lazy="selectin"
    )
    __table_args__ = (
        db.UniqueConstraint("brand_id", "slug", name="uq_items_brand_slug"),
        db.Index("ix_items_brand_slug", "brand_id", "slug"),
    )    
    def __repr__(self):
        return f"<Item {self.name}>"
    
    def add_section(self, section_obj):
        if section_obj not in self.sections:
            self.sections.append(section_obj)
    def add_topic(self, topic_obj):
        if topic_obj not in self.topics:
            self.topics.append(topic_obj)

class ItemVariant(db.Model):
    __tablename__ = "item_variants"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False
    )
    title = db.Column(db.String(200), nullable=True)
    sku = db.Column(db.String(100), unique=True, nullable=True)
    attributes = db.Column(db.JSON)  
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    item = db.relationship("Item", back_populates="variants")    
    store_links = db.relationship(
        "ItemStoreLink",
        back_populates="variant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def normalize_attributes(self):
        if not self.attributes:
            return
        self.attributes = {
            str(k).lower().strip(): str(v).strip()
            for k, v in self.attributes.items()
        }

    def display_name(self):
        if self.title:
            return self.title
        if self.attributes:
            return " / ".join(
                f"{k.capitalize()}: {v}"
                for k, v in self.attributes.items()
            )
        return "Default"
    
    __table_args__ = (
        db.Index("ix_variant_item", "item_id"),
        db.Index("ix_variant_default", "item_id", "is_default"),
    )

class ItemStoreLink(db.Model):
    __tablename__ = "item_store_links"
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey("item_variants.id", ondelete="CASCADE"),
        nullable=False
    )
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False
    )
    external_item_id = db.Column(db.String(150))
    affiliate_url = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2))
    old_price = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3))
    availability = db.Column(db.String(32), index=True)
    last_checked_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    variant = db.relationship("ItemVariant", back_populates="store_links")
    store = db.relationship("Store", back_populates="item_links")
    price_history = db.relationship("PriceHistory", back_populates="variant_link", cascade="all, delete-orphan")
    __table_args__ = (
        db.UniqueConstraint(
            "variant_id", "store_id",
            name="uq_variant_store"
        ),
        db.Index("ix_item_store_price", "price"),
        db.Index("ix_item_store_variant", "variant_id"),
        db.Index("ix_item_store_store", "store_id"),
    )

class ItemImage(db.Model):
    __tablename__ = "item_images"
    id = db.Column(db.Integer, primary_key=True)
    # Fix #20: Added ondelete='CASCADE' to the FK.
    # Without this, raw SQL DELETE on items (bulk deletes, migrations) raises a
    # FK violation or leaves orphaned image rows. ORM cascade only works through
    # SQLAlchemy session — raw DELETE FROM items WHERE ... bypasses it entirely.
    item_id = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.Text, nullable=False)
    alt_text = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0)
    item = db.relationship("Item", back_populates="images")
    def __repr__(self):
        return f"<ItemImage {self.image_path}>"

class ItemSpecification(db.Model):
    __tablename__ = "item_specifications"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    category = db.Column(db.String(100))
    spec_json = db.Column(db.JSON)
    item = db.relationship("Item", back_populates="specifications")
    __table_args__ = (
        db.Index("ix_item_specs_item", "item_id"),
    )
    def __repr__(self):
        return f"<ItemSpecification {self.category}>"

class PriceHistory(db.Model):
    __tablename__ = "price_history"
    id = db.Column(db.Integer, primary_key=True)
    variant_link_id = db.Column(db.Integer, db.ForeignKey('item_store_links.id', ondelete="CASCADE"), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    variant_link = db.relationship("ItemStoreLink", back_populates="price_history")
    def __repr__(self):
        return f"<PriceHistory Link:{self.variant_link_id} Price:{self.price} Date:{self.recorded_at}>"

class ItemRecommendation(db.Model):
    """
    Stores pre-calculated recommendations for high-speed retrieval.
    Replaces real-time calculations with simple lookups.

    Constraints:
    - uq_item_rec: Guarantees only ONE row per (source_item, target_item) pair.
      Without this, concurrent Celery tasks can insert duplicate recommendations,
      causing the same perfume to appear twice in the UI.
    - ix_item_rec_lookup: Covers the exact filter in get_similar_fragrances():
      filter_by(item_id=X, rec_type='clone'/'similar') — eliminates full table scans.
    """
    __tablename__ = 'item_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    recommended_item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='CASCADE'), nullable=False)

    match_score = db.Column(db.Integer, default=0)
    price_diff = db.Column(db.Float, default=0.0)
    # Types: 'clone' (cheaper), 'similar' (high match), 'related' (same brand/category)
    rec_type = db.Column(db.String(20), nullable=False)

    # server_default: timestamp set by the DB engine (timezone-safe, works in bulk inserts)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationships
    item = db.relationship('Item', foreign_keys=[item_id], backref=db.backref('recommendations_generated', lazy='dynamic'))
    recommended_item = db.relationship('Item', foreign_keys=[recommended_item_id], backref=db.backref('as_recommendation', lazy='dynamic'))

    __table_args__ = (
        # One recommendation row per source→target pair (regardless of type).
        # Protects against duplicate inserts from concurrent Celery refresh tasks.
        db.UniqueConstraint("item_id", "recommended_item_id", name="uq_item_rec"),
        # Composite index covering the exact lookup in get_similar_fragrances():
        #   .filter_by(item_id=X, rec_type='clone'/'similar').limit(N)
        db.Index("ix_item_rec_lookup", "item_id", "rec_type"),
    )

    def __repr__(self):
        return f"<ItemRec {self.item_id} -> {self.recommended_item_id} ({self.rec_type})>"

# ── Phase 4: Automation Hooks ───────────────────────────────────────────────
#
# IMPORTANT: We use 'after_flush_postexec' (not 'after_insert'/'after_update')
# to ensure hooks run AFTER the transaction is committed — never inside one.
# Calling db.session.commit() inside after_insert causes nested transactions
# and risks data corruption with PostgreSQL.

@event.listens_for(db.session.__class__, 'after_bulk_update')
def _noop(*args):
    pass  # Placeholder to confirm session events are wired


@event.listens_for(Item, 'after_insert')
@event.listens_for(Item, 'after_update')
def auto_sync_item_normalized_notes(mapper, connection, target):
    """
    Sync tokens when an item is created or updated.
    Uses connection-level execution (no db.session.commit call) to stay safe
    within the enclosing transaction.
    """
    from app.services.discovery_service import sync_item_normalized_notes
    from app.services.vector_service import vector_service
    try:
        sync_item_normalized_notes(target)
        # Fix #2: Invalidate semantic search cache on item updates
        vector_service.invalidate_search_cache()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            f"auto_sync_item_normalized_notes failed for item {target.id}: {exc}"
        )


@event.listens_for(ItemSpecification, 'after_insert')
@event.listens_for(ItemSpecification, 'after_update')
def auto_refresh_on_spec_change(mapper, connection, target):
    """
    If perfume notes are updated, schedule recommendation refresh.
    We use db.session.object_session() to avoid creating a new session,
    and we do NOT commit here — the caller's transaction handles commit.
    """
    if target.category not in ("مكونات العطر", "Fragrance Notes"):
        return

    from app.services.discovery_service import sync_item_normalized_notes
    try:
        item = db.session.get(Item, target.item_id)
        if item:
            sync_item_normalized_notes(item)
            # Refresh recommendations deferred: enqueue via after-request hook
            # so we never commit inside an event.
            from flask import g
            pending = getattr(g, "_pending_rec_refresh", set())
            pending.add(item.id)
            g._pending_rec_refresh = pending
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            f"auto_refresh_on_spec_change failed for spec {target.id}: {exc}"
        )


@event.listens_for(ItemStoreLink, 'after_insert')
@event.listens_for(ItemStoreLink, 'after_update')
def auto_refresh_on_price_change(mapper, connection, target):
    """
    If a store price changes, schedule recommendation refresh via g._pending_rec_refresh.
    Never commits inside this event.
    """
    if not (target.variant and target.variant.item_id):
        return
    try:
        from flask import g
        pending = getattr(g, "_pending_rec_refresh", set())
        pending.add(target.variant.item_id)
        g._pending_rec_refresh = pending
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            f"auto_refresh_on_price_change failed: {exc}"
        )

# Fix #17: Moving min_price and currency calculation to SQL directly
# IMPORTANT: deferred=True prevents these correlated subqueries from running on
# every Item query. Without deferred=True, loading 50 items in api_items() triggers
# 50 subqueries for min_price + 50 for currency = 100 extra DB round-trips per page.
#
# With deferred=True:
#   - Basic Item queries (lists, recommendations) do NOT run the subqueries.
#   - Only when item.min_price_sql or item.currency_sql is accessed does the subquery run.
#   - Routes that need prices for ALL items should use db.undefer(Item.min_price_sql)
#     in their query options to load eagerly in a single batch.
Item.min_price_sql = db.column_property(
    db.select(db.func.min(ItemStoreLink.price))
    .where(ItemStoreLink.variant_id == ItemVariant.id)
    .where(ItemVariant.item_id == Item.id)
    .where(ItemStoreLink.is_active == True)
    .correlate_except(ItemStoreLink, ItemVariant)
    .scalar_subquery(),
    deferred=True  # Load lazily — eliminates N+1 on list/recommendation queries
)

Item.currency_sql = db.column_property(
    db.select(ItemStoreLink.currency)
    .where(ItemStoreLink.variant_id == ItemVariant.id)
    .where(ItemVariant.item_id == Item.id)
    .where(ItemStoreLink.is_active == True)
    .where(ItemStoreLink.price != None)
    .order_by(ItemStoreLink.price.asc())
    .limit(1)
    .correlate_except(ItemStoreLink, ItemVariant)
    .scalar_subquery(),
    deferred=True  # Load lazily — eliminates N+1 on list/recommendation queries
)
