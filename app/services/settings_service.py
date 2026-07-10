"""Settings orchestration (was web/settings/helpers.py).

NOTE (follow-up, out of scope for the structural refactor): ``get_available_interfaces``
returns a hardcoded stub list rather than enumerating real interfaces. Behavior is
preserved here deliberately; wiring it to real enumeration (via ``app.core.network_utils``)
is a separate behavioral change.
"""

import os

from app.config import config
from app.core.validation import ValidationError, validate_interface


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
    """Save the selected interface to the configuration.

    The interface is whitelisted before it is stored: ``config['interface']`` flows into
    ``sudo`` / ``iw`` argv across the app, so an invalid name is rejected here rather than
    persisted. Returns ``False`` on a missing or invalid interface.
    """
    try:
        if not interface_name:
            return False
        config["interface"] = validate_interface(interface_name)
        return True
    except ValidationError:
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
        if output_dir:
            config["output_dir"] = output_dir
            # Create directory if it doesn't exist
            os.makedirs(config["output_dir"], exist_ok=True)
            return True
        return False
    except Exception:
        return False
