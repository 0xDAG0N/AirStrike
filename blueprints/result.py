"""
Results Blueprint
-----------------

This blueprint is responsible for displaying the results of various
operations, such as captured handshakes.
"""

from flask import Blueprint, render_template, current_app, send_from_directory
from airstrike import utils

results_bp = Blueprint('results', __name__, url_prefix='/results')

@results_bp.route('/')
def results_page():
    """Renders the results page."""
    handshakes = utils.get_captured_handshakes(current_app.config['UPLOAD_FOLDER'])
    return render_template('results.html', handshakes=handshakes)

@results_bp.route('/download/<filename>')
def download_capture(filename):
    """Allows downloading of a capture file."""
    captures_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(directory=captures_dir, path=filename, as_attachment=True)
