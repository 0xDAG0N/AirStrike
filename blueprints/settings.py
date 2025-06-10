"""
Settings Blueprint
------------------

This blueprint handles application settings, primarily managing the
wireless network interface.
"""
from flask import Blueprint, request, jsonify, render_template
from airstrike import state, utils

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
def settings_page():
    """Renders the settings page."""
    state.available_interfaces = utils.get_wireless_interfaces()
    return render_template('settings.html', interfaces=state.available_interfaces, current_interface=state.interface)

@settings_bp.route('/interface', methods=['POST'])
def set_interface():
    """API endpoint to set the active wireless interface."""
    data = request.get_json()
    iface = data.get('interface')

    if not iface:
        return jsonify({'status': 'error', 'message': 'Interface not provided.'}), 400

    if iface not in utils.get_wireless_interfaces():
        return jsonify({'status': 'error', 'message': f'Interface {iface} not available.'}), 400

    state.interface = iface
    state.socketio.emit('interface_changed', {'interface': state.interface})
    print(f"Interface set to {state.interface}")
    return jsonify({'status': 'success', 'message': f'Interface set to {iface}.'})

@settings_bp.route('/monitor-mode', methods=['POST'])
def set_monitor_mode_route():
    """API endpoint to enable or disable monitor mode."""
    data = request.get_json()
    enable = data.get('enable', True)

    if not state.interface:
        return jsonify({'status': 'error', 'message': 'Set an interface first.'}), 400
    
    success = utils.set_monitor_mode(state.interface, enable)
    
    if success:
        mode = "enabled" if enable else "disabled"
        state.socketio.emit('notification', {'message': f'Monitor mode {mode} on {state.interface}.'})
        return jsonify({'status': 'success', 'message': f'Monitor mode {mode} on {state.interface}.'})
    else:
        mode = "enable" if enable else "disable"
        state.socketio.emit('notification', {'message': f'Failed to {mode} monitor mode.'})
        return jsonify({'status': 'error', 'message': f'Failed to {mode} monitor mode.'}), 500
