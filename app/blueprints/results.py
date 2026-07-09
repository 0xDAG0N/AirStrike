"""Results routes (was web/results/routes.py + web/results/helpers.py, folded inline).

Sole owner of ``/attack_status`` and ``/attack_log`` (these used to be duplicated in the
attacks blueprint, which shadowed these ones).
"""

import os

from flask import Blueprint, jsonify, render_template

from app.config import config
from app.state import attack_state

results_bp = Blueprint("results", __name__)


# --- helpers (were web/results/helpers.py) ---


def get_attack_status():
    """Get the current status of any running attack."""
    return {
        "running": attack_state["running"],
        "attack_type": attack_state["attack_type"],
        "target_network": attack_state["target_network"],
        "progress": attack_state["progress"],
    }


def get_attack_log():
    """Get the log messages from the current or last attack."""
    return attack_state["log"]


def get_captured_handshakes():
    """Get a list of captured handshake files."""
    handshakes = []
    try:
        if not os.path.exists(config["output_dir"]):
            return handshakes

        # Iterate through directories in the output directory
        for bssid_dir in os.listdir(config["output_dir"]):
            bssid_path = os.path.join(config["output_dir"], bssid_dir)
            if os.path.isdir(bssid_path):
                # Look for capture files
                for file in os.listdir(bssid_path):
                    if file.endswith(".cap"):
                        file_path = os.path.join(bssid_path, file)
                        handshakes.append({
                            "bssid": bssid_dir.replace("-", ":"),
                            "file": file,
                            "path": file_path,
                            "size": os.path.getsize(file_path),
                            "date": os.path.getmtime(file_path),
                        })
    except Exception as e:
        print(f"Error getting handshakes: {e}")

    return handshakes


# --- routes ---


@results_bp.route("/results")
def show_results():
    return render_template("results.html")


@results_bp.route("/attack_status")
def attack_status():
    return jsonify(get_attack_status())


@results_bp.route("/attack_log")
def attack_log():
    return jsonify({"log": get_attack_log()})


@results_bp.route("/captured_handshakes")
def captured_handshakes():
    return jsonify({"handshakes": get_captured_handshakes()})
