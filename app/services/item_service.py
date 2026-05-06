from app.utils.request import get_country
from app.models import Item, ItemVariant, Store

def filter_items_by_country(query):
    country = get_country()
    if not country: return

    return query.join(Item.store_links)\
        .join(Store).filter(Store.country == country.upper())

def get_search_items(query):
    p_query = Item.query.filter(Item.name.ilike(f'%{query}%'))

    p_query = filter_items_by_country(p_query)

    return p_query.order_by(Item.created_at.desc()).limit(50).all()


def set_default_variant(item, variant):
    for v in item.variants:
        v.is_default = False
    variant.is_default = True

def ensure_default_variant(item):
    """
    Ensures an item has a default variant. Creates one if missing.
    Always returns a valid ItemVariant instance.
    """
    from app.extensions import db
    if not item.variants:
        variant = ItemVariant(
            item=item,
            title="Default",
            is_default=True,
            attributes={}
        )
        item.variants.append(variant)
        db.session.flush()  # Ensure variant.id is generated
        return variant

    # Find or set the default variant
    default = next((v for v in item.variants if v.is_default), None)
    if not default:
        item.variants[0].is_default = True
        default = item.variants[0]

    return default  # Always return a variant

def get_active_store_links(item):
    return [
        link
        for variant in item.variants
        for link in variant.store_links
        if link.is_active
    ]
