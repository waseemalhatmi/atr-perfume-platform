from app.extensions import db

class ActiveSortMixin:
    """
    Shared Mixin for models that support activation toggling and ordering.
    Eliminates the duplication of `is_active` and `sort_order` columns
    across Brand, Category, Section, Topic, and Store.
    """
    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0,    nullable=False)
