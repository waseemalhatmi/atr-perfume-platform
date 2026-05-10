"""
scripts/aliexpress_scraper.py
══════════════════════════════════════════════════════════════════════════════
AliExpress Web Scraper — يعمل بجانب aliexpress_api_sync.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• لا يحتاج API Key أو Access Token
• يستخدم Playwright لمحاكاة المتصفح وسحب العطور من AliExpress
• يخزن البيانات في نفس قاعدة Supabase بنفس models الموجودة
• يتحقق من external_item_id لتجنب التكرار مع سكربت الـ API
• مصدر البيانات: 'aliexpress_scraper' (مختلف عن 'aliexpress_api')
══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import re
import time
import logging
import random
from datetime import datetime, timezone
from typing import Optional

# ── 1. إعداد المسارات ─────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# ── 2. إعداد اللوغ ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("aliexpress_scraper")

# ── 3. التحقق من وجود Playwright ──────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    log.error("❌ Playwright غير مثبت!")
    log.error("   شغّل: pip install playwright && playwright install chromium")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# ── 4. إعدادات السكربت ───────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# كلمات البحث — تتوافق مع aliexpress_api_sync.py
PERFUME_KEYWORDS = [
    "perfume",
    "eau de parfum",
    "fragrance",
    "cologne",
    "oud perfume",
    "musk perfume",
    "attar perfume",
]

# إعدادات الجلب
SCRAPE_CONFIG = {
    "max_pages_per_keyword": 5,   # 5 صفحات × ~60 منتج = ~300 منتج/كلمة
    "delay_between_pages": (2, 5),  # ثانية عشوائية بين الصفحات (anti-ban)
    "delay_between_keywords": (5, 10),
    "headless": True,              # True = بدون واجهة (للسيرفر)
    "timeout_ms": 30_000,          # 30 ثانية للانتظار
}

# فلترة العطور
WHITELIST = [
    "perfume", "fragrance", "cologne", "parfum", "scent", "attar", "oud", "musk",
    "eau de parfum", "edp", "eau de toilette", "edt", "extrait", "absolu",
    "concentrated", "body mist", "aftershave", "bakhoor",
    "عطر", "بخور", "مسك", "عود", "دهن",
]
BLACKLIST = [
    "lcd", "screen", "fan", "battery", "cable", "phone", "charger", "sensor",
    "machine", "motor", "burner", "stand", "decor", "statue", "shirt", "clothing",
    "shoes", "bag", "watch", "toy", "repair", "replacement", "led", "lamp",
    "case", "cover", "adapter", "usb", "wireless", "speaker", "camera",
]


def _is_perfume(title: str) -> bool:
    """فلترة دقيقة: هل المنتج عطر؟ — نفس المنطق في aliexpress_api_sync.py"""
    if not title:
        return False
    text = title.lower()
    if any(w in text for w in BLACKLIST):
        return False
    return any(w in text for w in WHITELIST)


def _parse_price(raw: str) -> Optional[float]:
    """استخراج السعر من نص مثل: US $12.50 → 12.50"""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", raw.replace(",", "."))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _extract_product_id(url: str) -> Optional[str]:
    """استخراج item_id من رابط AliExpress"""
    if not url:
        return None
    # مثال: https://www.aliexpress.com/item/1234567890.html
    match = re.search(r"/item/(\d+)", url)
    if match:
        return match.group(1)
    # مثال: item_id=1234567890
    match = re.search(r"item_id=(\d+)", url)
    return match.group(1) if match else None


# ══════════════════════════════════════════════════════════════════════════════
# ── 5. محرك الكشط (Playwright Engine) ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _random_delay(range_tuple: tuple):
    """انتظار عشوائي لتجنب الحظر"""
    t = random.uniform(*range_tuple)
    log.debug(f"   ⏳ Waiting {t:.1f}s...")
    time.sleep(t)


def scrape_keyword(browser, keyword: str) -> list[dict]:
    """
    يبحث عن كلمة مفتاحية في AliExpress ويرجع قائمة المنتجات المُصفّاة.
    يستخدم نفس المتصفح (browser) لتجنب إعادة الفتح في كل كلمة.
    """
    collected = []
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        viewport={"width": 1366, "height": 768},
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    try:
        page = context.new_page()

        for page_num in range(1, SCRAPE_CONFIG["max_pages_per_keyword"] + 1):
            url = (
                f"https://www.aliexpress.com/wholesale"
                f"?SearchText={keyword.replace(' ', '+')}"
                f"&page={page_num}"
                f"&SortType=total_tranpro_desc"  # الأكثر مبيعاً أولاً
            )

            log.info(f"   📄 Page {page_num}: {url[:80]}...")

            try:
                page.goto(url, wait_until="domcontentloaded",
                          timeout=SCRAPE_CONFIG["timeout_ms"])
                # انتظر تحميل بطاقات المنتجات
                page.wait_for_selector(
                    "[class*='product-item'], [class*='list--gallery'],"
                    " a[href*='/item/']",
                    timeout=SCRAPE_CONFIG["timeout_ms"],
                )
            except PlaywrightTimeout:
                log.warning(f"   ⚠️  Timeout on page {page_num} — skipping.")
                break

            # ── استخراج بطاقات المنتجات ─────────────────────────────────────
            products_on_page = page.evaluate("""
                () => {
                    const results = [];
                    // محاولة أولى: بطاقات النتائج الحديثة
                    const cards = document.querySelectorAll(
                        'a[href*="/item/"]'
                    );
                    const seen = new Set();

                    cards.forEach(a => {
                        const href = a.href || '';
                        const idMatch = href.match(/\\/item\\/(\\d+)/);
                        if (!idMatch) return;
                        const itemId = idMatch[1];
                        if (seen.has(itemId)) return;
                        seen.add(itemId);

                        // ── محاولة استخراج العنوان ──
                        const card = a.closest(
                            '[class*="item"], [class*="product"], ' +
                            '[class*="card"], [class*="tile"]'
                        ) || a.parentElement;

                        const titleEl = card
                            ? card.querySelector(
                                '[class*="title"], h3, span[title], ' +
                                '[class*="name"]'
                              )
                            : null;
                        const title = titleEl
                            ? (titleEl.textContent || titleEl.title || '').trim()
                            : (a.title || a.textContent || '').trim();

                        // ── محاولة استخراج السعر ──
                        const priceEl = card
                            ? card.querySelector(
                                '[class*="price--current"], ' +
                                '[class*="sale-price"], ' +
                                '[class*="price"]'
                              )
                            : null;
                        const priceText = priceEl
                            ? (priceEl.textContent || '').trim()
                            : '';

                        // ── محاولة استخراج الصورة ──
                        const imgEl = card
                            ? card.querySelector('img[src], img[data-src]')
                            : null;
                        const img = imgEl
                            ? (imgEl.src || imgEl.dataset.src || '')
                            : '';

                        if (title && title.length > 5) {
                            results.push({
                                item_id: itemId,
                                title: title.substring(0, 200),
                                price_text: priceText,
                                image_url: img.startsWith('http') ? img : '',
                                item_url: href,
                            });
                        }
                    });
                    return results;
                }
            """)

            if not products_on_page:
                log.info(f"   ↳ No products found on page {page_num}. Stopping.")
                break

            # فلترة العطور فقط
            perfumes = [p for p in products_on_page if _is_perfume(p["title"])]

            # تحليل السعر
            for p in perfumes:
                p["price"] = _parse_price(p.get("price_text", ""))

            # تصفية المنتجات بدون سعر (اختياري — تُحفظ بسعر 0 إذا أردت)
            perfumes_valid = [
                p for p in perfumes
                if p.get("item_id") and p.get("title") and p.get("price")
            ]

            collected.extend(perfumes_valid)
            log.info(
                f"   ↳ Page {page_num}: {len(products_on_page)} total "
                f"→ {len(perfumes_valid)} perfumes kept"
            )

            if page_num < SCRAPE_CONFIG["max_pages_per_keyword"]:
                _random_delay(SCRAPE_CONFIG["delay_between_pages"])

    except Exception as exc:
        log.error(f"   ❌ scrape_keyword error for '{keyword}': {exc}")
    finally:
        context.close()

    return collected


# ══════════════════════════════════════════════════════════════════════════════
# ── 6. حفظ البيانات في Supabase (نفس models الموجودة) ───────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _save_to_db(app, all_products: list[dict]) -> tuple[int, int, int]:
    """
    يحفظ المنتجات في Supabase باستخدام نفس SQLAlchemy models.
    يُميّز مصدر البيانات بـ source='aliexpress_scraper'.
    يتحقق من external_item_id لتجنب التكرار مع API sync.

    Returns: (added, updated, skipped)
    """
    from app.extensions import db
    from app.models import (
        Store, Item, ItemStoreLink,
        Brand, Category, ItemImage, ItemVariant,
    )
    from app.utils.normalizers import generate_slug

    added = updated = skipped = 0

    with app.app_context():
        # ── إيجاد/إنشاء متجر AliExpress ───────────────────────────────────
        store = Store.query.filter(Store.name.ilike("%aliexpress%")).first()
        if not store:
            log.error(
                "❌ AliExpress store not found in DB. "
                "Please create it from Admin panel first."
            )
            return 0, 0, 0

        # ── إيجاد/إنشاء البراند الافتراضي ─────────────────────────────────
        brand = Brand.query.filter(Brand.name.ilike("Generic")).first()
        if not brand:
            brand = Brand()
            brand.name = "Generic"
            brand.slug = "generic"
            db.session.add(brand)
            db.session.flush()

        # ── إيجاد/إنشاء التصنيف الافتراضي ────────────────────────────────
        category = Category.query.filter(Category.name.ilike("عطور")).first()
        if not category:
            category = Category()
            category.name = "عطور"
            category.slug = "perfumes"
            db.session.add(category)
            db.session.flush()

        for raw in all_products:
            try:
                ext_id    = str(raw.get("item_id", "")).strip()
                title     = (raw.get("title") or "").strip()
                price     = raw.get("price")
                image_url = raw.get("image_url", "")
                item_url  = raw.get("item_url", "")

                if not ext_id or not title or not price:
                    skipped += 1
                    continue

                # ── هل الرابط موجود مسبقاً (API أو Scraper)؟ ────────────
                existing_link = ItemStoreLink.query.filter_by(
                    store_id=store.id,
                    external_item_id=ext_id,
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

                # ── إيجاد أو إنشاء Item ───────────────────────────────────
                item = Item.query.filter(Item.name.ilike(title)).first()

                if not item:
                    base_slug = generate_slug(title) or f"product-{ext_id}"
                    slug      = base_slug
                    counter   = 1
                    while Item.query.filter_by(brand_id=brand.id, slug=slug).first():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    item = Item()
                    item.name        = title
                    item.slug        = slug
                    item.brand_id    = brand.id
                    item.category_id = category.id
                    item.item_type   = "perfume"
                    db.session.add(item)
                    db.session.flush()

                    if image_url:
                        img = ItemImage()
                        img.item_id    = item.id
                        img.image_path = image_url
                        img.alt_text   = title[:200]
                        img.position   = 0
                        db.session.add(img)

                # ── إيجاد أو إنشاء Variant ────────────────────────────────
                variant = ItemVariant.query.filter_by(item_id=item.id).first()
                if not variant:
                    variant = ItemVariant()
                    variant.item_id    = item.id
                    variant.title      = "Default"
                    variant.sku        = f"SCRAPE-{ext_id}"
                    variant.is_default = True
                    db.session.add(variant)
                    db.session.flush()

                # ── إنشاء StoreLink ───────────────────────────────────────
                link = ItemStoreLink()
                link.variant_id       = variant.id
                link.store_id         = store.id
                link.external_item_id = ext_id
                link.affiliate_url    = item_url or f"https://www.aliexpress.com/item/{ext_id}.html"
                link.price            = price
                link.currency         = "USD"
                link.availability     = "instock"
                link.is_active        = True
                link.source           = "aliexpress_scraper"   # ← يُميّزه عن API
                link.imported_at      = datetime.now(timezone.utc)
                link.last_checked_at  = datetime.now(timezone.utc)
                db.session.add(link)

                added += 1

                # Commit دفعي كل 50 منتج
                if (added + updated) % 50 == 0:
                    db.session.commit()
                    log.info(f"   💾 Batch saved: {added} added, {updated} updated so far...")

            except Exception as exc:
                db.session.rollback()
                log.error(f"   ⚠️  Error saving product '{raw.get('item_id')}': {exc}")
                continue

        # الحفظ النهائي
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            log.error(f"❌ Final commit failed: {exc}")

    return added, updated, skipped


# ══════════════════════════════════════════════════════════════════════════════
# ── 7. نقطة التشغيل الرئيسية ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def run_scraper():
    """المهمة الرئيسية: تشغيل الكشط وحفظ النتائج في Supabase."""

    log.info("══════════════════════════════════════════════════════════")
    log.info("🕷️  ALIEXPRESS SCRAPER STARTED")
    log.info("   Source tag : aliexpress_scraper")
    log.info("   Keywords   : " + ", ".join(PERFUME_KEYWORDS))
    log.info("══════════════════════════════════════════════════════════")

    # ── التحقق من DATABASE_URL ────────────────────────────────────────────
    if not os.environ.get("DATABASE_URL"):
        log.error("❌ DATABASE_URL is not set in environment!")
        sys.exit(1)

    # ── تحميل Flask app للوصول إلى DB ─────────────────────────────────────
    try:
        from app import create_app
    except ImportError as exc:
        log.error(f"❌ Cannot import Flask app: {exc}")
        sys.exit(1)

    flask_app = create_app()

    # ── تشغيل Playwright وجمع المنتجات ────────────────────────────────────
    all_products: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=SCRAPE_CONFIG["headless"],
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        try:
            for i, keyword in enumerate(PERFUME_KEYWORDS):
                log.info(f"🔍 [{i+1}/{len(PERFUME_KEYWORDS)}] Searching: '{keyword}'")
                results = scrape_keyword(browser, keyword)
                all_products.extend(results)
                log.info(f"   ✅ '{keyword}' → {len(results)} perfumes collected")

                if i < len(PERFUME_KEYWORDS) - 1:
                    _random_delay(SCRAPE_CONFIG["delay_between_keywords"])

        finally:
            browser.close()

    log.info(f"📦 Total perfumes collected: {len(all_products)}")

    if not all_products:
        log.warning("⚠️ No perfumes collected. AliExpress may have blocked or changed layout.")
        log.warning("   Try: reducing keywords, increasing delays, or using a proxy.")
        sys.exit(0)

    # ── حفظ في Supabase ───────────────────────────────────────────────────
    log.info("💾 Saving to Supabase...")
    added, updated, skipped = _save_to_db(flask_app, all_products)

    log.info("══════════════════════════════════════════════════════════")
    log.info("🏁 ALIEXPRESS SCRAPER COMPLETED")
    log.info(f"   ✅ Added   : {added}")
    log.info(f"   🔄 Updated : {updated}")
    log.info(f"   ⏭️  Skipped : {skipped}")
    log.info("══════════════════════════════════════════════════════════")


if __name__ == "__main__":
    run_scraper()
