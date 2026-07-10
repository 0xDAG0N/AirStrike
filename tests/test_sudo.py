"""Tests for ``run_with_sudo``: it must take an argv list and never a shell string."""

import pytest

from app.core import sudo


class _RecordingPopen:
    """Stand-in for ``subprocess.Popen`` that records argv and fakes a successful run."""

    last_argv = None
    last_kwargs = None

    def __init__(self, argv, **kwargs):
        type(self).last_argv = argv
        type(self).last_kwargs = kwargs

    def communicate(self):
        return ("out", "")

    @property
    def returncode(self):
        return 0


def _install_recorder(monkeypatch, *, euid):
    monkeypatch.setattr(sudo.os, "geteuid", lambda: euid)
    monkeypatch.setattr(sudo.subprocess, "Popen", _RecordingPopen)
    _RecordingPopen.last_argv = None
    _RecordingPopen.last_kwargs = None


def test_rejects_shell_string(monkeypatch):
    _install_recorder(monkeypatch, euid=0)
    with pytest.raises(TypeError):
        sudo.run_with_sudo("ip link show wlan0; rm -rf /")
    # The injection string must never reach Popen.
    assert _RecordingPopen.last_argv is None


def test_rejects_bytes(monkeypatch):
    _install_recorder(monkeypatch, euid=0)
    with pytest.raises(TypeError):
        sudo.run_with_sudo(b"reboot")


def test_rejects_empty_argv(monkeypatch):
    _install_recorder(monkeypatch, euid=0)
    with pytest.raises(ValueError):
        sudo.run_with_sudo([])


def test_runs_argv_directly_when_root(monkeypatch):
    _install_recorder(monkeypatch, euid=0)
    success, out, err = sudo.run_with_sudo(["ip", "link", "show", "wlan0"])
    assert success is True
    assert out == "out"
    # No sudo prefix when already root, and NO shell.
    assert _RecordingPopen.last_argv == ["ip", "link", "show", "wlan0"]
    assert "shell" not in _RecordingPopen.last_kwargs


def test_prefixes_sudo_when_not_root(monkeypatch):
    _install_recorder(monkeypatch, euid=1000)
    sudo.run_with_sudo(["iwconfig", "wlan0"])
    assert _RecordingPopen.last_argv == ["sudo", "iwconfig", "wlan0"]


def test_argv_tokens_are_never_reparsed(monkeypatch):
    """A metacharacter arriving as a single argv token stays one opaque argument."""
    _install_recorder(monkeypatch, euid=0)
    sudo.run_with_sudo(["ip", "link", "show", "wlan0; rm -rf /"])
    # The dangerous value is a single token, not split into new command words.
    assert _RecordingPopen.last_argv == ["ip", "link", "show", "wlan0; rm -rf /"]
