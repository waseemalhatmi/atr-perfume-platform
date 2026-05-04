#!/usr/bin/env bash
# =============================================================================
# entrypoint.sh — Professional Docker Entrypoint Script
# Runs database migrations and starts the Gunicorn production server.
# =============================================================================

# Exit immediately if any command fails — prevents starting a broken app
set -o errexit
# Treat unset variables as errors
set -o nounset
# Propagate pipe failures correctly
set -o pipefail

echo ""
echo "============================================="
echo "  🚀 ATR Perfume Platform — Production Start"
echo "============================================="
echo ""

# ── 1. Print Runtime Environment Info ────────────────────────────────────────
echo "📋 Environment:"
echo "   Python:     $(python --version)"
echo "   Flask ENV:  ${FLASK_ENV:-production}"
echo "   Port:       ${PORT:-10000}"
echo ""

# ── 2. Apply Database Migrations (Safe — Idempotent) ─────────────────────────
echo "🗄️  Applying database migrations..."
set +e
flask db upgrade
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️  Migration failed! This usually means tables already exist."
    echo "    Stamping initial schema and retrying..."
    flask db stamp b12bf6c34f4b
    
    set +e
    flask db upgrade
    SECOND_EXIT=$?
    set -e
    
    if [ $SECOND_EXIT -ne 0 ]; then
        echo "⚠️  Second migration failed (columns likely exist). Stamping head..."
        flask db stamp head
    fi
fi

echo "   ✅ Database schema is up to date."
echo ""

# ── 3. Start Gunicorn Production Server ──────────────────────────────────────
# Configuration explained:
#   --bind          : Listen on 0.0.0.0 so Render/cloud can route traffic in
#   --workers       : 2 workers per CPU core is the standard Gunicorn formula
#   --worker-class  : gthread allows handling concurrent requests efficiently
#   --threads       : 2 threads per worker for I/O-bound Flask requests
#   --timeout       : Kill a worker if it hangs for more than 120 seconds
#   --keep-alive    : Keep connections alive for 5 seconds (reduces TCP overhead)
#   --access-logfile: Log every request to stdout (captured by Render logs)
#   --error-logfile : Log errors to stderr (captured by Render logs)
#   --log-level     : 'info' for production (change to 'debug' only when needed)

echo "🌐 Starting Gunicorn..."
exec gunicorn main:app \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --worker-class "gthread" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile "-" \
    --error-logfile "-" \
    --log-level "info"
