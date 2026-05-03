import pytest


@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        ("/", 200),
        ("/login", 200),
        ("/register", 200),
        ("/items", 200),
        ("/contact", 200),
        ("/admin/", 302),
        ("/api/notifications", 302),
        ("/admin/run-price-tracker", 302),
    ],
)
def test_sensitive_routes_smoke_get(client, path, expected_status):
    res = client.get(path)
    assert res.status_code == expected_status


def test_sensitive_route_smoke_contact_post(client):
    res = client.post(
        "/contact",
        data={
            "name": "Tester",
            "email": "tester@example.com",
            "subject": "Hello",
            "message": "Smoke test message",
        },
    )
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_sensitive_route_smoke_subscribe_post(client):
    res = client.post("/subscribe", data={"mode": "guest", "email": "guest@example.com"})
    assert res.status_code == 200
    assert "success" in res.get_json()
