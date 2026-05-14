import os
import json
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.catalog import Store, Item, ItemVariant, ItemStoreLink, Brand, Category, ItemImage
from app.utils.logger import get_logger
from app.utils.normalizers import generate_slug
from .admitad_service import AdmitadService, SCORE_VALUES

from app.utils import iop

log = get_logger(__name__)

class AliExpressService:
    """
    Professional service for syncing products from AliExpress Affiliate API.
    Integrates with the project's existing catalog and scoring system.
    """

    @staticmethod
    def sync_products(keywords='perfume', page_size=50):
        """
        Main sync function: Fetches from API and upserts into DB.
        """
        config = current_app.config
        url = config.get("ALIEXPRESS_API_URL")
        app_key = config.get("ALIEXPRESS_APP_KEY")
        app_secret = config.get("ALIEXPRESS_APP_SECRET")
        tracking_id = config.get("ALIEXPRESS_TRACKING_ID")

        if not all([url, app_key, app_secret]):
            log.warning("aliexpress_sync_skipped", reason="Missing API credentials in config")
            return False, "Missing API credentials"

        # 1. Get or Create AliExpress Store in DB
        store = Store.query.filter_by(slug='aliexpress').first()
        if not store:
            store = Store()
            store.name = "AliExpress"
            store.slug = "aliexpress"
            store.website = "https://www.aliexpress.com"
            store.affiliate_network = "AliExpress Portals"
            store.is_auto_sync = True
            db.session.add(store)
            db.session.commit()

        client = iop.IopClient(url, app_key, app_secret)
        request = iop.IopRequest('aliexpress.affiliate.product.query')
        
        # Set parameters
        request.add_api_param('keywords', keywords)
        request.add_api_param('page_no', str(1)) # Starting from page 1
        request.add_api_param('page_size', str(page_size))
        request.add_api_param('platform_product_type', 'ALL')
        request.add_api_param('ship_to_country', 'US')
        request.add_api_param('target_currency', 'USD')
        request.add_api_param('target_language', 'EN')
        
        if tracking_id:
            request.add_api_param('tracking_id', tracking_id)
        
        try:
            log.info("aliexpress_api_request", keywords=keywords)
            response = client.execute(request)
            
            if response.type == "ISP": # Based on iop.py error handling
                log.error("aliexpress_api_error", body=response.body)
                return False, "API Error"

            # Parse result
            data = json.loads(response.body)
            resp_result = data.get('aliexpress_affiliate_product_query_response', {}).get('resp_result', {})
            
            if resp_result.get('resp_code') != 200:
                log.error("aliexpress_business_error", code=resp_result.get('resp_code'), msg=resp_result.get('resp_msg'))
                return False, resp_result.get('resp_msg')

            products_data = resp_result.get('result', {}).get('products', {}).get('product', [])
            if not isinstance(products_data, list):
                products_data = [products_data] if products_data else []

            log.info("aliexpress_products_received", count=len(products_data))

            new_count = 0
            update_count = 0
            filtered_count = 0

            for p in products_data:
                title = p.get('product_title', '')
                desc = p.get('product_detail_url', '')
                
                score, details = AdmitadService._calculate_product_score(title, desc, "AliExpress")
                
                if score < SCORE_VALUES["minimum_score"]:
                    filtered_count += 1
                    continue

                ext_id = str(p.get('product_id'))
                price = float(p.get('sale_price') or 0)
                
                p_data = {
                    "external_id": ext_id,
                    "name": title,
                    "brand": "AliExpress Seller",
                    "price": price,
                    "currency": p.get('target_sale_price_currency', 'USD'),
                    "affiliate_url": p.get('promotion_link'),
                    "image_url": p.get('product_main_image_url'),
                    "description": title,
                    "availability": "instock"
                }

                existing_link = ItemStoreLink.query.filter_by(store_id=store.id, external_item_id=ext_id).first()
                
                if existing_link:
                    if float(existing_link.price or 0) != p_data["price"]:
                        existing_link.old_price = existing_link.price
                        existing_link.price = p_data["price"]
                        update_count += 1
                    existing_link.last_checked_at = datetime.now(timezone.utc)
                    existing_link.is_active = True
                else:
                    item = Item.query.filter(Item.name.ilike(p_data["name"])).first()
                    if item:
                        AliExpressService._add_link_to_item(item, store, p_data)
                    else:
                        AliExpressService._create_new_item(store, p_data)
                    new_count += 1

            db.session.commit()
            log.info("aliexpress_sync_complete", new=new_count, updated=update_count, filtered=filtered_count)
            return True, f"Successfully synced {new_count} new products and updated {update_count}."

        except Exception as e:
            db.session.rollback()
            log.error("aliexpress_sync_exception", error=str(e))
            return False, str(e)

    @staticmethod
    def _add_link_to_item(item, store, p_data):
        from app.services.item_service import ensure_default_variant
        variant = ensure_default_variant(item)
        
        new_link = ItemStoreLink()
        new_link.variant_id = variant.id
        new_link.store_id = store.id
        new_link.external_item_id = p_data["external_id"]
        new_link.affiliate_url = p_data["affiliate_url"]
        new_link.price = p_data["price"]
        new_link.currency = p_data["currency"]
        new_link.availability = p_data["availability"]
        new_link.is_active = True
        new_link.source = "auto_feed"
        new_link.imported_at = datetime.now(timezone.utc)
        new_link.last_checked_at = datetime.now(timezone.utc)
        db.session.add(new_link)

    @staticmethod
    def _create_new_item(store, p_data):
        brand_name = p_data["brand"]
        brand = Brand.query.filter(Brand.name.ilike(brand_name)).first()
        if not brand:
            brand = Brand()
            brand.name = brand_name
            brand.slug = generate_slug(brand_name)
            db.session.add(brand)
            db.session.flush()

        category = Category.query.filter(Category.name.ilike("عطور")).first()
        if not category:
            category = Category()
            category.name = "عطور"
            category.slug = "perfumes"
            db.session.add(category)
            db.session.flush()

        base_slug = generate_slug(p_data["name"]) or f"ali-{p_data['external_id']}"
        slug, counter = base_slug, 1
        while Item.query.filter_by(brand_id=brand.id, slug=slug).first():
            slug, counter = f"{base_slug}-{counter}", counter + 1

        new_item = Item()
        new_item.name = p_data["name"]
        new_item.slug = slug
        new_item.description = p_data["description"][:1000] if p_data.get("description") else None
        new_item.brand_id = brand.id
        new_item.category_id = category.id
        new_item.item_type = "perfume"
        db.session.add(new_item)
        db.session.flush()

        if p_data.get("image_url"):
            img = ItemImage()
            img.item_id = new_item.id
            img.image_path = p_data["image_url"]
            img.alt_text = p_data["name"]
            img.position = 0
            db.session.add(img)

        AliExpressService._add_link_to_item(new_item, store, p_data)
