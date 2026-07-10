"""Whitelisting/validation for values that reach privileged subprocess calls.

The wireless attacks interpolate user-controlled values — a network BSSID, an ESSID, a
Wi-Fi channel, and an interface name — into ``sudo`` / ``iw`` / ``hostapd`` invocations.
Even with argv-list execution (no shell), an unvalidated value can smuggle extra flags
(argument injection, e.g. an "interface" of ``-i``) or, when written verbatim into a
generated ``hostapd`` / ``dnsmasq`` config, inject config directives via an embedded
newline. These validators are the single choke point: every externally supplied value must
pass through one of them *before* it reaches a subprocess or a config file.

Each validator raises :class:`ValidationError` (a ``ValueError`` subclass) on bad input and
returns a normalised value on success. They are pure — no global state, no subprocess.
"""

import os
import re

__all__ = [
    "ValidationError",
    "validate_bssid",
    "validate_interface",
    "validate_channel",
    "validate_essid",
    "valid_bssid",
    "valid_interface",
    "valid_channel",
    "sanitize_ssid",
    "bounded_number",
    "safe_path",
]


class ValidationError(ValueError):
    """Raised when an externally supplied value fails validation."""


# A BSSID/MAC is six colon-separated hex octets, e.g. ``00:11:22:AA:BB:CC``.
_BSSID_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

# Linux interface names: 1..15 chars (IFNAMSIZ - 1), must start with an alphanumeric
# (never ``-``, which a tool would read as a flag) and thereafter allow only
# ``[A-Za-z0-9._-]``. This rejects whitespace and every shell metacharacter, so the value
# is safe both as an argv token and in the rare shell-free config path.
_INTERFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,14}$")

# 802.11 channel numbers actually in use span 1..196 (2.4 GHz + 5/6 GHz bands).
_MIN_CHANNEL = 1
_MAX_CHANNEL = 196

# 802.11 SSID maximum length is 32 octets.
_MAX_ESSID_BYTES = 32


def validate_bssid(value):
    """Return the upper-cased BSSID when ``value`` is a well-formed MAC, else raise.

    Raises:
        ValidationError: if ``value`` is not a string or not a colon-separated MAC.
    """
    if not isinstance(value, str):
        raise ValidationError(f"BSSID must be a string, got {type(value).__name__}")
    candidate = value.strip()
    if not _BSSID_RE.match(candidate):
        raise ValidationError(f"Invalid BSSID: {value!r}")
    return candidate.upper()


def validate_interface(value):
    """Return the interface name when it matches the safe whitelist, else raise.

    Raises:
        ValidationError: if ``value`` is not a string or contains anything outside the
            ``[A-Za-z0-9._-]`` set / starts with a non-alphanumeric / is empty or >15 chars.
    """
    if not isinstance(value, str):
        raise ValidationError(f"Interface must be a string, got {type(value).__name__}")
    candidate = value.strip()
    if not _INTERFACE_RE.match(candidate):
        raise ValidationError(f"Invalid interface name: {value!r}")
    return candidate


def validate_channel(value):
    """Return ``value`` coerced to an int within the 802.11 channel range, else raise.

    Accepts an int or a numeric string (as arrives via JSON). Raises:
        ValidationError: if ``value`` is not an integer or falls outside 1..196.
    """
    try:
        channel = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid channel: {value!r}")
    if not (_MIN_CHANNEL <= channel <= _MAX_CHANNEL):
        raise ValidationError(f"Channel out of range ({_MIN_CHANNEL}-{_MAX_CHANNEL}): {value!r}")
    return channel


def validate_essid(value):
    """Return the ESSID when it is 1..32 bytes and control-character free, else raise.

    The ESSID is written verbatim into generated ``hostapd`` config; a newline or NUL would
    let it inject arbitrary config directives, so control characters are rejected outright.

    Raises:
        ValidationError: if ``value`` is not a string, is empty, exceeds 32 bytes, or
            contains any control character (``< 0x20`` or ``0x7F``).
    """
    if not isinstance(value, str):
        raise ValidationError(f"ESSID must be a string, got {type(value).__name__}")
    if value == "":
        raise ValidationError("ESSID must not be empty")
    if len(value.encode("utf-8")) > _MAX_ESSID_BYTES:
        raise ValidationError(f"ESSID exceeds {_MAX_ESSID_BYTES} bytes: {value!r}")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise ValidationError(f"ESSID contains control characters: {value!r}")
    return value


# --- Compatibility helpers (bool / None returning) used by the route + settings layer ---
# The validators above raise on bad input; these thin wrappers return bool / None / a bounded
# value, which is what the request handlers and the settings service expect.

def valid_bssid(value):
    """True if ``value`` is a well-formed BSSID."""
    try:
        validate_bssid(value)
        return True
    except ValidationError:
        return False


def valid_interface(value):
    """True if ``value`` is a safe interface name."""
    try:
        validate_interface(value)
        return True
    except ValidationError:
        return False


def valid_channel(value):
    """True if ``value`` is an in-range 802.11 channel."""
    try:
        validate_channel(value)
        return True
    except ValidationError:
        return False


def sanitize_ssid(value):
    """Return the ESSID if safe to write into hostapd.conf, else None."""
    try:
        return validate_essid(value)
    except ValidationError:
        return None


def bounded_number(value, lo, hi, as_int=True):
    """Return the coerced number if it parses and lo <= n <= hi, else None.

    Bounds attacker-supplied counts/intervals/durations so they can't drive a root-level
    resource-exhaustion DoS.
    """
    try:
        num = int(value) if as_int else float(value)
    except (TypeError, ValueError):
        return None
    return num if lo <= num <= hi else None


def safe_path(value, base):
    """Return an absolute path guaranteed to sit inside ``base``, else None.

    Blocks path traversal (``../``) and absolute-path escapes on user-supplied output paths
    that reach a root-level ``os.makedirs``.
    """
    if not isinstance(value, str) or not value:
        return None
    base_abs = os.path.abspath(base)
    candidate = (
        os.path.abspath(value)
        if os.path.isabs(value)
        else os.path.abspath(os.path.join(base_abs, value))
    )
    if candidate == base_abs or candidate.startswith(base_abs + os.sep):
        return candidate
    return None
