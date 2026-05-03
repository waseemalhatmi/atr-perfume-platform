"""fix view unique indexes and add contact message indexes

Revision ID: d8b21c4f9a63
Revises: c7d41a8e3f92
Create Date: 2026-05-03 20:36:00.000000

Changes:
  views table:
  - DROP the broken UniqueConstraint 'unique_view' (user_id, ip_address, target_type, target_id).
    PostgreSQL treats NULL != NULL in unique constraints, so every row had at least one NULL
    (either user_id or ip_address), making the constraint effectively inactive.
  - CREATE partial unique index 'uq_view_user' ON (user_id, target_type, target_id)
    WHERE user_id IS NOT NULL   → enforces one view per authenticated user per target
  - CREATE partial unique index 'uq_view_ip'   ON (ip_address, target_type, target_id)
    WHERE ip_address IS NOT NULL → enforces one view per guest IP per target
  - CREATE composite index 'ix_views_dedup' ON (target_type, target_id, created_at)
    Covers the 24-hour deduplication query in record_view():
      WHERE target_type=? AND target_id=? AND created_at >= cutoff

  contact_message table:
  - CREATE index 'ix_contact_is_read'   ON (is_read)      → admin unread filter
  - CREATE index 'ix_contact_email'     ON (email)        → support ticket lookup
  - CREATE index 'ix_contact_created_at' ON (created_at)  → chronological inbox sort
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'd8b21c4f9a63'
down_revision = 'c7d41a8e3f92'
branch_labels = None
depends_on = None


def upgrade():
    # ── views: drop broken composite unique constraint ─────────────────────────
    # The old constraint (user_id, ip_address, target_type, target_id) never fired
    # because one of the first two columns is always NULL, and PostgreSQL considers
    # NULLs as distinct from each other in unique constraints.
    op.drop_constraint("unique_view", "views", type_="unique")

    # ── views: partial unique index for authenticated users ────────────────────
    # Guarantees one view record per (user, target) pair — enforced at DB level.
    op.execute(
        "CREATE UNIQUE INDEX uq_view_user "
        "ON views (user_id, target_type, target_id) "
        "WHERE user_id IS NOT NULL"
    )

    # ── views: partial unique index for guest visitors (IP-based) ─────────────
    # Guarantees one view record per (ip, target) pair — enforced at DB level.
    op.execute(
        "CREATE UNIQUE INDEX uq_view_ip "
        "ON views (ip_address, target_type, target_id) "
        "WHERE ip_address IS NOT NULL"
    )

    # ── views: composite index for the 24-hour dedup query ────────────────────
    # Covers: WHERE target_type=? AND target_id=? AND created_at >= cutoff
    # Without this, record_view() does a sequential scan on the full views table.
    op.create_index(
        "ix_views_dedup",
        "views",
        ["target_type", "target_id", "created_at"]
    )

    # ── contact_message: add admin/support indexes ────────────────────────────
    op.create_index("ix_contact_is_read",    "contact_message", ["is_read"])
    op.create_index("ix_contact_email",      "contact_message", ["email"])
    op.create_index("ix_contact_created_at", "contact_message", ["created_at"])


def downgrade():
    # contact_message indexes
    op.drop_index("ix_contact_created_at", table_name="contact_message")
    op.drop_index("ix_contact_email",      table_name="contact_message")
    op.drop_index("ix_contact_is_read",    table_name="contact_message")

    # views indexes
    op.drop_index("ix_views_dedup", table_name="views")
    op.execute("DROP INDEX IF EXISTS uq_view_ip")
    op.execute("DROP INDEX IF EXISTS uq_view_user")

    # Restore the original (broken) constraint for reversibility
    op.create_unique_constraint(
        "unique_view",
        "views",
        ["user_id", "ip_address", "target_type", "target_id"]
    )
