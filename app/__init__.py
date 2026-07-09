"""AirStrike application package.

``create_app`` is the single application-construction path (it replaces both the dead
``web/__init__.py`` factory and the ``web/app.py`` shadow entry point). All Flask /
blueprint / SocketIO imports are deferred into the function body so that ``import app``
(and therefore ``import app.engine`` / ``import app.core``) does NOT require Flask — the
attack engine stays importable and unit-testable with Flask absent.

The factory performs NO process-level side effects: the root check, ``/etc/hosts`` patch,
output-dir creation, and ``socketio.run`` all live in :func:`app.cli.main`.
"""

import os
import sys
import logging


def create_app(config_object=None):
    """Build and return the Flask application (with SocketIO, blueprints, handlers)."""
    from flask import Flask, render_template, request

    from app.config import Config
    from app.core.logging import logger
    from app.extensions import socketio
    from app.sockets import register_socket_handlers
    from app.blueprints import register_blueprints

    app = Flask(__name__, static_folder="static", template_folder="templates")

    # --- configuration ---
    app.config.from_object(config_object or Config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _resolve_secret_key(logger)
    app.debug = app.config.get("DEBUG", False)

    # --- logging (was web.shared.init_logging + web.socket_io import-time basicConfig) ---
    _configure_logging(app, logger)
    logger.info("Starting AirStrike web interface")

    # --- extensions ---
    # Preserve the old graceful-degradation behavior: if SocketIO fails to initialize,
    # log it but still return a working app (blueprints/HTTP keep functioning) — matching
    # web/socket_io.init_socketio + web/app.py's non-fatal handling.
    try:
        socketio.init_app(app)
        register_socket_handlers()
        logger.info(f"SocketIO initialized with app {app.name}")
    except Exception as e:
        logger.error(f"Error initializing SocketIO events: {e}")
        logger.critical("SocketIO failed to initialize properly. Real-time updates will not work.")

    # --- blueprints (single registration; resolves the /attack_status collision) ---
    register_blueprints(app)

    # --- error handlers (were in web/app.py) ---
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 error: {request.path}")
        return render_template("error.html", error=f"Page {request.path} not found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"500 error: {str(e)}")
        return render_template("error.html", error=str(e)), 500

    return app


def _resolve_secret_key(logger):
    """SECRET_KEY from env, else an ephemeral generated key (with a warning)."""
    secret = os.environ.get("AIRSTRIKE_SECRET_KEY")
    if secret:
        return secret
    logger.warning(
        "AIRSTRIKE_SECRET_KEY not set; generating an ephemeral key. Sessions will not "
        "survive a restart. Set AIRSTRIKE_SECRET_KEY to persist them."
    )
    return os.urandom(24)


def _configure_logging(app, logger):
    """Replicate the old logging setup at app-construction time.

    Combines ``web.shared.init_logging`` (wire Flask's app.logger to our handlers,
    before_request logging, AIRSTRIKE_DEBUG level bumps) with the import-time
    ``logging.basicConfig`` that used to live in ``web/socket_io.py`` — now here instead
    of at import.
    """
    from flask import request

    # Root logging config (was the import-time logging.basicConfig in web/socket_io.py).
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Wire Flask's app logger to our handlers (was web.shared.init_logging).
    app.logger.handlers = []
    for handler in logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logger.level)

    if os.environ.get("AIRSTRIKE_DEBUG"):
        logger.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        logging.getLogger("socketio").setLevel(logging.DEBUG)
        logging.getLogger("engineio").setLevel(logging.DEBUG)
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)

    @app.before_request
    def log_request_info():
        logger.debug(f"Request: {request.method} {request.path}")
