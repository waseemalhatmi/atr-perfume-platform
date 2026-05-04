from flask import Blueprint, request, jsonify, send_from_directory, Response, stream_with_context
from app.services.search_service import search_items
from app.services.discovery_service import get_perfume_clones, get_similar_fragrances
from app.services.ai_service import ai_service
from app.utils.request import get_country, get_client_ip
from app.services.interaction_service import record_view
from app.constants import TargetType
from app.models import Category, Brand, Item, ItemVariant, ItemStoreLink, ItemSpecification, ComparisonLog, db
from flask_login import current_user
from app import limiter, cache
from app.utils.logger import get_logger
from app.utils.cache_metrics import record_hit, record_miss
import os
import json
import hashlib

catalog_bp = Blueprint('catalog', __name__)
log = get_logger(__name__)
from app.utils.serializers import _serialize_item, _serialize_variant, _serialize_store_link

# ─── Routes ─────────────────────────────────────────────────────────────────


@catalog_bp.route("/api/items", methods=["GET"])
@limiter.limit("300 per minute")
def api_items():
    """List & filter perfumes with pagination."""
    # ── Parse params early (needed for cache key) ────────────────────────────
    category_ids = sorted(request.args.getlist("category"))
    brand_ids    = sorted(request.args.getlist("brand"))
    sort_by      = request.args.get("sort", "newest")
    page         = request.args.get("page",     1,  type=int)
    per_page     = min(request.args.get("per_page", 12, type=int), 50)  # global max 50

    # ── Cache check (5-min TTL, keyed by all filter params) ──────────────────
    _ck = f"items:list:{hashlib.md5(f'{category_ids}{brand_ids}{sort_by}{page}{per_page}'.encode()).hexdigest()}"
    try:
        cached = cache.get(_ck)
        if cached is not None:
            record_hit("item_list")
            resp = jsonify({"success": True, "data": cached})
            resp.headers["X-Cache-Status"] = "HIT"
            return resp
        record_miss("item_list")
    except Exception:
        pass

    # ── Build query ────────────────────────────────────────────────────
    # NOTE: We do NOT eager-load variants/store_links here because:
    # - _serialize_item(full=False) never accesses item.variants
    # - min_price / currency come from SQL column properties (subqueries)
    # This removes O(N * variants) joins and cuts query time significantly.
    query = Item.query.options(
        db.selectinload(Item.brand),
        db.selectinload(Item.category),
        db.selectinload(Item.images),
    )

    if category_ids:
        query = query.filter(Item.category_id.in_(category_ids))
    if brand_ids:
        query = query.filter(Item.brand_id.in_(brand_ids))

    if sort_by == "oldest":
        query = query.order_by(Item.created_at.asc())
    elif sort_by == "popular":
        query = query.order_by(Item.view_count.desc())
    elif sort_by == "price_asc":
        query = query.order_by(Item.min_price_sql.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Item.min_price_sql.desc())
    else:
        query = query.order_by(Item.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    result = {
        "items": [_serialize_item(i) for i in pagination.items],
        "pagination": {
            "page":        pagination.page,
            "per_page":    pagination.per_page,
            "total":       pagination.total,
            "total_pages": pagination.pages,
            "has_next":    pagination.has_next,
            "has_prev":    pagination.has_prev,
        },
    }

    # Cache serialised result (JSON-safe dicts) for 5 minutes
    try:
        cache.set(_ck, result, timeout=300)
    except Exception:
        pass

    resp = jsonify({"success": True, "data": result})
    resp.headers["X-Cache-Status"] = "MISS"
    return resp


@catalog_bp.route("/api/items/<int:item_id>", methods=["GET"])
@limiter.limit("200 per minute")
def api_item_detail(item_id):
    """Full item detail with variants, specs, and perfume clones."""

    # ── Route-level JSON-safe cache ───────────────────────────────────────────
    # We cache serialised dicts (not SQLAlchemy objects) so this is safe for Redis.
    # View tracking is done BEFORE the cache check so counts stay accurate.
    item = Item.query.options(
        db.selectinload(Item.variants)
            .selectinload(ItemVariant.store_links)
            .selectinload(ItemStoreLink.store),
        db.selectinload(Item.images),
        db.selectinload(Item.specifications),
        db.selectinload(Item.brand),
        db.selectinload(Item.category),
    ).get_or_404(item_id)

    # Fire-and-forget view tracking (always runs, regardless of cache state)
    user = current_user if current_user.is_authenticated else None
    ip   = None if user else get_client_ip()
    try:
        record_view(item, TargetType.PRODUCT, user, ip)
    except Exception:
        pass

    # Check cache AFTER tracking view so view_count stays accurate
    _cache_key = f"item_detail:{item_id}"
    try:
        cached = cache.get(_cache_key)
        if cached is not None:
            resp = jsonify({"success": True, "data": cached})
            resp.headers['X-Cache-Status'] = 'HIT'
            return resp
    except Exception:
        pass

    # 1. Get Clones (Similar & Cheaper)
    clones_raw = get_similar_fragrances(item_id, limit=4, only_cheaper=True)
    clones = []
    for c in clones_raw:
        s = _serialize_item(c.get("item"))
        if s:
            clones.append({**s, "match_score": c["match_score"], "price_diff": c["price_diff"]})

    # 2. Get Similar Fragrance Profiles (Highest similarity regardless of price)
    similar_raw = get_similar_fragrances(item_id, limit=4, only_cheaper=False)
    similar = []
    for s_raw in similar_raw:
        s = _serialize_item(s_raw.get("item"))
        if s:
            similar.append({**s, "match_score": s_raw["match_score"], "price_diff": s_raw["price_diff"]})

    # 3. Get Recommended (Related by Brand/Category)
    recommended_items = item.get_related_items(limit=4)
    recommended = []
    for i in recommended_items:
        s = _serialize_item(i)
        if s:
            recommended.append(s)

    result_data = {
        "item":        _serialize_item(item, full=True),
        "clones":      clones,
        "similar":     similar,
        "recommended": recommended,
    }

    # Store serialised JSON-safe dicts — safe for Redis
    try:
        cache.set(_cache_key, result_data, timeout=1800)  # 30-min TTL
    except Exception:
        pass

    return jsonify({"success": True, "data": result_data})



from app.utils.validation import validate_query, SearchRequestSchema

@catalog_bp.route("/api/search", methods=["GET"])
@limiter.limit("30 per minute; 300 per hour")
@validate_query(SearchRequestSchema)
def api_search(validated_data: SearchRequestSchema):
    """Full-text search across items."""
    q = validated_data.q.strip()
    if not q:
        return jsonify({"success": False, "error": "Search query is required."}), 400

    results = search_items(q)
    return jsonify({
        "success": True,
        "data": {
            "query":   q,
            "results": [_serialize_item(i) for i in results],
            "count":   len(results),
        },
    })


@catalog_bp.route("/api/filters", methods=["GET"])
@limiter.exempt
def api_filters():
    """Return available filter options (categories & brands) — cached 1 hour."""
    _ck = "catalog:filters"
    try:
        cached = cache.get(_ck)
        if cached is not None:
            resp = jsonify({"success": True, "data": cached})
            resp.headers["X-Cache-Status"] = "HIT"
            return resp
    except Exception:
        pass

    categories = Category.query.order_by(Category.name).all()
    brands     = Brand.query.order_by(Brand.name).all()
    result = {
        "categories": [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories],
        "brands":     [{"id": b.id, "name": b.name, "slug": b.slug} for b in brands],
    }
    try:
        cache.set(_ck, result, timeout=3600)  # 1-hour TTL — filter options rarely change
    except Exception:
        pass
    return jsonify({"success": True, "data": result})


@catalog_bp.route("/api/set-country", methods=["POST"])
def api_set_country():
    """Persist the user's selected country in a cookie."""
    country  = (request.json or {}).get("country")
    response = jsonify({"success": True})
    if country:
        response.set_cookie("country", country.lower(), max_age=60 * 60 * 24 * 365)
    else:
        response.delete_cookie("country")
    return response


@catalog_bp.route("/api/compare", methods=["POST"])
@limiter.limit("60 per minute")
def api_compare():
    """High-performance comparison API with Redis caching and smart scoring."""
    data = request.get_json() or {}
    item_ids = data.get("ids", [])
    
    if not isinstance(item_ids, list) or not all(isinstance(x, int) for x in item_ids):
        return jsonify({"success": False, "error": "Invalid IDs format."}), 400
        
    item_ids = sorted(list(set(item_ids[:4]))) # Normalize & limit
    if not item_ids:
        return jsonify({"success": True, "data": {"items": []}})

    # 1. Redis Caching Check (graceful fallback)
    result_data = None
    try:
        cache_key = f"compare_v3_{hashlib.md5(json.dumps(item_ids).encode()).hexdigest()}"
        result_data = cache.get(cache_key)
        if result_data:
            record_hit("compare")
        else:
            record_miss("compare")
    except Exception as exc:
        log.warning("compare_cache_error", error=str(exc))

    if result_data:
        resp = jsonify({"success": True, "data": result_data, "source": "cache"})
        resp.headers['X-Cache-Status'] = 'HIT'
        return resp

    # 2. Database Fetch
    try:
        items = Item.query.options(
            db.selectinload(Item.variants).selectinload(ItemVariant.store_links).selectinload(ItemStoreLink.store),
            db.selectinload(Item.images),
            db.selectinload(Item.specifications),
            db.selectinload(Item.brand),
        ).filter(Item.id.in_(item_ids)).all()
        
        if not items:
            return jsonify({"success": False, "error": "العطور المطلوبة غير موجودة."}), 404

        # 3. Smart Scoring Logic — uses real engagement metrics
        scored_items = []
        for item in items:
            # ── Real metrics (no hardcoded values) ──────────────────────────────────────
            serialized = _serialize_item(item, full=True)

            # 1. Price score: cheaper = better (0–100)
            min_p = serialized.get('min_price') or 0
            price_score = max(0.0, 100.0 - min(min_p / 10.0, 50.0)) if min_p > 0 else 50.0

            # 2. Engagement score: real view_count + click_count (0–100)
            views  = item.view_count  or 0
            clicks = item.click_count or 0
            engagement   = (clicks * 3 + views) / 100.0
            rating_score = min(95.0, 50.0 + engagement)

            # 3. Availability score: active store links = trust signal (0–100)
            active_links = sum(
                1 for v in (item.variants or [])
                for lnk in (v.store_links or []) if lnk.is_active
            )
            perf_score = min(95.0, 50.0 + active_links * 10.0)

            total_score = (rating_score * 0.4) + (price_score * 0.3) + (perf_score * 0.3)
            serialized['ai_score'] = round(total_score, 1)
            scored_items.append(serialized)


        # Determine Winner
        winner = max(scored_items, key=lambda x: x.get('ai_score', 0))
        for item in scored_items:
            item['is_winner'] = (item['id'] == winner['id'])

        result_data = {
            "items": scored_items,
            "winner_id": winner['id'],
            "seo": {
                "title": f"مقارنة: {' vs '.join([i.name for i in items])}",
                "json_ld": {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Perfume Comparison",
                    "description": f"تحليل شامل ومقارنة بين {len(items)} من أرقى العطور العالمية."
                }
            }
        }

        # 4. Save to Cache (If possible)
        try:
            cache.set(cache_key, result_data, timeout=600)
        except:
            pass

        # 5. Logging
        try:
            log = ComparisonLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                item_ids=item_ids,
                winner_id=winner['id']
            )
            db.session.add(log)
            db.session.commit()
        except:
            db.session.rollback()

        resp = jsonify({"success": True, "data": result_data, "source": "db"})
        resp.headers['X-Cache-Status'] = 'MISS'
        return resp

    except Exception as exc:
        db.session.rollback()
        log.error("compare_api_error", error=str(exc))
        return jsonify({"success": False, "error": str(exc)}), 500


