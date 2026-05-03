from flask import request, jsonify, current_app
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
from app.models import Item, Brand, Category, Store, ItemImage, ItemSpecification, ItemVariant, ItemStoreLink, db
from app.utils.normalizers import generate_slug
from . import admin_bp
from .utils import admin_required, _save_uploaded_item_image

def _serialize_item_full(item):
    # Get notes from ItemSpecification
    spec = ItemSpecification.query.filter_by(item_id=item.id, category="مكونات العطر").first()
    notes = spec.spec_json if spec else {"القمة": "", "القلب": "", "القاعدة": ""}
    
    # Get store links
    links = []
    if item.variants:
        variant = item.variants[0]
        links = [{
            'id': l.id,
            'store_id': l.store_id,
            'store_name': l.store.name,
            'price': float(l.price) if l.price else None,
            'affiliate_url': l.affiliate_url
        } for l in variant.store_links]

    return {
        'id': item.id,
        'name': item.name,
        'slug': item.slug,
        'brand_id': item.brand_id,
        'category_id': item.category_id,
        'description': item.description,
        'meta_description': item.meta_description,
        'image': item.images[0].image_path if item.images else None,
        'notes': notes,
        'links': links
    }

@admin_bp.route('/items', methods=['GET'])
@login_required
@admin_required
def api_items_list():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify([_serialize_item_full(i) for i in items])

@admin_bp.route('/items/form-data', methods=['GET'])
@login_required
@admin_required
def api_items_form_data():
    """Returns brands, categories, and stores for the item form."""
    brands = [{'id': b.id, 'name': b.name} for b in Brand.query.all()]
    categories = [{'id': c.id, 'name': c.name} for c in Category.query.all()]
    stores = [{'id': s.id, 'name': s.name} for s in Store.query.all()]
    return jsonify({
        'brands': brands,
        'categories': categories,
        'stores': stores
    })

@admin_bp.route('/items', methods=['POST'])
@login_required
@admin_required
def api_add_item():
    try:
        # We use request.form because we might have an image file
        name = request.form.get('name')
        if not name:
            return jsonify({'error': 'اسم العطر مطلوب'}), 400
            
        item = Item(
            name=name,
            slug=generate_slug(name),
            brand_id=request.form.get('brand_id'),
            category_id=request.form.get('category_id'),
            description=request.form.get('description'),
            meta_description=request.form.get('meta_description')
        )
        db.session.add(item)
        db.session.flush()

        # Handle Image
        image_file = request.files.get('image')
        if image_file:
            image_path = _save_uploaded_item_image(image_file, item.id)
            img = ItemImage(item_id=item.id, image_path=image_path)
            db.session.add(img)

        # Handle Notes
        notes_json = {
            "القمة": request.form.get('notes_top'),
            "القلب": request.form.get('notes_heart'),
            "القاعدة": request.form.get('notes_base')
        }
        spec = ItemSpecification(item_id=item.id, category="مكونات العطر", spec_json=notes_json)
        db.session.add(spec)

        # Handle Links (assuming JSON array of links sent as string or multiple form fields)
        # For simplicity in this iteration, we'll look for store_id[], price[], affiliate_url[]
        store_ids = request.form.getlist('store_id[]')
        prices = request.form.getlist('price[]')
        urls = request.form.getlist('affiliate_url[]')
        
        if any(urls):
            variant = ItemVariant(item_id=item.id, title="Default", is_default=True)
            db.session.add(variant)
            db.session.flush()
            for s_id, p, u in zip(store_ids, prices, urls):
                if u:
                    db.session.add(ItemStoreLink(
                        variant_id=variant.id, store_id=s_id,
                        price=p if p else None, affiliate_url=u
                    ))

        db.session.commit()
        return jsonify({'message': 'تم إضافة العطر بنجاح', 'id': item.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/items/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def api_get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(_serialize_item_full(item))

@admin_bp.route('/items/<int:item_id>', methods=['PUT'])
@login_required
@admin_required
def api_edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        item.name = request.form.get('name', item.name)
        item.brand_id = request.form.get('brand_id', item.brand_id)
        item.category_id = request.form.get('category_id', item.category_id)
        item.description = request.form.get('description', item.description)
        item.meta_description = request.form.get('meta_description', item.meta_description)
        
        # Handle Image Update
        image_file = request.files.get('image')
        if image_file:
            image_path = _save_uploaded_item_image(image_file, item.id)
            if item.images:
                item.images[0].image_path = image_path
            else:
                db.session.add(ItemImage(item_id=item.id, image_path=image_path))

        # Handle Notes Update
        spec = ItemSpecification.query.filter_by(item_id=item.id, category="مكونات العطر").first()
        notes_json = {
            "القمة": request.form.get('notes_top'),
            "القلب": request.form.get('notes_heart'),
            "القاعدة": request.form.get('notes_base')
        }
        if spec: spec.spec_json = notes_json
        else: db.session.add(ItemSpecification(item_id=item.id, category="مكونات العطر", spec_json=notes_json))

        # Handle Links Update (Delete and Re-add for simplicity)
        if not item.variants:
            variant = ItemVariant(item_id=item.id, title="Default", is_default=True)
            db.session.add(variant)
            db.session.flush()
        else:
            variant = item.variants[0]
            ItemStoreLink.query.filter_by(variant_id=variant.id).delete()

        store_ids = request.form.getlist('store_id[]')
        prices = request.form.getlist('price[]')
        urls = request.form.getlist('affiliate_url[]')
        for s_id, p, u in zip(store_ids, prices, urls):
            if u:
                db.session.add(ItemStoreLink(
                    variant_id=variant.id, store_id=s_id,
                    price=p if p else None, affiliate_url=u
                ))

        db.session.commit()
        return jsonify({'message': 'تم تحديث العطر بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'تم حذف العطر بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
