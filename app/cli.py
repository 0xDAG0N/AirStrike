"""Command-line entry point (``airstrike`` console script and the ``run.py`` shim target).

Everything that used to happen at import time in ``run.py`` / ``web/app.py`` — enforcing
root, patching ``/etc/hosts``, creating the output dir, and running the server — lives here
in :func:`main`, so importing the application package has no side effects.
"""

import os
import sys


def _patch_hosts():
    """Ensure airstrike.local resolves locally by updating /etc/hosts if necessary."""
    host_entry = "127.0.0.1 airstrike.local"
    hosts_file = "/etc/hosts"
    try:
        with open(hosts_file, "r", encoding="utf-8", errors="ignore") as hosts_handle:
            content = hosts_handle.read()
        if host_entry not in content:
            print(f"Adding '{host_entry}' to {hosts_file}")
            with open(hosts_file, "a", encoding="utf-8") as hosts_handle:
                hosts_handle.write(f"\n{host_entry}\n")
    except OSError as exc:
        print(f"Error modifying {hosts_file}: {exc}")
        print("Please add the following line manually if the domain does not resolve:")
        print(f"    {host_entry}")


def main():
    """Root-gate, wire up the environment, build the app, and run the server."""
    # Set environment variables to suppress debugger warnings (was run.py).
    os.environ["GEVENT_SUPPORT"] = "True"
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["AIRSTRIKE_DEBUG"] = "1"

    # Ensure the process is running with root privileges (single gate).
    if os.environ.get("AIRSTRIKE_SKIP_ROOT_CHECK") != "1":
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            print("=" * 80)
            print("ERROR: AirStrike must be run with root privileges!")
            print("The application will now exit.")
            print("Please restart with: sudo python run.py   (or: sudo airstrike)")
            print("=" * 80)
            sys.exit(1)

    print("Running AirStrike with root privileges. All features will be available.")

    # Ensure airstrike.local resolves locally.
    _patch_hosts()

    # Build the application (deferred imports keep the engine importable off-root).
    from app import create_app
    from app.config import config, Config
    from app.extensions import socketio

    app = create_app()

    # Create output directory if it doesn't exist.
    os.makedirs(config["output_dir"], exist_ok=True)

    if Config.HOST == "0.0.0.0":
        print(
            "\n[!] WARNING: AIRSTRIKE_BIND_ALL exposes this root-privileged panel on ALL "
            "interfaces over PLAINTEXT HTTP — the session cookie and CSRF token can be "
            "sniffed and replayed on the network. Prefer the default loopback bind with an "
            "SSH tunnel, or terminate TLS in front.\n",
            flush=True,
        )

    is_root = (not hasattr(os, "geteuid")) or os.geteuid() == 0
    print("\n" + "=" * 60)
    print("Starting AirStrike with Socket.IO enabled")
    print("Using root privileges: {}".format("Yes" if is_root else "No"))
    print("\nAccess the web interface at:")
    print("\033[1;34mhttp://airstrike.local:5000\033[0m")  # Bold blue
    print("\033]8;;http://airstrike.local:5000\033\\Click here to open in browser\033]8;;\033\\")
    print("=" * 60 + "\n")

    # Run the Flask app with SocketIO (production mode to avoid debugger spam).
    socketio.run(app, debug=False, host=Config.HOST, port=Config.PORT)


if __name__ == "__main__":
    main()
