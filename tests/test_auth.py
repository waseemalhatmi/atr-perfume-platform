def test_register_login_logout_flow(client):
    register_res = client.post(
        "/register",
        data={"email": "newuser@example.com", "password": "Pass12345!", "subscribe": "1"},
        follow_redirects=True,
    )
    assert register_res.status_code == 200
    assert b"Registration completed successfully" in register_res.data

    client.get("/logout", follow_redirects=True)

    login_res = client.post(
        "/login",
        data={"email": "newuser@example.com", "password": "Pass12345!"},
        follow_redirects=True,
    )
    assert login_res.status_code == 200

    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"logged out successfully" in logout_res.data


def test_login_rejects_invalid_credentials(client, user_factory):
    user_factory("valid@example.com", password="Pass12345!")
    bad_login = client.post(
        "/login",
        data={"email": "valid@example.com", "password": "WrongPassword"},
        follow_redirects=True,
    )
    assert bad_login.status_code == 200
    assert b"Invalid email or password" in bad_login.data
