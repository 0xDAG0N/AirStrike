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


def test_auth_off_by_default_allows_direct_access(monkeypatch):
    # Loopback single-operator default: no login gate, tool is directly usable.
    monkeypatch.setenv("AIRSTRIKE_DISABLE_AUTH", "1")
    from app import create_app
    from app.config import TestConfig

    app = create_app(TestConfig)
    c = app.test_client()
    assert c.get("/dashboard_stats").status_code == 200  # no session needed
    assert c.get("/login").status_code == 404            # login route not even registered


def test_cross_origin_request_rejected(client):
    # Authenticated, but the Origin header is a different site → blocked.
    resp = client.get("/dashboard_stats", headers={"Origin": "http://evil.example"})
    assert resp.status_code == 403


def test_login_brute_force_lockout(anon_client):
    from app.core import auth

    try:
        for _ in range(auth._MAX_FAILS):
            anon_client.post("/login", data={"password": "wrong"})
        # Now locked: even the correct password is refused (no redirect, still unauthenticated).
        resp = anon_client.post("/login", data={"password": "test-pass"})
        assert resp.status_code == 200
        assert anon_client.get("/dashboard_stats").status_code == 401
    finally:
        auth.clear_login_failures("127.0.0.1")
