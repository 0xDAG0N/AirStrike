"""Diagnostics routes (was web/diagnostics/routes.py + web/diagnostics/helpers.py, folded
inline). Trivial orchestration — no separate service module."""

import os
import re
import platform
import subprocess
import shutil
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

from app.config import config
from app.core.logging import logger
from app.core.sudo import run_with_sudo

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
        # Check if interface exists
        success, output, _ = run_with_sudo(f"ip link show {interface}")
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
        success, output, _ = run_with_sudo(f"iwconfig {interface}")
        if success and "no wireless extensions" not in output.lower():
            details["is_wireless"] = True

            # Check mode
            mode_match = re.search(r"Mode:(\w+)", output)
            if mode_match:
                details["mode"] = mode_match.group(1)

        # Try to get driver information
        success, output, _ = run_with_sudo(f"ethtool -i {interface}")
        if success:
            driver_match = re.search(r"driver:\s+(\w+)", output)
            if driver_match:
                details["driver"] = driver_match.group(1)

            # Try to get chipset info
            chipset_match = re.search(r"bus-info:\s+(.+)", output)
            if chipset_match:
                details["chipset"] = chipset_match.group(1)

        # Check if monitor mode is supported
        success, output, _ = run_with_sudo(
            f"iw phy `iw dev {interface} info | grep wiphy | awk '{{print $2}}'` info"
        )
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
        success, output, _ = run_with_sudo("uname -r")
        if success:
            info["kernel"] = output.strip()

        # Get hostname
        success, output, _ = run_with_sudo("hostname")
        if success:
            info["hostname"] = output.strip()

        # Check if NetworkManager is running
        success, output, _ = run_with_sudo("systemctl is-active NetworkManager")
        if success and "active" in output:
            info["network_manager"] = "Active"
        else:
            # Try another method
            success, output, _ = run_with_sudo("ps aux | grep NetworkManager")
            if (
                success
                and "NetworkManager" in output
                and not output.strip().endswith("grep NetworkManager")
            ):
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


@diagnostics_bp.route("/run_diagnostic", methods=["POST"])
def run_diagnostic():
    """Run a diagnostic command with sudo privileges"""
    command = request.form.get("command")
    if not command:
        flash("No command provided", "danger")
        return redirect(url_for("diagnostics.show_diagnostics"))

    # Only allow certain safe diagnostic commands
    allowed_commands = [
        "iwconfig",
        "ifconfig",
        "ip a",
        "iwlist",
        "iw dev",
        "rfkill list",
        'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"',
    ]

    # Check if the command is allowed
    command_allowed = False
    for allowed in allowed_commands:
        if command.startswith(allowed):
            command_allowed = True
            break

    if not command_allowed:
        flash(f'Command not allowed. Allowed commands: {", ".join(allowed_commands)}', "danger")
        return redirect(url_for("diagnostics.show_diagnostics"))

    # Run the command
    success, output, error = run_with_sudo(command)

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
                "interface": conf.iface,
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
