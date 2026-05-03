"""add item_recommendations constraints and indexes

Revision ID: a3f92c1e8b45
Revises: b12bf6c34f4b
Create Date: 2026-05-03 20:10:00.000000

Changes:
  - item_recommendations: Add UniqueConstraint (item_id, recommended_item_id)
    Prevents duplicate recommendation rows from concurrent Celery refresh tasks.
  - item_recommendations: Add composite index (item_id, rec_type)
    Covers the exact lookup in get_similar_fragrances():
      filter_by(item_id=X, rec_type='clone'/'similar').limit(N)
  - item_recommendations: Add composite index (target_type, target_id, created_at)
    on the views table to speed up the 24-hour deduplication query in record_view().
  - views: Add composite index (target_type, target_id, created_at)
    Covers the deduplication query: WHERE target_type=? AND target_id=? AND created_at > cutoff
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a3f92c1e8b45'
down_revision = 'b12bf6c34f4b'
branch_labels = None
depends_on = None


def upgrade():
    # ── item_recommendations: unique constraint (item_id, recommended_item_id) ──
    # Prevents duplicate rows from concurrent Celery refresh tasks.
    op.create_unique_constraint(
        "uq_item_rec",
        "item_recommendations",
        ["item_id", "recommended_item_id"]
    )

    # ── item_recommendations: composite lookup index ───────────────────────────
    # Covers: filter_by(item_id=X, rec_type='clone'/'similar').limit(N)
    op.create_index(
        "ix_item_rec_lookup",
        "item_recommendations",
        ["item_id", "rec_type"]
    )

    # ── views: composite index for 24-hour dedup query ────────────────────────
    # Covers: WHERE target_type=? AND target_id=? AND created_at > cutoff
    # AND (user_id=? OR ip_address=?)
    # Without this, record_view() does a sequential scan on the full views table.
    op.create_index(
        "ix_views_dedup",
        "views",
        ["target_type", "target_id", "created_at"]
    )


def downgrade():
    op.drop_index("ix_views_dedup", table_name="views")
    op.drop_index("ix_item_rec_lookup", table_name="item_recommendations")
    op.drop_constraint("uq_item_rec", "item_recommendations", type_="unique")
