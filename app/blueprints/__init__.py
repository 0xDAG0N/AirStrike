"""Blueprint registration.

Single registration point for the six feature blueprints, registered in the same order as
the old ``web/app.py``. Because ``/attack_status`` and ``/attack_log`` now live only in the
results blueprint (they used to be declared in BOTH attacks and results, with the attacks
copies silently shadowing the results ones), the old route collision is gone.
"""


def register_blueprints(app):
    """Import and register every feature blueprint exactly once."""
    from app.blueprints.main import main_bp
    from app.blueprints.scan import scan_bp
    from app.blueprints.attacks import attacks_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.results import results_bp
    from app.blueprints.diagnostics import diagnostics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(attacks_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(diagnostics_bp)
