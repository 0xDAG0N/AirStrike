"""Diagnostics routes (was web/diagnostics/routes.py + web/diagnostics/helpers.py, folded
inline). Trivial orchestration — no separate service module."""

import os
import re
import shlex
import platform
import subprocess
import shutil
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

from app.config import config
from app.core.logging import logger
from app.core.sudo import run_with_sudo
from app.core.validation import ValidationError, validate_interface

diagnostics_bp = Blueprint("diagnostics", __name__)


# --- helpers (were web/diagnostics/helpers.py) ---


def get_interface_details(interface):
    """Get detailed information about a network interface."""
    details = {
        "name": interface,
        "exists": False,
        "is_wireless": False,
        "mode": "Unknown",
        "status": "Unknown",
        "mac_address": "Unknown",
        "driver": "Unknown",
        "chipset": "Unknown",
        "supports_monitor": False,
    }

    try:
        interface = validate_interface(interface)
    except ValidationError:
        logger.error(f"Refusing to query invalid interface: {interface!r}")
        return details

    try:
        # Check if interface exists
        success, output, _ = run_with_sudo(["ip", "link", "show", interface])
        if success:
            details["exists"] = True

            # Check if it's UP
            if "UP" in output:
                details["status"] = "UP"
            elif "DOWN" in output:
                details["status"] = "DOWN"

            # Get MAC address
            mac_match = re.search(r"link/ether\s+([0-9a-f:]{17})", output, re.IGNORECASE)
            if mac_match:
                details["mac_address"] = mac_match.group(1)

        # Check if it's a wireless interface
        success, output, _ = run_with_sudo(["iwconfig", interface])
        if success and "no wireless extensions" not in output.lower():
            details["is_wireless"] = True

            # Check mode
            mode_match = re.search(r"Mode:(\w+)", output)
            if mode_match:
                details["mode"] = mode_match.group(1)

        # Try to get driver information
        success, output, _ = run_with_sudo(["ethtool", "-i", interface])
        if success:
            driver_match = re.search(r"driver:\s+(\w+)", output)
            if driver_match:
                details["driver"] = driver_match.group(1)

            # Try to get chipset info
            chipset_match = re.search(r"bus-info:\s+(.+)", output)
            if chipset_match:
                details["chipset"] = chipset_match.group(1)

        # Check if monitor mode is supported. The old one-liner shelled out to
        # `iw phy `iw dev IFACE info | grep wiphy | awk ...` info` — resolve the wiphy index
        # in Python instead and run each `iw` call as argv (no shell, no backticks).
        success, output, _ = run_with_sudo(["iw", "dev", interface, "info"])
        if success:
            wiphy_match = re.search(r"wiphy\s+(\d+)", output)
            if wiphy_match:
                success, output, _ = run_with_sudo(["iw", "phy", f"phy{wiphy_match.group(1)}", "info"])
                if success and "monitor" in output:
                    details["supports_monitor"] = True

        return details
    except Exception as e:
        logger.error(f"Error getting interface details: {str(e)}")
        return details


def get_system_info():
    """Get system information."""
    info = {
        "os": "Unknown",
        "kernel": "Unknown",
        "hostname": "Unknown",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
        "network_manager": "Not detected",
    }

    try:
        # Get OS information
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                os_release = f.read()
                name_match = re.search(r'PRETTY_NAME="(.+)"', os_release)
                if name_match:
                    info["os"] = name_match.group(1)

        # Get kernel version
        success, output, _ = run_with_sudo(["uname", "-r"])
        if success:
            info["kernel"] = output.strip()

        # Get hostname
        success, output, _ = run_with_sudo(["hostname"])
        if success:
            info["hostname"] = output.strip()

        # Check if NetworkManager is running
        success, output, _ = run_with_sudo(["systemctl", "is-active", "NetworkManager"])
        if success and "active" in output:
            info["network_manager"] = "Active"
        else:
            # Try another method: list processes and look for NetworkManager (was a shell
            # `ps aux | grep NetworkManager` pipe; grep in Python instead).
            success, output, _ = run_with_sudo(["ps", "aux"])
            if success and "NetworkManager" in output:
                info["network_manager"] = "Running"

        return info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return info


# --- routes ---


@diagnostics_bp.route("/diagnostics")
def show_diagnostics():
    """Render the diagnostics page"""
    # Get system info
    system_info = get_system_info()
    # Get interface details
    interface_details = get_interface_details(config["interface"])

    # Get available diagnostic commands
    diagnostic_commands = [
        {"name": "iwconfig", "description": "Show wireless interfaces"},
        {"name": "ifconfig", "description": "Show all interfaces"},
        {"name": "ip a", "description": "Show all interfaces (modern version)"},
        {"name": f"iwlist {config['interface']} scanning", "description": "Scan for networks"},
        {"name": f"iw dev {config['interface']} scan", "description": "Alternative network scan"},
        {"name": "rfkill list", "description": "Check for blocked interfaces"},
        {
            "name": 'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"',
            "description": "Show WiFi kernel modules",
        },
    ]

    return render_template(
        "diagnostics.html",
        system_info=system_info,
        interface_details=interface_details,
        diagnostic_commands=diagnostic_commands,
    )


