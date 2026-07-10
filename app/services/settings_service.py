"""Settings orchestration (was web/settings/helpers.py).

NOTE (follow-up, out of scope for the structural refactor): ``get_available_interfaces``
returns a hardcoded stub list rather than enumerating real interfaces. Behavior is
preserved here deliberately; wiring it to real enumeration (via ``app.core.network_utils``)
is a separate behavioral change.
"""

import os

from app.config import config
from app.core.validation import safe_path


def get_available_interfaces():
    """
    Get a list of available network interfaces.

    Returns:
        list: List of interface names.
    """
    # This is a placeholder - in a real implementation, you would
    # use a library like netifaces or subprocess to get actual interfaces
    try:
        # For now, return a static list
        return ["wlan0", "wlan1", "eth0"]
    except Exception:
        return ["wlan0"]  # Fallback to default


def save_interface_setting(interface_name):
    """Save the selected interface to the configuration."""
    try:
        if interface_name:
            config["interface"] = interface_name
            return True
        return False
    except Exception:
        return False


def save_wordlist_setting(wordlist_path):
    """Save the wordlist path to the configuration."""
    try:
        if wordlist_path:
            config["wordlist"] = wordlist_path
            return True
        return False
    except Exception:
        return False


def save_output_dir_setting(output_dir):
    """Save the output directory to the configuration and create it if it doesn't exist."""
    try:
        if not output_dir:
            return False
        # Jail the (root-created) capture directory under the working dir — block traversal
        # and absolute-path escapes so a request can't makedirs anywhere on the host.
        jailed = safe_path(output_dir, os.getcwd())
        if jailed is None:
            return False
        config["output_dir"] = jailed
        os.makedirs(jailed, exist_ok=True)
        return True
    except Exception:
        return False
