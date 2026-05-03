# app/services/search_service.py
from sqlalchemy import or_, func
from sqlalchemy.orm import selectinload
from app.models import Item, Brand, Category, ItemStoreLink, Store, ItemVariant
from app.utils.request import get_country


def search_items(query: str, limit: int = 50) -> list:
    """
    Full-text search across item name, description, brand name, and category name.
    Optionally filters by country cookie if set.
    Returns up to `limit` results ordered by relevance (name match first).

    NOTE: Uses 'simple' FTS dictionary — 'arabic' does not exist in PostgreSQL
    by default and would cause a runtime error. 'simple' correctly tokenises
    Arabic text without stemming, which is sufficient for this use-case.
    """
    if not query or not query.strip():
        return []

    q = query.strip()
    term = f"%{q}%"

    # 'simple' is available in every PostgreSQL installation and handles
    # Arabic text correctly (no stemming, just lowercasing & tokenisation).
    fts_vector = func.to_tsvector('simple', Item.name + ' ' + func.coalesce(Item.description, ''))
    fts_query  = func.plainto_tsquery('simple', q)

    # Build base query with joins for brand/category search
    base_query = (
        Item.query
        .join(Item.brand)
        .join(Item.category)
        .filter(
            or_(
                fts_vector.op('@@')(fts_query),
                Item.name.ilike(term),          # direct ILIKE fallback
                Brand.name.ilike(term),
                Category.name.ilike(term),
            )
        )
        .options(
            selectinload(Item.images),
            selectinload(Item.brand),
            selectinload(Item.category),
        )
    )

    # Country filtering (only if a country cookie is set)
    country = get_country()
    if country:
        base_query = (
            base_query
            .join(Item.variants)
            .join(ItemVariant.store_links)
            .join(ItemStoreLink.store)
            .filter(Store.country == country.upper())
        )

    # Prioritise FTS rank, then exact name-starts-with matches
    rank    = func.ts_rank(fts_vector, fts_query)
    results = base_query.order_by(rank.desc(), Item.name).limit(limit).all()
    return results
