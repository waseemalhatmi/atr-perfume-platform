import os
import uuid
from functools import wraps
from flask import flash, redirect, url_for, current_app, request, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAGIC_TO_IMAGE_TYPE = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
}

def _detect_image_type(file_storage):
    stream = file_storage.stream
    stream.seek(0)
    header = stream.read(16)
    stream.seek(0)

    for signature, image_type in MAGIC_TO_IMAGE_TYPE.items():
        if header.startswith(signature):
            return image_type

    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"

    return None

def _save_uploaded_item_image(image_file, item_id):
    if not image_file or not image_file.filename:
        return None

    safe_original_name = secure_filename(image_file.filename)
    if not safe_original_name:
        raise ValueError("اسم الملف غير صالح.")

    ext = os.path.splitext(safe_original_name)[1].lstrip(".").lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("نوع الصورة غير مدعوم. الأنواع المسموحة: JPG, PNG, WEBP.")

    detected_type = _detect_image_type(image_file)
    if not detected_type:
        raise ValueError("الملف المرفوع ليس صورة صالحة.")

    normalized_ext = "jpeg" if ext == "jpg" else ext
    if normalized_ext != detected_type:
        raise ValueError("امتداد الصورة لا يطابق محتوى الملف الحقيقي.")

    stream = image_file.stream
    stream.seek(0, os.SEEK_END)
    image_size = stream.tell()
    stream.seek(0)
    max_size = current_app.config.get("MAX_IMAGE_UPLOAD_SIZE", 5 * 1024 * 1024)

    if image_size > max_size:
        raise ValueError("حجم الصورة كبير جدًا. الحد الأقصى 5MB.")

    saved_ext = "jpg" if detected_type == "jpeg" else detected_type
    filename = f"item_{item_id}_{uuid.uuid4().hex[:12]}.{saved_ext}"
    upload_dir = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    upload_path = os.path.join(upload_dir, filename)
    image_file.save(upload_path)
    return f"static/uploads/{filename}"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            # If it's an API request, return JSON 403 instead of redirecting
            if request.path.startswith('/admin/') or request.headers.get('Accept') == 'application/json':
                return jsonify({"success": False, "error": "Admin privileges required."}), 403
            
            flash("عذراً، لا تمتلك صلاحيات الوصول لهذه الصفحة.", "error")
            return redirect(url_for('catalog.home'))
        return f(*args, **kwargs)
    return decorated_function

def safe_delete(obj, related_attr: str, error_msg: str, success_msg: str, redirect_target: str):
    if getattr(obj, related_attr, None):
        flash(error_msg, 'error')
    else:
        db.session.delete(obj)
        db.session.commit()
        flash(success_msg, 'success')
    return redirect(url_for(redirect_target))
