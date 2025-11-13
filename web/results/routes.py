from flask import Blueprint, jsonify, request, render_template, redirect, url_for
import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from .helpers import get_attack_status, get_attack_log, get_captured_handshakes
from web.shared import config

results_bp = Blueprint('results', __name__)
@results_bp.route('/results')
def show_results():
    # Root execution is enforced at startup, so no need to check here anymore
    return render_template('results.html')

@results_bp.route('/attack_status')
def attack_status():
    # Root execution is enforced at startup, so no need to check here anymore
    return jsonify(get_attack_status())

@results_bp.route('/attack_log')
def attack_log():
    # Root execution is enforced at startup, so no need to check here anymore
    return jsonify({'log': get_attack_log()})

@results_bp.route('/captured_handshakes')
def captured_handshakes():
    # Root execution is enforced at startup, so no need to check here anymore
    return jsonify({'handshakes': get_captured_handshakes()})