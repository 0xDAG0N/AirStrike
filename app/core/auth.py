"""Authentication + CSRF for the control panel (P0, docs/roadmap/01-security.md · S3).

Single-operator model: one password (from ``AIRSTRIKE_PASSWORD``, or a random one that is
generated and logged once at startup). A session cookie gates every route except the login
page and static files, and every state-changing request must carry the per-session CSRF
token. Combined with the loopback-by-default bind, this closes the "anyone on the network
gets root" exposure.
"""

import os
import hmac
import secrets

from flask import session, request, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from app.core.logging import logger

# Reachable without a session.
_PUBLIC_ENDPOINTS = {"auth.login", "auth.logout", "static"}

# GET endpoints that render a full HTML page → redirect to login rather than a JSON 401.
_PAGE_ENDPOINTS = {
    "main.index",
    "scan.show_scan",
    "attacks.show_attack",
    "results.show_results",
    "diagnostics.show_diagnostics",
    "settings.show_settings",
}


def resolve_password():
    """Return the operator password: ``AIRSTRIKE_PASSWORD`` or a generated one (logged once)."""
    pw = os.environ.get("AIRSTRIKE_PASSWORD")
    if pw:
        return pw
    pw = secrets.token_urlsafe(12)
    logger.warning("=" * 66)
    logger.warning("AIRSTRIKE_PASSWORD not set. Generated a login password for this run:")
    logger.warning("      %s", pw)
    logger.warning("Set AIRSTRIKE_PASSWORD to choose your own and keep it stable across runs.")
    logger.warning("=" * 66)
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


def init_auth(app, password):
    """Wire session hardening, the login + CSRF guard, and the ``csrf_token`` template global."""
    app.config["AIRSTRIKE_PASSWORD_HASH"] = generate_password_hash(password)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def _require_login_and_csrf():
        # Let the SocketIO transport and public endpoints through.
        if request.path.startswith("/socket.io"):
            return None
        if request.endpoint in _PUBLIC_ENDPOINTS:
            return None

        # 1) Authentication.
        if not session.get("authenticated"):
            if request.endpoint in _PAGE_ENDPOINTS:
                return redirect(url_for("auth.login", next=request.path))
            return jsonify({"success": False, "error": "Authentication required"}), 401

        # 2) CSRF on every state-changing request.
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sent = request.headers.get("X-CSRFToken")
            if not sent and request.form:
                sent = request.form.get("csrf_token")
            expected = session.get("csrf_token", "")
            if not sent or not expected or not hmac.compare_digest(str(sent), str(expected)):
                return jsonify({"success": False, "error": "CSRF token missing or invalid"}), 400

        return None
