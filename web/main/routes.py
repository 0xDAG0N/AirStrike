from flask import Blueprint, render_template, jsonify
from web.shared import stats

main = Blueprint('main', __name__)

# Routes
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard_stats')
def dashboard_stats():
    return jsonify(stats)