from flask import jsonify, request, abort
from flask_login import login_required
from app.models import User, ContactMessage, NewsletterSubscriber, db
from . import admin_bp
from .utils import admin_required

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def api_users_list():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'is_admin': u.is_admin,
        'provider': u.provider or 'local',
        'created_at': u.created_at.isoformat() if u.created_at else None
    } for u in users])

@admin_bp.route('/messages', methods=['GET'])
@login_required
@admin_required
def api_messages_list():
    msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'email': m.email,
        'subject': m.subject,
        'message': m.message,
        'is_read': m.is_read,
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in msgs])

@admin_bp.route('/messages/<int:msg_id>/read', methods=['POST'])
@login_required
@admin_required
def api_mark_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return jsonify({'message': 'تم تعليم الرسالة كمقروءة'})

@admin_bp.route('/messages/<int:msg_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    return jsonify({'message': 'تم حذف الرسالة بنجاح'})

@admin_bp.route('/newsletter', methods=['GET'])
@login_required
@admin_required
def api_newsletter_list():
    subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    return jsonify([{
        'id': s.id,
        'email': s.email,
        'subscribed_at': s.subscribed_at.isoformat() if s.subscribed_at else None
    } for s in subs])
