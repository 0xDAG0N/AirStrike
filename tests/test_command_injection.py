"""Command-injection hardening tests for the wireless-attack shell-outs.

Each test drives a real entry point (service function, engine worker, or the diagnostics
route) with a malicious BSSID / ESSID / channel / interface and asserts the value is
rejected *before* any subprocess is spawned — and that the surviving code paths pass argv
lists, never shell strings.
"""

from types import SimpleNamespace

import pytest

from app.core.validation import ValidationError


# --- helpers ----------------------------------------------------------------------------

class _Recorder:
    """Records every ``subprocess.run``-style call so tests can assert argv / no-shell."""

    def __init__(self):
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="", args=args)


def _boom(*args, **kwargs):
    raise AssertionError(f"a subprocess was spawned with untrusted input: {args!r}")


# ======================================================================================
# attack_service — the three launch functions
# ======================================================================================

@pytest.fixture
def atk(monkeypatch):
    import app.services.attack_service as atk

    # Any subprocess spawned during a *rejection* test is a failure.
    monkeypatch.setattr(atk.subprocess, "run", _boom)
    monkeypatch.setattr(atk.subprocess, "Popen", _boom)
    return atk


MALICIOUS_INTERFACES = ["wlan0; rm -rf /", "wlan0 && reboot", "-i", "$(reboot)", "wlan0|nc"]
MALICIOUS_BSSIDS = ["00:11:22:33:44:55; reboot", "$(reboot)", "not-a-mac", "`id`"]


@pytest.mark.parametrize("bssid", MALICIOUS_BSSIDS)
def test_deauth_rejects_malicious_bssid(atk, bssid):
    with pytest.raises(ValidationError):
        atk.launch_deauth_attack({"bssid": bssid, "channel": "6"}, {})


@pytest.mark.parametrize("interface", MALICIOUS_INTERFACES)
def test_deauth_rejects_malicious_interface(atk, monkeypatch, interface):
    monkeypatch.setitem(atk.config, "interface", interface)
    with pytest.raises(ValidationError):
        atk.launch_deauth_attack({"bssid": "AA:BB:CC:DD:EE:FF", "channel": "6"}, {})


def test_deauth_rejects_out_of_range_channel(atk):
    with pytest.raises(ValidationError):
        atk.launch_deauth_attack({"bssid": "AA:BB:CC:DD:EE:FF", "channel": "9999"}, {})


def test_deauth_rejects_malicious_client(atk):
    with pytest.raises(ValidationError):
        atk.launch_deauth_attack(
            {"bssid": "AA:BB:CC:DD:EE:FF", "channel": "6"}, {"client": "FF; reboot"}
        )


@pytest.mark.parametrize("bssid", MALICIOUS_BSSIDS)
def test_handshake_rejects_malicious_bssid(atk, bssid):
    with pytest.raises(ValidationError):
        atk.launch_handshake_attack({"bssid": bssid, "channel": "6"}, {})


def test_evil_twin_rejects_essid_config_injection(atk):
    # A newline in the ESSID would inject directives into the generated hostapd.conf.
    with pytest.raises(ValidationError):
        atk.launch_evil_twin_attack(
            {"bssid": "AA:BB:CC:DD:EE:FF", "essid": "evil\nssid=attacker", "channel": "6"}, {}
        )


@pytest.mark.parametrize("interface", MALICIOUS_INTERFACES)
def test_evil_twin_rejects_malicious_interface(atk, monkeypatch, interface):
    monkeypatch.setitem(atk.config, "interface", interface)
    with pytest.raises(ValidationError):
        atk.launch_evil_twin_attack(
            {"bssid": "AA:BB:CC:DD:EE:FF", "essid": "Net", "channel": "6"}, {}
        )


