"""fix item_images fk ondelete cascade

Revision ID: f2a94b7c1d05
Revises: e1f83c5d2b47
Create Date: 2026-05-03 20:51:00.000000

Changes:
  item_images:
  - DROP FK constraint item_images_item_id_fkey
  - RE-ADD FK with ON DELETE CASCADE

  WHY:
    Without CASCADE, a raw SQL DELETE on items (admin bulk delete, data migrations,
    or any DELETE that bypasses SQLAlchemy session) will either:
      a) Be BLOCKED by PostgreSQL FK violation (default RESTRICT behavior), or
      b) Leave orphaned item_images rows pointing to non-existent items

    SQLAlchemy ORM cascade="all, delete-orphan" only works when items are deleted
    through the ORM session (db.session.delete(item)). Raw SQL entirely bypasses it.

    ON DELETE CASCADE at the database level provides the safety net regardless of
    how the deletion is performed.
"""
from alembic import op
import sqlalchemy as sa


revision = 'f2a94b7c1d05'
down_revision = 'e1f83c5d2b47'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing FK (no ondelete) and re-create with CASCADE
    op.drop_constraint("item_images_item_id_fkey", "item_images", type_="foreignkey")
    op.create_foreign_key(
        "item_images_item_id_fkey",
        "item_images", "items",
        ["item_id"], ["id"],
        ondelete="CASCADE"
    )


def downgrade():
    # Revert to original FK without CASCADE
    op.drop_constraint("item_images_item_id_fkey", "item_images", type_="foreignkey")
    op.create_foreign_key(
        "item_images_item_id_fkey",
        "item_images", "items",
        ["item_id"], ["id"]
    )
