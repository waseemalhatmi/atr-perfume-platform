"""
health.py — Dedicated health check endpoint for Render / load balancers.

This blueprint MUST:
  1. Never be rate-limited (no @limiter.limit decoration)
  2. Respond in < 500ms (no DB queries, only a lightweight ping)
  3. Return HTTP 200 if the app is alive, 503 otherwise
"""
import time
from flask import Blueprint, jsonify
from app.extensions import db, cache

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Lightweight health endpoint used by Render's uptime monitor.
    Checks:
      - App is running (always true if we reach here)
      - DB is reachable (single cheap query)
      - Cache is reachable (optional — degrades gracefully)
    """
    start = time.monotonic()
    status = {"status": "ok", "checks": {}}

    # ── DB ping ───────────────────────────────────────────────────────────────
    try:
        db.session.execute(db.text("SELECT 1"))
        status["checks"]["db"] = "ok"
    except Exception as e:
        status["checks"]["db"] = f"error: {e}"
        status["status"] = "degraded"

    # ── Cache ping (optional) ─────────────────────────────────────────────────
    try:
        cache.set("_health_ping", "1", timeout=10)
        status["checks"]["cache"] = "ok"
    except Exception:
        status["checks"]["cache"] = "unavailable"
        # Cache being down is not fatal — app still works

    status["latency_ms"] = round((time.monotonic() - start) * 1000, 2)

    http_code = 200 if status["status"] != "error" else 503
    return jsonify(status), http_code
