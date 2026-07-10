"""Flask extension singletons.

Holds the bare SocketIO instance and nothing else. This module imports nothing internal,
which is what lets :mod:`app.sockets` and the application factory import ``socketio``
without recreating the old ``web.shared`` <-> ``web.socket_io`` deferred-import cycle.
"""

import os

from flask_socketio import SocketIO

# Scope CORS to the loopback origins the panel is served from (default bind). A wildcard
# would let any site the operator visits open an authenticated socket. For a non-loopback
# deployment (AIRSTRIKE_BIND_ALL=1), set AIRSTRIKE_ORIGINS to a comma-separated allowlist.
_PORT = os.environ.get("AIRSTRIKE_PORT", "5000")
_origins_env = os.environ.get("AIRSTRIKE_ORIGINS")
if _origins_env:
    _ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    _ALLOWED_ORIGINS = [f"http://127.0.0.1:{_PORT}", f"http://localhost:{_PORT}"]

socketio = SocketIO(cors_allowed_origins=_ALLOWED_ORIGINS, logger=True, engineio_logger=True)
