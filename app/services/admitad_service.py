import re
import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from app.extensions import db
from app.models import Store, Item, ItemVariant, ItemStoreLink, FeedSyncLog, Brand, Category
from app.utils.logger import get_logger
from app.utils.resilience import retry, feed_circuit_breaker
from app.utils.normalizers import generate_slug

log = get_logger(__name__)

# --- 🌟 القاموس العطري الاحترافي (Whitelist) 🌟 ---
WHITELIST_PERFUME = [
    'perfume', 'fragrance', 'cologne', 'parfum', 'scent', 'attar', 'oud', 'musk',
    'eau de parfum', 'edp', 'eau de toilette', 'edt', 'extrait de parfum', 'absolu',
    'concentrated', 'intense', 'vaporisateur', 'natural spray',
    'body mist', 'body spray', 'fragrance oil', 'essential oil', 'aftershave',
    'incense', 'bakhoor', 'frankincense', 'resin', 'perfume oil',
    'عطر', 'بخور', 'مسك', 'عود', 'دهن', 'مرش', 'فواحة', 'طيب', 'تستر عطر'
]

# --- 🚫 قائمة الممنوعات الشاملة (Blacklist) 🚫 ---
BLACKLIST_ITEMS = [
    'lcd', 'screen', 'fan', 'refrigerator', 'battery', 'voltage', 'car', 'automobile', 
    'electronics', 'tool', 'meter', 'cable', 'adapter', 'phone', 'charger', 'module', 
    'relay', 'sensor', 'board', 'circuit', 'vacuum', 'machine', 'motor', 'tester tool',
    'humidifier', 'diffuser machine', 'dispenser', 'intelligent', 'thermostatic',
    'burner', 'holder', 'stand', 'rack', 'vase', 'pot', 'kettle', 'decor', 'ornament', 
    'statue', 'sculpture', 'handmade', 'wooden', 'metal', 'ceramic', 'glass', 'frame', 
    'poster', 'sticker', 'hook', 'base', 'tray', 'box only', 'empty bottle',
    't-shirt', 'shirt', 'clothing', 'shoes', 'pants', 'jacket', 'hat', 'bag', 'wallet', 
    'watch', 'jewelry', 'toy', 'doll', 'vest', 'knitted', 'floral print', 'floral pattern',
    'case for', 'cover for', 'kit for', 'replacement', 'repair', 'part', 'connector', 
    'plug', 'switch', 'socket', 'bulb', 'led', 'lamp', 'tempered glass'
]

RE_VOLUME = re.compile(r'\d+\s*(ml|مل|oz|أوز|ounce)', re.IGNORECASE)

# --- 🎯 نظام الأوزان الاحترافي (Weight System) 🎯 ---
WEIGHTS = {
    "critical_positive": ["eau de parfum", "edp", "eau de toilette", "edt", "extrait de parfum", "عطر", "بخور", "parfum"],
    "strong_positive": ["perfume", "fragrance", "cologne", "oud", "musk", "دهن", "مسك", "عود", "tester", "تستر"],
    "medium_positive": ["scent", "attar", "spray", "vaporisateur", "طيب", "مرش"],
    "negative": BLACKLIST_ITEMS
}

# قيم النقاط (موحدة ومركزية)
SCORE_VALUES = {
    "critical_positive": 25,
    "strong_positive": 15,
    "medium_positive": 5,
    "category_boost": 20,
    "volume_boost": 20,
    "blacklist_penalty": -100,
    "minimum_score": 20
}

