# app/services/discovery_service.py
from app.models import Item, ItemVariant, db
from sqlalchemy.orm import joinedload
import re

# Mapping dictionary for common fragrance notes (Synonyms)
# This ensures "Rose" matches "ورد" and "Oud" matches "عود", etc.
FRAGRANCE_MAP = {
    # Flowers
    "rose": ["ورد", "جوري", "rose", "rosa", "floral"],
    "jasmine": ["ياسمين", "jasmin", "jasmine", "فل"],
    "lavender": ["لافندر", "خزامى", "lavender"],
    "neroli": ["نيرولي", "زهر البرتقال", "neroli"],
    
    # Woods & Oriental
    "oud": ["عود", "agarwood", "oud", "aoud"],
    "musk": ["مسك", "musk", "musc"],
    "amber": ["عنبر", "amber", "ambre"],
    "sandalwood": ["صندل", "sandalwood", "sandal"],
    "patchouli": ["باتشولي", "patchouli", "patchouly"],
    "vanilla": ["فانيليا", "vanilla", "vanille"],
    
    # Fruits & Citrus
    "bergamot": ["برغموت", "bergamot", "bergamote"],
    "lemon": ["ليمون", "lemon", "citrus"],
    "orange": ["برتقال", "orange"],
    "apple": ["تفاح", "apple"],
    
    # Spices
    "saffron": ["زعفران", "saffron"],
    "cardamom": ["هيل", "cardamom", "cardamome"],
    "cinnamon": ["قرفة", "cinnamon", "canelle"]
}

def normalize_note(text):
    """
    Advanced linguistic cleaning:
    - Strips Arabic 'Al-' prefix
    - Removes common adjectives
    - Standardizes characters
    - Maps to common concept using FRAGRANCE_MAP
    """
    if not text: return ""
    text = text.lower().strip()
    
    # Remove Arabic "Al-" and some common prefixes/suffixes
    text = re.sub(r'^(ال|الـ)', '', text)
    
    # Remove common adjectives that don't change the ingredient essence
    adjectives = ['طبيعي', 'فاخر', 'مركز', 'خالص', 'معتق', 'pure', 'natural', 'absolute', 'luxury']
    for adj in adjectives:
        text = text.replace(adj, '').strip()

    # Standardization of similar letters
    text = text.replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    
    # Concept Mapping: Check if the word belongs to a known fragrance concept
    for concept, synonyms in FRAGRANCE_MAP.items():
        if any(syn in text for syn in synonyms):
            return concept
            
    return text

def flatten_notes(notes_dict):
    """
    Advanced Tokenization:
    - Splits strings by commas/spaces
    - Normalizes each individual word (token)
    - Returns a unique set of core ingredients
    """
    if not notes_dict: return []
    
    all_raw_notes = []
    if isinstance(notes_dict, dict):
        for val in notes_dict.values():
            if val:
                # Tokenization: split by comma, semicolon or slash
                tokens = re.split(r'[,;/،]', str(val))
                all_raw_notes.extend(tokens)
    
    # Process each token
    processed_notes = set()
    for raw_note in all_raw_notes:
        clean = normalize_note(raw_note)
        if clean and len(clean) > 1: # Ignore single character artifacts
            processed_notes.add(clean)
            
    return list(processed_notes)