@catalog_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message')
    history = data.get('history', [])
    stream = data.get('stream', False)
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
        
    if stream:
        def generate():
            for chunk in ai_service.stream_response(message, history):
                # We send as a custom format or simple text
                # For simplicity in frontend, we use text/event-stream format style but simple chunks
                yield chunk
        return Response(stream_with_context(generate()), mimetype='text/plain')
    
    response = ai_service.get_response(message, history)
    return jsonify({"response": response})


# ─── SPA Catch-all (serve React app for all non-API routes) ─────────────────

@catalog_bp.route("/", defaults={"path": ""})
@catalog_bp.route("/<path:path>")
def spa(path):
    """Serve the React SPA for any non-API, non-static route."""
    from flask import current_app
    
    # 1. Strictly ignore API and Static paths - let Flask handlers take them
    if path.startswith(('api/', 'static/')) or 'api' in path:
        return jsonify({"success": False, "error": "Endpoint not handled by SPA."}), 404

    frontend_dist = os.path.abspath(os.path.join(current_app.root_path, "..", "frontend", "dist"))

    # 2. Try to serve specific files from dist if they exist (assets, favicon, etc.)
    # We check this first so that .js, .css, .svg files are served correctly.
    if path:
        target_file = os.path.join(frontend_dist, path)
        if os.path.isfile(target_file):
            return send_from_directory(frontend_dist, path)

    # 3. If the path has an extension but wasn't found in dist, it's a genuine 404 for a file.
    if "." in path and not path.endswith('.html'):
         return jsonify({"success": False, "error": f"File {path} not found in frontend build."}), 404

    # 4. Fallback to index.html for React Router (Single Page Application)
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        # ── SEO Dynamic Injection (Social Sharing Fix) ──
        if path.startswith('items/'):
            parts = path.split('/')
            if len(parts) == 2 and parts[1].isdigit():
                item_id = int(parts[1])
                item = Item.query.get(item_id)
                if item:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        html = f.read()
                    
                    from flask import url_for
                    title = f"{item.name} | ATR Perfumes"
                    desc = f"اكتشف وتسوق {item.name} من {item.brand.name} بأفضل الأسعار على منصة ATR."
                    img_url = url_for('serve_uploads', filename=item.images[0].path, _external=True) if item.images else "/og-image.jpg"
                    
                    html = html.replace("<title>منصة ATR للعطور الفاخرة | مقارنة، تقييم، واكتشاف أفضل العطور</title>", f"<title>{title}</title>")
                    html = html.replace('content="اكتشف أفضل العطور الفاخرة، قارن الأسعار، شاهد تقييمات المستخدمين، واحصل على أفضل العروض في منصة ATR."', f'content="{desc}"')
                    html = html.replace('content="ATR Perfume Platform"', f'content="{title}"')
                    html = html.replace('content="اكتشف وقارن أفضل العطور الفاخرة بسهولة"', f'content="{desc}"')
                    html = html.replace('content="/og-image.jpg"', f'content="{img_url}"')
                    
                    return Response(html, mimetype='text/html')

        return send_from_directory(frontend_dist, "index.html")
        
    # 5. Last resort fallback
    return jsonify({
        "success": False, 
        "error": "SPA build missing. Please run 'npm run build' in the frontend directory."
    }), 404
