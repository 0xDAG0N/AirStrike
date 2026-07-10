"""Login / logout routes (P0 · S3)."""

from flask import Blueprint, render_template, request, redirect, url_for, session

from app.core.auth import check_password, get_csrf_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.values.get("next", "")
    if request.method == "POST":
        if check_password(request.form.get("password", "")):
            session["authenticated"] = True
            get_csrf_token()  # mint a CSRF token for the new session
            # Only allow local same-site redirects — reject protocol-relative (//host) and
            # backslash tricks to prevent open redirects.
            safe_next = next_url.startswith("/") and not next_url.startswith(("//", "/\\"))
            return redirect(next_url if safe_next else url_for("main.index"))
        error = "Incorrect password."
    return render_template("login.html", error=error, next=next_url)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
