from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.models import Item, QuizLog, db
from app.services.price_service import get_item_price_history
from app import limiter

api_bp = Blueprint("api", __name__, url_prefix="/api")


from app.utils.idempotency import idempotent

from app.utils.validation import validate_json, QuizRequestSchema

# ─── Quiz Recommend ──────────────────────────────────────────────────────────
@api_bp.route("/quiz/recommend", methods=["POST"])
@limiter.limit("60 per hour;10 per minute")
@idempotent(timeout=300)
@validate_json(QuizRequestSchema) # Fix #5 & #11: Pydantic Validation Layer
def quiz_recommend(validated_data: QuizRequestSchema):
    """
    FIXED: No longer calls Item.query.all().
    Uses DB-level ILIKE filtering with LIMIT 20, then lightweight Python scoring.
    """
    gender   = validated_data.gender
    apparel  = validated_data.apparel
    activity = validated_data.activity
    weather  = validated_data.weather
    vibe     = validated_data.vibe

    # ── Keyword mapping ───────────────────────────────────────────────────────
    weights = []
    if gender == "نسائي":    weights.append("نسائ")
    elif gender == "رجالي":  weights.append("رجالي")

    if apparel == "suit":     weights.extend(["فخم", "رسمي", "أنيق", "Luxury", "Elegant"])
    elif apparel == "casual": weights.extend(["يومي", "كاجوال", "منعش", "Daily", "Casual"])
    elif apparel == "sport":  weights.extend(["رياضي", "نشاط", "Sport", "Fresh"])

    if activity == "office":    weights.extend(["هادئ", "نظيف", "Office", "Professional"])
    elif activity == "outdoor": weights.extend(["صيفي", "خارجية", "Summer", "Outdoor"])
    elif activity == "nightout":weights.extend(["سهرة", "حفلة", "جذاب", "Night", "Clubbing"])

    if weather == "cold": weights.extend(["عود", "خشب", "دافئ", "Winter", "Oud", "Warm"])
    elif weather == "hot": weights.extend(["حمضيات", "بحر", "انتعاش", "Summer", "Citrus", "Oceanic"])

    if vibe == "mysterious": weights.extend(["غامض", "بخور", "جلد", "Mysterious", "Smoky"])
    elif vibe == "bold":     weights.extend(["قوي", "جريء", "توابل", "Bold", "Strong"])
    elif vibe == "clean":    weights.extend(["مسك", "بودرة", "Clean", "Musk", "Powdery"])

    # ── DB-level filter — max 20 rows, no full scan ───────────────────────────
    results = []
    
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 3, type=int)
    per_page = min(per_page, 10) # limit max items
    
    if weights:
        # Hardening Fix #1: Use Vector Semantic Search for high-quality ranking
        from app.services.vector_service import vector_service
        search_query = f"{gender} perfume with vibes: {vibe}, for {activity} or {apparel} use. Keywords: {', '.join(weights)}"
        
        # We fetch more items and then filter by gender properly
        candidates = vector_service.semantic_search(search_query, limit=20)
        
        scored = []
        for item in candidates:
            desc  = (item.description or "").lower()
            name  = item.name.lower()
            
            # Strict Gender guard
            if gender == "نسائي" and "رجالي" in desc and "نسائ" not in desc:
                continue
            if gender == "رجالي" and "نسائ" in desc and "رجالي" not in desc:
                continue
                
            scored.append(item)

        # Pagination logic
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        results = scored[start_idx:end_idx]

    # ── Fallback: random without full-table scan ──────────────────────────────
    if not results:
        results = (
            Item.query
            .options(joinedload(Item.images), joinedload(Item.brand))
            .order_by(db.func.random())
            .limit(per_page)
            .all()
        )

    # ── Log quiz ──────────────────────────────────────────────────────────────
    try:
        db.session.add(QuizLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            gender=gender, apparel=apparel, activity=activity,
            weather=weather, vibe=vibe,
            recommended_items=[r.id for r in results],
        ))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f"Quiz logging failed: {exc}")

    from app.utils.serializers import _serialize_item
    return jsonify({"success": True, "items": [_serialize_item(r) for r in results]})


# ─── Price History ────────────────────────────────────────────────────────────
@api_bp.route("/items/<int:item_id>/price-history")
@limiter.limit("100 per day; 10 per minute")
def api_price_history(item_id):
    return jsonify(get_item_price_history(item_id))

# ─── Health & Readiness APIs (Enterprise Point 4) ─────────────────────────────
@api_bp.route("/health")
@limiter.exempt
def health_check():
    """Liveness probe for orchestrators (e.g., Kubernetes)."""
    return jsonify({"status": "healthy"}), 200

@api_bp.route("/readiness")
@limiter.exempt
def readiness_check():
    """Readiness probe checking DB, Redis, and AI connections."""
    status = {"ready": True, "db": "ok", "redis": "ok", "ai": "ok"}
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception as e:
        status["db"] = "failed"
        status["ready"] = False
        current_app.logger.error(f"Readiness DB Check Failed: {e}")

    try:
        from app.extensions import cache
        cache.get('test_key')
    except Exception as e:
        status["redis"] = "failed"
        status["ready"] = False
        current_app.logger.error(f"Readiness Cache Check Failed: {e}")

    # Checking AI requires a lightweight check if applicable, or we mark ok if loaded
    from app.services.vector_service import vector_service
    if not vector_service.model:
        status["ai"] = "degraded (no model)"

    return jsonify(status), (200 if status["ready"] else 503)
