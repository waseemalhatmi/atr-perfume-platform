def test_admin_dashboard_requires_login(client):
    res = client.get("/admin/")
    assert res.status_code in (301, 302)


def test_non_admin_cannot_access_admin_dashboard(client, user_factory):
    user_factory("member@example.com", is_admin=False)
    client.post("/login", data={"email": "member@example.com", "password": "Pass12345!"})

    res = client.get("/admin/")
    assert res.status_code in (301, 302)


def test_non_admin_forbidden_on_price_tracker(client, user_factory):
    user_factory("member2@example.com", is_admin=False)
    client.post("/login", data={"email": "member2@example.com", "password": "Pass12345!"})

    res = client.get("/admin/run-price-tracker")
    assert res.status_code == 403


def test_admin_can_access_dashboard(client, user_factory):
    user_factory("admin@example.com", is_admin=True)
    client.post("/login", data={"email": "admin@example.com", "password": "Pass12345!"})

    res = client.get("/admin/")
    assert res.status_code == 200
