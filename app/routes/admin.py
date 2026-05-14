from flask import Blueprint, request, jsonify, current_app, Response
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import User, Item, Brand, Category, ContactMessage, NewsletterSubscriber, QuizLog, ItemImage, Store, ItemVariant, ItemStoreLink, ItemSpecification
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from sqlalchemy import func
import os
import csv
import io
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"success": False, "error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def admin_stats():
    # Totals
    total_items = Item.query.count()
    total_users = User.query.count()
    
    # We might not have a global View model that records every view, but Item has view_count and click_count
    total_views = db.session.query(func.sum(Item.view_count)).scalar() or 0
    total_clicks = db.session.query(func.sum(Item.click_count)).scalar() or 0
    
    # Daily stats (dummy data if no robust timeseries exists, as Item views aren't timeseries by default except in Interaction logs)
    # Just returning a placeholder array that matches the Recharts area chart format
    today = datetime.utcnow()
    daily_stats = []
    for i in range(7, -1, -1):
        d = (today - timedelta(days=i)).strftime('%m/%d')
        daily_stats.append({
            "date": d,
            "views": int(total_views / 7) + (i*5),
            "clicks": int(total_clicks / 7) + (i*2)
        })

    return jsonify({
        "success": True,
        "totals": {
            "items": total_items,
            "users": total_users,
            "total_views": total_views,
            "total_clicks": total_clicks
        },
        "daily_stats": daily_stats
    })


@admin_bp.route("/items", methods=["GET"])
@admin_required
def get_items():
    items = Item.query.options(db.joinedload(Item.brand), db.joinedload(Item.category), db.joinedload(Item.images)).all()
    result = []
    for item in items:
        image_url = f"/static/uploads/{item.images[0].image_path}" if item.images else None
        result.append({
            "id": item.id,
            "name": item.name,
            "slug": item.slug,
            "brand_name": item.brand.name if item.brand else "بدون ماركة",
            "category_name": item.category.name if item.category else "بدون تصنيف",
            "views": item.view_count or 0,
            "clicks": item.click_count or 0,
            "image_url": image_url,
            "brand_id": item.brand_id,
            "category_id": item.category_id,
            "description": item.description,
            "is_active": True # Add field if available in DB
        })
    return jsonify(result)


@admin_bp.route("/items/form-data", methods=["GET"])
@admin_required
def get_form_data():
    brands = Brand.query.all()
    categories = Category.query.all()
    stores = Store.query.all()
    return jsonify({
        "brands": [{"id": b.id, "name": b.name} for b in brands],
        "categories": [{"id": c.id, "name": c.name} for c in categories],
        "stores": [{"id": s.id, "name": s.name} for s in stores]
    })


@admin_bp.route("/items/<int:item_id>", methods=["GET"])
@admin_required
def get_item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    image_url = f"/static/uploads/{item.images[0].image_path}" if item.images else None
    
    variants_data = []
    for v in item.variants:
        links_data = []
        for link in v.store_links:
            links_data.append({
                "id": link.id,
                "store_id": link.store_id,
                "external_item_id": link.external_item_id,
                "affiliate_url": link.affiliate_url,
                "price": float(link.price) if link.price else None,
                "old_price": float(link.old_price) if link.old_price else None,
                "currency": link.currency,
                "is_active": link.is_active
            })
        variants_data.append({
            "id": v.id,
            "title": v.title,
            "sku": v.sku,
            "attributes": v.attributes,
            "is_default": v.is_default,
            "store_links": links_data
        })
        
    specs_data = {}
    for spec in item.specifications:
        specs_data[spec.category] = spec.spec_json

    return jsonify({
        "id": item.id,
        "name": item.name,
        "slug": item.slug,
        "brand_id": item.brand_id,
        "category_id": item.category_id,
        "description": item.description,
        "image_url": image_url,
        "variants": variants_data,
        "specifications": specs_data
    })


