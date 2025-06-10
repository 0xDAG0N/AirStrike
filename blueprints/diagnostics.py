"""
Diagnostics Blueprint
---------------------

This blueprint provides tools for diagnosing system and network configurations
to ensure the application can run correctly.
"""

from flask import Blueprint, render_template, request, jsonify
from airstrike import utils

diagnostics_bp = Blueprint('diagnostics', __name__, url_prefix='/diagnostics')

@diagnostics_bp.route('/')
def diagnostics_page():
    """Renders the diagnostics page."""
    return render_template('diagnostics.html')

@diagnostics_bp.route('/run', methods=['POST'])
def run_diagnostic_command():
    """
    API endpoint to run a shell command for diagnostic purposes.
    Warning: Be extremely careful with this functionality in a production
    environment as it can expose the system to security risks.
    """
    data = request.get_json()
    command_str = data.get('command')

    if not command_str:
        return jsonify({'output': 'Error: No command provided.'}), 400
    
    # Simple sanitization/validation
    allowed_commands = ['ls', 'whoami', 'ifconfig', 'iwconfig', 'ls -l captures']
    if command_str not in allowed_commands:
        return jsonify({'output': f"Error: Command '{command_str}' is not allowed."}), 403

    # Split command string into a list for subprocess
    command_list = command_str.split()

    output = utils.run_command(command_list)
    
    return jsonify({'output': output})
