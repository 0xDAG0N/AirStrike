"""Flask extension singletons.

Holds the bare SocketIO instance and nothing else. This module imports nothing internal,
which is what lets :mod:`app.sockets` and the application factory import ``socketio``
without recreating the old ``web.shared`` <-> ``web.socket_io`` deferred-import cycle.
"""

from flask_socketio import SocketIO

# Same configuration as the old web.socket_io instance (behavior-preserving).
socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)
