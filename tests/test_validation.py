"""Unit tests for the input validators that guard every privileged subprocess call.

These are the choke point for command/argument/config injection, so the malicious-input
cases matter as much as the happy path.
"""

import pytest

from app.core.validation import (
    ValidationError,
    validate_bssid,
    validate_channel,
    validate_essid,
    validate_interface,
)


# --- BSSID ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("00:11:22:33:44:55", "00:11:22:33:44:55"),
        ("aa:bb:cc:dd:ee:ff", "AA:BB:CC:DD:EE:FF"),   # normalised to upper-case
        ("  00:11:22:AA:BB:CC  ", "00:11:22:AA:BB:CC"),  # surrounding whitespace trimmed
        ("FF:FF:FF:FF:FF:FF", "FF:FF:FF:FF:FF:FF"),
    ],
)
def test_validate_bssid_accepts_valid(raw, expected):
    assert validate_bssid(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "00:11:22:33:44:55; rm -rf /",   # command chaining
        "00:11:22:33:44:55 && reboot",
        "$(reboot)",
        "`reboot`",
        "00:11:22:33:44",                # too few octets
        "00:11:22:33:44:55:66",          # too many octets
        "0011.2233.4455",                # wrong separator
        "gg:11:22:33:44:55",             # non-hex
        "00-11-22-33-44-55",             # dash separator
        "",
        "wlan0",
    ],
)
def test_validate_bssid_rejects_malicious(raw):
    with pytest.raises(ValidationError):
        validate_bssid(raw)


def test_validate_bssid_rejects_non_string():
    with pytest.raises(ValidationError):
        validate_bssid(None)
    with pytest.raises(ValidationError):
        validate_bssid(123456)


# --- Interface --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    ["wlan0", "wlan1", "eth0", "wlan0mon", "mon0", "eth0.100", "wlp3s0", "  wlan0  "],
)
def test_validate_interface_accepts_valid(raw):
    assert validate_interface(raw) == raw.strip()


@pytest.mark.parametrize(
    "raw",
    [
        "wlan0; rm -rf /",       # command chaining
        "wlan0 && reboot",
        "wlan0|reboot",
        "$(reboot)",
        "`reboot`",
        "wlan0 scanning",        # embedded space / extra token
        "-i",                    # leading dash -> would be read as a flag (arg injection)
        "--version",
        "eth0\nreboot",          # newline injection
        "eth0/../../x",          # slash not allowed
        "a" * 16,                # exceeds IFNAMSIZ-1 (15)
        "",
    ],
)
def test_validate_interface_rejects_malicious(raw):
    with pytest.raises(ValidationError):
        validate_interface(raw)


# --- Channel ----------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [("6", 6), (11, 11), ("1", 1), (196, 196), ("36", 36)])
def test_validate_channel_accepts_valid(raw, expected):
    assert validate_channel(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["0", "-1", "197", "9999", "6; reboot", "6 || rm", "abc", "", "6.5", None, "$(id)"],
)
def test_validate_channel_rejects_invalid(raw):
    with pytest.raises(ValidationError):
        validate_channel(raw)


# --- ESSID ------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    ["MyNetwork", "Free WiFi", "café_2.4G", "a" * 32, "SSID-with-symbols!@#$%"],
)
def test_validate_essid_accepts_valid(raw):
    assert validate_essid(raw) == raw


@pytest.mark.parametrize(
    "raw",
    [
        "evil\nssid=attacker",         # newline -> hostapd config-directive injection
        "evil\r\nignore_broadcast_ssid=1",
        "ssid\x00null",                 # NUL byte
        "tab\tinjection",               # control character
        "a" * 33,                       # exceeds 32-octet SSID limit
        "𝓍" * 33,                       # >32 bytes once UTF-8 encoded
        "",                             # empty
    ],
)
def test_validate_essid_rejects_malicious(raw):
    with pytest.raises(ValidationError):
        validate_essid(raw)


def test_validation_error_is_value_error():
    """Callers may catch ValueError; ValidationError must remain a subclass of it."""
    assert issubclass(ValidationError, ValueError)