def test_deauth_valid_path_uses_argv_and_normalises(atk, monkeypatch):
    """The happy path still runs: it must build argv lists (no shell) and normalise inputs."""
    import threading

    recorder = _Recorder()
    monkeypatch.setattr(atk.subprocess, "run", recorder)
    monkeypatch.setattr(atk, "add_log_message", lambda *a, **k: None)
    monkeypatch.setattr(atk, "update_attack_progress", lambda *a, **k: None)
    monkeypatch.setattr(atk.os, "geteuid", lambda: 0)
    monkeypatch.setitem(atk.config, "interface", "wlan0")

    captured = {}

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            captured["args"] = args

        def start(self):
            pass

    monkeypatch.setattr(atk.threading, "Thread", DummyThread)
    atk.attack_state["stop_event"] = threading.Event()
    atk.attack_state["threads"] = []

    atk.launch_deauth_attack({"bssid": "aa:bb:cc:dd:ee:ff", "channel": "6"}, {})

    # Every subprocess call is an argv list with no shell.
    assert recorder.calls, "expected the deauth setup to shell out"
    for args, kwargs in recorder.calls:
        assert isinstance(args, list), f"argv must be a list, got {args!r}"
        assert kwargs.get("shell") in (None, False)
        assert "wlan0" in args  # the validated interface, not raw config access

    # BSSID normalised to upper-case and interface threaded through to the worker.
    worker_args = captured["args"]
    assert worker_args[0] == "AA:BB:CC:DD:EE:FF"
    assert worker_args[2] == "wlan0"


# ======================================================================================
# diagnostics — the /run_diagnostic allowlist resolver + route
# ======================================================================================

@pytest.mark.parametrize(
    "command, expected",
    [
        ("iwconfig", ["iwconfig"]),
        ("ifconfig", ["ifconfig"]),
        ("ip a", ["ip", "a"]),
        ("rfkill list", ["rfkill", "list"]),
        ('lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"', ["lsmod"]),
        ("iwlist wlan0 scanning", ["iwlist", "wlan0", "scanning"]),
        ("iw dev wlan0 scan", ["iw", "dev", "wlan0", "scan"]),
    ],
)
def test_diagnostic_resolver_allows_known_commands(command, expected):
    from app.blueprints.diagnostics import _resolve_diagnostic_argv

    assert _resolve_diagnostic_argv(command) == expected


@pytest.mark.parametrize(
    "command",
    [
        "iwconfig; rm -rf /",
        "ifconfig && reboot",
        "iwlist $(reboot) scanning",       # command substitution in the interface slot
        "iwlist wlan0; reboot scanning",   # extra shell token
        "iw dev wlan0; reboot scan",
        "cat /etc/shadow",
        "reboot",
        "",
        "iwlist -i scanning",              # flag-style interface (argument injection)
    ],
)
def test_diagnostic_resolver_rejects_injection(command):
    from app.blueprints.diagnostics import _resolve_diagnostic_argv

    assert _resolve_diagnostic_argv(command) is None


def test_run_diagnostic_route_runs_only_allowed(client, csrf, monkeypatch):
    import app.blueprints.diagnostics as diag

    calls = []

    def fake_run_with_sudo(argv, password=None):
        calls.append(argv)
        return True, "ok", ""

    monkeypatch.setattr(diag, "run_with_sudo", fake_run_with_sudo)

    # Allowed command is translated to argv and executed. (CSRF token required now.)
    resp = client.post("/run_diagnostic", data={"command": "ifconfig", "csrf_token": csrf})
    assert resp.status_code == 200
    assert calls == [["ifconfig"]]

    # Injection attempt is rejected before run_with_sudo is ever called.
    calls.clear()
    resp = client.post("/run_diagnostic", data={"command": "ifconfig; rm -rf /", "csrf_token": csrf})
    assert resp.status_code in (302, 303)
    assert calls == []


# ======================================================================================
# scan_service — reachable directly from /scan_wifi?interface=...
# ======================================================================================

@pytest.mark.parametrize("interface", MALICIOUS_INTERFACES)
def test_scan_wifi_networks_rejects_bad_interface(monkeypatch, interface):
    from app.services import scan_service

    monkeypatch.setattr(scan_service, "run_with_sudo", _boom)
    monkeypatch.setattr(scan_service, "run_scan", _boom)

    networks, error = scan_service.scan_wifi_networks(interface)
    assert networks == []
    assert error  # a non-empty error string, and nothing shelled out


