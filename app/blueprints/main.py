"""Main / dashboard routes (was web/main/routes.py). Trivial — logic stays inline."""

from flask import Blueprint, render_template, jsonify

from app.state import stats

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard_stats")
def dashboard_stats():
    return jsonify(stats)