@admin_bp.route("/items", methods=["POST"])
@admin_required
def add_item():
    try:
        import json
        data = request.form
        image = request.files.get('image')
        advanced_data_str = data.get('advanced_data', '{}')
        advanced_data = json.loads(advanced_data_str)
        
        from app.utils.normalizers import generate_slug as slugify
        
        new_item = Item()
        new_item.name = data.get('name')
        new_item.slug = slugify(data.get('name', ''))
        new_item.brand_id = data.get('brand_id')
        new_item.category_id = data.get('category_id')
        new_item.description = data.get('description')
        db.session.add(new_item)
        db.session.flush()

        if image:
            filename = secure_filename(image.filename)
            uploads_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            image_path = os.path.join(uploads_dir, filename)
            image.save(image_path)
            
            item_img = ItemImage()
            item_img.item_id = new_item.id
            item_img.image_path = filename
            item_img.position = 0
            db.session.add(item_img)

        # Handle Variants & Store Links
        variants = advanced_data.get('variants', [])
        for v_data in variants:
            variant = ItemVariant()
            variant.item_id = new_item.id
            variant.title = v_data.get('title')
            variant.sku = v_data.get('sku')
            variant.attributes = v_data.get('attributes')
            variant.is_default = v_data.get('is_default', False)
            db.session.add(variant)
            db.session.flush()
            
            for link_data in v_data.get('store_links', []):
                link = ItemStoreLink()
                link.variant_id = variant.id
                link.store_id = link_data.get('store_id')
                link.external_item_id = link_data.get('external_item_id')
                link.affiliate_url = link_data.get('affiliate_url')
                link.price = link_data.get('price')
                link.old_price = link_data.get('old_price')
                link.currency = link_data.get('currency', 'USD')
                link.is_active = link_data.get('is_active', True)
                db.session.add(link)

        # Handle Specifications
        specs = advanced_data.get('specifications', {})
        for category, spec_json in specs.items():
            spec = ItemSpecification()
            spec.item_id = new_item.id
            spec.category = category
            spec.spec_json = spec_json
            db.session.add(spec)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@admin_bp.route("/items/<int:item_id>", methods=["PUT"])
