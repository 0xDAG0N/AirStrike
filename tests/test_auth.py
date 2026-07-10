"""Auth + CSRF tests (P0 · S3)."""


def test_unauthenticated_api_returns_401(anon_client):
    assert anon_client.get("/dashboard_stats").status_code == 401


def test_unauthenticated_page_redirects_to_login(anon_client):
    resp = anon_client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_page_is_public(anon_client):
    assert anon_client.get("/login").status_code == 200


def test_login_with_correct_password_grants_access(anon_client):
    resp = anon_client.post("/login", data={"password": "test-pass"})
    assert resp.status_code == 302
    # The session cookie now authenticates subsequent requests.
    assert anon_client.get("/dashboard_stats").status_code == 200


def test_login_with_wrong_password_denied(anon_client):
    resp = anon_client.post("/login", data={"password": "nope"})
    assert resp.status_code == 200  # re-rendered login with an error
    assert anon_client.get("/dashboard_stats").status_code == 401


def test_post_without_csrf_is_blocked(client):
    # Authenticated but no CSRF header → rejected before the route runs.
    assert client.post("/stop_attack", json={}).status_code == 400


def test_post_with_valid_csrf_passes(client, csrf):
    # Reaches the route (no attack running → 200 success:false), i.e. NOT a 400 CSRF failure.
    resp = client.post("/stop_attack", json={}, headers={"X-CSRFToken": csrf})
    assert resp.status_code == 200


def test_login_blocks_open_redirect(anon_client):
    resp = anon_client.post("/login", data={"password": "test-pass", "next": "//evil.com"})
    assert resp.status_code == 302
    assert "evil.com" not in resp.headers["Location"]