def get_similar_fragrances(item_id, limit=6, only_cheaper=False):
    """
    High-performance engine to find similar fragrances.
    Uses Jaccard Similarity and supports price filtering.
    Eagerly loads relationships to prevent DetachedInstanceErrors.

    NOTE: @cache.memoize was intentionally removed. This function returns
    SQLAlchemy model instances which are NOT safely serializable to Redis
    (causes DetachedInstanceError on subsequent access). Caching is handled
    at the route level using JSON-safe serialized dicts instead.
    """
    # ── Phase 3: Instant Retrieval from Pre-calculated Table ──────────────────
    from app.models import ItemRecommendation
    
    # Optimize query with eager loading for ALL relationships needed by _serialize_item
    query = ItemRecommendation.query.options(
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.brand),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.category),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.images),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.variants).selectinload(ItemVariant.store_links)
    ).filter_by(item_id=item_id).filter_by(rec_type='clone' if only_cheaper else 'similar').limit(limit)
    
    stored_recs = query.all()
    
    if stored_recs:
        results = []
        for r in stored_recs:
            if r.recommended_item: # Defensive check
                results.append({
                    "item": r.recommended_item,
                    "match_score": r.match_score,
                    "price_diff": r.price_diff,
                    "is_cheaper": r.price_diff > 0
                })
        return results

    # FALLBACK: If not pre-calculated, calculate now.
    # NOTE: refresh_item_recommendations uses flush(), not commit().
    # We commit here explicitly since we are inside a request context.
    refresh_item_recommendations(item_id)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    # Try again with same eager loading options
    stored_recs = ItemRecommendation.query.options(
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.brand),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.category),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.images),
        joinedload(ItemRecommendation.recommended_item).selectinload(Item.variants).selectinload(ItemVariant.store_links)
    ).filter_by(item_id=item_id).filter_by(rec_type='clone' if only_cheaper else 'similar').limit(limit).all()
    
    results = []
    for r in stored_recs:
        if r.recommended_item:
            results.append({
                "item": r.recommended_item,
                "match_score": r.match_score,
                "price_diff": r.price_diff,
                "is_cheaper": r.price_diff > 0
            })
            
    # Fix #5: Ultimate Fallback if recommendation calculation yields nothing
    if not results:
        target_item = Item.query.get(item_id)
        if target_item:
            fallback_items = Item.query.options(
                joinedload(Item.brand),
                joinedload(Item.category),
                joinedload(Item.images),
                joinedload(Item.variants).selectinload(ItemVariant.store_links)
            ).filter(Item.category_id == target_item.category_id, Item.id != item_id).limit(limit).all()
            
            for item in fallback_items:
                results.append({
                    "item": item,
                    "match_score": 50, # Arbitrary fallback score
                    "price_diff": 0,
                    "is_cheaper": False
                })

    return results


def get_perfume_clones(item_id, limit=4):
    """Legacy wrapper for clones (cheaper similar items)."""
    return get_similar_fragrances(item_id, limit=limit, only_cheaper=True)


# ── Phase 2: High Performance Logic ──────────────────────────────────────────

def sync_item_normalized_notes(item):
    """
    Converts raw notes to standardized tokens and saves them to the DB.
    This runs once per item update, making future comparisons instant.
    """
    if not item.perfume_notes:
        item.normalized_notes = ""
        return ""
        
    tokens = flatten_notes(item.perfume_notes)
    token_str = ",".join(sorted(tokens))
    item.normalized_notes = token_str
    return token_str

from app.utils.locking import redis_lock

def refresh_item_recommendations(item_id):
    """
    The 'Chef' function:
    Calculates similarities for a specific item and saves them to the
    ItemRecommendation table for instant retrieval.

    Distributed Locking Strategy:
      We use a per-item Redis lock: lock:refresh_recs_item:{item_id}
      This means item 42 and item 99 can refresh concurrently (different locks),
      but two tasks for the SAME item 42 won't overlap (one skips, one runs).

      WHY NOT a shared 'refresh_recs' lock:
        A global lock means only 1 item refreshes system-wide at any time.
        If 50 items update simultaneously, 49 Celery tasks wait up to 2 minutes
        each → worker starvation → task queue backup → cascading timeouts.

      The inner function _do_refresh carries the actual logic so the lock
      is applied with the correct per-item key at call time.
    """
    @redis_lock(f"refresh_recs_item:{item_id}", timeout=120)
    def _do_refresh():
        return _refresh_item_recommendations_impl(item_id)

    return _do_refresh()