# The diagnostic commands the UI offers, each mapped to a fixed argv list. The submitted
# ``command`` string is matched against this allowlist and translated to argv — user input
# never becomes a shell string. ``lsmod`` ignores trailing arguments, so the historical
# ``lsmod | grep -E ...`` entry only ever ran plain ``lsmod``; that is preserved here.
_STATIC_DIAGNOSTIC_COMMANDS = {
    "iwconfig": ["iwconfig"],
    "ifconfig": ["ifconfig"],
    "ip a": ["ip", "a"],
    "rfkill list": ["rfkill", "list"],
    "lsmod": ["lsmod"],
    'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"': ["lsmod"],
}

# Human-readable allowlist for the "not allowed" flash message.
_ALLOWED_DIAGNOSTIC_HELP = [
    "iwconfig",
    "ifconfig",
    "ip a",
    "iwlist <interface> scanning",
    "iw dev <interface> scan",
    "rfkill list",
    'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"',
]


def _resolve_diagnostic_argv(command):
    """Translate an allow-listed diagnostic command string into a safe argv list.

    Returns the argv list, or ``None`` if the command is not allow-listed or carries an
    invalid interface. Never returns a shell string; interface-parameterised commands
    validate the interface token via :func:`validate_interface`.
    """
    command = (command or "").strip()
    if command in _STATIC_DIAGNOSTIC_COMMANDS:
        return list(_STATIC_DIAGNOSTIC_COMMANDS[command])

    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    try:
        # `iwlist <interface> scanning`
        if len(tokens) == 3 and tokens[0] == "iwlist" and tokens[2] == "scanning":
            return ["iwlist", validate_interface(tokens[1]), "scanning"]
        # `iw dev <interface> scan`
        if len(tokens) == 4 and tokens[0] == "iw" and tokens[1] == "dev" and tokens[3] == "scan":
            return ["iw", "dev", validate_interface(tokens[2]), "scan"]
    except ValidationError:
        return None

    return None


@diagnostics_bp.route("/run_diagnostic", methods=["POST"])
def run_diagnostic():
    """Run an allow-listed diagnostic command (translated to argv, never a shell string)."""
    command = request.form.get("command")
    if not command:
        flash("No command provided", "danger")
        return redirect(url_for("diagnostics.show_diagnostics"))

    argv = _resolve_diagnostic_argv(command)
    if argv is None:
        flash(
            f'Command not allowed. Allowed commands: {", ".join(_ALLOWED_DIAGNOSTIC_HELP)}',
            "danger",
        )
        return redirect(url_for("diagnostics.show_diagnostics"))

    # Run the command
    success, output, error = run_with_sudo(argv)

    # Show the result
    if success:
        result = output
        flash("Command executed successfully", "success")
    else:
        result = f"Error: {error}"
        flash("Command failed", "danger")

    return render_template(
        "command_result.html",
        command=command,
        result=result,
        success=success,
        back_url=url_for("diagnostics.show_diagnostics"),
    )


@diagnostics_bp.route("/check_permissions")
def check_permissions():
    """Check if the application has the necessary permissions."""
    results = {
        "root_privileges": os.geteuid() == 0,
        "scapy_installed": shutil.which("scapy") is not None,
        "iwconfig_installed": shutil.which("iwconfig") is not None,
        "ifconfig_installed": shutil.which("ifconfig") is not None,
        "aircrack_installed": shutil.which("aircrack-ng") is not None,
        "tshark_installed": shutil.which("tshark") is not None,
        "can_set_monitor_mode": False,
        "can_inject_packets": False,
    }

    # Check if we can set monitor mode (requires root)
    if results["root_privileges"] and results["iwconfig_installed"]:
        interface = config["interface"]
        try:
            # Try to briefly set monitor mode and check if it works
            subprocess.run(
                ["sudo", "iwconfig", interface, "mode", "monitor"],
                check=True,
                capture_output=True,
                timeout=5,
            )
            results["can_set_monitor_mode"] = True

            # Set it back to managed mode
            subprocess.run(
                ["sudo", "iwconfig", interface, "mode", "managed"],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            results["error_monitor_mode"] = str(e)

    # Check if we can inject packets (requires root and monitor mode)
    if results["root_privileges"] and results["can_set_monitor_mode"]:
        try:
            from scapy.all import RadioTap, Dot11, Dot11Deauth, conf  # noqa: F401
            results["can_inject_packets"] = True
        except ImportError:
            results["error_scapy"] = "Scapy not properly installed"
        except Exception as e:
            results["error_scapy"] = str(e)

    return jsonify(results)


@diagnostics_bp.route("/test_deauth")
def test_deauth():
    """Test a single deauthentication packet (without actually sending it)."""
    try:
        from scapy.all import RadioTap, Dot11, Dot11Deauth, conf

        test_bssid = "00:11:22:33:44:55"  # Dummy BSSID for testing
        test_client = "FF:FF:FF:FF:FF:FF"  # Broadcast

        # Create but don't send the packet
        dot11 = Dot11(addr1=test_client, addr2=test_bssid, addr3=test_bssid)
        deauth_frame = RadioTap() / dot11 / Dot11Deauth(reason=7)  # noqa: F841

        return jsonify({
            "success": True,
            "packet_created": True,
            "root_privileges": os.geteuid() == 0,
            "message": "Deauth packet created successfully but not sent. This confirms scapy is working correctly.",
            "would_send_to": {
                # scapy >= 2.6 returns a NetworkInterface object here, which is not JSON
                # serializable — coerce to its name string.
                "interface": str(conf.iface),
                "bssid": test_bssid,
                "client": test_client,
            },
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "root_privileges": os.geteuid() == 0,
        })