@admin_required
def update_item(item_id):
    try:
        import json
        item = Item.query.get_or_404(item_id)
        data = request.form
        image = request.files.get('image')
        advanced_data_str = data.get('advanced_data', '{}')
        advanced_data = json.loads(advanced_data_str)
        
        item.name = data.get('name', item.name)
        item.brand_id = data.get('brand_id', item.brand_id)
        item.category_id = data.get('category_id', item.category_id)
        item.description = data.get('description', item.description)

        if image:
            filename = secure_filename(image.filename)
            uploads_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            image_path = os.path.join(uploads_dir, filename)
            image.save(image_path)
            
            old_img = ItemImage.query.filter_by(item_id=item.id, position=0).first()
            if old_img:
                db.session.delete(old_img)
            
            item_img = ItemImage()
            item_img.item_id = item.id
            item_img.image_path = filename
            item_img.position = 0
            db.session.add(item_img)

        # Update variants
        variants = advanced_data.get('variants', None)
        if variants is not None:
            # Delete old variants not in payload
            incoming_variant_ids = [v['id'] for v in variants if v.get('id')]
            for existing_v in list(item.variants):
                if existing_v.id not in incoming_variant_ids:
                    db.session.delete(existing_v)
            
            for v_data in variants:
                if v_data.get('id'):
                    variant = ItemVariant.query.get(v_data['id'])
                    variant.title = v_data.get('title')
                    variant.sku = v_data.get('sku')
                    variant.attributes = v_data.get('attributes')
                    variant.is_default = v_data.get('is_default', False)
                else:
                    variant = ItemVariant()
                    variant.item_id = item.id
                    variant.title = v_data.get('title')
                    variant.sku = v_data.get('sku')
                    variant.attributes = v_data.get('attributes')
                    variant.is_default = v_data.get('is_default', False)
                    db.session.add(variant)
                
                db.session.flush()

                # Update store links for this variant
                incoming_link_ids = [l['id'] for l in v_data.get('store_links', []) if l.get('id')]
                for existing_l in list(variant.store_links):
                    if existing_l.id not in incoming_link_ids:
                        db.session.delete(existing_l)
                
                for link_data in v_data.get('store_links', []):
                    if link_data.get('id'):
                        link = ItemStoreLink.query.get(link_data['id'])
                        link.store_id = link_data.get('store_id')
                        link.external_item_id = link_data.get('external_item_id')
                        link.affiliate_url = link_data.get('affiliate_url')
                        link.price = link_data.get('price')
                        link.old_price = link_data.get('old_price')
                        link.currency = link_data.get('currency', 'USD')
                        link.is_active = link_data.get('is_active', True)
                    else:
                        link = ItemStoreLink()
                        link.variant_id = variant.id
                        link.store_id = link_data.get('store_id')
                        link.external_item_id = link_data.get('external_item_id')
                        link.affiliate_url = link_data.get('affiliate_url')
                        link.price = link_data.get('price')
                        link.old_price = link_data.get('old_price')
                        link.currency = link_data.get('currency', 'USD')
                        link.is_active = link_data.get('is_active', True)
                        db.session.add(link)

        # Update specifications
        specs = advanced_data.get('specifications', None)
        if specs is not None:
            # Delete old specs
            for existing_spec in list(item.specifications):
                if existing_spec.category not in specs:
                    db.session.delete(existing_spec)
            
            for category, spec_json in specs.items():
                spec = ItemSpecification.query.filter_by(item_id=item.id, category=category).first()
                if spec:
                    spec.spec_json = spec_json
                else:
                    spec = ItemSpecification()
                    spec.item_id = item.id
                    spec.category = category
                    spec.spec_json = spec_json
                    db.session.add(spec)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@admin_bp.route("/items/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_item(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([{
        "id": u.id,
        "email": u.email,
        "is_admin": u.is_admin,
        "provider": u.provider or 'local',
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users])


@admin_bp.route("/expert-analytics/data", methods=["GET"])
@admin_required
def get_analytics():
    logs = QuizLog.query.order_by(QuizLog.created_at.desc()).all()
    
    vibe_counts = {}
    gender_counts = {}
    apparel_counts = {}
    
    for l in logs:
        v = l.vibe or "غير محدد"
        g = l.gender or "غير محدد"
        a = l.apparel or "غير محدد"
        
        vibe_counts[v] = vibe_counts.get(v, 0) + 1
        gender_counts[g] = gender_counts.get(g, 0) + 1
        apparel_counts[a] = apparel_counts.get(a, 0) + 1

    # Format for charts
    quiz_vibe = {
        "labels": list(vibe_counts.keys()),
        "data": list(vibe_counts.values())
    }
    quiz_gender = {
        "labels": list(gender_counts.keys()),
        "data": list(gender_counts.values())
    }
    quiz_apparel = {
        "labels": list(apparel_counts.keys()),
        "data": list(apparel_counts.values())
    }

    recent_logs = [{
        "id": l.id,
        "created_at": l.created_at.isoformat() if l.created_at else None,
        "gender": l.gender,
        "apparel": l.apparel,
        "vibe": l.vibe,
        "user": l.user.email if l.user else "Guest"
    } for l in logs[:10]]

    # For top recommended, count recommended items
    rec_counts = {}
    for l in logs:
        if l.recommended_items:
            for rid in l.recommended_items:
                rec_counts[rid] = rec_counts.get(rid, 0) + 1
    
    top_recommended = []
    sorted_recs = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for rid, count in sorted_recs:
        it = Item.query.get(rid)
        if it:
            top_recommended.append({
                "id": it.id,
                "name": it.name,
                "brand": it.brand.name if it.brand else "",
                "recommend_count": count
            })

    return jsonify({
        "success": True,
        "quiz_vibe": quiz_vibe,
        "quiz_gender": quiz_gender,
        "quiz_apparel": quiz_apparel,
        "recent_logs": recent_logs,
        "top_recommended": top_recommended
    })

