"""
Shared module for AirStrike web interface.

This module contains shared variables, configurations, and utilities
used across the web interface components.
"""

import time
import logging
import threading
import subprocess
import os
from flask import Blueprint, request

# Set up logging
logger = logging.getLogger('airstrike')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def init_logging(app):
    """
    Initialize logging for the Flask application.
    
    Args:
        app: The Flask application instance
    """
    # Set up Flask app to use our logger
    app.logger.handlers = []
    for handler in logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logger.level)
    
    # Enable more verbose logging
    if os.environ.get('AIRSTRIKE_DEBUG'):
        logger.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        logging.getLogger('socketio').setLevel(logging.DEBUG)
        logging.getLogger('engineio').setLevel(logging.DEBUG)
        logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    
    # Create a request logger
    @app.before_request
    def log_request_info():
        logger.debug(f'Request: {request.method} {request.path}')

    return True

# Create Blueprint for shared routes
shared = Blueprint('shared', __name__)

# Configuration
config = {
    'interface': 'wlan0',
    'wordlist': '/usr/share/wordlists/rockyou.txt',
    'output_dir': './captures/'
    # Removed sudo password and configuration flags since we require root execution
}

# Attack state
attack_state = {
    'running': False,
    'attack_type': None,
    'target_network': None,
    'progress': 0,
    'log': [],
    'stop_event': None,
    'threads': []
}

# Statistics
stats = {
    'networks_count': 0,
    'attacks_count': 0,
    'captures_count': 0
}

# Initialize stop event
attack_state['stop_event'] = threading.Event()

def log_message(message):
    """
    Log a message to both the attack log and the application logger.
    
    Args:
        message (str): The message to log
    """
    timestamp = time.strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    attack_state['log'].append(formatted_message)
    logger.info(formatted_message)
    

def add_log_message_shared(message):
    """
    Add a log message to both the attack log and the application logger.
    This function is used to break circular imports.
    
    Args:
        message (str): The message to log
    """
    log_message(message)
    
    # The socketio emit will be handled by the web.attacks.helpers.add_log_message function
    # This function is only used by modules that can't import web.attacks.helpers directly

def reset_attack_state():
    """
    Reset the attack state to default values.
    This should be called when an attack is stopped or fails.
    """
    attack_state['running'] = False
    attack_state['attack_type'] = None
    attack_state['progress'] = 0
    
    # Properly clean up threads and events
    if attack_state['stop_event'] and not attack_state['stop_event'].is_set():
        attack_state['stop_event'].set()
    
    # Create a new event for future attacks
    attack_state['stop_event'] = threading.Event()
    attack_state['threads'] = []

def run_with_sudo(command, password=None):
    """
    Run a command with sudo privileges.
    Since we're running as root, this is simplified to just run the command directly.
    
    Args:
        command (str): The command to run
        password (str, optional): Ignored parameter, kept for compatibility
        
    Returns:
        tuple: (success, output, error)
    """
    try:
        # If we're already running as root, don't use sudo
        if os.geteuid() == 0:
            # Run the command directly without sudo
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            # Run with sudo if we're not root
            process = subprocess.Popen(
                ['sudo'] + command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        stdout, stderr = process.communicate()
        success = process.returncode == 0
        
        # Log command execution for debugging
        if not success:
            logger.debug(f"Command failed: {command}\nStderr: {stderr}")
        
        return success, stdout, stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False, "", str(e)

def is_running_as_root():
    """
    Returns True if the current process is running as root (UID 0).
    """
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows compatibility (no geteuid)
        return False

def can_run_sudo_without_password():
    """
    Returns True if the current user can run sudo without a password (NOPASSWD sudoers).
    """
    try:
        result = subprocess.run(['sudo', '-n', 'id', '-u'], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() == '0'
    except Exception:
        return False

def is_sudo_authenticated():
    """
    Always returns True since we enforce root execution for the entire application.
    This function is kept for compatibility with existing code.
    """
    return True
    
    