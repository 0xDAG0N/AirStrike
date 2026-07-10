"""Authentication + CSRF for the control panel (P0, docs/roadmap/01-security.md · S3).

Single-operator model: one password (from ``AIRSTRIKE_PASSWORD``, or a random one that is
generated and printed once at startup). A session cookie gates every route except the login
page and static files; every state-changing request must carry the per-session CSRF token;
and every authenticated request must be same-origin. Session cookies are HttpOnly +
SameSite=Strict, so cross-site navigations never carry them (closing cross-site GET
side-effects and forced-logout). Combined with the loopback-by-default bind, the panel is
not reachable — let alone controllable — by other machines or other sites.
"""

import os
import time
import hmac
import secrets
from urllib.parse import urlparse

from flask import session, request, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.core.logging import logger

# Reachable without a session. (logout requires a session, protected by SameSite=Strict.)
_PUBLIC_ENDPOINTS = {"auth.login", "static"}

# GET endpoints that render a full HTML page → redirect to login rather than a JSON 401.
_PAGE_ENDPOINTS = {
    "main.index",
    "scan.show_scan",
    "attacks.show_attack",
    "results.show_results",
    "diagnostics.show_diagnostics",
    "settings.show_settings",
}

# --- in-memory login brute-force throttle (per source IP; resets on restart) ---
_LOGIN_FAILS = {}
_MAX_FAILS = 8
_WINDOW = 300  # seconds to accumulate failures over
_LOCK = 300    # seconds locked once _MAX_FAILS is reached


def auth_required():
    """Whether to enforce the login gate.

    OFF by default: the app binds to loopback and is single-operator, so the loopback bind is
    itself the access control and a password only adds friction. It turns ON automatically
    when the panel is exposed to the network (``AIRSTRIKE_BIND_ALL=1``) or when explicitly
    requested (``AIRSTRIKE_REQUIRE_AUTH=1``). ``AIRSTRIKE_DISABLE_AUTH=1`` forces it off even
    when exposed (an operator's explicit choice).
    """
    if os.environ.get("AIRSTRIKE_DISABLE_AUTH") == "1":
        return False
    if os.environ.get("AIRSTRIKE_REQUIRE_AUTH") == "1":
        return True
    return os.environ.get("AIRSTRIKE_BIND_ALL") == "1"


def resolve_password():
    """Return the operator password: ``AIRSTRIKE_PASSWORD`` or a generated one (shown once)."""
    pw = os.environ.get("AIRSTRIKE_PASSWORD")
    if pw:
        return pw
    pw = secrets.token_urlsafe(12)
    # Print the secret directly to the console rather than routing it through the logging
    # stack (which could be shipped to a file/aggregator).
    banner = "=" * 66
    print(f"\n{banner}\n  AIRSTRIKE_PASSWORD not set. Login password for this run:\n"
          f"      {pw}\n  Set AIRSTRIKE_PASSWORD to choose your own and keep it stable.\n{banner}\n",
          flush=True)
    return pw


def get_csrf_token():
    """Return the session CSRF token, creating one if the session doesn't have it yet."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def check_password(password):
    """Constant-time check of a submitted password against the configured hash."""
    from flask import current_app

    return check_password_hash(current_app.config["AIRSTRIKE_PASSWORD_HASH"], password or "")


def login_locked(ip):
    """True if this source IP is currently locked out from login attempts."""
    entry = _LOGIN_FAILS.get(ip)
    if not entry:
        return False
    count, first = entry
    if time.time() - first > max(_WINDOW, _LOCK):
        _LOGIN_FAILS.pop(ip, None)
        return False
    return count >= _MAX_FAILS


def record_login_failure(ip):
    now = time.time()
    count, first = _LOGIN_FAILS.get(ip, (0, now))
    if now - first > _WINDOW:
        count, first = 0, now
    _LOGIN_FAILS[ip] = (count + 1, first)


def clear_login_failures(ip):
    _LOGIN_FAILS.pop(ip, None)


def _same_origin(req):
    """True if the request's Origin/Referer matches the request host (or neither is present).

    SameSite=Strict already stops cross-site cookies; this is defense-in-depth against any
    cross-origin XHR/fetch that still manages to ride the session.
    """
    origin = req.headers.get("Origin")
    if origin:
        return urlparse(origin).netloc == req.host
    referer = req.headers.get("Referer")
    if referer:
        return urlparse(referer).netloc == req.host
    return True


def init_auth(app, password):
    """Wire session hardening, the login + CSRF + same-origin guard, and the template global."""
    app.config["AIRSTRIKE_PASSWORD_HASH"] = generate_password_hash(password)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")
    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def _require_login_and_csrf():
        # The SocketIO transport authenticates in its own connect handler; login/static are public.
        if request.path.startswith("/socket.io"):
            return None
        if request.endpoint in _PUBLIC_ENDPOINTS:
            return None

        # 1) Authentication.
        if not session.get("authenticated"):
            if request.endpoint in _PAGE_ENDPOINTS:
                return redirect(url_for("auth.login", next=request.path))
            return jsonify({"success": False, "error": "Authentication required"}), 401

        # 2) Same-origin only (blocks cross-site fetch/XHR that rides the session).
        if not _same_origin(request):
            return jsonify({"success": False, "error": "Cross-origin request rejected"}), 403

        # 3) CSRF on every state-changing request.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sent = request.headers.get("X-CSRFToken")
            if not sent and request.form:
                sent = request.form.get("csrf_token")
            expected = session.get("csrf_token", "")
            if not sent or not expected or not hmac.compare_digest(str(sent), str(expected)):
                return jsonify({"success": False, "error": "CSRF token missing or invalid"}), 400

        return None