def _refresh_item_recommendations_impl(item_id):
    """Internal implementation — called only through refresh_item_recommendations()."""

    from app.models import ItemRecommendation
    
    target_item = Item.query.get(item_id)
    if not target_item: return False
    
    # Ensure notes are synced
    target_tokens = target_item.normalized_notes
    if not target_tokens:
        target_tokens = sync_item_normalized_notes(target_item)
    
    if not target_tokens: return False
    
    target_notes_set = set(target_tokens.split(','))
    
    # Get target price
    target_price = 0
    if target_item.default_variant:
        links = [l.price for l in target_item.default_variant.store_links if l.is_active and l.price]
        if links: target_price = float(min(links))

    # Find candidates with eager loading to prevent N+1 queries
    from sqlalchemy.orm import selectinload
    candidates = Item.query.options(
        selectinload(Item.variants).selectinload(ItemVariant.store_links)
    ).filter(
        Item.category_id == target_item.category_id,
        Item.id != target_item.id
    ).all()

    # Clear old recommendations for this item
    ItemRecommendation.query.filter_by(item_id=item_id).delete()

    recommendations = []
    for candidate in candidates:
        if not candidate.normalized_notes:
            sync_item_normalized_notes(candidate)
            
        if not candidate.normalized_notes: continue
        
        cand_notes_set = set(candidate.normalized_notes.split(','))
        
        # Jaccard calculation on pre-processed tokens
        intersection = target_notes_set.intersection(cand_notes_set)
        union = target_notes_set.union(cand_notes_set)
        similarity = (len(intersection) / len(union)) * 100 if union else 0

        if similarity < 10: continue

        # Get candidate price
        cand_price = 0
        if candidate.default_variant:
            links = [l.price for l in candidate.default_variant.store_links if l.is_active and l.price]
            if links: cand_price = float(min(links))

        price_diff = round(target_price - cand_price, 2) if target_price and cand_price else 0
        
        # Categorize
        rec_type = 'similar'
        if price_diff > 10: # If significantly cheaper
            rec_type = 'clone'
        elif target_item.brand_id == candidate.brand_id:
            rec_type = 'related'

        recommendations.append(ItemRecommendation(
            item_id=item_id,
            recommended_item_id=candidate.id,
            match_score=round(similarity),
            price_diff=price_diff,
            rec_type=rec_type
        ))

    # Save top recommendations (flush only — caller is responsible for commit)
    # This keeps the function safe to use in any context including celery tasks
    # without risking nested-transaction corruption under SQLAlchemy events.
    recommendations.sort(key=lambda x: (x.match_score, x.price_diff), reverse=True)
    for rec in recommendations[:12]:  # Save top 12
        db.session.add(rec)
    db.session.flush()  # Persist to transaction without committing
    return True

def sync_all_perfumes(batch_size: int = 200):
    """
    Batch-processes all perfumes in the database to sync normalized_notes tokens.

    WHY BATCHED (not Item.query.all()):
      Item.query.all() loads the ENTIRE items table into Python memory at once.
      At 100k items with JSON specs/descriptions, this can exceed 2-4 GB RAM,
      causing OOM kills on production servers.

    BATCH STRATEGY:
      Process `batch_size` items at a time, commit after each batch.
      Peak memory = O(batch_size) instead of O(total_rows).
      Each commit also releases locks held during the transaction.

    Args:
        batch_size: Number of items to process per DB round-trip. Default: 200.

    Returns:
        int: Total number of items processed.
    """
    count = 0
    offset = 0

    while True:
        batch = (
            Item.query
            .order_by(Item.id)           # Stable ordering — prevents skips on concurrent inserts
            .limit(batch_size)
            .offset(offset)
            .all()
        )
        if not batch:
            break                        # No more items — done

        for item in batch:
            sync_item_normalized_notes(item)
            count += 1

        db.session.commit()              # Commit each batch — releases locks, limits transaction size
        offset += batch_size

    return count

