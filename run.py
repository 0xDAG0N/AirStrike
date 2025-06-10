"""
AirStrike Runner
----------------

This is the main entry point for the AirStrike application.
It creates the Flask app using the application factory pattern
and runs it with SocketIO support.

To run the application:
`python run.py`
"""

from airstrike import create_app
from airstrike.state import socketio

# Create the Flask app instance using the factory
app = create_app()

if __name__ == '__main__':
    # Run the app with SocketIO, allowing for real-time communication.
    # The host is set to '0.0.0.0' to make the server accessible on your network.
    socketio.run(app, debug=True, host='0.0.0.0')
