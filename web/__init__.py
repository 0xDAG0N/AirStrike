from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'airstrike_secret_key'
    
    # Import and register blueprints
    from web.attacks.routes import attacks_bp
    from web.results.routes import results_bp
    from web.scan.routes import scan_bp
    from web.settings.routes import settings_bp
    from web.diagnostics.routes import diagnostics_bp
    from web.shared import shared
    app.register_blueprint(attacks_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(diagnostics_bp)
    app.register_blueprint(shared)
    
    return app