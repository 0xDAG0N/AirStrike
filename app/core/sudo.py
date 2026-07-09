"""Privilege / command-execution helpers.

Moved verbatim from the old ``web.shared`` god-module. The application enforces root
execution at startup, so ``run_with_sudo`` runs commands directly when already root.

NOTE (follow-up, out of scope for the structural refactor): ``run_with_sudo`` builds its
argument list with ``command.split()`` and several callers interpolate user-controlled
values (BSSID / interface) into the command string. That is a command-injection surface
and should be hardened separately (accept an argv list + sanitize inputs).
"""

import os
import subprocess

from app.core.logging import logger


def run_with_sudo(command, password=None):
    """
    Run a command with sudo privileges.
    Since we're running as root, this is simplified to just run the command directly.

    Args:
        command (str): The command to run
        password (str, optional): Ignored parameter, kept for compatibility

    Returns:
        tuple: (success, output, error)
    """
    try:
        # If we're already running as root, don't use sudo
        if os.geteuid() == 0:
            # Run the command directly without sudo
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        else:
            # Run with sudo if we're not root
            process = subprocess.Popen(
                ["sudo"] + command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        stdout, stderr = process.communicate()
        success = process.returncode == 0

        # Log command execution for debugging
        if not success:
            logger.debug(f"Command failed: {command}\nStderr: {stderr}")

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
