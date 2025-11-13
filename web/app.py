"""
Flask app for AirStrike web interface.
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
import logging

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.shared import config, logger, init_logging
from web.socket_io import socketio, init_socketio

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.debug = False  # Disable debug mode for production use

# Initialize logging
init_logging(app)
logger.info("Starting AirStrike web interface")

# Initialize SocketIO with the Flask app
socketio_ready = init_socketio(app)
if not socketio_ready:
    logger.critical("SocketIO failed to initialize properly. Real-time updates will not work.")
    
# Register blueprints after socketio initialization
from web.scan.routes import scan_bp
from web.attacks.routes import attacks_bp
from web.settings.routes import settings_bp
from web.results.routes import results_bp
from web.diagnostics.routes import diagnostics_bp
from web.main.routes import main as main_bp

app.register_blueprint(main_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(attacks_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(results_bp)
app.register_blueprint(diagnostics_bp)

# Root route is already handled by main_bp
# Just add error handlers

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return render_template('error.html', error=f"Page {request.path} not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    logger.error(f"500 error: {str(e)}")
    return render_template('error.html', error=str(e)), 500

# This allows the app to be run using "python app.py" instead of the Flask development server
# when run directly (but not when imported by run.py)
if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # Use socketio.run instead of app.run for Socket.IO to work properly
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
