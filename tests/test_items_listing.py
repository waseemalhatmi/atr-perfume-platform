def test_items_listing_renders_items(client, item_factory):
    item_factory("Amber Night", brand_name="House A", category_name="Luxury")
    item_factory("Ocean Mist", brand_name="House B", category_name="Fresh")

    res = client.get("/items")
    assert res.status_code == 200
    assert b"Amber Night" in res.data
    assert b"Ocean Mist" in res.data


def test_items_filter_by_brand(client, item_factory):
    item_a = item_factory("Filtered A", brand_name="Filter Brand A", category_name="Luxury")
    item_factory("Filtered B", brand_name="Filter Brand B", category_name="Luxury")

    res = client.get(f"/items?brand={item_a['brand_id']}")
    assert res.status_code == 200
    assert b"Filtered A" in res.data
    assert b"Filtered B" not in res.data


def test_items_filter_by_category(client, item_factory):
    item_a = item_factory("Category A Item", brand_name="Brand C", category_name="Category A")
    item_factory("Category B Item", brand_name="Brand C", category_name="Category B")

    res = client.get(f"/items?category={item_a['category_id']}")
    assert res.status_code == 200
    assert b"Category A Item" in res.data
    assert b"Category B Item" not in res.data
