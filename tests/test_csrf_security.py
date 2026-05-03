import re


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', html)
    assert match, "CSRF token was not found in rendered HTML."
    return match.group(1)


def test_post_without_csrf_token_is_rejected(client_csrf):
    res = client_csrf.post("/set-country", json={"country": "sa"})
    assert res.status_code == 400


def test_post_with_valid_csrf_token_succeeds(client_csrf):
    page = client_csrf.get("/")
    token = _extract_csrf_token(page.get_data(as_text=True))

    res = client_csrf.post(
        "/set-country",
        json={"country": "sa"},
        headers={"X-CSRFToken": token},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["success"] is True
