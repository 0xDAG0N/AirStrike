"""Application logging.

Provides the shared ``airstrike`` logger. This module is framework-agnostic: the
Flask-specific wiring (app.logger handlers, before_request logging) lives in the
application factory (:func:`app.create_app`), not here.
"""

import logging

# The single named logger used across the whole application. Creating a named
# logger and attaching a handler is a cheap, side-effect-free import.
logger = logging.getLogger("airstrike")

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def get_logger():
    """Return the shared ``airstrike`` logger."""
    return logger
