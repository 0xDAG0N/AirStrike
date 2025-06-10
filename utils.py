"""
AirStrike Utility Functions
---------------------------

This module provides consolidated utility functions used across the AirStrike application.
It includes network-related helpers for managing interfaces and running commands.
"""

import subprocess
import netifaces
import os
import re

def get_wireless_interfaces():
    """
    Retrieves a list of wireless network interfaces.

    Returns:
        list: A list of strings, where each string is the name of a wireless interface.
    """
    interfaces = []
    try:
        for iface in netifaces.interfaces():
            # Use iwconfig to check if the interface is wireless.
            # A non-zero return code usually means it's not a wireless interface.
            if subprocess.call(['iwconfig', iface], stderr=subprocess.PIPE, stdout=subprocess.PIPE) == 0:
                interfaces.append(iface)
    except FileNotFoundError:
        # 'iwconfig' not found, maybe not a Linux system or not installed.
        print("Warning: 'iwconfig' command not found. Could not detect wireless interfaces.")
    except Exception as e:
        print(f"An error occurred while getting wireless interfaces: {e}")
    return interfaces


def set_monitor_mode(interface, enable=True):
    """
    Enables or disables monitor mode on a given network interface.

    Args:
        interface (str): The name of the network interface.
        enable (bool): True to enable monitor mode, False to disable.

    Returns:
        bool: True if the command was successful, False otherwise.
    """
    if not interface:
        print("Error: No interface specified.")
        return False
        
    action = "start" if enable else "stop"
    print(f"Setting monitor mode to '{action}' on interface {interface}...")
    try:
        # Bring the interface down before changing mode
        subprocess.run(['ifconfig', interface, 'down'], check=True)
        # Set the mode to monitor
        subprocess.run(['iwconfig', interface, 'mode', 'monitor' if enable else 'managed'], check=True)
        # Bring the interface back up
        subprocess.run(['ifconfig', interface, 'up'], check=True)
        print(f"Successfully set monitor mode to '{action}' on {interface}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error changing monitor mode on {interface}: {e}")
        return False
    except FileNotFoundError:
        print("Error: 'ifconfig' or 'iwconfig' not found. Make sure you are on a Linux system with wireless tools installed.")
        return False

def get_captured_handshakes(captures_dir='captures'):
    """
    Scans the captures directory for .cap files.

    Args:
        captures_dir (str): The directory where capture files are stored.

    Returns:
        list: A list of dictionaries, each containing info about a handshake file.
    """
    handshakes = []
    if not os.path.exists(captures_dir):
        return handshakes

    for filename in os.listdir(captures_dir):
        if filename.endswith(".cap"):
            # Extract BSSID and ESSID from filename, assuming format like 'BSSID_ESSID.cap'
            # This regex is more robust to handle ESSIDs with spaces or special characters.
            match = re.match(r"([0-9A-Fa-f:]{17})_(.+)\.cap", filename)
            if match:
                bssid = match.group(1)
                essid = match.group(2).replace('_', ' ') # Replace underscores back to spaces in ESSID
                handshakes.append({
                    'essid': essid,
                    'bssid': bssid,
                    'filename': filename
                })
    return handshakes

def run_command(command):
    """
    Runs a shell command and returns its output.

    Args:
        command (list): The command to run as a list of strings.

    Returns:
        str: The standard output of the command, or an error message.
    """
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running command: {e}\n{e.stderr}"
    except FileNotFoundError:
        return f"Error: Command '{command[0]}' not found."

