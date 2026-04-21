# app/services/search_service.py
from sqlalchemy import or_
from app.models import Item, Brand, Category
from app.utils.request import get_country


def search_items(query: str, limit: int = 50) -> list:
    """
    Full-text search across item name, description, brand name, and category name.
    Optionally filters by country cookie if set.
    Returns up to `limit` results ordered by relevance (name match first).
    """
    if not query or not query.strip():
        return []

    q = query.strip()
    term = f"%{q}%"
    
    # Build base query with joins for brand/category search
    base_query = (
        Item.query
        .join(Item.brand)
        .join(Item.category)
        .filter(
            or_(
                Item.name.ilike(term),
                Item.description.ilike(term),
                Brand.name.ilike(term),
                Category.name.ilike(term),
            )
        )
        .options(
            __import__('sqlalchemy.orm', fromlist=['selectinload'])
            .selectinload(Item.images),
            __import__('sqlalchemy.orm', fromlist=['selectinload'])
            .selectinload(Item.brand),
            __import__('sqlalchemy.orm', fromlist=['selectinload'])
            .selectinload(Item.category),
        )
    )

    # Country filtering (only if a country cookie is set)
    country = get_country()
    if country:
        from app.models import ItemStoreLink, Store, ItemVariant
        base_query = (
            base_query
            .join(Item.variants)
            .join(ItemVariant.store_links)
            .join(ItemStoreLink.store)
            .filter(Store.country == country.upper())
        )

    # Prioritise exact name-starts-with matches first
    results = base_query.order_by(Item.name).limit(limit).all()
    return results
