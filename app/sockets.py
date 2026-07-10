"""SocketIO event handlers.

Registered by the application factory after ``socketio.init_app(app)``. The import-time
``logging.basicConfig`` that used to live in ``web.socket_io`` has moved into the factory
(configured at app construction, not at import).
"""

from flask import session

from app.extensions import socketio
from app.core.logging import logger
from app.state import attack_state


def register_socket_handlers():
    """Attach the SocketIO event handlers. Called once from the application factory."""

    @socketio.on("connect")
    def handle_connect():
        # Reject unauthenticated sockets — the /socket.io transport is exempt from the HTTP
        # before_request guard, so the connection itself is the auth boundary here.
        if not session.get("authenticated"):
            logger.warning("Rejected unauthenticated socket connection")
            return False
        logger.info("Client connected")
        # Send a welcome message to confirm connection
        socketio.emit("welcome", {"message": "Connected to AirStrike server"})

    @socketio.on("disconnect")
    def handle_disconnect():
        logger.info("Client disconnected")

    @socketio.on("attack_status_request")
    def handle_attack_status_request():
        logger.info("Received attack status request")
        socketio.emit(
            "attack_status",
            {
                "running": attack_state["running"],
                "attack_type": attack_state["attack_type"],
                "progress": attack_state["progress"],
            },
        )

    @socketio.on_error()
    def handle_error(e):
        logger.error(f"SocketIO error: {e}")
