import os
import time
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from logging.handlers import RotatingFileHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from .models import User
from config import Config
from .extensions import db, mail, migrate, cache

# Rate limiter — initialized here so blueprints can import it
limiter = Limiter(key_func=get_remote_address)


def create_app():
    app = Flask(
        __name__, 
        static_url_path='/static', 
        static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    )
    app.config.from_object(Config)

    # ── Enterprise Observability: Sentry (Fix #7) ─────────────────────────────
    if os.environ.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=os.environ.get("SENTRY_DSN"),
            integrations=[FlaskIntegration(), CeleryIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.2, # Capture 20% of transactions for performance monitoring
            profiles_sample_rate=0.1,
            environment=os.environ.get("FLASK_ENV", "development")
        )

    # ── Celery Background Jobs (Fix #1) ───────────────────────────────────────
    from app.celery_ext import init_celery
    init_celery(app)


    # ── Core extensions ───────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # ── CORS ─────────────────────────────────────────────────────────────────
    # FIXED #4: Enforce explicit origin whitelist — never allow wildcard with
    # supports_credentials=True (browsers block it anyway, but it's bad practice).
    _raw_origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    react_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

    _is_production = os.environ.get("FLASK_ENV") == "production"
    if _is_production and "*" in react_origins:
        raise RuntimeError(
            "CORS wildcard (*) is forbidden in production with credentials. "
            "Set CORS_ORIGINS to your exact domain in the environment."
        )

    CORS(
        app,
        origins=react_origins,
        supports_credentials=True,   # Required for Flask-Login session cookies
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # ── Cache — Environment-Aware Selection ──────────────────────────────────
    # Priority: Redis (always preferred) → NullCache (prod fallback) → FileSystemCache (dev only)
    #
    # WHY NOT FileSystemCache in production:
    #   Gunicorn runs N worker processes. Each has its own isolated FS cache dir.
    #   There is NO shared state between workers — cache misses explode, stale data
    #   is served, and cache invalidation is completely broken.
    #
    # WHY NullCache in production without Redis:
    #   Better to have no cache (slightly slower) than broken/inconsistent cache.
    #   The app stays correct; operators are warned clearly in logs.
    if app.config.get("REDIS_URL"):
        cache_config = {
            "CACHE_TYPE":            "RedisCache",
            "CACHE_REDIS_URL":       app.config["REDIS_URL"],
            "CACHE_DEFAULT_TIMEOUT": 3600,
        }
    elif _is_production:
        # Production without Redis → disable caching entirely (safe default)
        app.logger.warning(
            "REDIS_URL is not configured in production. "
            "Caching is DISABLED (NullCache). All requests will hit the database. "
            "Set REDIS_URL to enable distributed caching."
        )
        cache_config = {"CACHE_TYPE": "NullCache"}
    else:
        # Development only — single worker, ephemeral cache is acceptable
        cache_config = {
            "CACHE_TYPE":            "FileSystemCache",
            "CACHE_DIR":             os.path.join(app.instance_path, "cache"),
            "CACHE_DEFAULT_TIMEOUT": 3600,
        }
    cache.init_app(app, config=cache_config)

    # ── Rate limiter ──────────────────────────────────────────────────────────
    limiter.init_app(app)
    if (
        os.environ.get("FLASK_ENV") == "production"
        and app.config.get("RATELIMIT_STORAGE_URI") == "memory://"
    ):
        app.logger.warning(
            "RATELIMIT_STORAGE_URI is set to memory:// in production. "
            "Use Redis for reliable distributed rate limits."
        )

    # ── Google OAuth ──────────────────────────────────────────────────────────
    oauth  = OAuth(app)
    google = oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://accounts.google.com/o/oauth2/token",
        access_token_params=None,
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        authorize_params=None,
        api_base_url="https://www.googleapis.com/oauth2/v1/",
        client_kwargs={"scope": "openid email profile"},
    )
    app.google = google

    # ── Flask-Login ───────────────────────────────────────────────────────────
    login_manager = LoginManager()
    login_manager.init_app(app)
    # For a pure API we return 401 JSON instead of redirecting to a login page
    login_manager.login_view = None

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"success": False, "error": "Authentication required."}), 401

    @login_manager.user_loader
    def load_user(user_id):
        return (
            User.query
            .options(db.joinedload(User.newsletter_subscription))
            .get(int(user_id))
        )

    # ── Observability & Monitoring (Enterprise Point 3, 9, 10, 11) ────────────────
    import time
    import json
    import uuid
    from flask_login import current_user

    MAX_CONCURRENT_REQUESTS = 500 # Load shedding threshold

    @app.before_request
    def start_timer():
        from flask import g
        g.start_time = time.time()
        g.trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
        
        # Load Shedding (Fix #11) with Dynamic Threshold
        try:
            active = cache.inc("global_active_requests")
            if active > MAX_CONCURRENT_REQUESTS:
                cache.dec("global_active_requests")
                app.logger.critical(json.dumps({
                    "event": "load_shedding",
                    "trace_id": g.trace_id,
                    "active_requests": active,
                    "error": "Overload"
                }))
                return jsonify({"success": False, "error": "Server is currently overloaded. Please try again later."}), 503
        except Exception:
            pass # Fail open if cache is down

    @app.after_request
    def log_request(response):
        from flask import g
        
        # Load Shedding decrement
        try:
            cache.dec("global_active_requests")
        except Exception:
            pass
            
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            log_data = {
                "event": "request_completed",
                "trace_id": getattr(g, "trace_id", "unknown"),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_sec": round(duration, 4),
                "ip": request.remote_addr,
                "user_id": current_user.id if current_user.is_authenticated else None
            }
            if duration > 1.0:
                log_data["warning"] = "slow_request"
                app.logger.warning(json.dumps(log_data))
            else:
                app.logger.info(json.dumps(log_data))
                
        # Inject Trace ID into response headers
        if hasattr(g, "trace_id"):
            response.headers["X-Trace-Id"] = g.trace_id
            
        return response

    # ── Slow Query Monitoring (Fix #11) ───────────────────────────────────────
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_time = conn.info.setdefault("query_start_time", []).pop()
        total_time = time.time() - start_time
        if total_time > 0.3: # > 300ms
            app.logger.warning(json.dumps({
                "event": "slow_query",
                "duration_sec": round(total_time, 4),
                "statement": statement[:200] + "..." if len(statement) > 200 else statement
            }))

    # ── Security headers ──────────────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"]        = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"]       = "1; mode=block"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response

    # ── Static-asset cache headers ────────────────────────────────────────────
    @app.after_request
    def set_cache_headers(response):
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    # ── Deferred Recommendation Refresh (Fix #1, #8) ──────────────────────────
    # Model events enqueue item IDs into g._pending_rec_refresh.
    # We now dispatch them to Celery background workers to avoid blocking the API.
    @app.after_request
    def process_pending_recommendation_refresh(response):
        from flask import g
        pending = getattr(g, "_pending_rec_refresh", None)
        if pending:
            from app.tasks import task_refresh_item_recommendations
            for item_id in pending:
                try:
                    # Offload to Celery Background Queue
                    task_refresh_item_recommendations.delay(item_id)
                except Exception as exc:
                    app.logger.error(f"Failed to queue Celery refresh task for item {item_id}: {exc}")
        return response

    # ── Global JSON error handlers (Fix #13) ──────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": str(e) if not hasattr(e, 'description') else getattr(e, 'description', 'Bad Request'), "code": 400}), 400

    @app.errorhandler(401)
    def unauthorized_err(e):
        return jsonify({"error": "Unauthorized.", "code": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden.", "code": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        # 1. API routes always return JSON
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found.", "code": 404}), 404
        
        # 2. Attempt to serve the frontend assets/files
        from flask import send_from_directory
        frontend_dist = os.path.join(app.root_path, "..", "frontend", "dist")
        
        # lstrip('/') converts "/assets/main.js" -> "assets/main.js"
        requested_path = request.path.lstrip('/')
        
        # If the specific file exists (e.g. /favicon.svg or /assets/index-xxx.js), serve it.
        if requested_path and os.path.exists(os.path.join(frontend_dist, requested_path)):
            return send_from_directory(frontend_dist, requested_path)

        # 3. For everything else (SPA routes like /login, /products), serve index.html
        if os.path.exists(os.path.join(frontend_dist, "index.html")):
            return send_from_directory(frontend_dist, "index.html")
            
        return jsonify({"error": "Backend route not found and SPA build missing.", "code": 404}), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        from app.utils.logger import get_logger as _get_logger
        _rl_log = _get_logger("rate_limiter")
        _rl_log.warning(
            "rate_limit_exceeded",
            ip=request.remote_addr,
            endpoint=request.endpoint,
            path=request.path,
        )
        return jsonify({"error": "Too many requests. Please slow down.", "code": 429}), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error.", "code": 500}), 500

    # ── Static Uploads Handler ──────────────────────────────────────────────
    @app.route('/static/uploads/<path:filename>')
    def serve_uploads(filename):
        """Explicitly serve files from the uploads directory to prevent 404s."""
        uploads_dir = os.path.join(app.static_folder, 'uploads')
        return send_from_directory(uploads_dir, filename)

    # ── Register blueprints ───────────────────────────────────────────────────
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.catalog import catalog_bp
    app.register_blueprint(catalog_bp)

    from .routes.interaction import interaction_bp
    app.register_blueprint(interaction_bp)

    from .routes.api import api_bp
    app.register_blueprint(api_bp)

    from .routes.seo import seo_bp
    app.register_blueprint(seo_bp)

    # ── Production Logging System (JSON structured) ───────────────────────────
    if not os.path.exists('logs'):
        os.mkdir('logs')
    import json as _json

    class _JsonFileFormatter(logging.Formatter):
        """Single-line JSON log records for log aggregators (Loki, ELK, etc.)"""
        def format(self, record):
            from datetime import datetime, timezone
            return _json.dumps({
                "ts":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "level":   record.levelname,
                "message": record.getMessage(),
                "module":  record.module,
            }, ensure_ascii=False)

    file_handler = RotatingFileHandler('logs/perfume_monitor.log', maxBytes=10_240_000, backupCount=10)
    file_handler.setFormatter(_JsonFileFormatter())
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Perfume Monitor Startup')


    # ── Structured logger for performance middleware ───────────────────────────
    from app.utils.logger import get_logger as _get_logger
    _perf_log = _get_logger("perf")

    @app.after_request
    def log_performance(response):
        from flask import g
        if hasattr(g, "start_time"):
            latency = (time.time() - g.start_time) * 1000
            response.headers["X-Response-Time-MS"] = f"{latency:.2f}"
            if request.path.startswith('/api/'):
                cache_status = response.headers.get('X-Cache-Status', 'MISS')
                log_fn = _perf_log.warning if latency > 500 else _perf_log.info
                log_fn(
                    "request_completed",
                    path=request.path,
                    status=response.status_code,
                    latency_ms=round(latency, 2),
                    cache=cache_status,
                )
        return response

    return app
