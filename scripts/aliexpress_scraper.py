"""
scripts/aliexpress_scraper.py
══════════════════════════════════════════════════════════════════════════════
AliExpress Web Scraper — يعمل بجانب aliexpress_api_sync.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• لا يحتاج API Key أو Access Token
• يستخدم Playwright مع تقنيات Stealth يدوية (بدون مكتبات خارجية)
• يخزن البيانات في نفس قاعدة Supabase بنفس models الموجودة
• يتحقق من external_item_id لتجنب التكرار مع سكربت الـ API
• مصدر البيانات: 'aliexpress_scraper'
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

# ── 3. التحقق من وجود Playwright فقط (لا نحتاج playwright-stealth) ───────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    log.error("❌ مكتبة Playwright غير مثبتة!")
    log.error("   شغّل: pip install playwright && playwright install chromium")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# ── 4. إعدادات السكربت ───────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

PERFUME_KEYWORDS = [
    "perfume",
    "eau de parfum",
    "fragrance",
    "cologne",
    "oud perfume",
    "musk perfume",
    "attar perfume",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

SCRAPE_CONFIG = {
    "max_pages_per_keyword": 3,
    "delay_between_pages":   (3, 7),
    "delay_between_keywords": (8, 15),
    "headless": True,
    "timeout_ms": 45_000,
}

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

# ── تعليمات JavaScript لإخفاء بصمة البوت تماماً (Stealth بدون مكتبة خارجية) ─
_STEALTH_JS = """
() => {
    // 1. إخفاء خاصية webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => false });

    // 2. تعبئة plugins بقيم وهمية
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // 3. تعبئة languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // 4. إخفاء chrome automation
    window.chrome = { runtime: {} };

    // 5. إخفاء permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
}
"""


# ══════════════════════════════════════════════════════════════════════════════
# ── 5. دوال المساعدة ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _is_perfume(title: str) -> bool:
    """فلترة دقيقة: هل المنتج عطر؟"""
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
    # تجنب نقطة فارغة مثل "." أو قيم غير صحيحة
    if not cleaned or cleaned == ".":
        return None
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def _random_delay(range_tuple: tuple):
    """انتظار عشوائي لتجنب الحظر"""
    time.sleep(random.uniform(*range_tuple))


def _handle_popups(page):
    """إغلاق النوافذ المنبثقة (اختيار الدولة، الكوكيز)"""
    selectors = [
        ".ship-to--close--3ToR9m9",
        ".next-dialog-close",
        ".pop-close-btn",
        ".close-button",
        "[class*='close-btn']",
        "[class*='modal-close']",
    ]
    for selector in selectors:
        try:
            if page.is_visible(selector, timeout=1000):
                page.click(selector)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# ── 6. محرك الكشط الاحترافي ──────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def scrape_keyword(browser, keyword: str) -> list:
    """
    يبحث عن كلمة مفتاحية في AliExpress باستخدام Stealth يدوي.
    يُعيد قائمة المنتجات المُصفّاة (عطور فقط) مع سعر صحيح.
    """
    collected = []

    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
        viewport={"width": 1920, "height": 1080},
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        },
    )

    try:
        page = context.new_page()

        # ✅ حقن Stealth JS في كل صفحة جديدة
        page.add_init_script(_STEALTH_JS)

        for page_num in range(1, SCRAPE_CONFIG["max_pages_per_keyword"] + 1):
            search_slug = keyword.replace(" ", "-")
            url = (
                f"https://www.aliexpress.com/w/wholesale-{search_slug}.html"
                f"?page={page_num}&g=y&SearchText={search_slug}"
            )

            log.info(f"   📄 Page {page_num}: {url[:75]}...")

            try:
                page.goto(url, wait_until="domcontentloaded",
                          timeout=SCRAPE_CONFIG["timeout_ms"])

                # إغلاق أي نوافذ منبثقة
                _handle_popups(page)

                # محاكاة تمرير بشري (Lazy Loading)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                _random_delay((1.5, 2.5))
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                _random_delay((1, 2))

                # انتظار ظهور الروابط
                page.wait_for_selector(
                    "a[href*='/item/']",
                    timeout=20_000,
                )

            except PlaywrightTimeout:
                log.warning(f"   ⚠️  Timeout page {page_num} — continuing to next.")
                continue
            except Exception as e:
                log.warning(f"   ⚠️  Page load error page {page_num}: {e}")
                continue

            # ── استخراج البيانات بـ JavaScript ───────────────────────────────
            try:
                products_on_page = page.evaluate("""
                    () => {
                        const results = [];
                        const seenIds = new Set();
                        const links = document.querySelectorAll('a[href*="/item/"]');

                        links.forEach(link => {
                            const href = link.href || '';
                            const idMatch = href.match(/\\/item\\/(\\d+)\\.html/);
                            const itemId = idMatch ? idMatch[1] : null;
                            if (!itemId || seenIds.has(itemId)) return;
                            seenIds.add(itemId);

                            // البحث عن الحاوية الأقرب للمنتج
                            const card = link.closest(
                                '[data-index], [class*="item"], [class*="product"], ' +
                                '[class*="card"], [class*="tile"]'
                            ) || link.parentElement || document.body;

                            // العنوان
                            const titleEl = card.querySelector(
                                'h1, h2, h3, [class*="title"], [class*="name"], span[title]'
                            );
                            const title = titleEl
                                ? (titleEl.innerText || titleEl.title || '').trim()
                                : (link.title || link.innerText || '').trim();

                            // السعر
                            const priceEl = card.querySelector(
                                '[class*="price-current"], [class*="price--current"], ' +
                                '[class*="sale-price"], [class*="price"]'
                            );
                            const priceText = priceEl ? priceEl.innerText.trim() : '';

                            // الصورة
                            const imgEl = card.querySelector('img');
                            const img = imgEl
                                ? (imgEl.src || imgEl.dataset.src || imgEl.dataset.lazySrc || '')
                                : '';

                            if (title && title.length > 8) {
                                results.push({
                                    item_id:   itemId,
                                    title:     title.substring(0, 200),
                                    price_text: priceText,
                                    image_url: img.startsWith('http') ? img : '',
                                    item_url:  href.split('?')[0],
                                });
                            }
                        });
                        return results;
                    }
                """)
            except Exception as e:
                log.warning(f"   ⚠️  JS evaluation failed page {page_num}: {e}")
                continue

            if not products_on_page:
                log.info(f"   ↳ No products found on page {page_num}.")
                continue

            # فلترة العطور وتحليل الأسعار
            page_added = 0
            for p in products_on_page:
                if not _is_perfume(p.get("title", "")):
                    continue
                price = _parse_price(p.get("price_text", ""))
                if not price:
                    continue
                p["price"] = price
                collected.append(p)
                page_added += 1

            log.info(
                f"   ↳ Page {page_num}: {len(products_on_page)} cards "
                f"→ {page_added} perfumes added (total: {len(collected)})"
            )

            if page_num < SCRAPE_CONFIG["max_pages_per_keyword"]:
                _random_delay(SCRAPE_CONFIG["delay_between_pages"])

    except Exception as exc:
        log.error(f"   ❌ scrape_keyword critical error '{keyword}': {exc}")
    finally:
        context.close()

    return collected


# ══════════════════════════════════════════════════════════════════════════════
# ── 7. حفظ البيانات في Supabase ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _save_to_db(app, all_products: list) -> tuple:
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
        # ── إيجاد متجر AliExpress ─────────────────────────────────────────
        store = Store.query.filter(Store.name.ilike("%aliexpress%")).first()
        if not store:
            log.error("❌ AliExpress store not found. Create it from Admin panel first.")
            return 0, 0, 0

        # ── البراند الافتراضي ──────────────────────────────────────────────
        brand = Brand.query.filter(Brand.name.ilike("Generic")).first()
        if not brand:
            brand = Brand()
            brand.name = "Generic"
            brand.slug = "generic"
            db.session.add(brand)
            db.session.flush()

        # ── التصنيف الافتراضي ──────────────────────────────────────────────
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
                image_url = (raw.get("image_url") or "").strip()
                item_url  = (raw.get("item_url") or "").strip()

                if not ext_id or not title or not price:
                    skipped += 1
                    continue

                # ── التحقق من وجود الرابط مسبقاً ────────────────────────
                existing_link = ItemStoreLink.query.filter_by(
                    store_id=store.id,
                    external_item_id=ext_id,
                ).first()

                if existing_link:
                    if float(existing_link.price or 0) != float(price):
                        existing_link.old_price = existing_link.price
                        existing_link.price = price
                        existing_link.last_checked_at = datetime.now(timezone.utc)
                        updated += 1
                    else:
                        skipped += 1
                    continue

                # ── إيجاد أو إنشاء Item ────────────────────────────────────
                item = Item.query.filter(Item.name.ilike(title)).first()

                if not item:
                    base_slug = generate_slug(title) or f"product-{ext_id}"
                    slug = base_slug
                    counter = 1
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

                # ── إيجاد أو إنشاء Variant ─────────────────────────────────
                variant = ItemVariant.query.filter_by(item_id=item.id).first()
                if not variant:
                    variant = ItemVariant()
                    variant.item_id    = item.id
                    variant.title      = "Default"
                    variant.sku        = f"SCRAPE-{ext_id}"
                    variant.is_default = True
                    db.session.add(variant)
                    db.session.flush()

                # ── إنشاء StoreLink ────────────────────────────────────────
                link = ItemStoreLink()
                link.variant_id       = variant.id
                link.store_id         = store.id
                link.external_item_id = ext_id
                link.affiliate_url    = item_url or f"https://www.aliexpress.com/item/{ext_id}.html"
                link.price            = price
                link.currency         = "USD"
                link.availability     = "instock"
                link.is_active        = True
                link.source           = "aliexpress_scraper"
                link.imported_at      = datetime.now(timezone.utc)
                link.last_checked_at  = datetime.now(timezone.utc)
                db.session.add(link)

                added += 1

                # Commit دفعي كل 50 منتج
                if (added + updated) % 50 == 0:
                    db.session.commit()
                    log.info(f"   💾 Batch: {added} added, {updated} updated...")

            except Exception as exc:
                db.session.rollback()
                log.error(f"   ⚠️  Error saving '{raw.get('item_id')}': {exc}")
                continue

        # الحفظ النهائي
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            log.error(f"❌ Final commit failed: {exc}")

    return added, updated, skipped


# ══════════════════════════════════════════════════════════════════════════════
# ── 8. نقطة التشغيل الرئيسية ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def run_scraper():
    """المهمة الرئيسية."""

    log.info("══════════════════════════════════════════════════════════")
    log.info("🕷️  ALIEXPRESS SCRAPER STARTED")
    log.info("   Mode   : Headless Chromium + Manual Stealth (no external deps)")
    log.info("   Source : aliexpress_scraper")
    log.info("══════════════════════════════════════════════════════════")

    if not os.environ.get("DATABASE_URL"):
        log.error("❌ DATABASE_URL is not set!")
        sys.exit(1)

    try:
        from app import create_app
    except ImportError as exc:
        log.error(f"❌ Cannot import Flask app: {exc}")
        sys.exit(1)

    flask_app = create_app()
    all_products: list = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=SCRAPE_CONFIG["headless"],
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080",
            ],
        )

        try:
            for i, keyword in enumerate(PERFUME_KEYWORDS):
                log.info(f"🔍 [{i+1}/{len(PERFUME_KEYWORDS)}] Searching: '{keyword}'")
                results = scrape_keyword(browser, keyword)
                all_products.extend(results)
                log.info(f"   ✅ '{keyword}' → {len(results)} perfumes")

                if i < len(PERFUME_KEYWORDS) - 1:
                    _random_delay(SCRAPE_CONFIG["delay_between_keywords"])

        finally:
            browser.close()

    log.info(f"📦 Total collected: {len(all_products)}")

    if not all_products:
        log.warning("⚠️ No perfumes collected. AliExpress may be blocking.")
        sys.exit(0)

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