@admin_bp.route("/expert-analytics/export", methods=["GET"])
@admin_required
def export_analytics():
    logs = QuizLog.query.order_by(QuizLog.created_at.desc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Date', 'Gender', 'Apparel', 'Activity', 'Weather', 'Vibe', 'User Email'])
    for l in logs:
        cw.writerow([
            l.id,
            l.created_at,
            l.gender,
            l.apparel,
            l.activity,
            l.weather,
            l.vibe,
            l.user.email if l.user else 'Guest'
        ])
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=analytics.csv"}
    )


# Dummy routes for missing endpoints to prevent 404s
@admin_bp.route("/messages", methods=["GET"])
@admin_required
def get_messages():
    return jsonify([])

@admin_bp.route("/messages/<int:id>/read", methods=["POST"])
@admin_required
def read_message(id):
    return jsonify({"success": True})

@admin_bp.route("/messages/<int:id>", methods=["DELETE"])
@admin_required
def delete_message(id):
    return jsonify({"success": True})

@admin_bp.route("/newsletter", methods=["GET"])
@admin_required
def get_newsletter():
    subs = NewsletterSubscriber.query.all()
    return jsonify([{"email": s.email, "is_active": s.is_active} for s in subs])

from app.models.settings import Setting

@admin_bp.route("/settings", methods=["GET"])
@admin_required
def get_settings():
    settings = Setting.query.all()
    return jsonify([{"key": s.key, "value": s.value} for s in settings])

@admin_bp.route("/settings", methods=["PUT"])
@admin_required
def update_settings():
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
        
    for k, v in data.items():
        setting = Setting.query.get(k)
        if setting:
            setting.value = v
        else:
            setting = Setting()
            setting.key = k
            setting.value = v
            db.session.add(setting)
    
    db.session.commit()
    return jsonify({"success": True})

@admin_bp.route("/brands", methods=["GET"])
@admin_required
def get_brands():
    brands = Brand.query.all()
    return jsonify([{"id": b.id, "name": b.name, "slug": b.slug} for b in brands])

@admin_bp.route("/brands", methods=["POST"])
@admin_required
def add_brand():
    name = request.json.get('name')
    if not name:
        return jsonify({"success": False, "error": "Name required"}), 400
    try:
        from app.utils.normalizers import generate_slug as slugify
        b = Brand()
        b.name = name
        b.slug = slugify(name)
        db.session.add(b)
        db.session.commit()
        return jsonify({"success": True, "id": b.id, "name": b.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "هذه الماركة موجودة مسبقاً أو حدث خطأ."}), 400

@admin_bp.route("/brands/<int:id>", methods=["DELETE"])
@admin_required
def delete_brand(id):
    b = Brand.query.get(id)
    if b:
        db.session.delete(b)
        db.session.commit()
    return jsonify({"success": True})

@admin_bp.route("/categories", methods=["GET"])
@admin_required
def get_categories():
    cats = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "slug": c.slug} for c in cats])

@admin_bp.route("/categories", methods=["POST"])
@admin_required
def add_category():
    name = request.json.get('name')
    if not name:
        return jsonify({"success": False, "error": "Name required"}), 400
    try:
        from app.utils.normalizers import generate_slug as slugify
        c = Category()
        c.name = name
        c.slug = slugify(name)
        db.session.add(c)
        db.session.commit()
        return jsonify({"success": True, "id": c.id, "name": c.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "هذا التصنيف موجود مسبقاً أو حدث خطأ."}), 400

@admin_bp.route("/categories/<int:id>", methods=["DELETE"])
@admin_required
def delete_category(id):
    c = Category.query.get(id)
    if c:
        db.session.delete(c)
        db.session.commit()
    return jsonify({"success": True})


# ─── Store & Feed Management ──────────────────────────────────────────────

