import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.helpers.context import invalidate_layout_cache, invalidate_settings_cache
from app.models import (
    Brand,
    Category,
    Item,
    ItemImage,
    Setting,
    User,
    db,
)


@pytest.fixture()
def app(tmp_path):
    app = create_app()
    db_path = tmp_path / "test.db"
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path.as_posix()}",
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
        SERVER_NAME="localhost",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        _seed_required_settings()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def app_csrf(tmp_path):
    app = create_app()
    db_path = tmp_path / "test_csrf.db"
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path.as_posix()}",
        WTF_CSRF_ENABLED=True,
        RATELIMIT_ENABLED=False,
        SERVER_NAME="localhost",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        _seed_required_settings()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def client_csrf(app_csrf):
    return app_csrf.test_client()


@pytest.fixture()
def user_factory(app):
    def _factory(email, password="Pass12345!", is_admin=False):
        with app.app_context():
            user = User(email=email, is_admin=is_admin)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user

    return _factory


@pytest.fixture()
def item_factory(app):
    def _factory(name, *, brand_name="Brand A", category_name="Category A"):
        with app.app_context():
            brand = Brand.query.filter_by(name=brand_name).first()
            if not brand:
                brand = Brand(name=brand_name, slug=re.sub(r"\s+", "-", brand_name.lower()))
                db.session.add(brand)

            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name, slug=re.sub(r"\s+", "-", category_name.lower()))
                db.session.add(category)

            db.session.flush()

            item = Item(
                name=name,
                slug=re.sub(r"\s+", "-", name.lower()),
                brand_id=brand.id,
                category_id=category.id,
                card_type="item",
                description=f"{name} description",
                meta_description=f"{name} meta",
            )
            db.session.add(item)
            db.session.flush()

            db.session.add(
                ItemImage(
                    item_id=item.id,
                    image_path="static/uploads/test.png",
                    alt_text=name,
                    position=0,
                )
            )

            db.session.commit()
            return {
                "id": item.id,
                "name": item.name,
                "brand_id": item.brand_id,
                "category_id": item.category_id,
            }

    return _factory


def _seed_required_settings():
    required = {
        "site_name": "ATRI Test",
        "meta_description_default": "Test description",
        "instagram_link": "https://instagram.com/test",
        "whatsapp_number": "+966500000000",
        "contact_email": "test@example.com",
    }

    for key, value in required.items():
        if not Setting.query.get(key):
            db.session.add(Setting(key=key, value=value, description="seeded for tests"))

    db.session.commit()
    invalidate_settings_cache()
    invalidate_layout_cache()
