"""Privilege / command-execution helpers.

Moved from the old ``web.shared`` god-module. The application enforces root execution at
startup, so ``run_with_sudo`` runs commands directly when already root.

``run_with_sudo`` accepts an **argv list** and never invokes a shell. It used to take a
shell string and split it with ``command.split()``, while callers interpolated
user-controlled values (BSSID / interface) into that string — a command-injection surface.
Passing a ``str`` is now rejected outright; callers build validated argv lists instead.
"""

import os
import subprocess

from app.core.logging import logger


def run_with_sudo(command, password=None):
    """
    Run an argv command with root privileges, prefixing ``sudo`` only when not already root.

    Args:
        command (list[str] | tuple[str, ...]): The command as an argv list, e.g.
            ``["ip", "link", "show", "wlan0"]``. A plain string is rejected — shell strings
            are a command-injection hazard and are no longer accepted.
        password (str, optional): Ignored parameter, kept for backwards-compatible callers.

    Returns:
        tuple: (success, output, error)

    Raises:
        TypeError: if ``command`` is a ``str`` or not an iterable of argv tokens.
        ValueError: if ``command`` is empty.
    """
    if isinstance(command, (str, bytes)):
        raise TypeError(
            "run_with_sudo requires an argv list (e.g. ['ip', 'link', 'show', iface]), "
            "not a shell string"
        )
    try:
        argv = [str(token) for token in command]
    except TypeError:
        raise TypeError("run_with_sudo requires an iterable of argv tokens")
    if not argv:
        raise ValueError("run_with_sudo requires a non-empty command")

    try:
        # If we're already running as root, don't use sudo; otherwise prefix it.
        full_argv = argv if os.geteuid() == 0 else ["sudo", *argv]

        process = subprocess.Popen(
            full_argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate()
        success = process.returncode == 0

        # Log command execution for debugging
        if not success:
            logger.debug(f"Command failed: {argv}\nStderr: {stderr}")

        return success, stdout, stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False, "", str(e)


def is_running_as_root():
    """Returns True if the current process is running as root (UID 0)."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows compatibility (no geteuid)
        return False


def can_run_sudo_without_password():
    """Returns True if the current user can run sudo without a password (NOPASSWD sudoers)."""
    try:
        result = subprocess.run(["sudo", "-n", "id", "-u"], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip() == "0"
    except Exception:
        return False


def is_sudo_authenticated():
    """
    Always returns True since we enforce root execution for the entire application.
    This function is kept for compatibility with existing code.
    """
    return True