@admin_bp.route("/stores", methods=["GET"])
@admin_required
def get_stores():
    stores = Store.query.all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "country": s.country,
        "currency": s.currency,
        "xml_feed_url": s.xml_feed_url,
        "is_auto_sync": s.is_auto_sync,
        "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
        "sync_status": s.sync_status,
        "is_active": s.is_active,
        "logo_url": s.logo_url,
        "last_external_sync": s.last_external_sync.isoformat() if s.last_external_sync else None
    } for s in stores])

@admin_bp.route("/stores", methods=["POST"])
@admin_required
def create_store():
    data = request.json
    if not data or not data.get("name"):
        return jsonify({"success": False, "error": "Store name required"}), 400
    
    try:
        from app.utils.normalizers import generate_slug
        store_name = data.get("name")
        store = Store()
        store.name = store_name
        store.slug = generate_slug(store_name)
        store.website = data.get("website", "#")
        store.country = data.get("country", "Global")
        store.currency = data.get("currency", "SAR")
        store.xml_feed_url = data.get("xml_feed_url")
        store.is_auto_sync = data.get("is_auto_sync", False)
        store.logo_url = data.get("logo_url")
        db.session.add(store)
        db.session.commit()
        return jsonify({"success": True, "id": store.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@admin_bp.route("/stores/<int:id>", methods=["PUT"])
@admin_required
def update_store(id):
    store = Store.query.get_or_404(id)
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    store.name = data.get("name", store.name)
    store.country = data.get("country", store.country)
    store.currency = data.get("currency", store.currency)
    store.xml_feed_url = data.get("xml_feed_url", store.xml_feed_url)
    store.is_auto_sync = data.get("is_auto_sync", store.is_auto_sync)
    store.logo_url = data.get("logo_url", store.logo_url)
    store.is_active = data.get("is_active", store.is_active)
    
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

@admin_bp.route("/stores/<int:id>/sync", methods=["POST"])
@admin_required
def trigger_store_sync(id):
    store = Store.query.get_or_404(id)
    if not store.xml_feed_url:
        return jsonify({"success": False, "error": "Store has no XML Feed URL"}), 400
        
    from app.tasks import task_sync_store_feed
    task_sync_store_feed.delay(id)
    return jsonify({"success": True, "message": "Sync started in background"})

@admin_bp.route("/aliexpress/sync", methods=["POST"])
@admin_required
def trigger_aliexpress_sync():
    data = request.json or {}
    keywords = data.get('keywords', 'perfume')
    from app.tasks import task_sync_aliexpress
    task_sync_aliexpress.delay(keywords)
    return jsonify({"success": True, "message": f"AliExpress sync started for '{keywords}'"})

@admin_bp.route("/stores/<int:id>/sync-logs", methods=["GET"])
@admin_required
def get_store_sync_logs(id):
    from app.models import FeedSyncLog
    logs = FeedSyncLog.query.filter_by(store_id=id).order_by(FeedSyncLog.started_at.desc()).limit(20).all()
    return jsonify([{
        "id": l.id,
        "started_at": l.started_at.isoformat() if l.started_at else None,
        "finished_at": l.finished_at.isoformat() if l.finished_at else None,
        "status": l.status,
        "total_found": l.total_found,
        "new_added": l.new_added,
        "updated": l.updated,
        "deactivated": l.deactivated,
        "error_msg": l.error_msg
    } for l in logs])

@admin_bp.route("/feeds/preview", methods=["POST"])
@admin_required
def preview_feed():
    from app.services.admitad_service import AdmitadService
    data = request.json
    xml_url = data.get("xml_url") if data else None
    
    if not xml_url:
        return jsonify({"success": False, "error": "URL required"}), 400
    
    try:
        content = AdmitadService.fetch_feed(xml_url)
        products = AdmitadService.parse_xml(content)
        # Return summary and small preview
        return jsonify({
            "success": True, 
            "total_count": len(products),
            "preview": products[:10]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

