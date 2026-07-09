"""Tests for the consolidated network_utils scan parser (against faked subprocess output)."""

from types import SimpleNamespace

from app.core import network_utils

IWLIST_OUTPUT = """\
          Cell 01 - Address: 00:11:22:33:44:55
                    ESSID:"TestNet"
                    Channel:6
          Cell 02 - Address: AA:BB:CC:DD:EE:FF
                    ESSID:"Second"
                    Channel:11
"""


def test_run_scan_parses_iwlist(monkeypatch):
    def fake_run(args, **kwargs):
        # args == ['sudo', 'iwlist', <iface>, 'scanning'] -> run_scan keys off args[1]
        return SimpleNamespace(stdout=IWLIST_OUTPUT, args=args, returncode=0)

    monkeypatch.setattr(network_utils.subprocess, "run", fake_run)
    aps = network_utils.run_scan("wlan0")
    assert aps == [
        {"BSSID": "00:11:22:33:44:55", "ESSID": "TestNet", "Channel": "6"},
        {"BSSID": "AA:BB:CC:DD:EE:FF", "ESSID": "Second", "Channel": "11"},
    ]


def test_run_scan_returns_empty_on_error(monkeypatch):
    import subprocess as sp

    def boom(args, **kwargs):
        raise sp.CalledProcessError(1, args)

    monkeypatch.setattr(network_utils.subprocess, "run", boom)
    assert network_utils.run_scan("wlan0") == []
