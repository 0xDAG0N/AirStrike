"""Input validation for user-controlled values that reach the OS / attack engine.

Every value that flows toward a subprocess, a config file, or the filesystem is validated
here first. Nothing downstream should accept a raw request string. See docs/roadmap/01-security.md.
"""

import os
import re

# 00:11:22:33:44:55 form only.
_BSSID_RE = re.compile(r"^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}$")
# Linux interface names: short, alnum plus a few separators, no shell metacharacters.
_INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,15}$")


def valid_bssid(value):
    """True if value is a well-formed MAC/BSSID."""
    return isinstance(value, str) and bool(_BSSID_RE.match(value))


def valid_interface(value):
    """True if value is a plausible, metacharacter-free interface name."""
    return isinstance(value, str) and bool(_INTERFACE_RE.match(value))


def valid_channel(value):
    """True if value is an integer-ish 2.4/5/6 GHz channel number."""
    try:
        channel = int(value)
    except (TypeError, ValueError):
        return False
    return 1 <= channel <= 233


def sanitize_ssid(value):
    """Return the SSID if safe to write into hostapd.conf, else None.

    Rejects control characters and newlines (config-injection) and over-length SSIDs.
    """
    if not isinstance(value, str) or not (0 < len(value) <= 32):
        return None
    if any(ord(ch) < 32 for ch in value):
        return None
    return value


def safe_path(value, base):
    """Return an absolute path guaranteed to sit inside ``base``, else None.

    Blocks path traversal (``../``) on user-supplied output/wordlist paths.
    """
    if not isinstance(value, str) or not value:
        return None
    base_abs = os.path.abspath(base)
    candidate = os.path.abspath(os.path.join(base_abs, value)) if not os.path.isabs(value) \
        else os.path.abspath(value)
    # Must be the base itself or nested under it.
    if candidate == base_abs or candidate.startswith(base_abs + os.sep):
        return candidate
    return None
