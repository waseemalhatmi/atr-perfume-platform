# =============================================================================
# Dockerfile — ATR Perfume Platform
# Strategy: Multi-Stage Build (Enterprise Pattern)
#
# Stage 1 (frontend-builder): Uses Node.js to compile the React/Vite app.
# Stage 2 (production):       Uses Python to run Flask. Copies ONLY the
#                             compiled frontend assets from Stage 1.
#
# Result: The final image contains NO Node.js and NO node_modules,
#         making it small, fast, and secure.
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: Frontend Builder
# ─────────────────────────────────────────────────────────────────────────────
# Use Node.js 22 on Debian Bookworm (full) to guarantee glibc ≥ 2.28,
# which is required by @rolldown/binding-linux-x64-gnu (native Rust addon).
FROM node:22-bookworm-slim AS frontend-builder

LABEL stage="frontend-builder"

WORKDIR /build/frontend

# ── Copy only the manifest files first (maximises layer cache hits) ────────────
COPY frontend/package.json ./

# ── Install ALL dependencies including platform-native optional bindings ────────
#
# WHY we do NOT use `npm ci` here:
#   • npm ci requires package-lock.json to be committed from the SAME OS
#   • A Windows-generated lockfile records Windows platform optionals
#     (@rolldown/binding-win32-x64-msvc) — these are missing on Linux.
#   • npm has a well-known bug (github.com/npm/cli/issues/4828) where
#     re-running `npm ci --include=optional` after the fact still fails
#     to fetch the correct platform binding.
#
# WHY `npm install --include=optional` works:
#   • npm detects the current OS (linux/x64) and installs the correct
#     native binding: @rolldown/binding-linux-x64-gnu
#   • A fresh lockfile is generated inside the container — no OS mismatch.
#
RUN npm install --include=optional

# ── Copy the rest of the frontend source ─────────────────────────────────────
COPY frontend/ ./

# ── Build the production bundle ───────────────────────────────────────────────
# We call vite build directly (with NODE_OPTIONS for memory limit).
# We do NOT use `npm run build` because that script calls `npm run install-optional`
# which invokes `npm ci` again — causing the exact lockfile-mismatch error above.
RUN NODE_OPTIONS=--max-old-space-size=400 npx vite build

# Verify the build succeeded and print the output size for transparency
RUN echo "✅ Frontend build complete. Output:" && ls -lah dist/


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: Production Runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

LABEL maintainer="ATR Perfume Platform"
LABEL description="Production image — Flask backend + pre-built React SPA"

# ── System Dependencies ───────────────────────────────────────────────────────
# Install only the essential system libraries:
#   build-essential : Required to compile some Python C-extension packages
#   libpq-dev       : Required for psycopg2 (PostgreSQL adapter)
#   curl            : Optional but useful for health checks inside container
# Clean up apt cache in the same RUN command to reduce image layer size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Create a non-root user for security ──────────────────────────────────────
# Running as root inside a container is a major security risk.
# We create a dedicated 'appuser' with no home directory.
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# ── Install Python Dependencies ───────────────────────────────────────────────
# Copy requirements first to leverage Docker layer caching.
# If requirements.txt hasn't changed, this layer is cached and skipped.
COPY requirements.txt .

RUN pip install --upgrade pip --quiet && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ── Copy Backend Source Code ──────────────────────────────────────────────────
COPY app/ ./app/
COPY config.py .
COPY main.py .
COPY celery_worker.py .
COPY migrations/ ./migrations/
COPY Procfile .

# ── THE KEY STEP: Import pre-built frontend from Stage 1 ─────────────────────
# We copy ONLY the compiled 'dist' folder from the builder stage.
# Node.js, node_modules, and all source files are LEFT BEHIND.
# This is what makes the final image small and production-ready.
#
# Path mapping:
#   Source (Stage 1): /build/frontend/dist
#   Destination:      /app/frontend/dist
#
# Flask looks for the SPA at: os.path.join(app.root_path, "..", "frontend", "dist")
# app.root_path = /app/app  →  ".." = /app  →  full path = /app/frontend/dist  ✅
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Verify the frontend assets are in place
RUN echo "✅ Frontend assets in place:" && ls -lah frontend/dist/

# ── Copy & Configure Entrypoint Script ───────────────────────────────────────
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# ── Set File Ownership ────────────────────────────────────────────────────────
# Give 'appuser' ownership of the entire /app directory
RUN chown -R appuser:appgroup /app

# ── Switch to Non-Root User ───────────────────────────────────────────────────
USER appuser

# ── Environment Variables ─────────────────────────────────────────────────────
# Set safe production defaults — all sensitive values come from Render secrets
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=10000

# ── Expose Port ───────────────────────────────────────────────────────────────
# Document that the container listens on port 10000 (Render's default)
EXPOSE 10000

# ── Health Check ─────────────────────────────────────────────────────────────
# Uses the dedicated /health endpoint (never rate-limited, always fast).
# Render's uptime monitor also hits this — must always return 200.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ── Launch Command ────────────────────────────────────────────────────────────
# Use the entrypoint script which handles migrations THEN starts the server
ENTRYPOINT ["./entrypoint.sh"]
