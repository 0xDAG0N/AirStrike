#!/usr/bin/env python3
"""
AirStrike Web Interface Runner
"""
import os
import sys
import time
import logging

# Set environment variables to suppress debugger warnings
os.environ['GEVENT_SUPPORT'] = 'True'
os.environ['PYTHONUNBUFFERED'] = '1'  # Ensure output is not buffered
os.environ['AIRSTRIKE_DEBUG'] = '1'   # Still enable our own debugging

# Ensure the script is running with root privileges
if os.geteuid() != 0:
    print("=" * 80)
    print("ERROR: AirStrike must be run with root privileges!")
    print("The application will now exit.")
    print("Please restart with: sudo python run.py")
    print("=" * 80)
    sys.exit(1)

print("Running AirStrike with root privileges. All features will be available.")

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app and SocketIO
from web.app import app
from web.socket_io import socketio

if __name__ == '__main__':
    # Add host entry for airstrike.local
    host_entry = "127.0.0.1 airstrike.local"
    hosts_file = "/etc/hosts"
    try:
        with open(hosts_file, 'r') as f:
            content = f.read()
        if host_entry not in content:
            print(f"Adding '{host_entry}' to {hosts_file}")
            with open(hosts_file, 'a') as f:
                f.write(f"\n{host_entry}\n")
    except IOError as e:
        print(f"Error modifying {hosts_file}: {e}")
        print("Please add the following line to your /etc/hosts file manually:")
        print(f"    {host_entry}")

    # Create output directory if it doesn't exist
    from web.shared import config
    os.makedirs(config['output_dir'], exist_ok=True)
    
    print("\n" + "=" * 60)
    print("Starting AirStrike with Socket.IO enabled")
    print("Using root privileges: {}".format("Yes" if os.geteuid() == 0 else "No"))
    
    # Print a clickable link with different formats for better compatibility
    print("\nAccess the web interface at:")
    print("\033[1;34mhttp://airstrike.local:5000\033[0m")  # Bold blue
    print("\033]8;;http://airstrike.local:5000\033\\Click here to open in browser\033]8;;\033\\")  # Hyperlink
    print("=" * 60 + "\n")
    
    # Run the Flask app with SocketIO (in production mode to avoid debugger spam)
    socketio.run(app, debug=False, host='0.0.0.0', port=5000) 