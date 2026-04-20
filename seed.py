from app import create_app, db
from app.models import (
    Brand, Category, Item, ItemVariant, 
    ItemStoreLink, ItemImage, Store, ItemSpecification
)
from decimal import Decimal
import os

def seed_data():
    app = create_app()
    with app.app_context():
        # 1. Clear existing data
        print("Cleaning up database...")
        db.drop_all()
        db.create_all()

        # 2. Add Stores
        print("Adding stores...")
        stores = [
            Store(name="Amazon", slug="amazon", website="https://amazon.com", country="SA", currency="SAR", affiliate_network="Amazon Associates"),
            Store(name="Noon", slug="noon", website="https://noon.com", country="SA", currency="SAR", affiliate_network="Noon Affiliate"),
            Store(name="Sephora", slug="sephora", website="https://sephora.com", country="SA", currency="SAR"),
        ]
        for s in stores: db.session.add(s)

        # 3. Add Brands
        print("Adding brands...")
        brands_data = [
            ("Chanel", "chanel"),
            ("Dior", "dior"),
            ("Tom Ford", "tom-ford"),
            ("Creed", "creed"),
            ("Giorgio Armani", "giorgio-armani"),
            ("YSL", "ysl"),
            ("Maison Francis Kurkdjian", "mfk")
        ]
        brands = {slug: Brand(name=name, slug=slug, is_featured=True) for name, slug in brands_data}
        for b in brands.values(): db.session.add(b)

        # 4. Add Categories
        print("Adding categories...")
        cats_data = [
            ("عطور رجالية", "men-perfumes"),
            ("عطور نسائية", "women-perfumes"),
            ("عطور النيش", "niche-perfumes")
        ]
        categories = {slug: Category(name=name, slug=slug) for name, slug in cats_data}
        for c in categories.values(): db.session.add(c)
        db.session.commit()

        # 5. Perfume Data & Images Mapping
        # Available images in app/static/uploads/perfumes/
        image_files = [
            "photo-1523293182086-7651a899d37f.jfif",
            "photo-1541643600914-78b084683601 (1).jfif",
            "photo-1541643600914-78b084683601.jfif",
            "photo-1587017539504-67cfbddac569.jfif",
            "photo-1592945403244-b3fbafd7f539.jfif",
            "photo-1594035910387-fea47794261f.jfif"
        ]

        perfumes = [
            {
                "name": "Bleu de Chanel",
                "slug": "bleu-de-chanel",
                "brand": "chanel",
                "category": "men-perfumes",
                "description": "عطر خشبي أروماتك للرجال، يجسد الحرية والرجولة. مزيج من الحمضيات الصقلية والروائح الخشبية الجافة.",
                "price": 150.00,
                "img_idx": 0,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "8-10 ساعات", "الفواحان": "قوي"},
                "notes": {"Top": "الجريب فروت، الليمون، النعناع", "Middle": "الزنجبيل، الياسمين، جوزة الطيب", "Base": "البخور، الأرز، خشب الصندل"}
            },
            {
                "name": "Dior Sauvage",
                "slug": "dior-sauvage",
                "brand": "dior",
                "category": "men-perfumes",
                "description": "عطر منعش وقوي مستوحى من المساحات المفتوحة الصخرية. تركيبة خام ونبيلة في آن واحد.",
                "price": 135.00,
                "img_idx": 1,
                "specs": {"التركيز": "Parfum", "الثبات": "10-12 ساعة", "الفواحان": "قوي جداً"},
                "notes": {"Top": "برغموت كالابريا، الفلفل", "Middle": "الفلفل الوردي، اللافندر، نجيل الهند", "Base": "الأمبروكسان، الأرز، اللابدانوم"}
            },
            {
                "name": "Creed Aventus",
                "slug": "creed-aventus",
                "brand": "creed",
                "category": "niche-perfumes",
                "description": "عطر النجاح والقوة، يجمع بين الفواكه والأخشاب بلمسة ملكية لا تُنسى.",
                "price": 420.00,
                "img_idx": 2,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "10 ساعات", "الفواحان": "ممتاز"},
                "notes": {"Top": "الأناناس، البرغموت، التفاح", "Middle": "التوابل، الياسمين، الباتشولي", "Base": "المسك، عنبر الحوت، البتولا"}
            },
            {
                "name": "Tom Ford Black Orchid",
                "slug": "black-orchid",
                "brand": "tom-ford",
                "category": "women-perfumes",
                "description": "عطر شرقي زهري غامض وفخم جداً للمرأة العصرية. مزيج من الأوركيد الأسود والتوابل.",
                "price": 180.00,
                "img_idx": 3,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "12 ساعة", "الفواحان": "ثقيل"},
                "notes": {"Top": "الكمأة، الغاردينيا، الياسمين", "Middle": "الأوركيد الأسود، التوابل، الفواكه", "Base": "الشوكولاتة المكسيكية، الباتشولي، البخور"}
            },
            {
                "name": "Acqua di Gio",
                "slug": "acqua-di-gio",
                "brand": "giorgio-armani",
                "category": "men-perfumes",
                "description": "عطر مائي حمضي مستوحى من البحر والشمس. رائحة الحرية والرياح والماء.",
                "price": 110.00,
                "img_idx": 4,
                "specs": {"التركيز": "Eau de Toilette", "الثبات": "6 ساعات", "الفواحان": "متوسط"},
                "notes": {"Top": "ماء البحر، البرغموت، الليمون", "Middle": "إكليل الجبل، الميرمية، إبرة الراعي", "Base": "الباتشولي، البخور"}
            },
            {
                "name": "YSL Libre",
                "slug": "ysl-libre",
                "brand": "ysl",
                "category": "women-perfumes",
                "description": "عطر الحرية، يمزج بين اللافندر الفرنسي وزهر البرتقال المغربي بلمسة من المسك.",
                "price": 140.00,
                "img_idx": 5,
                "specs": {"التركيز": "Eau de Parfum Intense", "الثبات": "9 ساعات", "الفواحان": "راقي"},
                "notes": {"Top": "اللافندر، المندرين، الكشمش الأسود", "Middle": "اللافندر، زهر البرتقال، الياسمين", "Base": "فانيليا مدغشقر، المسك، الأرز"}
            },
            {
                "name": "Baccarat Rouge 540",
                "slug": "baccarat-rouge-540",
                "brand": "mfk",
                "category": "niche-perfumes",
                "description": "عطر المليونيرات الشهير، رائحة العنبر والأزهار الخشبية التي تداعب الحواس.",
                "price": 320.00,
                "img_idx": 0,
                "specs": {"التركيز": "Extrait de Parfum", "الثبات": "15 ساعة", "الفواحان": "خرافي"},
                "notes": {"Top": "الزعفران، الياسمين", "Middle": "خشب العنبر، عنبر الحوت", "Base": "راتنج الصنوبر، الأرز"}
            },
            {
                "name": "Chanel No. 5",
                "slug": "chanel-no-5",
                "brand": "chanel",
                "category": "women-perfumes",
                "description": "الأسطورة الخالدة، العطر الذي غير مفهوم الأنوثة برائحة الألدهيدات والأزهار.",
                "price": 165.00,
                "img_idx": 1,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "8 ساعات", "الفواحان": "كلاسيكي"},
                "notes": {"Top": "الألدهيدات، الإيلنغ، المندرين", "Middle": "الياسمين، الورد، زنبق الوادي", "Base": "خشب الصندل، الفانيليا، العنبر"}
            },
            {
                "name": "Tom Ford Ombré Leather",
                "slug": "ombre-leather",
                "brand": "tom-ford",
                "category": "niche-perfumes",
                "description": "عطر الجلود الفاخر، يجسد روح الغرب الأمريكي الواسعة والجمال الجامح.",
                "price": 210.00,
                "img_idx": 2,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "10 ساعات", "الفواحان": "جذاب"},
                "notes": {"Top": "الهيل", "Middle": "الجلود، ياسمين سامباك", "Base": "العنبر، الطحالب، الباتشولي"}
            },
            {
                "name": "Dior J'adore",
                "slug": "dior-jadore",
                "brand": "dior",
                "category": "women-perfumes",
                "description": "باقة من أجمل زهور العالم، عطر أنثوي بامتياز يجمع بين الفخمة والأناقة.",
                "price": 145.00,
                "img_idx": 3,
                "specs": {"التركيز": "Eau de Parfum", "الثبات": "8 ساعات", "الفواحان": "ناعم"},
                "notes": {"Top": "الكمثرى، البطيخ، البرغموت", "Middle": "الياسمين، الورد، مسك الروم", "Base": "المسك، الفانيليا، الأرز"}
            }
        ]

        print("Adding perfumes and details...")
        for p in perfumes:
            item = Item(
                name=p["name"],
                slug=p["slug"],
                description=p["description"],
                brand=brands[p["brand"]],
                category=categories[p["category"]],
                card_type="item",
                item_type="perfume"
            )
            db.session.add(item)
            db.session.flush()

            # Image
            img_path = f"uploads/perfumes/{image_files[p['img_idx']]}"
            img = ItemImage(item_id=item.id, image_path=img_path, position=1)
            db.session.add(img)

            # Variant
            variant = ItemVariant(
                item_id=item.id,
                title="100ml",
                is_default=True,
                attributes={"size": "100ml", "type": "EDP"}
            )
            db.session.add(variant)
            db.session.flush()

            # Store Links
            for i, s in enumerate(stores):
                # Add some price variation
                final_price = p["price"] + (i * 5) 
                link = ItemStoreLink(
                    variant_id=variant.id,
                    store_id=s.id,
                    affiliate_url=f"{s.website}/product/{p['slug']}",
                    price=Decimal(str(final_price)),
                    is_active=True,
                    availability="in_stock"
                )
                db.session.add(link)

            # Specs
            spec = ItemSpecification(
                item_id=item.id,
                category="العطر",
                spec_json=p["specs"]
            )
            db.session.add(spec)

            # Notes
            if "notes" in p:
                notes_spec = ItemSpecification(
                    item_id=item.id,
                    category="مكونات العطر",
                    spec_json=p["notes"]
                )
                db.session.add(notes_spec)

        db.session.commit()
        print("Success! Added 10 luxury perfumes with stores and images.")

if __name__ == "__main__":
    seed_data()
