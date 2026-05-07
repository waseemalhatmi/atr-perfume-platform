import re
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
    def fetch_feed(url: str) -> str:
        """
        Fetches XML from URL with retry logic and circuit breaker.
        Increased timeout to 60s for large files.
        """
        log.info("fetching_xml_feed", url=url)
        # Use a longer timeout for large feeds (60 seconds)
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # We read the content in chunks if it's very large, but for now text is okay
        return response.text

    @staticmethod
    def parse_xml(content):
        """
        Parses Admitad XML into a list of clean dictionaries.
        Includes a high-speed 'Smart Filter' to keep only perfume-related items.
        """
        products = []
        try:
            root = ET.fromstring(content)
            offers = root.findall(".//offer")
            
            log.info("parsing_xml_started", total_offers=len(offers))
            
            for offer in offers:
                try:
                    name = offer.findtext("name", "").strip()
                    description = offer.findtext("description", "").strip()
                    
                    # --- SMART FILTER: High-Speed Regex Check ---
                    full_text = f"{name} {description}"
                    if not RE_PERFUME.search(full_text):
                        continue # Skip non-perfume items fast
                        
                    product = {
                        "external_id":  offer.get("id"),
                        "name":         name,
                        "brand":        offer.findtext("vendor", "Generic").strip(),
                        "price":        float(offer.findtext("price") or 0),
                        "old_price":    float(offer.findtext("oldprice") or 0) if offer.findtext("oldprice") else None,
                        "currency":     offer.findtext("currencyId", "USD"),
                        "affiliate_url": offer.findtext("url", ""),
                        "image_url":     offer.findtext("picture", ""),
                        "description":   description,
                        "availability":  "instock" if offer.get("available") == "true" else "outofstock",
                        "ean":           offer.findtext("barcode")
                    }
                    if product["name"] and product["external_id"]:
                        products.append(product)
                except (ValueError, TypeError):
                    continue
            
            log.info("parsing_xml_completed", filtered_count=len(products))
                    
        except ET.ParseError as e:
            log.error("xml_parsing_error", error=str(e))
        
        return products

    @staticmethod
    def sync_store_feed(store_id):
        """
        Orchestrates the full sync process for a specific store.
        1. Fetch & Parse
        2. Match & Sync
        3. Log Results
        """
        store = db.session.get(Store, store_id)
        if not store or not store.xml_feed_url:
            log.warning("sync_skipped", store_id=store_id, reason="No URL")
            return False, "Store not found or missing feed URL"

        # Initialize Sync Log
        sync_log = FeedSyncLog(
            store_id=store.id, 
            status="running",
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        
        store.sync_status = "running"
        db.session.commit()

        try:
            # Step 1: Data Acquisition
            raw_content = AdmitadService.fetch_feed(store.xml_feed_url)
            products = AdmitadService.parse_xml(raw_content)
            
            sync_log.total_found = len(products)
            db.session.flush()

            new_added = 0
            updated = 0
            deactivated = 0

            # Step 2: Intelligent Batch Syncing
            # Optimization: Load all existing links for this store into memory at once
            existing_links = {
                l.external_item_id: l for l in ItemStoreLink.query.filter_by(store_id=store.id).all()
            }
            
            found_external_ids = set()
            for p in products:
                found_external_ids.add(p["external_id"])
                
                # Logic 1: High-Speed Memory Match
                existing_link = existing_links.get(p["external_id"])

                if existing_link:
                    # Fast Price Tracking
                    p_price = float(p["price"])
                    if float(existing_link.price or 0) != p_price:
                        existing_link.old_price = existing_link.price
                        existing_link.price = p_price
                        updated += 1
                    
                    existing_link.availability = p["availability"]
                    existing_link.is_active = (p["availability"] == "instock")
                    existing_link.last_checked_at = datetime.utcnow()
                    continue

                # Logic 2: Match by EAN Code (Database lookup only if not matched by ID)
                item = None
                if p.get("ean"):
                    item = Item.query.filter_by(ean_code=p["ean"]).first()

                # Logic 3: Exact Name Match
                if not item:
                    item = Item.query.filter(Item.name.ilike(p["name"])).first()

                if item:
                    AdmitadService._add_link_to_item(item, store, p)
                    new_added += 1
                else:
                    AdmitadService._create_new_item(store, p)
                    new_added += 1
                
                # Periodic Commit to keep memory usage low
                if (new_added + updated) % 100 == 0:
                    db.session.commit()

            # Logic 5: Deactivate missing products
            # Products that are in DB for this store but NOT in the current XML
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

            # Step 3: Success Completion
            sync_log.new_added = new_added
            sync_log.updated = updated
            sync_log.deactivated = deactivated
            sync_log.status = "success"
            sync_log.finished_at = datetime.utcnow()
            
            store.sync_status = "success"
            store.last_synced_at = datetime.utcnow()
            
            db.session.commit()
            log.info("sync_completed", store_id=store_id, added=new_added, updated=updated)
            return True, f"Sync successful: {new_added} added, {updated} updated."

        except Exception as e:
            db.session.rollback()
            sync_log.status = "error"
            sync_log.error_msg = str(e)
            sync_log.finished_at = datetime.utcnow()
            
            store.sync_status = "error"
            db.session.commit()
            
            log.error("sync_execution_failed", store_id=store_id, error=str(e))
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

