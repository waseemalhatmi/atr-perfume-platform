import csv
import io
from datetime import datetime, timedelta
from collections import Counter
from flask import request, current_app, make_response, jsonify, abort, redirect
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Item, Brand, Category, View, ItemClick, NewsletterSubscriber, ContactMessage, QuizLog, db
from . import admin_bp
from .utils import admin_required

def _serialize_item_mini(item):
    return {
        'id': item.id,
        'name': item.name,
        'brand': item.brand.name,
        'view_count': item.view_count,
        'created_at': item.created_at.isoformat() if item.created_at else None
    }

def _serialize_message(msg):
    return {
        'id': msg.id,
        'name': msg.name,
        'email': msg.email,
        'subject': msg.subject,
        'is_read': msg.is_read,
        'created_at': msg.created_at.isoformat() if msg.created_at else None
    }

@admin_bp.route('/stats')
@login_required
@admin_required
def dashboard_stats():
    """Returns JSON data for the admin dashboard in the format expected by the frontend."""
    # 1. Totals
    from app.models import User
    totals = {
        'items': Item.query.count(),
        'total_views': View.query.count(),
        'total_clicks': ItemClick.query.count(),
        'users': User.query.count()
    }

    # 2. Daily Stats (Last 7 Days)
    today = datetime.utcnow().date()
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    
    daily_stats = []
    for d in dates:
        d_str = d.strftime('%Y-%m-%d')
        
        # Views for this day
        v_count = View.query.filter(func.date(View.created_at) == d).count()
        # Clicks for this day
        c_count = ItemClick.query.filter(func.date(ItemClick.created_at) == d).count()
        
        daily_stats.append({
            'date': d_str,
            'views': v_count,
            'clicks': c_count
        })

    return jsonify({
        'totals': totals,
        'daily_stats': daily_stats
    })

@admin_bp.route('/expert-analytics/data')
@login_required
@admin_required
def expert_analytics_data():
    vibe_stats = db.session.query(QuizLog.vibe, func.count(QuizLog.id)).group_by(QuizLog.vibe).all()
    vibe_labels = [v[0] for v in vibe_stats if v[0]]
    vibe_data = [v[1] for v in vibe_stats if v[0]]

    gender_stats = db.session.query(QuizLog.gender, func.count(QuizLog.id)).group_by(QuizLog.gender).all()
    gender_labels = [g[0] for g in gender_stats if g[0]]
    gender_data = [g[1] for g in gender_stats if g[0]]

    apparel_stats = db.session.query(QuizLog.apparel, func.count(QuizLog.id)).group_by(QuizLog.apparel).all()
    apparel_labels = [a[0] for a in apparel_stats if a[0]]
    apparel_data = [a[1] for a in apparel_stats if a[0]]

    # Process top recommended items from quiz logs
    all_logs = QuizLog.query.all()
    item_id_counts = Counter()
    for log in all_logs:
        if log.recommended_items:
            item_id_counts.update(log.recommended_items)
    
    top_5_ids = [item_id for item_id, count in item_id_counts.most_common(5)]
    top_recommended = []
    if top_5_ids:
        items_map = {item.id: item for item in Item.query.filter(Item.id.in_(top_5_ids)).all()}
        for iid in top_5_ids:
            if iid in items_map:
                item = items_map[iid]
                top_recommended.append({
                    'id': item.id,
                    'name': item.name,
                    'brand': item.brand.name,
                    'recommend_count': item_id_counts[iid]
                })

    recent_logs = [{
        'id': log.id,
        'created_at': log.created_at.isoformat(),
        'user': log.user.email if log.user else 'Guest',
        'gender': log.gender,
        'vibe': log.vibe
    } for log in QuizLog.query.order_by(QuizLog.created_at.desc()).limit(15).all()]

    return jsonify({
        'quiz_vibe': {'labels': vibe_labels, 'data': vibe_data},
        'quiz_gender': {'labels': gender_labels, 'data': gender_data},
        'quiz_apparel': {'labels': apparel_labels, 'data': apparel_data},
        'top_recommended': top_recommended,
        'recent_logs': recent_logs
    })

@admin_bp.route('/expert-analytics/export')
@login_required
@admin_required
def export_quiz_logs():
    logs = QuizLog.query.order_by(QuizLog.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'User Email', 'Gender', 'Apparel', 'Activity', 'Weather', 'Vibe', 'Recommended IDs'])
    
    for log in logs:
        writer.writerow([
            log.id, 
            log.created_at.strftime('%Y-%m-%d %H:%M'),
            log.user.email if log.user else 'Guest',
            log.gender,
            log.apparel,
            log.activity,
            log.weather,
            log.vibe,
            ", ".join(map(str, log.recommended_items)) if log.recommended_items else ""
        ])
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=expert_quiz_logs.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@admin_bp.route("/run-price-tracker", methods=['POST'])
@login_required
@admin_required
def run_price_tracker():
    from app.services.price_service import record_daily_prices
    count, alerts = record_daily_prices()
    return jsonify({"recorded": count, "alerts_triggered": alerts})
# Compatibility Redirects for old frontend builds
@admin_bp.route('/admin/stats')
def old_stats_redirect():
    return redirect('/api/admin/stats')

@admin_bp.route('/admin/expert-analytics/data')
def old_analytics_redirect():
    return redirect('/api/admin/expert-analytics/data')
