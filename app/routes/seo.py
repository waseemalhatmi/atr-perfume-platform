from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
    url_for
)
from app.services.mailer import send_admin_email
from app.models import ContactMessage, db
from app import limiter

seo_bp = Blueprint('seo', __name__)

@seo_bp.route("/api/contact", methods=["POST"])
@limiter.limit("10 per hour;3 per minute")
def send_contact_message():
    data = {k: request.form.get(k, "").strip() for k in
            ("name", "email", "subject", "message")}

    if not all(data.values()):
        return jsonify({
            "success": False,
            "error": "One or more fields are empty!!"
            })

    msg = ContactMessage(
        **data,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    db.session.add(msg)
    db.session.commit()

    try:
        send_admin_email(data)  # wrapped function
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")

    current_app.logger.info(
        "Contact message saved (id=%s) from %s",
        msg.id, data["email"]
    )

    return jsonify({
        "success": True,
        "message": "Message sent successfully!!"
        })

@seo_bp.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\nSitemap: " + url_for('seo.sitemap', _external=True)
    return current_app.response_class(content, mimetype='text/plain')

@seo_bp.route('/sitemap.xml')
def sitemap():
    pages = []
    # Static pages
    for rule in current_app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            # Exclude admin and internal routes
            if not str(rule.endpoint).startswith('admin') and not str(rule.endpoint).startswith('api'):
                pages.append(url_for(rule.endpoint, _external=True))
    
    # Item pages
    from app.models import Item
    items = Item.query.all()
    for item in items:
        pages.append(url_for('catalog.item_page', item_id=item.id, _external=True))

    sitemap_xml = render_template('seo/sitemap.xml', pages=pages)
    return current_app.response_class(sitemap_xml, mimetype='application/xml')
