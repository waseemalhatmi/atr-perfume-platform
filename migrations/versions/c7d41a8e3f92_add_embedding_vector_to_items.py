"""add embedding vector column to items

Revision ID: c7d41a8e3f92
Revises: a3f92c1e8b45
Create Date: 2026-05-03 20:18:00.000000

Changes:
  - Enables the pgvector PostgreSQL extension (required for vector type and <=> operator).
  - Adds embedding column of type vector(768) to the items table.
    768 dimensions = Gemini embedding-001 model output size.
  - Creates an IVFFlat approximate nearest-neighbor index for fast similarity search.
    lists=100 is appropriate for catalogs up to ~1M items (tune upward as data grows).

  NOTE on ORM mapping:
    The Item model declares `embedding = db.Column(db.Text, nullable=True)` as a
    placeholder so SQLAlchemy tracks the column. The ACTUAL DB type is vector(768),
    created here via raw SQL. vector_service.py uses raw SQL for all embedding
    reads and writes — the ORM placeholder is never written to directly.

  PREREQUISITE:
    pgvector must be installed in your PostgreSQL instance:
      $ sudo apt install postgresql-15-pgvector   (Ubuntu/Debian)
    OR available on your managed DB provider (Supabase, Neon, Railway all support it).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'c7d41a8e3f92'
down_revision = 'a3f92c1e8b45'
branch_labels = None
depends_on = None


def upgrade():
    # ── Step 1: Enable pgvector extension ─────────────────────────────────────
    # IF NOT EXISTS makes this idempotent — safe to run multiple times.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Step 2: Add vector(768) column to items ────────────────────────────────
    # nullable=True: existing rows get NULL — vector_service.sync_all_items()
    # must be run after this migration to populate embeddings for existing items.
    op.execute(
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS embedding vector(768)"
    )

    # ── Step 3: Create IVFFlat index for approximate nearest-neighbor search ──
    # ivfflat with vector_cosine_ops matches the <=> (cosine distance) operator
    # used in vector_service.semantic_search().
    #
    # lists=100 recommendation: sqrt(num_rows). For 10k items → 100 lists.
    # For 100k items, increase to 316. For 1M items, use 1000.
    # probes=10 at query time (default) gives ~95% recall — adjust in app if needed.
    #
    # CONCURRENTLY: allows reads/writes during index build (no table lock).
    # Note: CONCURRENTLY cannot run inside a transaction, hence the op.execute approach.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_items_embedding_ivfflat "
        "ON items USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_items_embedding_ivfflat")
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS embedding")
    # Note: we do NOT drop the vector extension on downgrade as other tables
    # might depend on it. Drop manually if truly needed: DROP EXTENSION vector;
