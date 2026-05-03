"""add medium priority fixes: price alert index, fk ondelete, gin trigram index

Revision ID: e1f83c5d2b47
Revises: d8b21c4f9a63
Create Date: 2026-05-03 20:46:00.000000

Changes:
  price_alerts:
  - CREATE composite index ix_price_alert_lookup ON (email, item_id, is_active)
    Covers the exact filter in PriceAlert.query.filter_by(email=X, item_id=Y, is_active=True)
    called on every price alert subscription. Without this: full table scan per request.

  quiz_logs:
  - ALTER COLUMN user_id: DROP FK, re-ADD FK with ON DELETE SET NULL
    Without this, PostgreSQL RESTRICTS user deletion when quiz logs reference the user.
    Admin "delete user" action silently fails with a 500 error.

  comparison_logs:
  - Same fix as quiz_logs for user_id FK
  - Same fix for winner_id FK (items.id) — item deletion blocked otherwise

  items:
  - Enable pg_trgm extension (needed for GIN trigram index)
  - CREATE GIN trigram index on normalized_notes for fast LIKE/admin-panel searches

  NOTE on deferred column_property (Fix #17):
  - deferred=True on min_price_sql/currency_sql is an ORM-only change (no migration needed).
  - SQLAlchemy simply skips the subquery in the SELECT unless explicitly requested.
"""
from alembic import op
import sqlalchemy as sa


revision = 'e1f83c5d2b47'
down_revision = 'd8b21c4f9a63'
branch_labels = None
depends_on = None


def upgrade():
    # ── price_alerts: composite lookup index ──────────────────────────────────
    op.create_index(
        "ix_price_alert_lookup",
        "price_alerts",
        ["email", "item_id", "is_active"]
    )

    # ── quiz_logs: add ON DELETE SET NULL to user_id FK ───────────────────────
    # PostgreSQL default FK behavior is RESTRICT — user deletion is blocked.
    op.drop_constraint("quiz_logs_user_id_fkey", "quiz_logs", type_="foreignkey")
    op.create_foreign_key(
        "quiz_logs_user_id_fkey",
        "quiz_logs", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL"
    )

    # ── comparison_logs: add ON DELETE SET NULL to user_id and winner_id FKs ──
    op.drop_constraint("comparison_logs_user_id_fkey", "comparison_logs", type_="foreignkey")
    op.create_foreign_key(
        "comparison_logs_user_id_fkey",
        "comparison_logs", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL"
    )
    op.drop_constraint("comparison_logs_winner_id_fkey", "comparison_logs", type_="foreignkey")
    op.create_foreign_key(
        "comparison_logs_winner_id_fkey",
        "comparison_logs", "items",
        ["winner_id"], ["id"],
        ondelete="SET NULL"
    )

    # ── items.normalized_notes: GIN trigram index for fast LIKE searches ───────
    # pg_trgm enables GIN/GIST indexing on arbitrary text columns.
    # This allows: WHERE normalized_notes ILIKE '%rose%' to use the index
    # instead of a sequential scan — critical for admin panel search.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_items_normalized_notes_gin "
        "ON items USING GIN (normalized_notes gin_trgm_ops)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_items_normalized_notes_gin")

    # Revert comparison_logs FKs (back to RESTRICT — default)
    op.drop_constraint("comparison_logs_winner_id_fkey", "comparison_logs", type_="foreignkey")
    op.create_foreign_key(
        "comparison_logs_winner_id_fkey",
        "comparison_logs", "items", ["winner_id"], ["id"]
    )
    op.drop_constraint("comparison_logs_user_id_fkey", "comparison_logs", type_="foreignkey")
    op.create_foreign_key(
        "comparison_logs_user_id_fkey",
        "comparison_logs", "users", ["user_id"], ["id"]
    )

    # Revert quiz_logs FK
    op.drop_constraint("quiz_logs_user_id_fkey", "quiz_logs", type_="foreignkey")
    op.create_foreign_key(
        "quiz_logs_user_id_fkey",
        "quiz_logs", "users", ["user_id"], ["id"]
    )

    op.drop_index("ix_price_alert_lookup", table_name="price_alerts")
