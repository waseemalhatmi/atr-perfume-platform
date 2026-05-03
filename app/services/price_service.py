# app/services/price_service.py
from app.models import db, ItemStoreLink, PriceHistory, PriceAlert, Notification, Item

def record_daily_prices():
    """
    Iterates through all store links, records the current price in history,
    and checks for price alerts.
    """
    links = ItemStoreLink.query.filter_by(is_active=True).all()
    count = 0
    alerts_triggered = 0

    for link in links:
        # 1. Record History
        history = PriceHistory(
            variant_link_id=link.id,
            price=link.price
        )
        db.session.add(history)
        count += 1

        # 2. Check Alerts
        # We check alerts for the specific ITEM (since alerts are linked to Item)
        # and current price of this specific link.
        active_alerts = PriceAlert.query.filter_by(
            item_id=link.variant.item_id, 
            is_active=True
        ).all()

        for alert in active_alerts:
            if link.price <= alert.target_price:
                # Trigger In-App Notification
                if alert.user_id:
                    # Check if a similar notification was sent recently to avoid spam
                    # (Simple implementation: just send it)
                    item_name = link.variant.item.name
                    store_name = link.store.name
                    
                    notification = Notification(
                        user_id=alert.user_id,
                        title=f"🎉 انخفاض في سعر {item_name}!",
                        message=f"انخفض السعر في متجر {store_name} ووصل إلى سعرك المستهدف: {link.price} {link.currency}",
                        link=f"/items/{link.variant.item_id}"
                    )
                    db.session.add(notification)
                    
                    # Deactivate alert after triggering so it doesn't spam every day
                    alert.is_active = False 
                    
                    alerts_triggered += 1

    db.session.commit()
    return count, alerts_triggered

def get_item_price_history(item_id):
    """
    Returns historical price data for all variants of an item.
    Formatted for Chart.js.
    """
    # For simplicity, we'll fetch history for the default variant's first store link
    item = Item.query.get(item_id)
    if not item or not item.default_variant:
        return []

    default_link = next((l for l in item.default_variant.store_links if l.is_active), None)
    if not default_link:
        return []

    history = PriceHistory.query.filter_by(variant_link_id=default_link.id).order_by(PriceHistory.recorded_at.asc()).all()
    
    return [
        {
            "date": h.recorded_at.strftime("%Y-%m-%d"),
            "price": float(h.price)
        }
        for h in history
    ]
