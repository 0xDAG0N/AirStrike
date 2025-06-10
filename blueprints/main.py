"""
Main Blueprint
--------------

This blueprint handles the main routes of the application, such as the
dashboard and initial data loading.
"""

from flask import Blueprint, render_template, jsonify
from airstrike import state
from airstrike import utils

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')

@main_bp.route('/dashboard-data')
def dashboard_data():
    """Provides initial data to the dashboard."""
    state.available_interfaces = utils.get_wireless_interfaces()
    return jsonify({
        'interface': state.interface,
        'interfaces': state.available_interfaces,
        'clients_connected': state.clients_connected,
        'is_scanning': state.is_scanning,
        'is_attacking': state.is_attacking,
        'current_attack': state.current_attack,
        'handshake_captured': state.handshake_captured,
    })

# SocketIO event handlers
@state.socketio.on('connect')
def handle_connect():
    """Handles new client connections."""
    state.clients_connected += 1
    state.socketio.emit('update_clients_connected', {'count': state.clients_connected})

@state.socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections."""
    state.clients_connected -= 1
    state.socketio.emit('update_clients_connected', {'count': state.clients_connected})
