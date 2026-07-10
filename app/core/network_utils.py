"""Wireless interface / scanning utilities.

Consolidated single copy of what used to be duplicated as ``utils/network_utils.py``
(the live copy, kept here verbatim) and ``web/utils/network_utils.py`` (the dead copy,
deleted). The ambiguous ``utils.network_utils`` import name and the four
``sys.path.append('../')`` hacks that tried to steer that ambiguity are gone — callers
now import the unambiguous ``app.core.network_utils``.

NOTE (follow-up, out of scope for the structural refactor): ``set_monitor_mode`` /
``set_managed_mode`` call ``sys.exit(1)`` on failure. They run inside SocketIO worker
threads, so a mode-switch failure kills the worker thread rather than surfacing an error.
Behavior is preserved here deliberately; converting these to return values / raised
exceptions is a separate behavioral fix.
"""

import subprocess
import re
import sys

from app.core.validation import validate_interface


def set_monitor_mode(interface_name):
    interface_name = validate_interface(interface_name)
    try:
        subprocess.run(["sudo", "ifconfig", interface_name, "down"], check=True)
        subprocess.run(["sudo", "iwconfig", interface_name, "mode", "monitor"], check=True)
        subprocess.run(["sudo", "ifconfig", interface_name, "up"], check=True)
        print(f"[Setup] Interface {interface_name} set to monitor mode.")
    except subprocess.CalledProcessError as e:
        print(f"[Setup] Error setting {interface_name} to monitor mode: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print("[Setup] Error: required tools not found (ifconfig/iwconfig).")
        sys.exit(1)


def set_managed_mode(interface_name):
    interface_name = validate_interface(interface_name)
    try:
        subprocess.run(
            ["sudo", "ifconfig", interface_name, "down"], check=True, capture_output=True
        )
        subprocess.run(
            ["sudo", "iwconfig", interface_name, "mode", "managed"], check=True, capture_output=True
        )
        subprocess.run(
            ["sudo", "ifconfig", interface_name, "up"], check=True, capture_output=True
        )
        print(f"[Setup] Interface {interface_name} set to managed mode.")
    except subprocess.CalledProcessError as e:
        print(f"[Setup] Error setting {interface_name} to managed mode: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "[Setup] Error: 'ifconfig' or 'iwconfig' command not found. "
            "Ensure network tools are installed."
        )
        sys.exit(1)


def run_scan(interface):
    """
    Scans for available Wi-Fi networks and returns a list of dictionaries
    containing network information.

    Args:
        interface (str): The network interface to use for scanning (e.g., "wlan0").

    Returns:
        list: A list of dictionaries, where each dictionary represents a Wi-Fi network
              and contains its details. Returns an empty list if an error occurs or
              no networks are found.

    Raises:
        ValidationError: if ``interface`` is not a valid interface name. Validation happens
            before the scan's own try/except so a bad interface never reaches ``sudo``.
    """
    interface = validate_interface(interface)
    print(f"Scanning for Wi-Fi networks on interface {interface}...")
    try:
        # Using iw scan is often preferred over iwlist nowadays if available
        # Trying iwlist first as it was in the original code
        try:
            result = subprocess.run(
                ["sudo", "iwlist", interface, "scanning"],
                capture_output=True,
                text=True,
                check=True,
                timeout=20,
            )
        except FileNotFoundError:
            print(f"iwlist not found. Trying 'iw dev {interface} scan'...")
            result = subprocess.run(
                ["sudo", "iw", "dev", interface, "scan"],
                capture_output=True,
                text=True,
                check=True,
                timeout=20,
            )
        except subprocess.CalledProcessError as e:
            # Sometimes scanning immediately after bringing interface up fails
            # Or permissions might be wrong even with sudo
            print(f"Error running scan command with iwlist: {e}")
            print(f"Trying 'iw dev {interface} scan' as fallback...")
            try:
                result = subprocess.run(
                    ["sudo", "iw", "dev", interface, "scan"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=20,
                )
            except Exception as iw_err:
                print(f"Error running scan command with iw: {iw_err}")
                return []
        except subprocess.TimeoutExpired:
            print("Scanning timed out.")
            return []

        output = result.stdout
        aps = []

        # --- Parsing Logic for iwlist ---
        if "iwlist" in result.args[1]:
            current_ap = {}
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("Cell"):
                    if current_ap:  # Save the previous AP before starting a new one
                        # Basic check for essential info before adding
                        if (
                            "BSSID" in current_ap
                            and "ESSID" in current_ap
                            and "Channel" in current_ap
                        ):
                            aps.append(current_ap)
                        else:
                            pass  # Skip incomplete entries quietly
                    current_ap = {}
                    match = re.search(r"Address:\s*([\da-fA-F:]+)", line, re.IGNORECASE)
                    if match:
                        current_ap["BSSID"] = match.group(1).upper()  # Standardize BSSID case
                elif line.startswith('ESSID:"'):
                    current_ap["ESSID"] = line.split('"')[1]
                elif line.startswith("Channel:"):
                    # Handle potential extra text like "(secondary)"
                    channel_match = re.search(r"Channel:(\d+)", line)
                    if channel_match:
                        current_ap["Channel"] = channel_match.group(1)
                # Add other fields if needed (like Quality, Signal Strength etc.)

            if current_ap:  # Add the last AP found
                if "BSSID" in current_ap and "ESSID" in current_ap and "Channel" in current_ap:
                    aps.append(current_ap)

        # --- Parsing Logic for iw (more modern) ---
        elif "iw" in result.args[1]:
            current_ap = {}
            blocks = output.split("BSS ")  # Split output by AP blocks
            for block in blocks[1:]:  # Skip the first part before the first BSS
                lines = block.strip().split("\n")
                current_ap = {}
                bssid_match = re.match(r"([\da-fA-F:]+)\(on", lines[0])
                if bssid_match:
                    current_ap["BSSID"] = bssid_match.group(1).upper()

                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith("SSID:"):
                        current_ap["ESSID"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DS Parameter set: channel"):
                        current_ap["Channel"] = line.split("channel")[1].strip()
                    elif line.startswith("freq:"):  # Alternative channel source for some outputs
                        if "Channel" not in current_ap:
                            freq = int(line.split(":")[1].strip())
                            if 2412 <= freq <= 2484:  # 2.4 GHz band
                                channel = str(int((freq - 2407) / 5))
                                current_ap["Channel"] = channel
                            elif 5180 <= freq <= 5825:  # 5 GHz band (approximate mapping)
                                channel = str(int((freq - 5000) / 5))
                                current_ap["Channel"] = channel

                # Basic check for essential info before adding
                if "BSSID" in current_ap and current_ap.get("ESSID") and "Channel" in current_ap:
                    aps.append(current_ap)

        if not aps:
            print("No Wi-Fi networks found or parsed.")
        else:
            print(f"Found {len(aps)} Wi-Fi networks.")
        return aps

    except FileNotFoundError:
        print("Error: 'iwlist' or 'iw' command not found. Please ensure wireless tools are installed.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error scanning APs: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during scanning: {e}")
        return []
