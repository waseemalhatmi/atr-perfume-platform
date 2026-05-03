from flask import jsonify, request, abort
from flask_login import login_required
from app.models import Brand, Category, Setting, db
from app.utils.normalizers import generate_slug
from . import admin_bp
from .utils import admin_required

@admin_bp.route('/brands', methods=['GET'])
@login_required
@admin_required
def api_brands_list():
    brands = Brand.query.order_by(Brand.name).all()
    return jsonify([{'id': b.id, 'name': b.name, 'slug': b.slug} for b in brands])

@admin_bp.route('/brands', methods=['POST'])
@login_required
@admin_required
def api_add_brand():
    data = request.get_json()
    name = data.get('name')
    if not name: return jsonify({'error': 'الاسم مطلوب'}), 400
    brand = Brand(name=name, slug=generate_slug(name))
    db.session.add(brand)
    db.session.commit()
    return jsonify({'id': brand.id, 'name': brand.name, 'message': 'تم إضافة البراند بنجاح'})

@admin_bp.route('/brands/<int:brand_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    if brand.items:
        return jsonify({'error': 'لا يمكن حذف براند مرتبط بعطور موجودة.'}), 400
    db.session.delete(brand)
    db.session.commit()
    return jsonify({'message': 'تم حذف البراند بنجاح'})

@admin_bp.route('/categories', methods=['GET'])
@login_required
@admin_required
def api_categories_list():
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'slug': c.slug} for c in cats])

@admin_bp.route('/categories', methods=['POST'])
@login_required
@admin_required
def api_add_category():
    data = request.get_json()
    name = data.get('name')
    if not name: return jsonify({'error': 'الاسم مطلوب'}), 400
    cat = Category(name=name, slug=generate_slug(name))
    db.session.add(cat)
    db.session.commit()
    return jsonify({'id': cat.id, 'name': cat.name, 'message': 'تم إضافة التصنيف بنجاح'})

@admin_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.items:
        return jsonify({'error': 'لا يمكن حذف تصنيف مرتبط بعطور موجودة.'}), 400
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'تم حذف التصنيف بنجاح'})

@admin_bp.route('/settings', methods=['GET'])
@login_required
@admin_required
def api_settings_list():
    settings = Setting.query.all()
    return jsonify([{'key': s.key, 'value': s.value, 'label': s.key.replace('_', ' ').title()} for s in settings])

@admin_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required
def api_update_settings():
    data = request.get_json()
    if not data: return jsonify({'error': 'لا توجد بيانات'}), 400
    for key, value in data.items():
        setting = Setting.query.get(key)
        if setting:
            setting.value = str(value)
    db.session.commit()
    return jsonify({'message': 'تم تحديث الإعدادات بنجاح'})