class AdmitadService:
    """
    Enterprise-grade Service for syncing products from Admitad XML Feeds.
    Supports smart matching, weighted scoring, and resilient processing.
    """

    @staticmethod
    @retry(max_attempts=3, delay=2, backoff=2)
    @feed_circuit_breaker
    def fetch_feed_stream(url: str):
        """Fetches XML from URL as a stream."""
        log.info("fetching_xml_feed_stream", url=url)
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        return response.raw

    @staticmethod
    def _calculate_product_score(name, description, category_text):
        """حساب نقاط المنتج بناءً على نظام الأوزان الاحترافي."""
        full_text = f"{name} {description} {category_text}".lower()
        score = 0
        details = {"matched_keywords": [], "blacklisted": False}

        # 0. فحص التصنيف
        if any(w in category_text.lower() for w in ["perfume", "fragrance", "عطر", "جمال", "beauty"]):
            score += SCORE_VALUES["category_boost"]
            details["matched_keywords"].append("category_match")

        # 1. فحص الكلمات المفتاحية
        for word in WEIGHTS["critical_positive"]:
            if word in full_text: 
                score += SCORE_VALUES["critical_positive"]
                details["matched_keywords"].append(word)
        
        for word in WEIGHTS["strong_positive"]:
            if word in full_text: 
                score += SCORE_VALUES["strong_positive"]
                details["matched_keywords"].append(word)
                
        for word in WEIGHTS["medium_positive"]:
            if word in full_text: 
                score += SCORE_VALUES["medium_positive"]
                details["matched_keywords"].append(word)

        # 2. فحص الحجم
        if RE_VOLUME.search(full_text):
            score += SCORE_VALUES["volume_boost"]
            details["matched_keywords"].append("volume_detected")
            
        # 3. الخصم للممنوعات
        for word in WEIGHTS["negative"]:
            if word in full_text:
                score += SCORE_VALUES["blacklist_penalty"]
                details["blacklisted"] = True
                break
        
        return score, details

    @staticmethod
    def sync_store_feed(store_id):
        """ULTRA-FAST STREAMING SYNC with professional filtering."""
        store = db.session.get(Store, store_id)
        if not store or not store.xml_feed_url:
            log.warning("sync_skipped", store_id=store_id, reason="No URL")
            return False, "Store not found or missing feed URL"

        # Initialize Sync Log (Safe Method)
        sync_log = FeedSyncLog()
        sync_log.store_id = store.id
        sync_log.status = "running"
        sync_log.started_at = datetime.now(timezone.utc)
        sync_log.total_found = 0
        db.session.add(sync_log)
        store.sync_status = "running"
        db.session.commit()

        try:
            # --- PHASE 0: CLEANUP ---
            log.info("cleaning_old_data", store_id=store.id)
            ItemStoreLink.query.filter_by(store_id=store.id).delete()
            orphans = Item.query.filter(~Item.variants.any()).all()
            for o in orphans: db.session.delete(o)
            db.session.commit()

            # --- PHASE 1: PRE-FETCH ---
            existing_links = {
                l.external_item_id: l for l in ItemStoreLink.query.filter_by(store_id=store.id).all()
            }
            
            # --- PHASE 2: STREAMING PROCESSING ---
            response = requests.get(store.xml_feed_url, timeout=120, stream=True)
            response.raise_for_status()
            raw_stream = response.raw
            
            # Robust GZIP Detection (Peek magic bytes)
            try:
                peek = raw_stream.peek(2)
                is_gzipped = peek.startswith(b'\x1f\x8b') or store.xml_feed_url.endswith('.gz') or response.headers.get('Content-Encoding') == 'gzip'
            except:
                is_gzipped = store.xml_feed_url.endswith('.gz') or response.headers.get('Content-Encoding') == 'gzip'

            if is_gzipped:
                log.info("decompressing_gzip_stream")
                stream = gzip.GzipFile(fileobj=raw_stream)
            else:
                stream = raw_stream

            new_added, updated, deactivated, processed_count, filtered_out = 0, 0, 0, 0, 0
            found_external_ids = set()

            try:
                context = ET.iterparse(stream, events=("end",))
                log.info("streaming_parse_started")
                
                for event, elem in context:
                    tag_name = elem.tag.split('}')[-1]
                    
                    if tag_name in ("offer", "product", "item"):
                        processed_count += 1
                        try:
                            name = (elem.findtext("name") or elem.findtext("title") or "").strip()
                            description = elem.findtext("description", "").strip()
                            category_text = elem.findtext("category", "") or elem.findtext("categoryId", "")
                            
                            # --- Professional Scoring ---
                            score, details = AdmitadService._calculate_product_score(name, description, category_text)
                            
                            is_match = score >= SCORE_VALUES["minimum_score"]
                            if not is_match or not name:
                                filtered_out += 1
                                if filtered_out % 500 == 0:
                                    log.debug("item_filtered", name=name[:30], score=score)
                                continue
                            
                            ext_id = elem.get("id")
                            found_external_ids.add(ext_id)
                            
                            try:
                                raw_price = elem.findtext("price") or "0"
                                price = float(raw_price.replace(',', '.'))
                            except:
                                price = 0.0

                            p_data = {
                                "external_id": ext_id,
                                "name": name,
                                "brand": elem.findtext("vendor", "Generic").strip(),
                                "price": price,
                                "old_price": float(elem.findtext("oldprice") or 0) if elem.findtext("oldprice") else None,
                                "currency": elem.findtext("currencyId", "USD"),
                                "affiliate_url": elem.findtext("url", ""),
                                "image_url": elem.findtext("picture", ""),
                                "description": description,
                                "availability": "instock" if elem.get("available") == "true" else "outofstock",
                                "ean": elem.findtext("barcode")
                            }

                            if p_data["price"] <= 0: continue

                            existing_link = existing_links.get(ext_id)
                            if existing_link:
                                if float(existing_link.price or 0) != p_data["price"]:
                                    existing_link.old_price = existing_link.price
                                    existing_link.price = p_data["price"]
                                    updated += 1
                                existing_link.availability = p_data["availability"]
                                existing_link.is_active = (p_data["availability"] == "instock")
                                existing_link.last_checked_at = datetime.now(timezone.utc)
                            else:
                                item = None
                                if p_data.get("ean"):
                                    item = Item.query.filter_by(ean_code=p_data["ean"]).first()
                                if not item:
                                    item = Item.query.filter(Item.name.ilike(p_data["name"])).first()
                                
                                if item: AdmitadService._add_link_to_item(item, store, p_data)
                                else: AdmitadService._create_new_item(store, p_data)
                                new_added += 1

                            if (new_added + updated) % 100 == 0:
                                try: db.session.commit()
                                except: db.session.rollback()

                        except Exception as e:
                            db.session.rollback()
                            log.error("product_processing_error", error=str(e))
                        
                        finally:
                            elem.clear()

            except ET.ParseError as e:
                log.error("xml_parse_critical_error", error=str(e))
            
            # --- PHASE 3: DEACTIVATION ---
            missing_links = ItemStoreLink.query.filter(
                ItemStoreLink.store_id == store.id,
                ItemStoreLink.source == "auto_feed",
                ItemStoreLink.is_active == True,
                ~ItemStoreLink.external_item_id.in_(found_external_ids)
            ).all()
            
            for m_link in missing_links:
                m_link.is_active, m_link.availability = False, "outofstock"
                deactivated += 1

            sync_log.new_added, sync_log.updated = new_added, updated
            sync_log.deactivated, sync_log.total_found = deactivated, processed_count
            sync_log.status, sync_log.finished_at = "success", datetime.now(timezone.utc)
            
            store.sync_status, store.last_synced_at = "success", datetime.now(timezone.utc)
            db.session.commit()
            
            log.info("sync_completed", added=new_added, filtered=filtered_out)
            return True, f"Sync successful: {new_added} added, {filtered_out} filtered out."

        except Exception as e:
            db.session.rollback()
            sync_log.status, sync_log.error_msg = "error", str(e)
            sync_log.finished_at = datetime.now(timezone.utc)
            store.sync_status = "error"
            db.session.commit()
            return False, str(e)

    @staticmethod
    def _add_link_to_item(item, store, p_data):
        from app.services.item_service import ensure_default_variant
        variant = ensure_default_variant(item)
        new_link = ItemStoreLink()
        new_link.variant_id, new_link.store_id = variant.id, store.id
        new_link.external_item_id, new_link.affiliate_url = p_data["external_id"], p_data["affiliate_url"]
        new_link.price, new_link.old_price = p_data["price"], p_data["old_price"]
        new_link.currency = p_data["currency"] or store.currency or "USD"
        new_link.availability, new_link.is_active = p_data["availability"], (p_data["availability"] == "instock")
        new_link.source, new_link.imported_at = "auto_feed", datetime.now(timezone.utc)
        new_link.last_checked_at = datetime.now(timezone.utc)
        db.session.add(new_link)

    @staticmethod
    def _create_new_item(store, p_data):
        from app.models import ItemImage
        brand_name = (p_data.get("brand") or "Generic").strip()
        brand = Brand.query.filter(Brand.name.ilike(brand_name)).first()
        if not brand:
            brand = Brand()
            brand.name, brand.slug = brand_name, generate_slug(brand_name)
            db.session.add(brand); db.session.flush()

        category = Category.query.filter(Category.name.ilike("عطور")).first()
        if not category:
            category = Category()
            category.name, category.slug = "عطور", "perfumes"
            db.session.add(category); db.session.flush()

        base_slug = generate_slug(p_data["name"]) or f"product-{p_data['external_id']}"
        slug, counter = base_slug, 1
        while Item.query.filter_by(brand_id=brand.id, slug=slug).first():
            slug, counter = f"{base_slug}-{counter}", counter + 1

        new_item = Item()
        new_item.name, new_item.slug = p_data["name"], slug
        new_item.description = p_data["description"][:1000] if p_data.get("description") else None
        new_item.brand_id, new_item.category_id = brand.id, category.id
        new_item.ean_code, new_item.item_type = p_data.get("ean"), "perfume"
        db.session.add(new_item); db.session.flush()

        if p_data.get("image_url"):
            img = ItemImage()
            img.item_id, img.image_path = new_item.id, p_data["image_url"]
            img.alt_text, img.position = p_data["name"], 0
            db.session.add(img)

        AdmitadService._add_link_to_item(new_item, store, p_data)
