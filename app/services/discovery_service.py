# app/services/discovery_service.py
from app.models import Item, db
from sqlalchemy import or_

def get_perfume_clones(item_id, limit=4):
    """
    Finds perfumes with similar notes but lower prices.
    Returns a list of (item, similarity_score).
    """
    target_item = Item.query.get(item_id)
    if not target_item:
        return []

    target_notes = target_item.perfume_notes
    if not target_notes:
        return []

    # Flatten notes for comparison
    def flatten_notes(notes_dict):
        all_notes = []
        for key in ['top', 'heart', 'base']:
            val = notes_dict.get(key)
            if val:
                if isinstance(val, list):
                    all_notes.extend([n.strip().lower() for n in val])
                elif isinstance(val, str):
                    all_notes.extend([n.strip().lower() for n in val.split(',')])
        return set(all_notes)

    target_note_set = flatten_notes(target_notes)
    if not target_note_set:
        return []

    # Get other items in same category
    potential_clones = Item.query.filter(
        Item.category_id == target_item.category_id,
        Item.id != target_item.id
    ).all()

    clones = []
    target_price = target_item.default_variant.store_links[0].price if target_item.default_variant and target_item.default_variant.store_links else 0

    for item in potential_clones:
        item_notes = item.perfume_notes
        if not item_notes:
            continue
            
        item_note_set = flatten_notes(item_notes)
        if not item_note_set:
            continue

        # Calculate similarity (Jaccard Index)
        intersection = target_note_set.intersection(item_note_set)
        union = target_note_set.union(item_note_set)
        
        if not union:
            continue
            
        similarity = (len(intersection) / len(union)) * 100
        
        # Check price
        item_price = item.default_variant.store_links[0].price if item.default_variant and item.default_variant.store_links else 999999
        
        # If similarity is significant (> 20%) and price is lower or similar
        # (Usually clones are significantly cheaper)
        if similarity > 15 and item_price < target_price:
            clones.append({
                "item": item,
                "score": round(similarity),
                "price_diff": round(float(target_price - item_price), 2)
            })

    # Sort by similarity score
    clones.sort(key=lambda x: x['score'], reverse=True)
    
    return clones[:limit]
