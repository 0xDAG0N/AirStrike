"""
Attacks Blueprint
-----------------

This blueprint manages all the attack-related routes and logic,
acting as the bridge between the web interface and the core attack scripts.
"""

from flask import Blueprint, jsonify, request, render_template
import threading
from airstrike import state
from airstrike.attacks.deauth_attack import deauth_attack

attacks_bp = Blueprint('attacks', __name__, url_prefix='/attacks')

@attacks_bp.route('/page')
def attack_page():
    """Renders the main attack configuration page."""
    # Pass the current scan results to the page so the user can select targets
    return render_template('attack.html', access_points=list(state.access_points.values()))


@attacks_bp.route('/deauth', methods=['POST'])
def start_deauth_attack():
    """API endpoint to start a deauthentication attack."""
    if state.is_attacking:
        return jsonify({"status": "error", "message": "Another attack is already in progress."}), 400

    data = request.json
    target_mac = data.get('target_mac')
    bssid = data.get('bssid')

    if not all([target_mac, bssid, state.interface]):
        return jsonify({"status": "error", "message": "Missing parameters: target_mac, bssid, or interface."}), 400

    state.is_attacking = True
    state.current_attack = "deauth"
    
    # Run the attack in a background thread
    attack_thread = threading.Thread(
        target=deauth_attack,
        args=(target_mac, bssid, state.interface)
    )
    attack_thread.daemon = True
    attack_thread.start()
    
    state.socketio.emit('attack_started', {'type': 'deauth', 'target': target_mac})
    return jsonify({"status": "success", "message": f"Deauth attack started on {target_mac}."})

@attacks_bp.route('/stop', methods=['POST'])
def stop_all_attacks():
    """API endpoint to stop any ongoing attack."""
    if not state.is_attacking:
        return jsonify({"status": "error", "message": "No attack is currently running."}), 400

    # This is a simplified stop mechanism. A more robust implementation would
    # involve properly managing and terminating the attack process/thread.
    state.is_attacking = False
    state.current_attack = "none"

    if state.attack_process and state.attack_process.is_alive():
        state.attack_process.terminate() # Terminate the process if it exists
        state.attack_process = None
        
    state.socketio.emit('attack_stopped')
    print("Attack stopped by user.")
    return jsonify({"status": "success", "message": "Attack stopped."})
