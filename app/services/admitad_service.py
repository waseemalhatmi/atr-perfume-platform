import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from app.extensions import db
from app.models import Store, Item, ItemVariant, ItemStoreLink, FeedSyncLog, Brand, Category
from app.utils.logger import get_logger
from app.utils.resilience import retry, feed_circuit_breaker
from app.utils.normalizers import generate_slug

log = get_logger(__name__)

# --- Smart Filter Keywords ---
PERFUME_KEYWORDS = [
    # English
    'perfume', 'fragrance', 'cologne', 'eau de parfum', 'edp', 'eau de toilette', 'edt', 
    'attar', 'scent', 'mist', 'oud', 'musk', 'essential oil', 'tester', 'parfum',
    # Arabic
    'عطر', 'بخور', 'مسك', 'عود', 'دهن', 'مرش', 'تستر', 'فواحة', 'طيب'
]
RE_PERFUME = re.compile('|'.join(PERFUME_KEYWORDS), re.IGNORECASE)

class AdmitadService:
    """
    Enterprise-grade Service for syncing products from Admitad XML Feeds.
    Supports smart matching, price updates, and automated item creation.
    """

    @staticmethod
    @retry(max_attempts=3, delay=2, backoff=2)
    @feed_circuit_breaker
    def fetch_feed_stream(url: str):
        """
        Fetches XML from URL as a stream to handle massive files.
        """
        log.info("fetching_xml_feed_stream", url=url)
        # Use stream=True to avoid loading everything into RAM
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        return response.raw # Return the raw socket-like stream

    @staticmethod
    def sync_store_feed(store_id):
        """
        ULTRA-FAST STREAMING SYNC
        Handles massive XML feeds (GBs) with constant low memory usage.
        """
        store = db.session.get(Store, store_id)
        if not store or not store.xml_feed_url:
            log.warning("sync_skipped", store_id=store_id, reason="No URL")
            return False, "Store not found or missing feed URL"

        # Initialize Sync Log
        sync_log = FeedSyncLog(
            store_id=store.id, 
            status="running",
            started_at=datetime.utcnow(),
            total_found=0
        )
        db.session.add(sync_log)
        store.sync_status = "running"
        db.session.commit()

        try:
            # --- PHASE 1: PRE-FETCH (Speed Optimization) ---
            # Load all existing external IDs for this store into a memory set
            log.info("pre_fetching_ids", store_id=store.id)
            existing_links = {
                l.external_item_id: l for l in ItemStoreLink.query.filter_by(store_id=store.id).all()
            }
            
            # --- PHASE 2: STREAMING PROCESSING ---
            stream = AdmitadService.fetch_feed_stream(store.xml_feed_url)
            
            new_added = 0
            updated = 0
            deactivated = 0
            processed_count = 0
            found_external_ids = set()

            # iterparse reads the file tag by tag without loading everything into memory
            context = ET.iterparse(stream, events=("end",))
            
            log.info("streaming_parse_started")
            
            for event, elem in context:
                if elem.tag == "offer":
                    processed_count += 1
                    try:
                        name = elem.findtext("name", "").strip()
                        description = elem.findtext("description", "").strip()
                        
                        # 1. SMART FILTER (Early Exit)
                        full_text = f"{name} {description}"
                        if not RE_PERFUME.search(full_text):
                            elem.clear() # Free memory
                            continue
                        
                        ext_id = elem.get("id")
                        found_external_ids.add(ext_id)
                        
                        p_data = {
                            "external_id": ext_id,
                            "name": name,
                            "brand": elem.findtext("vendor", "Generic").strip(),
                            "price": float(elem.findtext("price") or 0),
                            "old_price": float(elem.findtext("oldprice") or 0) if elem.findtext("oldprice") else None,
                            "currency": elem.findtext("currencyId", "USD"),
                            "affiliate_url": elem.findtext("url", ""),
                            "image_url": elem.findtext("picture", ""),
                            "description": description,
                            "availability": "instock" if elem.get("available") == "true" else "outofstock",
                            "ean": elem.findtext("barcode")
                        }

                        # 2. MATCH & UPDATE
                        existing_link = existing_links.get(ext_id)
                        if existing_link:
                            # Update existing
                            if float(existing_link.price or 0) != p_data["price"]:
                                existing_link.old_price = existing_link.price
                                existing_link.price = p_data["price"]
                                updated += 1
                            existing_link.availability = p_data["availability"]
                            existing_link.is_active = (p_data["availability"] == "instock")
                            existing_link.last_checked_at = datetime.utcnow()
                        else:
                            # Search for global item (EAN or Name)
                            item = None
                            if p_data.get("ean"):
                                item = Item.query.filter_by(ean_code=p_data["ean"]).first()
                            if not item:
                                item = Item.query.filter(Item.name.ilike(p_data["name"])).first()
                            
                            if item:
                                AdmitadService._add_link_to_item(item, store, p_data)
                            else:
                                AdmitadService._create_new_item(store, p_data)
                            new_added += 1

                        # Batch Commit every 100 items to save RAM and DB load
                        if (new_added + updated) % 100 == 0:
                            db.session.commit()

                    except Exception as e:
                        log.error("product_processing_error", error=str(e), product_name=name if 'name' in locals() else 'Unknown')
                    
                    # IMPORTANT: Clear the element from memory after processing
                    elem.clear()
            
            # Clear root element memory
            # Note: iterparse doesn't clear previous elements automatically
            # but clearing root helps for long files
            
            # --- PHASE 3: DEACTIVATION & FINAL LOGS ---
            # Deactivate products no longer in the feed
            missing_links = ItemStoreLink.query.filter(
                ItemStoreLink.store_id == store.id,
                ItemStoreLink.source == "auto_feed",
                ItemStoreLink.is_active == True,
                ~ItemStoreLink.external_item_id.in_(found_external_ids)
            ).all()
            
            for m_link in missing_links:
                m_link.is_active = False
                m_link.availability = "outofstock"
                deactivated += 1

            sync_log.new_added = new_added
            sync_log.updated = updated
            sync_log.deactivated = deactivated
            sync_log.total_found = processed_count
            sync_log.status = "success"
            sync_log.finished_at = datetime.utcnow()
            
            store.sync_status = "success"
            store.last_synced_at = datetime.utcnow()
            
            db.session.commit()
            log.info("sync_completed", added=new_added, updated=updated, processed=processed_count)
            return True, f"Sync successful: {new_added} added, {updated} updated."

        except Exception as e:
            db.session.rollback()
            sync_log.status = "error"
            sync_log.error_msg = str(e)
            sync_log.finished_at = datetime.utcnow()
            store.sync_status = "error"
            db.session.commit()
            log.error("sync_failed", error=str(e))
            return False, str(e)

    @staticmethod
    def _add_link_to_item(item, store, p_data):
        """Attaches a new store offer to an existing item's default variant."""
        from app.services.item_service import ensure_default_variant
        variant = ensure_default_variant(item)
        
        new_link = ItemStoreLink(
            variant_id=variant.id,
            store_id=store.id,
            external_item_id=p_data["external_id"],
            affiliate_url=p_data["affiliate_url"],
            price=p_data["price"],
            old_price=p_data["old_price"],
            currency=p_data["currency"] or store.currency or "USD",
            availability=p_data["availability"],
            is_active=(p_data["availability"] == "instock"),
            source="auto_feed",
            imported_at=datetime.utcnow(),
            last_checked_at=datetime.utcnow()
        )
        db.session.add(new_link)

    @staticmethod
    def _create_new_item(store, p_data):
        """Creates a new Item, Brand, ItemImage, and initial StoreLink from feed data."""
        from app.models import ItemImage
        
        # ── Brand Management ────────────────────────────────────────────────
        brand_name = (p_data.get("brand") or "Generic").strip()
        brand = Brand.query.filter(Brand.name.ilike(brand_name)).first()
        if not brand:
            brand = Brand(name=brand_name, slug=generate_slug(brand_name))
            db.session.add(brand)
            db.session.flush()

        # ── Category Management (Default to 'عطور' / Perfumes) ─────────────
        category = Category.query.filter(Category.name.ilike("عطور")).first()
        if not category:
            category = Category(name="عطور", slug="perfumes")
            db.session.add(category)
            db.session.flush()

        # ── Slug — safe & unique per brand ──────────────────────────────────
        base_slug = generate_slug(p_data["name"]) or f"product-{p_data['external_id']}"
        slug = base_slug
        counter = 1
        while Item.query.filter_by(brand_id=brand.id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # ── Create Item ──────────────────────────────────────────────────────
        new_item = Item(
            name=p_data["name"],
            slug=slug,
            description=p_data["description"][:1000] if p_data.get("description") else None,
            brand_id=brand.id,
            category_id=category.id,
            ean_code=p_data.get("ean"),
            item_type="perfume"
        )
        db.session.add(new_item)
        db.session.flush()  # generate new_item.id before adding relations

        # ── Save product image (stored as external URL; Celery will proxy later) ──
        if p_data.get("image_url"):
            img = ItemImage(
                item_id=new_item.id,
                image_path=p_data["image_url"],   # will be proxied to local by nightly task
                alt_text=p_data["name"],
                position=0
            )
            db.session.add(img)

        # ── Add initial store link ───────────────────────────────────────────
        AdmitadService._add_link_to_item(new_item, store, p_data)