@pytest.mark.parametrize("interface", MALICIOUS_INTERFACES)
def test_check_interface_status_rejects_bad_interface(monkeypatch, interface):
    from app.services import scan_service

    monkeypatch.setattr(scan_service, "run_with_sudo", _boom)

    status = scan_service.check_interface_status(interface)
    assert status["exists"] is False


# ======================================================================================
# settings_service — validation keeps config['interface'] clean
# ======================================================================================

def test_save_interface_setting_rejects_and_preserves(monkeypatch):
    from app.services import settings_service
    from app.config import config

    monkeypatch.setitem(config, "interface", "wlan0")

    assert settings_service.save_interface_setting("wlan0; rm -rf /") is False
    assert config["interface"] == "wlan0"  # unchanged

    assert settings_service.save_interface_setting("wlan1") is True
    assert config["interface"] == "wlan1"


# ======================================================================================
# capture engine — worker refuses to start on bad input, before any subprocess
# ======================================================================================

def test_capture_worker_refuses_malicious_bssid(monkeypatch):
    import threading
    from app.engine import capture_attack

    monkeypatch.setattr(capture_attack.subprocess, "run", _boom)
    monkeypatch.setattr(capture_attack.subprocess, "Popen", _boom)

    stop = threading.Event()
    logs = []
    capture_attack.capture_worker(
        "aa:bb; reboot", 6, "wlan0", 1, "./x/capture", "./x/capture-01.cap", "/tmp/wl",
        stop, log=logs.append,
    )
    assert stop.is_set()
    assert any("Refusing" in m for m in logs)


def test_capture_worker_refuses_malicious_interface(monkeypatch):
    import threading
    from app.engine import capture_attack

    monkeypatch.setattr(capture_attack.subprocess, "run", _boom)
    monkeypatch.setattr(capture_attack.subprocess, "Popen", _boom)

    stop = threading.Event()
    logs = []
    capture_attack.capture_worker(
        "AA:BB:CC:DD:EE:FF", 6, "wlan0; rm -rf /", 1, "./x/capture",
        "./x/capture-01.cap", "/tmp/wl", stop, log=logs.append,
    )
    assert stop.is_set()
    assert any("Refusing" in m for m in logs)


# ======================================================================================
# evil-twin engine — no shell, validated interface, config-injection-proof
# ======================================================================================

def test_run_command_is_shell_free(monkeypatch):
    from app.engine import evil_twin

    recorder = _Recorder()
    monkeypatch.setattr(evil_twin.subprocess, "run", recorder)

    evil_twin.run_command(["ifconfig", "wlan0", "up"])
    (args, kwargs), = recorder.calls
    assert args == ["ifconfig", "wlan0", "up"]
    assert kwargs.get("shell") in (None, False)


def test_setup_fake_ap_network_uses_argv(monkeypatch):
    from app.engine import evil_twin

    recorder = _Recorder()
    monkeypatch.setattr(evil_twin.subprocess, "run", recorder)
    monkeypatch.setattr(evil_twin, "_enable_ip_forwarding", lambda: None)

    evil_twin.setup_fake_ap_network("wlan0")

    assert recorder.calls
    for args, kwargs in recorder.calls:
        assert isinstance(args, list)
        assert kwargs.get("shell") in (None, False)


def test_setup_fake_ap_network_rejects_bad_interface(monkeypatch):
    from app.engine import evil_twin

    monkeypatch.setattr(evil_twin.subprocess, "run", _boom)
    with pytest.raises(ValidationError):
        evil_twin.setup_fake_ap_network("wlan0; rm -rf /")


def test_create_hostapd_config_rejects_ssid_injection(tmp_path):
    from app.engine import evil_twin

    with pytest.raises(ValidationError):
        evil_twin.create_hostapd_config("wlan0", "evil\nssid=attacker", 6, str(tmp_path))
    # Nothing was written.
    assert not list(tmp_path.iterdir())


def test_create_hostapd_config_writes_valid(tmp_path):
    from app.engine import evil_twin

    path = evil_twin.create_hostapd_config("wlan0", "MyNet", 6, str(tmp_path))
    assert path is not None
    contents = (tmp_path / "hostapd.conf").read_text()
    assert "ssid=MyNet" in contents
    assert "interface=wlan0" in contents
