"""
scripts/aliexpress_api_sync.py
══════════════════════════════════════════════════════════════════════════════
Enterprise-grade AliExpress API Sync Runner
- يعمل بالكامل على GitHub Actions (لا يحتاج سيرفر Render)
- يتصل بـ AliExpress API مباشرة ويبحث عن العطور
- يحفظ النتائج مباشرة في قاعدة بيانات Supabase (PostgreSQL)
- يستخدم نظام الأوزان الاحترافي للتأكد من أن المنتج عطر حقيقي
══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import hmac
import hashlib
import logging
import requests
from datetime import datetime, timezone
from urllib.parse import urlencode

# ── 1. Setup ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(__file__))  # لاستيراد iop.py من مجلد scripts
import iop  # ✅ IOP SDK الرسمي موجود في scripts/iop.py

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("aliexpress_sync")

# ── 2. إعدادات AliExpress API ─────────────────────────────────────────────────
ALIEXPRESS_API_URL     = "https://api-sg.aliexpress.com/sync"
ALIEXPRESS_APP_KEY     = os.environ.get("ALIEXPRESS_APP_KEY", "")
ALIEXPRESS_SECRET      = os.environ.get("ALIEXPRESS_APP_SECRET", "")
ALIEXPRESS_TOKEN       = os.environ.get("ALIEXPRESS_ACCESS_TOKEN", "")
ALIEXPRESS_REFRESH_TOKEN = os.environ.get("ALIEXPRESS_REFRESH_TOKEN", "")

# المتغير القابل للتحديث أثناء التشغيل
_active_token: str = ALIEXPRESS_TOKEN

# ── 3. كلمات البحث (يمكنك إضافة أي كلمة) ────────────────────────────────────
PERFUME_KEYWORDS = [
    "perfume",
    "eau de parfum",
    "fragrance",
    "cologne",
    "oud perfume",
    "musk perfume",
    "attar perfume",
]

# ── 4. إعدادات جلب البيانات ───────────────────────────────────────────────────
FETCH_CONFIG = {
    "local":       "en_US",
    "countryCode": "SA",       # شحن إلى المملكة العربية السعودية
    "currency":    "USD",
    "sortBy":      "orders,desc",  # الأكثر مبيعاً أولاً
    "pageSize":    50,             # 50 منتج في كل صفحة
    "maxPages":    10,             # أقصى عدد صفحات لكل كلمة (500 منتج لكل كلمة)
}

# ── 5. نظام الأوزان (نفس المعيار الاحترافي) ──────────────────────────────────
WHITELIST = [
    "perfume", "fragrance", "cologne", "parfum", "scent", "attar", "oud", "musk",
    "eau de parfum", "edp", "eau de toilette", "edt", "extrait", "absolu",
    "concentrated", "vaporisateur", "body mist", "aftershave", "bakhoor",
    "عطر", "بخور", "مسك", "عود", "دهن", "فواحة",
]
BLACKLIST = [
    "lcd", "screen", "fan", "battery", "cable", "phone", "charger", "sensor",
    "machine", "motor", "burner", "stand", "decor", "statue", "shirt", "clothing",
    "shoes", "bag", "watch", "toy", "repair", "replacement", "led", "lamp",
]

def _is_perfume(title: str, category_id: str = "") -> bool:
    """فلترة سريعة: هل المنتج عطر؟"""
    text = title.lower()
    # إذا كانت في القائمة السوداء → رفض فوري
    if any(w in text for w in BLACKLIST):
        return False
    # إذا كانت في القائمة البيضاء → قبول
    if any(w in text for w in WHITELIST):
        return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
# الجزء الأول: الاتصال بـ AliExpress API
# ══════════════════════════════════════════════════════════════════════════════

def _build_signature(params: dict, secret: str) -> str:
    """
    AliExpress Official MD5 Signing Algorithm:
    1. Exclude the 'sign' field itself
    2. Sort all remaining params alphabetically
    3. secret + key1value1key2value2... + secret → MD5 uppercase
    """
    sign_params = {k: v for k, v in params.items() if k != "sign"}
    sorted_params = sorted(sign_params.items())
    sign_string = secret + "".join(f"{k}{v}" for k, v in sorted_params) + secret
    return hashlib.md5(sign_string.encode("utf-8")).hexdigest().upper()


def _refresh_access_token() -> str:
    """
    يجدد Access Token باستخدام Refresh Token.

    الكود الرسمي من صفحة AliExpress Open Platform:
        client  = iop.IopClient(url, appkey, appSecret)
        request = iop.IopRequest('/auth/token/refresh')
        request.add_api_param('refresh_token', REFRESH_TOKEN)
        response = client.execute(request)
    """
    global _active_token

    if not ALIEXPRESS_REFRESH_TOKEN:
        log.warning("⚠️  ALIEXPRESS_REFRESH_TOKEN غير مضبوط — لا يمكن تجديد التوكن تلقائياً.")
        log.warning("   أضف ALIEXPRESS_REFRESH_TOKEN إلى GitHub Secrets لتفعيل التجديد التلقائي.")
        return _active_token

    log.info("🔄 محاولة تجديد Access Token باستخدام IOP SDK الرسمي...")

    try:
        # ✅ بالضبط كما هو موثّق في صفحة AliExpress Developer
        client  = iop.IopClient(
            "https://api-sg.aliexpress.com",
            ALIEXPRESS_APP_KEY,
            ALIEXPRESS_SECRET
        )
        request = iop.IopRequest("/auth/token/refresh")
        request.add_api_param("refresh_token", ALIEXPRESS_REFRESH_TOKEN)

        response = client.execute(request)
        log.info(f"   ↳ IOP Refresh: HTTP {response.http_status} | type={response.type}")
        log.info(f"   ↳ raw: {response.body[:400]}")

        # تحليل الرد
        try:
            data = json.loads(response.body)
        except (json.JSONDecodeError, TypeError):
            log.error("❌ الرد ليس JSON صالح.")
            return _active_token


        # ── AliExpress يُعيد التوكن في مسارات مختلفة حسب الإصدار ──────────────
        new_token = (
            data.get("access_token") or
            data.get("result", {}).get("access_token") or
            data.get("data", {}).get("access_token")
        )
        expires_in = (
            data.get("expire_time") or
            data.get("result", {}).get("expire_time") or
            data.get("expires_in") or
            0
        )

        if new_token:
            _active_token = new_token
            try:
                days_left = int(expires_in) // 86400
            except (TypeError, ValueError):
                days_left = "?"
            log.info(f"✅ تم تجديد التوكن بنجاح! صالح لـ {days_left} يوم.")
            log.info("   ⚡ تذكر: حدّث ALIEXPRESS_ACCESS_TOKEN في GitHub Secrets بالقيمة الجديدة.")
            return new_token

        log.error(f"❌ فشل تجديد التوكن — رد الـ API: {data}")
        if "error_response" in data:
            err = data["error_response"]
            log.error(f"   code={err.get('code')} | msg={err.get('msg')}")
            log.error("   ⚠️  قد يكون الـ Refresh Token نفسه منتهياً (صالح سنة واحدة فقط).")
            log.error("   ⚠️  الحل: احصل على Auth Code جديد وشغّل scripts/get_aliexpress_token.py")

    except ValueError:
        log.error("❌ الرد ليس JSON صالح — الـ endpoint أو الـ Content-Type غير صحيح.")
    except Exception as exc:
        log.error(f"❌ استثناء أثناء تجديد التوكن: {exc}")

    return _active_token


def fetch_products_from_api(keyword: str, page_index: int = 1) -> dict:
    """
    إرسال طلب بحث إلى AliExpress Affiliate API وإرجاع البيانات.
    يستخدم نظام التوقيع الرسمي المدمج في iop.py.
    """
    log.info(f"   📡 Calling AliExpress Affiliate API for: '{keyword}' (Page {page_index})")
    
    try:
        # ✅ استخدام IOP SDK المدمج في المشروع
        client = iop.IopClient(ALIEXPRESS_API_URL, ALIEXPRESS_APP_KEY, ALIEXPRESS_SECRET)
        request = iop.IopRequest('aliexpress.affiliate.product.query')
        
        # إعداد المعلمات حسب طلب المستخدم
        request.add_api_param('keywords', keyword)
        request.add_api_param('page_no', str(page_index))
        request.add_api_param('page_size', str(FETCH_CONFIG["pageSize"]))
        request.add_api_param('platform_product_type', 'ALL')
        request.add_api_param('target_currency', FETCH_CONFIG["currency"])
        request.add_api_param('target_language', 'EN')
        request.add_api_param('ship_to_country', FETCH_CONFIG["countryCode"])
        
        # إذا كان الـ Tracking ID متوفراً
        tracking_id = os.environ.get("ALIEXPRESS_TRACKING_ID", "default_tracking")
        request.add_api_param('tracking_id', tracking_id)

        response = client.execute(request)
        
        if response.type == "error":
            log.error(f"   ❌ API Error Response: {response.body}")
            return {}

        data = json.loads(response.body)
        return data

    except Exception as e:
        log.error(f"   ❌ Exception during API call: {e}")
        return {}


def extract_products(api_response: dict) -> tuple:
    """
    استخراج قائمة المنتجات من استجابة Affiliate API.
    الهيكل: resp_result -> result -> products -> product
    """
    try:
        resp = api_response.get("aliexpress_affiliate_product_query_response", {})
        result_wrapper = resp.get("resp_result", {})
        
        if result_wrapper.get("resp_code") != 200:
            log.warning(f"   ⚠️ API Business Error: {result_wrapper.get('resp_msg')}")
            return [], 0
            
        result_data = result_wrapper.get("result", {})
        products_list = result_data.get("products", {}).get("product", [])
        total_count = result_data.get("total_record_count", 0)
        
        if isinstance(products_list, dict):
            products_list = [products_list]
            
        return products_list, int(total_count)
    except Exception as e:
        log.warning(f"   ⚠️ extract_products error: {e}")
        return [], 0


# ══════════════════════════════════════════════════════════════════════════════
# الجزء الثاني: حفظ البيانات في Supabase مباشرةً
# ══════════════════════════════════════════════════════════════════════════════

def run_api_sync():
    """المهمة الرئيسية: تجمع البيانات من AliExpress وتحفظها في Supabase."""
    global _active_token

    log.info("══════════════════════════════════════════════════")
    log.info("🚀 ALIEXPRESS API SYNC STARTED (GitHub Actions)")
    log.info("══════════════════════════════════════════════════")

    # التحقق من وجود المفاتيح
    if not all([ALIEXPRESS_APP_KEY, ALIEXPRESS_SECRET, ALIEXPRESS_TOKEN]):
        log.error("❌ Missing AliExpress API credentials in environment variables!")
        log.error("   Required: ALIEXPRESS_APP_KEY, ALIEXPRESS_APP_SECRET, ALIEXPRESS_ACCESS_TOKEN")
        sys.exit(1)

    # ── طباعة حالة إعدادات التوكن ─────────────────────────────────────────────
    log.info(f"🔑 Access Token  : {'✅ Set' if ALIEXPRESS_TOKEN else '❌ Missing'}")
    log.info(f"🔄 Refresh Token : {'✅ Set (Auto-Refresh ON)' if ALIEXPRESS_REFRESH_TOKEN else '⚠️  Not Set (Auto-Refresh OFF)'}")
    _active_token = ALIEXPRESS_TOKEN  # تهيئة التوكن النشط

    # ── تهيئة Flask + SQLAlchemy للاتصال بـ Supabase ─────────────────────────
    try:
        from app import create_app
        from app.extensions import db
        from app.models import Store, Item, ItemStoreLink, Brand, Category
        from app.models import ItemImage, ItemVariant
        from app.utils.normalizers import generate_slug
    except ImportError as e:
        log.error(f"❌ Import failed: {e}")
        sys.exit(1)

    app = create_app()

    # ── البحث بكل كلمة مفتاحية ───────────────────────────────────────────────
    all_products_raw = []

    for keyword in PERFUME_KEYWORDS:
        log.info(f"🔍 Searching: '{keyword}'")
        page = 1

        while page <= FETCH_CONFIG["maxPages"]:
            result = fetch_products_from_api(keyword, page)
            products, total = extract_products(result)

            if not products:
                log.info(f"   ↳ No more results for '{keyword}' at page {page}.")
                break

            # فلترة العطور فقط
            filtered = [p for p in products if _is_perfume(p.get("title", ""))]
            all_products_raw.extend(filtered)
            log.info(f"   ↳ Page {page}: {len(products)} found → {len(filtered)} perfumes kept")

            # إذا جلبنا كل المنتجات، لا حاجة للصفحة التالية
            if page * FETCH_CONFIG["pageSize"] >= total:
                break

            page += 1
            time.sleep(0.5)  # تجنب تجاوز حد الطلبات (Rate Limit)

    log.info(f"📦 Total perfumes collected from API: {len(all_products_raw)}")

    if not all_products_raw:
        log.warning("⚠️ No perfumes found. Check API credentials or keywords.")
        return

    # ── حفظ البيانات في Supabase ──────────────────────────────────────────────
    with app.app_context():
        # إيجاد متجر AliExpress في قاعدة البيانات
        store = Store.query.filter(Store.name.ilike("%aliexpress%")).first()
        if not store:
            log.error("❌ AliExpress store not found in database. Add it first from Admin.")
            sys.exit(1)

        added, updated, skipped = 0, 0, 0

        for raw in all_products_raw:
            try:
                ext_id    = str(raw.get("product_id") or "")
                title     = (raw.get("product_title") or "").strip()
                image_url = raw.get("product_main_image_url", "")
                item_url  = raw.get("promotion_link", "")
                
                # تحليل السعر بشكل آمن (Affiliate API يستخدم sale_price)
                try:
                    price = float(str(raw.get("sale_price") or 0).replace(",", "."))
                    old_price = float(str(raw.get("original_price") or 0).replace(",", "."))
                except (ValueError, TypeError):
                    price, old_price = 0.0, 0.0

                if not ext_id or not title or price <= 0:
                    skipped += 1
                    continue

                # ── هل الرابط موجود مسبقاً؟ (Update or Skip) ─────────────
                existing_link = ItemStoreLink.query.filter_by(
                    store_id=store.id,
                    external_item_id=ext_id
                ).first()

                if existing_link:
                    if existing_link.price != price:
                        existing_link.old_price = existing_link.price
                        existing_link.price = price
                        existing_link.last_checked_at = datetime.now(timezone.utc)
                        updated += 1
                    else:
                        skipped += 1
                    continue

                # ── البراند (Generic لأن AliExpress لا يرسل بيانات البراند دائماً) ──
                brand = Brand.query.filter(Brand.name.ilike("Generic")).first()
                if not brand:
                    brand = Brand()
                    brand.name = "Generic"
                    brand.slug = "generic"
                    db.session.add(brand)
                    db.session.flush()

                # ── التصنيف ─────────────────────────────────────────────────
                category = Category.query.filter(Category.name.ilike("عطور")).first()
                if not category:
                    category = Category()
                    category.name = "عطور"
                    category.slug = "perfumes"
                    db.session.add(category)
                    db.session.flush()

                # ── هل المنتج موجود بالاسم؟ ─────────────────────────────────
                item = Item.query.filter(Item.name.ilike(title)).first()

                if not item:
                    # إنشاء slug فريد
                    base_slug = generate_slug(title) or f"product-{ext_id}"
                    slug = base_slug
                    counter = 1
                    while Item.query.filter_by(slug=slug).first():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    # إنشاء المنتج
                    item = Item()
                    item.name        = title
                    item.slug        = slug
                    item.brand_id    = brand.id
                    item.category_id = category.id
                    item.item_type   = "perfume"
                    db.session.add(item)
                    db.session.flush()

                    # حفظ الصورة
                    if image_url:
                        img = ItemImage()
                        img.item_id    = item.id
                        img.image_path = image_url
                        img.alt_text   = title
                        img.position   = 0
                        db.session.add(img)

                # ── إنشاء Variant افتراضي إذا لم يوجد ───────────────────────
                variant = ItemVariant.query.filter_by(item_id=item.id).first()
                if not variant:
                    variant = ItemVariant()
                    variant.item_id = item.id
                    variant.name    = "Default"
                    variant.sku     = f"AE-{ext_id}"
                    db.session.add(variant)
                    db.session.flush()

                # ── إنشاء رابط المتجر ─────────────────────────────────────
                link = ItemStoreLink()
                link.variant_id       = variant.id
                link.store_id         = store.id
                link.external_item_id = ext_id
                link.affiliate_url    = item_url
                link.price            = price
                link.old_price        = old_price if old_price > price else None
                link.currency         = "USD"
                link.availability     = "instock"
                link.is_active        = True
                link.source           = "aliexpress_api"
                link.imported_at      = datetime.now(timezone.utc)
                link.last_checked_at  = datetime.now(timezone.utc)
                db.session.add(link)

                added += 1

                # Commit كل 50 منتج
                if (added + updated) % 50 == 0:
                    db.session.commit()
                    log.info(f"   💾 Batch saved: {added} added, {updated} updated so far...")

            except Exception as e:
                db.session.rollback()
                log.error(f"⚠️  Error processing product '{ext_id}': {e}")
                continue

        # الحفظ النهائي
        db.session.commit()

    log.info("══════════════════════════════════════════════════")
    log.info("🏁 ALIEXPRESS API SYNC COMPLETED")
    log.info(f"   ✅ Added:   {added}")
    log.info(f"   🔄 Updated: {updated}")
    log.info(f"   ⏭️  Skipped: {skipped}")
    log.info("══════════════════════════════════════════════════")


if __name__ == "__main__":
    run_api_sync()
