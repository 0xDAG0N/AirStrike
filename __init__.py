"""
AirStrike Application Factory
-----------------------------

This file contains the application factory, `create_app`, which is responsible
for creating and configuring the Flask application instance. This pattern
makes the application more modular and easier to test and scale.
"""

import os
from flask import Flask, render_template
from airstrike.state import socketio

def create_app():
    """
    Creates and configures a Flask application instance.
    """
    # The template_folder is set to be in the same directory as this __init__.py file
    # The static_folder is also configured similarly.
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    # It's recommended to move this to a config file or environment variables
    # for better security and flexibility.
    app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_changed'
    app.config['UPLOAD_FOLDER'] = 'captures'

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Ensure the captures folder exists
    captures_dir = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
    if not os.path.exists(captures_dir):
        os.makedirs(captures_dir)

    # Initialize extensions
    socketio.init_app(app)

    # Register Blueprints
    # Blueprints help in organizing the application into distinct components.
    from .blueprints import main, scan, attacks, results, settings, diagnostics
    
    app.register_blueprint(main.main_bp)
    app.register_blueprint(scan.scan_bp)
    app.register_blueprint(attacks.attacks_bp)
    app.register_blueprint(results.results_bp)
    app.register_blueprint(settings.settings_bp)
    app.register_blueprint(diagnostics.diagnostics_bp)

    # Register Error Handlers
    # Custom error pages provide a better user experience.
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_code=500, error_message="Internal Server Error"), 500

    return app
