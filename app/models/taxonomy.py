from app.extensions import db
from .shared import ActiveSortMixin

# ==================== ASSOCIATION TABLES ====================
item_sections = db.Table(
    "item_sections",
    db.Column("item_id", db.Integer, db.ForeignKey(
        "items.id"), primary_key=True),
    db.Column("section_id", db.Integer, db.ForeignKey(
        "sections.id"), primary_key=True)
)

item_topics = db.Table(
    "item_topics",
    db.Column("item_id", db.Integer, db.ForeignKey("items.id"), primary_key=True),
    db.Column("topic_id", db.Integer, db.ForeignKey("topics.id"), primary_key=True)
)

# ==================== SECTION ====================
class Section(db.Model, ActiveSortMixin):
    __tablename__ = "sections"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    items = db.relationship(
        "Item",
        secondary=item_sections,
        back_populates="sections"
    )
    def __repr__(self):
        return f"<Section id={self.id} name='{self.name}'>"

class Topic(db.Model, ActiveSortMixin):
    __tablename__ = "topics"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    slug       = db.Column(db.String(120), unique=True, nullable=False)
    type       = db.Column(db.String(50),  nullable=True)
    is_featured= db.Column(db.Boolean, default=False)
    items = db.relationship(
        "Item",
        secondary=item_topics,
        back_populates="topics"
    )
    def __repr__(self):
        return f"<Topic {self.slug}>"
