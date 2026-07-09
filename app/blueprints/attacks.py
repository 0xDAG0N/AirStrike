"""Attack control routes (was web/attacks/routes.py).

Thread/engine orchestration lives in ``app.services.attack_service``; these handlers keep
the request/response flow, state transitions, and WebSocket events. ``/attack_status`` and
``/attack_log`` are intentionally NOT declared here — the results blueprint owns them (the
old duplicate declarations here silently shadowed the results ones).
"""

import threading

from flask import Blueprint, jsonify, request, render_template, url_for

from app.config import config
from app.core.logging import logger
from app.core.network_utils import set_managed_mode
from app.core.validation import valid_bssid, valid_channel, sanitize_ssid
from app.extensions import socketio
from app.services.attack_service import (
    launch_deauth_attack,
    launch_handshake_attack,
    launch_evil_twin_attack,
)
from app.state import attack_state, stats, log_message, reset_attack_state

attacks_bp = Blueprint("attacks", __name__)


@attacks_bp.route("/attack")
def show_attack():
    """Render the attack configuration page"""
    # No need to check sudo anymore since we enforce root execution
    return render_template("attack.html")


@attacks_bp.route("/start_attack", methods=["POST"])
def start_attack():
    """
    Start an attack based on the provided parameters.

    Expected JSON payload:
    {
        "network": {"bssid": "...", "essid": "...", "channel": "6"},
        "attack_type": "deauth|handshake|evil_twin",
        "config": { ... }
    }
    """
    # Root execution is enforced at startup, so no need to check here anymore
    try:

        # Check if an attack is already running
        if attack_state["running"]:
            return jsonify({"success": False, "error": "An attack is already running"})

        # Validate request data
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})

        if "network" not in data or "attack_type" not in data:
            return jsonify({"success": False, "error": "Missing required parameters"})

        # Get attack parameters
        network = data["network"]
        attack_type = data["attack_type"]
        attack_config = data.get("config", {})

        # Validate network data — presence…
        required_network_fields = ["bssid", "essid", "channel"]
        for field in required_network_fields:
            if field not in network:
                return jsonify(
                    {"success": False, "error": f"Missing required network field: {field}"}
                )

        # …then VALUES, before anything reaches the OS / attack engine.
        if not valid_bssid(network["bssid"]):
            return jsonify({"success": False, "error": "Invalid BSSID format"}), 400
        if not valid_channel(network["channel"]):
            return jsonify({"success": False, "error": "Invalid channel"}), 400
        if sanitize_ssid(network["essid"]) is None:
            return jsonify({"success": False, "error": "Invalid ESSID"}), 400
        client = attack_config.get("client")
        if client is not None and not valid_bssid(client):
            return jsonify({"success": False, "error": "Invalid client MAC"}), 400

        # Initialize attack state
        attack_state["running"] = True
        attack_state["attack_type"] = attack_type
        attack_state["target_network"] = network
        attack_state["progress"] = 0
        attack_state["log"] = []
        attack_state["stop_event"] = threading.Event()
        attack_state["threads"] = []

        # Log the start of the attack
        log_message(f"Starting {attack_type} attack on {network['essid']} ({network['bssid']})")

        # Emit attack started event via WebSocket
        socketio.emit("attack_started", {"attack_type": attack_type, "target_network": network})

        try:
            # Launch the appropriate attack
            if attack_type == "deauth":
                launch_deauth_attack(network, attack_config)
            elif attack_type == "handshake":
                launch_handshake_attack(network, attack_config)
            elif attack_type == "evil_twin":
                launch_evil_twin_attack(network, attack_config)
            else:
                reset_attack_state()
                socketio.emit("attack_error", {"error": f"Unknown attack type: {attack_type}"})
                return jsonify({"success": False, "error": f"Unknown attack type: {attack_type}"})

            # Update stats
            stats["attacks_count"] += 1

            return jsonify({"success": True})
        except Exception as e:
            reset_attack_state()

            # Check if the error is related to sudo
            error_str = str(e)
            if "sudo" in error_str.lower() or "permission" in error_str.lower():
                config["sudo_configured"] = False
                socketio.emit("attack_error", {"error": "Administrator privileges required"})
                return jsonify({
                    "success": False,
                    "error": "sudo_auth_required",
                    "redirect": url_for(
                        "settings.sudo_auth", next=request.referrer or url_for("attacks.show_attack")
                    ),
                }), 401

            logger.error(f"Error starting attack: {e}")
            socketio.emit("attack_error", {"error": str(e)})
            return jsonify({"success": False, "error": str(e)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@attacks_bp.route("/stop_attack", methods=["POST"])
def stop_attack():
    """Stop the currently running attack"""
    # Root execution is enforced at startup, so no need to check here anymore

    if not attack_state["running"]:
        return jsonify({"success": False, "error": "No attack is running"})

    try:
        # Signal threads to stop
        if attack_state["stop_event"]:
            attack_state["stop_event"].set()

        # Wait for threads to finish
        for thread in attack_state["threads"]:
            if thread and thread.is_alive():
                thread.join(timeout=2)

        # Reset interface to managed mode
        success = set_managed_mode(config["interface"])
        if not success:
            # Log the error but continue with attack cleanup
            error_msg = "Failed to set interface to managed mode. Continuing with attack cleanup."
            logger.warning(error_msg)
            socketio.emit("attack_warning", {"warning": error_msg})

        # Update attack state
        log_message("Attack stopped")
        reset_attack_state()

        # Emit attack stopped event via WebSocket
        socketio.emit("attack_stopped")

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error stopping attack: {e}")
        # Still try to reset the attack state even if there was an error
        reset_attack_state()
        socketio.emit("attack_error", {"error": str(e)})
        return jsonify({"success": False, "error": str(e)})
