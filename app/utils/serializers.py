from app.utils.logger import get_logger

log = get_logger(__name__)

def _serialize_store_link(link):
    return {
        "id": link.id,
        "store": {"id": link.store.id, "name": link.store.name, "slug": link.store.slug},
        "price": float(link.price) if link.price else None,
        "old_price": float(link.old_price) if link.old_price else None,
        "currency": link.currency,
        "affiliate_url": link.affiliate_url,
        "availability": link.availability,
        "is_active": link.is_active,
    }

def _serialize_variant(variant):
    return {
        "id": variant.id,
        "title": variant.title,
        "is_default": variant.is_default,
        "attributes": variant.attributes,
        "store_links": [_serialize_store_link(l) for l in variant.store_links if l.is_active],
    }

def _serialize_item(item, full=False):
    if not item:
        return None
    try:
        images = [
            {"path": img.image_path, "alt": img.alt_text or item.name}
            for img in item.images
        ]
        brand_data    = {"id": item.brand.id,    "name": item.brand.name,    "slug": item.brand.slug}    if item.brand    else {"id": 0, "name": "Unknown", "slug": "unknown"}
        category_data = {"id": item.category.id, "name": item.category.name, "slug": item.category.slug} if item.category else {"id": 0, "name": "Unknown", "slug": "unknown"}
        base = {
            "id":          item.id,
            "name":        item.name,
            "slug":        item.slug,
            "description": item.description,
            "brand":       brand_data,
            "category":    category_data,
            "images":      images,
            "view_count":  item.view_count,
            "click_count": item.click_count,
            "min_price":   float(getattr(item, 'min_price_sql', None) or 0),
            "currency":    getattr(item, 'currency_sql', None) or "SAR",
        }
        if full:
            base.update({
                "variants":         [_serialize_variant(v) for v in item.variants],
                "specs":            item.full_details,
                "perfume_notes":    item.perfume_notes,
                "quick_details":    item.quick_details,
                "meta_description": item.meta_description,
            })
        return base
    except Exception as exc:
        log.error("serialize_item_failed", item_id=getattr(item, 'id', None), error=str(exc))
        return None
