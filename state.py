"""
AirStrike Shared State
----------------------

This module manages the shared, in-memory state of the application.
It holds global variables that need to be accessed across different parts
of the application, such as the current network interface, scan results,
and attack statuses. It also initializes the SocketIO instance for real-time
communication.

Note: Using global variables for state management is simple but may not be
suitable for large-scale or multi-worker deployments. For such cases,
consider using a more robust solution like Redis.
"""

from flask_socketio import SocketIO
from prettytable import PrettyTable

# Initialize SocketIO without a Flask app instance yet.
# The app will be associated with it in the application factory.
socketio = SocketIO()

# -- Network State --
interface = None  # The selected network interface for all operations
available_interfaces = [] # List of available network interfaces

# -- Scanning State --
is_scanning = False  # Flag to indicate if a scan is in progress
scan_process = None  # Holds the process object for the network scan
access_points = {}  # Dictionary to store discovered access points
clients = {} # Dictionary to store discovered clients

# -- Attack State --
current_attack = "none" # Describes the currently active attack
is_attacking = False  # Flag to indicate if an attack is in progress
attack_process = None  # Holds the process object for the current attack

# -- Handshake Capture State --
handshake_captured = False # Flag indicating if a handshake has been captured
capturing_handshake = False # Flag indicating if handshake capture is active
handshake_capture_process = None # Process for handshake capture

# -- Deauth Attack State --
deauth_process = None # Process for deauthentication attack

# -- Evil Twin State --
evil_twin_process = None # Process for the Evil Twin attack

# -- General State --
clients_connected = 0  # Number of clients connected via SocketIO

# -- Results & Data --
captured_handshakes = [] # List of captured handshake files
deauth_results_table = PrettyTable() # Table for deauth results
deauth_results_table.field_names = ["Time", "Client MAC", "Status"]
